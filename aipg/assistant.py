import asyncio
import logging
from typing import Generic, List, Type, TypeVar

from pydantic import BaseModel

from aipg.configs.app_config import AppConfig
from aipg.llm import LLMClient
from aipg.rag.rag_builder import build_rag_service
from aipg.state import (
    FeedbackAgentState,
    ProcessTopicAgentState,
    ProjectsAgentState,
    Topic2Project,
)
from aipg.task_inference import (
    DefineTopicsInference,
    FeedbackInference,
    LLMRankerInference,
    ProjectGenerationInference,
    RAGServiceInference,
    TaskInference,
)

StateT = TypeVar("StateT", bound=BaseModel)

logger = logging.getLogger(__name__)


class BaseAssistant(Generic[StateT]):
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.llm = LLMClient(config)

    def handle_exception(self, stage: str, exception: Exception):
        raise Exception(f"{stage}: {exception}")

    async def _run_task_inference(
        self, task_inferences: List[Type[TaskInference[StateT]]], state: StateT
    ) -> StateT:
        for inference_class in task_inferences:
            logger.debug("Running task inference: %s", inference_class.__name__)
            inference = inference_class(llm=self.llm)
            try:
                state = await inference.transform(state)
            except Exception as e:
                logger.exception("Task inference failed: %s", inference_class.__name__)
                self.handle_exception(f"Task inference preprocessing: {inference_class}", e)
        return state

    async def execute(self, state: StateT) -> StateT:
        raise NotImplementedError("Subclasses must implement this method")


class ProjectAssistant(BaseAssistant[ProjectsAgentState]):
    def __init__(self, config: AppConfig) -> None:
        super().__init__(config)
        self.rag_service = build_rag_service(config)

    async def process_topic(self, topic: str) -> ProcessTopicAgentState:
        """Search for projects for a single topic using RAG service and LLM ranking."""
        state = ProcessTopicAgentState(topic=topic)

        # Create task inferences with the RAG service
        rag_inference = RAGServiceInference(llm=self.llm, rag_service=self.rag_service)
        llm_ranker_inference = LLMRankerInference(
            llm=self.llm, similarity_threshold=self.config.rag.similarity_threshold
        )
        project_generation_inference = ProjectGenerationInference(llm=self.llm)

        # Run RAG service inference to get candidates
        state = await rag_inference.transform(state)

        # If we have candidates, run LLM ranking
        if state.candidates:
            state = await llm_ranker_inference.transform(state)

        if not state.project:
            state = await project_generation_inference.transform(state)
            if state.project:
                await self.rag_service.save(state.topic, state.project)

        return state

    async def execute(self, state: ProjectsAgentState) -> ProjectsAgentState:
        task_inferences: List[Type[TaskInference[ProjectsAgentState]]] = [
            DefineTopicsInference,
        ]

        state = await self._run_task_inference(task_inferences, state)

        # Run parallel processing of each topic
        if state.topics:
            # Create tasks for parallel execution
            process_topic_tasks = [self.process_topic(topic) for topic in state.topics]

            # Execute all searches in parallel
            process_topic_results = await asyncio.gather(
                *process_topic_tasks, return_exceptions=True
            )

            # Update topic2project mapping with found projects or None
            for i, result in enumerate(process_topic_results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Process topic failed for topic '{state.topics[i]}': {result}"
                    )
                    continue

                if not isinstance(result, ProcessTopicAgentState):
                    logger.error(
                        f"Unexpected result type for topic '{state.topics[i]}': {type(result)}"
                    )
                    continue

                # If we have a best candidate from LLM ranking, use it, otherwise use None
                if result.project:
                    state.topic2project.append(
                        Topic2Project(topic=result.topic, project=result.project)
                    )
                else:
                    logger.error(f"Error processing topic '{result.topic}': {result}")

        return state


class FeedbackAssistant(BaseAssistant[FeedbackAgentState]):
    async def execute(self, state: FeedbackAgentState) -> FeedbackAgentState:
        task_inferences: List[Type[TaskInference[FeedbackAgentState]]] = [
            FeedbackInference,
        ]
        return await self._run_task_inference(task_inferences, state)

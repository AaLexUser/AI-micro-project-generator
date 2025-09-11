import asyncio
import logging
from typing import Generic, List, Type, TypeVar

from pydantic import BaseModel

from aipg.configs.app_config import AppConfig
from aipg.domain import (
    FeedbackAgentState,
    ProcessTopicAgentState,
    ProjectsAgentState,
    Topic2Project,
)
from aipg.llm import LLMClient
from aipg.rag.rag_builder import build_rag_service
from aipg.sandbox.builder import build_sandbox_service
from aipg.task_inference import (
    BugFixerInference,
    CheckAutotestSandboxInference,
    DefineTopicsInference,
    FeedbackInference,
    LLMRankerInference,
    ProjectGenerationInference,
    RAGServiceInference,
    TaskInference,
)
from aipg.task_inference.task_inference import (
    CheckUserSolutionSandboxInference,
    ProjectCorrectorInference,
    ProjectValidatorInference,
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
            # Special handling for inferences that require sandbox_service
            if hasattr(self, "sandbox_service") and inference_class.__name__ in [
                "CheckUserSolutionSandboxInference",
                "CheckAutotestSandboxInference",
            ]:
                inference = inference_class(
                    llm=self.llm, sandbox_service=self.sandbox_service
                )
            else:
                inference = inference_class(llm=self.llm)
            try:
                state = await inference.transform(state)
            except Exception as e:
                logger.exception("Task inference failed: %s", inference_class.__name__)
                self.handle_exception(
                    f"Task inference preprocessing: {inference_class}", e
                )
        return state

    async def execute(self, state: StateT) -> StateT:
        raise NotImplementedError("Subclasses must implement this method")


class ProjectAssistant(BaseAssistant[ProjectsAgentState]):
    def __init__(self, config: AppConfig) -> None:
        super().__init__(config)
        self.rag_service = build_rag_service(config)
        self.sandbox_service = build_sandbox_service(config)

    async def process_topic(self, topic: str) -> ProcessTopicAgentState:
        """Search for projects for a single topic using RAG service and LLM ranking."""
        state = ProcessTopicAgentState(topic=topic)

        # Create task inferences with the RAG service
        rag_inference = RAGServiceInference(llm=self.llm, rag_service=self.rag_service)
        llm_ranker_inference = LLMRankerInference(
            llm=self.llm, similarity_threshold=self.config.rag.similarity_threshold
        )
        project_generation_inference = ProjectGenerationInference(llm=self.llm)
        project_validator_inference = ProjectValidatorInference(llm=self.llm)
        project_corrector_inference = ProjectCorrectorInference(llm=self.llm)
        check_autotest_inference = CheckAutotestSandboxInference(
            llm=self.llm, sandbox_service=self.sandbox_service
        )
        bug_fixer_inference = BugFixerInference(llm=self.llm)

        # Run RAG service inference to get candidates
        state = await rag_inference.transform(state)

        # If we have candidates, run LLM ranking
        if state.candidates:
            state = await llm_ranker_inference.transform(state)

        if not state.project:
            state = await project_generation_inference.transform(state)
            if state.project:
                previous_version = state.project
                for attempt in range(1, self.config.project_correction_attempts + 1):
                    logger.info(
                        f"Project correction attempt {attempt}/{self.config.project_correction_attempts}"
                    )
                    state = await project_validator_inference.transform(state)
                    if state.validation_result and not state.validation_result.is_valid:
                        logger.info("Project validation failed, correcting...")
                        state = await project_corrector_inference.transform(state)
                        if not state.project:
                            state.project = previous_version
                            logger.info(
                                "Project correction failed, using previous version"
                            )
                            break
                    else:
                        break
                if not state.project:
                    state.project = previous_version

                # Only run final validation if we don't already have a valid result
                if not state.validation_result or not state.validation_result.is_valid:
                    logger.info("Running final validation before persisting project")
                    state = await project_validator_inference.transform(state)

                    # Check final validation result and revert if invalid
                    if (
                        not state.validation_result
                        or not state.validation_result.is_valid
                    ):
                        logger.warning(
                            "Final validation failed, reverting to previous version"
                        )
                        state.project = previous_version
                        state.validation_result = (
                            None  # Clear invalid validation result
                        )
                    else:
                        logger.info(
                            "Final validation successful, project ready for persistence"
                        )
                else:
                    logger.info(
                        "Project already validated successfully, skipping final validation"
                    )

            # Run autotest and bug fixing if project is valid
            if (
                state.project
                and state.validation_result
                and state.validation_result.is_valid
            ):
                logger.info("Project is valid, running autotest and bug fixing")

                # Run autotest to check for bugs
                state = await check_autotest_inference.transform(state)

                # Try to fix bugs if any are found
                for attempt in range(1, self.config.bug_fix_attempts + 1):
                    if state.execution_result and (
                        state.execution_result.exit_code != 0
                        or state.execution_result.timed_out
                    ):
                        logger.info(
                            f"Bugs detected, running bug fixer attempt {attempt}/{self.config.bug_fix_attempts}"
                        )
                        state = await bug_fixer_inference.transform(state)

                        # Re-run autotest to check if bugs are fixed
                        state = await check_autotest_inference.transform(state)

                        # If no more bugs, break out of the loop
                        if (
                            state.execution_result
                            and state.execution_result.exit_code == 0
                            and not state.execution_result.timed_out
                        ):
                            logger.info("All bugs fixed successfully")
                            break
                    else:
                        logger.info("No bugs detected, skipping bug fixing")
                        break
                else:
                    logger.warning(
                        f"Could not fix all bugs after {self.config.bug_fix_attempts} attempts"
                    )

            # Only save if project is present and validation passed
            if (
                state.project
                and state.validation_result
                and state.validation_result.is_valid
            ):
                await self.rag_service.save(state.topic, state.project)
                logger.info(f"Project successfully saved for topic: {state.topic}")
            elif state.project:
                logger.warning(
                    f"Project exists but validation failed, not saving for topic: {state.topic}"
                )

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
                    logger.warning(
                        f"Warning no project found for topic. Skipping '{result.topic}'"
                    )

        return state


class FeedbackAssistant(BaseAssistant[FeedbackAgentState]):
    def __init__(self, config: AppConfig) -> None:
        super().__init__(config)
        self.sandbox_service = build_sandbox_service(config)

    async def execute(self, state: FeedbackAgentState) -> FeedbackAgentState:
        task_inferences: List[Type[TaskInference[FeedbackAgentState]]] = [
            CheckUserSolutionSandboxInference,
            FeedbackInference,
        ]
        return await self._run_task_inference(task_inferences, state)

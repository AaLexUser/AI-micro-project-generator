import asyncio
import logging
import signal
import sys
import threading
from contextlib import contextmanager
from typing import Generic, List, Optional, Type, TypeVar

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


@contextmanager
def timeout(seconds: int, error_message: Optional[str] = None):
    if sys.platform == "win32":
        # Windows implementation using threading + async exception injection
        # Note: This uses CPython internals to raise an exception in the current thread.
        # It is a pragmatic solution because Windows lacks SIGALRM.
        import ctypes

        current_thread_id = threading.get_ident()

        # Configure CPython API call for safety
        _set_async_exc = ctypes.pythonapi.PyThreadState_SetAsyncExc
        _set_async_exc.argtypes = [ctypes.c_long, ctypes.py_object]
        _set_async_exc.restype = ctypes.c_int

        def _raise_timeout_in_thread():
            # Raises TimeoutError in the target thread asynchronously.
            # The message cannot be passed directly; raising bare TimeoutError instead.
            res = _set_async_exc(
                ctypes.c_long(current_thread_id), ctypes.py_object(TimeoutError)
            )
            if res == 0:
                logger.warning(
                    "timeout: failed to deliver TimeoutError to thread %s",
                    current_thread_id,
                )
            elif res > 1:
                # Revert per CPython docs
                _set_async_exc(ctypes.c_long(current_thread_id), None)
                logger.error(
                    "timeout: PyThreadState_SetAsyncExc affected multiple threads; reverted"
                )

        timer = threading.Timer(seconds, _raise_timeout_in_thread)
        timer.daemon = True
        timer.start()
        try:
            yield
        finally:
            timer.cancel()
    else:
        # Unix implementation using SIGALRM
        def handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        if threading.current_thread() is not threading.main_thread():
            raise RuntimeError("timeout(SIGALRM) must be used from the main thread")
        previous = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous)


class BaseAssistant(Generic[StateT]):
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.llm = LLMClient(config)

    def handle_exception(self, stage: str, exception: Exception):
        raise Exception(f"{stage}: {exception}")

    def _run_task_inference(
        self, task_inferences: List[Type[TaskInference]], state: StateT
    ) -> StateT:
        for inference_class in task_inferences:
            logger.debug("Running task inference: %s", inference_class.__name__)
            inference = inference_class(llm=self.llm)
            try:
                state = inference.transform(state)
            except Exception as e:
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
        state = rag_inference.transform(state)

        # If we have candidates, run LLM ranking
        if state.candidates:
            state = llm_ranker_inference.transform(state)

        if not state.project:
            state = project_generation_inference.transform(state)
            if state.project:
                self.rag_service.save(state.topic, state.project)

        return state

    async def execute(self, state: ProjectsAgentState) -> ProjectsAgentState:
        task_inferences: List[Type[TaskInference[ProjectsAgentState]]] = [
            DefineTopicsInference,
        ]

        state = self._run_task_inference(task_inferences, state)

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
                    logger.info(f"Error processing topic '{result.topic}': {result}")

        return state


class FeedbackAssistant(BaseAssistant[FeedbackAgentState]):
    async def execute(self, state: FeedbackAgentState) -> FeedbackAgentState:
        task_inferences: List[Type[TaskInference[FeedbackAgentState]]] = [
            FeedbackInference,
        ]
        return self._run_task_inference(task_inferences, state)

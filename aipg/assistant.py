import logging
import signal
import sys
import threading
from contextlib import contextmanager
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel

from aipg.configs.app_config import AppConfig
from aipg.llm import LLMClient
from aipg.state import FeedbackAgentState, ProjectAgentState
from aipg.task_inference import (
    DefineTopicsInference,
    FeedbackInference,
    ProjectGenerationInference,
    TaskInference,
)

StateT = TypeVar("StateT", bound=BaseModel)

logger = logging.getLogger(__name__)


@contextmanager
def timeout(seconds: int, error_message: Optional[str] = None):
    """
    Context manager that raises TimeoutError if the block does not complete within `seconds`.
    
    On Unix-like systems this uses SIGALRM to deliver a TimeoutError (the provided
    `error_message` is used as the exception message). Because SIGALRM is a
    process-wide signal, this implementation must be entered from the main thread
    and restores the previous SIGALRM handler on exit.
    
    On Windows this uses a background timer and CPython's internal
    PyThreadState_SetAsyncExc to asynchronously raise a bare `TimeoutError` in the
    current thread when the timer fires. Windows cannot attach a custom message to
    the injected exception; only a plain TimeoutError is raised. The timer is
    cancelled when the context exits.
    
    Parameters:
        seconds (int): Number of seconds to wait before raising TimeoutError.
        error_message (Optional[str]): Message used for the TimeoutError on Unix;
            ignored on Windows.
    
    Raises:
        RuntimeError: if invoked from a non-main thread on platforms that use SIGALRM.
        TimeoutError: when the timeout expires (raised asynchronously inside the
            managed block).
    """
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


class BaseAssistant[StateT]:
    def __init__(self, config: AppConfig) -> None:
        """
        Initialize the assistant with the given application configuration.
        
        Parameters:
            config (AppConfig): Application configuration used to configure the assistant and to instantiate its LLM client.
        """
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

    def execute(self, state: StateT) -> StateT:
        raise NotImplementedError("Subclasses must implement this method")


class ProjectAssistant(BaseAssistant[ProjectAgentState]):
    def execute(self, state: ProjectAgentState) -> ProjectAgentState:
        """
        Execute the project assistant pipeline to transform a ProjectAgentState.
        
        Runs the DefineTopicsInference followed by ProjectGenerationInference (in that order), applying each inference to the provided state and returning the resulting ProjectAgentState.
        
        Parameters:
            state (ProjectAgentState): Current project agent state to be transformed by the inference pipeline.
        
        Returns:
            ProjectAgentState: Updated state after all inferences have been applied.
        """
        task_inferences: List[Type[TaskInference[ProjectAgentState]]] = [
            DefineTopicsInference,
            ProjectGenerationInference,
        ]

        state = self._run_task_inference(task_inferences, state)

        return state


class FeedbackAssistant(BaseAssistant[FeedbackAgentState]):
    def execute(self, state: FeedbackAgentState) -> FeedbackAgentState:
        task_inferences: List[Type[TaskInference[FeedbackAgentState]]] = [
            FeedbackInference,
        ]

        state = self._run_task_inference(task_inferences, state)

        return state

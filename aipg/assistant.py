import logging
import signal
import sys
import threading
from contextlib import contextmanager
from typing import List, Optional, Type

from aipg.configs.app_config import AppConfig
from aipg.llm import LLMClient
from aipg.state import AgentState
from aipg.task_inference import (
    DefineTopicsInference,
    ProjectGenerationInference,
    TaskInference,
)

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


class Assistant:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.llm = LLMClient(config)

    def handle_exception(self, stage: str, exception: Exception):
        raise Exception(f"{stage}: {exception}")

    def _run_task_inference(
        self, task_inferences: List[Type[TaskInference]], state: AgentState
    ) -> AgentState:
        for inference_class in task_inferences:
            logger.debug("Running task inference: %s", inference_class.__name__)
            inference = inference_class(llm=self.llm)
            try:
                with timeout(
                    seconds=self.config.task_timeout,
                    error_message=f"Task inference preprocessing time out: {inference_class}",
                ):
                    state = inference.transform(state)
            except Exception as e:
                self.handle_exception(
                    f"Task inference preprocessing: {inference_class}", e
                )
        return state

    def execute(self, state: AgentState) -> AgentState:
        task_inferences: List[Type[TaskInference]] = [
            DefineTopicsInference,
            ProjectGenerationInference,
        ]

        state = self._run_task_inference(task_inferences, state)

        return state

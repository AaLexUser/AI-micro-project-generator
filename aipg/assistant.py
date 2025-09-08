import logging
import signal
import sys
import threading
from contextlib import contextmanager
from typing import List, Optional, Type

from aipg.configs.app_config import AppConfig
from aipg.llm import LLMClient
from aipg.state import AgentState
from aipg.task_inference import ProjectGenerationInference, TaskInference

logger = logging.getLogger(__name__)


@contextmanager
def timeout(seconds: int, error_message: Optional[str] = None):
    if sys.platform == "win32":
        # Windows implementation using threading
        timer = threading.Timer(
            seconds, lambda: (_ for _ in ()).throw(TimeoutError(error_message))
        )
        timer.start()
        try:
            yield
        finally:
            timer.cancel()
    else:
        # Unix impementation using SIGALRM
        def handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)


class Assistant:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.llm = LLMClient(config)

    def handle_exception(self, stage: str, exception: Exception):
        raise Exception(str(exception), stage)

    def _run_task_inference(
        self, task_inferences: List[Type[TaskInference]], state: AgentState
    ):
        for inference_class in task_inferences:
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

    def execute(self, state: AgentState) -> AgentState:
        task_inferences: List[Type[TaskInference]] = [
            ProjectGenerationInference,
        ]

        self._run_task_inference(task_inferences, state)

        return state

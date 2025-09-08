import logging
import signal
import sys
import threading
from contextlib import contextmanager
from typing import List, Optional, Type

from aipg.configs.app_config import AppConfig
from aipg.llm import LLMClient
from aipg.task import Task
from aipg.task_inference import MicroProjectGenerationInference, TaskInference

logger = logging.getLogger(__name__)


@contextmanager
def timeout(seconds: int, error_message: Optional[str] = None):
    # Use signal-based timeout only on Unix main thread. Otherwise, fall back to threading.Timer
    use_threading_timer = (
        sys.platform == "win32"
        or threading.current_thread() is not threading.main_thread()
    )

    if use_threading_timer:
        timer = threading.Timer(
            seconds, lambda: (_ for _ in ()).throw(TimeoutError(error_message))
        )
        timer.start()
        try:
            yield
        finally:
            timer.cancel()
    else:
        # Unix implementation using SIGALRM on main thread only
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
        self, task_inferences: List[Type[TaskInference]], task: Task
    ):
        for inference_class in task_inferences:
            inference = inference_class(llm=self.llm)
            try:
                with timeout(
                    seconds=self.config.task_timeout,
                    error_message=f"Task inference preprocessing time out: {inference_class}",
                ):
                    task = inference.transform(task)
            except Exception as e:
                self.handle_exception(
                    f"Task inference preprocessing: {inference_class}", e
                )

    def generate_project(self, task: Task) -> Task:
        task_inferences: List[Type[TaskInference]] = [
            MicroProjectGenerationInference,
        ]

        self._run_task_inference(task_inferences, task)

        return task

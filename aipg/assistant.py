from __future__ import annotations

import logging
import signal
import sys
import threading
from contextlib import contextmanager
from typing import List, Optional, Type

from aipg.configs.app_config import AppConfig
from aipg.task import Task

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
    def __init__(self, config: AppConfig, rag_service: Optional[object] = None) -> None:
        self.config = config
        self.llm = None  # Lazy initialize to avoid heavy imports
        self.rag = rag_service

    def handle_exception(self, stage: str, exception: Exception):
        raise Exception(str(exception), stage)

    def _run_task_inference(
        self, task_inferences: List[Type[object]], task: Task
    ):
        class _LLMProxy:
            def __init__(self, ensure_llm):
                self._ensure_llm = ensure_llm

            def __getattr__(self, item):
                return getattr(self._ensure_llm(), item)

        for inference_class in task_inferences:
            inference = inference_class(llm=_LLMProxy(self._ensure_llm))
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

    def _ensure_llm(self):
        if self.llm is None:
            from aipg.llm import LLMClient

            self.llm = LLMClient(self.config)
        return self.llm

    def _ensure_rag(self):
        if self.rag is None:
            llm = self._ensure_llm()
            from aipg.rag.integration import build_rag_service

            self.rag = build_rag_service(self.config, llm)
        return self.rag

    def generate_project(self, task: Task) -> Task:
        # 1) Try RAG retrieval first
        try:
            rag = self._ensure_rag()
            retrieved = rag.retrieve(task.issue.description)  # type: ignore[attr-defined]
        except Exception:
            retrieved = None

        if retrieved:
            # Parse and set task fields
            from aipg.prompting.utils import parse_and_check_json
            from aipg.prompting.prompt_generator import (
                MicroTaskGenerationPromptGenerator,
            )

            parsed = parse_and_check_json(
                retrieved, expected_keys=MicroTaskGenerationPromptGenerator.fields
            )
            for k, v in parsed.items():
                setattr(task, k, v)
            return task

        # 2) Generate via LLM
        # Lazy import to allow test monkeypatching and avoid heavy imports at module load
        from aipg import task_inference as ti_mod

        task_inferences: List[Type[object]] = [
            ti_mod.MicroProjectGenerationInference,
        ]
        self._run_task_inference(task_inferences, task)

        # 3) Save generated to RAG
        try:
            rag = self._ensure_rag()
            import json

            micro_project_json = json.dumps(
                {
                    "task_description": task.task_description or "",
                    "task_goal": task.task_goal or "",
                    "expert_solution": task.expert_solution or "",
                }
            )
            rag.save(task.issue.description, micro_project_json)  # type: ignore[attr-defined]
        except Exception:
            pass

        return task

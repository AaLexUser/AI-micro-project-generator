from __future__ import annotations

from typing import Optional

from aipg.assistant import Assistant
from aipg.configs.app_config import AppConfig
from aipg.task import Task


class FakeRag:
    def __init__(self, retrieved: Optional[str] = None):
        self.retrieved = retrieved
        self.saved = []

    def retrieve(self, issue: str) -> Optional[str]:
        return self.retrieved

    def save(self, issue: str, micro_project: str) -> None:
        self.saved.append((issue, micro_project))


def test_assistant_uses_rag_when_available():
    # retrieved JSON
    mp = '{"task_description":"A","task_goal":"B","expert_solution":"C"}'
    assistant = Assistant(AppConfig(), rag_service=FakeRag(retrieved=mp))
    task = Task("Some issue")
    out = assistant.generate_project(task)
    assert out.task_description == "A"
    assert out.task_goal == "B"
    assert out.expert_solution == "C"


def test_assistant_generates_and_saves_when_not_found(monkeypatch):
    # Force LLM inference to be a no-op by mocking transform flow
    # We patch MicroProjectGenerationInference to avoid external LLM calls
    from aipg import task_inference as ti_mod

    class DummyInference(ti_mod.TaskInference):
        def transform(self, task: Task) -> Task:  # type: ignore[override]
            task.task_description = "X"
            task.task_goal = "Y"
            task.expert_solution = "Z"
            return task

    monkeypatch.setattr(ti_mod, "MicroProjectGenerationInference", DummyInference)

    fake_rag = FakeRag(retrieved=None)
    assistant = Assistant(AppConfig(), rag_service=fake_rag)
    task = Task("Different issue")
    out = assistant.generate_project(task)
    assert out.task_description == "X"
    assert fake_rag.saved, "Generated project should be saved in RAG"


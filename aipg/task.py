from dataclasses import dataclass


@dataclass
class Issue:
    description: str


@dataclass
class MicroProject:
    description: str
    solution: str


class Task:
    """This is task for AI Assistant"""

    def __init__(self, issue_description: str):
        self.issue = Issue(description=issue_description)

        self.task_description: str | None = None
        self.task_goal: str | None = None
        self.expert_solution: str | None = None

    @property
    def micro_project(self) -> MicroProject:
        return self.micro_project

    @micro_project.setter
    def micro_project(self, description: str, solution: str):
        self.micro_project = MicroProject(description=description, solution=solution)

    def __repr__(self):
        return f"Task(task_description={self.task_description}, task_goal={self.task_goal}, expert_solution={self.expert_solution})"

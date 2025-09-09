# ai_micro_project_generator/repos_sqlalchemy.py
from __future__ import annotations
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import update

from model.models import Student, Task, StudentsTask


class SAStudentRepo:
    def __init__(self, s: Session):
        self.s = s

    def get(self, student_id: int) -> Optional[Student]:
        return self.s.get(Student, student_id)

    def create(self) -> Student:
        obj = Student()
        self.s.add(obj)
        # id появится после flush/commit
        return obj

    def assign_task(self, student_id: int, task_id: int) -> StudentsTask:
        # не дублируем
        link = self.s.get(StudentsTask, {"stud_id": student_id, "task_id": task_id})
        if link:
            return link
        link = StudentsTask(stud_id=student_id, task_id=task_id)
        self.s.add(link)
        return link

    def mark_finished(
        self, student_id: int, task_id: int, when: Optional[datetime] = None
    ) -> None:
        when = when or datetime.utcnow()
        stmt = (
            update(StudentsTask)
            .where(StudentsTask.stud_id == student_id, StudentsTask.task_id == task_id)
            .values(finished_at=when)
        )
        self.s.execute(stmt)

    def list_tasks(self, student_id: int, open_only: bool = False) -> List[Task]:
        # через join ассоциации
        q = (
            self.s.query(Task)
            .join(StudentsTask, StudentsTask.task_id == Task.id)
            .filter(StudentsTask.stud_id == student_id)
        )
        if open_only:
            q = q.filter(StudentsTask.finished_at.is_(None))
        return q.all()


class SATaskRepo:
    def __init__(self, s: Session):
        self.s = s

    def get(self, task_id: int) -> Optional[Task]:
        return self.s.get(Task, task_id)

    def create(
        self,
        *,
        description: str,
        project_description: str | None = None,
        solution: str | None = None,
        tests: str | None = None,
    ) -> Task:
        obj = Task(
            description=description,
            project_description=project_description,
            solution=solution,
            tests=tests,
        )
        self.s.add(obj)
        return obj

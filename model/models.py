# ai_micro_project_generator/models.py
from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Text, ForeignKey, UniqueConstraint, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.db_config import Base


class StudentsTask(Base):
    """
    Ассоциация Student<->Task с доп.полями.
    PK составной (stud_id, task_id), чтобы одна и та же задача
    не дублировалась одному студенту.
    """

    __tablename__ = "students_task"
    __table_args__ = (UniqueConstraint("stud_id", "task_id", name="uq_students_task"),)

    stud_id: Mapped[int] = mapped_column(ForeignKey("students.id"), primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # связи к концам
    student: Mapped["Student"] = relationship(back_populates="links")
    task: Mapped["Task"] = relationship(back_populates="links")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # связь с ассоциацией
    links: Mapped[List[StudentsTask]] = relationship(
        back_populates="student",
        cascade="all, delete-orphan",
    )

    # удобная "виртуальная" M2M без полей (только чтение)
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        secondary="students_task",
        viewonly=True,
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    project_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tests: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON-строка или текст

    links: Mapped[List[StudentsTask]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )

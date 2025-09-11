from pydantic import BaseModel, ConfigDict, Field, field_validator

from aipg.sandbox.domain import SandboxResult


class ProjectValidationCheck(BaseModel):
    rule_id: str
    passed: bool
    comment: str


class ProjectValidationResult(BaseModel):
    is_valid: bool
    checks: list[ProjectValidationCheck]


class Project(BaseModel):
    raw_markdown: str
    topic: str
    goal: str
    description: str
    input_data: str
    expected_output: str
    expert_solution: str
    autotest: str


class Topic2Project(BaseModel):
    topic: str
    project: Project | None = Field(default=None)


class ProjectsAgentState(BaseModel):
    comments: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    topic2project: list[Topic2Project] = Field(default_factory=list)

    # Ensure validators run on attribute assignment as well
    model_config = ConfigDict(validate_assignment=True)

    @field_validator("topics", mode="after")
    def _ensure_unique_topics(cls, topics: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_topics: list[str] = []
        for topic in topics:
            if topic not in seen:
                seen.add(topic)
                unique_topics.append(topic)
        return unique_topics

    @field_validator("topic2project", mode="after")
    def _ensure_unique_topic2project(
        cls, items: list[Topic2Project]
    ) -> list[Topic2Project]:
        seen_topics: set[str] = set()
        unique_items: list[Topic2Project] = []
        for item in items:
            if item.topic not in seen_topics:
                seen_topics.add(item.topic)
                unique_items.append(item)
        return unique_items


class ProcessTopicAgentState(BaseModel):
    topic: str
    candidates: list[Topic2Project] = Field(default_factory=list)
    project: Project | None = Field(default=None)
    validation_result: ProjectValidationResult | None = Field(default=None)
    execution_result: SandboxResult | None = Field(default=None)


class FeedbackAgentState(BaseModel):
    user_solution: str
    project: Project
    feedback: str = ""
    execution_result: SandboxResult | None = Field(default=None)

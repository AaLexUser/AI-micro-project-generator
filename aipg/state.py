from pydantic import BaseModel, Field


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


class ProcessTopicAgentState(BaseModel):
    topic: str
    candidates: list[Topic2Project] = Field(default_factory=list)
    project: Project | None = Field(default=None)


class FeedbackAgentState(BaseModel):
    user_solution: str
    project: Project
    feedback: str = ""

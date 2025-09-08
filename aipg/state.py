from dataclasses import dataclass, field

@dataclass
class Project:
    topic: str | None = None
    description: str | None = None
    
    def __repr__(self):
        return f"Project(topic={self.topic}, description={self.description})"

@dataclass
class AgentState:
    comments: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    projects: list[Project] = field(default_factory=list)
    
    def __repr__(self):
        return f"AgentState(comments={self.comments}, topics={self.topics}, projects={self.projects})"

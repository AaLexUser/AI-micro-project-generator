import logging
from typing import List, Optional

import uvicorn  # type: ignore[import-not-found]
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aipg.assistant import FeedbackAssistant, ProjectAssistant
from aipg.configs.app_config import AppConfig
from aipg.configs.loader import load_config
from aipg.state import FeedbackAgentState, Project, ProjectAgentState

logger = logging.getLogger(__name__)

app = FastAPI(title="AI Micro Project Generator API", version="0.1.0")

# Enable CORS for local development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    comments: List[str]
    presets: Optional[str] = None
    config_path: Optional[str] = None
    overrides: Optional[List[str]] = None


class ProjectResponse(Project):
    pass


class FeedbackRequest(BaseModel):
    project: Project
    user_solution: str
    config_path: Optional[str] = None
    overrides: Optional[List[str]] = None


class FeedbackResponse(BaseModel):
    feedback: str


def _generate_projects(
    comments: List[str],
    presets: Optional[str] = None,
    config_path: Optional[str] = None,
    overrides: Optional[List[str]] = None,
) -> List[Project]:
    config: AppConfig = load_config(
        presets=presets,
        config_path=config_path,
        overrides=overrides,
        schema=AppConfig,
    )
    assistant = ProjectAssistant(config)
    state = ProjectAgentState(comments=comments)
    state = assistant.execute(state)
    projects: List[Project] = [
        item.project for item in state.topic2project if item.project is not None
    ]
    return projects


def _generate_feedback(
    project: Project,
    user_solution: str,
    config_path: Optional[str] = None,
    overrides: Optional[List[str]] = None,
) -> str:
    config: AppConfig = load_config(
        config_path=config_path,
        overrides=overrides,
        schema=AppConfig,
    )
    assistant = FeedbackAssistant(config)
    state = FeedbackAgentState(user_solution=user_solution, project=project)
    state = assistant.execute(state)
    return state.feedback


@app.post("/projects", response_model=List[ProjectResponse])
def generate_projects(payload: GenerateRequest):
    try:
        return _generate_projects(
            comments=payload.comments,
            overrides=payload.overrides,
        )
    except Exception as e:
        logger.exception("Failed to generate projects")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback", response_model=FeedbackResponse)
def generate_feedback(payload: FeedbackRequest):
    try:
        feedback = _generate_feedback(
            project=payload.project,
            user_solution=payload.user_solution,
            overrides=payload.overrides,
        )
        return FeedbackResponse(feedback=feedback)
    except Exception as e:
        logger.exception("Failed to generate feedback")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def main():
    uvicorn.run("aipg.api:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    main()

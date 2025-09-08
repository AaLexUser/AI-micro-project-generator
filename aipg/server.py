import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from aipg.assistant import Assistant
from aipg.configs.app_config import AppConfig
from aipg.configs.loader import load_config
from aipg.task import Task


logger = logging.getLogger(__name__)


class GenerateRequest(BaseModel):
    issue: str
    presets: Optional[str] = None
    config_path: Optional[str] = None
    config_overrides: Optional[list[str]] = None


class GenerateResponse(BaseModel):
    task_description: Optional[str]
    task_goal: Optional[str]
    expert_solution: Optional[str]
    raw: Dict[str, Any]


def create_app() -> FastAPI:
    app = FastAPI(title="AI Micro-Project Generator API")

    @app.get("/healthz")
    def healthz() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/generate", response_model=GenerateResponse)
    def generate(req: GenerateRequest) -> GenerateResponse:
        try:
            config = load_config(
                presets=req.presets,
                config_path=req.config_path,
                overrides=req.config_overrides,
                schema=AppConfig,
            )
            assistant = Assistant(config)
            task = Task(issue_description=req.issue)
            task = assistant.generate_project(task)
            return GenerateResponse(
                task_description=task.task_description,
                task_goal=task.task_goal,
                expert_solution=task.expert_solution,
                raw={
                    "issue": task.issue.description,
                    "task_description": task.task_description,
                    "task_goal": task.task_goal,
                    "expert_solution": task.expert_solution,
                },
            )
        except Exception as e:
            logger.exception("Failed to generate micro-project")
            raise HTTPException(status_code=500, detail=str(e))

    return app


def main() -> None:
    import uvicorn

    uvicorn.run(
        "aipg.server:create_app",
        host="0.0.0.0",
        port=8000,
        factory=True,
        reload=True,
    )


app = create_app()



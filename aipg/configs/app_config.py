from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from aipg.constants import PACKAGE_PATH


class CachingConfig(BaseModel):
    enabled: bool = True
    dir_path: str = Field(default=str(Path(PACKAGE_PATH) / "cache"))


class LLMConfig(BaseModel):
    model_name: str = "openai/gpt-4o"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    caching: CachingConfig = Field(default_factory=CachingConfig)
    max_completion_tokens: Optional[int] = None
    temperature: Optional[float] = None
    extra_headers: Dict[str, Any] = Field(default_factory=dict)
    completion_params: Dict[str, Any] = Field(default_factory=dict)


class LangfuseConfig(BaseModel):
    host: str = "https://cloud.langfuse.com"
    public_key: Optional[str] = None
    secret_key: Optional[str] = None


class RagConfig(BaseModel):
    similarity_threshold: float = 0.7
    k_candidates: int = 5
    collection_name: str = "micro_projects"
    chroma_path: str = Field(default=str(Path(PACKAGE_PATH) / "cache" / "chroma"))
    embedding_model: str = "gemini-embedding-001"
    embedding_base_url: Optional[str] = None
    embedding_api_key: Optional[str] = None


class SandboxConfig(BaseModel):
    docker_image: str = "python:3.12-alpine"
    memory_limit: str = "128m"
    cpu_quota: Optional[float] = 0.5
    pids_limit: int = 128
    default_timeout_seconds: int = 5


class AppConfig(BaseModel):
    llm: LLMConfig = Field(default_factory=LLMConfig)
    langfuse: LangfuseConfig = Field(default_factory=LangfuseConfig)
    task_timeout: int = 3600
    time_limit: int = 14400
    project_correction_attempts: int = 3
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    rag: RagConfig = RagConfig()
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)

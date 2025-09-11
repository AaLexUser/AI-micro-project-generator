"""Builder for creating sandbox services with configuration."""

from __future__ import annotations

import os
from aipg.configs.app_config import AppConfig
from aipg.sandbox.adapters import DockerPythonRunner, ComposeDockerRunner
from aipg.sandbox.ports import SandboxRunner
from aipg.sandbox.service import PythonSandboxService


def build_sandbox_service(config: AppConfig) -> PythonSandboxService:
    """Build a configured sandbox service.

    Args:
        config: Application configuration containing sandbox settings.

    Returns:
        Configured PythonSandboxService instance.
    """
    # Use ComposeDockerRunner if we're in a Docker Compose environment
    # (detected by checking if ENVIRONMENT is set to development/production)
    environment = os.getenv("ENVIRONMENT", "").lower()
    runner: SandboxRunner
    if environment in ("development", "production"):
        runner = ComposeDockerRunner(
            container_name="ai-micro-project-generator-sandbox-1",
            default_timeout_seconds=config.sandbox.default_timeout_seconds,
        )
    else:
        # Fall back to DockerPythonRunner for standalone usage
        runner = DockerPythonRunner(config=config.sandbox)

    return PythonSandboxService(
        runner=runner, default_timeout_seconds=config.sandbox.default_timeout_seconds
    )

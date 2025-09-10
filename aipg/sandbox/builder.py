"""Builder for creating sandbox services with configuration."""

from __future__ import annotations

from aipg.configs.app_config import AppConfig
from aipg.sandbox.adapters import DockerPythonRunner
from aipg.sandbox.service import PythonSandboxService


def build_sandbox_service(config: AppConfig) -> PythonSandboxService:
    """Build a configured sandbox service.

    Args:
        config: Application configuration containing sandbox settings.

    Returns:
        Configured PythonSandboxService instance.
    """
    runner = DockerPythonRunner(config=config.sandbox)
    return PythonSandboxService(
        runner=runner, default_timeout_seconds=config.sandbox.default_timeout_seconds
    )

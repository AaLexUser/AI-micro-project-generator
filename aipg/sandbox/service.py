from __future__ import annotations

from typing import Optional

from .domain import SandboxResult
from .ports import SandboxRunner


class PythonSandboxService:
    """Application service that coordinates sandboxed Python execution.

    This service treats the runner as a port and performs minimal validation,
    delegating execution details to the adapter.
    """

    def __init__(self, runner: SandboxRunner, default_timeout_seconds: int = 5) -> None:
        self._runner = runner
        self._default_timeout_seconds = default_timeout_seconds

    async def run_code(
        self,
        code: str,
        input_data: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ) -> SandboxResult:
        if not isinstance(code, str) or code.strip() == "":
            raise ValueError("code must be a non-empty string")

        effective_timeout = (
            self._default_timeout_seconds
            if timeout_seconds is None
            else int(timeout_seconds)
        )

        return await self._runner.run(
            code=code, input_data=input_data, timeout_seconds=effective_timeout
        )

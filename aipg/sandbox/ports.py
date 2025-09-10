from __future__ import annotations

from typing import Optional, Protocol

from .domain import SandboxResult


class SandboxRunner(Protocol):
    def run(
        self, code: str, input_data: Optional[str], timeout_seconds: int
    ) -> SandboxResult: ...

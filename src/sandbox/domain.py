from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SandboxError(Exception):
    """Base exception for sandbox domain errors."""


class InvalidSandboxInput(SandboxError):
    """Raised when input parameters are invalid."""


@dataclass(frozen=True)
class SandboxSpec:
    python_version: str
    # Optional requirements content to include in the sandbox image
    requirements_txt: str | None = None


class SandboxSaverPort(Protocol):
    def save(self, spec: SandboxSpec) -> str:
        """Save a Python sandbox and return an identifier/reference.

        Implementations may build and store a Docker image or other artifact.
        """
        ...


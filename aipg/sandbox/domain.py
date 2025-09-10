from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False


class SandboxError(Exception):
    """Base exception for sandbox errors."""


class SandboxTimeoutError(SandboxError):
    """Raised when the sandboxed execution times out."""


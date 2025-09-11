from __future__ import annotations

from .domain import SandboxSpec, SandboxSaverPort, InvalidSandboxInput


def save_python_sandbox(spec: SandboxSpec, saver: SandboxSaverPort) -> str:
    """Use case to save a Python sandbox using the provided saver port.

    Validates input minimally and delegates to the saver port.
    """
    if not spec.python_version or not isinstance(spec.python_version, str):
        raise InvalidSandboxInput()
    return saver.save(spec)


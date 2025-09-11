from __future__ import annotations

import asyncio
import base64
import contextlib
import subprocess
import uuid
from typing import Optional

from aipg.configs.app_config import SandboxConfig

from .domain import SandboxResult
from .ports import SandboxRunner


class DockerPythonRunner(SandboxRunner):
    """Run untrusted Python code inside a Docker container with strict limits.

    This adapter intentionally avoids the Docker SDK to reduce dependencies and
    uses the `docker` CLI instead. It sets conservative defaults and supports
    passing stdin to the containerized process.
    """

    def __init__(
        self,
        config: Optional[SandboxConfig] = None,
        image: Optional[str] = None,
        memory_limit: Optional[str] = None,
        cpu_quota: Optional[float] = None,
        pids_limit: Optional[int] = None,
        default_timeout_seconds: Optional[int] = None,
    ) -> None:
        # Use config if provided, otherwise fall back to individual parameters or defaults
        if config is not None:
            self._image = config.docker_image
            self._memory_limit = config.memory_limit
            self._cpu_quota = config.cpu_quota
            self._pids_limit = config.pids_limit
            self._default_timeout_seconds = config.default_timeout_seconds
        else:
            # Fallback to individual parameters or defaults for backward compatibility
            self._image = image or "aipg-sandbox:latest"
            self._memory_limit = memory_limit or "128m"
            self._cpu_quota = cpu_quota if cpu_quota is not None else 0.5
            self._pids_limit = pids_limit or 128
            self._default_timeout_seconds = default_timeout_seconds or 5

    async def run(
        self, code: str, input_data: Optional[str], timeout_seconds: int
    ) -> SandboxResult:
        encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")
        container_name = f"py-sbx-{uuid.uuid4().hex[:12]}"

        # Compose a safe command that decodes and executes the user code.
        python_cmd = (
            "python - <<'PY'\n"
            'import base64,sys; exec(base64.b64decode("'
            + encoded
            + "\").decode('utf-8'))\n"
            "PY"
        )

        shell_cmd = [
            "sh",
            "-lc",
            python_cmd,
        ]

        # Build docker run command with strict isolation flags
        docker_cmd = [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--cpus",
            str(self._cpu_quota if self._cpu_quota is not None else 1),
            "--memory",
            self._memory_limit,
            "--pids-limit",
            str(self._pids_limit),
            "--security-opt",
            "no-new-privileges:true",
            "--user",
            "65534:65534",  # nobody
            self._image,
        ] + shell_cmd

        # Use asyncio subprocess to avoid blocking the event loop
        try:
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=(input_data or "").encode("utf-8")),
                    timeout=(
                        timeout_seconds
                        if timeout_seconds is not None
                        else self._default_timeout_seconds
                    ),
                )
                exit_code = await process.wait()
                return SandboxResult(
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    exit_code=exit_code,
                    timed_out=False,
                )
            except asyncio.TimeoutError:  # pragma: no cover - depends on timing
                with contextlib.suppress(Exception):
                    process.kill()
                    await process.wait()
                self._force_remove(container_name)
                return SandboxResult(
                    stdout="",
                    stderr="",
                    exit_code=124,
                    timed_out=True,
                )
        except Exception:
            # In case docker is not available or other runtime error
            return SandboxResult(
                stdout="",
                stderr="docker execution failed",
                exit_code=1,
                timed_out=False,
            )

    def _force_remove(self, name: str) -> None:
        try:
            subprocess.run(
                ["docker", "rm", "-f", name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            # Best-effort cleanup
            pass


class ComposeDockerRunner(SandboxRunner):
    """Run untrusted Python code in the existing sandbox container via docker exec.

    This runner is designed for Docker Compose environments where a sandbox
    container is already running and we need to execute code inside it using
    docker exec instead of spawning new containers.
    """

    def __init__(
        self,
        container_name: str = "ai-micro-project-generator-sandbox-1",
        default_timeout_seconds: int = 5,
    ) -> None:
        self._container_name = container_name
        self._default_timeout_seconds = default_timeout_seconds

    async def run(
        self, code: str, input_data: Optional[str], timeout_seconds: int
    ) -> SandboxResult:
        # Encode the code to avoid shell injection issues
        encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")

        # Create a safe command that decodes and executes the user code
        python_cmd = f"python -c \"import base64; exec(base64.b64decode('{encoded}').decode('utf-8'))\""

        # Use docker exec to run code in the existing sandbox container
        docker_cmd = [
            "docker",
            "exec",
            "-i",  # Interactive for stdin
            "--user",
            "sandbox",  # Use sandbox user
            self._container_name,
            "sh",
            "-c",
            python_cmd,
        ]

        try:
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=(input_data or "").encode("utf-8")),
                    timeout=timeout_seconds or self._default_timeout_seconds,
                )
                exit_code = await process.wait()
                return SandboxResult(
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    exit_code=exit_code,
                    timed_out=False,
                )
            except asyncio.TimeoutError:
                with contextlib.suppress(Exception):
                    process.kill()
                    await process.wait()
                return SandboxResult(
                    stdout="",
                    stderr="Execution timed out",
                    exit_code=124,
                    timed_out=True,
                )
        except Exception as e:
            return SandboxResult(
                stdout="",
                stderr=f"docker exec failed: {str(e)}",
                exit_code=1,
                timed_out=False,
            )

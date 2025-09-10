from __future__ import annotations

import base64
import shlex
import subprocess
import sys
import uuid
from typing import Optional

from .domain import SandboxResult, SandboxTimeoutError
from .ports import SandboxRunner


class DockerPythonRunner(SandboxRunner):
    """Run untrusted Python code inside a Docker container with strict limits.

    This adapter intentionally avoids the Docker SDK to reduce dependencies and
    uses the `docker` CLI instead. It sets conservative defaults and supports
    passing stdin to the containerized process.
    """

    def __init__(
        self,
        image: str = "python:3.12-alpine",
        memory_limit: str = "128m",
        cpu_quota: Optional[float] = 0.5,
        pids_limit: int = 128,
        default_timeout_seconds: int = 5,
    ) -> None:
        self._image = image
        self._memory_limit = memory_limit
        self._cpu_quota = cpu_quota
        self._pids_limit = pids_limit
        self._default_timeout_seconds = default_timeout_seconds

    def run(self, code: str, input_data: Optional[str], timeout_seconds: int) -> SandboxResult:
        encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")
        container_name = f"py-sbx-{uuid.uuid4().hex[:12]}"

        # Compose a safe command that decodes and executes the user code.
        python_cmd = (
            "python - <<'PY'\n"
            "import base64,sys; exec(base64.b64decode(\"" + encoded + "\").decode('utf-8'))\n"
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

        try:
            completed = subprocess.run(
                docker_cmd,
                input=(input_data or "").encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds or self._default_timeout_seconds,
                check=False,
            )
            return SandboxResult(
                stdout=completed.stdout.decode("utf-8", errors="replace"),
                stderr=completed.stderr.decode("utf-8", errors="replace"),
                exit_code=completed.returncode,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as exc:  # pragma: no cover - depends on timing
            self._force_remove(container_name)
            return SandboxResult(
                stdout=(exc.stdout or b"").decode("utf-8", errors="replace"),
                stderr=(exc.stderr or b"").decode("utf-8", errors="replace"),
                exit_code=124,
                timed_out=True,
            )

    def _force_remove(self, name: str) -> None:
        try:
            subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            # Best-effort cleanup
            pass


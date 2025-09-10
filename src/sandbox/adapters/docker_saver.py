from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path

from ..domain import SandboxSpec, SandboxSaverPort, SandboxError


class DockerSandboxSaver(SandboxSaverPort):
    def __init__(self, docker_binary: str = "docker", image_repo: str = "sandbox"):
        self.docker_binary = docker_binary
        self.image_repo = image_repo

    def save(self, spec: SandboxSpec) -> str:
        try:
            ref = self._build_ref(spec)
            with self._build_context(spec) as ctx_dir:
                self._docker_build(ctx_dir, ref)
            return ref
        except subprocess.CalledProcessError as exc:
            raise SandboxError() from exc

    def _build_ref(self, spec: SandboxSpec) -> str:
        hasher = hashlib.sha256()
        hasher.update(spec.python_version.encode())
        if spec.requirements_txt:
            hasher.update(spec.requirements_txt.encode())
        digest = hasher.hexdigest()[:12]
        return f"{self.image_repo}:py{spec.python_version}-{digest}"

    def _build_context(self, spec: SandboxSpec):
        class _Tmp:
            def __init__(self, path: str):
                self.path = path

            def __enter__(self):
                return self.path

            def __exit__(self, exc_type, exc, tb):
                try:
                    for root, dirs, files in os.walk(self.path, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(self.path)
                except FileNotFoundError:
                    pass

        tmp_dir = tempfile.mkdtemp(prefix="sandbox-build-")
        path = Path(tmp_dir)
        dockerfile = path / "Dockerfile"
        base = f"python:{spec.python_version}-slim"
        dockerfile.write_text(
            f"FROM {base}\nWORKDIR /app\nCOPY requirements.txt /app/requirements.txt\nRUN python -m pip install --no-cache-dir --upgrade pip && \\\n+    if [ -s /app/requirements.txt ]; then pip install --no-cache-dir -r /app/requirements.txt; fi\n",
            encoding="utf-8",
        )
        (path / "requirements.txt").write_text(spec.requirements_txt or "", encoding="utf-8")
        return _Tmp(tmp_dir)

    def _docker_build(self, ctx_dir: str, ref: str) -> None:
        subprocess.run(
            [self.docker_binary, "build", "-t", ref, ctx_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


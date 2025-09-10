import os
import shutil
import subprocess

import pytest


pytestmark = pytest.mark.integration


def _docker_available() -> bool:
    return shutil.which("docker") is not None and os.access(shutil.which("docker"), os.X_OK)


@pytest.mark.skipif(not _docker_available(), reason="Docker CLI not available")
def test_docker_runner_executes_basic_code():
    from aipg.sandbox.adapters import DockerPythonRunner
    from aipg.sandbox.service import PythonSandboxService

    service = PythonSandboxService(runner=DockerPythonRunner(), default_timeout_seconds=5)
    result = service.run_code("print('ok')")
    assert result.exit_code == 0
    assert "ok" in result.stdout


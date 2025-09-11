import os
import shutil

import pytest

pytestmark = pytest.mark.integration


def _docker_available() -> bool:
    docker_path = shutil.which("docker")
    return docker_path is not None and os.access(docker_path, os.X_OK)


@pytest.mark.skipif(not _docker_available(), reason="Docker CLI not available")
async def test_docker_runner_executes_basic_code():
    from aipg.sandbox.adapters import DockerPythonRunner
    from aipg.sandbox.service import PythonSandboxService

    service = PythonSandboxService(
        runner=DockerPythonRunner(), default_timeout_seconds=5
    )
    result = await service.run_code("print('ok')")
    assert result.exit_code == 0
    assert "ok" in result.stdout

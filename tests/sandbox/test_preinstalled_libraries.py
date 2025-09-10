import os
import shutil
import subprocess

import pytest

from aipg.configs.app_config import AppConfig, SandboxConfig

pytestmark = pytest.mark.integration


def _docker_available() -> bool:
    docker_path = shutil.which("docker")
    return docker_path is not None and os.access(docker_path, os.X_OK)


def _custom_image_available() -> bool:
    """Check if the custom sandbox image is available."""
    if not _docker_available():
        return False
    try:
        result = subprocess.run(
            ["docker", "images", "-q", "aipg-sandbox:latest"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        return False


@pytest.mark.skipif(not _docker_available(), reason="Docker CLI not available")
@pytest.mark.skipif(
    not _custom_image_available(), reason="Custom sandbox image not built"
)
def test_preinstalled_libraries_available():
    """Test that preinstalled libraries (pandas, numpy, torch) are available in the custom image."""
    from aipg.sandbox.builder import build_sandbox_service

    # Arrange: create config with custom image
    sandbox_config = SandboxConfig(
        docker_image="aipg-sandbox:latest", default_timeout_seconds=10
    )
    config = AppConfig(sandbox=sandbox_config)
    service = build_sandbox_service(config)

    # Test pandas
    result = service.run_code(
        "import pandas as pd; print('pandas version:', pd.__version__)"
    )
    assert result.exit_code == 0
    assert "pandas version:" in result.stdout

    # Test numpy
    result = service.run_code(
        "import numpy as np; print('numpy version:', np.__version__)"
    )
    assert result.exit_code == 0
    assert "numpy version:" in result.stdout

    # Test torch
    result = service.run_code(
        "import torch; print('torch version:', torch.__version__)"
    )
    assert result.exit_code == 0
    assert "torch version:" in result.stdout


@pytest.mark.skipif(not _docker_available(), reason="Docker CLI not available")
@pytest.mark.skipif(
    not _custom_image_available(), reason="Custom sandbox image not built"
)
def test_preinstalled_libraries_functionality():
    """Test that preinstalled libraries work correctly."""
    from aipg.sandbox.builder import build_sandbox_service

    # Arrange: create config with custom image
    sandbox_config = SandboxConfig(
        docker_image="aipg-sandbox:latest", default_timeout_seconds=10
    )
    config = AppConfig(sandbox=sandbox_config)
    service = build_sandbox_service(config)

    # Test pandas DataFrame creation
    code = """
import pandas as pd
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
print('DataFrame shape:', df.shape)
print('Sum of column A:', df['A'].sum())
"""
    result = service.run_code(code)
    assert result.exit_code == 0
    assert "DataFrame shape: (3, 2)" in result.stdout
    assert "Sum of column A: 6" in result.stdout

    # Test numpy array operations
    code = """
import numpy as np
arr = np.array([1, 2, 3, 4, 5])
print('Array sum:', arr.sum())
print('Array mean:', arr.mean())
"""
    result = service.run_code(code)
    assert result.exit_code == 0
    assert "Array sum: 15" in result.stdout
    assert "Array mean: 3.0" in result.stdout

    # Test torch tensor operations
    code = """
import torch
tensor = torch.tensor([1.0, 2.0, 3.0])
print('Tensor sum:', tensor.sum().item())
print('Tensor mean:', tensor.mean().item())
"""
    result = service.run_code(code)
    assert result.exit_code == 0
    assert "Tensor sum: 6.0" in result.stdout
    assert "Tensor mean: 2.0" in result.stdout

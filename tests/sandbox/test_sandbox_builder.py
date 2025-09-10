import pytest

from aipg.configs.app_config import AppConfig, SandboxConfig


@pytest.mark.unit
def test_build_sandbox_service_uses_config():
    """Test that the builder creates a service with the correct configuration."""
    from aipg.sandbox.builder import build_sandbox_service

    # Arrange: create a mock config with custom sandbox settings
    sandbox_config = SandboxConfig(
        docker_image="custom-python:latest",
        memory_limit="256m",
        cpu_quota=1.0,
        pids_limit=256,
        default_timeout_seconds=10,
    )
    config = AppConfig(sandbox=sandbox_config)

    # Act
    service = build_sandbox_service(config)

    # Assert: verify the service is created with the correct configuration
    assert service is not None
    assert service._default_timeout_seconds == 10
    # The runner should be configured with the custom settings
    assert service._runner._image == "custom-python:latest"
    assert service._runner._memory_limit == "256m"
    assert service._runner._cpu_quota == 1.0
    assert service._runner._pids_limit == 256


@pytest.mark.unit
def test_build_sandbox_service_with_default_config():
    """Test that the builder works with default configuration."""
    from aipg.sandbox.builder import build_sandbox_service

    # Arrange: use default config
    config = AppConfig()

    # Act
    service = build_sandbox_service(config)

    # Assert: verify the service is created with default settings
    assert service is not None
    assert service._default_timeout_seconds == 5  # default from SandboxConfig
    assert service._runner._image == "python:3.12-alpine"  # default from SandboxConfig
    assert service._runner._memory_limit == "128m"
    assert service._runner._cpu_quota == 0.5
    assert service._runner._pids_limit == 128

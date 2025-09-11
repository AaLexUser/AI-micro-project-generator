from importlib.resources import files
from pathlib import Path

PACKAGE_NAME = "aipg"


def _get_package_path() -> str:
    """
    Get the package path, handling development, installed, and Docker environments.

    Returns:
        Path to the package directory as a string.
    """
    # Check if we're in a Docker container with configs in /app
    docker_config_path = Path("/app/aipg/configs")
    if docker_config_path.exists():
        return "/app/aipg"

    # Try to use importlib.resources for installed packages
    try:
        package_path = str(Path(files(PACKAGE_NAME)))  # type: ignore
        # Verify that configs directory exists in the package path
        configs_path = Path(package_path) / "configs"
        if configs_path.exists():
            return package_path
    except (ImportError, FileNotFoundError, ModuleNotFoundError):
        pass

    # Fallback for development environment
    return str(Path(__file__).parent)


PACKAGE_PATH = _get_package_path()

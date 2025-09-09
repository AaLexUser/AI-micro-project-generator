from importlib.resources import files
from pathlib import Path

PACKAGE_NAME = "aipg"
PACKAGE_PATH = str(Path(files(PACKAGE_NAME)))  # type: ignore

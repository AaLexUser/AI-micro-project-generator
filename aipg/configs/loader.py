import logging
from pathlib import Path
from typing import List, Optional, Type, TypeVar, cast

from dotenv import load_dotenv
from omegaconf import DictConfig, ListConfig, OmegaConf
from pydantic import BaseModel

from aipg.configs.app_config import AppConfig
from aipg.constants import PACKAGE_NAME, PACKAGE_PATH
from aipg.configs.overrides import apply_overrides


def _get_default_config_path(
    presets: str,
) -> Path:
    """
    Get the path to a config YAML file under the package's configs directory.

    Args:
        presets: Name of the preset config (without .yaml extension).

    Returns:
        Path to the config YAML file.

    Raises:
        ValueError: If the config file is not found.
    """
    try:
        config_path = Path(PACKAGE_PATH) / "configs" / f"{presets}.yaml"

        if not config_path.exists():
            raise ValueError(
                f"Config file not found at expected location: {config_path}\n"
                "Please ensure the config files are properly installed in the configs directory."
            )
        return config_path
    except Exception:
        # Fallback for development environment
        package_root = Path(__file__).parent.parent
        config_path = package_root / "configs" / f"{presets}.yaml"
        if not config_path.exists():
            raise ValueError(f"Config file not found: {config_path}")
        return config_path


def _path_resolver(path: str | Path) -> Path:
    """
    Resolve a config path, supporting '<PACKAGE_NAME>:<alias>' package-scoped syntax for configs.

    Args:
        path: Path string, possibly with '<PACKAGE_NAME>:' prefix.

    Returns:
        Path object to the resolved config file.
    """
    raw = str(path).strip()
    prefix = f"{PACKAGE_NAME}:"
    if raw.startswith(prefix):
        alias = raw.split(":", 1)[1].strip()
        logging.info(f"Config path resolved: {alias}")
        return _get_default_config_path(alias)
    return Path(raw)


def _load_config_file(
    config_path: str | Path, name: Optional[str] = None
) -> DictConfig | ListConfig:
    """
    Load a configuration YAML file using OmegaConf.

    Args:
        config_path: Path to the config file (can use '<PACKAGE_NAME>:<alias>' syntax).
        name: Optional name for logging and error messages.
    Returns:
        Loaded configuration as an OmegaConf object.

    Raises:
        ValueError: If the config file is not found.
    """
    resolved_config_path = _path_resolver(config_path)
    name = name if name else resolved_config_path.name
    if not resolved_config_path.is_file():
        raise ValueError(
            f"{name.capitalize()} config file not found at: {resolved_config_path}"
        )
    logging.info(f"Loading {name} config from: {resolved_config_path}")
    loaded_config = OmegaConf.load(resolved_config_path)
    return loaded_config


T = TypeVar("T", bound=BaseModel)


def load_config(
    presets: Optional[str | Path | List[str | Path]] = None,
    config_path: Optional[str | Path] = None,
    overrides: Optional[List[str]] = None,
    schema: Type[T] = AppConfig,  # type: ignore
) -> T:
    """
    Load and merge configuration from YAML files and command-line overrides.

    Loads the default config, applies one or more preset configs (merging them in order),
    and applies any command-line style overrides. The final config is validated against
    the provided Pydantic schema.

    Args:
        schema: Pydantic model class to validate the config against.
        presets: Single preset name or list of preset names to merge into the config.
        config_path: Path or alias to the default config file.
        overrides: Optional list of command-line overrides in format ["key1=value1", "key2.nested=value2"].

    Returns:
        Loaded and merged configuration as an instance of the provided schema.

    Raises:
        ValueError: If any config file is not found or invalid.
        pydantic.ValidationError: If the merged config does not match the schema.
    """
    # Load env
    load_dotenv()

    # Load default config
    config_path = config_path if config_path else f"{PACKAGE_NAME}:default"
    config = _load_config_file(config_path, name="default")

    # Apply Presets
    if presets:
        presets = [presets] if isinstance(presets, (str, Path)) else presets
        for preset in presets:
            presets_config = _load_config_file(preset)
            logging.info(f"Merging {preset} config")
            config = OmegaConf.merge(config, presets_config)
            logging.info("Successfully merged custom config with default config")

    # Apply command-line overrides if any
    if overrides:
        logging.info(f"Applying command-line overrides: {overrides}")
        config = apply_overrides(config, overrides)
        logging.info("Successfully applied command-line overrides")

    # Set pydantic schema
    config_dict = OmegaConf.to_container(config, resolve=True)
    validated_config = cast(T, schema.model_validate(config_dict))
    return validated_config

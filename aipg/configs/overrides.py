import ast
import re
from typing import Any, List

from omegaconf import DictConfig, ListConfig, OmegaConf


def parse_override(override: str) -> tuple[str, str]:
    """
    Parse a single override string in the format 'key=value' or 'key.nested=value'.

    Raises ValueError if the format is invalid.
    """
    if "=" not in override:
        raise ValueError(
            f"Invalid override format: {override}. Must be in format 'key=value' or 'key.nested=value'"
        )
    key, value = override.split("=", 1)
    return key, value


def _safe_parse_value(value: str) -> Any:
    """
    Safely parse a string override value into a Python type without using eval.

    Order of attempts:
    - ast.literal_eval
    - Simple bracketed lists with bare items (fallback)
    - Typed literals (true/false/null/none)
    - int, float
    - raw string
    """
    try:
        return ast.literal_eval(value)
    except Exception:
        pass

    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1]
        items = [item.strip() for item in inner.split(",") if item.strip()]
        parsed_items: list[Any] = []
        for item in items:
            try:
                parsed_items.append(ast.literal_eval(item))
            except Exception:
                lowered = item.lower()
                if lowered == "true":
                    parsed_items.append(True)
                elif lowered == "false":
                    parsed_items.append(False)
                elif lowered in {"null", "none"}:
                    parsed_items.append(None)
                else:
                    try:
                        parsed_items.append(int(item))
                    except Exception:
                        try:
                            parsed_items.append(float(item))
                        except Exception:
                            parsed_items.append(item)
        return parsed_items

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none"}:
        return None

    try:
        return int(value)
    except Exception:
        try:
            return float(value)
        except Exception:
            return value


def apply_overrides(
    config: DictConfig | ListConfig, overrides: List[str]
) -> DictConfig | ListConfig:
    """
    Apply command-line style overrides to a configuration dictionary.

    - Supports nested keys via dot notation (e.g., a.b.c=value)
    - Supports lists via Python/JSON-like notation
    - Safe parsing without eval
    """
    if not overrides:
        return config

    # Flatten potential comma-separated items while preserving commas in brackets
    flattened: list[str] = []
    for item in overrides:
        parts = re.split(pattern=r",(?![^\[]*\])", string=item)
        flattened.extend([p for p in (part.strip() for part in parts) if p])

    override_conf: dict[str, Any] = {}

    for override in flattened:
        key, raw_value = parse_override(override)
        value = _safe_parse_value(raw_value)

        current = override_conf
        key_parts = key.split(".")
        for part in key_parts[:-1]:
            current = current.setdefault(part, {})
        current[key_parts[-1]] = value

    override_conf_cfg = OmegaConf.create(override_conf)  # type: ignore
    return OmegaConf.merge(config, override_conf_cfg)

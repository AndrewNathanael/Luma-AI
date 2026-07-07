"""Utility helpers for configuration, filesystem, and reproducibility."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any, Dict

import numpy as np
import yaml


def load_config(path: str | Path | None = None) -> Dict[str, Any]:
    """Load YAML config. Returns an empty dict when path is None."""
    if path is None:
        return {}
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def deep_get(config: Dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    """Read nested config values using a dotted key, e.g. 'rppg.method'."""
    value: Any = config
    for key in dotted_key.split("."):
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def ensure_parent(path: str | Path) -> Path:
    """Create parent directory for a file path and return Path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_json(data: Dict[str, Any], path: str | Path) -> None:
    path = ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=_json_default)


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)

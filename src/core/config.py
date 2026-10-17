"""Runtime configuration loading (TOML, with optional override file)."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "default.toml"


def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(override: Path | str | None = None) -> dict[str, Any]:
    cfg = tomllib.loads(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    if override:
        cfg = _merge(cfg, tomllib.loads(Path(override).read_text(encoding="utf-8")))
    return cfg


def resolve(path: str | Path) -> Path:
    """Resolve config-relative paths against the project root."""
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p

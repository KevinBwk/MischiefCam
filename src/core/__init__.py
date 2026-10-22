"""Core pipeline. The package name is deliberately product-neutral so the product can be renamed freely."""

import os as _os
from pathlib import Path as _Path

# Keep model caches and tool settings inside the project even when scripts/env.sh was not sourced.
# setdefault: an explicit environment (env.sh, CI) still wins.
_ROOT = _Path(__file__).resolve().parents[2]
_os.environ.setdefault("YOLO_CONFIG_DIR", str(_ROOT / ".yolo_config"))
_os.environ.setdefault("HF_HOME", str(_ROOT / ".hf_cache"))
_os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
_os.environ.setdefault("YOLO_OFFLINE", "1")

# Once models are in the project cache, run fully offline by default (no Hub update checks at runtime).
# To download a new model on purpose:  HF_HUB_OFFLINE=0 uv run ...
if (_ROOT / ".hf_cache" / "hub").is_dir():
    _os.environ.setdefault("HF_HUB_OFFLINE", "1")
    _os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

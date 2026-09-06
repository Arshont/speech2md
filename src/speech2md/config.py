"""User configuration: JSON file with default model and options."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

KNOWN_KEYS = ("model", "language", "format", "timestamps", "device")


def config_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "speech2md" / "config.json"


def load_config() -> dict:
    try:
        data = json.loads(config_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(updates: dict) -> Path:
    """Merges updates into the existing config and writes it back."""
    path = config_path()
    config = {**load_config(), **updates}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path

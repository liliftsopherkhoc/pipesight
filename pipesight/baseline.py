"""Baseline management: save and load a reference pipeline summary for regression tracking."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

DEFAULT_BASELINE_PATH = ".pipesight_baseline.json"


def save_baseline(summary: dict, path: str = DEFAULT_BASELINE_PATH) -> None:
    """Persist *summary* as the current baseline."""
    dest = Path(path)
    dest.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def load_baseline(path: str = DEFAULT_BASELINE_PATH) -> Optional[dict]:
    """Return the baseline dict, or *None* if the file does not exist."""
    dest = Path(path)
    if not dest.exists():
        return None
    try:
        return json.loads(dest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def clear_baseline(path: str = DEFAULT_BASELINE_PATH) -> bool:
    """Delete the baseline file.  Returns *True* if the file was removed."""
    dest = Path(path)
    if dest.exists():
        dest.unlink()
        return True
    return False


def baseline_exists(path: str = DEFAULT_BASELINE_PATH) -> bool:
    """Return *True* when a baseline file is present at *path*."""
    return Path(path).exists()


def promote_to_baseline(
    source_path: str,
    baseline_path: str = DEFAULT_BASELINE_PATH,
) -> None:
    """Copy an existing JSON export at *source_path* to *baseline_path*."""
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")
    data = json.loads(source.read_text(encoding="utf-8"))
    save_baseline(data, baseline_path)

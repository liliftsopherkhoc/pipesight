"""Export StepProfile data to dict / JSON / CSV."""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List

from pipesight.profiler import StepProfile


def profile_to_dict(profile: StepProfile) -> Dict[str, Any]:
    """Serialise a single StepProfile to a plain dict."""
    return {
        "step_name": profile.step_name,
        "duration_ms": profile.duration_ms,
        "memory_before_mb": profile.memory_before_mb,
        "memory_after_mb": profile.memory_after_mb,
        "memory_delta_mb": profile.memory_delta_mb,
        "cpu_percent": profile.cpu_percent,
    }


def profiles_to_json(profiles: List[StepProfile], indent: int = 2) -> str:
    """Return a JSON string for a list of StepProfiles."""
    return json.dumps([profile_to_dict(p) for p in profiles], indent=indent)


def profiles_to_csv(profiles: List[StepProfile]) -> str:
    """Return a CSV string (with header) for a list of StepProfiles."""
    fieldnames = [
        "step_name",
        "duration_ms",
        "memory_before_mb",
        "memory_after_mb",
        "memory_delta_mb",
        "cpu_percent",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for p in profiles:
        writer.writerow(profile_to_dict(p))
    return buf.getvalue()


def save_profiles(
    profiles: List[StepProfile],
    path: str,
    fmt: str = "json",
) -> None:
    """Write profiles to *path* in the requested format (``json`` or ``csv``)."""
    fmt = fmt.lower()
    if fmt == "json":
        content = profiles_to_json(profiles)
    elif fmt == "csv":
        content = profiles_to_csv(profiles)
    else:
        raise ValueError(f"Unsupported format: {fmt!r}. Use 'json' or 'csv'.")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)

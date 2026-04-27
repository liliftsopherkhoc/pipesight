"""Export pipeline tracker summaries to JSON or CSV formats."""

from __future__ import annotations

import csv
import json
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipesight.tracker import PipelineTracker


def to_dict(tracker: "PipelineTracker") -> dict:
    """Serialize a PipelineTracker to a plain dictionary."""
    return {
        "pipeline": tracker.name,
        "total_duration_ms": tracker.total_duration_ms(),
        "steps": [
            {
                "name": step.name,
                "duration_ms": step.duration_ms,
                "rows_in": step.rows_in,
                "rows_out": step.rows_out,
                "rows_delta": step.rows_delta(),
                "error": step.error,
            }
            for step in tracker.steps
        ],
    }


def to_json(tracker: "PipelineTracker", indent: int = 2) -> str:
    """Serialize a PipelineTracker to a JSON string."""
    return json.dumps(to_dict(tracker), indent=indent, default=str)


def to_csv(tracker: "PipelineTracker") -> str:
    """Serialize PipelineTracker steps to a CSV string."""
    output = io.StringIO()
    fieldnames = ["name", "duration_ms", "rows_in", "rows_out", "rows_delta", "error"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for step in tracker.steps:
        writer.writerow(
            {
                "name": step.name,
                "duration_ms": step.duration_ms,
                "rows_in": step.rows_in,
                "rows_out": step.rows_out,
                "rows_delta": step.rows_delta(),
                "error": step.error or "",
            }
        )
    return output.getvalue()


def save(tracker: "PipelineTracker", path: str, fmt: str = "json") -> None:
    """Write tracker summary to *path* in the given format ('json' or 'csv')."""
    fmt = fmt.lower()
    if fmt == "json":
        content = to_json(tracker)
    elif fmt == "csv":
        content = to_csv(tracker)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}. Use 'json' or 'csv'.")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)

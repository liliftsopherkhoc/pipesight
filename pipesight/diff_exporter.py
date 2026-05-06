"""Export DiffResult to JSON or CSV."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List

from pipesight.differ import DiffResult


def diff_to_dict(result: DiffResult) -> Dict[str, Any]:
    return {
        "total_duration_delta_ms": result.total_duration_delta_ms,
        "added_steps": result.added_steps,
        "removed_steps": result.removed_steps,
        "deltas": [
            {
                "name": d.name,
                "prev_ms": d.prev_ms,
                "curr_ms": d.curr_ms,
                "duration_delta_ms": d.duration_delta_ms,
                "pct_change": round(d.pct_change, 2) if d.pct_change is not None else None,
                "prev_rows": d.prev_rows,
                "curr_rows": d.curr_rows,
                "rows_delta": d.rows_delta,
            }
            for d in result.deltas
        ],
    }


def diff_to_json(result: DiffResult, indent: int = 2) -> str:
    return json.dumps(diff_to_dict(result), indent=indent)


def diff_to_csv(result: DiffResult) -> str:
    buf = io.StringIO()
    headers = [
        "name", "prev_ms", "curr_ms", "duration_delta_ms",
        "pct_change", "prev_rows", "curr_rows", "rows_delta",
    ]
    writer = csv.DictWriter(buf, fieldnames=headers)
    writer.writeheader()
    for d in result.deltas:
        writer.writerow({
            "name": d.name,
            "prev_ms": d.prev_ms,
            "curr_ms": d.curr_ms,
            "duration_delta_ms": d.duration_delta_ms,
            "pct_change": round(d.pct_change, 2) if d.pct_change is not None else None,
            "prev_rows": d.prev_rows,
            "curr_rows": d.curr_rows,
            "rows_delta": d.rows_delta,
        })
    return buf.getvalue()


def save_diff(result: DiffResult, path: str, fmt: str = "json") -> None:
    p = Path(path)
    if fmt == "json":
        p.write_text(diff_to_json(result), encoding="utf-8")
    elif fmt == "csv":
        p.write_text(diff_to_csv(result), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported format: {fmt!r}. Use 'json' or 'csv'.")

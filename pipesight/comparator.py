"""Compare two pipeline runs and highlight regressions or improvements."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class StepDiff:
    name: str
    duration_ms_before: float
    duration_ms_after: float
    delta_ms: float
    delta_pct: float  # positive = slower, negative = faster

    @property
    def is_regression(self) -> bool:
        return self.delta_pct > 10.0

    @property
    def is_improvement(self) -> bool:
        return self.delta_pct < -10.0


@dataclass
class ComparisonResult:
    step_diffs: List[StepDiff]
    total_before_ms: float
    total_after_ms: float
    added_steps: List[str]
    removed_steps: List[str]

    @property
    def total_delta_ms(self) -> float:
        return self.total_after_ms - self.total_before_ms

    @property
    def total_delta_pct(self) -> float:
        if self.total_before_ms == 0:
            return 0.0
        return (self.total_delta_ms / self.total_before_ms) * 100.0


def compare_summaries(
    before: Dict,
    after: Dict,
) -> ComparisonResult:
    """Compare two pipeline summary dicts (as produced by exporter.to_dict)."""
    before_steps: Dict[str, float] = {
        s["name"]: s["duration_ms"] for s in before.get("steps", [])
    }
    after_steps: Dict[str, float] = {
        s["name"]: s["duration_ms"] for s in after.get("steps", [])
    }

    added = [n for n in after_steps if n not in before_steps]
    removed = [n for n in before_steps if n not in after_steps]

    diffs: List[StepDiff] = []
    for name, dur_before in before_steps.items():
        if name not in after_steps:
            continue
        dur_after = after_steps[name]
        delta_ms = dur_after - dur_before
        delta_pct = (delta_ms / dur_before * 100.0) if dur_before != 0 else 0.0
        diffs.append(
            StepDiff(
                name=name,
                duration_ms_before=dur_before,
                duration_ms_after=dur_after,
                delta_ms=delta_ms,
                delta_pct=delta_pct,
            )
        )

    return ComparisonResult(
        step_diffs=diffs,
        total_before_ms=before.get("total_duration_ms", 0.0),
        total_after_ms=after.get("total_duration_ms", 0.0),
        added_steps=added,
        removed_steps=removed,
    )

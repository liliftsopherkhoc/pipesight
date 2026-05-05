"""Annotate pipeline steps with human-readable performance badges."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipesight.tracker import PipelineTracker, StepResult

# Thresholds in milliseconds
_SLOW_MS = 1_000
_VERY_SLOW_MS = 5_000

# Thresholds for row throughput (rows / second)
_LOW_THROUGHPUT = 10_000
_HIGH_THROUGHPUT = 1_000_000


@dataclass
class StepAnnotation:
    step_name: str
    duration_ms: float
    badge: str          # e.g. "FAST", "SLOW", "BOTTLENECK"
    note: Optional[str] = None


def _throughput(step: StepResult) -> Optional[float]:
    """Return rows-per-second for *step*, or None if not computable."""
    if step.duration_ms and step.duration_ms > 0 and step.row_count_out is not None:
        return step.row_count_out / (step.duration_ms / 1_000)
    return None


def _badge_for_step(step: StepResult) -> tuple[str, Optional[str]]:
    """Return (badge, note) for a single step."""
    ms = step.duration_ms or 0.0

    if ms >= _VERY_SLOW_MS:
        return "BOTTLENECK", f"{ms:,.0f} ms — consider caching or chunking"
    if ms >= _SLOW_MS:
        tp = _throughput(step)
        note = None
        if tp is not None and tp < _LOW_THROUGHPUT:
            note = f"low throughput: {tp:,.0f} rows/s"
        return "SLOW", note

    tp = _throughput(step)
    if tp is not None and tp >= _HIGH_THROUGHPUT:
        return "FAST", f"{tp:,.0f} rows/s"

    return "OK", None


def annotate(tracker: PipelineTracker) -> List[StepAnnotation]:
    """Return a :class:`StepAnnotation` for every recorded step."""
    annotations: List[StepAnnotation] = []
    for step in tracker.steps:
        badge, note = _badge_for_step(step)
        annotations.append(
            StepAnnotation(
                step_name=step.name,
                duration_ms=step.duration_ms or 0.0,
                badge=badge,
                note=note,
            )
        )
    return annotations


def bottlenecks(tracker: PipelineTracker) -> List[StepAnnotation]:
    """Return only steps annotated as BOTTLENECK or SLOW."""
    return [a for a in annotate(tracker) if a.badge in ("BOTTLENECK", "SLOW")]

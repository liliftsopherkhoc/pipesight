"""Step-level diff utilities for comparing two pipeline runs over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipesight.tracker import PipelineTracker, StepResult


@dataclass
class StepDelta:
    name: str
    prev_ms: Optional[float]
    curr_ms: Optional[float]
    prev_rows: Optional[int]
    curr_rows: Optional[int]

    @property
    def duration_delta_ms(self) -> Optional[float]:
        if self.prev_ms is None or self.curr_ms is None:
            return None
        return self.curr_ms - self.prev_ms

    @property
    def rows_delta(self) -> Optional[int]:
        if self.prev_rows is None or self.curr_rows is None:
            return None
        return self.curr_rows - self.prev_rows

    @property
    def pct_change(self) -> Optional[float]:
        if self.prev_ms is None or self.curr_ms is None or self.prev_ms == 0:
            return None
        return (self.curr_ms - self.prev_ms) / self.prev_ms * 100.0


@dataclass
class DiffResult:
    deltas: List[StepDelta] = field(default_factory=list)
    added_steps: List[str] = field(default_factory=list)
    removed_steps: List[str] = field(default_factory=list)

    @property
    def total_duration_delta_ms(self) -> float:
        return sum(
            d.duration_delta_ms for d in self.deltas if d.duration_delta_ms is not None
        )

    def regressions(self, threshold_pct: float = 10.0) -> List[StepDelta]:
        return [
            d for d in self.deltas
            if d.pct_change is not None and d.pct_change > threshold_pct
        ]

    def improvements(self, threshold_pct: float = 10.0) -> List[StepDelta]:
        return [
            d for d in self.deltas
            if d.pct_change is not None and d.pct_change < -threshold_pct
        ]


def diff_trackers(prev: PipelineTracker, curr: PipelineTracker) -> DiffResult:
    """Compare two pipeline runs step by step."""
    prev_map: Dict[str, StepResult] = {s.name: s for s in prev.steps}
    curr_map: Dict[str, StepResult] = {s.name: s for s in curr.steps}

    prev_names = set(prev_map)
    curr_names = set(curr_map)

    deltas: List[StepDelta] = []
    for name in curr_names & prev_names:
        p = prev_map[name]
        c = curr_map[name]
        deltas.append(StepDelta(
            name=name,
            prev_ms=p.duration_ms,
            curr_ms=c.duration_ms,
            prev_rows=p.rows_out,
            curr_rows=c.rows_out,
        ))

    deltas.sort(key=lambda d: d.name)

    return DiffResult(
        deltas=deltas,
        added_steps=sorted(curr_names - prev_names),
        removed_steps=sorted(prev_names - curr_names),
    )

"""Core step timing tracker for pipesight pipelines."""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StepResult:
    name: str
    duration_ms: float
    input_rows: Optional[int] = None
    output_rows: Optional[int] = None
    error: Optional[str] = None

    @property
    def rows_delta(self) -> Optional[int]:
        if self.input_rows is not None and self.output_rows is not None:
            return self.output_rows - self.input_rows
        return None


@dataclass
class PipelineTracker:
    name: str
    steps: List[StepResult] = field(default_factory=list)
    _start_time: float = field(default_factory=time.perf_counter, repr=False)

    @contextmanager
    def track(self, step_name: str, input_rows: Optional[int] = None):
        """Context manager to time a single pipeline step."""
        start = time.perf_counter()
        result = StepResult(name=step_name, duration_ms=0.0, input_rows=input_rows)
        try:
            yield result
        except Exception as exc:
            result.error = str(exc)
            raise
        finally:
            result.duration_ms = (time.perf_counter() - start) * 1000
            self.steps.append(result)

    @property
    def total_duration_ms(self) -> float:
        return sum(s.duration_ms for s in self.steps)

    @property
    def slowest_step(self) -> Optional[StepResult]:
        return max(self.steps, key=lambda s: s.duration_ms) if self.steps else None

    def summary(self) -> dict:
        return {
            "pipeline": self.name,
            "total_steps": len(self.steps),
            "total_duration_ms": round(self.total_duration_ms, 2),
            "slowest_step": self.slowest_step.name if self.slowest_step else None,
            "steps": [
                {
                    "name": s.name,
                    "duration_ms": round(s.duration_ms, 2),
                    "input_rows": s.input_rows,
                    "output_rows": s.output_rows,
                    "rows_delta": s.rows_delta,
                    "error": s.error,
                }
                for s in self.steps
            ],
        }

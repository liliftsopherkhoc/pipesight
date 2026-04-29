"""Step-level memory and CPU profiling utilities for PipelinTracker steps."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PSUTIL_AVAILABLE = False


@dataclass
class StepProfile:
    """Memory and CPU snapshot for a single pipeline step."""
    step_name: str
    duration_ms: float
    memory_before_mb: Optional[float] = None
    memory_after_mb: Optional[float] = None
    cpu_percent: Optional[float] = None

    @property
    def memory_delta_mb(self) -> Optional[float]:
        """Difference in RSS memory between start and end of step."""
        if self.memory_before_mb is None or self.memory_after_mb is None:
            return None
        return round(self.memory_after_mb - self.memory_before_mb, 3)


def _rss_mb() -> Optional[float]:
    """Return current process RSS memory in MB, or None if psutil unavailable."""
    if not _PSUTIL_AVAILABLE:
        return None
    try:
        proc = psutil.Process(os.getpid())
        return round(proc.memory_info().rss / (1024 ** 2), 3)
    except Exception:  # pragma: no cover
        return None


def _cpu_percent() -> Optional[float]:
    """Return current process CPU percent, or None if psutil unavailable."""
    if not _PSUTIL_AVAILABLE:
        return None
    try:
        proc = psutil.Process(os.getpid())
        return proc.cpu_percent(interval=None)
    except Exception:  # pragma: no cover
        return None


def profile_tracker(tracker) -> List[StepProfile]:
    """Build StepProfile list from an existing PipelineTracker's recorded steps.

    Since steps are already completed, memory/CPU are unavailable; duration is
    extracted from each StepResult.  Use ``ProfilingTracker`` for live capture.
    """
    profiles: List[StepProfile] = []
    for step in tracker.steps:
        profiles.append(
            StepProfile(
                step_name=step.name,
                duration_ms=step.duration_ms,
            )
        )
    return profiles


class ProfilingTracker:
    """Thin wrapper around PipelineTracker that captures memory/CPU per step."""

    def __init__(self, tracker):
        self._tracker = tracker
        self.profiles: List[StepProfile] = []

    # Delegate attribute access to the wrapped tracker
    def __getattr__(self, name):
        return getattr(self._tracker, name)

    def track(self, name: str, df):
        """Record a step with memory/CPU profiling then delegate to tracker."""
        mem_before = _rss_mb()
        cpu_before = _cpu_percent()  # prime the measurement
        result_df = self._tracker.track(name, df)
        mem_after = _rss_mb()
        cpu_after = _cpu_percent()

        step = self._tracker.steps[-1]
        self.profiles.append(
            StepProfile(
                step_name=name,
                duration_ms=step.duration_ms,
                memory_before_mb=mem_before,
                memory_after_mb=mem_after,
                cpu_percent=cpu_after,
            )
        )
        return result_df

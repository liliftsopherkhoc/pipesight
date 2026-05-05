"""Alert rules for pipeline step thresholds."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipesight.tracker import PipelineTracker
from pipesight.annotator import StepAnnotation, annotate


@dataclass
class AlertRule:
    """A single threshold rule that can fire on a step."""
    max_duration_ms: Optional[float] = None
    max_memory_mb: Optional[float] = None
    min_throughput_rows_per_sec: Optional[float] = None


@dataclass
class Alert:
    """Fired when a step violates one or more rules."""
    step_name: str
    violations: List[str] = field(default_factory=list)

    @property
    def is_critical(self) -> bool:
        return len(self.violations) > 1


def check_alerts(
    tracker: PipelineTracker,
    rule: AlertRule,
    profiles: Optional[list] = None,
) -> List[Alert]:
    """Evaluate *rule* against every step in *tracker*.

    Parameters
    ----------
    tracker:
        The finished pipeline tracker.
    rule:
        Threshold rule applied to all steps.
    profiles:
        Optional list of ``StepProfile`` objects (from ``profiler``).
        Required for memory-based alerts.

    Returns
    -------
    List[Alert]
        One ``Alert`` per step that violated at least one threshold.
    """
    annotations: List[StepAnnotation] = annotate(tracker)
    profile_map: dict = {}
    if profiles:
        for p in profiles:
            profile_map[p.step_name] = p

    alerts: List[Alert] = []
    for ann in annotations:
        violations: List[str] = []

        if rule.max_duration_ms is not None:
            if ann.step.duration_ms > rule.max_duration_ms:
                violations.append(
                    f"duration {ann.step.duration_ms:.1f} ms "
                    f"exceeds limit {rule.max_duration_ms:.1f} ms"
                )

        if rule.max_memory_mb is not None:
            prof = profile_map.get(ann.step.name)
            if prof is not None and prof.memory_delta_mb is not None:
                if prof.memory_delta_mb > rule.max_memory_mb:
                    violations.append(
                        f"memory delta {prof.memory_delta_mb:.2f} MB "
                        f"exceeds limit {rule.max_memory_mb:.2f} MB"
                    )

        if rule.min_throughput_rows_per_sec is not None:
            if ann.throughput is not None:
                if ann.throughput < rule.min_throughput_rows_per_sec:
                    violations.append(
                        f"throughput {ann.throughput:.0f} rows/s "
                        f"below minimum {rule.min_throughput_rows_per_sec:.0f} rows/s"
                    )

        if violations:
            alerts.append(Alert(step_name=ann.step.name, violations=violations))

    return alerts

"""Step filtering utilities for narrowing pipeline views by name, badge, or threshold."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

from pipesight.tracker import StepResult


@dataclass
class FilterConfig:
    """Criteria used to select a subset of pipeline steps."""

    name_contains: Optional[str] = None
    min_duration_ms: Optional[float] = None
    max_duration_ms: Optional[float] = None
    badge: Optional[str] = None  # e.g. "slow", "bottleneck", "fast"
    only_errors: bool = False


def _matches(step: StepResult, cfg: FilterConfig, badge_map: Optional[dict] = None) -> bool:
    """Return True when *step* satisfies every criterion in *cfg*."""
    if cfg.name_contains and cfg.name_contains.lower() not in step.name.lower():
        return False
    if cfg.min_duration_ms is not None and step.duration_ms < cfg.min_duration_ms:
        return False
    if cfg.max_duration_ms is not None and step.duration_ms > cfg.max_duration_ms:
        return False
    if cfg.only_errors and step.error is None:
        return False
    if cfg.badge is not None:
        resolved = (badge_map or {}).get(step.name)
        if resolved != cfg.badge:
            return False
    return True


def filter_steps(
    steps: List[StepResult],
    cfg: FilterConfig,
    badge_map: Optional[dict] = None,
) -> List[StepResult]:
    """Return the subset of *steps* that match *cfg*."""
    return [s for s in steps if _matches(s, cfg, badge_map)]


def build_filter(
    name_contains: Optional[str] = None,
    min_duration_ms: Optional[float] = None,
    max_duration_ms: Optional[float] = None,
    badge: Optional[str] = None,
    only_errors: bool = False,
) -> Callable[[List[StepResult]], List[StepResult]]:
    """Return a single-argument callable that applies a FilterConfig."""
    cfg = FilterConfig(
        name_contains=name_contains,
        min_duration_ms=min_duration_ms,
        max_duration_ms=max_duration_ms,
        badge=badge,
        only_errors=only_errors,
    )
    return lambda steps, bm=None: filter_steps(steps, cfg, bm)

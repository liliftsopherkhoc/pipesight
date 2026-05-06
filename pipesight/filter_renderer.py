"""Render a filtered subset of pipeline steps to the terminal."""

from __future__ import annotations

from typing import List, Optional

from pipesight.formatter import format_step_line, format_summary
from pipesight.step_filter import FilterConfig, filter_steps
from pipesight.tracker import PipelineTracker, StepResult

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_YELLOW = "\033[33m"


def _header(cfg: FilterConfig) -> str:
    parts: List[str] = []
    if cfg.name_contains:
        parts.append(f"name~'{cfg.name_contains}'")
    if cfg.min_duration_ms is not None:
        parts.append(f">={cfg.min_duration_ms:.0f}ms")
    if cfg.max_duration_ms is not None:
        parts.append(f"<={cfg.max_duration_ms:.0f}ms")
    if cfg.badge:
        parts.append(f"badge={cfg.badge}")
    if cfg.only_errors:
        parts.append("errors-only")
    label = ", ".join(parts) if parts else "none"
    return f"{_BOLD}{_YELLOW}Filter:{_RESET} {label}"


def render_filtered(
    tracker: PipelineTracker,
    cfg: FilterConfig,
    badge_map: Optional[dict] = None,
    total_ms: Optional[float] = None,
) -> str:
    """Return a terminal string showing only the steps that match *cfg*."""
    matched: List[StepResult] = filter_steps(tracker.steps, cfg, badge_map)
    lines: List[str] = [_header(cfg)]

    if not matched:
        lines.append(f"  {_DIM}(no steps matched){_RESET}")
        return "\n".join(lines)

    denom = total_ms or tracker.total_duration_ms() or 1.0
    for step in matched:
        lines.append("  " + format_step_line(step, denom))

    lines.append("")
    lines.append(format_summary(tracker))
    lines.append(
        f"  {_DIM}{len(matched)} of {len(tracker.steps)} step(s) shown{_RESET}"
    )
    return "\n".join(lines)

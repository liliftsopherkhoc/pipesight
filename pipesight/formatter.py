"""Human-readable formatting utilities for pipeline summaries."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pipesight.tracker import PipelineTracker


def format_duration(ms: float) -> str:
    """Return a tidy string for a millisecond duration."""
    if ms < 1_000:
        return f"{ms:.1f}ms"
    if ms < 60_000:
        return f"{ms / 1_000:.2f}s"
    minutes = int(ms // 60_000)
    seconds = (ms % 60_000) / 1_000
    return f"{minutes}m {seconds:.1f}s"


def format_rows(n: int | None) -> str:
    """Return a compact string for a row count, e.g. 1_200 -> '1.2k'."""
    if n is None:
        return "—"
    if n < 1_000:
        return str(n)
    if n < 1_000_000:
        return f"{n / 1_000:.1f}k"
    return f"{n / 1_000_000:.2f}M"


def format_step_line(name: str, duration_ms: float, total_ms: float, rows_out: int | None) -> str:
    """Format a single pipeline step as a one-line summary string."""
    pct = (duration_ms / total_ms * 100) if total_ms > 0 else 0.0
    dur_str = format_duration(duration_ms)
    rows_str = format_rows(rows_out)
    return f"{name:<30} {dur_str:>10}  ({pct:5.1f}%)  rows_out={rows_str}"


def format_summary(tracker: "PipelineTracker") -> str:
    """Return a multi-line human-readable summary of a completed pipeline."""
    from pipesight.tracker import total_duration_ms, slowest_step

    lines: list[str] = []
    total = total_duration_ms(tracker)
    lines.append(f"Pipeline summary  —  total: {format_duration(total)}")
    lines.append("-" * 60)

    for step in tracker.steps:
        status = "✓" if step.error is None else "✗"
        line = format_step_line(step.name, step.duration_ms, total, step.rows_out)
        lines.append(f"  {status}  {line}")
        if step.error is not None:
            lines.append(f"       ERROR: {step.error}")

    lines.append("-" * 60)
    slowest = slowest_step(tracker)
    if slowest:
        lines.append(f"  Slowest step: {slowest.name} ({format_duration(slowest.duration_ms)})")
    return "\n".join(lines)

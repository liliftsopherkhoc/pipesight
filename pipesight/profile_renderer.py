"""Render StepProfile results as a formatted CLI table."""

from __future__ import annotations

from typing import List

from pipesight.profiler import StepProfile
from pipesight.formatter import format_duration, format_rows
from pipesight.renderer import _bar, _color_for_fraction

_ANSI_RESET = "\033[0m"
_ANSI_RED = "\033[31m"
_ANSI_YELLOW = "\033[33m"
_ANSI_GREEN = "\033[32m"
_ANSI_CYAN = "\033[36m"
_ANSI_BOLD = "\033[1m"

_BAR_WIDTH = 20


def _mem_color(mb: float) -> str:
    """Return ANSI color code based on memory usage in MB."""
    if mb >= 100:
        return _ANSI_RED
    if mb >= 25:
        return _ANSI_YELLOW
    return _ANSI_GREEN


def render_profiles(profiles: List[StepProfile], use_color: bool = True) -> str:
    """Render a list of StepProfile objects as a formatted string.

    Args:
        profiles: List of StepProfile instances to render.
        use_color: Whether to emit ANSI color codes.

    Returns:
        A multi-line string suitable for printing to a terminal.
    """
    if not profiles:
        return "No profile data available."

    max_duration = max((p.duration_ms for p in profiles), default=1.0) or 1.0
    max_mem = max(
        (p.memory_delta_mb for p in profiles if p.memory_delta_mb is not None),
        default=0.0,
    ) or 1.0

    header = (
        f"{'Step':<24} {'Duration':>12} {'Bar':<{_BAR_WIDTH + 2}} "
        f"{'ΔMem (MB)':>10} {'CPU %':>7} {'Rows':>10}"
    )
    divider = "-" * len(header)
    lines = []

    if use_color:
        lines.append(f"{_ANSI_BOLD}{header}{_ANSI_RESET}")
    else:
        lines.append(header)
    lines.append(divider)

    for p in profiles:
        fraction = p.duration_ms / max_duration
        bar = _bar(fraction, width=_BAR_WIDTH)

        dur_str = format_duration(p.duration_ms)
        rows_str = format_rows(p.rows_out)

        mem_str = (
            f"{p.memory_delta_mb:+.1f}"
            if p.memory_delta_mb is not None
            else "    n/a"
        )
        cpu_str = (
            f"{p.cpu_percent:.1f}"
            if p.cpu_percent is not None
            else "  n/a"
        )

        if use_color:
            dur_color = _color_for_fraction(fraction)
            mem_color = (
                _mem_color(abs(p.memory_delta_mb))
                if p.memory_delta_mb is not None
                else ""
            )
            line = (
                f"{p.step_name:<24} "
                f"{dur_color}{dur_str:>12}{_ANSI_RESET} "
                f"[{_ANSI_CYAN}{bar}{_ANSI_RESET}] "
                f"{mem_color}{mem_str:>10}{_ANSI_RESET} "
                f"{cpu_str:>7} "
                f"{rows_str:>10}"
            )
        else:
            line = (
                f"{p.step_name:<24} {dur_str:>12} [{bar}] "
                f"{mem_str:>10} {cpu_str:>7} {rows_str:>10}"
            )

        lines.append(line)

    lines.append(divider)
    total_dur = sum(p.duration_ms for p in profiles)
    lines.append(f"{'TOTAL':<24} {format_duration(total_dur):>12}")
    return "\n".join(lines)

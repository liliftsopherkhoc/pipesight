"""Render profiling results to the terminal."""
from __future__ import annotations

from typing import List

from pipesight.profiler import StepProfile
from pipesight.renderer import _bar, _color_for_fraction
from pipesight.formatter import format_duration

_COL_NAME = 28
_COL_DUR = 12
_COL_MEM = 14
_COL_CPU = 8
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"


def _mem_color(delta_mb: float) -> str:
    if delta_mb > 100:
        return "\033[31m"  # red
    if delta_mb > 20:
        return "\033[33m"  # yellow
    return "\033[32m"  # green


def render_profiles(profiles: List[StepProfile]) -> str:
    """Return a formatted table string for the given step profiles."""
    if not profiles:
        return "No profile data available.\n"

    max_dur = max(p.duration_ms for p in profiles) or 1.0

    header = (
        f"{_BOLD}"
        f"{'Step':<{_COL_NAME}}"
        f"{'Duration':>{_COL_DUR}}"
        f"{'Mem Δ (MB)':>{_COL_MEM}}"
        f"{'CPU%':>{_COL_CPU}}"
        f"{_RESET}"
    )
    separator = "-" * (_COL_NAME + _COL_DUR + _COL_MEM + _COL_CPU)
    lines = [header, separator]

    for p in profiles:
        frac = p.duration_ms / max_dur
        color = _color_for_fraction(frac)
        dur_str = format_duration(p.duration_ms)
        bar = _bar(frac, width=10)

        if p.memory_delta_mb is not None:
            mem_col = _mem_color(p.memory_delta_mb)
            mem_str = f"{mem_col}{p.memory_delta_mb:+.1f}{_RESET}"
        else:
            mem_str = f"{_DIM}n/a{_RESET}"

        if p.cpu_percent is not None:
            cpu_str = f"{p.cpu_percent:.1f}"
        else:
            cpu_str = f"{_DIM}n/a{_RESET}"

        name_col = p.step_name[:_COL_NAME - 1].ljust(_COL_NAME)
        dur_col = f"{color}{dur_str}{_RESET}".rjust(_COL_DUR + len(color) + len(_RESET))
        lines.append(f"{name_col}{dur_col}{mem_str:>{_COL_MEM}}{cpu_str:>{_COL_CPU}}")
        lines.append(f"  {bar}")

    lines.append(separator)
    return "\n".join(lines) + "\n"

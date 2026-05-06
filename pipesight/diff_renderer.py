"""Render a DiffResult to the terminal."""
from __future__ import annotations

from typing import List

from pipesight.differ import DiffResult, StepDelta

_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _sign(value: float) -> str:
    return "+" if value >= 0 else ""


def _colorize_pct(pct: float) -> str:
    if pct > 10:
        return f"{_RED}{_sign(pct)}{pct:.1f}%{_RESET}"
    if pct < -10:
        return f"{_GREEN}{_sign(pct)}{pct:.1f}%{_RESET}"
    return f"{_YELLOW}{_sign(pct)}{pct:.1f}%{_RESET}"


def _format_delta_line(delta: StepDelta) -> str:
    dur = (
        f"{delta.curr_ms:.1f}ms"
        if delta.curr_ms is not None
        else "n/a"
    )
    if delta.duration_delta_ms is not None:
        d_str = f"{_sign(delta.duration_delta_ms)}{delta.duration_delta_ms:.1f}ms"
    else:
        d_str = "n/a"

    pct_str = _colorize_pct(delta.pct_change) if delta.pct_change is not None else "n/a"
    return f"  {_BOLD}{delta.name:<30}{_RESET} {dur:>10}  Δ {d_str:>10}  ({pct_str})"


def render_diff(result: DiffResult, threshold_pct: float = 10.0) -> str:
    lines: List[str] = []
    lines.append(f"{_BOLD}{'Step':<30} {'Duration':>10}  {'Delta':>12}  {'Change':>10}{_RESET}")
    lines.append("-" * 72)

    for delta in result.deltas:
        lines.append(_format_delta_line(delta))

    for name in result.added_steps:
        lines.append(f"  {_CYAN}{'+ ' + name:<30}{_RESET} {'(new)':>10}")

    for name in result.removed_steps:
        lines.append(f"  {_RED}{'- ' + name:<30}{_RESET} {'(gone)':>10}")

    lines.append("-" * 72)
    total = result.total_duration_delta_ms
    total_str = f"{_sign(total)}{total:.1f}ms"
    color = _RED if total > 0 else _GREEN
    lines.append(f"  {'Total Δ':<30} {color}{total_str:>10}{_RESET}")

    regressions = result.regressions(threshold_pct)
    improvements = result.improvements(threshold_pct)
    if regressions:
        lines.append(f"\n{_RED}Regressions (>{threshold_pct:.0f}%): {', '.join(d.name for d in regressions)}{_RESET}")
    if improvements:
        lines.append(f"{_GREEN}Improvements (>{threshold_pct:.0f}%): {', '.join(d.name for d in improvements)}{_RESET}")

    return "\n".join(lines)

"""Render a ComparisonResult to a human-readable string."""

from __future__ import annotations

from pipesight.comparator import ComparisonResult, StepDiff
from pipesight.formatter import format_duration

_GREEN = "\033[32m"
_RED = "\033[31m"
_YELLOW = "\033[33m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _sign(value: float) -> str:
    return "+" if value >= 0 else ""


def _colorize(text: str, delta_pct: float) -> str:
    if delta_pct > 10.0:
        return f"{_RED}{text}{_RESET}"
    if delta_pct < -10.0:
        return f"{_GREEN}{text}{_RESET}"
    return f"{_YELLOW}{text}{_RESET}"


def render_comparison(result: ComparisonResult, color: bool = True) -> str:
    lines: list[str] = []
    lines.append(f"{_BOLD}Pipeline Comparison{_RESET}" if color else "Pipeline Comparison")
    lines.append("-" * 52)

    for diff in result.step_diffs:
        sign = _sign(diff.delta_ms)
        change = f"{sign}{diff.delta_ms:+.1f} ms ({sign}{diff.delta_pct:.1f}%)"
        if color:
            change = _colorize(change, diff.delta_pct)
        label = "REGRESSION" if diff.is_regression else ("IMPROVEMENT" if diff.is_improvement else "OK")
        lines.append(
            f"  {diff.name:<24}  "
            f"{format_duration(diff.duration_ms_before):>10} -> "
            f"{format_duration(diff.duration_ms_after):>10}  "
            f"{change}  [{label}]"
        )

    if result.added_steps:
        lines.append("")
        lines.append("  Added steps:   " + ", ".join(result.added_steps))
    if result.removed_steps:
        lines.append("  Removed steps: " + ", ".join(result.removed_steps))

    lines.append("-" * 52)
    total_sign = _sign(result.total_delta_ms)
    total_str = (
        f"Total: {format_duration(result.total_before_ms)} -> "
        f"{format_duration(result.total_after_ms)}  "
        f"({total_sign}{result.total_delta_pct:.1f}%)"
    )
    lines.append(total_str)
    return "\n".join(lines)

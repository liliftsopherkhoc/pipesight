"""CLI renderer for displaying pipeline profiling results."""

from typing import List
from pipesight.tracker import PipelineTracker, StepResult

BAR_WIDTH = 30
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
CYAN = "\033[36m"


def _bar(fraction: float, width: int = BAR_WIDTH) -> str:
    filled = int(fraction * width)
    return "█" * filled + "░" * (width - filled)


def _color_for_fraction(fraction: float) -> str:
    if fraction >= 0.6:
        return RED
    if fraction >= 0.3:
        return YELLOW
    return GREEN


def render_tracker(tracker: PipelineTracker) -> str:
    lines: List[str] = []
    total = tracker.total_duration_ms or 1.0

    lines.append(f"{BOLD}{CYAN}Pipeline: {tracker.name}{RESET}")
    lines.append(f"Total duration: {total:.2f} ms  |  Steps: {len(tracker.steps)}")
    lines.append("-" * 60)

    for step in tracker.steps:
        fraction = step.duration_ms / total
        color = _color_for_fraction(fraction)
        bar = _bar(fraction)
        pct = fraction * 100

        row_info = ""
        if step.input_rows is not None and step.output_rows is not None:
            row_info = f"  rows: {step.input_rows}→{step.output_rows}"
        elif step.output_rows is not None:
            row_info = f"  rows: {step.output_rows}"

        error_tag = f"  {RED}[ERROR]{RESET}" if step.error else ""
        lines.append(
            f"{color}{bar}{RESET} {pct:5.1f}%  "
            f"{BOLD}{step.name}{RESET}  {step.duration_ms:.2f} ms"
            f"{row_info}{error_tag}"
        )

    lines.append("-" * 60)
    slowest = tracker.slowest_step
    if slowest:
        lines.append(f"Bottleneck: {RED}{BOLD}{slowest.name}{RESET} ({slowest.duration_ms:.2f} ms)")

    return "\n".join(lines)

"""Render live scheduler status to the terminal."""
from __future__ import annotations

import datetime
from typing import Optional

from pipesight.scheduler import ScheduleState
from pipesight.formatter import format_duration
from pipesight.renderer import render_tracker

_RESET = "\033[0m"
_BOLD = "\033[1m"
_CYAN = "\033[96m"
_YELLOW = "\033[93m"
_GREEN = "\033[92m"
_RED = "\033[91m"


def _timestamp() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


def render_schedule_header(config_interval: float, run_count: int, max_runs: Optional[int]) -> str:
    """Return a one-line status banner for the scheduler."""
    interval_str = format_duration(config_interval * 1000)
    runs_str = f"{run_count}" if max_runs is None else f"{run_count}/{max_runs}"
    return (
        f"{_BOLD}{_CYAN}[pipesight scheduler]{_RESET} "
        f"interval={interval_str}  runs={runs_str}  "
        f"ts={_timestamp()}"
    )


def render_schedule_error(error: str, run_index: int) -> str:
    """Return a formatted error line for a failed run."""
    return f"{_RED}[run {run_index} ERROR]{_RESET} {error}"


def render_schedule_state(state: ScheduleState, interval_seconds: float, max_runs: Optional[int] = None) -> str:
    """Render a full status block for the current scheduler state."""
    lines: list[str] = []
    lines.append(render_schedule_header(interval_seconds, state.run_count, max_runs))

    if state.errors:
        lines.append(f"{_YELLOW}  Errors ({len(state.errors)}):{_RESET}")
        for i, err in enumerate(state.errors[-3:], 1):  # show last 3
            lines.append(f"    {_RED}{i}.{_RESET} {err}")

    if state.last_tracker is not None:
        lines.append(f"{_GREEN}  Last result:{_RESET}")
        for line in render_tracker(state.last_tracker).splitlines():
            lines.append(f"    {line}")
    else:
        lines.append(f"{_YELLOW}  No results yet.{_RESET}")

    status = f"{_GREEN}running{_RESET}" if not state.stopped else f"{_RED}stopped{_RESET}"
    lines.append(f"  Status: {status}")
    return "\n".join(lines)

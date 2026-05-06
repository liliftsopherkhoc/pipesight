"""Scheduled pipeline re-runs with configurable intervals."""
from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

from pipesight.tracker import PipelineTracker


@dataclass
class ScheduleConfig:
    interval_seconds: float
    max_runs: Optional[int] = None  # None = run forever
    on_result: Optional[Callable[[PipelineTracker, int], None]] = None
    on_error: Optional[Callable[[Exception, int], None]] = None


@dataclass
class ScheduleState:
    run_count: int = 0
    last_tracker: Optional[PipelineTracker] = None
    errors: list[str] = field(default_factory=list)
    stopped: bool = False


def _run_once(
    factory: Callable[[], PipelineTracker],
    state: ScheduleState,
    config: ScheduleConfig,
) -> None:
    """Execute one pipeline run and update state."""
    try:
        tracker = factory()
        state.run_count += 1
        state.last_tracker = tracker
        if config.on_result:
            config.on_result(tracker, state.run_count)
    except Exception as exc:  # noqa: BLE001
        state.errors.append(str(exc))
        if config.on_error:
            config.on_error(exc, state.run_count)


def run_scheduled(
    factory: Callable[[], PipelineTracker],
    config: ScheduleConfig,
) -> ScheduleState:
    """Block and run *factory* on a fixed interval.

    Returns the final :class:`ScheduleState` when the loop ends.
    """
    state = ScheduleState()
    while not state.stopped:
        _run_once(factory, state, config)
        if config.max_runs is not None and state.run_count >= config.max_runs:
            state.stopped = True
            break
        time.sleep(config.interval_seconds)
    return state


def run_scheduled_async(
    factory: Callable[[], PipelineTracker],
    config: ScheduleConfig,
) -> tuple[threading.Thread, ScheduleState]:
    """Run the scheduler in a background thread.

    Returns ``(thread, state)`` so callers can inspect progress or stop
    the loop by setting ``state.stopped = True``.
    """
    state = ScheduleState()

    def _loop() -> None:
        while not state.stopped:
            _run_once(factory, state, config)
            if config.max_runs is not None and state.run_count >= config.max_runs:
                state.stopped = True
                break
            time.sleep(config.interval_seconds)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()
    return thread, state

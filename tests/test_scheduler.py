"""Tests for pipesight.scheduler."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from pipesight.tracker import PipelineTracker
from pipesight.scheduler import (
    ScheduleConfig,
    ScheduleState,
    _run_once,
    run_scheduled,
    run_scheduled_async,
)


def _make_tracker() -> PipelineTracker:
    t = PipelineTracker()
    with t.track("step"):
        pass
    return t


# ---------------------------------------------------------------------------
# _run_once
# ---------------------------------------------------------------------------

def test_run_once_increments_run_count():
    state = ScheduleState()
    config = ScheduleConfig(interval_seconds=0)
    _run_once(_make_tracker, state, config)
    assert state.run_count == 1


def test_run_once_stores_last_tracker():
    state = ScheduleState()
    config = ScheduleConfig(interval_seconds=0)
    _run_once(_make_tracker, state, config)
    assert isinstance(state.last_tracker, PipelineTracker)


def test_run_once_calls_on_result():
    callback = MagicMock()
    state = ScheduleState()
    config = ScheduleConfig(interval_seconds=0, on_result=callback)
    _run_once(_make_tracker, state, config)
    callback.assert_called_once()


def test_run_once_records_error_on_exception():
    def bad_factory():
        raise ValueError("boom")

    state = ScheduleState()
    config = ScheduleConfig(interval_seconds=0)
    _run_once(bad_factory, state, config)
    assert len(state.errors) == 1
    assert "boom" in state.errors[0]


def test_run_once_calls_on_error_callback():
    err_cb = MagicMock()
    config = ScheduleConfig(interval_seconds=0, on_error=err_cb)
    state = ScheduleState()
    _run_once(lambda: (_ for _ in ()).throw(RuntimeError("fail")), state, config)
    err_cb.assert_called_once()


# ---------------------------------------------------------------------------
# run_scheduled
# ---------------------------------------------------------------------------

def test_run_scheduled_respects_max_runs():
    config = ScheduleConfig(interval_seconds=0, max_runs=3)
    state = run_scheduled(_make_tracker, config)
    assert state.run_count == 3
    assert state.stopped is True


def test_run_scheduled_zero_interval_completes_quickly():
    start = time.monotonic()
    config = ScheduleConfig(interval_seconds=0, max_runs=5)
    run_scheduled(_make_tracker, config)
    elapsed = time.monotonic() - start
    assert elapsed < 2.0


# ---------------------------------------------------------------------------
# run_scheduled_async
# ---------------------------------------------------------------------------

def test_run_scheduled_async_returns_thread_and_state():
    config = ScheduleConfig(interval_seconds=0, max_runs=2)
    thread, state = run_scheduled_async(_make_tracker, config)
    thread.join(timeout=3)
    assert state.run_count == 2


def test_run_scheduled_async_can_be_stopped_early():
    config = ScheduleConfig(interval_seconds=0.05, max_runs=100)
    thread, state = run_scheduled_async(_make_tracker, config)
    time.sleep(0.12)
    state.stopped = True
    thread.join(timeout=2)
    # Should have stopped well before 100 runs
    assert state.run_count < 100

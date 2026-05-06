"""Tests for pipesight.schedule_renderer."""
from __future__ import annotations

import pytest

from pipesight.tracker import PipelineTracker
from pipesight.scheduler import ScheduleState
from pipesight.schedule_renderer import (
    render_schedule_header,
    render_schedule_error,
    render_schedule_state,
)


def _make_tracker() -> PipelineTracker:
    t = PipelineTracker()
    with t.track("load"):
        pass
    return t


def _make_state(run_count: int = 3, with_tracker: bool = True, errors: list[str] | None = None) -> ScheduleState:
    s = ScheduleState()
    s.run_count = run_count
    s.last_tracker = _make_tracker() if with_tracker else None
    s.errors = errors or []
    return s


# ---------------------------------------------------------------------------
# render_schedule_header
# ---------------------------------------------------------------------------

def test_header_contains_interval():
    out = render_schedule_header(5.0, 1, None)
    assert "5" in out


def test_header_contains_run_count():
    out = render_schedule_header(2.0, 7, None)
    assert "7" in out


def test_header_shows_max_runs_fraction():
    out = render_schedule_header(1.0, 3, 10)
    assert "3/10" in out


def test_header_contains_scheduler_label():
    out = render_schedule_header(1.0, 1, None)
    assert "scheduler" in out.lower()


# ---------------------------------------------------------------------------
# render_schedule_error
# ---------------------------------------------------------------------------

def test_error_contains_message():
    out = render_schedule_error("something went wrong", 2)
    assert "something went wrong" in out


def test_error_contains_run_index():
    out = render_schedule_error("oops", 5)
    assert "5" in out


# ---------------------------------------------------------------------------
# render_schedule_state
# ---------------------------------------------------------------------------

def test_state_shows_last_result_when_tracker_present():
    state = _make_state()
    out = render_schedule_state(state, 5.0)
    assert "Last result" in out or "load" in out


def test_state_shows_no_results_when_tracker_missing():
    state = _make_state(with_tracker=False)
    out = render_schedule_state(state, 5.0)
    assert "No results" in out


def test_state_shows_errors_section_when_errors_present():
    state = _make_state(errors=["err1", "err2"])
    out = render_schedule_state(state, 5.0)
    assert "Errors" in out
    assert "err1" in out


def test_state_shows_running_status():
    state = _make_state()
    state.stopped = False
    out = render_schedule_state(state, 5.0)
    assert "running" in out


def test_state_shows_stopped_status():
    state = _make_state()
    state.stopped = True
    out = render_schedule_state(state, 5.0)
    assert "stopped" in out


def test_state_limits_error_display_to_three():
    many_errors = [f"err{i}" for i in range(10)]
    state = _make_state(errors=many_errors)
    out = render_schedule_state(state, 1.0)
    # Only last 3 errors shown
    assert "err9" in out
    assert "err0" not in out

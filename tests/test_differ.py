"""Tests for pipesight.differ."""
from __future__ import annotations

import pytest

from pipesight.differ import (
    DiffResult,
    StepDelta,
    diff_trackers,
)
from pipesight.tracker import PipelineTracker, StepResult


def _make_tracker(*steps: tuple) -> PipelineTracker:
    """steps = (name, duration_ms, rows_out)"""
    t = PipelineTracker()
    for name, duration_ms, rows_out in steps:
        t.steps.append(
            StepResult(name=name, duration_ms=duration_ms, rows_in=None, rows_out=rows_out)
        )
    return t


def test_step_delta_duration_delta():
    d = StepDelta(name="a", prev_ms=100.0, curr_ms=150.0, prev_rows=None, curr_rows=None)
    assert d.duration_delta_ms == pytest.approx(50.0)


def test_step_delta_pct_change():
    d = StepDelta(name="a", prev_ms=100.0, curr_ms=120.0, prev_rows=None, curr_rows=None)
    assert d.pct_change == pytest.approx(20.0)


def test_step_delta_pct_change_none_when_zero_prev():
    d = StepDelta(name="a", prev_ms=0.0, curr_ms=10.0, prev_rows=None, curr_rows=None)
    assert d.pct_change is None


def test_step_delta_rows_delta():
    d = StepDelta(name="a", prev_ms=10.0, curr_ms=10.0, prev_rows=100, curr_rows=80)
    assert d.rows_delta == -20


def test_diff_trackers_shared_steps():
    prev = _make_tracker(("load", 100.0, 1000), ("clean", 50.0, 900))
    curr = _make_tracker(("load", 120.0, 1000), ("clean", 40.0, 900))
    result = diff_trackers(prev, curr)
    assert len(result.deltas) == 2
    names = {d.name for d in result.deltas}
    assert names == {"load", "clean"}


def test_diff_trackers_added_steps():
    prev = _make_tracker(("load", 100.0, 1000))
    curr = _make_tracker(("load", 100.0, 1000), ("transform", 30.0, 900))
    result = diff_trackers(prev, curr)
    assert "transform" in result.added_steps
    assert result.removed_steps == []


def test_diff_trackers_removed_steps():
    prev = _make_tracker(("load", 100.0, 1000), ("validate", 20.0, 1000))
    curr = _make_tracker(("load", 100.0, 1000))
    result = diff_trackers(prev, curr)
    assert "validate" in result.removed_steps
    assert result.added_steps == []


def test_diff_result_total_duration_delta():
    prev = _make_tracker(("a", 100.0, None), ("b", 50.0, None))
    curr = _make_tracker(("a", 110.0, None), ("b", 45.0, None))
    result = diff_trackers(prev, curr)
    assert result.total_duration_delta_ms == pytest.approx(5.0)


def test_diff_result_regressions():
    prev = _make_tracker(("slow", 100.0, None), ("fast", 10.0, None))
    curr = _make_tracker(("slow", 130.0, None), ("fast", 11.0, None))
    result = diff_trackers(prev, curr)
    regressions = result.regressions(threshold_pct=10.0)
    assert len(regressions) == 1
    assert regressions[0].name == "slow"


def test_diff_result_improvements():
    prev = _make_tracker(("step", 200.0, None))
    curr = _make_tracker(("step", 100.0, None))
    result = diff_trackers(prev, curr)
    improvements = result.improvements(threshold_pct=10.0)
    assert len(improvements) == 1
    assert improvements[0].name == "step"

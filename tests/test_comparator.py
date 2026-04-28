"""Tests for pipesight.comparator."""

from __future__ import annotations

import pytest

from pipesight.comparator import compare_summaries, StepDiff, ComparisonResult


def _summary(steps, total_ms=None):
    if total_ms is None:
        total_ms = sum(s["duration_ms"] for s in steps)
    return {"steps": steps, "total_duration_ms": total_ms}


def _step(name, ms):
    return {"name": name, "duration_ms": ms}


# ---------------------------------------------------------------------------
# StepDiff helpers
# ---------------------------------------------------------------------------

def test_step_diff_regression():
    d = StepDiff("load", 100.0, 120.0, 20.0, 20.0)
    assert d.is_regression is True
    assert d.is_improvement is False


def test_step_diff_improvement():
    d = StepDiff("load", 100.0, 80.0, -20.0, -20.0)
    assert d.is_improvement is True
    assert d.is_regression is False


def test_step_diff_neutral():
    d = StepDiff("load", 100.0, 105.0, 5.0, 5.0)
    assert d.is_regression is False
    assert d.is_improvement is False


# ---------------------------------------------------------------------------
# compare_summaries
# ---------------------------------------------------------------------------

def test_compare_identical_pipelines():
    steps = [_step("load", 50.0), _step("transform", 150.0)]
    result = compare_summaries(_summary(steps), _summary(steps))
    assert len(result.step_diffs) == 2
    for d in result.step_diffs:
        assert d.delta_ms == 0.0
        assert d.delta_pct == 0.0


def test_compare_detects_regression():
    before = _summary([_step("load", 100.0)])
    after = _summary([_step("load", 200.0)])
    result = compare_summaries(before, after)
    assert result.step_diffs[0].is_regression is True


def test_compare_added_and_removed_steps():
    before = _summary([_step("load", 50.0), _step("old_step", 30.0)])
    after = _summary([_step("load", 50.0), _step("new_step", 40.0)])
    result = compare_summaries(before, after)
    assert "new_step" in result.added_steps
    assert "old_step" in result.removed_steps


def test_compare_total_delta():
    before = _summary([_step("a", 100.0)], total_ms=100.0)
    after = _summary([_step("a", 150.0)], total_ms=150.0)
    result = compare_summaries(before, after)
    assert result.total_delta_ms == pytest.approx(50.0)
    assert result.total_delta_pct == pytest.approx(50.0)


def test_compare_empty_before():
    before = _summary([], total_ms=0.0)
    after = _summary([_step("load", 100.0)], total_ms=100.0)
    result = compare_summaries(before, after)
    assert result.added_steps == ["load"]
    assert result.step_diffs == []
    assert result.total_delta_pct == 0.0

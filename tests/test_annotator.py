"""Tests for pipesight.annotator."""

from __future__ import annotations

import pytest

from pipesight.annotator import (
    StepAnnotation,
    annotate,
    bottlenecks,
    _throughput,
    _badge_for_step,
)
from pipesight.tracker import PipelineTracker, StepResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _step(name: str, duration_ms: float, row_out: int | None = None) -> StepResult:
    s = StepResult(name=name, duration_ms=duration_ms)
    s.row_count_out = row_out
    return s


def _tracker(*steps: StepResult) -> PipelineTracker:
    t = PipelineTracker()
    t.steps = list(steps)
    return t


# ---------------------------------------------------------------------------
# _throughput
# ---------------------------------------------------------------------------

def test_throughput_computed():
    s = _step("x", duration_ms=500, row_out=5_000)
    assert _throughput(s) == pytest.approx(10_000.0)


def test_throughput_none_when_no_rows():
    s = _step("x", duration_ms=500, row_out=None)
    assert _throughput(s) is None


def test_throughput_none_when_zero_duration():
    s = _step("x", duration_ms=0, row_out=1_000)
    assert _throughput(s) is None


# ---------------------------------------------------------------------------
# _badge_for_step
# ---------------------------------------------------------------------------

def test_badge_bottleneck_for_very_slow_step():
    s = _step("heavy", duration_ms=6_000)
    badge, note = _badge_for_step(s)
    assert badge == "BOTTLENECK"
    assert note is not None


def test_badge_slow_for_moderately_slow_step():
    s = _step("medium", duration_ms=2_000)
    badge, _ = _badge_for_step(s)
    assert badge == "SLOW"


def test_badge_slow_includes_throughput_note_when_low():
    s = _step("medium", duration_ms=2_000, row_out=100)  # very low throughput
    badge, note = _badge_for_step(s)
    assert badge == "SLOW"
    assert note is not None and "rows/s" in note


def test_badge_fast_for_high_throughput():
    s = _step("speedy", duration_ms=10, row_out=50_000)  # 5M rows/s
    badge, note = _badge_for_step(s)
    assert badge == "FAST"
    assert note is not None


def test_badge_ok_for_normal_step():
    s = _step("normal", duration_ms=200, row_out=1_000)
    badge, note = _badge_for_step(s)
    assert badge == "OK"


# ---------------------------------------------------------------------------
# annotate
# ---------------------------------------------------------------------------

def test_annotate_returns_one_per_step():
    t = _tracker(
        _step("a", 100),
        _step("b", 3_000),
        _step("c", 7_000),
    )
    result = annotate(t)
    assert len(result) == 3
    assert [a.step_name for a in result] == ["a", "b", "c"]


def test_annotate_empty_tracker():
    t = _tracker()
    assert annotate(t) == []


def test_annotate_step_annotation_type():
    t = _tracker(_step("s", 50))
    ann = annotate(t)[0]
    assert isinstance(ann, StepAnnotation)
    assert ann.step_name == "s"


# ---------------------------------------------------------------------------
# bottlenecks
# ---------------------------------------------------------------------------

def test_bottlenecks_filters_fast_steps():
    t = _tracker(
        _step("fast", 50),
        _step("slow", 2_000),
        _step("neck", 8_000),
    )
    result = bottlenecks(t)
    names = [a.step_name for a in result]
    assert "fast" not in names
    assert "slow" in names
    assert "neck" in names


def test_bottlenecks_empty_when_all_ok():
    t = _tracker(_step("a", 10), _step("b", 20))
    assert bottlenecks(t) == []

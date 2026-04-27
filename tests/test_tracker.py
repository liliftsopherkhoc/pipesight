"""Tests for PipelineTracker and StepResult."""

import time
import pytest
from pipesight.tracker import PipelineTracker, StepResult
from pipesight.renderer import render_tracker


def test_step_result_rows_delta():
    s = StepResult(name="filter", duration_ms=10.0, input_rows=100, output_rows=80)
    assert s.rows_delta == -20


def test_step_result_rows_delta_none_when_missing():
    s = StepResult(name="load", duration_ms=5.0)
    assert s.rows_delta is None


def test_tracker_records_step():
    tracker = PipelineTracker(name="test_pipe")
    with tracker.track("step_a") as result:
        time.sleep(0.01)
        result.output_rows = 50

    assert len(tracker.steps) == 1
    assert tracker.steps[0].name == "step_a"
    assert tracker.steps[0].duration_ms >= 10
    assert tracker.steps[0].output_rows == 50


def test_tracker_captures_error():
    tracker = PipelineTracker(name="err_pipe")
    with pytest.raises(ValueError):
        with tracker.track("bad_step"):
            raise ValueError("boom")

    assert tracker.steps[0].error == "boom"


def test_slowest_step():
    tracker = PipelineTracker(name="multi")
    tracker.steps.append(StepResult("fast", duration_ms=5.0))
    tracker.steps.append(StepResult("slow", duration_ms=50.0))
    assert tracker.slowest_step.name == "slow"


def test_summary_structure():
    tracker = PipelineTracker(name="summary_test")
    tracker.steps.append(StepResult("load", 20.0, input_rows=None, output_rows=200))
    summary = tracker.summary()
    assert summary["pipeline"] == "summary_test"
    assert summary["total_steps"] == 1
    assert summary["steps"][0]["name"] == "load"


def test_render_produces_output():
    tracker = PipelineTracker(name="render_test")
    tracker.steps.append(StepResult("ingest", 30.0, input_rows=1000, output_rows=1000))
    tracker.steps.append(StepResult("transform", 70.0, input_rows=1000, output_rows=900))
    output = render_tracker(tracker)
    assert "render_test" in output
    assert "ingest" in output
    assert "transform" in output
    assert "Bottleneck" in output

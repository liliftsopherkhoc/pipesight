"""Tests for pipesight.step_filter and pipesight.filter_renderer."""

from __future__ import annotations

import pytest

from pipesight.step_filter import FilterConfig, build_filter, filter_steps
from pipesight.tracker import PipelineTracker, StepResult
from pipesight.filter_renderer import render_filtered


def _step(name: str, duration_ms: float, rows: int = 100, error: str | None = None) -> StepResult:
    return StepResult(name=name, duration_ms=duration_ms, rows_in=rows, rows_out=rows, error=error)


def _tracker(*steps: StepResult) -> PipelineTracker:
    t = PipelineTracker()
    for s in steps:
        t.steps.append(s)
    return t


STEPS = [
    _step("load_csv", 120.0, 1000),
    _step("clean", 45.0, 950),
    _step("transform", 300.0, 950),
    _step("export", 80.0, 950, error="IOError"),
]


def test_filter_name_contains():
    cfg = FilterConfig(name_contains="clean")
    result = filter_steps(STEPS, cfg)
    assert len(result) == 1
    assert result[0].name == "clean"


def test_filter_min_duration():
    cfg = FilterConfig(min_duration_ms=100.0)
    result = filter_steps(STEPS, cfg)
    names = {s.name for s in result}
    assert "load_csv" in names
    assert "transform" in names
    assert "clean" not in names


def test_filter_max_duration():
    cfg = FilterConfig(max_duration_ms=100.0)
    result = filter_steps(STEPS, cfg)
    names = {s.name for s in result}
    assert "clean" in names
    assert "export" in names
    assert "transform" not in names


def test_filter_only_errors():
    cfg = FilterConfig(only_errors=True)
    result = filter_steps(STEPS, cfg)
    assert len(result) == 1
    assert result[0].error == "IOError"


def test_filter_badge():
    badge_map = {"transform": "bottleneck", "clean": "fast"}
    cfg = FilterConfig(badge="bottleneck")
    result = filter_steps(STEPS, cfg, badge_map=badge_map)
    assert len(result) == 1
    assert result[0].name == "transform"


def test_filter_combined_name_and_min_duration():
    cfg = FilterConfig(name_contains="load", min_duration_ms=50.0)
    result = filter_steps(STEPS, cfg)
    assert len(result) == 1
    assert result[0].name == "load_csv"


def test_build_filter_returns_callable():
    fn = build_filter(min_duration_ms=200.0)
    result = fn(STEPS)
    assert all(s.duration_ms >= 200.0 for s in result)


def test_filter_empty_config_returns_all():
    cfg = FilterConfig()
    result = filter_steps(STEPS, cfg)
    assert len(result) == len(STEPS)


# --- render_filtered ---


def test_render_filtered_contains_header():
    t = _tracker(*STEPS)
    cfg = FilterConfig(min_duration_ms=100.0)
    output = render_filtered(t, cfg)
    assert "Filter:" in output
    assert "100ms" in output


def test_render_filtered_shows_matched_steps():
    t = _tracker(*STEPS)
    cfg = FilterConfig(name_contains="transform")
    output = render_filtered(t, cfg)
    assert "transform" in output
    assert "clean" not in output


def test_render_filtered_no_match_message():
    t = _tracker(*STEPS)
    cfg = FilterConfig(name_contains="nonexistent")
    output = render_filtered(t, cfg)
    assert "no steps matched" in output


def test_render_filtered_shows_step_count():
    t = _tracker(*STEPS)
    cfg = FilterConfig(min_duration_ms=100.0)
    output = render_filtered(t, cfg)
    assert "of 4 step(s) shown" in output

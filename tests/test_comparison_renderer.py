"""Tests for pipesight.comparison_renderer."""

from __future__ import annotations

from pipesight.comparator import compare_summaries
from pipesight.comparison_renderer import render_comparison


def _summary(steps, total_ms=None):
    if total_ms is None:
        total_ms = sum(s["duration_ms"] for s in steps)
    return {"steps": steps, "total_duration_ms": total_ms}


def _step(name, ms):
    return {"name": name, "duration_ms": ms}


def test_render_contains_step_names():
    before = _summary([_step("load", 100.0), _step("transform", 200.0)])
    after = _summary([_step("load", 120.0), _step("transform", 180.0)])
    result = compare_summaries(before, after)
    output = render_comparison(result, color=False)
    assert "load" in output
    assert "transform" in output


def test_render_regression_label():
    before = _summary([_step("slow_step", 50.0)])
    after = _summary([_step("slow_step", 200.0)])
    result = compare_summaries(before, after)
    output = render_comparison(result, color=False)
    assert "REGRESSION" in output


def test_render_improvement_label():
    before = _summary([_step("fast_step", 200.0)])
    after = _summary([_step("fast_step", 50.0)])
    result = compare_summaries(before, after)
    output = render_comparison(result, color=False)
    assert "IMPROVEMENT" in output


def test_render_ok_label():
    before = _summary([_step("stable", 100.0)])
    after = _summary([_step("stable", 102.0)])
    result = compare_summaries(before, after)
    output = render_comparison(result, color=False)
    assert "OK" in output


def test_render_shows_added_removed():
    before = _summary([_step("old", 50.0)])
    after = _summary([_step("new", 50.0)])
    result = compare_summaries(before, after)
    output = render_comparison(result, color=False)
    assert "Added steps" in output
    assert "new" in output
    assert "Removed steps" in output
    assert "old" in output


def test_render_total_line_present():
    before = _summary([_step("x", 100.0)], total_ms=100.0)
    after = _summary([_step("x", 150.0)], total_ms=150.0)
    result = compare_summaries(before, after)
    output = render_comparison(result, color=False)
    assert "Total:" in output


def test_render_with_color_does_not_crash():
    before = _summary([_step("x", 100.0)])
    after = _summary([_step("x", 50.0)])
    result = compare_summaries(before, after)
    output = render_comparison(result, color=True)
    assert "x" in output

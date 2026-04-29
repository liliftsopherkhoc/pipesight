"""Tests for pipesight.profile_renderer."""

from __future__ import annotations

import pytest

from pipesight.profiler import StepProfile
from pipesight.profile_renderer import render_profiles, _mem_color


def _make_profile(
    name: str,
    duration_ms: float = 100.0,
    memory_before_mb: float = 50.0,
    memory_after_mb: float = 60.0,
    cpu_percent: float = 12.5,
    rows_in: int = 1000,
    rows_out: int = 900,
) -> StepProfile:
    return StepProfile(
        step_name=name,
        duration_ms=duration_ms,
        memory_before_mb=memory_before_mb,
        memory_after_mb=memory_after_mb,
        cpu_percent=cpu_percent,
        rows_in=rows_in,
        rows_out=rows_out,
    )


# ---------------------------------------------------------------------------
# _mem_color
# ---------------------------------------------------------------------------

def test_mem_color_low():
    assert _mem_color(10.0) == "\033[32m"


def test_mem_color_medium():
    assert _mem_color(50.0) == "\033[33m"


def test_mem_color_high():
    assert _mem_color(150.0) == "\033[31m"


# ---------------------------------------------------------------------------
# render_profiles – empty input
# ---------------------------------------------------------------------------

def test_render_profiles_empty():
    result = render_profiles([])
    assert "No profile data" in result


# ---------------------------------------------------------------------------
# render_profiles – basic content checks (no color)
# ---------------------------------------------------------------------------

def test_render_profiles_contains_step_name():
    profiles = [_make_profile("load_csv")]
    result = render_profiles(profiles, use_color=False)
    assert "load_csv" in result


def test_render_profiles_contains_duration():
    profiles = [_make_profile("step_a", duration_ms=250.0)]
    result = render_profiles(profiles, use_color=False)
    assert "250" in result


def test_render_profiles_contains_total():
    profiles = [
        _make_profile("a", duration_ms=100.0),
        _make_profile("b", duration_ms=200.0),
    ]
    result = render_profiles(profiles, use_color=False)
    assert "TOTAL" in result


def test_render_profiles_total_sums_durations():
    profiles = [
        _make_profile("a", duration_ms=100.0),
        _make_profile("b", duration_ms=200.0),
    ]
    result = render_profiles(profiles, use_color=False)
    # 300 ms → format_duration should produce something with "300"
    assert "300" in result


def test_render_profiles_multiple_steps():
    profiles = [
        _make_profile("step_one"),
        _make_profile("step_two"),
    ]
    result = render_profiles(profiles, use_color=False)
    assert "step_one" in result
    assert "step_two" in result


def test_render_profiles_memory_delta_shown():
    profiles = [_make_profile("mem_step", memory_before_mb=40.0, memory_after_mb=65.0)]
    result = render_profiles(profiles, use_color=False)
    # delta = +25.0 MB
    assert "+25.0" in result


def test_render_profiles_na_when_memory_missing():
    p = StepProfile(
        step_name="no_mem",
        duration_ms=50.0,
        memory_before_mb=None,
        memory_after_mb=None,
        cpu_percent=None,
        rows_in=None,
        rows_out=None,
    )
    result = render_profiles([p], use_color=False)
    assert "n/a" in result


def test_render_profiles_with_color_contains_ansi():
    profiles = [_make_profile("colored")]
    result = render_profiles(profiles, use_color=True)
    assert "\033[" in result


def test_render_profiles_no_color_no_ansi():
    profiles = [_make_profile("plain")]
    result = render_profiles(profiles, use_color=False)
    assert "\033[" not in result

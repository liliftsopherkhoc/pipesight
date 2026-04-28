"""Tests for pipesight.renderer module."""

import pytest
from unittest.mock import patch
from pipesight.renderer import _bar, _color_for_fraction, render_tracker
from pipesight.tracker import PipelineTracker


# ---------------------------------------------------------------------------
# _bar
# ---------------------------------------------------------------------------

def test_bar_full():
    """A fraction of 1.0 should produce a fully filled bar."""
    result = _bar(1.0, width=10)
    assert len(result) == 10
    assert result == "█" * 10


def test_bar_empty():
    """A fraction of 0.0 should produce an empty bar."""
    result = _bar(0.0, width=10)
    assert len(result) == 10
    assert result == "░" * 10


def test_bar_half():
    """A fraction of 0.5 should fill roughly half the bar."""
    result = _bar(0.5, width=10)
    filled = result.count("█")
    assert filled == 5
    assert len(result) == 10


def test_bar_clamps_above_one():
    """Fractions > 1.0 should be clamped to a full bar."""
    result = _bar(2.5, width=8)
    assert result == "█" * 8


def test_bar_clamps_below_zero():
    """Negative fractions should be clamped to an empty bar."""
    result = _bar(-0.5, width=8)
    assert result == "░" * 8


# ---------------------------------------------------------------------------
# _color_for_fraction
# ---------------------------------------------------------------------------

def test_color_for_fraction_low():
    """Low fractions (fast steps) should return a green-ish ANSI code."""
    code = _color_for_fraction(0.1)
    # Just verify it returns a non-empty string with an ANSI escape
    assert "\033[" in code


def test_color_for_fraction_high():
    """High fractions (slow steps) should return a red-ish ANSI code."""
    low_code = _color_for_fraction(0.1)
    high_code = _color_for_fraction(0.9)
    # The two codes should differ — slow steps get a different colour
    assert low_code != high_code


def test_color_for_fraction_mid():
    """Mid-range fractions should return some valid ANSI code."""
    code = _color_for_fraction(0.5)
    assert "\033[" in code


# ---------------------------------------------------------------------------
# render_tracker  (uses a real PipelineTracker)
# ---------------------------------------------------------------------------

def _make_tracker():
    """Build a small tracker with two completed steps."""
    tracker = PipelineTracker()
    with tracker.track("load"):
        pass
    with tracker.track("transform"):
        pass
    return tracker


def test_render_tracker_returns_string():
    """render_tracker should return a non-empty string."""
    tracker = _make_tracker()
    output = render_tracker(tracker)
    assert isinstance(output, str)
    assert len(output) > 0


def test_render_tracker_contains_step_names():
    """Each step name should appear somewhere in the rendered output."""
    tracker = _make_tracker()
    output = render_tracker(tracker)
    assert "load" in output
    assert "transform" in output


def test_render_tracker_contains_bar_characters():
    """The rendered output should contain bar fill characters."""
    tracker = _make_tracker()
    output = render_tracker(tracker)
    assert "█" in output or "░" in output


def test_render_tracker_empty_pipeline():
    """Rendering an empty tracker should not raise and should return a string."""
    tracker = PipelineTracker()
    output = render_tracker(tracker)
    assert isinstance(output, str)


def test_render_tracker_shows_duration():
    """The rendered output should include some numeric duration information."""
    tracker = _make_tracker()
    output = render_tracker(tracker)
    # At minimum a digit should appear (ms or s values)
    assert any(ch.isdigit() for ch in output)

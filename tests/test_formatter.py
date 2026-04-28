"""Tests for pipesight.formatter."""

from __future__ import annotations

import pytest

from pipesight.formatter import (
    format_duration,
    format_rows,
    format_step_line,
    format_summary,
)
from pipesight.tracker import PipelineTracker, track


# ---------------------------------------------------------------------------
# format_duration
# ---------------------------------------------------------------------------

def test_format_duration_ms():
    assert format_duration(42.5) == "42.5ms"


def test_format_duration_seconds():
    result = format_duration(2_500.0)
    assert result == "2.50s"


def test_format_duration_minutes():
    result = format_duration(90_000.0)  # 1m 30s
    assert result.startswith("1m")
    assert "30.0s" in result


# ---------------------------------------------------------------------------
# format_rows
# ---------------------------------------------------------------------------

def test_format_rows_none():
    assert format_rows(None) == "—"


def test_format_rows_small():
    assert format_rows(500) == "500"


def test_format_rows_thousands():
    result = format_rows(1_200)
    assert result == "1.2k"


def test_format_rows_millions():
    result = format_rows(3_500_000)
    assert "M" in result


# ---------------------------------------------------------------------------
# format_step_line
# ---------------------------------------------------------------------------

def test_format_step_line_contains_name():
    line = format_step_line("load_csv", 100.0, 1000.0, 500)
    assert "load_csv" in line


def test_format_step_line_contains_percentage():
    line = format_step_line("load_csv", 250.0, 1000.0, None)
    assert "25.0%" in line


def test_format_step_line_zero_total_no_crash():
    line = format_step_line("step", 0.0, 0.0, 0)
    assert "step" in line


# ---------------------------------------------------------------------------
# format_summary
# ---------------------------------------------------------------------------

def _build_tracker() -> PipelineTracker:
    tracker = PipelineTracker()
    with track(tracker, "ingest", rows_out=1000):
        pass
    with track(tracker, "transform", rows_out=800):
        pass
    return tracker


def test_format_summary_contains_step_names():
    summary = format_summary(_build_tracker())
    assert "ingest" in summary
    assert "transform" in summary


def test_format_summary_contains_total_label():
    summary = format_summary(_build_tracker())
    assert "total" in summary.lower()


def test_format_summary_contains_slowest_label():
    summary = format_summary(_build_tracker())
    assert "Slowest step" in summary


def test_format_summary_marks_error_step():
    tracker = PipelineTracker()
    try:
        with track(tracker, "bad_step"):
            raise ValueError("oops")
    except ValueError:
        pass
    summary = format_summary(tracker)
    assert "✗" in summary
    assert "oops" in summary

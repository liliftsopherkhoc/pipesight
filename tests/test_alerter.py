"""Tests for pipesight.alerter and pipesight.alert_renderer."""
from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from pipesight.tracker import PipelineTracker
from pipesight.alerter import AlertRule, Alert, check_alerts
from pipesight.alert_renderer import render_alerts


def _make_tracker(steps: list[tuple[str, float, int | None]]) -> PipelineTracker:
    """Build a tracker with synthetic steps (name, duration_ms, rows)."""
    tracker = PipelineTracker()
    for name, duration_ms, rows in steps:
        result = MagicMock()
        result.name = name
        result.duration_ms = duration_ms
        result.row_count = rows
        result.error = None
        tracker.steps.append(result)
    return tracker


def _make_profile(step_name: str, memory_delta_mb: float):
    p = MagicMock()
    p.step_name = step_name
    p.memory_delta_mb = memory_delta_mb
    return p


# ---------------------------------------------------------------------------
# check_alerts — duration
# ---------------------------------------------------------------------------

def test_no_alerts_when_all_within_limits():
    tracker = _make_tracker([("load", 100.0, 1000), ("clean", 50.0, 900)])
    rule = AlertRule(max_duration_ms=500.0)
    alerts = check_alerts(tracker, rule)
    assert alerts == []


def test_duration_alert_fires():
    tracker = _make_tracker([("slow_step", 800.0, 500)])
    rule = AlertRule(max_duration_ms=500.0)
    alerts = check_alerts(tracker, rule)
    assert len(alerts) == 1
    assert alerts[0].step_name == "slow_step"
    assert any("duration" in v for v in alerts[0].violations)


def test_duration_alert_only_for_offending_step():
    tracker = _make_tracker([("fast", 10.0, 100), ("slow", 600.0, 100)])
    rule = AlertRule(max_duration_ms=200.0)
    alerts = check_alerts(tracker, rule)
    assert len(alerts) == 1
    assert alerts[0].step_name == "slow"


# ---------------------------------------------------------------------------
# check_alerts — memory
# ---------------------------------------------------------------------------

def test_memory_alert_fires_with_profile():
    tracker = _make_tracker([("transform", 50.0, 1000)])
    profiles = [_make_profile("transform", memory_delta_mb=300.0)]
    rule = AlertRule(max_memory_mb=100.0)
    alerts = check_alerts(tracker, rule, profiles=profiles)
    assert len(alerts) == 1
    assert any("memory" in v for v in alerts[0].violations)


def test_memory_alert_skipped_without_profile():
    tracker = _make_tracker([("transform", 50.0, 1000)])
    rule = AlertRule(max_memory_mb=100.0)
    alerts = check_alerts(tracker, rule, profiles=None)
    assert alerts == []


# ---------------------------------------------------------------------------
# check_alerts — throughput
# ---------------------------------------------------------------------------

def test_throughput_alert_fires_when_below_minimum():
    # 100 rows / 10 s = 10 rows/s  →  below 500 rows/s minimum
    tracker = _make_tracker([("ingest", 10_000.0, 100)])
    rule = AlertRule(min_throughput_rows_per_sec=500.0)
    alerts = check_alerts(tracker, rule)
    assert len(alerts) == 1
    assert any("throughput" in v for v in alerts[0].violations)


# ---------------------------------------------------------------------------
# Alert.is_critical
# ---------------------------------------------------------------------------

def test_alert_is_critical_with_multiple_violations():
    alert = Alert(step_name="x", violations=["v1", "v2"])
    assert alert.is_critical is True


def test_alert_not_critical_with_single_violation():
    alert = Alert(step_name="x", violations=["v1"])
    assert alert.is_critical is False


# ---------------------------------------------------------------------------
# render_alerts
# ---------------------------------------------------------------------------

def test_render_no_alerts_shows_ok():
    output = render_alerts([], color=False)
    assert "No alerts" in output


def test_render_alerts_contains_step_name():
    alerts = [Alert(step_name="bad_step", violations=["duration 999 ms exceeds limit 100 ms"])]
    output = render_alerts(alerts, color=False)
    assert "bad_step" in output


def test_render_alerts_contains_violation_text():
    alerts = [Alert(step_name="s", violations=["memory delta 500.00 MB exceeds limit 100.00 MB"])]
    output = render_alerts(alerts, color=False)
    assert "memory delta" in output


def test_render_critical_label_for_multiple_violations():
    alerts = [Alert(step_name="s", violations=["v1", "v2"])]
    output = render_alerts(alerts, color=False)
    assert "CRITICAL" in output


def test_render_warning_label_for_single_violation():
    alerts = [Alert(step_name="s", violations=["v1"])]
    output = render_alerts(alerts, color=False)
    assert "WARNING" in output

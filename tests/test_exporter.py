"""Tests for pipesight.exporter."""

from __future__ import annotations

import csv
import io
import json
import os
import tempfile

import pytest

from pipesight.tracker import PipelineTracker, StepResult
from pipesight.exporter import to_dict, to_json, to_csv, save


def _make_tracker() -> PipelineTracker:
    tracker = PipelineTracker(name="test_pipe")
    tracker.steps.append(
        StepResult(name="load", duration_ms=120.5, rows_in=None, rows_out=1000)
    )
    tracker.steps.append(
        StepResult(name="filter", duration_ms=45.0, rows_in=1000, rows_out=750)
    )
    tracker.steps.append(
        StepResult(name="transform", duration_ms=200.0, rows_in=750, rows_out=750, error=None)
    )
    return tracker


def test_to_dict_structure():
    tracker = _make_tracker()
    result = to_dict(tracker)
    assert result["pipeline"] == "test_pipe"
    assert len(result["steps"]) == 3
    assert result["steps"][1]["name"] == "filter"
    assert result["steps"][1]["rows_delta"] == -250


def test_to_dict_total_duration():
    tracker = _make_tracker()
    result = to_dict(tracker)
    assert result["total_duration_ms"] == pytest.approx(365.5)


def test_to_json_valid():
    tracker = _make_tracker()
    raw = to_json(tracker)
    parsed = json.loads(raw)
    assert parsed["pipeline"] == "test_pipe"
    assert isinstance(parsed["steps"], list)


def test_to_csv_has_header_and_rows():
    tracker = _make_tracker()
    raw = to_csv(tracker)
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 3
    assert rows[0]["name"] == "load"
    assert rows[1]["rows_delta"] == "-250"


def test_to_csv_error_field_empty_when_none():
    tracker = _make_tracker()
    raw = to_csv(tracker)
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert rows[0]["error"] == ""


def test_save_json(tmp_path):
    tracker = _make_tracker()
    out = tmp_path / "summary.json"
    save(tracker, str(out), fmt="json")
    assert out.exists()
    parsed = json.loads(out.read_text())
    assert parsed["pipeline"] == "test_pipe"


def test_save_csv(tmp_path):
    tracker = _make_tracker()
    out = tmp_path / "summary.csv"
    save(tracker, str(out), fmt="csv")
    assert out.exists()
    content = out.read_text()
    assert "filter" in content


def test_save_unsupported_format(tmp_path):
    tracker = _make_tracker()
    with pytest.raises(ValueError, match="Unsupported export format"):
        save(tracker, str(tmp_path / "out.xml"), fmt="xml")

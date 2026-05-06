"""Tests for pipesight.diff_exporter."""
from __future__ import annotations

import csv
import io
import json
import tempfile
from pathlib import Path

import pytest

from pipesight.differ import diff_trackers
from pipesight.diff_exporter import diff_to_csv, diff_to_dict, diff_to_json, save_diff
from pipesight.tracker import PipelineTracker, StepResult


def _make_tracker(*steps):
    t = PipelineTracker()
    for name, duration_ms, rows_out in steps:
        t.steps.append(
            StepResult(name=name, duration_ms=duration_ms, rows_in=None, rows_out=rows_out)
        )
    return t


def _make_result():
    prev = _make_tracker(("load", 100.0, 1000), ("clean", 50.0, 900))
    curr = _make_tracker(("load", 120.0, 1000), ("clean", 40.0, 900))
    return diff_trackers(prev, curr)


def test_diff_to_dict_has_keys():
    d = diff_to_dict(_make_result())
    assert "total_duration_delta_ms" in d
    assert "deltas" in d
    assert "added_steps" in d
    assert "removed_steps" in d


def test_diff_to_dict_delta_fields():
    d = diff_to_dict(_make_result())
    delta = d["deltas"][0]
    assert "name" in delta
    assert "prev_ms" in delta
    assert "curr_ms" in delta
    assert "duration_delta_ms" in delta
    assert "pct_change" in delta


def test_diff_to_json_valid():
    raw = diff_to_json(_make_result())
    parsed = json.loads(raw)
    assert isinstance(parsed["deltas"], list)


def test_diff_to_csv_has_header():
    raw = diff_to_csv(_make_result())
    reader = csv.DictReader(io.StringIO(raw))
    assert "name" in reader.fieldnames
    assert "duration_delta_ms" in reader.fieldnames


def test_diff_to_csv_row_count():
    raw = diff_to_csv(_make_result())
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 2


def test_save_diff_json(tmp_path):
    out = tmp_path / "diff.json"
    save_diff(_make_result(), str(out), fmt="json")
    assert out.exists()
    parsed = json.loads(out.read_text())
    assert "deltas" in parsed


def test_save_diff_csv(tmp_path):
    out = tmp_path / "diff.csv"
    save_diff(_make_result(), str(out), fmt="csv")
    assert out.exists()
    assert "name" in out.read_text()


def test_save_diff_invalid_format(tmp_path):
    out = tmp_path / "diff.txt"
    with pytest.raises(ValueError, match="Unsupported format"):
        save_diff(_make_result(), str(out), fmt="xml")

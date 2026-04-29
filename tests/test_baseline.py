"""Tests for pipesight.baseline."""

from __future__ import annotations

import json
import pytest

from pipesight.baseline import (
    baseline_exists,
    clear_baseline,
    load_baseline,
    promote_to_baseline,
    save_baseline,
)

_SAMPLE: dict = {
    "steps": [
        {"name": "load", "duration_ms": 120.0, "rows_in": None, "rows_out": 1000},
        {"name": "filter", "duration_ms": 45.0, "rows_in": 1000, "rows_out": 800},
    ],
    "total_duration_ms": 165.0,
}


def test_save_and_load_roundtrip(tmp_path):
    path = str(tmp_path / "baseline.json")
    save_baseline(_SAMPLE, path)
    result = load_baseline(path)
    assert result == _SAMPLE


def test_load_returns_none_when_missing(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    assert load_baseline(path) is None


def test_load_returns_none_on_corrupt_file(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not valid json", encoding="utf-8")
    assert load_baseline(str(path)) is None


def test_baseline_exists_false_when_missing(tmp_path):
    path = str(tmp_path / "nope.json")
    assert baseline_exists(path) is False


def test_baseline_exists_true_after_save(tmp_path):
    path = str(tmp_path / "bl.json")
    save_baseline(_SAMPLE, path)
    assert baseline_exists(path) is True


def test_clear_baseline_removes_file(tmp_path):
    path = str(tmp_path / "bl.json")
    save_baseline(_SAMPLE, path)
    removed = clear_baseline(path)
    assert removed is True
    assert not baseline_exists(path)


def test_clear_baseline_returns_false_when_missing(tmp_path):
    path = str(tmp_path / "ghost.json")
    assert clear_baseline(path) is False


def test_promote_to_baseline_copies_content(tmp_path):
    source = tmp_path / "export.json"
    source.write_text(json.dumps(_SAMPLE), encoding="utf-8")
    dest = str(tmp_path / "baseline.json")
    promote_to_baseline(str(source), dest)
    assert load_baseline(dest) == _SAMPLE


def test_promote_to_baseline_raises_for_missing_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        promote_to_baseline(str(tmp_path / "missing.json"), str(tmp_path / "bl.json"))

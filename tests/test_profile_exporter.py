"""Tests for pipesight.profile_exporter."""
from __future__ import annotations

import csv
import io
import json
import os
import tempfile

import pytest

from pipesight.profiler import StepProfile
from pipesight.profile_exporter import (
    profile_to_dict,
    profiles_to_json,
    profiles_to_csv,
    save_profiles,
)


def _make_profiles():
    return [
        StepProfile("load", 120.5, memory_before_mb=80.0, memory_after_mb=95.0, cpu_percent=12.3),
        StepProfile("transform", 340.0, memory_before_mb=95.0, memory_after_mb=110.0, cpu_percent=45.0),
    ]


def test_profile_to_dict_keys():
    p = StepProfile("load", 50.0)
    d = profile_to_dict(p)
    expected_keys = {"step_name", "duration_ms", "memory_before_mb", "memory_after_mb", "memory_delta_mb", "cpu_percent"}
    assert set(d.keys()) == expected_keys


def test_profile_to_dict_values():
    p = StepProfile("load", 50.0, memory_before_mb=10.0, memory_after_mb=20.0, cpu_percent=5.0)
    d = profile_to_dict(p)
    assert d["step_name"] == "load"
    assert d["duration_ms"] == 50.0
    assert d["memory_delta_mb"] == pytest.approx(10.0, abs=1e-3)


def test_profiles_to_json_valid():
    profiles = _make_profiles()
    raw = profiles_to_json(profiles)
    data = json.loads(raw)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["step_name"] == "load"


def test_profiles_to_csv_has_header():
    profiles = _make_profiles()
    raw = profiles_to_csv(profiles)
    reader = csv.DictReader(io.StringIO(raw))
    rows = list(reader)
    assert len(rows) == 2
    assert "step_name" in reader.fieldnames
    assert "memory_delta_mb" in reader.fieldnames


def test_profiles_to_csv_values():
    profiles = _make_profiles()
    raw = profiles_to_csv(profiles)
    reader = csv.DictReader(io.StringIO(raw))
    first = next(iter(reader))
    assert first["step_name"] == "load"
    assert float(first["duration_ms"]) == pytest.approx(120.5)


def test_save_profiles_json(tmp_path):
    profiles = _make_profiles()
    out = str(tmp_path / "profiles.json")
    save_profiles(profiles, out, fmt="json")
    with open(out) as fh:
        data = json.load(fh)
    assert len(data) == 2


def test_save_profiles_csv(tmp_path):
    profiles = _make_profiles()
    out = str(tmp_path / "profiles.csv")
    save_profiles(profiles, out, fmt="csv")
    with open(out) as fh:
        content = fh.read()
    assert "step_name" in content


def test_save_profiles_invalid_format(tmp_path):
    profiles = _make_profiles()
    with pytest.raises(ValueError, match="Unsupported format"):
        save_profiles(profiles, str(tmp_path / "x.txt"), fmt="xml")

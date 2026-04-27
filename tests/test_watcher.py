"""Tests for pipesight.watcher."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from pipesight.tracker import PipelineTracker, StepResult
from pipesight.watcher import _mtime, _load_and_run, watch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SCRIPT_GOOD = textwrap.dedent("""\
    from pipesight.tracker import PipelineTracker, StepResult
    tracker = PipelineTracker(name="watched")
    tracker.steps.append(StepResult(name="step1", duration_ms=50.0, rows_in=100, rows_out=80))
""")

_SCRIPT_NO_TRACKER = textwrap.dedent("""\
    x = 42
""")

_SCRIPT_ERROR = textwrap.dedent("""\
    raise RuntimeError("boom")
""")


# ---------------------------------------------------------------------------
# _mtime
# ---------------------------------------------------------------------------

def test_mtime_returns_zero_for_missing_file():
    assert _mtime("/no/such/file.py") == 0.0


def test_mtime_returns_positive_for_existing_file(tmp_path):
    f = tmp_path / "script.py"
    f.write_text("pass")
    assert _mtime(str(f)) > 0.0


# ---------------------------------------------------------------------------
# _load_and_run
# ---------------------------------------------------------------------------

def test_load_and_run_returns_tracker(tmp_path):
    script = tmp_path / "pipe.py"
    script.write_text(_SCRIPT_GOOD)
    result = _load_and_run(str(script))
    assert isinstance(result, PipelineTracker)
    assert result.name == "watched"


def test_load_and_run_returns_none_when_no_tracker(tmp_path):
    script = tmp_path / "no_tracker.py"
    script.write_text(_SCRIPT_NO_TRACKER)
    result = _load_and_run(str(script))
    assert result is None


def test_load_and_run_propagates_script_error(tmp_path):
    script = tmp_path / "bad.py"
    script.write_text(_SCRIPT_ERROR)
    with pytest.raises(RuntimeError, match="boom"):
        _load_and_run(str(script))


# ---------------------------------------------------------------------------
# watch (limited iterations)
# ---------------------------------------------------------------------------

def test_watch_calls_on_update(tmp_path):
    script = tmp_path / "pipe.py"
    script.write_text(_SCRIPT_GOOD)

    received: list[PipelineTracker] = []

    with patch("pipesight.watcher.time.sleep"):  # skip real sleeping
        watch(
            str(script),
            interval=0.0,
            on_update=received.append,
            max_iterations=2,
        )

    assert len(received) >= 1
    assert received[0].name == "watched"


def test_watch_handles_script_error_gracefully(tmp_path, capsys):
    script = tmp_path / "bad.py"
    script.write_text(_SCRIPT_ERROR)

    with patch("pipesight.watcher.time.sleep"):
        watch(
            str(script),
            interval=0.0,
            on_update=lambda t: None,
            max_iterations=1,
        )

    captured = capsys.readouterr()
    assert "Error running script" in captured.out

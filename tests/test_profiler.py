"""Tests for pipesight.profiler."""
from __future__ import annotations

import pytest

from pipesight.profiler import StepProfile, profile_tracker, ProfilingTracker
from pipesight.tracker import PipelineTracker


# ---------------------------------------------------------------------------
# StepProfile
# ---------------------------------------------------------------------------

def test_step_profile_memory_delta_computed():
    p = StepProfile("load", 10.0, memory_before_mb=100.0, memory_after_mb=115.5)
    assert p.memory_delta_mb == pytest.approx(15.5, abs=1e-3)


def test_step_profile_memory_delta_none_when_missing():
    p = StepProfile("load", 10.0)
    assert p.memory_delta_mb is None


def test_step_profile_memory_delta_none_partial():
    p = StepProfile("load", 10.0, memory_before_mb=50.0)
    assert p.memory_delta_mb is None


# ---------------------------------------------------------------------------
# profile_tracker
# ---------------------------------------------------------------------------

def _make_tracker() -> PipelineTracker:
    import pandas as pd
    tracker = PipelineTracker()
    df = pd.DataFrame({"a": range(10)})
    tracker.track("step_one", df)
    tracker.track("step_two", df.head(5))
    return tracker


def test_profile_tracker_returns_one_profile_per_step():
    tracker = _make_tracker()
    profiles = profile_tracker(tracker)
    assert len(profiles) == len(tracker.steps)


def test_profile_tracker_step_names_match():
    tracker = _make_tracker()
    profiles = profile_tracker(tracker)
    assert [p.step_name for p in profiles] == [s.name for s in tracker.steps]


def test_profile_tracker_no_memory_data():
    tracker = _make_tracker()
    profiles = profile_tracker(tracker)
    for p in profiles:
        assert p.memory_before_mb is None
        assert p.memory_after_mb is None


# ---------------------------------------------------------------------------
# ProfilingTracker
# ---------------------------------------------------------------------------

def test_profiling_tracker_records_profiles():
    import pandas as pd
    inner = PipelineTracker()
    pt = ProfilingTracker(inner)
    df = pd.DataFrame({"x": range(20)})
    pt.track("load", df)
    pt.track("filter", df.head(10))
    assert len(pt.profiles) == 2


def test_profiling_tracker_profile_names():
    import pandas as pd
    inner = PipelineTracker()
    pt = ProfilingTracker(inner)
    df = pd.DataFrame({"x": range(5)})
    pt.track("alpha", df)
    assert pt.profiles[0].step_name == "alpha"


def test_profiling_tracker_delegates_steps():
    import pandas as pd
    inner = PipelineTracker()
    pt = ProfilingTracker(inner)
    df = pd.DataFrame({"x": range(5)})
    pt.track("beta", df)
    # steps attribute comes from the inner tracker via __getattr__
    assert len(pt.steps) == 1
    assert pt.steps[0].name == "beta"

"""Tests for pipesight.reporter, .report_renderer, and .report_exporter."""
from __future__ import annotations

import os
import tempfile

import pytest

from pipesight.tracker import PipelineTracker
from pipesight.reporter import build_report, ReportSection
from pipesight.report_renderer import render_markdown, render_html
from pipesight.report_exporter import save_report
from pipesight.profiler import StepProfile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tracker() -> PipelineTracker:
    t = PipelineTracker()
    with t.track("load"):
        pass
    t.steps[-1].rows_out = 1000
    t.steps[-1].duration_ms = 120.0
    with t.track("transform"):
        pass
    t.steps[-1].rows_out = 950
    t.steps[-1].duration_ms = 450.0
    return t


def _make_profiles() -> list:
    return [
        StepProfile(
            step_name="load",
            mem_before_mb=50.0,
            mem_after_mb=80.0,
            cpu_percent=12.5,
        ),
    ]


# ---------------------------------------------------------------------------
# reporter.build_report
# ---------------------------------------------------------------------------

def test_build_report_returns_sections():
    t = _make_tracker()
    sections = build_report(t)
    assert len(sections) >= 1
    assert all(isinstance(s, ReportSection) for s in sections)


def test_build_report_step_section_has_correct_headers():
    t = _make_tracker()
    sections = build_report(t)
    step_section = sections[0]
    assert "Step" in step_section.headers
    assert "Duration" in step_section.headers


def test_build_report_includes_profile_section_when_provided():
    t = _make_tracker()
    profiles = _make_profiles()
    sections = build_report(t, profiles=profiles)
    titles = [s.title for s in sections]
    assert "Resource Profiles" in titles


def test_build_report_no_profile_section_without_profiles():
    t = _make_tracker()
    sections = build_report(t)
    titles = [s.title for s in sections]
    assert "Resource Profiles" not in titles


# ---------------------------------------------------------------------------
# report_renderer
# ---------------------------------------------------------------------------

def test_render_markdown_contains_heading():
    t = _make_tracker()
    sections = build_report(t)
    md = render_markdown(sections)
    assert "# PipeSight Report" in md


def test_render_markdown_contains_step_names():
    t = _make_tracker()
    sections = build_report(t)
    md = render_markdown(sections)
    assert "load" in md
    assert "transform" in md


def test_render_html_is_valid_html():
    t = _make_tracker()
    sections = build_report(t)
    html = render_html(sections)
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html


def test_render_html_contains_table():
    t = _make_tracker()
    sections = build_report(t)
    html = render_html(sections)
    assert "<table" in html
    assert "</table>" in html


# ---------------------------------------------------------------------------
# report_exporter.save_report
# ---------------------------------------------------------------------------

def test_save_report_markdown_creates_file():
    t = _make_tracker()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "report.md")
        result = save_report(t, path, fmt="markdown")
        assert os.path.isfile(result)
        assert result.endswith("report.md")


def test_save_report_html_creates_file():
    t = _make_tracker()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "report.html")
        result = save_report(t, path, fmt="html")
        content = open(result).read()
        assert "<!DOCTYPE html>" in content


def test_save_report_invalid_format_raises():
    t = _make_tracker()
    with pytest.raises(ValueError, match="Unsupported format"):
        save_report(t, "/tmp/x.txt", fmt="pdf")

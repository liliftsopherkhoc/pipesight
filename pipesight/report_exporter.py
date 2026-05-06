"""Save rendered reports to disk."""
from __future__ import annotations

import os
from typing import List, Optional

from pipesight.reporter import ReportSection, build_report
from pipesight.report_renderer import render_markdown, render_html
from pipesight.tracker import PipelineTracker
from pipesight.profiler import StepProfile


def save_report(
    tracker: PipelineTracker,
    path: str,
    fmt: str = "markdown",
    profiles: Optional[List[StepProfile]] = None,
) -> str:
    """Build and save a report.  Returns the absolute path written.

    Parameters
    ----------
    tracker: PipelineTracker
    path:    Destination file path (e.g. ``report.md`` or ``report.html``).
    fmt:     ``'markdown'`` or ``'html'``.
    profiles: Optional profiling data to include.
    """
    if fmt not in ("markdown", "html"):
        raise ValueError(f"Unsupported format '{fmt}'. Choose 'markdown' or 'html'.")

    sections: List[ReportSection] = build_report(tracker, profiles=profiles)

    if fmt == "html":
        content = render_html(sections)
    else:
        content = render_markdown(sections)

    abs_path = os.path.abspath(path)
    os.makedirs(os.path.dirname(abs_path) or ".", exist_ok=True)
    with open(abs_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return abs_path

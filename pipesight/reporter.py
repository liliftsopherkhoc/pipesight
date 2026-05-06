"""Generate a structured HTML or Markdown report from a pipeline run."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from pipesight.tracker import PipelineTracker
from pipesight.annotator import annotate, bottlenecks, StepAnnotation
from pipesight.formatter import format_duration, format_rows
from pipesight.profiler import StepProfile


@dataclass
class ReportSection:
    title: str
    rows: List[List[str]]  # each inner list is a table row
    headers: List[str]


def _step_table(annotations: List[StepAnnotation]) -> ReportSection:
    headers = ["Step", "Duration", "Rows Out", "Throughput", "Badge"]
    rows = [
        [
            ann.step.name,
            format_duration(ann.step.duration_ms),
            format_rows(ann.step.rows_out),
            f"{ann.throughput_rows_per_sec:.0f} rows/s" if ann.throughput_rows_per_sec is not None else "—",
            ann.badge,
        ]
        for ann in annotations
    ]
    return ReportSection(title="Pipeline Steps", rows=rows, headers=headers)


def _profile_table(profiles: List[StepProfile]) -> Optional[ReportSection]:
    if not profiles:
        return None
    headers = ["Step", "CPU %", "Mem Before (MB)", "Mem After (MB)", "Mem Delta (MB)"]
    rows = [
        [
            p.step_name,
            f"{p.cpu_percent:.1f}" if p.cpu_percent is not None else "—",
            f"{p.mem_before_mb:.1f}" if p.mem_before_mb is not None else "—",
            f"{p.mem_after_mb:.1f}" if p.mem_after_mb is not None else "—",
            f"{p.memory_delta_mb:.1f}" if p.memory_delta_mb is not None else "—",
        ]
        for p in profiles
    ]
    return ReportSection(title="Resource Profiles", rows=rows, headers=headers)


def build_report(
    tracker: PipelineTracker,
    profiles: Optional[List[StepProfile]] = None,
) -> List[ReportSection]:
    """Return a list of ReportSections summarising the pipeline run."""
    annotations = annotate(tracker)
    sections: List[ReportSection] = [_step_table(annotations)]
    if profiles:
        prof_section = _profile_table(profiles)
        if prof_section:
            sections.append(prof_section)
    bns = bottlenecks(annotations)
    if bns:
        bn_rows = [[b.step.name, b.badge, format_duration(b.step.duration_ms)] for b in bns]
        sections.append(ReportSection(title="Bottlenecks", rows=bn_rows, headers=["Step", "Badge", "Duration"]))
    return sections

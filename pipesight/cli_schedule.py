"""CLI sub-command: `pipesight schedule`."""
from __future__ import annotations

import argparse
import sys
import importlib.util
from pathlib import Path
from typing import Optional

from pipesight.tracker import PipelineTracker
from pipesight.scheduler import ScheduleConfig, run_scheduled
from pipesight.schedule_renderer import render_schedule_state


def _load_tracker_from_script(script_path: str) -> Optional[PipelineTracker]:
    path = Path(script_path).resolve()
    spec = importlib.util.spec_from_file_location("_pipesight_script", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return getattr(module, "tracker", None)


def build_schedule_parser(parent: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = parent.add_parser("schedule", help="Re-run a pipeline script on a fixed interval.")
    p.add_argument("script", help="Path to a Python script that exposes a `tracker` variable.")
    p.add_argument(
        "--interval",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="Seconds between runs (default: 5).",
    )
    p.add_argument(
        "--runs",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of runs (default: unlimited).",
    )
    p.set_defaults(func=run_schedule_cmd)


def run_schedule_cmd(args: argparse.Namespace) -> int:
    script = args.script
    interval: float = args.interval
    max_runs: Optional[int] = args.runs

    def factory() -> PipelineTracker:
        tracker = _load_tracker_from_script(script)
        if tracker is None:
            raise RuntimeError(f"No `tracker` variable found in {script!r}")
        return tracker

    def on_result(tracker: PipelineTracker, run_count: int) -> None:
        # Clear screen and re-render
        print("\033[2J\033[H", end="")
        from pipesight.scheduler import ScheduleState  # local import to avoid circularity
        dummy = ScheduleState(run_count=run_count, last_tracker=tracker)
        print(render_schedule_state(dummy, interval, max_runs))

    def on_error(exc: Exception, run_count: int) -> None:
        print(f"[run {run_count} ERROR] {exc}", file=sys.stderr)

    config = ScheduleConfig(
        interval_seconds=interval,
        max_runs=max_runs,
        on_result=on_result,
        on_error=on_error,
    )
    try:
        run_scheduled(factory, config)
    except KeyboardInterrupt:
        print("\nScheduler stopped.")
    return 0

"""Entry-point CLI for pipesight."""

import json
import sys
import argparse

from pipesight.renderer import render_tracker
from pipesight.tracker import PipelineTracker


def _load_summary(path: str) -> dict:
    with open(path) as fh:
        return json.load(fh)


def _tracker_from_summary(data: dict) -> PipelineTracker:
    tracker = PipelineTracker(name=data["pipeline"])
    for s in data.get("steps", []):
        from pipesight.tracker import StepResult
        tracker.steps.append(
            StepResult(
                name=s["name"],
                duration_ms=s["duration_ms"],
                input_rows=s.get("input_rows"),
                output_rows=s.get("output_rows"),
                error=s.get("error"),
            )
        )
    return tracker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pipesight",
        description="Visualize and profile pandas/polars pipeline bottlenecks.",
    )
    sub = parser.add_subparsers(dest="command")

    show = sub.add_parser("show", help="Render a saved pipeline summary JSON.")
    show.add_argument("file", help="Path to summary JSON produced by PipelineTracker.")
    show.add_argument("--json", action="store_true", help="Print raw JSON summary.")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "show":
        data = _load_summary(args.file)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            tracker = _tracker_from_summary(data)
            print(render_tracker(tracker))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()

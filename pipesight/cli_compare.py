"""CLI subcommand: compare two exported pipeline JSON summaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pipesight.comparator import compare_summaries
from pipesight.comparison_renderer import render_comparison


def _load_json(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        print(f"[pipesight] File not found: {path}", file=sys.stderr)
        sys.exit(1)
    with p.open() as fh:
        return json.load(fh)


def build_compare_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser(
        "compare",
        help="Compare two pipeline JSON exports and show regressions/improvements.",
    )
    p.add_argument("before", metavar="BEFORE_JSON", help="Path to the baseline summary JSON.")
    p.add_argument("after", metavar="AFTER_JSON", help="Path to the new summary JSON.")
    p.add_argument(
        "--no-color",
        action="store_true",
        default=False,
        help="Disable ANSI color output.",
    )
    p.set_defaults(func=run_compare)


def run_compare(args: argparse.Namespace) -> None:
    before = _load_json(args.before)
    after = _load_json(args.after)
    result = compare_summaries(before, after)
    use_color = not args.no_color
    print(render_comparison(result, color=use_color))
    # Exit with non-zero code if any regressions detected
    if any(d.is_regression for d in result.step_diffs):
        sys.exit(2)

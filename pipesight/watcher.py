"""File-system watcher: re-run a pipeline script and refresh the display."""

from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional

from pipesight.tracker import PipelineTracker
from pipesight.renderer import render_tracker


def _mtime(path: str) -> float:
    """Return the last-modified timestamp for *path*, or 0.0 if missing."""
    try:
        return os.path.getmtime(path)
    except FileNotFoundError:
        return 0.0


def _load_and_run(script_path: str) -> Optional[PipelineTracker]:
    """Execute *script_path* and return the last PipelineTracker it produced."""
    spec = importlib.util.spec_from_file_location("_pipesight_watched", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load script: {script_path}")
    module = importlib.util.module_from_spec(spec)
    # Ensure the script can import its own siblings
    script_dir = str(Path(script_path).parent.resolve())
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    # Convention: script exposes a module-level `tracker` variable
    return getattr(module, "tracker", None)


def watch(
    script_path: str,
    interval: float = 1.0,
    on_update: Optional[Callable[[PipelineTracker], None]] = None,
    max_iterations: Optional[int] = None,
) -> None:
    """Poll *script_path* for changes and re-render the tracker on each change.

    Parameters
    ----------
    script_path:
        Path to a Python script that defines a ``tracker`` variable.
    interval:
        Polling interval in seconds.
    on_update:
        Optional callback invoked with the new tracker after each reload.
        Defaults to printing via :func:`render_tracker`.
    max_iterations:
        Stop after this many poll cycles (useful for testing).

    Raises
    ------
    FileNotFoundError
        If *script_path* does not exist when ``watch`` is first called.
    """
    resolved = str(Path(script_path).resolve())
    if not os.path.isfile(resolved):
        raise FileNotFoundError(f"[pipesight] Script not found: {script_path!r}")

    if on_update is None:
        on_update = lambda t: print(render_tracker(t))

    last_mtime = 0.0
    iterations = 0

    print(f"[pipesight] Watching {script_path!r} (interval={interval}s) …")
    try:
        while True:
            current_mtime = _mtime(resolved)
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                try:
                    tracker = _load_and_run(resolved)
                    if tracker is not None:
                        on_update(tracker)
                    else:
                        print(
                            "[pipesight] Warning: script did not expose a "
                            "`tracker` variable."
                        )
                except Exception as exc:  # noqa: BLE001
                    print(f"[pipesight] Error running script: {exc}")
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[pipesight] Stopped watching.")

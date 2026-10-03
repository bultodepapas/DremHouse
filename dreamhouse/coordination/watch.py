"""Debounce repository edits through the same complete-candidate builder."""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path
from threading import Event

from dreamhouse.coordination.model import ROOT, dependency_hashes, digest


def build_fresh_process(project_path: Path, out: Path, *, visuals: bool = False) -> dict:
    """Reload all Python consumers on every watch rebuild, including changed loaders."""
    program = (
        "import json, sys; from pathlib import Path; "
        "from dreamhouse.coordination.pipeline import build_candidate; "
        "result = build_candidate(Path(sys.argv[1]), Path(sys.argv[2]), "
        "visuals=sys.argv[3] == 'yes'); print(json.dumps(result))"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            program,
            str(project_path.resolve()),
            str(out.resolve()),
            "yes" if visuals else "no",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Build failed")
    return json.loads(result.stdout)


def watch_sources(
    project_path: Path,
    build: Callable[[], dict],
    *,
    stop: Event | None = None,
    interval: float = 0.5,
    debounce: float = 0.75,
    notify: Callable[[str], None] = print,
    fingerprint: Callable[[], str] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> None:
    """Build on stable input changes; failed input/builds preserve the prior package.

    No generated output participates in the fingerprint. A failing fingerprint (for
    example a JSON file mid-save) is retried, never accepted as a successful revision.
    The caller owns output locking and atomic publication via ``build_candidate``.
    """
    if any(not math.isfinite(v) or v < 0 for v in (interval, debounce)) or interval == 0:
        raise ValueError("Watch interval must be positive and debounce nonnegative")
    stop = stop if stop is not None else Event()
    fingerprint = fingerprint or (lambda: digest(dependency_hashes(project_path)))
    observed = None
    attempted = None
    stable_since = clock()
    last_error = None
    while not stop.is_set():
        try:
            current = fingerprint()
            if current != observed:
                observed, stable_since = current, clock()
            if observed != attempted and clock() - stable_since >= debounce:
                try:
                    result = build()
                    notify(f"Built review: {result['path']}/index.html")
                    last_error = None
                except (ValueError, TypeError, KeyError, OSError, RuntimeError) as exc:
                    message = f"Review unchanged: {exc}"
                    if message != last_error:
                        notify(message)
                    last_error = message
                attempted = observed
        except (ValueError, TypeError, KeyError, OSError, RuntimeError) as exc:
            # Partial JSON saves are a transient input state, not a stable revision.
            observed, attempted = None, None
            message = f"Waiting for valid source inputs: {exc}"
            if message != last_error:
                notify(message)
            last_error = message
        stop.wait(interval)

#!/usr/bin/env python3
"""Capture or check README previews from the verified current visual review release.

These are dated review snapshots, never adopted drawing aliases. Run explicitly after
building a release; ordinary source edits do not silently promote publication assets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dreamhouse.coordination.publication import read_current_release

DESTINATION = ROOT / ".github/assets/coordination"
VIEWS = (
    "plan-pb", "plan-p2", "stair-sections",
    "drawings/architecture-ground-floor", "drawings/architecture-upper-floor",
)


def preview_files(release_root: Path) -> dict[str, bytes]:
    release = read_current_release(release_root, require_fresh=True)
    files = {}
    for view in VIEWS:
        for suffix in ("svg", "png"):
            name = f"{view}.{suffix}"
            contents = (Path(release["path"]) / name).read_bytes()
            if hashlib.sha256(contents).hexdigest() != release["release"]["artifacts"].get(name):
                raise RuntimeError(f"Review preview changed during export: {name}")
            files[name] = contents
    current = read_current_release(release_root, require_fresh=True)
    if current["release_id"] != release["release_id"]:
        raise RuntimeError("Selected review changed during preview export")
    manifest = {
        "schema_version": 1,
        "status": "review snapshot; not for construction; not an adopted drawing issue",
        "release_id": release["release_id"],
        "source_input_hash": release["release"]["source_input_hash"],
        "source_model_hash": release["release"]["source_model_hash"],
        "artifacts": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
    }
    files["manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = preview_files(ROOT / ".build/coordination/published")
    if args.write:
        DESTINATION.mkdir(parents=True, exist_ok=True)
        for name, contents in files.items():
            path = DESTINATION / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(contents)
    else:
        for name, contents in files.items():
            path = DESTINATION / name
            if not path.is_file() or path.read_bytes() != contents:
                raise SystemExit(f"Stale README preview: {name}; rebuild release and use --write")
    print(f"{'Updated' if args.write else 'Verified'} {len(VIEWS)} SVG/PNG review previews.")


if __name__ == "__main__":
    main()

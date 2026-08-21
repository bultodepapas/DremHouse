"""Generate the D-074 P2 issue from the shared stair-core model."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.architecture.stair_core import load_stair_core
from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b23 import load_b23_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b23_delta.json")
DELTA = Path(__file__).with_name("p2_b24_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b24_p2"


def load_b24_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b23_delta.json changed; review the b24 delta before regenerating")

    model = deepcopy(load_b23_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    model["stair_core_source"] = delta["stair_core"]
    model["stair_core"] = load_stair_core(ROOT / delta["stair_core"])
    model["design_basis"].append("D-074 shared PB/P2 stair-core geometry SC-01")
    door_change = delta["change"]["stair_door"]
    stair_door = next(item for item in model["doors"] if item["id"] == door_change["id"])
    stair_door["at"] = door_change["at"]
    stair_door["width"] = door_change["width"]
    model["design_notes"].extend(
        [
            "D-074 uses the same two-flight dogleg geometry in PB and P2.",
            "The P2 stair door aligns with the upper-flight top platform at the Great Wall.",
            "The four D-048 column reservations retain their exact SC-01 coordinates.",
            "CF-011 remains open because the current rear door meets the +1.90 m intermediate-landing plane rather than PB grade.",
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b24_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b24.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

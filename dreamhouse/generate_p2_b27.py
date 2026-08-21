"""Generate the D-082 P2 rescue-window and vertical foldout-ladder issue."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b26 import load_b26_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b26_delta.json")
DELTA = Path(__file__).with_name("p2_b27_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b27_p2"


def load_b27_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b26_delta.json changed; review the b27 delta before regenerating")

    model = deepcopy(load_b26_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    change = delta["change"]
    model["windows"].append(deepcopy(change["rescue_window"]))
    model["egress_reserve"] = deepcopy(change["egress_reserve"])
    model["design_basis"].append(
        "D-082 rear rescue window and wall-mounted vertical foldout escape-ladder reserve"
    )
    model["design_notes"].extend(
        [
            "D-082 replaces the incorrect inclined retractable-stair concept; the fixed rail remains vertical against the rear facade while the mobile rail and rungs deploy outward by controlled gravity assist.",
            "W-EGRESS-P2 is an operable rescue-window coordination hypothesis beside the ladder, not a door or a dimensional authority for a code-compliant clear opening.",
            "The ladder axis is screened 0.60 m south of the window jamb with a 0.80 x 0.80 m clear deployment zone that does not cross the current PB EXT-ESC opening below.",
            "The foldout ladder remains a supplementary escape/rescue device and is not credited as a required second exit under CF-012.",
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b27_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b27.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

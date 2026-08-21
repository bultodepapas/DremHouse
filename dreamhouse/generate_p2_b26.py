"""Generate the D-081 P2 issue with clean exterior-wall plan corners."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b25 import load_b25_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b25_delta.json")
DELTA = Path(__file__).with_name("p2_b26_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b26_p2"


def load_b26_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b25_delta.json changed; review the b26 delta before regenerating")

    model = deepcopy(load_b25_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    model["drawing_controls"] = delta["change"]["drawing_controls"]
    model["design_basis"].append("D-081 clean P2 exterior-corner plan representation")
    model["design_notes"].append(
        "D-081 overlaps only the P2-W05 plan strokes at wall junctions; wall axes, "
        "nominal thickness, openings and room geometry remain unchanged."
    )
    return model


def main() -> None:
    report = generate(
        load_b26_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b26.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

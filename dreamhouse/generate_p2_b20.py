"""Generate the D-064 visually simplified upper-floor plan revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b19 import load_b19_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b19_delta.json")
DELTA = Path(__file__).with_name("p2_b20_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b20_p2"


def load_b20_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b19_delta.json changed; review the b20 delta before regenerating")

    model = deepcopy(load_b19_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    model["design_basis"].append("D-064 simplified main-plan graphics with phasing retained in the dedicated diagram")
    model["hide_phase_boundary_on_plan"] = delta["change"]["hide_phase_boundary_on_plan"]
    model["design_notes"].extend(
        [
            "D-064 suppresses the F1/F2 boundary line and legend key on the main architectural plan only to improve visual clarity.",
            "The Y=11.00 m phase boundary, validation and temporary-works requirement remain active in the model and access/egress diagram.",
            "D-064 changes no geometry, programme, construction scope or cost baseline."
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b20_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b20.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

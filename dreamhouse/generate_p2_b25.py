"""Generate the D-080 P2 issue with wall thickness differentiated by duty."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b24 import load_b24_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b24_delta.json")
DELTA = Path(__file__).with_name("p2_b25_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b25_p2"


def load_b25_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b24_delta.json changed; review the b25 delta before regenerating")

    model = deepcopy(load_b24_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    change = delta["change"]
    model["envelope"].update(change["envelope"])
    model["wall_schedule"] = change["wall_schedule"]
    model["internal_partition"] = change["internal_partition"]
    model["acoustic_partition"] = change["acoustic_partition"]
    model["hall_edge_partition"].update(change["hall_edge_partition"])
    model["exterior_wall_assembly"].update(change["exterior_wall_assembly"])
    model["design_basis"].append("D-080 differentiated P2 wall family by duty")
    model["design_notes"].extend(
        [
            "P2-W01A is limited to dry boundaries within one suite; privacy boundaries use P2-W01B.",
            "Wet, sauna, protected-core and temporary phase walls retain separate coordination types and open professional gates.",
            "P2-W05 integrates the insulated industrial facade panel with one independent residential service lining.",
            "No acoustic, fire, wind, structural, moisture or thermal rating is inferred from nominal thickness.",
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b25_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b25.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

"""Generate the D-067 unified primary-bedroom reading revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b22 import load_b22_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b22_delta.json")
DELTA = Path(__file__).with_name("p2_b23_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b23_p2"


def load_b23_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b22_delta.json changed; review the b23 delta before regenerating")

    model = deepcopy(load_b22_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    model["design_basis"].append("D-067 one-name primary bedroom without fitted privacy screen")
    model["primary_bedroom_unified"] = delta["primary_bedroom_unified"]

    change = delta["change"]
    replacement_names = change["replace_space_names"]
    for space in model["spaces"]:
        if space["id"] in replacement_names:
            space["name"] = replacement_names[space["id"]]
    for key in change["remove_primary_suite_rebalance_keys"]:
        model["primary_suite_rebalance"].pop(key, None)
    model["design_notes"].extend(
        [
            "D-067 identifies M-D and M-L as one 35.24 m2 gross primary bedroom.",
            "Only one Primary bedroom label is shown on the plan.",
            "The 1.45 m fitted privacy screen introduced under D-065 is removed without changing room area or circulation geometry.",
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b23_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b23.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

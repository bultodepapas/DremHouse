"""Generate the D-061 family-distributor upper-floor revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b16 import load_b16_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b16_delta.json")
DELTA = Path(__file__).with_name("p2_b17_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b17_p2"


def _replace_by_id(
    items: list[dict[str, Any]], replacements: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    replacement_by_id = {item["id"]: item for item in replacements}
    result = [replacement_by_id.get(item["id"], item) for item in items]
    existing = {item["id"] for item in result}
    result.extend(item for item in replacements if item["id"] not in existing)
    return result


def load_b17_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b16_delta.json changed; review the b17 delta before regenerating")

    model = deepcopy(load_b16_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    model["design_basis"].append("D-061 stair-to-family distributor and short-spur layout")
    model["family_centre"] = delta["family_centre"]
    model["central_distributor"] = delta["central_distributor"]

    change = delta["change"]
    removed_spaces = set(change["remove_space_ids"])
    model["spaces"] = [item for item in model["spaces"] if item["id"] not in removed_spaces]
    model["spaces"] = _replace_by_id(model["spaces"], change["replace_spaces"])

    removed_doors = set(change["remove_door_ids"])
    model["doors"] = [item for item in model["doors"] if item["id"] not in removed_doors]
    model["doors"] = _replace_by_id(model["doors"], change["replace_doors"])
    model["egress_reserve"]["access_space"] = change["egress_access_space"]
    model["design_notes"].extend(
        [
            "D-061 merges the former protected arrival into a 10.50 x 3.60 m furnished family distributor reached directly from the stair.",
            "The former 15.00 m Phase 2 lobby becomes a 10.50 x 1.45 m open family study edge and one 4.50 x 1.45 m wellness/egress spur.",
            "The Y=11 Phase 1 closure remains temporary and is removed across the shared centre when Phase 2 is completed.",
            "A compact rated or glazed stair vestibule must be reinstated if required by the professional fire and smoke strategy."
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b17_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b17.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

"""Generate the D-062 expanded-wellness upper-floor revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b17 import load_b17_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b17_delta.json")
DELTA = Path(__file__).with_name("p2_b18_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b18_p2"


def _replace_by_id(
    items: list[dict[str, Any]], replacements: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    replacement_by_id = {item["id"]: item for item in replacements}
    result = [replacement_by_id.get(item["id"], item) for item in items]
    existing = {item["id"] for item in result}
    result.extend(item for item in replacements if item["id"] not in existing)
    return result


def load_b18_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b17_delta.json changed; review the b18 delta before regenerating")

    model = deepcopy(load_b17_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    model["design_basis"].append("D-062 expanded dry/wet wellness suite")
    model["central_distributor"] = delta["central_distributor"]
    model["wellness_suite"] = delta["wellness_suite"]

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
            "D-062 removes F2-SPUR as a separate corridor and absorbs its 6.53 m2 into the wellness programme as a dry threshold.",
            "The L-shaped wellness grows from 16.10 m2 to 22.62 m2 gross and adds change, storage and cooling/recline functions.",
            "A 1.20 m clear route is retained through the dry threshold to the rear exterior-stair reserve.",
            "Professional fire review must accept a route through the dry wellness threshold or require a physically separated clear lane."
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b18_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b18.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

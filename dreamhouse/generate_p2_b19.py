"""Generate the D-063 open-family-balcony upper-floor revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b18 import load_b18_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b18_delta.json")
DELTA = Path(__file__).with_name("p2_b19_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b19_p2"


def _replace_by_id(
    items: list[dict[str, Any]], replacements: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    replacement_by_id = {item["id"]: item for item in replacements}
    return [replacement_by_id.get(item["id"], item) for item in items]


def load_b19_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b18_delta.json changed; review the b19 delta before regenerating")

    model = deepcopy(load_b18_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    model["design_basis"].append("D-063 open family balcony toward the double-height hall")
    model["hall_edge_partition"] = delta["hall_edge_partition"]
    model["family_balcony"] = delta["family_balcony"]

    change = delta["change"]
    for space in model["spaces"]:
        if space["id"] in change["space_name_updates"]:
            space["name"] = change["space_name_updates"][space["id"]]
    removed_glazing = set(change["remove_internal_glazing_ids"])
    model["internal_glazing"] = [
        item for item in model["internal_glazing"] if item["id"] not in removed_glazing
    ]
    model["doors"] = _replace_by_id(model["doors"], change["replace_doors"])
    model["design_notes"].extend(
        [
            "D-063 removes the complete X=21 wall/glazing from Y=5.00 to 12.45 and joins the former mini deck, family distributor and study edge behind one open internal balcony frontage.",
            "P2-W04R remains full height only at the Child 1 and Child 2 bedroom ends; those suites remain enclosed.",
            "A continuous 1.10 m minimum schematic guard is reserved along the 7.45 m opening; final guard and edge structure require professional design.",
            "The owner accepts that the family centre is no longer acoustically isolated from the hall; smoke transfer and hall-to-suite noise remain open design gates."
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b19_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b19.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

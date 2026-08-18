"""Generate the D-065 primary-suite rebalance revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b20 import load_b20_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b20_delta.json")
DELTA = Path(__file__).with_name("p2_b21_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b21_p2"


def _replace_by_id(
    items: list[dict[str, Any]], replacements: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    replacement_by_id = {item["id"]: item for item in replacements}
    result = [replacement_by_id.get(item["id"], item) for item in items]
    existing = {item["id"] for item in result}
    result.extend(item for item in replacements if item["id"] not in existing)
    return result


def load_b21_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b20_delta.json changed; review the b21 delta before regenerating")

    model = deepcopy(load_b20_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    model["design_basis"].append("D-065 compact primary dressing and enlarged bedroom")
    model["primary_suite_rebalance"] = delta["primary_suite_rebalance"]

    change = delta["change"]
    removed_spaces = set(change["remove_space_ids"])
    model["spaces"] = [item for item in model["spaces"] if item["id"] not in removed_spaces]
    model["spaces"] = _replace_by_id(model["spaces"], change["replace_spaces"])
    removed_doors = set(change["remove_door_ids"])
    model["doors"] = [item for item in model["doors"] if item["id"] not in removed_doors]
    model["doors"] = _replace_by_id(model["doors"], change["replace_doors"])
    model["windows"] = _replace_by_id(model["windows"], change["replace_windows"])
    model["design_notes"].extend(
        [
            "D-065 moves the primary dressing to a 3.20 x 4.20 m rectangle beside the Child 1 wardrobe/bathroom service band.",
            "The former dressing joins the bedroom as a lounge/entry zone; the combined bedroom grows from 31.08 to 35.24 m2 gross.",
            "A 4.20 m opening replaces the former bedroom/dressing wall over the sleep-zone width, while a short fitted screen protects the bed sightline.",
            "The south primary-bedroom window begins at X=32.05; the east window remains unchanged."
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b21_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b21.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

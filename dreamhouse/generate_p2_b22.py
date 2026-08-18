"""Generate the D-066 unified primary-bathroom revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate
from dreamhouse.generate_p2_b21 import load_b21_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b21_delta.json")
DELTA = Path(__file__).with_name("p2_b22_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b22_p2"


def _replace_by_id(
    items: list[dict[str, Any]], replacements: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    replacement_by_id = {item["id"]: item for item in replacements}
    result = [replacement_by_id.get(item["id"], item) for item in items]
    existing = {item["id"] for item in result}
    result.extend(item for item in replacements if item["id"] not in existing)
    return result


def load_b22_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b21_delta.json changed; review the b22 delta before regenerating")

    model = deepcopy(load_b21_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    model["design_basis"].append("D-066 unified L-shaped primary bathroom")
    model["primary_bathroom_unified"] = delta["primary_bathroom_unified"]

    change = delta["change"]
    replacement_names = change["replace_space_names"]
    for space in model["spaces"]:
        if space["id"] in replacement_names:
            space["name"] = replacement_names[space["id"]]
    model["doors"] = _replace_by_id(model["doors"], change["replace_doors"])
    model["design_notes"].extend(
        [
            "D-066 treats M-B-A and M-B as one 17.60 m2 gross L-shaped primary bathroom.",
            "The full 2.40 m shared boundary is open: no intermediate partition, jamb or door leaf remains.",
            "The schematic 15.66 m2 net area uses a transparent 0.10 m inward wet-wall allowance around the L-shaped perimeter.",
            "One fixture programme replaces the former duplicated bathroom symbols: walk-in shower, tub, double vanity, WC and linen storage.",
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b22_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b22.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

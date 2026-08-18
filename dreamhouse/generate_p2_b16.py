"""Generate the D-060 coherent-family-centre upper-floor revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b09 import generate, load_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b15.json")
DELTA = Path(__file__).with_name("p2_b16_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b16_p2"


def _replace_by_id(
    items: list[dict[str, Any]], replacements: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    replacement_by_id = {item["id"]: item for item in replacements}
    result = [replacement_by_id.get(item["id"], item) for item in items]
    existing = {item["id"] for item in result}
    result.extend(item for item in replacements if item["id"] not in existing)
    return result


def load_b16_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("p2_b15.json changed; review the b16 delta before regenerating")

    model = deepcopy(load_model(BASE))
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    model["design_basis"].append("D-060 coherent family-centre consolidation")
    model["family_centre"] = delta["family_centre"]

    change = delta["change"]
    removed_spaces = set(change["remove_space_ids"])
    model["spaces"] = [item for item in model["spaces"] if item["id"] not in removed_spaces]
    model["spaces"] = _replace_by_id(model["spaces"], change["replace_spaces"])

    removed_doors = set(change["remove_door_ids"])
    model["doors"] = [item for item in model["doors"] if item["id"] not in removed_doors]
    model["doors"] = _replace_by_id(model["doors"], change["replace_doors"])
    model["internal_glazing"] = _replace_by_id(
        model["internal_glazing"], change["replace_internal_glazing"]
    )
    model["design_notes"].extend(
        [
            (
                "D-060 consolidates the former family lounge, gallery/library and private "
                "hall into one 7.60 x 3.60 m shared room."
            ),
            (
                "Circulation is absorbed along the family room edges and a 4.20 m fitted "
                "library wall replaces the dedicated 1.10 m gallery strip."
            ),
            (
                "The mini deck contracts to 2.80 x 2.40 m and remains a distinct "
                "acoustically glazed destination."
            ),
            (
                "Child Suite 1 access through the mini deck is deliberately unchanged "
                "and remains a separate open architectural recommendation."
            ),
        ]
    )
    return model


def main() -> None:
    report = generate(
        load_b16_model(),
        OUT,
        source_path=DELTA,
        generator_name="dreamhouse/generate_p2_b16.py",
    )
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

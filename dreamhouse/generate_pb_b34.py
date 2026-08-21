"""Generate the D-077 integrated PB issue from b32 and the shared stair core."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b32 as b32
from dreamhouse.architecture.stair_core import load_stair_core, validate_stair_core

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b32_delta.json")
DELTA = Path(__file__).with_name("pb_b34_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b34_pb"


def load_b34_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b32_delta.json changed; review the b34 integration before regenerating")

    model = deepcopy(b32.load_b32_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))

    remove_markers = tuple(delta["coordination_holds_remove_contains"])
    model["coordination_holds"] = [
        item
        for item in model["coordination_holds"]
        if not item.startswith(remove_markers)
    ]
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))

    model["stair_core"] = load_stair_core(ROOT / delta["stair_core"])
    model["structural_reservations"] = deepcopy(
        model["stair_core"]["structure"]["column_reservations"]
    )
    return model


def validate_b34(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b32.validate_b32(model)
    owner_gate = next(item for item in checks if item["rule_id"] == "PB-KD-OWNER-SELECTION")
    owner_gate["status"] = "PASS"
    owner_gate["message"] = (
        "D-077 adopts the b32 opposite-dining/full-span-kitchen relationship as the "
        "active schematic PB basis; D-024 product and equipment selection remains open."
    )

    checks.extend(validate_stair_core(model["stair_core"]))
    stair_core = model["stair_core"]
    enclosure = stair_core["enclosure"]
    stair_room = next(item for item in model["core"] if item["id"] == "ESC")
    lower = stair_core["stair"]["lower_flight"]
    dining = model["social_layout"]["dining"]
    table = dining["table"]
    kitchen = model["kitchen"]
    island = kitchen["island"]
    wall_run = kitchen["wall_run"]
    expected_columns = {
        (item["id"], item["x"], item["y"])
        for item in stair_core["structure"]["column_reservations"]
    }
    actual_columns = {
        (item["id"], item["x"], item["y"])
        for item in model["structural_reservations"]
    }

    def add(rule_id: str, ok: bool, message: str) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "PASS" if ok else "FAIL",
                "message": message,
            }
        )

    add(
        "PB34-D077-DOMESTIC-GEOMETRY",
        table == {
            "x": 24.65,
            "y": 13.86,
            "length": 3.2,
            "depth": 1.1,
            "height": 0.75,
            "label": "12P · 3.20 × 1.10",
        }
        and dining["chairs_per_side"] == 5
        and dining["end_chairs"] == 1
        and dining["seat_count"] == 12
        and wall_run["length"] == 10.05
        and island["length"] == 7.2,
        (
            "D-077 restores the centred 3.20 x 1.10 m, 5+5+2 dining group opposite "
            "the 10.05 m kitchen wall and 7.20 m dry island."
        ),
    )
    add(
        "PB34-DOMESTIC-CORE-SEPARATION",
        table["x"] + table["length"] < enclosure["x0"]
        and island["x"] + island["length"] < enclosure["x0"]
        and wall_run["x"] + wall_run["length"] <= enclosure["x0"] - 0.25,
        "Dining, island and wall cabinets stop clear of the Great Wall and SC-01 core.",
    )
    add(
        "PB34-STAIR-SHARED-FOOTPRINT",
        model["great_wall"]["x"] == enclosure["x0"]
        and model["envelope"]["length"] == enclosure["x1"]
        and stair_room["y0"] == enclosure["y0"]
        and stair_room["y1"] == enclosure["y1"],
        "The restored PB layout retains SC-01 at X=31.50-36.00 m / Y=7.40-11.00 m.",
    )
    door_reference = stair_core["stair"]["pb_access_platform"]["door_reference_y"]
    add(
        "PB34-STAIR-ACCESS-FLIGHT",
        stair_room["door_y"] == door_reference
        and lower["y0"] <= door_reference <= lower["y1"],
        "The PB Great Wall portal remains aligned with the SC-01 lower-flight access zone.",
    )
    add(
        "PB34-STAIR-FOUR-COLUMN-SYNC",
        actual_columns == expected_columns and len(actual_columns) == 4,
        "PB b34 retains the same four SC-01 column IDs and coordinates used by P2.",
    )
    return checks


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b34(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        (
            "D-077 restores the centred dining, full-span kitchen and centred Project "
            "Car/lift while retaining the SC-01 stair and four columns."
        ),
    )
    outputs = {"DH-ARQ-PLN-001-R12_PB-INTEGRATED-RESTORATION.svg": plan}
    target.mkdir(parents=True, exist_ok=True)
    for filename, content in outputs.items():
        target.joinpath(filename).write_text(content, encoding="utf-8")

    report = {
        "revision": model["revision"],
        "status": model["status"],
        "checks": checks,
        "passed": sum(item["status"] == "PASS" for item in checks),
        "open": sum(item["status"] == "OPEN" for item in checks),
        "failed": sum(item["status"] == "FAIL" for item in checks),
    }
    target.joinpath("compliance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "revision": model["revision"],
        "status": model["status"],
        "source": "dreamhouse/pb_b34_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "base_source": "dreamhouse/pb_b32_delta.json",
        "base_source_sha256": hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest(),
        "shared_stair_source": "dreamhouse/stair_core.json",
        "shared_stair_sha256": hashlib.sha256(
            Path(__file__).with_name("stair_core.json").read_bytes()
        ).hexdigest(),
        "generator": "dreamhouse/generate_pb_b34.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b34 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b34_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

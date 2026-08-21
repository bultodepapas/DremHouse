"""Generate the D-074 PB issue from the shared stair-core model."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b29 as b29
from dreamhouse.architecture.stair_core import load_stair_core, validate_stair_core

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b29_delta.json")
DELTA = Path(__file__).with_name("pb_b33_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b33_pb"


def load_b33_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b29_delta.json changed; review the b33 delta before regenerating")

    model = deepcopy(b29.load_b29_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    model["stair_core"] = load_stair_core(ROOT / delta["stair_core"])
    model["structural_reservations"] = deepcopy(
        model["stair_core"]["structure"]["column_reservations"]
    )
    return model


def validate_b33(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b29.validate_b29(model)
    checks.extend(validate_stair_core(model["stair_core"]))
    stair_room = next(item for item in model["core"] if item["id"] == "ESC")
    stair_core = model["stair_core"]
    enclosure = stair_core["enclosure"]
    lower = stair_core["stair"]["lower_flight"]
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
        "PB-STAIR-SHARED-FOOTPRINT",
        model["great_wall"]["x"] == enclosure["x0"]
        and model["envelope"]["length"] == enclosure["x1"]
        and stair_room["y0"] == enclosure["y0"]
        and stair_room["y1"] == enclosure["y1"],
        "PB stair enclosure matches SC-01 at X=31.50-36.00 m and Y=7.40-11.00 m.",
    )
    door_reference = stair_core["stair"]["pb_access_platform"]["door_reference_y"]
    add(
        "PB-STAIR-ACCESS-FLIGHT",
        stair_room["door_y"] == door_reference
        and lower["y0"] <= door_reference <= lower["y1"],
        "The PB Great Wall portal aligns with the lower-flight access zone.",
    )
    add(
        "PB-STAIR-FOUR-COLUMN-SYNC",
        actual_columns == expected_columns and len(actual_columns) == 4,
        "PB renders the same four SC-01 column IDs and coordinates used by P2 and D-048.",
    )
    return checks


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b33(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        "D-074 coordinates one shared PB/P2 stair model and four continuous column reserves.",
    )
    core = b24.translate_visible_text(base.core_sheet(model))
    outputs = {
        "DH-ARQ-PLN-001-R11_PB-STAIR-CORE.svg": plan,
        "DH-ARQ-DET-001-R05_PB-STAIR-CORE.svg": core,
    }
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
        "source": "dreamhouse/pb_b33_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "shared_stair_source": "dreamhouse/stair_core.json",
        "shared_stair_sha256": hashlib.sha256(
            Path(__file__).with_name("stair_core.json").read_bytes()
        ).hexdigest(),
        "generator": "dreamhouse/generate_pb_b33.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b33 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b33_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

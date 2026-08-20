"""Generate the D-069 enlarged ground-floor workstation/cabinet revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b24_delta.json")
DELTA = Path(__file__).with_name("pb_b25_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b25_pb"


def load_b25_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b24_delta.json changed; review the b25 delta before regenerating")

    model = deepcopy(b24.load_b24_model())
    for key in ("revision", "status", "date", "supersedes", "decision", "drawing_meta"):
        model[key] = deepcopy(delta[key])
    for workstation in model["workstations"]:
        workstation.update(deepcopy(delta["workstation_update"]))
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    return model


def validate_b25(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b24.validate_b24(model)
    by_side = {item["side"]: item for item in model["workstations"]}
    a, b = by_side["A"], by_side["B"]

    def add(rule_id: str, ok: bool, message: str) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "PASS" if ok else "FAIL",
                "message": message,
            }
        )

    add(
        "PB-WS-FULL-BAY-WORKTOP",
        a["worktop_x0"] == a["zone_x0"]
        and a["worktop_length"] == a["zone_x1"] - a["zone_x0"]
        and a["worktop_length"] == b["worktop_length"] == 3.0,
        "Each worktop spans the full 3.00 m workstation/window bay.",
    )
    add(
        "PB-WS-CONTROLLED-DEPTH",
        a["worktop_depth"] == b["worktop_depth"] == 0.9
        and a["worktop_depth"] < 1.0,
        "Both enlarged worktops are 0.90 m deep and remain below the 1.00 m depth limit.",
    )
    cabinetry_equal = all(
        a[key] == b[key]
        for key in (
            "drawer_cabinet_width",
            "drawer_cabinet_depth",
            "drawer_cabinet_height",
            "drawer_cabinet_count",
            "drawer_levels",
            "central_knee_clear_width",
        )
    )
    add(
        "PB-WS-CABINETRY-MIRROR",
        cabinetry_equal and a["drawer_cabinet_count"] == 2 and a["drawer_levels"] == 3,
        "Each side has the same pair of large suspended three-drawer steel cabinets.",
    )
    calculated_clear = a["worktop_length"] - 2 * a["drawer_cabinet_width"]
    add(
        "PB-WS-KNEE-CLEARANCE",
        abs(calculated_clear - a["central_knee_clear_width"]) < 1e-9
        and calculated_clear >= 1.5,
        f"The central knee/chair opening is {calculated_clear:.2f} m clear.",
    )
    add(
        "PB-WS-CABINET-WITHIN-TOP",
        a["drawer_cabinet_depth"] <= a["worktop_depth"]
        and a["drawer_cabinet_height"] < a["worktop_height"],
        "Drawer cabinets remain within the worktop depth and suspended above the floor.",
    )
    return checks


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b25(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        "D-069 enlarges the workstation/cabinet assembly only.",
    )
    outputs = {
        "DH-ARQ-PLN-001-R06_PB-ENLARGED-INTEGRATED-WORKSTATIONS.svg": plan,
        "DH-ARQ-ELE-003-R08_SIDE-A-FULL-BAY-WORKSTATION.svg":
            b24.translate_visible_text(base.side_elevation_sheet(model, "A")),
        "DH-ARQ-ELE-004-R08_SIDE-B-FULL-BAY-WORKSTATION.svg":
            b24.translate_visible_text(base.side_elevation_sheet(model, "B")),
        "DH-ARQ-DET-006-R01_ENLARGED-WORKSTATION-CABINET-FAMILY.svg":
            b24.workstation_detail_sheet(model),
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
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "revision": model["revision"],
        "status": model["status"],
        "source": "dreamhouse/pb_b25_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b25.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if report["failed"]:
        raise ValueError(f'PB b25 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b25_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

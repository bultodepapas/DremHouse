"""Generate the D-073 front-corner-start technical workbench revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b28 as b28

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b28_delta.json")
DELTA = Path(__file__).with_name("pb_b29_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b29_pb"


def load_b29_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b28_delta.json changed; review the b29 delta before regenerating")

    model = deepcopy(b28.load_b28_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["built_in_benches"] = deepcopy(delta["built_in_benches"])
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    return model


def validate_b29(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b28.validate_b28(model)
    benches = {item["id"]: item for item in model["built_in_benches"]}
    car_bench = benches["PB-BENCH-CAR"]
    rc_bench = benches["PB-BENCH-RC"]
    openings = {item["id"]: item for item in model["front_openings"]}
    ext = model["envelope"]["exterior_wall"]

    def add(rule_id: str, ok: bool, message: str) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "PASS" if ok else "FAIL",
                "message": message,
            }
        )

    add(
        "PB-TECH-BENCHES-FRONT-CORNER-START",
        all(
            abs(item["x0"] - ext) < 1e-9
            and item.get("start_condition") == "front_inner_corner"
            for item in benches.values()
        ),
        "Both 9.00 m technical benches begin at X=0.18 m, the front interior corner.",
    )
    add(
        "PB-TECH-BENCHES-LENGTH-RETAINED",
        all(item["length"] == 9.0 and item["x0"] + item["length"] == 9.18 for item in benches.values()),
        "Both benches retain 9.00 m length and terminate at X=9.18 m.",
    )
    car_door_gap = openings["CAR"]["y0"] - (car_bench["y0"] + car_bench["depth"])
    rc_door_edge = openings["RC"]["y0"] + openings["RC"]["width"]
    rc_door_gap = rc_bench["y0"] - rc_door_edge
    add(
        "PB-TECH-BENCHES-FRONT-DOOR-SEPARATION",
        car_door_gap >= 0.25 and rc_door_gap >= 0.25,
        f"The corner-start benches retain nominal plan gaps of {car_door_gap:.2f} m and {rc_door_gap:.2f} m to the adjacent front door openings.",
    )
    return checks


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b29(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        "D-073 starts both 9.00 m technical workbenches at the front interior corners.",
    )
    outputs = {"DH-ARQ-PLN-001-R10_PB-CORNER-START-WORKBENCHES.svg": plan}
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
        "source": "dreamhouse/pb_b29_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b29.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b29 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b29_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

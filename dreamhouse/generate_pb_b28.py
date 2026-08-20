"""Generate the D-072 Side A wall-integrated project-car workbench revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b27 as b27

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b27_delta.json")
DELTA = Path(__file__).with_name("pb_b28_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b28_pb"


def load_b28_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b27_delta.json changed; review the b28 delta before regenerating")

    model = deepcopy(b27.load_b27_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["built_in_benches"] = deepcopy(delta["built_in_benches"])
    model["car_lift_layout"] = deepcopy(delta["car_lift_layout"])
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    return model


def validate_b28(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b27.validate_b27(model)
    benches = {item["id"]: item for item in model["built_in_benches"]}
    car_bench = benches["PB-BENCH-CAR"]
    rc_bench = benches["PB-BENCH-RC"]
    lift = model["car_lift_layout"]["envelope"]
    ext = model["envelope"]["exterior_wall"]
    width = model["envelope"]["width"]
    axis0 = model["design_values"]["axis_y0"]
    car_window = next(
        item for item in model["technical_glazing"] if item["id"] == "GLZ-CAR"
    )

    def add(rule_id: str, ok: bool, message: str) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "PASS" if ok else "FAIL",
                "message": message,
            }
        )

    add(
        "PB-CAR-BENCH-SIDE-A-WALL",
        car_bench.get("mounting") == "side_a_perimeter"
        and abs(car_bench["y0"] - ext) < 1e-9,
        "The 9.00 m project-car bench is fixed directly against the Side A perimeter wall.",
    )
    add(
        "PB-TECHNICAL-BENCHES-PERIMETER",
        rc_bench.get("mounting") == "side_b_perimeter"
        and abs(rc_bench["y0"] + rc_bench["depth"] - (width - ext)) < 1e-9,
        "Both long technical workbenches are now wall-side elements on opposite hall walls.",
    )
    add(
        "PB-CAR-BENCH-BELOW-WINDOW",
        car_bench["x0"] <= car_window["x0"]
        and car_bench["x0"] + car_bench["length"] >= car_window["x1"]
        and car_bench["worktop_height"] <= car_window["sill"],
        "The project-car bench spans below the full technical window without raising its test worktop above the sill.",
    )
    bench_inside_edge = car_bench["y0"] + car_bench["depth"]
    lift_gap = lift["y"] - bench_inside_edge
    add(
        "PB-CAR-BENCH-LIFT-GRAPHIC-SEPARATION",
        lift_gap >= 0.10 and lift["y"] + lift["d"] < axis0,
        f"The shifted lift envelope retains {lift_gap:.2f} m graphic separation from the bench and stops before the central axis.",
    )
    return checks


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b28(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        "D-072 fixes the project-car workbench to the Side A perimeter wall and shifts the lift test envelope clear.",
    )
    outputs = {"DH-ARQ-PLN-001-R09_PB-WALL-INTEGRATED-WORKBENCH.svg": plan}
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
        "source": "dreamhouse/pb_b28_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b28.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b28 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b28_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

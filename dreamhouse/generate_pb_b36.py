"""Generate the D-079 modular PB technical-workbench coordination issue."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b35 as b35

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b35_delta.json")
DELTA = Path(__file__).with_name("pb_b36_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b36_pb"


def load_b36_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b35_delta.json changed; review the b36 integration before regenerating")

    model = deepcopy(b35.load_b35_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["technical_bench_detail_meta"] = deepcopy(delta["technical_bench_detail_meta"])
    model["built_in_benches"] = deepcopy(delta["built_in_benches"])
    model["central_rc_bench"] = deepcopy(delta["central_rc_bench"])
    model["rc_support_equipment"] = deepcopy(delta["rc_support_equipment"])
    model["technical_bench_research_basis"] = deepcopy(delta["research_basis"])
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    return model


def validate_b36(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b35.validate_b35(model)
    benches = {item["id"]: item for item in model["built_in_benches"]}
    car = benches["PB-BENCH-CAR"]
    rc = benches["PB-BENCH-RC"]
    central = model["central_rc_bench"]
    support = model["rc_support_equipment"]
    lift = model["car_lift_layout"]["envelope"]
    axis_y1 = model["design_values"]["axis_y1"]

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
                "message": message,
            }
        )

    add(
        "PB36-D079-COMMON-MODULE-GRID",
        all(
            item["length"] == 9.0
            and item["depth"] == .75
            and item["module_count"] == 6
            and item["module_width"] == 1.5
            and item["module_count"] * item["module_width"] == item["length"]
            for item in (car, rc)
        ),
        "Both 9.00 x 0.75 m wall benches use six replaceable 1.50 m modules.",
    )
    add(
        "PB36-D079-CAR-DUTY-HEIGHTS",
        car["module_top_heights"] == [.90, .84, .90, .90, .90, .90]
        and car["heavy_module_index"] == 1
        and car["rear_service_zone"] + car["active_depth"] == car["depth"],
        "Project Car tests one +0.84 m heavy-force bay and five +0.90 m general bays with a 0.12 m service zone.",
    )
    add(
        "PB36-D079-RC-ADJUSTABLE-ESD",
        rc["adjustable_module_indices"] == [1, 2, 3]
        and rc["esd_module_indices"] == [1, 2, 3]
        and rc["adjustment_min_height"] == .70
        and rc["adjustment_max_height"] == 1.10
        and all(rc["module_top_depths"][index] == .80 for index in rc["adjustable_module_indices"]),
        "RC tests three 0.80 m-deep, +0.70-1.10 m manual-adjustable ESD-capable clean modules.",
    )
    add(
        "PB36-D079-CENTRAL-RC-ISLAND",
        central["length"] == 4.50
        and central["depth"] == 1.60
        and central["height"] == .84
        and central["module_count"] == 3
        and central["module_width"] == 1.50
        and central["access"] == "all_sides",
        "The central RC assembly island remains 4.50 x 1.60 m, uses three 1.50 m modules and tests a +0.84 m two-sided top.",
    )
    support_clearance = rc["operating_strip_y0"] - max(
        support["printer_zone"]["y"] + support["printer_zone"]["d"],
        support["lipo_zone"]["y"] + support["lipo_zone"]["d"],
    )
    central_axis_clearance = central["y"] - axis_y1
    central_wall_clearance = rc["operating_strip_y0"] - (central["y"] + central["depth"])
    add(
        "PB36-D079-RC-OPERATING-CLEARANCES",
        abs(support_clearance - .07) < 1e-9
        and abs(central_axis_clearance - 1.70) < 1e-9
        and abs(central_wall_clearance - 1.57) < 1e-9,
        "The shifted RC support equipment stops before the 1.20 m wall-bench strip; the central island retains 1.70 m to the axis and 1.57 m to that strip.",
    )
    overlap = min(car["operating_strip_y1"], lift["y"] + lift["d"]) - max(
        car["operating_strip_y0"], lift["y"]
    )
    add(
        "PB36-D079-CAR-LIFT-OPERATING-CONFLICT",
        False,
        (
            f"The 1.20 m Project Car bench operating strip overlaps the schematic lift/vehicle "
            f"envelope by {overlap:.2f} m. Select the real lift and vehicle and test simultaneous use."
        ),
        open_gate=True,
    )
    add(
        "PB36-D079-ANTHROPOMETRY-AND-MOCKUP",
        False,
        (
            "Test +0.84/+0.90 m fixed heights and the +0.70-1.10 m RC range against owner "
            "standing/seated elbow heights, real work objects and full-scale 1.50 m mock-ups."
        ),
        open_gate=True,
    )
    add(
        "PB36-D079-WINDOW-SERVICE-INDEPENDENCE",
        False,
        (
            "Both technical-window sills remain +0.90 m. Detail maintainable shadow gaps, "
            "rear service trays, drainage and independent support without loading frames or girts."
        ),
        open_gate=True,
    )
    add(
        "PB36-D079-MEP-ESD-FUME-BATTERY",
        False,
        (
            "Electrical designer to coordinate RETIE-compliant circuits and protective earth; "
            "verify ESD common-point grounding, solder source extraction, printer emissions and "
            "a separate LiPo fire/charging strategy with real equipment."
        ),
        open_gate=True,
    )
    add(
        "PB36-D079-COST-CODE-GAP",
        False,
        (
            "The 9.00 m RC wall bench is not yet a one-to-one priced atomic item. Reconcile local "
            "fixed modules, three adjustable modules, services, storage and phasing before target change."
        ),
        open_gate=True,
    )
    return checks


def _bench_elevation(
    bench: dict[str, Any],
    *,
    x: float,
    floor_y: float,
    scale: float,
    prefix: str,
    window_x0_relative: float,
) -> list[str]:
    parts: list[str] = []
    width = bench["length"] * scale
    sill_y = floor_y - .90 * scale
    head_y = floor_y - 3.80 * scale
    window_x = x + window_x0_relative * scale
    window_w = 7.20 * scale
    parts.append(base.rect(window_x, head_y, window_w, sill_y - head_y, fill="#426671", stroke="#172126", stroke_width="2"))
    for index in range(1, 6):
        xx = window_x + index * 1.20 * scale
        parts.append(f'<line x1="{xx}" y1="{head_y}" x2="{xx}" y2="{sill_y}" stroke="#9bb3b8" stroke-width="1"/>')
    adjustable = set(bench.get("adjustable_module_indices", []))
    storage = set(bench.get("storage_module_indices_test", []))
    for index in range(bench["module_count"]):
        module_x = x + index * bench["module_width"] * scale
        module_w = bench["module_width"] * scale
        top_y = floor_y - bench["module_top_heights"][index] * scale
        color = "#82b5b4" if index in adjustable else ("#9b8772" if index == bench.get("heavy_module_index") else "#c99f6b")
        parts.append(f'<line x1="{module_x}" y1="{top_y}" x2="{module_x+module_w}" y2="{top_y}" stroke="{color}" stroke-width="9"/>')
        parts.append(f'<line x1="{module_x}" y1="{top_y+5}" x2="{module_x}" y2="{floor_y}" stroke="#334348" stroke-width="2"/>')
        if index in storage:
            parts.append(base.rect(module_x + 8, top_y + 8, module_w - 16, floor_y - top_y - 14, fill="#8b6a4d", stroke="#26363b", stroke_width="1"))
        parts.append(base.text(module_x + module_w / 2, floor_y + 15, f"{prefix}{index+1}", 6.2, weight=700))
    parts.append(f'<line x1="{x}" y1="{floor_y}" x2="{x+width}" y2="{floor_y}" stroke="#4f5c60" stroke-width="1.5"/>')
    return parts


def technical_workbench_detail_sheet(model: dict[str, Any]) -> str:
    benches = {item["id"]: item for item in model["built_in_benches"]}
    car = benches["PB-BENCH-CAR"]
    rc = benches["PB-BENCH-RC"]
    central = model["central_rc_bench"]
    meta = model["technical_bench_detail_meta"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        base.title_block(meta["code"], meta["title"], meta["subtitle"]),
    ]

    parts.append(base.text(70, 120, "A · PROJECT CAR WALL BENCH · SIX DUTY MODULES", 13, "start", 700))
    parts.extend(_bench_elevation(car, x=75, floor_y=315, scale=50, prefix="C", window_x0_relative=1.32))
    car_roles = "C1 door/service · C2 heavy force +0.84 · C3-C4 mechanical · C5 diagnostics · C6 landing/storage"
    parts.append(base.text(75, 342, car_roles, 7.2, "start", 700, "#5b432b"))
    parts.append(base.text(75, 362, "0.75 m total depth = 0.63 m active + 0.12 m removable rear service zone · 1.20 m operating strip OPEN against real lift", 7.0, "start"))

    parts.append(base.text(70, 405, "B · RC / ELECTRONICS WALL BENCH · CLEAN AND DIRTY TASKS SEPARATED", 13, "start", 700))
    parts.extend(_bench_elevation(rc, x=75, floor_y=600, scale=50, prefix="R", window_x0_relative=1.32))
    rc_roles = "R1 model mechanics · R2 electronics ESD · R3 solder ESD + source extraction · R4 instruments ESD · R5 tools · R6 landing"
    parts.append(base.text(75, 627, rc_roles, 6.8, "start", 700, "#294f58"))
    parts.append(base.text(75, 647, "R2-R4: 0.80 m tops and manual +0.70-1.10 m adjustment · ESD common point bonds to protective earth · LiPo stays separate", 7.0, "start"))

    parts.append(base.text(770, 120, "C · WALL / SILL / SERVICE PRINCIPLE", 13, "start", 700))
    floor_y = 380
    wall_x = 830
    parts.append(base.rect(760, 155, 70, 225, fill="#a2abad", stroke="#26363b", stroke_width="1.3"))
    parts.append(base.rect(830, 155, 60, 225, fill="#d8ded9", stroke="#536166", stroke_width="1"))
    sill_y = floor_y - .90 * 150
    parts.append(base.rect(890, 165, 30, sill_y - 165, fill="#416771", stroke="#172126", stroke_width="2"))
    parts.append(base.rect(882, sill_y, 46, 12, fill="#29383d", stroke="#172126"))
    parts.append(f'<line x1="{940}" y1="{sill_y}" x2="{1240}" y2="{sill_y}" stroke="#c99f6b" stroke-width="12"/>')
    parts.append(base.rect(920, sill_y + 16, 50, 24, fill="#fff4df", stroke="#b56c31", stroke_width="1"))
    parts.append(base.text(945, sill_y + 32, "30-50", 6.2, weight=700, fill="#8e3825"))
    parts.append(base.text(990, sill_y - 12, "TOP / SILL ALIGN VISUALLY; DO NOT JOIN STRUCTURALLY", 7.2, "start", 700, "#8e3825"))
    parts.append(base.text(990, sill_y + 22, "removable shadow gap + service trough", 7.0, "start"))
    parts.append(base.text(990, sill_y + 44, "window drains and seals independently", 7.0, "start"))
    parts.append(base.text(990, sill_y + 66, "no furniture load to frame or facade girt", 7.0, "start"))
    parts.append(base.text(760, 405, "HEIGHT DATUM", 7.5, "start", 700, "#8e3825"))
    parts.append(base.text(855, 405, "+0.90 general · +0.84 heavy / large-object test · +0.70-1.10 adjustable electronics", 7.0, "start"))
    parts.append(base.text(760, 428, "AUTHORITY", 7.5, "start", 700, "#8e3825"))
    parts.append(base.text(855, 428, "Owner anthropometry, tasks and full-scale mock-ups govern final heights.", 7.0, "start"))

    parts.append(base.text(70, 700, "D · CENTRAL RC TWO-SIDED ASSEMBLY ISLAND", 13, "start", 700))
    plan_x, plan_y, scale = 75.0, 725.0, 92.0
    plan_w, plan_d = central["length"] * scale, central["depth"] * scale
    parts.append(base.rect(plan_x, plan_y, plan_w, plan_d, fill="#d9d3c6", stroke="#526064", stroke_width="2"))
    for index in range(1, central["module_count"]):
        xx = plan_x + index * central["module_width"] * scale
        parts.append(f'<line x1="{xx}" y1="{plan_y}" x2="{xx}" y2="{plan_y+plan_d}" stroke="#667579" stroke-width="1.2" stroke-dasharray="5 3"/>')
    parts.append(f'<line x1="{plan_x}" y1="{plan_y+plan_d/2}" x2="{plan_x+plan_w}" y2="{plan_y+plan_d/2}" stroke="#9d8c70" stroke-width="1" stroke-dasharray="4 3"/>')
    parts.append(base.text(plan_x + plan_w / 2, plan_y + plan_d / 2 + 3, "4.50 × 1.60 m · 3 × 1.50 m · TWO-SIDED · TOP +0.84", 7.5, weight=700))
    parts.append(base.text(75, 890, "Flat replaceable light surface · central line is two 0.80 m reach halves · fixed versus lockable-mobile support remains open", 7.0, "start"))

    parts.append(base.text(770, 485, "E · OPEN PROFESSIONAL GATES", 13, "start", 700))
    gates = [
        "1  Select real lift + vehicle; current 1.20 m car-bench strip overlaps the test envelope by 1.10 m.",
        "2  Mock up one 1.50 m car module and one adjustable RC module with the owner's real work objects.",
        "3  Engineer bench frames, local vice/impact loads, drawer loads and bolted backing independently of the facade.",
        "4  Coordinate RETIE circuits/protective earth, ESD point, solder extraction, printer emissions and LiPo fire strategy.",
        "5  Quote local fixed and manual-adjustable modules; reconcile the unpriced 9.00 m RC wall bench before target change.",
    ]
    for index, gate in enumerate(gates):
        y = 515 + index * 44
        parts.append(base.rect(770, y, 555, 34, fill="#f1eee7", stroke="#c0bbb0", stroke_width=".8"))
        parts.append(base.text(784, y + 21, gate, 6.6, "start", 700 if index == 0 else 400, "#8e3825" if index == 0 else "#26363b"))

    parts.append(base.rect(770, 754, 555, 126, fill="#fff4df", stroke="#bd5c3c", stroke_width="1"))
    parts.append(base.text(787, 779, "D-079 CONTROL", 9, "start", 700, "#8e3825"))
    parts.append(base.text(787, 803, "Lengths and footprints remain schematic architectural reservations.", 7.0, "start"))
    parts.append(base.text(787, 825, "Adjustability, loads, products, fire/extraction and electrical design remain open.", 7.0, "start"))
    parts.append(base.text(787, 847, "Use imported systems only as benchmarks; price economical local modular fabrication.", 7.0, "start"))
    parts.append(base.text(787, 869, "NOT FOR PROCUREMENT, FABRICATION OR CONSTRUCTION.", 7.5, "start", 700, "#8e3825"))
    parts.append("</svg>")
    return "".join(parts)


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b36(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        (
            "D-079 differentiates six Project Car and six RC/electronics wall-bench modules, "
            "retains the three-module central RC island and exposes lift, ESD, extraction and cost gates."
        ),
    )
    outputs = {
        "DH-ARQ-PLN-001-R14_PB-MODULAR-TECHNICAL-WORKBENCHES.svg": plan,
        "DH-ARQ-DET-007-R01_PB-TECHNICAL-WORKBENCH-SYSTEM.svg": technical_workbench_detail_sheet(model),
    }
    target.mkdir(parents=True, exist_ok=True)
    for filename, content in outputs.items():
        target.joinpath(filename).write_text(content, encoding="utf-8")

    report = {
        "revision": model["revision"],
        "status": model["status"],
        "decision": model["decision"],
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
        "decision": model["decision"],
        "source": "dreamhouse/pb_b36_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "base_source": "dreamhouse/pb_b35_delta.json",
        "base_source_sha256": hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b36.py",
        "supersedes": model["supersedes"],
        "retained_sources": [
            "planos/conceptual_v0.3_b35_pb/DH-ARQ-ELE-003-R09_SIDE-A-PERFORMANCE-FIRST-OPENING.svg",
            "planos/conceptual_v0.3_b35_pb/DH-ARQ-DET-006-R02_SIDE-A-SHARED-WORKSTATION.svg"
        ],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b36 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b36_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

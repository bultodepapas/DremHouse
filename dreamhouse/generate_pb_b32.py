"""Generate the centred project-car/lift refinement within the PB option study."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b31 as b31

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b31_delta.json")
DELTA = Path(__file__).with_name("pb_b32_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b32_pb"


def load_b32_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b31_delta.json changed; review the b32 option before regenerating")

    model = deepcopy(b31.load_b31_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["car_territory"] = deepcopy(delta["car_territory"])
    model["car_lift_layout"] = deepcopy(delta["car_lift_layout"])
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    return model


def validate_b32(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b31.validate_b31(model)
    territory = model["car_territory"]
    layout = model["car_lift_layout"]
    envelope = layout["envelope"]
    car = layout["car"]
    posts = layout["posts"]
    centre = layout["centre"]
    bench = next(
        item for item in model["built_in_benches"] if item["id"] == "PB-BENCH-CAR"
    )
    axis0 = model["design_values"]["axis_y0"]

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
                "message": message,
            }
        )

    envelope_centre_x = envelope["x"] + envelope["w"] / 2
    envelope_centre_y = envelope["y"] + envelope["d"] / 2
    add(
        "PB-CAR-LIFT-LONGITUDINAL-CENTRE",
        abs(envelope_centre_x - territory["centre"]["x"]) < 1e-9
        and abs(centre["x"] - territory["centre"]["x"]) < 1e-9,
        (
            "The 6.40 m lift/vehicle envelope is centred at "
            f"X={envelope_centre_x:.2f} m in the X=0.18–10.50 m technical bay."
        ),
    )
    front_residual = envelope["x"] - territory["x"]
    rear_residual = territory["x"] + territory["width"] - envelope["x"] - envelope["w"]
    add(
        "PB-CAR-LIFT-EQUAL-END-RESIDUALS",
        abs(front_residual - rear_residual) < 1e-9
        and abs(front_residual - layout["front_residual"]) < 1e-9
        and abs(rear_residual - layout["rear_residual"]) < 1e-9,
        f"The centred envelope leaves equal {front_residual:.2f} m front and rear residuals.",
    )
    car_centre_x = car["x"] + car["w"] / 2
    car_centre_y = car["y"] + car["d"] / 2
    post_centres_x = [value + posts["w"] / 2 for value in posts["x"]]
    posts_centre_x = sum(post_centres_x) / len(post_centres_x)
    posts_centre_y = posts["y"] + posts["d"] / 2
    add(
        "PB-CAR-LIFT-INTERNAL-CENTRE",
        abs(car_centre_x - envelope_centre_x) < 1e-9
        and abs(car_centre_y - envelope_centre_y) < 1e-9
        and abs(posts_centre_x - envelope_centre_x) < 1e-9
        and abs(posts_centre_y - envelope_centre_y) < 1e-9,
        (
            "Vehicle and symmetric post-pair centres coincide with the envelope at "
            f"X={envelope_centre_x:.2f} m, Y={envelope_centre_y:.3f} m."
        ),
    )
    bench_gap = envelope["y"] - (bench["y0"] + bench["depth"])
    axis_gap = axis0 - (envelope["y"] + envelope["d"])
    add(
        "PB-CAR-LIFT-CONSTRAINED-TRANSVERSE-FIT",
        abs(envelope_centre_y - territory["centre"]["y"]) < 1e-9
        and abs(bench_gap - layout["bench_clearance"]) < 1e-9
        and abs(axis_gap - layout["axis_clearance"]) < 1e-9
        and abs(bench_gap - axis_gap) < 1e-9,
        (
            "The transverse envelope centre coincides with the usable-territory centre, "
            f"leaving equal {bench_gap:.3f} m graphic residuals to the bench and axis."
        ),
    )
    add(
        "PB-CAR-LIFT-REAL-EQUIPMENT",
        False,
        (
            "Real car and lift geometry, doors, arms, controls, tool carts, egress, "
            "slab loads, anchors and manufacturer working zones remain open."
        ),
        open_gate=True,
    )
    return checks


def _car_plan(
    parts: list[str],
    *,
    ox: float,
    oy: float,
    title: str,
    layout: dict[str, Any],
    territory: dict[str, Any],
) -> None:
    scale = 49.0
    x0 = 0.18
    y0 = 0.18
    x1 = 10.50
    y1 = 7.00

    def px(value: float) -> float:
        return ox + (value - x0) * scale

    def py(value: float) -> float:
        return oy + (y1 - value) * scale

    def plan_rect(x: float, y: float, w: float, d: float, **kwargs: Any) -> str:
        return base.rect(px(x), py(y + d), w * scale, d * scale, **kwargs)

    parts.append(base.text(ox, oy - 26, title, 13, "start", 700, "#26363c"))
    parts.append(base.rect(ox, oy, (x1 - x0) * scale, (y1 - y0) * scale, fill="#f7f4ee", stroke="#26363c", stroke_width="2"))
    parts.append(plan_rect(.18, .18, 9.0, .75, fill="#aeb9bc", stroke="#314247", stroke_width="1.2"))
    parts.append(base.text(px(4.68), py(.555) + 3, "9.00 m WALL BENCH", 6.3, weight=700))
    parts.append(plan_rect(territory["x"], territory["y"], territory["width"], territory["depth"], fill="none", stroke="#78918d", stroke_width="1.2", stroke_dasharray="7 4"))
    parts.append(base.text(px(territory["centre"]["x"]), py(6.78), "USABLE PROJECT CAR TERRITORY", 6.4, weight=700, fill="#4e6965"))

    envelope = layout["envelope"]
    car = layout["car"]
    posts = layout["posts"]
    parts.append(plan_rect(envelope["x"], envelope["y"], envelope["w"], envelope["d"], fill="none", stroke="#b14e35", stroke_width="1.6", stroke_dasharray="9 5"))
    parts.append(plan_rect(car["x"], car["y"], car.get("w", 4.8), car.get("d", 2.0), fill="#edf0ef", stroke="#4e5d63", stroke_width="1.2", rx="12"))
    parts.append(plan_rect(car["x"] + car.get("w", 4.8) * .24, car["y"] + car.get("d", 2.0) * .12, car.get("w", 4.8) * .52, car.get("d", 2.0) * .76, fill="#c9d6d8", stroke="#6b7a7f", stroke_width=".8", rx="7"))
    for post_x in posts["x"]:
        parts.append(plan_rect(post_x, posts["y"], posts["w"], posts["d"], fill="#48555b", stroke="#263238", stroke_width="1"))

    target_x = px(territory["centre"]["x"])
    target_y = py(territory["centre"]["y"])
    parts.append(f'<line x1="{target_x}" y1="{oy}" x2="{target_x}" y2="{oy + (y1-y0)*scale}" stroke="#a65f35" stroke-width="1" stroke-dasharray="6 4"/>')
    parts.append(f'<line x1="{ox}" y1="{target_y}" x2="{ox + (x1-x0)*scale}" y2="{target_y}" stroke="#a65f35" stroke-width="1" stroke-dasharray="6 4"/>')
    parts.append(base.text(target_x + 7, target_y - 8, "TARGET CENTRE", 6.5, "start", 700, "#8e3825"))
    parts.append(base.text(ox + 6, oy + 18, "Y=7.00 CENTRAL AXIS EDGE", 6.2, "start", 700, "#8a6518"))
    parts.append(base.text(ox + 6, oy + (y1-y0)*scale - 8, "SIDE A / BENCH EDGE", 6.2, "start", 700, "#526168"))


def car_centring_study_sheet(model: dict[str, Any]) -> str:
    meta = model["drawing_meta"]
    territory = model["car_territory"]
    proposed = model["car_lift_layout"]
    current = {
        "envelope": {"x": 1.60, "y": 1.05, "w": 6.40, "d": 5.90},
        "car": {"x": 2.25, "y": 2.15, "w": 4.80, "d": 2.00},
        "posts": {"x": [2.00, 6.85], "y": 1.25, "w": .35, "d": 4.00},
    }
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        base.title_block(meta["study_code"], meta["study_title"], meta["study_subtitle"]),
    ]
    _car_plan(
        parts,
        ox=70,
        oy=165,
        title="A · PREDECESSOR POSITION",
        layout=current,
        territory=territory,
    )
    _car_plan(
        parts,
        ox=745,
        oy=165,
        title="B · CENTRED b32 POSITION",
        layout=proposed,
        territory=territory,
    )

    parts.append(base.text(70, 555, "C · CENTRING SCHEDULE", 13, "start", 700, "#26363c"))
    rows = [
        ("USABLE TERRITORY", "X=0.18–10.50 m · Y=0.93–7.00 m · centre X=5.34 / Y=3.965 m"),
        ("LIFT ENVELOPE", "X=2.14–8.54 m · Y=1.03–6.90 m · centre X=5.34 / Y=3.965 m"),
        ("PROJECT CAR", "4.80 × 2.00 m symbol · X=2.94–7.74 m · Y=2.965–4.965 m"),
        ("POST PAIR", "X=2.74 and 7.59 m · symmetric about X=5.34 m · Y centre=3.965 m"),
        ("END RESIDUALS", "1.96 m front + 1.96 m rear · exact longitudinal centring"),
        ("SIDE RESIDUALS", "0.10 m to bench + 0.10 m to central axis · exact transverse centring"),
    ]
    for index, (key, value) in enumerate(rows):
        y = 578 + index * 37
        parts.append(base.rect(70, y, 610, 28, fill="#f3efe8", stroke="#c3bcb1", stroke_width=".8"))
        parts.append(base.text(86, y + 19, key, 7, "start", 700, "#8e3825"))
        parts.append(base.text(210, y + 19, value, 6.8, "start", 400, "#35454b"))

    parts.append(base.text(745, 555, "D · ARCHITECTURAL READING", 13, "start", 700, "#26363c"))
    notes = [
        ("WHOLE GROUP", "Car, posts and exclusion envelope now share one centre; this is not a cosmetic car-only move."),
        ("BENCH", "The Side A bench is subtracted before judging the usable transverse centre."),
        ("AXIS", "The Y=7.00 pedestrian axis stays visually and physically unobstructed."),
        ("MOVEMENT", "Envelope +0.54 m X; car +0.69 m X and +0.815 m Y from the predecessor."),
        ("SAFETY", "Graphic centring does not approve lift working clearances, door opening or egress."),
        ("PRODUCT", "Real car and lift data must replace every schematic rectangle before developed design."),
    ]
    for index, (key, value) in enumerate(notes):
        y = 578 + index * 37
        parts.append(base.rect(745, y, 585, 28, fill="#f7eddd", stroke="#c7ad86", stroke_width=".8"))
        parts.append(base.text(761, y + 19, key, 7, "start", 700, "#7d5528"))
        parts.append(base.text(855, y + 19, value, 6.5, "start", 400, "#35454b"))

    parts.append(base.rect(70, 845, 1260, 35, fill="#fff4df", stroke="#bd5c3c", stroke_width="1"))
    parts.append(base.text(88, 867, "OPTION STATUS", 8, "start", 700, "#8e3825"))
    parts.append(base.text(190, 867, "b32 supersedes b31 for project-car/lift position only. PB b29 remains the active published plan. Real equipment and manufacturer clearances remain mandatory. Not for construction.", 6.8, "start", 700, "#5a3a2c"))
    parts.append("</svg>")
    return "".join(parts)


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b32(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        "PB b32 centres the complete Project Car/lift group in its usable technical bay while retaining bench and axis constraints; PB b29 remains current.",
    )
    outputs = {
        "DH-ARQ-PLN-001-S03_PB-CENTRED-PROJECT-CAR-LIFT.svg": plan,
        "DH-ARQ-OPT-003-R00_PB-PROJECT-CAR-CENTRING-STUDY.svg": car_centring_study_sheet(model),
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
        "source": "dreamhouse/pb_b32_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b32.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b32 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b32_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

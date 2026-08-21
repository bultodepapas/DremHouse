"""Generate the researched, centred 12-seat PB dining refinement."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b30 as b30

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b30_delta.json")
DELTA = Path(__file__).with_name("pb_b31_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b31_pb"


def load_b31_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b30_delta.json changed; review the b31 option before regenerating")

    model = deepcopy(b30.load_b30_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["social_layout"]["dining"] = deepcopy(delta["dining"])
    model["research_sources"] = deepcopy(delta["research_sources"])
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    return model


def validate_b31(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b30.validate_b30(model)
    dining = model["social_layout"]["dining"]
    table = dining["table"]
    territory = dining["territory"]
    group = dining["group_envelope"]
    centre = dining["centre"]

    inherited_dining = next(
        item for item in checks if item["rule_id"] == "PB-DINING-INDEPENDENT"
    )
    inherited_dining["status"] = "PASS"
    inherited_dining["message"] = (
        "The researched 12-seat group uses five chairs on each long side and one at "
        "each head; table size is validated separately by b31."
    )
    owner_gate = next(item for item in checks if item["rule_id"] == "PB-KD-OWNER-SELECTION")
    owner_gate["message"] = (
        "The b31 table refinement follows the owner's instruction, but D-071 still "
        "locates dining beside the kitchen; record a new decision before promotion."
    )

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
                "message": message,
            }
        )

    territory_centre_x = territory["x"] + territory["width"] / 2
    territory_centre_y = territory["y"] + territory["depth"] / 2
    table_centre_x = table["x"] + table["length"] / 2
    table_centre_y = table["y"] + table["depth"] / 2
    add(
        "PB-KD-DINING-TRUE-CENTRE",
        abs(table_centre_x - territory_centre_x) < 1e-9
        and abs(table_centre_y - territory_centre_y) < 1e-9
        and abs(centre["x"] - territory_centre_x) < 1e-9
        and abs(centre["y"] - territory_centre_y) < 1e-9,
        f"The table and symmetric dining group are centred at X={table_centre_x:.2f} m, Y={table_centre_y:.2f} m in the 10.50 × 6.82 m territory.",
    )
    add(
        "PB-KD-DINING-12-SEATS",
        dining["seat_count"] == 12
        and 2 * dining["chairs_per_side"] + 2 * dining["end_chairs"] == 12,
        "The chair topology is 5 + 5 along the long sides and one chair at each head: 12 seats total.",
    )
    side_seat_width = table["length"] / dining["chairs_per_side"]
    add(
        "PB-KD-DINING-RESEARCHED-SIZE",
        3.05 <= table["length"] <= 3.30
        and 1.00 <= table["depth"] <= 1.20
        and side_seat_width >= 0.61,
        f"The 3.20 × 1.10 m table provides {side_seat_width:.2f} m per long-side chair and remains within the researched 12-seat product range.",
    )
    residual_x = (territory["width"] - group["width"]) / 2
    residual_y = (territory["depth"] - group["depth"]) / 2
    add(
        "PB-KD-DINING-CLEARANCE-ENVELOPE",
        dining["clearance_around_table"] >= 1.10
        and abs(group["x"] + group["width"] / 2 - centre["x"]) < 1e-9
        and abs(group["y"] + group["depth"] / 2 - centre["y"]) < 1e-9
        and residual_x >= 1.50
        and residual_y >= 1.50,
        f"A 1.10 m chair/walk envelope is centred with {residual_x:.2f} m and {residual_y:.2f} m additional open-space buffers beyond it.",
    )
    add(
        "PB-KD-DINING-PRODUCT-SELECTION",
        False,
        "Select the real table, base/leg geometry and chairs before procurement; nominal capacity does not prove that armchairs fit between the supports.",
        open_gate=True,
    )
    return checks


def dining_study_sheet(model: dict[str, Any]) -> str:
    dining = model["social_layout"]["dining"]
    table = dining["table"]
    territory = dining["territory"]
    group = dining["group_envelope"]
    meta = model["drawing_meta"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        base.title_block(meta["study_code"], meta["study_title"], meta["study_subtitle"]),
    ]

    parts.append(base.text(70, 120, "A · RESEARCH BASIS", 13, "start", 700, "#26363c"))
    evidence = [
        ("CAPACITY", "West Elm guidance: 120 in / 3.05 m rectangular table seats 12."),
        ("SEAT WIDTH", "West Elm + IKEA guidance: approximately 24 in / 0.61 m per diner."),
        ("PRODUCT", "Blakley 12-seat option: 120 × 39 or 45 in / 3.05 × 0.99 or 1.14 m."),
        ("CROSS-CHECK", "Pottery Barn Keaton: 120 × 52 in / 3.05 × 1.32 m seats 10–12."),
        ("CLEARANCE", "West Elm guidance: 36–44 in / 0.91–1.12 m table-to-wall chair zone."),
    ]
    for index, (key, value) in enumerate(evidence):
        y = 140 + index * 42
        parts.append(base.rect(70, y, 560, 32, fill="#f3efe8", stroke="#c3bcb1", stroke_width=".8"))
        parts.append(base.text(86, y + 21, key, 7.2, "start", 700, "#8e3825"))
        parts.append(base.text(175, y + 21, value, 7, "start", 400, "#35454b"))

    parts.append(base.text(70, 380, "B · SELECTED COORDINATION ENVELOPE", 13, "start", 700, "#26363c"))
    selected = [
        ("TABLE", "3.20 × 1.10 × 0.75 m · rectangular · product not selected"),
        ("CHAIRS", "5 per long side + 1 per head = 12 total"),
        ("PERSON", "0.64 m nominal width per long-side chair"),
        ("CLEAR ZONE", "1.10 m around the tabletop · symmetric 5.40 × 3.30 m envelope"),
        ("CENTRE", "X=26.25 m · Y=14.41 m · centre of the 10.50 × 6.82 m territory"),
    ]
    for index, (key, value) in enumerate(selected):
        y = 400 + index * 42
        parts.append(base.rect(70, y, 560, 32, fill="#f7eddd", stroke="#c7ad86", stroke_width=".8"))
        parts.append(base.text(86, y + 21, key, 7.2, "start", 700, "#7d5528"))
        parts.append(base.text(175, y + 21, value, 7, "start", 400, "#35454b"))

    parts.append(base.text(700, 120, "C · TRUE CENTRING IN THE SIDE B DINING TERRITORY", 13, "start", 700, "#26363c"))
    scale = 54.0
    ox = 720
    oy = 180

    def px(value: float) -> float:
        return ox + (value - territory["x"]) * scale

    def py(value: float) -> float:
        return oy + (territory["y"] + territory["depth"] - value) * scale

    def plan_rect(x: float, y: float, w: float, d: float, **kwargs: Any) -> str:
        return base.rect(px(x), py(y + d), w * scale, d * scale, **kwargs)

    parts.append(base.rect(ox, oy, territory["width"] * scale, territory["depth"] * scale, fill="#f7f4ee", stroke="#26363c", stroke_width="2"))
    parts.append(plan_rect(group["x"], group["y"], group["width"], group["depth"], fill="#fff8e7", stroke="#aa7b31", stroke_width="1.4", stroke_dasharray="8 5"))
    parts.append(plan_rect(table["x"], table["y"], table["length"], table["depth"], fill="#d6b58b", stroke="#60492f", stroke_width="1.5", rx="4"))
    parts.append(base.text(px(dining["centre"]["x"]), py(dining["centre"]["y"]) + 4, "3.20 × 1.10 m", 8, weight=700))

    chair_step = table["length"] / dining["chairs_per_side"]
    for index in range(dining["chairs_per_side"]):
        chair_x = table["x"] + chair_step * (index + .5)
        for chair_y in (table["y"] - .28, table["y"] + table["depth"] + .28):
            parts.append(f'<circle cx="{px(chair_x)}" cy="{py(chair_y)}" r="8" fill="#fbfaf6" stroke="#68767a"/>')
    head_y = table["y"] + table["depth"] / 2
    for chair_x in (table["x"] - .28, table["x"] + table["length"] + .28):
        parts.append(f'<circle cx="{px(chair_x)}" cy="{py(head_y)}" r="8" fill="#fbfaf6" stroke="#68767a"/>')

    centre_x = px(dining["centre"]["x"])
    centre_y = py(dining["centre"]["y"])
    parts.append(f'<line x1="{centre_x}" y1="{oy}" x2="{centre_x}" y2="{oy + territory["depth"] * scale}" stroke="#a65f35" stroke-width="1" stroke-dasharray="6 4"/>')
    parts.append(f'<line x1="{ox}" y1="{centre_y}" x2="{ox + territory["width"] * scale}" y2="{centre_y}" stroke="#a65f35" stroke-width="1" stroke-dasharray="6 4"/>')
    parts.append(base.text(centre_x + 8, centre_y - 10, "TRUE CENTRE · X=26.25 / Y=14.41", 7, "start", 700, "#8e3825"))
    parts.append(base.text(ox + territory["width"] * scale / 2, oy - 12, "SIDE B / LANDSCAPE SIDE", 7, weight=700, fill="#526168"))
    parts.append(base.text(ox + territory["width"] * scale / 2, oy + territory["depth"] * scale + 22, "CENTRAL PEDESTRIAN AXIS SIDE", 7, weight=700, fill="#8a6518"))
    parts.append(base.text(ox + 8, centre_y - 8, "2.55 m beyond clear envelope", 6.5, "start", 700, "#7d5528"))
    parts.append(base.text(ox + territory["width"] * scale - 8, centre_y - 8, "2.55 m", 6.5, "end", 700, "#7d5528"))
    parts.append(base.text(centre_x + 8, oy + 20, "1.76 m beyond envelope", 6.5, "start", 700, "#7d5528"))
    parts.append(base.text(centre_x + 8, oy + territory["depth"] * scale - 12, "1.76 m", 6.5, "start", 700, "#7d5528"))

    parts.append(base.text(700, 615, "D · ARCHITECTURAL RESULT", 13, "start", 700, "#26363c"))
    notes = [
        ("SCALE", "3.20 m is generous for 12 without turning the table into a banquet object."),
        ("COMFORT", "1.10 m depth supports shared dishes while keeping conversation and reach reasonable."),
        ("ORDER", "The symmetric 5+5+2 arrangement makes the centre visually legible in the large hall."),
        ("LIGHT", "Centre a linear pendant or pendant group on the final table, not on the room boundary."),
        ("HOLD", "Real chair width, arms, table supports and product capacity govern procurement."),
    ]
    for index, (key, value) in enumerate(notes):
        y = 635 + index * 39
        parts.append(base.rect(700, y, 630, 29, fill="#f3efe8", stroke="#c3bcb1", stroke_width=".8"))
        parts.append(base.text(715, y + 19, key, 7, "start", 700, "#8e3825"))
        parts.append(base.text(785, y + 19, value, 6.7, "start", 400, "#35454b"))

    parts.append(base.rect(70, 845, 1260, 35, fill="#fff4df", stroke="#bd5c3c", stroke_width="1"))
    parts.append(base.text(88, 867, "OPTION STATUS", 8, "start", 700, "#8e3825"))
    parts.append(base.text(190, 867, "b31 supersedes b30 for dining geometry only. PB b29 and D-071 remain active until the opposite-side dining move is formally adopted. Not for construction or procurement.", 6.8, "start", 700, "#5a3a2c"))
    parts.append("</svg>")
    return "".join(parts)


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b31(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        "PB b31 centres a researched 3.20 × 1.10 m 12-seat dining group within the Side B option territory; PB b29 remains current.",
    )
    outputs = {
        "DH-ARQ-PLN-001-S02_PB-CENTRED-12-SEAT-DINING.svg": plan,
        "DH-ARQ-OPT-002-R00_PB-CENTRED-DINING-STUDY.svg": dining_study_sheet(model),
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
        "source": "dreamhouse/pb_b31_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b31.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b31 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b31_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

"""Generate the non-adopted PB kitchen/dining option study requested on 2026-08-21."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b29 as b29

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b29_delta.json")
DELTA = Path(__file__).with_name("pb_b30_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b30_pb"


def load_b30_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b29_delta.json changed; review the b30 option before regenerating")

    model = deepcopy(b29.load_b29_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["kitchen"] = deepcopy(delta["kitchen"])
    model["social_layout"]["program_territories"] = deepcopy(delta["program_territories"])
    model["social_layout"]["dining"] = deepcopy(delta["dining"])
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    return model


def validate_b30(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b29.validate_b29(model)
    inherited_dining = next(
        item for item in checks if item["rule_id"] == "PB-DINING-INDEPENDENT"
    )
    inherited_dining["message"] = (
        "The 12-seat dining table remains an independent group; b30 separately tests "
        "its relocation opposite the kitchen."
    )
    kitchen = model["kitchen"]
    wall = kitchen["wall_run"]
    island = kitchen["island"]
    table = model["social_layout"]["dining"]["table"]
    great_wall_x = model["great_wall"]["x"]
    axis0 = model["design_values"]["axis_y0"]
    axis1 = model["design_values"]["axis_y1"]
    living = model["social_layout"]["living"]

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
                "message": message,
            }
        )

    add(
        "PB-KD-FULL-DOMESTIC-WALL",
        wall["length"] >= 10.0
        and wall["x"] >= 21.0
        and wall["x"] + wall["length"] <= great_wall_x - 0.25,
        f'The kitchen wall composition spans {wall["length"]:.2f} m of the 10.50 m domestic bay and stops {great_wall_x - wall["x"] - wall["length"]:.2f} m before the Great Wall.',
    )
    operating_aisle = island["y"] - (wall["y"] + wall["depth"])
    add(
        "PB-KD-WORKING-AISLE",
        1.30 <= operating_aisle <= 1.50,
        f"The wall-to-island working aisle is {operating_aisle:.2f} m.",
    )
    front_end_route = island["x"] - 21.0
    rear_end_route = great_wall_x - island["x"] - island["length"]
    add(
        "PB-KD-ISLAND-END-ROUTES",
        front_end_route >= 1.20 and rear_end_route >= 1.50,
        f"The 7.20 m island retains {front_end_route:.2f} m and {rear_end_route:.2f} m clear end routes.",
    )
    island_seat_edge = island["y"] + island["depth"] + 0.25 + 7 / base.S
    dining_near_edge = table["y"] - 0.25 - 7 / base.S
    add(
        "PB-KD-CENTRAL-AXIS-CLEAR",
        island_seat_edge < axis0 and dining_near_edge > axis1,
        f"Island seating ends at Y={island_seat_edge:.2f} m and dining begins at Y={dining_near_edge:.2f} m, outside the Y={axis0:.2f}–{axis1:.2f} m pedestrian axis.",
    )
    add(
        "PB-KD-DINING-OPPOSITE",
        table["y"] > axis1
        and table["x"] >= 21.0
        and table["x"] + table["length"] < great_wall_x,
        "The independent 12-seat dining table occupies the Side B domestic bay opposite the kitchen.",
    )
    add(
        "PB-KD-DINING-LIVING-SEPARATION",
        table["x"] - (living["rug"]["x"] + living["rug"]["w"]) >= 3.0,
        f'The dining table starts {table["x"] - living["rug"]["x"] - living["rug"]["w"]:.2f} m beyond the living rug.',
    )
    add(
        "PB-KD-DRY-ISLAND-SERVICES",
        "dry" in kitchen["service_strategy"].lower(),
        "The option keeps water, drainage and extraction on the Side A wall; the island carries only dry prep/seating and coordinated power/data.",
    )
    add(
        "PB-KD-OWNER-SELECTION",
        False,
        "D-024 and CF-006 remain open, and D-071 still locates dining beside the kitchen: "
        "confirm the b30 relationship and record a new decision before promotion.",
        open_gate=True,
    )
    add(
        "PB-KD-APPLIANCE-MEP",
        False,
        "Real appliance sizes, extraction, circuits, lighting, plumbing, joinery and replacement access remain open.",
        open_gate=True,
    )
    add(
        "PB-KD-DINING-DAYLIGHT",
        False,
        "The Side B dining opening and glare/thermal strategy depend on the selected site and coordinated P2 facade.",
        open_gate=True,
    )
    return checks


def _study_plan(
    parts: list[str],
    *,
    ox: float,
    oy: float,
    title: str,
    proposed: bool,
    model: dict[str, Any],
) -> None:
    scale = 23.0

    def px(value: float) -> float:
        return ox + (value - 21.0) * scale

    def py(value: float) -> float:
        return oy + (18.0 - value) * scale

    def plan_rect(x: float, y: float, w: float, d: float, **kwargs: Any) -> str:
        return base.rect(px(x), py(y + d), w * scale, d * scale, **kwargs)

    parts.append(base.text(ox, oy - 28, title, 13, "start", 700, "#26363c"))
    parts.append(
        base.rect(
            ox,
            oy,
            10.5 * scale,
            18.0 * scale,
            fill="#f7f4ee",
            stroke="#26363c",
            stroke_width="2",
        )
    )
    parts.append(
        plan_rect(
            21.0,
            7.0,
            10.5,
            4.0,
            fill="#fff8e7",
            stroke="#b87918",
            stroke_width="1.4",
            stroke_dasharray="7 4",
        )
    )
    parts.append(base.text(px(26.25), py(9.0) + 4, "4.00 m CLEAR AXIS", 7, weight=700, fill="#8d651d"))
    parts.append(base.text(px(26.25), py(17.45), "SIDE B", 7, weight=700, fill="#506168"))
    parts.append(base.text(px(26.25), py(.25), "SIDE A", 7, weight=700, fill="#506168"))
    parts.append(
        plan_rect(
            31.25,
            0.0,
            .25,
            18.0,
            fill="#856246",
            stroke="#4f3827",
            stroke_width="1",
        )
    )
    parts.append(base.text(px(31.10), py(9.0), "GREAT WALL", 6.2, weight=700, fill="#493426", rotate=-90))

    if proposed:
        kitchen = model["kitchen"]
        wall = kitchen["wall_run"]
        island = kitchen["island"]
        dining = model["social_layout"]["dining"]["table"]
        parts.append(plan_rect(wall["x"], wall["y"], wall["length"], wall["depth"], fill="#b69066", stroke="#60492f", stroke_width="1.2"))
        parts.append(base.text(px(wall["x"] + wall["length"] / 2), py(wall["y"] + wall["depth"] / 2) + 2, "10.05 m WALL COMPOSITION", 6.3, weight=700, fill="#fff7e9"))
        parts.append(plan_rect(island["x"], island["y"], island["length"], island["depth"], fill="#d1b187", stroke="#60492f", stroke_width="1.2", rx="3"))
        parts.append(base.text(px(island["x"] + island["length"] / 2), py(island["y"] + island["depth"] / 2) + 2, "7.20 m ISLAND", 7, weight=700))
        for index in range(8):
            cx = island["x"] + .5 + (island["length"] - 1.0) * (index + .5) / 8
            parts.append(
                f'<circle cx="{px(cx)}" cy="{py(island["y"] + island["depth"] + .25)}" '
                'r="4.8" fill="#f8f4ec" stroke="#68767a"/>'
            )
        parts.append(plan_rect(dining["x"], dining["y"], dining["length"], dining["depth"], fill="#efe6d7", stroke="#806a50", stroke_width="1.2", rx="3"))
        parts.append(base.text(px(dining["x"] + dining["length"] / 2), py(dining["y"] + dining["depth"] / 2) + 2, "12-SEAT DINING", 6.5, weight=700))
        parts.append(base.text(px(26.25), py(16.0), "FORMAL DINING / LANDSCAPE SIDE", 6.4, weight=700, fill="#755639"))
        parts.append(base.text(px(26.25), py(5.25), "DAILY MEALS AT ISLAND", 6.4, weight=700, fill="#755639"))
    else:
        parts.append(plan_rect(26.70, .25, 4.50, .75, fill="#b69066", stroke="#60492f", stroke_width="1.2"))
        parts.append(base.text(px(28.95), py(.625) + 2, "4.50 m WALL", 6.2, weight=700, fill="#fff7e9"))
        parts.append(plan_rect(27.00, 2.20, 3.60, 1.20, fill="#d1b187", stroke="#60492f", stroke_width="1.2", rx="3"))
        parts.append(base.text(px(28.80), py(2.80) + 2, "3.60 m ISLAND", 6.3, weight=700))
        parts.append(plan_rect(22.60, 2.50, 3.60, 1.30, fill="#efe6d7", stroke="#806a50", stroke_width="1.2", rx="3"))
        parts.append(base.text(px(24.40), py(3.15) + 2, "12-SEAT DINING", 6.3, weight=700))
        parts.append(
            plan_rect(
                21.20,
                11.20,
                9.80,
                6.20,
                fill="#f2efe9",
                stroke="#aaa298",
                stroke_width="1",
                stroke_dasharray="5 4",
            )
        )
        parts.append(base.text(px(26.10), py(14.30) + 2, "UNDERUSED DOMESTIC HALF", 6.5, weight=700, fill="#817a72"))


def kitchen_study_sheet(model: dict[str, Any]) -> str:
    meta = model["drawing_meta"]
    kitchen = model["kitchen"]
    wall = kitchen["wall_run"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        base.title_block(meta["study_code"], meta["study_title"], meta["study_subtitle"]),
    ]

    _study_plan(parts, ox=70, oy=145, title="A · CURRENT PB b29", proposed=False, model=model)
    _study_plan(parts, ox=390, oy=145, title="B · PREFERRED TEST (NOT ADOPTED)", proposed=True, model=model)

    parts.append(base.text(735, 117, "C · 10.05 m KITCHEN WALL COMPOSITION", 13, "start", 700, "#26363c"))
    scale = 54.0
    x0 = 765
    floor = 410
    for module in kitchen["wall_modules"]:
        local_x = x0 + (module["x"] - wall["x"]) * scale
        module_w = module["length"] * scale
        is_tall = module["label"] in {"FR", "FZ", "OV"}
        height = 190 if is_tall else 78
        y = floor - height
        parts.append(base.rect(local_x, y, module_w, height, fill="#b69066" if not is_tall else "#927051", stroke="#5a412d", stroke_width="1"))
        parts.append(base.text(local_x + module_w / 2, y + height / 2 + 3, module["label"], 6.2 if len(module["label"]) < 6 else 5.2, weight=700, fill="#fff8ef"))
    parts.append(f'<line x1="{x0}" y1="{floor}" x2="{x0 + wall["length"] * scale}" y2="{floor}" stroke="#26363c" stroke-width="2"/>')
    parts.append(base.text(x0 + wall["length"] * scale / 2, floor + 24, "FULL DOMESTIC-BAY READING · STANDARD MODULAR CARCASSES", 7.2, weight=700))
    parts.append(base.text(735, 465, "D · WHY THE ISLAND STOPS AT 7.20 m", 13, "start", 700, "#26363c"))
    island_x = 835
    island_y = 510
    island_w = kitchen["island"]["length"] * 54
    parts.append(base.rect(island_x, island_y, island_w, 68, fill="#d1b187", stroke="#60492f", stroke_width="1.4", rx="4"))
    parts.append(base.text(island_x + island_w / 2, island_y + 38, "7.20 m DRY ISLAND · 8 SEATS", 8, weight=700))
    for index in range(8):
        cx = island_x + 28 + (island_w - 56) * (index + .5) / 8
        parts.append(
            f'<circle cx="{cx}" cy="{island_y + 88}" r="8" '
            'fill="#faf7f0" stroke="#68767a"/>'
        )
    parts.append(base.text(760, island_y + 36, "1.40 m", 7, "end", 700, "#8e3825"))
    parts.append(base.text(island_x + island_w + 20, island_y + 36, "1.90 m", 7, "start", 700, "#8e3825"))
    parts.append(base.text(735, 625, "E · ARCHITECTURAL READING", 13, "start", 700, "#26363c"))
    notes = [
        ("SPACE", "Kitchen gains the entire Side A domestic bay; dining activates the empty Side B half."),
        ("USE", "Eight island seats handle daily meals; the opposite 12-seat table becomes the formal/event table."),
        ("FLOW", "The 4.00 m centreline remains untouched; 1.40 m and 1.90 m island-end routes prevent a barrier."),
        ("MEP", "Keep sink, dishwasher and extraction on the wall. A dry island avoids slab drainage and duct loops."),
        ("COST", "The test is close to the control-estimate total joinery length, but shifts scope into a larger island."),
    ]
    for index, (key, value) in enumerate(notes):
        y = 645 + index * 40
        parts.append(base.rect(735, y, 595, 30, fill="#f3efe8", stroke="#c3bcb1", stroke_width=".8"))
        parts.append(base.text(750, y + 20, key, 7.2, "start", 700, "#8e3825"))
        parts.append(base.text(820, y + 20, value, 6.6, "start", 400, "#35454b"))

    parts.append(base.rect(70, 835, 1260, 45, fill="#fff4df", stroke="#bd5c3c", stroke_width="1"))
    parts.append(base.text(88, 854, "OPTION STATUS", 8, "start", 700, "#8e3825"))
    parts.append(base.text(185, 854, "Owner-requested study only. PB b29 remains current; D-024 and CF-006 remain open. Site, appliances, MEP, facade, detailed joinery and quotations must precede design freeze.", 6.8, "start", 700, "#5a3a2c"))
    parts.append(base.text(88, 870, "ARCHITECT'S POSITION", 8, "start", 700, "#8e3825"))
    parts.append(base.text(185, 870, "Use the whole bay visually, but retain island-end circulation. A literal 10.50 m wall-to-wall island is not recommended.", 6.8, "start", 700, "#5a3a2c"))
    parts.append("</svg>")
    return "".join(parts)


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b30(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        "PB b30 is an owner-requested kitchen/dining option only; PB b29 remains current and D-024/CF-006 remain open.",
    )
    outputs = {
        "DH-ARQ-PLN-001-S01_PB-KITCHEN-DINING-OPTION.svg": plan,
        "DH-ARQ-OPT-001-R00_PB-KITCHEN-DINING-STUDY.svg": kitchen_study_sheet(model),
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
        "source": "dreamhouse/pb_b30_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b30.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b30 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b30_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

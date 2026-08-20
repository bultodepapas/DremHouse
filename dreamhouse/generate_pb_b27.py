"""Generate the D-071 Side B perimeter-wall TV living-room revision."""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b25 as b25
from dreamhouse import generate_pb_b26 as b26

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b26_delta.json")
DELTA = Path(__file__).with_name("pb_b27_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b27_pb"


def load_b27_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b26_delta.json changed; review the b27 delta before regenerating")

    model = deepcopy(b26.load_b26_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["social_layout"] = deepcopy(delta["social_layout"])
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    return model


def perimeter_media_sheet(model: dict[str, Any]) -> str:
    social = model["social_layout"]
    media = social["media_wall"]
    living = social["living"]
    meta = model["drawing_meta"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        base.title_block(meta["media_code"], meta["media_title"], meta["media_subtitle"]),
    ]

    # A — the real perimeter wall, seen from the living room.
    parts.append(base.text(70, 125, "A · SIDE B HALL-WALL INTERIOR ELEVATION", 14, "start", 700))
    scale = 150
    wall_x = 70
    floor_y = 730
    wall_w = (media["x1"] - media["x0"]) * scale
    wall_h = media["height"] * scale
    wall_y = floor_y - wall_h
    parts.append(
        base.rect(
            wall_x,
            wall_y,
            wall_w,
            wall_h,
            fill="#c6a37b",
            stroke="#302821",
            stroke_width="2.5",
        )
    )
    for offset in range(12, int(wall_w), 15):
        parts.append(
            f'<line x1="{wall_x + offset}" y1="{wall_y}" '
            f'x2="{wall_x + offset}" y2="{floor_y}" '
            'stroke="#8d6f50" stroke-width=".8"/>'
        )

    tv_w = media["tv_width"] * scale
    tv_h = media["tv_height"] * scale
    tv_x = wall_x + (wall_w - tv_w) / 2
    tv_center_y = floor_y - media["tv_center_height"] * scale
    tv_y = tv_center_y - tv_h / 2
    parts.append(
        base.rect(
            tv_x,
            tv_y,
            tv_w,
            tv_h,
            fill="#172126",
            stroke="#080b0c",
            stroke_width="4",
            rx="3",
        )
    )
    parts.append(
        base.rect(
            tv_x + 9,
            tv_y + 9,
            tv_w - 18,
            tv_h - 18,
            fill="#324e57",
            stroke="#718b91",
            stroke_width="1",
        )
    )
    parts.append(
        base.text(
            tv_x + tv_w / 2,
            tv_y + tv_h / 2 - 5,
            "100-IN TV EQUIPMENT ENVELOPE",
            11,
            weight=700,
            fill="#f1f5f4",
        )
    )
    parts.append(
        base.text(
            tv_x + tv_w / 2,
            tv_y + tv_h / 2 + 14,
            f'{media["tv_width"]:.2f} × {media["tv_height"]:.2f} m · 16:9',
            8,
            fill="#e0e8e7",
        )
    )

    console = media["console"]
    console_w = console["length"] * scale
    console_h = console["height"] * scale
    console_x = wall_x + (wall_w - console_w) / 2
    console_y = floor_y - console_h
    parts.append(
        base.rect(
            console_x,
            console_y,
            console_w,
            console_h,
            fill="#6f543e",
            stroke="#30241b",
            stroke_width="2",
        )
    )
    for division in range(1, 4):
        xx = console_x + console_w * division / 4
        parts.append(
            f'<line x1="{xx}" y1="{console_y}" x2="{xx}" y2="{floor_y}" '
            'stroke="#b99876" stroke-width="1"/>'
        )
    parts.append(
        base.text(
            console_x + console_w / 2,
            console_y + console_h / 2 + 4,
            "3.40 m ACCESSIBLE AV CONSOLE",
            9,
            weight=700,
            fill="#fff5e9",
        )
    )
    parts.append(
        f'<line x1="{wall_x}" y1="{floor_y}" x2="{wall_x + wall_w}" '
        f'y2="{floor_y}" stroke="#273136" stroke-width="3"/>'
    )
    parts.append(
        base.text(
            wall_x + wall_w / 2,
            floor_y + 28,
            "4.40 m MOUNTING FIELD · DIRECTLY ON SIDE B PERIMETER WALL",
            9.5,
            weight=700,
        )
    )
    parts.append(
        base.text(
            wall_x + wall_w / 2,
            wall_y - 14,
            "NO INTERNAL MEDIA PARTITION · BACKING AND SERVICES REMAIN WITHIN THE WALL BUILD-UP",
            8,
            weight=700,
            fill="#654832",
        )
    )
    leader_x = wall_x + wall_w - 18
    parts.append(
        f'<line x1="{tv_x + tv_w + 8}" y1="{tv_center_y}" '
        f'x2="{leader_x}" y2="{tv_center_y}" stroke="#9b4c32" stroke-width="1.2"/>'
    )
    parts.append(
        base.text(
            leader_x - 4,
            tv_center_y - 7,
            f'TV CENTRE +{media["tv_center_height"]:.2f} m AFF',
            7.5,
            "end",
            700,
            "#8e3825",
        )
    )

    # B — plan relationship showing the wall, workstation and protected axis.
    parts.append(base.text(790, 125, "B · WALL / LIVING / WORKSTATION RELATIONSHIP", 14, "start", 700))
    parts.append(base.rect(780, 150, 550, 300, fill="#f2eee7", stroke="#aaa297", stroke_width="1"))
    x_scale = 58
    y_scale = 38

    def px(value: float) -> float:
        return 800 + (value - 13.0) * x_scale

    def py(value: float) -> float:
        return 430 - (value - 11.0) * y_scale

    ws_b = next(item for item in model["workstations"] if item["side"] == "B")
    ws_y0 = model["envelope"]["width"] - model["envelope"]["exterior_wall"] - ws_b["zone_depth"]
    parts.append(
        base.rect(
            px(ws_b["zone_x0"]),
            py(model["envelope"]["width"] - model["envelope"]["exterior_wall"]),
            (ws_b["zone_x1"] - ws_b["zone_x0"]) * x_scale,
            ws_b["zone_depth"] * y_scale,
            fill="#dce9e5",
            stroke="#5d6d69",
            stroke_width="1.2",
        )
    )
    parts.append(base.text(px(14.5), py(ws_y0 + 1.5), "WORKSTATION 2", 8, weight=700))

    rug = living["rug"]
    parts.append(
        base.rect(
            px(rug["x"]),
            py(rug["y"] + rug["d"]),
            rug["w"] * x_scale,
            rug["d"] * y_scale,
            fill="#d8c5ae",
            stroke="#927a61",
            stroke_width="1",
            rx="8",
        )
    )
    sofa = living["sofa"]
    parts.append(
        base.rect(
            px(sofa["x"]),
            py(sofa["y"] + sofa["depth"]),
            sofa["length"] * x_scale,
            sofa["depth"] * y_scale,
            fill="#aa9077",
            stroke="#685748",
            stroke_width="1.5",
            rx="5",
        )
    )
    chaise = living["chaise"]
    parts.append(
        base.rect(
            px(chaise["x"]),
            py(chaise["y"] + chaise["d"]),
            chaise["w"] * x_scale,
            chaise["d"] * y_scale,
            fill="#aa9077",
            stroke="#685748",
            stroke_width="1.5",
            rx="5",
        )
    )
    wall_plan_y = py(media["y"])
    parts.append(
        f'<line x1="{px(media["x0"])}" y1="{wall_plan_y}" '
        f'x2="{px(media["x1"])}" y2="{wall_plan_y}" '
        'stroke="#4b3b31" stroke-width="8"/>'
    )
    tv_x0 = media["tv_center_x"] - media["tv_width"] / 2
    parts.append(
        f'<line x1="{px(tv_x0)}" y1="{wall_plan_y + 5}" '
        f'x2="{px(tv_x0 + media["tv_width"])}" y2="{wall_plan_y + 5}" '
        'stroke="#111719" stroke-width="5"/>'
    )
    view_x = px(media["tv_center_x"])
    parts.append(
        f'<line x1="{view_x}" y1="{py(media["viewing_point_y"])}" '
        f'x2="{view_x}" y2="{wall_plan_y}" stroke="#a46d20" '
        'stroke-width="1.5" stroke-dasharray="6 4"/>'
    )
    parts.append(
        base.text(
            view_x + 9,
            (py(media["viewing_point_y"]) + wall_plan_y) / 2,
            f'{media["viewing_distance"]:.2f} m VIEW',
            8,
            "start",
            700,
            "#8a5b1c",
            rotate=-90,
        )
    )
    axis_y = py(model["design_values"]["axis_y1"])
    parts.append(
        f'<line x1="{px(13)}" y1="{axis_y}" x2="{px(21)}" y2="{axis_y}" '
        'stroke="#b47d16" stroke-width="2" stroke-dasharray="8 4"/>'
    )
    parts.append(base.text(px(17), axis_y - 7, "4.00 m CENTRAL AXIS ENDS HERE", 8, weight=700, fill="#8a6518"))
    parts.append(base.text(px(18.6), 438, "LIVING / TV · SIDE B WALL", 9, weight=700, fill="#5b432b"))

    # C — coordination schedule.
    parts.append(base.text(790, 480, "C · COORDINATION SCHEDULE", 14, "start", 700))
    rows = [
        ("LOCATION", "Existing Side B perimeter wall · X=16.40–20.80 m · no room divider"),
        ("TV", f'{media["tv_diagonal_inches"]:.0f} in · {media["tv_width"]:.3f} × {media["tv_height"]:.3f} m · product pending'),
        ("VIEW", f'{media["viewing_distance"]:.2f} m test distance · furniture remains beyond Y=11.00 m axis'),
        ("BACKING", "Verify facade studs/girts, local reinforcement and mount eccentric load"),
        ("AV", "Accessible power/data, spare conduits, ventilation and replacement route"),
        ("ENVELOPE", "Maintain insulation, vapour, air/water, fire and acoustic continuity"),
    ]
    for index, (key, value) in enumerate(rows):
        y = 500 + index * 42
        parts.append(base.rect(790, y, 520, 32, fill="#f1eee7", stroke="#c0bbb0", stroke_width=".8"))
        parts.append(base.text(806, y + 21, key, 8, "start", 700, "#8e3825"))
        parts.append(base.text(885, y + 21, value, 7.2, "start"))

    parts.append(base.rect(70, 805, 1260, 75, fill="#fff4df", stroke="#bd5c3c", stroke_width="1"))
    parts.append(base.text(88, 830, "FACADE HOLD", 9.5, "start", 700, "#8e3825"))
    parts.append(base.text(220, 830, "The TV is on the hall wall, but unverified cladding rails or window framing may not carry its load. Design local independent backing and sealed penetrations.", 7.5, "start", 700, "#5a3a2c"))
    parts.append(base.text(88, 852, "EQUIPMENT HOLD", 9.5, "start", 700, "#8e3825"))
    parts.append(base.text(220, 852, "Confirm real TV mass, mount pattern, speakers, console equipment, cooling, access and replacement path before fabrication.", 7.5, "start", 700, "#5a3a2c"))
    parts.append(base.text(88, 873, "VISUAL HOLD", 9.5, "start", 700, "#8e3825"))
    parts.append(base.text(220, 873, "Validate Side B daylight and glare after site selection; keep the TV field solid and preserve workstation glazing at X=13.00–16.00 m.", 7.5, "start", 700, "#5a3a2c"))
    parts.append("</svg>")
    return "".join(parts)


def validate_b27(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b25.validate_b25(model)
    social = model["social_layout"]
    media = social["media_wall"]
    living = social["living"]
    dining = social["dining"]
    axis1 = model["design_values"]["axis_y1"]

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
                "message": message,
            }
        )

    chair_radius_m = 11 / base.S
    sofa = living["sofa"]
    chaise = living["chaise"]
    living_min_y = min(
        living["rug"]["y"],
        sofa["y"],
        chaise["y"],
        living["coffee_table"]["y"],
        min(item["y"] - chair_radius_m for item in living["chairs"]),
        media["y"] - media["backing_depth"],
        media["y"] - media["console"]["depth"],
    )
    add(
        "PB-SOCIAL-AXIS-CLEAR",
        living_min_y > axis1,
        f"Living furniture begins at Y={living_min_y:.2f} m beyond the Y={axis1:.2f} m pedestrian axis.",
    )

    ws_b = next(item for item in model["workstations"] if item["side"] == "B")
    living_min_x = min(
        living["rug"]["x"],
        sofa["x"],
        chaise["x"],
        living["coffee_table"]["x"],
        min(item["x"] - chair_radius_m for item in living["chairs"]),
        media["x0"],
        media["console"]["x"],
    )
    add(
        "PB-SOCIAL-WORKSTATION-CLEAR",
        living_min_x > ws_b["zone_x1"],
        f"Living furniture starts at X={living_min_x:.2f} m beyond the workstation-2 zone ending at X={ws_b['zone_x1']:.2f} m.",
    )

    side_b_inside = model["envelope"]["width"] - model["envelope"]["exterior_wall"]
    add(
        "PB-TV-SIDE-B-PERIMETER",
        media["mounting"] == "side_b_perimeter"
        and media["side"] == "B"
        and abs(media["y"] - side_b_inside) < 1e-9
        and media["x0"] >= 16.0
        and media["x1"] < 21.0,
        "The 100-inch TV mounting field is directly on the Side B perimeter wall and no internal media partition remains.",
    )

    diagonal_m = media["tv_diagonal_inches"] * 0.0254
    expected_w = diagonal_m * 16 / math.sqrt(16**2 + 9**2)
    expected_h = diagonal_m * 9 / math.sqrt(16**2 + 9**2)
    add(
        "PB-TV-100-IN-ENVELOPE",
        abs(media["tv_width"] - expected_w) < 0.01
        and abs(media["tv_height"] - expected_h) < 0.01,
        f'The 100-inch 16:9 test envelope is {media["tv_width"]:.3f} × {media["tv_height"]:.3f} m.',
    )
    calculated_view = media["y"] - media["viewing_point_y"]
    add(
        "PB-TV-VIEWING-DISTANCE",
        abs(calculated_view - media["viewing_distance"]) < 1e-9
        and 3.5 <= calculated_view <= 4.5,
        f"The test viewing point is {calculated_view:.2f} m from the Side B TV wall.",
    )
    table = dining["table"]
    add(
        "PB-DINING-INDEPENDENT",
        table["length"] == 3.6
        and table["depth"] == 1.3
        and dining["chairs_per_side"] == 6
        and table["x"] > 21.0,
        "The 12-seat dining table remains beside the kitchen and no longer depends on a reverse-face media partition.",
    )
    add(
        "PB-SIDE-B-SOLID-HALL-BAY",
        model.get("side_b_main_bay") == "solid",
        "The Side B hall bay remains solid behind the TV mounting field pending site design.",
    )
    add(
        "PB-TV-PERIMETER-BACKING",
        False,
        "Local Side B wall backing, mount loads, facade penetrations and enclosure continuity require structural/facade design.",
        open_gate=True,
    )
    add(
        "PB-TV-AV-MEP",
        False,
        "Real TV, mount, speakers, power, data, AV, ventilation and replacement access remain open.",
        open_gate=True,
    )
    add(
        "PB-TV-GLARE-SIDE-B",
        False,
        "Side B daylight, glare and blackout control remain dependent on the selected site and facade design.",
        open_gate=True,
    )
    return checks


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b27(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        "D-071 places the 100-inch TV directly on the Side B perimeter wall and removes the internal media partition.",
    )
    outputs = {
        "DH-ARQ-PLN-001-R08_PB-SIDE-B-WALL-TV-LIVING.svg": plan,
        "DH-ARQ-ELE-INT-002-R01_PB-100IN-SIDE-B-WALL.svg": perimeter_media_sheet(model),
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
        "source": "dreamhouse/pb_b27_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b27.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b27 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b27_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

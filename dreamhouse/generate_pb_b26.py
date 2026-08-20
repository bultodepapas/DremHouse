"""Generate the D-070 ground-floor living, dining and media-wall revision."""

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

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b25_delta.json")
DELTA = Path(__file__).with_name("pb_b26_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b26_pb"


def load_b26_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b25_delta.json changed; review the b26 delta before regenerating")

    model = deepcopy(b25.load_b25_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["side_b_main_bay"] = delta["side_b_main_bay"]
    model["social_layout"] = deepcopy(delta["social_layout"])
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    return model


def media_wall_sheet(model: dict[str, Any]) -> str:
    social = model["social_layout"]
    media = social["media_wall"]
    dining = social["dining"]
    living = social["living"]
    meta = model["drawing_meta"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        base.title_block(meta["media_code"], meta["media_title"], meta["media_subtitle"]),
    ]

    # A — living-side interior elevation.
    parts.append(base.text(85, 125, "A · LIVING-SIDE INTERIOR ELEVATION", 14, "start", 700))
    scale = 150
    wall_x = 90
    floor_y = 730
    wall_w = (media["y1"] - media["y0"]) * scale
    wall_h = media["height"] * scale
    wall_y = floor_y - wall_h
    parts.append(base.rect(wall_x, wall_y, wall_w, wall_h, fill="#c6a37b", stroke="#302821", stroke_width="2.5"))
    for offset in range(12, int(wall_w), 15):
        parts.append(f'<line x1="{wall_x+offset}" y1="{wall_y}" x2="{wall_x+offset}" y2="{floor_y}" stroke="#8d6f50" stroke-width=".8"/>')
    tv_w = media["tv_width"] * scale
    tv_h = media["tv_height"] * scale
    tv_x = wall_x + (wall_w - tv_w) / 2
    tv_center_y = floor_y - media["tv_center_height"] * scale
    tv_y = tv_center_y - tv_h / 2
    parts.append(base.rect(tv_x, tv_y, tv_w, tv_h, fill="#172126", stroke="#080b0c", stroke_width="4", rx="3"))
    parts.append(base.rect(tv_x+9, tv_y+9, tv_w-18, tv_h-18, fill="#324e57", stroke="#718b91", stroke_width="1"))
    parts.append(base.text(tv_x+tv_w/2, tv_y+tv_h/2-5, "100-IN TV EQUIPMENT ENVELOPE", 11, weight=700, fill="#f1f5f4"))
    parts.append(base.text(tv_x+tv_w/2, tv_y+tv_h/2+14, f'{media["tv_width"]:.2f} × {media["tv_height"]:.2f} m · 16:9', 8, fill="#e0e8e7"))
    console_w = media["console"]["length"] * scale
    console_h = media["console"]["height"] * scale
    console_x = wall_x + (wall_w - console_w) / 2
    console_y = floor_y - console_h
    parts.append(base.rect(console_x, console_y, console_w, console_h, fill="#6f543e", stroke="#30241b", stroke_width="2"))
    for division in range(1, 4):
        xx = console_x + console_w * division / 4
        parts.append(f'<line x1="{xx}" y1="{console_y}" x2="{xx}" y2="{floor_y}" stroke="#b99876" stroke-width="1"/>')
    parts.append(base.text(console_x+console_w/2, console_y+console_h/2+4, "3.40 m ACCESSIBLE AV CONSOLE", 9, weight=700, fill="#fff5e9"))
    parts.append(f'<line x1="{wall_x}" y1="{floor_y}" x2="{wall_x+wall_w}" y2="{floor_y}" stroke="#273136" stroke-width="3"/>')
    parts.append(base.text(wall_x+wall_w/2, floor_y+28, "4.20 m MEDIA WALL · X=21.00 m UPPER-FLOOR EDGE", 10, weight=700))
    parts.append(base.text(wall_x+wall_w/2, wall_y-14, "WARM ACOUSTIC FINISH OVER INDEPENDENTLY COORDINATED SECONDARY FRAME", 8, weight=700, fill="#654832"))
    dim_x = wall_x + wall_w + 24
    parts.append(f'<line x1="{dim_x}" y1="{tv_y}" x2="{dim_x}" y2="{floor_y}" stroke="#9b4c32" stroke-width="1.2"/>')
    parts.append(base.text(dim_x+10, (tv_center_y+floor_y)/2, f'TV CENTRE +{media["tv_center_height"]:.2f} m', 7.5, "start", 700, "#8e3825"))

    # B — relationship plan.
    parts.append(base.text(790, 125, "B · LIVING / MEDIA / DINING RELATIONSHIP", 14, "start", 700))
    parts.append(base.rect(780, 150, 550, 285, fill="#f2eee7", stroke="#aaa297", stroke_width="1"))
    plan_scale = 40
    px0 = 800
    py0 = 175
    sofa = living["sofa"]
    wall_px = px0 + (media["x"] - 16.0) * plan_scale
    wall_py = py0
    wall_ph = (media["y1"] - media["y0"]) * plan_scale
    parts.append(base.rect(px0, py0+48, sofa["depth"]*plan_scale, sofa["length"]*plan_scale, fill="#aa9077", stroke="#685748", stroke_width="1.5", rx="5"))
    parts.append(base.rect(wall_px-media["thickness"]*plan_scale, wall_py, media["thickness"]*plan_scale, wall_ph, fill="#4b3b31", stroke="#241e1a", stroke_width="1.5"))
    tv_plan_y = wall_py + (wall_ph-media["tv_width"]*plan_scale)/2
    parts.append(f'<line x1="{wall_px-media["thickness"]*plan_scale-4}" y1="{tv_plan_y}" x2="{wall_px-media["thickness"]*plan_scale-4}" y2="{tv_plan_y+media["tv_width"]*plan_scale}" stroke="#111719" stroke-width="5"/>')
    sideboard = dining["sideboard"]
    parts.append(base.rect(wall_px+4, wall_py+8, sideboard["depth"]*plan_scale, sideboard["length"]*plan_scale, fill="#a98460", stroke="#5a4330", stroke_width="1"))
    table = dining["table"]
    table_x = px0 + (table["x"]-16.0)*plan_scale
    table_y = py0 + (table["y"]-media["y0"])*plan_scale
    parts.append(base.rect(table_x, table_y, table["length"]*plan_scale, table["depth"]*plan_scale, fill="#dfc49d", stroke="#60492f", stroke_width="1.5", rx="4"))
    view_x0 = px0 + (media["viewing_point_x"]-16.0)*plan_scale
    view_x1 = wall_px-media["thickness"]*plan_scale
    view_y = py0 + (media["tv_center_y"]-media["y0"])*plan_scale
    parts.append(f'<line x1="{view_x0}" y1="{view_y}" x2="{view_x1}" y2="{view_y}" stroke="#a46d20" stroke-width="1.5" stroke-dasharray="6 4"/>')
    parts.append(base.text((view_x0+view_x1)/2, view_y-9, f'{media["viewing_distance"]:.2f} m VIEW', 8, weight=700, fill="#8a5b1c"))
    parts.append(base.text(px0+20, 410, "LIVING / TV", 9, "start", 700, "#5b432b"))
    parts.append(base.text(table_x+table["length"]*plan_scale/2, 410, "DINING", 9, weight=700, fill="#5b432b"))

    # C — test schedule.
    parts.append(base.text(790, 475, "C · COORDINATION SCHEDULE", 14, "start", 700))
    rows = [
        ("TV", f'{media["tv_diagonal_inches"]:.0f} in · {media["tv_width"]:.3f} × {media["tv_height"]:.3f} m · product pending'),
        ("VIEW", f'{media["viewing_distance"]:.2f} m test distance · central axis remains clear'),
        ("WALL", f'{media["y1"]-media["y0"]:.2f} × {media["height"]:.2f} m · 0.25 m test thickness'),
        ("AV", "Accessible power/data, spare conduits, ventilation and replacement route"),
        ("REVERSE", "3.80 m dining sideboard/service face; no concealed inaccessible services"),
        ("GLARE", "Main glazing remains open under H-07; coordinate solar/blackout control"),
    ]
    for index, (key, value) in enumerate(rows):
        y = 495 + index * 42
        parts.append(base.rect(790, y, 520, 32, fill="#f1eee7", stroke="#c0bbb0", stroke_width=".8"))
        parts.append(base.text(806, y+21, key, 8, "start", 700, "#8e3825"))
        parts.append(base.text(870, y+21, value, 7.4, "start"))

    parts.append(base.rect(70, 805, 1260, 75, fill="#fff4df", stroke="#bd5c3c", stroke_width="1"))
    parts.append(base.text(88, 830, "STRUCTURE HOLD", 9.5, "start", 700, "#8e3825"))
    parts.append(base.text(220, 830, "Alignment with X=21.00 m does not make this media wall primary structure. Coordinate frame, attachments, edge truss, deflection, fire and acoustics.", 7.6, "start", 700, "#5a3a2c"))
    parts.append(base.text(88, 852, "EQUIPMENT HOLD", 9.5, "start", 700, "#8e3825"))
    parts.append(base.text(220, 852, "Confirm real TV mass, mount pattern, speakers, console equipment, cooling, access and replacement path before fabrication.", 7.6, "start", 700, "#5a3a2c"))
    parts.append(base.text(88, 873, "VISUAL HOLD", 9.5, "start", 700, "#8e3825"))
    parts.append(base.text(220, 873, "Validate screen glare and curtain strategy with the selected site while retaining the D-070 furniture/axis logic.", 7.6, "start", 700, "#5a3a2c"))
    parts.append("</svg>")
    return "".join(parts)


def validate_b26(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b25.validate_b25(model)
    social = model["social_layout"]
    media = social["media_wall"]
    living = social["living"]
    dining = social["dining"]
    axis0 = model["design_values"]["axis_y0"]

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
                "message": message,
            }
        )

    chair_radius_m = 11 / base.S
    living_max_y = max(
        living["rug"]["y"] + living["rug"]["d"],
        living["sofa"]["y"] + living["sofa"]["length"],
        living["chaise"]["y"] + living["chaise"]["depth"],
        living["coffee_table"]["y"] + living["coffee_table"]["d"],
        max(item["y"] + chair_radius_m for item in living["chairs"]),
        media["y1"],
    )
    add(
        "PB-SOCIAL-AXIS-CLEAR",
        living_max_y < axis0,
        f"Living furniture and media wall stop at Y={living_max_y:.2f} m before the Y={axis0:.2f} m pedestrian axis.",
    )
    ws_a = next(item for item in model["workstations"] if item["side"] == "A")
    ws_zone_top = model["envelope"]["exterior_wall"] + ws_a["zone_depth"]
    furniture_clears_ws = (
        living["sofa"]["x"] >= ws_a["zone_x1"]
        or living["sofa"]["y"] >= ws_zone_top
    )
    add(
        "PB-SOCIAL-WORKSTATION-CLEAR",
        furniture_clears_ws,
        "The TV-lounge sofa does not enter the Side A 3 × 3 m workstation clearance envelope.",
    )
    add(
        "PB-MEDIA-WALL-P2-EDGE",
        abs(media["x"] - 21.0) < 1e-9 and media["y1"] < axis0,
        "The partial media wall aligns with X=21.00 m and terminates before the central axis.",
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
    calculated_view = media["x"] - media["thickness"] - media["viewing_point_x"]
    add(
        "PB-TV-VIEWING-DISTANCE",
        abs(calculated_view - media["viewing_distance"]) < 1e-9
        and 3.5 <= calculated_view <= 4.5,
        f"The test viewing point is {calculated_view:.2f} m from the TV face.",
    )
    table = dining["table"]
    sideboard = dining["sideboard"]
    dining_clearance = table["x"] - (sideboard["x"] + sideboard["depth"])
    add(
        "PB-DINING-HINGE",
        table["length"] == 3.6
        and table["depth"] == 1.3
        and dining["chairs_per_side"] == 6
        and dining_clearance >= 1.0,
        f"The 12-seat dining table retains its 3.60 × 1.30 m envelope and {dining_clearance:.2f} m to the reverse-face sideboard.",
    )
    add(
        "PB-SIDE-B-SOLID-HALL-BAY",
        model.get("side_b_main_bay") == "solid",
        "The unassigned Side B alternative-opening graphic is removed; the bay remains solid pending site design.",
    )
    add(
        "PB-TV-MEDIA-WALL-STRUCTURE",
        False,
        "Media-wall framing and attachment at the D-043 X=21.00 m edge-truss interface require structural design.",
        open_gate=True,
    )
    add(
        "PB-TV-AV-MEP",
        False,
        "Real TV, mount, speakers, power, data, AV, ventilation and replacement access remain open.",
        open_gate=True,
    )
    add(
        "PB-TV-GLARE-PRIMARY-GLAZING",
        False,
        "Glare, blackout and solar control remain dependent on the selected site and the open H-07 primary-glazing decision.",
        open_gate=True,
    )
    return checks


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b26(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        "D-070 replaces the abstract social furniture with a coordinated TV lounge and dining hinge.",
    )
    outputs = {
        "DH-ARQ-PLN-001-R07_PB-LIVING-DINING-MEDIA.svg": plan,
        "DH-ARQ-ELE-004-R09_SIDE-B-SOLID-HALL-BAY.svg":
            b24.translate_visible_text(base.side_elevation_sheet(model, "B")),
        "DH-ARQ-ELE-INT-002-R00_PB-100IN-MEDIA-WALL.svg": media_wall_sheet(model),
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
        "source": "dreamhouse/pb_b26_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b26.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b26 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b26_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

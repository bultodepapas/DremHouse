"""Generate the D-078 Side A shared-workstation and unified-opening PB issue."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b34 as b34

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b34_delta.json")
DELTA = Path(__file__).with_name("pb_b35_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b35_pb"


def load_b35_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest()
    if digest != delta["base_delta_sha256"]:
        raise ValueError("pb_b34_delta.json changed; review the b35 integration before regenerating")

    model = deepcopy(b34.load_b34_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = deepcopy(delta[key])
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["side_a_unified_workstation"] = deepcopy(delta["side_a_unified_workstation"])
    model["side_a_facade_note"] = delta["side_a_facade_note"]

    model["workstations"] = [
        deepcopy(delta["side_a_workstation"])
        if workstation["side"] == "A"
        else workstation
        for workstation in model["workstations"]
    ]
    model["workstation_glazing"] = [
        deepcopy(delta["side_a_glazing"])
        if opening["side"] == "A"
        else opening
        for opening in model["workstation_glazing"]
    ]

    remove_markers = tuple(delta["coordination_holds_remove_contains"])
    model["coordination_holds"] = [
        item
        for item in model["coordination_holds"]
        if not item.startswith(remove_markers)
    ]
    model["coordination_holds"].extend(deepcopy(delta["coordination_holds_append"]))
    return model


def validate_b35(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = b34.validate_b34(model)
    by_rule = {item["rule_id"]: item for item in checks}

    superseded_messages = {
        "PB-WS-MIRROR": (
            "D-078 deliberately replaces strict A/B workstation mirroring: Side A is a "
            "two-person work/hall assembly while Side B retains its single workstation."
        ),
        "PB-WS-GLAZING-SYMMETRY": (
            "D-078 deliberately replaces equal A/B workstation windows; Side A now combines "
            "workstation and hall daylight in one opening while Side B remains unchanged."
        ),
        "PB-WS-FULL-BAY-WORKTOP": (
            "D-078 centres the 5.40 m Side A worktop within the wider 7.20 m shared clearance "
            "and glazing bay; D-069 full-bay geometry remains only on Side B."
        ),
        "PB-WS-CABINETRY-MIRROR": (
            "D-078 adopts three Side A cabinets for two seats and retains the D-069 two-cabinet "
            "single workstation on Side B."
        ),
        "PB-WS-KNEE-CLEARANCE": (
            "D-078 provides two separate 1.65 m clear Side A knee/chair bays between three "
            "cabinets; the predecessor one-bay formula no longer governs Side A."
        ),
        "PB-WS-A-MAIN-GLAZING-JUNCTION": (
            "D-078 removes the separate 0.20 m workstation/main-glazing junction by replacing "
            "both predecessor openings with one architectural opening."
        ),
    }
    for rule_id, message in superseded_messages.items():
        by_rule[rule_id]["status"] = "PASS"
        by_rule[rule_id]["message"] = message

    by_rule["PB-WS-STRUCTURAL-BAY"]["status"] = "OPEN"
    by_rule["PB-WS-STRUCTURAL-BAY"]["message"] = (
        "The centred 7.20 m Side A opening crosses the neutral X=12–18 m M60 test bay. "
        "Final primary frames, header, jambs, facade rails and longitudinal stability remain open."
    )

    workstation = next(item for item in model["workstations"] if item["side"] == "A")
    window = next(item for item in model["workstation_glazing"] if item["side"] == "A")
    concept = model["side_a_unified_workstation"]
    band_centre = (concept["monumental_band_x0"] + concept["monumental_band_x1"]) / 2
    window_centre = (window["x0"] + window["x1"]) / 2
    worktop_centre = workstation["worktop_x0"] + workstation["worktop_length"] / 2

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
                "message": message,
            }
        )

    add(
        "PB35-D078-COMMON-CENTRE",
        abs(band_centre - 15.75) < 1e-9
        and abs(window_centre - band_centre) < 1e-9
        and abs(worktop_centre - band_centre) < 1e-9,
        "Monumental band, 7.20 m opening and 5.40 m worktop share X=15.75 m exactly.",
    )
    add(
        "PB35-D078-WINDOW-GEOMETRY",
        window["x0"] == 12.15
        and window["x1"] == 19.35
        and window["sill"] == 0.90
        and window["height"] == 2.90
        and window["modules"] == 6,
        "Side A uses one 7.20 × 2.90 m modular opening with a +0.90 m sill and +3.80 m head.",
    )
    add(
        "PB35-D078-SYMMETRIC-RESIDUALS",
        abs(window["x0"] - concept["monumental_band_x0"] - 1.65) < 1e-9
        and abs(concept["monumental_band_x1"] - window["x1"] - 1.65) < 1e-9
        and abs(workstation["worktop_x0"] - window["x0"] - 0.90) < 1e-9
        and abs(window["x1"] - workstation["worktop_x0"] - workstation["worktop_length"] - 0.90) < 1e-9,
        "The opening leaves equal 1.65 m opaque piers; the worktop leaves equal 0.90 m glazed ends.",
    )
    cabinet_offsets = workstation["drawer_cabinet_offsets"]
    cabinet_width = workstation["drawer_cabinet_width"]
    left_clear = cabinet_offsets[1] - (cabinet_offsets[0] + cabinet_width)
    right_clear = cabinet_offsets[2] - (cabinet_offsets[1] + cabinet_width)
    add(
        "PB35-D078-TWO-SEATS-THREE-CABINETS",
        workstation["seat_count"] == 2
        and workstation["drawer_cabinet_count"] == 3
        and len(cabinet_offsets) == 3
        and abs(left_clear - 1.65) < 1e-9
        and abs(right_clear - 1.65) < 1e-9
        and len(workstation["chair_centres_x"]) == 2,
        "Three 0.70 m cabinets define two equal 1.65 m clear work positions within the 5.40 m top.",
    )
    add(
        "PB35-D078-AXIS-AND-CAR-CLEAR",
        model["envelope"]["exterior_wall"] + workstation["zone_depth"]
        < model["design_values"]["axis_y0"]
        and workstation["zone_x0"] > model["car_lift_layout"]["envelope"]["x"]
        + model["car_lift_layout"]["envelope"]["w"],
        "The shared Side A workstation remains outside the 4.00 m pedestrian axis and behind the car/lift territory.",
    )
    add(
        "PB35-D078-INTERIOR-FIRST-ENVELOPE",
        False,
        (
            "Exterior appearance is subordinate to internal light/use and a rugged economical "
            "industrial envelope. Verify panel gauge/coating, impact, safe glazing, replacement, "
            "thermal performance, seals, flashings, gutter/downpipes and whole-life cost."
        ),
        open_gate=True,
    )
    add(
        "PB35-D078-MULLION-MONITOR-COORDINATION",
        False,
        (
            "Six economical test modules do not freeze mullion positions. Coordinate real "
            "monitors, seated sightlines, operable panels, glass sizes and quotations before fabrication."
        ),
        open_gate=True,
    )
    return checks


def shared_workstation_detail_sheet(model: dict[str, Any]) -> str:
    workstation = next(item for item in model["workstations"] if item["side"] == "A")
    window = next(item for item in model["workstation_glazing"] if item["side"] == "A")
    meta = model["drawing_meta"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        base.title_block(meta["detail_code"], meta["detail_title"], meta["detail_subtitle"]),
    ]

    parts.append(base.text(75, 120, "A · WALL / SILL / WORKTOP PRINCIPLE", 14, "start", 700))
    floor_y = 610
    wall_x = 180
    parts.append(base.rect(90, 170, 90, 440, fill="#9da7a9", stroke="#26363b", stroke_width="1.5"))
    parts.append(base.rect(180, 170, 75, 440, fill="#d8ded9", stroke="#536166", stroke_width="1"))
    parts.append(base.text(135, 390, "RUGGED CORRUGATED INDUSTRIAL ENVELOPE", 7.5, weight=700, rotate=-90))
    parts.append(base.text(217, 390, "INSULATED / DRAINED WALL ZONE", 7.5, weight=700, rotate=-90))
    sill_y = floor_y - window["sill"] * 120
    head_y = floor_y - (window["sill"] + window["height"]) * 120
    worktop_y = floor_y - workstation["worktop_height"] * 120
    parts.append(base.rect(255, head_y, 34, sill_y - head_y, fill="#416771", stroke="#172126", stroke_width="2.4"))
    parts.append(base.rect(246, head_y - 10, 52, 10, fill="#29383d", stroke="#172126"))
    parts.append(base.rect(246, sill_y, 52, 14, fill="#29383d", stroke="#172126"))
    parts.append(base.rect(251, worktop_y - 8, 225, 16, fill="#c99f6b", stroke="#5b432b", stroke_width="1.4"))
    parts.append(base.rect(244, floor_y - .68 * 120 - 9, 52, 18, fill="#26363b", stroke="#172126"))
    parts.append(base.text(310, (head_y + sill_y) / 2, "REPLACEABLE MODULAR WINDOW", 8, "start", 700, "#294f58"))
    parts.append(base.text(315, worktop_y + 4, "0.90 m REPLACEABLE WORKTOP", 7.5, "start", 700, "#4f3925"))
    parts.append(base.text(315, sill_y - 8, "0.15 m INSULATED UPSTAND", 7.2, "start", 700, "#8e3825"))
    parts.append(base.text(315, floor_y - .68 * 120 + 4, "INDEPENDENT BOLTED SERVICE RAIL", 7.2, "start", 700))
    parts.append(base.text(75, 640, "EXTERIOR PERFORMANCE FIRST", 8.5, "start", 700, "#8e3825"))
    parts.append(base.text(75, 660, "No furniture load to glazing or unverified facade rails.", 7.5, "start", 400))

    parts.append(base.text(510, 120, "B · CENTRED INTERIOR ELEVATION", 14, "start", 700))
    ex, ey, scale = 510.0, 170.0, 100.0
    ew = (window["x1"] - window["x0"]) * scale
    eh = window["height"] * scale
    parts.append(base.rect(ex, ey, ew, eh, fill="#426671", stroke="#172126", stroke_width="3"))
    for module in range(1, window["modules"]):
        xx = ex + ew * module / window["modules"]
        parts.append(f'<line x1="{xx}" y1="{ey}" x2="{xx}" y2="{ey+eh}" stroke="#9bb3b8" stroke-width="1.5"/>')
    centre_x = ex + ew / 2
    parts.append(f'<line x1="{centre_x}" y1="{ey-14}" x2="{centre_x}" y2="{floor_y+10}" stroke="#b56c31" stroke-width="1.2" stroke-dasharray="7 4"/>')
    worktop_x = ex + (workstation["worktop_x0"] - window["x0"]) * scale
    worktop_w = workstation["worktop_length"] * scale
    parts.append(f'<line x1="{worktop_x}" y1="{worktop_y}" x2="{worktop_x+worktop_w}" y2="{worktop_y}" stroke="#c49a62" stroke-width="14"/>')
    rail_y = floor_y - .68 * scale
    parts.append(f'<line x1="{worktop_x}" y1="{rail_y}" x2="{worktop_x+worktop_w}" y2="{rail_y}" stroke="#26363b" stroke-width="6"/>')
    cabinet_w = workstation["drawer_cabinet_width"] * scale
    cabinet_h = workstation["drawer_cabinet_height"] * scale
    cabinet_y = worktop_y + 9
    for offset in workstation["drawer_cabinet_offsets"]:
        cabinet_x = worktop_x + offset * scale
        parts.append(base.rect(cabinet_x, cabinet_y, cabinet_w, cabinet_h, fill="#8d6745", stroke="#26363b", stroke_width="2"))
        for drawer in (1, 2):
            yy = cabinet_y + cabinet_h * drawer / 3
            parts.append(f'<line x1="{cabinet_x}" y1="{yy}" x2="{cabinet_x+cabinet_w}" y2="{yy}" stroke="#d6c1a5" stroke-width="1.2"/>')
    for chair_x in workstation["chair_centres_x"]:
        px = ex + (chair_x - window["x0"]) * scale
        parts.append(base.text(px, 560, "WORK POSITION", 7, weight=700, fill="#294b52"))
    parts.append(base.text(centre_x, 155, "COMMON CENTRE X=15.75 m", 8, weight=700, fill="#8e3825"))
    parts.append(base.text(centre_x, 325, "ONE 7.20 × 2.90 m ARCHITECTURAL OPENING · MODULAR, NOT ONE GLASS SHEET", 8.5, weight=700, fill="#eff5f5"))
    parts.append(base.text(centre_x, 585, "0.90 + 0.70 + 1.65 + 0.70 + 1.65 + 0.70 + 0.90 = 7.20 m", 8, weight=700, fill="#5b432b"))

    parts.append(base.text(510, 640, "C · CONTROL SCHEDULE", 14, "start", 700))
    schedule = [
        ("OPENING", "7.20 × 2.90 m · sill +0.90 · head +3.80 · six replaceable test modules"),
        ("WORKTOP", "5.40 × 0.90 m · top +0.75 · 0.90 m glazed residual at each end"),
        ("STORAGE", "three 0.70 × 0.75 × 0.62 m suspended steel three-drawer units"),
        ("USERS", "two equal 1.65 m clear knee/chair bays · independent power/data zones"),
        ("EXTERIOR", "direct industrial panels and trims; resistance, drainage, replacement and cost govern"),
    ]
    for index, (key, value) in enumerate(schedule):
        y = 660 + index * 30
        parts.append(base.rect(510, y, 770, 24, fill="#f1eee7", stroke="#c0bbb0", stroke_width=".8"))
        parts.append(base.text(526, y + 17, key, 7.2, "start", 700, "#8e3825"))
        parts.append(base.text(625, y + 17, value, 7.0, "start"))

    parts.append(base.rect(70, 825, 1260, 55, fill="#fff4df", stroke="#bd5c3c", stroke_width="1"))
    parts.append(base.text(88, 849, "DESIGN HOLD", 9.5, "start", 700, "#8e3825"))
    parts.append(base.text(205, 849, "Internal use and daylight govern the composition. Outside remains rugged industrial envelope, not a formal facade. Header, stability, glass safety, seals, low-eave drainage, glare, condensation, monitor/mullion alignment and quotations remain open.", 7.2, "start", 700, "#5a3a2c"))
    parts.append(base.text(88, 869, "AUTHORITY", 9.5, "start", 700, "#8e3825"))
    parts.append(base.text(205, 869, "Schematic coordination only. No profile, glass product, coating, connection, cabinet hardware or construction method is selected.", 7.2, "start", 700, "#5a3a2c"))
    parts.append("</svg>")
    return "".join(parts)


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b35(model)
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        (
            "D-078 centres one shared two-person Side A workstation within one unified "
            "work/hall opening; exterior expression remains performance-first industrial."
        ),
    )
    outputs = {
        "DH-ARQ-PLN-001-R13_PB-SIDE-A-SHARED-WORKSTATION.svg": plan,
        "DH-ARQ-ELE-003-R09_SIDE-A-PERFORMANCE-FIRST-OPENING.svg":
            b24.translate_visible_text(base.side_elevation_sheet(model, "A")),
        "DH-ARQ-DET-006-R02_SIDE-A-SHARED-WORKSTATION.svg":
            shared_workstation_detail_sheet(model),
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
        "source": "dreamhouse/pb_b35_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "base_source": "dreamhouse/pb_b34_delta.json",
        "base_source_sha256": hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b35.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if report["failed"]:
        raise ValueError(f'PB b35 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b35_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

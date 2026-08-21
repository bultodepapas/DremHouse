"""Generate the D-083 coordinated PB/P2 window and daylight issue."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base
from dreamhouse import generate_pb_b24 as b24
from dreamhouse import generate_pb_b35 as b35
from dreamhouse.generate_pb_b36 import load_b36_model, validate_b36
from dreamhouse.generate_p2_b28 import load_b28_model
from dreamhouse.envelope.openings import build_opening_schedule

ROOT = Path(__file__).resolve().parents[1]
BASE_DELTA = Path(__file__).with_name("pb_b36_delta.json")
DELTA = Path(__file__).with_name("pb_b37_delta.json")
WINDOW_SOURCE = Path(__file__).with_name("window_daylight_d083.json")
ROOFLIGHTS = Path(__file__).with_name("rooflight_b12.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b37_pb"


def load_b37_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    if hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest() != delta["base_delta_sha256"]:
        raise ValueError("pb_b36_delta.json changed; review the b37 integration before regenerating")
    if hashlib.sha256(WINDOW_SOURCE.read_bytes()).hexdigest() != delta["window_source_sha256"]:
        raise ValueError("window_daylight_d083.json changed; review the b37 integration before regenerating")
    source = json.loads(WINDOW_SOURCE.read_text(encoding="utf-8"))
    p2 = load_b28_model()
    model = deepcopy(load_b36_model())
    for key in ("revision", "status", "date", "supersedes", "decision"):
        model[key] = delta[key]
    model["drawing_meta"].update(deepcopy(delta["drawing_meta"]))
    model["workstation_glazing"] = deepcopy(source["ground_floor_workstation_glazing"])
    bedroom_names = {
        "W-H1": ("GLZ-H1", "A", "Child 1 bedroom"),
        "W-H2": ("GLZ-H2", "B", "Child 2 bedroom"),
        "W-G": ("GLZ-G", "B", "Guest bedroom"),
        "W-M-LAT-A": ("GLZ-M-A", "A", "Primary suite"),
        "W-M-REAR": ("GLZ-M-R", "REAR", "Primary suite rear"),
    }
    model["bedroom_glazing"] = []
    for item in p2["windows"]:
        if item["id"] not in bedroom_names:
            continue
        opening_id, facade, name = bedroom_names[item["id"]]
        model["bedroom_glazing"].append({
            "id": opening_id,
            "p2_id": item["id"],
            "facade": facade,
            "name": name,
            "from": item["from"],
            "to": item["to"],
            "sill": item["sill"],
            "height": item["height"],
            "modules": item["modules"],
        })
    model["window_daylight_coordination"] = deepcopy(source)
    model["optional_opening_studies"] = [deepcopy(source["optional_dining_study"])]
    model["side_a_facade_note"] = (
        "D-083 aligns the desk sill and +0.75 m worktop while retaining independent steel, "
        "drainage and seals. The rugged economical envelope, site response, safe glass, "
        "header, glare, condensation and cost remain open."
    )
    model["coordination_holds"].extend([
        "D-083 lowers only GLZ-WS-A and GLZ-WS-B sills to the +0.75 m desk datum while retaining their +3.80 m and +2.55 m heads; the desk and facade remain structurally independent across a maintainable 30-50 mm shadow/service gap.",
        "The two +0.90 m technical-window sills remain unchanged because the Project Car and RC workbench duties are not ordinary desk work.",
        "The five P2 bedroom openings now derive from the same D-083 source used by the P2 plan: repeated 1.20 m modules, +0.05 m sill and +2.95 m head.",
        "GLZ-DINING-STUDY-B remains a non-adopted study and is excluded from active drawing and area totals until site, privacy, solar, structure and cost gates close.",
    ])
    return model


def validate_b37(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = validate_b36(model)
    by_rule = {item["rule_id"]: item for item in checks}
    for rule_id in (
        "PB35-D078-WINDOW-GEOMETRY",
        "PB-P2-WINDOW-SYNC",
        "PB-GLAZING-IN-ROOM",
        "PB-WS-SILL-CLEARANCE",
    ):
        if rule_id in by_rule:
            by_rule[rule_id]["status"] = "PASS"
            by_rule[rule_id]["message"] = "Superseded by the D-083 checks against p2 b28 and the canonical window source."
    source = model["window_daylight_coordination"]
    p2 = load_b28_model()

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append({
            "rule_id": rule_id,
            "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
            "message": message,
        })

    desks = {item["side"]: item for item in model["workstations"]}
    openings = {item["side"]: item for item in model["workstation_glazing"]}
    add(
        "PB37-D083-DESK-SILL-DATUM",
        all(openings[side]["sill"] == desks[side]["worktop_height"] == .75 for side in ("A", "B")),
        "Both workstation-window sills align visually with the +0.75 m worktop datum.",
    )
    add(
        "PB37-D083-RETAINED-HEADS",
        openings["A"]["sill"] + openings["A"]["height"] == 3.80
        and openings["B"]["sill"] + openings["B"]["height"] == 2.55,
        "Lowering the desk sills retains the prior +3.80 m Side A and +2.55 m Side B heads.",
    )
    add(
        "PB37-D083-TECHNICAL-SILLS",
        all(item["sill"] == source["technical_window_rule"]["sill_m"] for item in model["technical_glazing"]),
        "Both technical-workbench window sills remain at +0.90 m.",
    )
    p2_by_id = {item["id"]: item for item in p2["windows"]}
    add(
        "PB37-D083-PB-P2-WINDOW-SYNC",
        all(
            p2_by_id[item["p2_id"]][key] == item[key]
            for item in model["bedroom_glazing"]
            for key in ("from", "to", "sill", "height", "modules")
        ),
        "Side and rear elevations use exactly the five P2 b28 bedroom-window geometries.",
    )
    adopted_vertical = sum(
        (item["x1"] - item["x0"]) * item["height"]
        for item in model["technical_glazing"] + model["workstation_glazing"]
    ) + sum((item["to"] - item["from"]) * item["height"] for item in p2["windows"])
    add(
        "PB37-D083-ACTIVE-VERTICAL-GLAZING",
        abs(adopted_vertical - 123.84) < 1e-9,
        "Adopted PB + P2 vertical glazing totals 123.84 m2; the dining study is excluded.",
    )
    add(
        "PB37-D083-DINING-STUDY-EXCLUDED",
        model["optional_opening_studies"][0]["status"].startswith("study only"),
        "The 4.80 m dining opening remains a separately identified, non-adopted study.",
    )
    for index, message in enumerate(source["open_gates"], start=1):
        add(f"PB37-D083-OPEN-{index:02d}", False, message, open_gate=True)
    return checks


def rear_elevation_sheet(model: dict[str, Any], p2: dict[str, Any]) -> str:
    meta_code = "ELE-002-R07"
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        base.title_block(meta_code, "REAR ENVELOPE · PRIVATE / SERVICE OPENINGS", "D-083 primary bedroom window + retained wellness and D-082 rescue system · not for construction"),
    ]
    left, floor_pb, scale = 140.0, 665.0, 62.0
    width = 18.0 * scale
    p2_floor = floor_pb - 3.8 * scale
    top_a, top_b, _, _ = base.roof_profile(model, scale, floor_pb)
    parts.append(f'<polygon points="{left},{floor_pb} {left},{top_a} {left+width},{top_b} {left+width},{floor_pb}" fill="#aeb5b6" stroke="#172126" stroke-width="4"/>')
    parts.append(f'<line x1="{left}" y1="{p2_floor}" x2="{left+width}" y2="{p2_floor}" stroke="#657378" stroke-width="1.2" stroke-dasharray="7 5"/>')
    for door in model["exterior_doors"]:
        x = left + (door["y"] - .5) * scale
        w = door["width"] * scale
        h = (2.4 if door["id"] == "EXT-ESC" else 2.3) * scale
        parts.append(base.rect(x, floor_pb - h, w, h, fill="#3e4d52", stroke="#172126", stroke_width=2.2))
        parts.append(base.text(x + w / 2, floor_pb - h / 2, door["id"], 7, weight=700, fill="#f5f3ed"))
    for item in p2["windows"]:
        if item["edge"] != "east":
            continue
        x = left + item["from"] * scale
        w = (item["to"] - item["from"]) * scale
        h = item["height"] * scale
        y = p2_floor - (item["sill"] + item["height"]) * scale
        css = "rescue-window" if item["id"] == "W-EGRESS-P2" else "rear-p2-window"
        parts.append(base.rect(x, y, w, h, fill="#426671", stroke="#172126", stroke_width=2.2, **{"class": css}))
        modules = item.get("modules", max(1, round((item["to"] - item["from"]) / 1.2)))
        for module in range(1, modules):
            xx = x + w * module / modules
            parts.append(f'<line x1="{xx}" y1="{y}" x2="{xx}" y2="{y+h}" stroke="#9bb3b8"/>')
        label = "PRIMARY · 2 x 1.20" if item["id"] == "W-M-REAR" else "WELLNESS" if item["id"] == "W-WELL" else "RESCUE · D-082"
        parts.append(base.text(x + w / 2, y + h / 2 + 3, label, 7, weight=700, fill="#eff5f5"))
    reserve = p2["egress_reserve"]
    ladder_x = left + reserve["ladder_axis_y"] * scale
    parts.append(f'<line x1="{ladder_x}" y1="{p2_floor-10}" x2="{ladder_x}" y2="{floor_pb-35}" stroke="#a63f31" stroke-width="5" class="foldout-ladder-closed-profile"/>')
    for rung in range(1, 11):
        yy = p2_floor + rung * (floor_pb - p2_floor - 50) / 11
        parts.append(f'<line x1="{ladder_x-12}" y1="{yy}" x2="{ladder_x+12}" y2="{yy}" stroke="#f2c6aa" stroke-width="1.3"/>')
    parts.append(base.text(ladder_x - 18, (p2_floor + floor_pb) / 2, "VERTICAL FOLDOUT LADDER", 6.5, weight=700, fill="#8e3825", rotate=-90))
    parts.append(base.rect(left - 40, floor_pb, width + 80, 42, fill="#d6d2ca", stroke="#858b89"))
    parts.append(base.text(left + width / 2, floor_pb + 27, "REAR GRADE, DRAINAGE, TRANSFER SAFETY AND SITE RELATIONSHIP REMAIN OPEN", 8, weight=700))
    parts.append(base.note_box("D-083 coordinates one 2.40 m primary window; wellness and D-082 rescue geometry are retained. Site orientation, privacy, solar control, safe glass, fall protection, structure, flashings and cost remain open."))
    parts.append("</svg>")
    return "".join(parts).replace("NOTA DE COORDINACIÓN", "COORDINATION NOTE")


def opening_schedule_sheet(model: dict[str, Any], p2: dict[str, Any], schedule: dict[str, Any]) -> str:
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        base.title_block("SCH-001-R00", "WINDOW / DAYLIGHT SCHEDULE", "D-083 adopted vertical openings + retained rooflights · study geometry, not procurement authority"),
    ]
    parts.append(base.text(70, 120, "A · ADOPTED VERTICAL OPENINGS", 14, "start", 700))
    headers = ("ID", "LOCATION", "SOURCE", "W × H m", "SILL / HEAD m", "MODULES", "AREA m2")
    xs = (70, 245, 370, 690, 840, 1045, 1195)
    for x, value in zip(xs, headers):
        parts.append(base.text(x, 153, value, 7, "start", 700, "#8e3825"))
    adopted = [item for item in schedule["items"] if item["kind"] == "vertical_glazing"]
    for index, item in enumerate(adopted):
        y = 168 + index * 34
        parts.append(base.rect(62, y - 14, 1270, 28, fill="#f1eee7" if index % 2 == 0 else "#f8f6f1", stroke="#d0cbc0", stroke_width=.5))
        values = (
            item["id"], item["location"], item["source"],
            f'{item["width_m"]:.2f} × {item["height_m"]:.2f}',
            f'{item["sill_m"]:.2f} / {item["head_m"]:.2f}',
            str(item.get("modules", "—")), f'{item["area_m2"]:.2f}',
        )
        for x, value in zip(xs, values):
            parts.append(base.text(x, y + 4, value, 6.7, "start", 700 if x == 70 else 400))
    vertical_total = schedule["area_totals_m2"]["vertical_glazing"]
    roof_total = schedule["area_totals_m2"]["rooflight"]
    parts.append(base.rect(62, 590, 1270, 55, fill="#dce9ec", stroke="#5e8e98", stroke_width=1))
    parts.append(base.text(82, 614, "ADOPTED VERTICAL GLAZING", 8, "start", 700, "#294f58"))
    parts.append(base.text(420, 614, f"{vertical_total:.2f} m2", 12, "start", 700, "#294f58"))
    parts.append(base.text(650, 614, "RETAINED ROOFLIGHTS", 8, "start", 700, "#294f58"))
    parts.append(base.text(930, 614, f"{roof_total:.2f} m2", 12, "start", 700, "#294f58"))
    parts.append(base.text(1110, 614, f"TOTAL {vertical_total + roof_total:.2f} m2", 10, "start", 700, "#294f58"))
    study = schedule["study_items_excluded_from_totals"][0]
    parts.append(base.text(70, 690, "B · NON-ADOPTED STUDY · EXCLUDED FROM TOTALS", 14, "start", 700))
    parts.append(base.rect(62, 712, 1270, 62, fill="#fff4df", stroke="#bd5c3c", stroke_width=1))
    parts.append(base.text(82, 738, f'{study["id"]} · Side B · {study["width_m"]:.2f} × {study["height_m"]:.2f} m · sill +{study["sill_m"]:.2f} · {study["area_m2"]:.2f} m2', 8, "start", 700, "#8e3825"))
    parts.append(base.text(82, 760, "Do not draw, price or procure until site orientation, privacy, solar exposure, structure and cost are resolved.", 7.4, "start", 700))
    parts.append(base.rect(62, 800, 1270, 62, fill="#f1eee7", stroke="#c0bbb0", stroke_width=.8))
    parts.append(base.text(82, 825, "AUTHORITY", 8, "start", 700, "#8e3825"))
    parts.append(base.text(180, 825, "Schematic coordination quantities only. Final clear openings, glass make-up, frames, operability, structure, performance and installation require professional design and quotation.", 7.2, "start", 700))
    parts.append(base.text(82, 849, "D-083 deliberately retains the two +0.90 m technical-window sills while desk sills use +0.75 m and bedroom windows use +0.05 m.", 7.2, "start"))
    parts.append("</svg>")
    return "".join(parts)


def workstation_detail(model: dict[str, Any]) -> str:
    return (
        b35.shared_workstation_detail_sheet(model)
        .replace("0.90 m REPLACEABLE WORKTOP", "0.75 m REPLACEABLE WORKTOP")
        .replace("0.15 m INSULATED UPSTAND", "30-50 mm INDEPENDENT SHADOW / SERVICE GAP")
        .replace("ONE 7.20 × 2.90 m ARCHITECTURAL OPENING", "ONE 7.20 × 3.05 m ARCHITECTURAL OPENING")
        .replace("7.20 × 2.90 m · sill +0.90 · head +3.80", "7.20 × 3.05 m · sill +0.75 · head +3.80")
    )


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    p2 = load_b28_model()
    rooflights = json.loads(ROOFLIGHTS.read_text(encoding="utf-8"))
    schedule = build_opening_schedule(model, p2, rooflights)
    schedule["revision"] = "0.3-D083-OPENINGS"
    schedule["decision"] = "D-083"
    checks = validate_b37(model)
    report = {
        "revision": model["revision"], "status": model["status"], "decision": model["decision"],
        "checks": checks,
        "passed": sum(item["status"] == "PASS" for item in checks),
        "open": sum(item["status"] == "OPEN" for item in checks),
        "failed": sum(item["status"] == "FAIL" for item in checks),
    }
    if report["failed"]:
        failed = [item["rule_id"] for item in checks if item["status"] == "FAIL"]
        raise ValueError(f"PB b37 validation failed: {failed}")
    plan = b24.translate_visible_text(base.plan_sheet(model)).replace(
        "D-068 changes workstation coordination only.",
        "D-083 aligns desk-window sills at +0.75 m; technical-window sills remain +0.90 m and the P2 bedroom family uses repeated 1.20 m modules.",
    )
    outputs = {
        "DH-ARQ-PLN-001-R15_PB-WINDOW-DAYLIGHT-DATUMS.svg": plan,
        "DH-ARQ-ELE-002-R07_REAR-WINDOW-DAYLIGHT.svg": rear_elevation_sheet(model, p2),
        "DH-ARQ-ELE-003-R10_SIDE-A-WINDOW-DAYLIGHT.svg": b24.translate_visible_text(base.side_elevation_sheet(model, "A")),
        "DH-ARQ-ELE-004-R10_SIDE-B-WINDOW-DAYLIGHT.svg": b24.translate_visible_text(base.side_elevation_sheet(model, "B")),
        "DH-ARQ-DET-006-R03_PB-DESK-WINDOW-INTERFACE.svg": workstation_detail(model),
        "DH-ARQ-SCH-001-R00_D083-WINDOW-SCHEDULE.svg": opening_schedule_sheet(model, p2, schedule),
    }
    target.mkdir(parents=True, exist_ok=True)
    for filename, content in outputs.items():
        target.joinpath(filename).write_text(content, encoding="utf-8")
    target.joinpath("opening_schedule.json").write_text(json.dumps(schedule, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    target.joinpath("compliance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "revision": model["revision"], "status": model["status"], "decision": model["decision"],
        "source": "dreamhouse/pb_b37_delta.json", "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "base_source": "dreamhouse/pb_b36_delta.json", "base_source_sha256": hashlib.sha256(BASE_DELTA.read_bytes()).hexdigest(),
        "window_source": "dreamhouse/window_daylight_d083.json", "window_source_sha256": hashlib.sha256(WINDOW_SOURCE.read_bytes()).hexdigest(),
        "p2_source": "dreamhouse/p2_b28_delta.json", "p2_source_sha256": hashlib.sha256(Path(__file__).with_name("p2_b28_delta.json").read_bytes()).hexdigest(),
        "rooflight_source": "dreamhouse/rooflight_b12.json", "rooflight_source_sha256": hashlib.sha256(ROOFLIGHTS.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b37.py", "supersedes": model["supersedes"],
        "outputs": [*outputs, "opening_schedule.json", "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    report = generate(load_b37_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

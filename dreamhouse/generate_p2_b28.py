"""Generate the D-083 upper-floor bedroom-window and daylight issue."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_p2_b09 as base
from dreamhouse.generate_p2_b27 import load_b27_model

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("p2_b27_delta.json")
DELTA = Path(__file__).with_name("p2_b28_delta.json")
WINDOW_SOURCE = Path(__file__).with_name("window_daylight_d083.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b28_p2"


def load_b28_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    if hashlib.sha256(BASE.read_bytes()).hexdigest() != delta["base_model_sha256"]:
        raise ValueError("p2_b27_delta.json changed; review the b28 delta before regenerating")
    source = json.loads(WINDOW_SOURCE.read_text(encoding="utf-8"))
    model = deepcopy(load_b27_model())
    for key in ("revision", "drawing_revision", "status", "date", "supersedes"):
        model[key] = delta[key]
    replacements = {item["id"]: deepcopy(item) for item in source["upper_floor_bedroom_windows"]}
    model["windows"] = [replacements.get(item["id"], item) for item in model["windows"]]
    model["decision"] = delta["decision"]
    model["window_daylight_coordination"] = deepcopy(source)
    model["design_basis"].append(
        "D-083 1.20 m modular bedroom-window family with +0.05 m visual sill and +2.95 m head"
    )
    model["design_notes"].extend(
        [
            "The five bedroom openings use repeated 1.20 m modules and read as near-floor-to-ceiling glazing; they are not single oversized glass sheets.",
            "Safety glazing, fall protection, operability, solar control, privacy, curtains, condensation and exact site response remain professional design gates.",
            "D-083 does not change W-WELL or the D-082 rescue window and vertical foldout ladder.",
        ]
    )
    return model


def validate_b28(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = base.validate_model(model)
    source = model["window_daylight_coordination"]
    adopted = {item["id"]: item for item in model["windows"]}
    predecessors = {item["id"]: item for item in load_b27_model()["windows"]}

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append({
            "rule_id": rule_id,
            "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
            "message": message,
        })

    expected = {item["id"]: item for item in source["upper_floor_bedroom_windows"]}
    add(
        "P2-B28-D083-BEDROOM-WINDOWS",
        all(adopted.get(key) == value for key, value in expected.items()),
        "All five bedroom openings match the D-083 canonical source exactly.",
    )
    add(
        "P2-B28-D083-MODULE",
        all(
            abs((item["to"] - item["from"]) - item["modules"] * source["module_width_m"]) < 1e-9
            for item in expected.values()
        ),
        "Bedroom-window widths resolve exactly into two or three 1.20 m modules.",
    )
    add(
        "P2-B28-D083-VERTICAL-DATUM",
        all(item["sill"] == .05 and item["height"] == 2.90 for item in expected.values()),
        "Bedroom windows use a +0.05 m sill and +2.95 m head as a near-floor-to-ceiling visual datum.",
    )
    bedroom_area = sum((item["to"] - item["from"]) * item["height"] for item in expected.values())
    add(
        "P2-B28-D083-BEDROOM-GLASS-AREA",
        abs(bedroom_area - 48.72) < 1e-9,
        "The five adopted bedroom openings total 48.72 m2 of schematic vertical glazing.",
    )
    add(
        "P2-B28-D083-RETAINED-OPENINGS",
        all(adopted[key] == predecessors[key] for key in ("W-WELL", "W-EGRESS-P2")),
        "Wellness and D-082 rescue-window geometries remain unchanged.",
    )
    for index, message in enumerate(source["open_gates"], start=1):
        add(f"P2-B28-D083-OPEN-{index:02d}", False, message, open_gate=True)
    return checks


def bedroom_window_detail_sheet(model: dict[str, Any]) -> str:
    source = model["window_daylight_coordination"]
    windows = {item["id"]: item for item in source["upper_floor_bedroom_windows"]}
    parts = base._svg_start(
        "Dream House P2 bedroom window family",
        "D-083 modular near-floor-to-ceiling bedroom-window coordination. Not for construction.",
        {"drawing": "DH-ARQ-DET-008-R00", "revision": model["revision"], "construction_authority": False},
    )
    base._header(parts, model, "DH-ARQ-DET-008-R00", "P2 BEDROOM WINDOW FAMILY", "D-083 · repeated 1.20 m modules · near-floor-to-ceiling visual datum")
    base._panel_title(parts, 72, 166, "01", "STANDARD THREE-MODULE BEDROOM OPENING", width=690)
    floor_y, scale, x = 615.0, 132.0, 145.0
    standard = windows["W-H1"]
    head_y = floor_y - (standard["sill"] + standard["height"]) * scale
    sill_y = floor_y - standard["sill"] * scale
    width = (standard["to"] - standard["from"]) * scale
    parts.append(base._rect(x, head_y, width, sill_y - head_y, fill="#426671", stroke=base.INK, stroke_width=3))
    for module in range(1, standard["modules"]):
        xx = x + width * module / standard["modules"]
        parts.append(base._line(xx, head_y, xx, sill_y, stroke="#a9c0c5", stroke_width=1.4))
    guard_y = floor_y - 1.05 * scale
    parts.append(base._line(x, guard_y, x + width, guard_y, stroke="#e7d19a", stroke_width=2, stroke_dasharray="8 4"))
    parts.append(base._line(x - 35, floor_y, x + width + 35, floor_y, stroke=base.INK, stroke_width=2))
    parts.append(base._text(x + width / 2, head_y - 18, "3.60 x 2.90 m · 3 x 1.20 m", 12, anchor="middle", weight=700))
    parts.append(base._text(x + width / 2, (head_y + sill_y) / 2, "FIXED + OPERABLE PANEL MIX\nPENDING SITE / VENTILATION", 10, anchor="middle", weight=700, fill="#eff5f5"))
    parts.append(base._text(x - 22, sill_y + 4, "+0.05", 8, anchor="end", weight=700, fill=base.RED))
    parts.append(base._text(x - 22, head_y + 4, "+2.95", 8, anchor="end", weight=700, fill=base.RED))
    parts.append(base._text(x + width / 2, guard_y - 8, "FALL-PROTECTION / RESTRICTOR DESIGN GATE", 7.5, anchor="middle", weight=700, fill="#f7e8b7"))

    base._panel_title(parts, 785, 166, "02", "PRIMARY SUITE CORNER FAMILY", width=780)
    schedule = [
        ("SIDE A", "W-M-LAT-A", "3.60 x 2.90 m · 3 modules", 815.0),
        ("REAR", "W-M-REAR", "2.40 x 2.90 m · 2 modules", 1190.0),
    ]
    for tag, window_id, label, xx0 in schedule:
        yy = 235.0
        item = windows[window_id]
        panel_w = (item["to"] - item["from"]) * 90
        panel_h = item["height"] * 90
        parts.append(base._text(xx0, yy - 28, tag, 8, weight=700, fill=base.TEAL))
        parts.append(base._text(xx0, yy - 10, label, 8, weight=700))
        parts.append(base._rect(xx0, yy, panel_w, panel_h, fill="#426671", stroke=base.INK, stroke_width=2.5))
        for module in range(1, item["modules"]):
            xx = xx0 + panel_w * module / item["modules"]
            parts.append(base._line(xx, yy, xx, yy + panel_h, stroke="#a9c0c5", stroke_width=1.2))
        parts.append(base._text(xx0 + panel_w / 2, yy + panel_h + 23, "sill +0.05 · head +2.95", 7.5, anchor="middle", fill=base.MUTED))

    base._panel_title(parts, 72, 700, "03", "REPEATED CONTROL SCHEDULE", width=690)
    rows = [
        ("W-H1 / W-H2 / W-G", "3.60 x 2.90 m", "3 x 1.20 m"),
        ("W-M-LAT-A", "3.60 x 2.90 m", "3 x 1.20 m"),
        ("W-M-REAR", "2.40 x 2.90 m", "2 x 1.20 m"),
        ("ALL FIVE", "sill +0.05 m", "head +2.95 m"),
    ]
    for index, row in enumerate(rows):
        yy = 742 + index * 42
        parts.append(base._rect(72, yy, 690, 31, fill="#ece8df", stroke="#c3ccce", stroke_width=.8))
        parts.append(base._text(88, yy + 21, row[0], 7.5, weight=700, fill=base.TEAL))
        parts.append(base._text(330, yy + 21, row[1], 7.5, weight=700))
        parts.append(base._text(555, yy + 21, row[2], 7.5, weight=700))

    base._panel_title(parts, 785, 700, "04", "OPEN PROFESSIONAL GATES", width=780)
    visible = source["open_gates"][:7]
    for index, note in enumerate(visible):
        yy = 740 + index * 39
        parts.append(base._rect(785, yy, 780, 30, fill="#fff4df" if index < 3 else "#ece8df", stroke="#d2c5ae", stroke_width=.8, rx=3))
        parts.append(base._text(800, yy + 20, f"{index + 1:02d}", 7, weight=700, fill=base.RED))
        parts.append(base._text(832, yy + 20, note, 7.1, weight=700 if index < 3 else 400))
    base._footer(parts, model, hashlib.sha256(WINDOW_SOURCE.read_bytes()).hexdigest(), "DH-ARQ-DET-008-R00")
    parts.append("</svg>")
    return "".join(parts)


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    base.generate(model, target, source_path=DELTA, generator_name="dreamhouse/generate_p2_b28.py")
    checks = validate_b28(model)
    if any(item["status"] == "FAIL" for item in checks):
        raise ValueError("P2 b28 D-083 validation failed")
    detail_name = "DH-ARQ-DET-008-R00_P2-BEDROOM-WINDOW-FAMILY.svg"
    target.joinpath(detail_name).write_text(bedroom_window_detail_sheet(model), encoding="utf-8")
    report = {
        "revision": model["revision"],
        "status": model["status"],
        "decision": model["decision"],
        "checks": checks,
        "passed": sum(item["status"] == "PASS" for item in checks),
        "open": sum(item["status"] == "OPEN" for item in checks),
        "failed": sum(item["status"] == "FAIL" for item in checks),
    }
    plan_name, _, _ = base.output_names(model)
    target.joinpath(plan_name).write_text(base.build_plan(model, report), encoding="utf-8")
    target.joinpath("compliance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.update({
        "decision": "D-083",
        "window_source": "dreamhouse/window_daylight_d083.json",
        "window_source_sha256": hashlib.sha256(WINDOW_SOURCE.read_bytes()).hexdigest(),
    })
    manifest["outputs"].insert(-2, detail_name)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    report = generate(load_b28_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

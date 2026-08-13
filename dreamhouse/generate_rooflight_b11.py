"""Generate the double-height-centred rooflight revision."""

from __future__ import annotations

import hashlib
import html
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).with_name("rooflight_b11.json")
PB = Path(__file__).with_name("pb_b05.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b11_rooflights"

PLAN_NAME = "DH-ARQ-PLN-CUB-001-R10_CENTRAL-ROOFLIGHTS.svg"
SECTION_NAME = "DH-ARQ-SEC-CUB-003-R10_CENTRAL-DAYLIGHT.svg"


def text(x, y, value, size=10, weight=400, anchor="start", fill="#233238"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial" font-size="{size}" '
        f'font-weight="{weight}" text-anchor="{anchor}" fill="{fill}">'
        f"{html.escape(str(value))}</text>"
    )


def header(title, code, subtitle):
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1684" height="1191" viewBox="0 0 1684 1191">',
        '<rect width="1684" height="1191" fill="#f6f3ec"/>',
        '<rect width="1684" height="112" fill="#172a33"/>',
        '<rect y="112" width="1684" height="6" fill="#168aa3"/>',
        text(52, 47, "DREAM HOUSE · BOYACA, COLOMBIA", 9, 700, fill="#9fc4cc"),
        text(52, 81, title, 22, 700, fill="#ffffff"),
        text(1615, 48, code, 15, 700, "end", "#ffffff"),
        text(1615, 77, subtitle, 8.5, 400, "end", "#c9d8dc"),
    ]


def center(model):
    zone = model["double_height"]
    return ((zone["x0"] + zone["x1"]) / 2, (zone["y0"] + zone["y1"]) / 2)


def group_center(model):
    rooflights = model["rooflights"]
    min_x = min(item["x"] for item in rooflights)
    max_x = max(item["x"] + item["length"] for item in rooflights)
    min_y = min(item["y"] for item in rooflights)
    max_y = max(item["y"] + item["width"] for item in rooflights)
    return ((min_x + max_x) / 2, (min_y + max_y) / 2)


def validate(model, pb):
    rooflights = model["rooflights"]
    zone = model["double_height"]
    tolerance = model["center_tolerance_m"]
    target = center(model)
    actual = group_center(model)
    overlap_x = min(
        rooflights[0]["x"] + rooflights[0]["length"],
        rooflights[1]["x"] + rooflights[1]["length"],
    ) - max(rooflights[0]["x"], rooflights[1]["x"])
    overlap_y = min(
        rooflights[0]["y"] + rooflights[0]["width"],
        rooflights[1]["y"] + rooflights[1]["width"],
    ) - max(rooflights[0]["y"], rooflights[1]["y"])
    tests = [
        ("RL-TWO", len(rooflights) == 2, "Two equal central rooflights"),
        (
            "RL-IN-DOUBLE-HEIGHT",
            all(
                item["x"] >= zone["x0"]
                and item["x"] + item["length"] <= zone["x1"]
                and item["y"] >= zone["y0"]
                and item["y"] + item["width"] <= zone["y1"]
                for item in rooflights
            ),
            "Both rooflights lie fully inside the 21 x 18 m double-height zone",
        ),
        (
            "RL-GROUP-CENTRE-X",
            abs(actual[0] - target[0]) <= tolerance,
            f"Group centre X={actual[0]:.2f} m versus double-height centre X={target[0]:.2f} m",
        ),
        (
            "RL-GROUP-CENTRE-Y",
            abs(actual[1] - target[1]) <= tolerance,
            f"Group centre Y={actual[1]:.2f} m versus double-height centre Y={target[1]:.2f} m",
        ),
        ("RL-NO-OVERLAP", not (overlap_x > 0 and overlap_y > 0), "Central rooflights remain separated"),
        ("RL-AREA", math.isclose(sum(item["area"] for item in rooflights), 23.04, abs_tol=0.01), "Total rooflight area remains 23.04 m2"),
        ("RL-ROOF-DIRECTION", model["roof"]["low_side"] == pb["roof"]["low_side"], "Roof direction matches pb_b05.json"),
    ]
    checks = [
        {"rule_id": rule_id, "status": "PASS" if passed else "FAIL", "message": message}
        for rule_id, passed, message in tests
    ]
    low_a = pb["roof"]["low_side"] == "A"
    drainage = []
    for item in sorted(rooflights, key=lambda value: value["y"]):
        upstream = 18 - (item["y"] + item["width"]) if low_a else item["y"]
        drainage.append(f"{item['id']} {upstream:.2f} m upstream / approx. {upstream * item['length']:.1f} m2 catchment")
    checks.extend(
        [
            {
                "rule_id": "RL-DRAINAGE",
                "status": "OPEN",
                "message": "Central geometry is fixed but hydraulic loading remains different: " + "; ".join(drainage),
            },
            {"rule_id": "RL-STRUCTURE", "status": "OPEN", "message": "Trimmers, purlins and roof-diaphragm interruption remain undesigned"},
            {"rule_id": "RL-HYGRO", "status": "OPEN", "message": "Glass build-up, solar control and condensation remain subject to calculation"},
        ]
    )
    return checks


def plan(model, report):
    drawing_revision = model.get("drawing_revision", "R10")
    parts = header(
        "CENTRAL ROOFLIGHTS · DOUBLE-HEIGHT HALL",
        f"DH-ARQ-PLN-CUB-001-{drawing_revision}",
        "group centre = X10.50 / Y9.00 m · tolerance ±0.10 m",
    )
    x0, y0, scale = 95.0, 185.0, 36.0
    parts.extend(
        [
            f'<rect x="{x0}" y="{y0}" width="{36 * scale}" height="{18 * scale}" fill="#c9ced0" stroke="#172a33" stroke-width="4"/>',
            f'<rect x="{x0}" y="{y0}" width="{21 * scale}" height="{18 * scale}" fill="#dce7e4" stroke="#168aa3" stroke-width="3"/>',
            f'<rect x="{x0 + 21 * scale}" y="{y0}" width="{15 * scale}" height="{18 * scale}" fill="#d9d4ce" stroke="#76558f" stroke-width="2" opacity="0.75"/>',
        ]
    )
    for x in range(0, 37, 6):
        parts.append(f'<line x1="{x0 + x * scale}" y1="{y0}" x2="{x0 + x * scale}" y2="{y0 + 18 * scale}" stroke="#7c8a8d" stroke-dasharray="7 5"/>')
    for y in range(0, 19, 3):
        parts.append(f'<line x1="{x0}" y1="{y0 + y * scale}" x2="{x0 + 36 * scale}" y2="{y0 + y * scale}" stroke="#9eaaac" stroke-width=".8"/>')
    for item in model["rooflights"]:
        x = x0 + item["x"] * scale
        y = y0 + item["y"] * scale
        width = item["length"] * scale
        height = item["width"] * scale
        parts.extend(
            [
                f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="5" fill="#5f9eae" stroke="#173c46" stroke-width="3" class="central-rooflight"/>',
                f'<path d="M{x + 7} {y + height - 9} L{x + width - 7} {y + 9}" stroke="#d7eef2" stroke-width="3"/>',
                text(x + width / 2, y + height / 2 - 3, item["id"], 8, 700, "middle"),
                text(x + width / 2, y + height / 2 + 15, "4.80 x 2.40 m", 7, 700, "middle"),
            ]
        )
    target = center(model)
    actual = group_center(model)
    cx, cy = x0 + target[0] * scale, y0 + target[1] * scale
    parts.extend(
        [
            f'<line x1="{cx - 20}" y1="{cy}" x2="{cx + 20}" y2="{cy}" stroke="#a63f31" stroke-width="2"/>',
            f'<line x1="{cx}" y1="{cy - 20}" x2="{cx}" y2="{cy + 20}" stroke="#a63f31" stroke-width="2"/>',
            f'<circle cx="{cx}" cy="{cy}" r="7" fill="#f6f3ec" stroke="#a63f31" stroke-width="2" class="double-height-centre"/>',
            text(cx, cy - 28, "EXACT DOUBLE-HEIGHT CENTRE", 7.5, 700, "middle", "#a63f31"),
            text(x0 + 10.5 * scale, y0 + 18 * scale + 31, "DOUBLE HEIGHT · X=0.00 to 21.00 m", 9, 700, "middle", "#168aa3"),
            text(x0 + 28.5 * scale, y0 + 18 * scale + 31, "P2 / REAR CORE", 9, 700, "middle", "#76558f"),
            text(930, 906, f"GROUP CENTRE: X={actual[0]:.2f} / Y={actual[1]:.2f} m", 13, 700, fill="#2e7252"),
            text(930, 938, f"OFFSET: {abs(actual[0] - target[0]):.2f} m X / {abs(actual[1] - target[1]):.2f} m Y", 10, 700, fill="#2e7252"),
            text(930, 978, f"RESULT: {report['passed']} PASS · {report['failed']} FAIL · {report['open']} OPEN", 11, 700),
            text(930, 1018, "The prior pair was centred in Y but 6.90 m forward of the hall centre in X.", 8.5),
            text(930, 1042, "The new pair is symmetric as a group, not one continuous strip.", 8.5),
            text(930, 1066, "NOT FOR CONSTRUCTION · structural and drainage coordination remain open.", 8.5, 700, fill="#a63f31"),
        ]
    )
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def section(model):
    drawing_revision = model.get("drawing_revision", "R10")
    parts = header(
        "CENTRAL DAYLIGHT · TRANSVERSE SECTION",
        f"DH-ARQ-SEC-CUB-003-{drawing_revision}",
        "two separated events centred around Y=9.00 m",
    )
    x0, base, scale = 180.0, 850.0, 62.0
    roof = model["roof"]
    a_low = roof["low_side"] == "A"
    elevation_a, elevation_b = (
        (roof["low_eave"], roof["high_eave"])
        if a_low
        else (roof["high_eave"], roof["low_eave"])
    )
    y_a, y_b = base - elevation_a * scale, base - elevation_b * scale

    def roof_y(y):
        return y_a + (y_b - y_a) * y / 18.0

    parts.extend(
        [
            f'<line x1="{x0}" y1="{base}" x2="{x0 + 18 * scale}" y2="{base}" stroke="#172a33" stroke-width="4"/>',
            f'<line x1="{x0}" y1="{y_a}" x2="{x0 + 18 * scale}" y2="{y_b}" stroke="#172a33" stroke-width="7"/>',
            f'<line x1="{x0}" y1="{base}" x2="{x0}" y2="{y_a}" stroke="#172a33" stroke-width="4"/>',
            f'<line x1="{x0 + 18 * scale}" y1="{base}" x2="{x0 + 18 * scale}" y2="{y_b}" stroke="#172a33" stroke-width="4"/>',
        ]
    )
    for item in model["rooflights"]:
        start, end = item["y"], item["y"] + item["width"]
        parts.extend(
            [
                f'<line x1="{x0 + start * scale}" y1="{roof_y(start)}" x2="{x0 + end * scale}" y2="{roof_y(end)}" stroke="#5f9eae" stroke-width="14" class="central-rooflight-section"/>',
                f'<polygon points="{x0 + (start + .15) * scale},{roof_y(start) + 14} {x0 + (end - .15) * scale},{roof_y(end) + 14} {x0 + (end - .45) * scale},{base - 30} {x0 + (start + .45) * scale},{base - 30}" fill="#cce8ee" opacity=".34"/>',
            ]
        )
    centre_x = x0 + 9 * scale
    parts.extend(
        [
            f'<line x1="{centre_x}" y1="{roof_y(9) - 45}" x2="{centre_x}" y2="{base}" stroke="#a63f31" stroke-width="2" stroke-dasharray="8 5"/>',
            text(centre_x, roof_y(9) - 58, "Y=9.00 m · DOUBLE-HEIGHT CENTRE", 8, 700, "middle", "#a63f31"),
            text(180, 915, "LATERAL A", 10, 700),
            text(1296, 915, "LATERAL B", 10, 700, "end"),
            text(1360, 270, "DESIGN INTENT", 11, 700),
            text(1360, 305, "Two equal separated rooflights", 8.5),
            text(1360, 332, "Centred as a group over the great void", 8.5),
            text(1360, 359, "Diffused light; fixed glazing by default", 8.5),
            text(1360, 404, "OPEN", 10, 700, fill="#a63f31"),
            text(1360, 433, "purlin trimmers / diaphragm", 8.5),
            text(1360, 460, "crickets / overflow / curb", 8.5),
            text(1360, 487, "glass / solar / condensation", 8.5),
            text(1360, 535, "NOT FOR CONSTRUCTION", 9, 700, fill="#a63f31"),
        ]
    )
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def generate(
    model=None,
    out_dir=OUT,
    *,
    source_path=DATA,
    plan_name=PLAN_NAME,
    section_name=SECTION_NAME,
):
    model = json.loads(source_path.read_text(encoding="utf-8")) if model is None else model
    pb = json.loads(PB.read_text(encoding="utf-8"))
    checks = validate(model, pb)
    report = {
        "revision": model["revision"],
        "passed": sum(item["status"] == "PASS" for item in checks),
        "open": sum(item["status"] == "OPEN" for item in checks),
        "failed": sum(item["status"] == "FAIL" for item in checks),
        "checks": checks,
    }
    if report["failed"]:
        raise ValueError("Rooflight model failed closed: " + "; ".join(item["message"] for item in checks if item["status"] == "FAIL"))
    outputs = {plan_name: plan(model, report), section_name: section(model)}
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        out_dir.joinpath(name).write_text(content, encoding="utf-8")
    out_dir.joinpath("compliance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "revision": model["revision"],
        "status": model["status"],
        "source": source_path.relative_to(ROOT).as_posix(),
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_rooflight_b11.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    out_dir.joinpath("manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    report = generate()
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

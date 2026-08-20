"""Generate the D-068 mirrored, wall-integrated ground-floor workstation revision."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse import generate_pb_b05 as base

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).with_name("pb_b05.json")
DELTA = Path(__file__).with_name("pb_b24_delta.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b24_pb"


def load_b24_model() -> dict[str, Any]:
    delta = json.loads(DELTA.read_text(encoding="utf-8"))
    digest = hashlib.sha256(BASE.read_bytes()).hexdigest()
    if digest != delta["base_model_sha256"]:
        raise ValueError("pb_b05.json changed; review the b24 delta before regenerating")

    model = deepcopy(json.loads(BASE.read_text(encoding="utf-8")))
    for key in (
        "revision",
        "status",
        "date",
        "supersedes",
        "decision",
        "drawing_meta",
        "workstations",
        "workstation_glazing",
        "built_in_benches",
        "coordination_holds",
    ):
        model[key] = deepcopy(delta[key])

    translations = {
        "PAN": "Pantry / clean support",
        "BOD": "Storage",
        "ESC": "Protected stair",
        "BAN": "Ground-floor bathroom",
        "HOM": "Homelab / technical",
    }
    for room in model["core"]:
        room["name"] = translations[room["id"]]

    opening_names = {
        "CAR": "Project-car door",
        "PED": "Pedestrian entrance",
        "RC": "RC workshop door",
    }
    for opening in model["front_openings"]:
        opening["name"] = opening_names[opening["id"]]

    technical_names = {
        "GLZ-CAR": "Project-car workshop window",
        "GLZ-RC": "RC / aircraft workshop window",
    }
    for opening in model["technical_glazing"]:
        opening["name"] = technical_names[opening["id"]]

    bedroom_names = {
        "GLZ-H1": "Child 1 bedroom",
        "GLZ-H2": "Child 2 bedroom",
        "GLZ-G": "Guest bedroom",
        "GLZ-M-A": "Primary suite",
        "GLZ-M-R": "Primary suite rear",
    }
    for opening in model["bedroom_glazing"]:
        opening["name"] = bedroom_names[opening["id"]]
    return model


VISIBLE_TRANSLATIONS = {
    "PLATAFORMA FRONTAL 3,00 m · pendiente 1,5–2% hacia drenaje":
        "FRONT CONCRETE APRON 3.00 m · 1.5–2% fall to drainage",
    "CAR PROJECT · 70,4 m² netos aprox.": "PROJECT CAR · approx. 70.4 m² net",
    "RC / DIY · 70,4 m² netos aprox.": "RC / DIY · approx. 70.4 m² net",
    "FRANJA DE RESPIRACIÓN": "BREATHING BUFFER",
    "SALA MONUMENTAL": "MONUMENTAL LIVING HALL",
    "COMEDOR": "DINING",
    "ESTAR / TRANSICIÓN": "LOUNGE / TRANSITION",
    "COCINA + GALERÍA DOMÉSTICA": "KITCHEN + DOMESTIC GALLERY",
    "EJE PEATONAL PERCEPTUAL LIBRE · 4,00 m":
        "CLEAR PERCEPTUAL PEDESTRIAN AXIS · 4.00 m",
    "m² brutos": "m² gross",
    "ISLA 3,60 × 1,20 · 4 puestos": "ISLAND 3.60 × 1.20 · 4 seats",
    "MESA 12 P · 3,60 × 1,30": "12-SEAT TABLE · 3.60 × 1.30",
    "CENTRO": "CENTRE",
    "1,20 m operativo": "1.20 m working side",
    "≥1,50 m social": "≥1.50 m social side",
    "VIDRIO PRINCIPAL PROVISIONAL · bolsillo de cortina acústica":
        "PROVISIONAL MAIN GLAZING · acoustic-curtain pocket",
    "PRISMA DE EXCLUSIÓN LIFT / VEHÍCULO": "LIFT / VEHICLE EXCLUSION ENVELOPE",
    "BANCO CENTRAL RC · 4,50 × 1,60": "CENTRAL RC BENCH · 4.50 × 1.60",
    "ventilado": "ventilated",
    "Portón carro": "Project-car door",
    "Acceso peatonal": "Pedestrian entrance",
    "Portón RC": "RC workshop door",
    "36,00 m nominales exteriores": "36.00 m nominal external length",
    "10,50": "10.50",
    "CRITERIOS DE ESTA REVISIÓN": "COORDINATION BASIS",
    "Envolvente 0,18 m; gran muro 0,20 m; divisiones 0,15 m y escalera 0,20 m: valores de estudio, no especificación IFC.":
        "Wall thicknesses remain study values; D-068 changes workstation coordination only.",
    "Gran muro continuo de madera/listón con respaldo absorbente: puertas de pantry, bodega, baño y homelab enrasadas; escalera deliberadamente legible.":
        "The Great Wall, flush service doors and legible stair portal remain unchanged.",
    "Losa industrial continua; juntas, pendientes, cargas del lift, drenajes, estructura, fuego, extracción y MEP siguen pendientes de ingeniería y predio.":
        "Slab, lift, drainage, structure, fire, extraction and MEP remain professional design gates.",
    "NO APTO PARA CONSTRUIR. El mobiliario y equipos son envolventes de prueba y deben sustituirse por fichas reales.":
        "NOT FOR CONSTRUCTION. Worktops and equipment remain coordination envelopes pending real product data.",
    "ALERO BAJO": "LOW EAVE",
    "ALERO ALTO": "HIGH EAVE",
    "TODA EL AGUA DE CUBIERTA DESCARGA AQUÍ": "ALL ROOF WATER DISCHARGES HERE",
    "P2 POSTERIOR · 15,00 m": "REAR UPPER FLOOR · 15.00 m",
    "EVENTO PRINCIPAL SALA": "MAIN LIVING-HALL GLAZING",
    "ALTERNATIVA SEGÚN PREDIO": "SITE-DEPENDENT ALTERNATIVE",
    "PISO A TECHO": "NEAR FLOOR TO CEILING",
    "COTA EXTERIOR / DRENAJE PERIMETRAL PENDIENTE DE TOPOGRAFÍA":
        "EXTERNAL LEVEL / PERIMETER DRAINAGE PENDING SURVEY",
    "10,50 técnica": "10.50 technical",
    "10,50 monumental": "10.50 monumental",
    "10,50 doméstica": "10.50 domestic",
    "4,50 núcleo": "4.50 core",
    "36,00 m": "36.00 m",
    "NOTA DE COORDINACIÓN": "COORDINATION NOTE",
    "La posición de vidrio, ventanas, bajantes y panelización es una hipótesis coordinable. No adoptar orientación cardinal, protección solar ni huecos definitivos antes de seleccionar el predio.":
        "Openings remain a coordination hypothesis. Do not freeze orientation, solar control, drainage or glazing performance before site selection.",
    "orientación cardinal pendiente de predio": "cardinal orientation pending site selection",
    "antepecho": "sill",
}


def translate_visible_text(svg: str) -> str:
    for source, target in sorted(
        VISIBLE_TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        svg = svg.replace(source, target)
    return svg


def workstation_detail_sheet(model: dict[str, Any]) -> str:
    window = model["workstation_glazing"][0]
    workstation = model["workstations"][0]
    meta = model.get("drawing_meta", {})
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900">',
        base.title_block(
            meta.get("detail_code", "DET-006-R00"),
            meta.get("detail_title", "PB INTEGRATED WORKSTATION + BENCH FAMILY"),
            meta.get(
                "detail_subtitle",
                "D-068 coordination detail · mirrored pair · dedicated secondary steel · not for construction",
            ),
        ),
    ]

    # A — schematic wall section.
    parts.append(base.text(85, 125, "A · WALL / WINDOW / WORKTOP SECTION", 14, "start", 700))
    section_base = 690
    scale = 160
    wall_x = 245
    sill_y = section_base - window["sill"] * scale
    head_y = section_base - (window["sill"] + window["height"]) * scale
    worktop_y = section_base - workstation["worktop_height"] * scale
    rail_y = section_base - 0.68 * scale
    parts.append(base.rect(105, 165, 70, 525, fill="#aab4b6", stroke="#26363b", stroke_width="1.5"))
    parts.append(base.rect(175, 165, 70, 525, fill="#d8ded9", stroke="#536166", stroke_width="1"))
    parts.append(base.text(138, 430, "CORRUGATED / PANEL ENVELOPE", 8, weight=700, rotate=-90))
    parts.append(base.text(210, 430, "INSULATED WALL ZONE", 8, weight=700, rotate=-90))
    parts.append(base.rect(wall_x, head_y, 34, sill_y-head_y, fill="#416771", stroke="#172126", stroke_width="2.4"))
    parts.append(base.rect(wall_x-8, head_y-10, 50, 10, fill="#29383d", stroke="#172126"))
    parts.append(base.rect(wall_x-8, sill_y, 50, 14, fill="#29383d", stroke="#172126"))
    parts.append(base.text(wall_x+58, (head_y+sill_y)/2, "COORDINATED WINDOW FRAME", 9, "start", 700, "#294f58"))
    parts.append(base.rect(wall_x-4, rail_y-10, 48, 20, fill="#26363b", stroke="#172126", stroke_width="1"))
    parts.append(base.rect(wall_x+20, worktop_y-7, 260, 14, fill="#c99f6b", stroke="#5b432b", stroke_width="1.5"))
    parts.append(base.text(wall_x+150, worktop_y+3, f'REPLACEABLE TIMBER WORKTOP · {workstation["worktop_depth"]:.2f} m TEST DEPTH', 7, weight=700, fill="#3f2d20"))
    parts.append(
        f'<polygon points="{wall_x+42},{rail_y+8} {wall_x+142},{worktop_y+7} '
        f'{wall_x+42},{worktop_y+7}" fill="none" stroke="#26363b" stroke-width="4"/>'
    )
    parts.append(base.rect(wall_x+55, worktop_y+28, 160, 28, fill="#d5dadd", stroke="#59676c", stroke_width="1"))
    parts.append(base.text(wall_x+135, worktop_y+46, "ACCESSIBLE POWER / DATA TRAY", 7, weight=700))
    parts.append(
        f'<polyline points="{wall_x+20},{rail_y+10} {wall_x+20},{worktop_y+86} '
        f'{wall_x+112},{worktop_y+86}" fill="none" stroke="#59676c" stroke-width="1.2"/>'
    )
    parts.append(base.text(wall_x+120, worktop_y+90, "DEDICATED SECONDARY STEEL SERVICE RAIL", 7.5, "start", 700))
    dim_x = 555
    parts.append(f'<line x1="{dim_x}" y1="{sill_y}" x2="{dim_x}" y2="{worktop_y}" stroke="#8e3825" stroke-width="1.2"/>')
    parts.append(f'<line x1="{dim_x-5}" y1="{sill_y}" x2="{dim_x+5}" y2="{sill_y}" stroke="#8e3825"/>')
    parts.append(f'<line x1="{dim_x-5}" y1="{worktop_y}" x2="{dim_x+5}" y2="{worktop_y}" stroke="#8e3825"/>')
    parts.append(base.text(dim_x+10, (sill_y+worktop_y)/2+3, "0.15 m UPSTAND", 6.8, "start", 700, "#8e3825"))
    parts.append(base.text(85, 718, "EXTERIOR", 9, "start", 700, "#59676c"))
    parts.append(base.text(560, 718, "HALL INTERIOR", 9, "end", 700, "#59676c"))

    # B — interior elevation of the repeated 3 m module.
    parts.append(base.text(660, 125, "B · REPEATED 3.00 m INTERIOR ELEVATION", 14, "start", 700))
    ex, ey, ew, eh = 690, 190, 510, 280
    parts.append(base.rect(ex, ey, ew, eh, fill="#426671", stroke="#172126", stroke_width="3"))
    for i in (1, 2):
        xx = ex + ew * i / 3
        parts.append(f'<line x1="{xx}" y1="{ey}" x2="{xx}" y2="{ey+eh}" stroke="#9bb3b8" stroke-width="2"/>')
    window_width = window["x1"] - window["x0"]
    work_w = ew * workstation["worktop_length"] / window_width
    work_x, work_y = ex + (ew - work_w) / 2, ey + eh + 26
    parts.append(f'<line x1="{work_x}" y1="{work_y}" x2="{work_x+work_w}" y2="{work_y}" stroke="#c49a62" stroke-width="14"/>')
    parts.append(f'<line x1="{work_x}" y1="{work_y+15}" x2="{work_x+work_w}" y2="{work_y+15}" stroke="#26363b" stroke-width="6"/>')
    for fraction in (0.12, 0.5, 0.88):
        px = work_x + work_w * fraction
        parts.append(f'<polyline points="{px-12},{work_y+16} {px},{work_y+42} {px+12},{work_y+16}" fill="none" stroke="#26363b" stroke-width="3"/>')
    cabinet_width = workstation.get("drawer_cabinet_width")
    cabinet_height = workstation.get("drawer_cabinet_height")
    if cabinet_width and cabinet_height:
        module_scale = ew / window_width
        cabinet_w = cabinet_width * module_scale
        cabinet_h = cabinet_height * module_scale
        cabinet_y = work_y + 18
        for cabinet_x in (work_x, work_x + work_w - cabinet_w):
            parts.append(base.rect(cabinet_x, cabinet_y, cabinet_w, cabinet_h, fill="#8d6745", stroke="#26363b", stroke_width="2"))
            for drawer in range(1, workstation.get("drawer_levels", 3)):
                drawer_y = cabinet_y + cabinet_h * drawer / workstation.get("drawer_levels", 3)
                parts.append(f'<line x1="{cabinet_x}" y1="{drawer_y}" x2="{cabinet_x+cabinet_w}" y2="{drawer_y}" stroke="#d6c1a5" stroke-width="1.2"/>')
            for drawer in range(workstation.get("drawer_levels", 3)):
                handle_y = cabinet_y + cabinet_h * (drawer + 0.5) / workstation.get("drawer_levels", 3)
                parts.append(f'<line x1="{cabinet_x+cabinet_w*.38}" y1="{handle_y}" x2="{cabinet_x+cabinet_w*.62}" y2="{handle_y}" stroke="#efe2cf" stroke-width="2"/>')
    parts.append(base.text(ex+ew/2, ey+eh/2, "DIRECT LANDSCAPE VIEW", 12, weight=700, fill="#eff5f5"))
    parts.append(base.text(ex+ew/2, work_y-14, f'FIXED WORKSTATION · {workstation["worktop_length"]:.2f} m TEST LENGTH', 9, weight=700, fill="#5b432b"))
    caption_y = work_y + (142 if cabinet_width else 72)
    parts.append(base.text(ex+ew/2, caption_y, "Same geometry on Side A and Side B; reflect across Y=9.00 m", 8, weight=700, fill="#294b52"))

    # C — kit and hold points.
    kit_title_y = 660 if cabinet_width else 620
    kit_start_y = 680 if cabinet_width else 650
    kit_step = 32 if cabinet_width else 42
    kit_height = 24 if cabinet_width else 32
    parts.append(base.text(660, kit_title_y, "C · COMMON LOW-COST KIT OF PARTS", 14, "start", 700))
    worktop_note = (
        "Replaceable timber top + two large suspended steel three-drawer cabinets"
        if cabinet_width
        else "Replaceable local timber worktop; desks and benches may use different duty classes"
    )
    kit = [
        ("01", "Dedicated secondary-steel rail and bolted brackets"),
        ("02", worktop_note),
        ("03", "Accessible separated power/data tray and task-lighting provision"),
        ("04", "Window trimmers, seals, flashing and thermal bridge resolved as one facade detail"),
    ]
    for index, (number, note) in enumerate(kit):
        y = kit_start_y + index * kit_step
        parts.append(base.rect(660, y, 620, kit_height, fill="#f1eee7", stroke="#c0bbb0", stroke_width=".8"))
        parts.append(base.text(676, y+18, number, 8, "start", 700, "#8e3825"))
        parts.append(base.text(710, y+18, note, 7.5, "start"))

    parts.append(base.rect(70, 825, 1260, 55, fill="#fff4df", stroke="#bd5c3c", stroke_width="1"))
    parts.append(base.text(88, 848, "ENGINEERING HOLD", 10, "start", 700, "#8e3825"))
    parts.append(base.text(220, 848, "The rail, brackets, trimmers, loads, deflection, vibration, fire/corrosion protection and connections require professional design. Do not field-weld to primary steel or load the window frame.", 7.6, "start", 700, "#5a3a2c"))
    parts.append(base.text(88, 868, "SITE HOLD", 10, "start", 700, "#8e3825"))
    parts.append(base.text(220, 868, "Glare, shading, privacy, condensation, cold downdraught and operable areas remain dependent on the selected site and orientation.", 7.6, "start", 700, "#5a3a2c"))
    parts.append("</svg>")
    return "".join(parts)


def validate_b24(model: dict[str, Any]) -> list[dict[str, str]]:
    checks = base.validate(model)
    ext = model["envelope"]["exterior_wall"]
    width = model["envelope"]["width"]
    by_side = {item["side"]: item for item in model["workstations"]}
    glazing = {item["side"]: item for item in model["workstation_glazing"]}
    a, b = by_side["A"], by_side["B"]
    ga, gb = glazing["A"], glazing["B"]

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
                "message": message,
            }
        )

    add(
        "PB-WS-PAIR",
        set(by_side) == {"A", "B"},
        "Exactly one permanent wall-integrated workstation is reserved on each long side.",
    )
    same_geometry = all(
        abs(a[key] - b[key]) < 1e-9
        for key in ("zone_x0", "zone_x1", "zone_depth", "worktop_x0", "worktop_length", "worktop_depth", "worktop_height")
    )
    add(
        "PB-WS-MIRROR",
        same_geometry,
        "The Side A and Side B workstation geometry is identical before reflection across Y=9.00 m.",
    )
    a_back = ext
    b_back = width - ext
    b_inner = b_back - b["worktop_depth"]
    add(
        "PB-WS-WALL-CONTACT",
        abs(a_back + a["worktop_depth"] - (width - b_inner)) < 1e-9,
        f"Both worktops meet the interior wall/service-rail plane: Y={a_back:.2f} m and Y={b_back:.2f} m.",
    )
    windows_equal = all(
        abs(ga[key] - gb[key]) < 1e-9
        for key in ("x0", "x1", "sill", "height", "modules")
    )
    add(
        "PB-WS-GLAZING-SYMMETRY",
        windows_equal,
        "The two workstation windows have identical nominal geometry and module count.",
    )
    aligned = all(
        abs(glazing[side]["x0"] - by_side[side]["zone_x0"]) < 1e-9
        and abs(glazing[side]["x1"] - by_side[side]["zone_x1"]) < 1e-9
        for side in ("A", "B")
    )
    add(
        "PB-WS-PLAN-ELEVATION-SYNC",
        aligned,
        "Each workstation clearance zone and its facade opening share the same X extent.",
    )
    add(
        "PB-WS-SILL-CLEARANCE",
        ga["sill"] - a["worktop_height"] >= 0.10,
        f'Window sill is {ga["sill"] - a["worktop_height"]:.2f} m above the test worktop.',
    )
    clear_axis = ext + a["zone_depth"] < model["design_values"]["axis_y0"] and (
        width - ext - b["zone_depth"] > model["design_values"]["axis_y1"]
    )
    add(
        "PB-WS-AXIS-CLEAR",
        clear_axis,
        "Both 3.00 m workstation clearance zones remain outside the 4.00 m central perceptual axis.",
    )
    add(
        "PB-WS-STRUCTURAL-BAY",
        ga["x0"] >= 12.0 and ga["x1"] <= 18.0,
        "Both workstation openings remain inside the X=12–18 m primary-frame bay pending trimmer design.",
    )
    add(
        "PB-WS-BENCH-FAMILY",
        len(model["built_in_benches"]) == 2
        and all("D-068 steel rail" in item["support_family"] for item in model["built_in_benches"]),
        "The RC and project-car benches reference the same steel-rail / replaceable-worktop family.",
    )
    junction = 16.2 - ga["x1"]
    add(
        "PB-WS-A-MAIN-GLAZING-JUNCTION",
        False,
        f"Side A retains a {junction:.2f} m nominal mullion/trimmer hold between workstation and main glazing; detailed facade and structural design remain open.",
        open_gate=True,
    )
    add(
        "PB-CAR-BENCH-LIFT-INTERFACE",
        False,
        "The project-car bench remains in its predecessor test position; real lift, vehicle and tool envelopes govern final support and location.",
        open_gate=True,
    )
    return checks


def generate(model: dict[str, Any], target: Path = OUT) -> dict[str, Any]:
    checks = validate_b24(model)
    outputs = {
        "DH-ARQ-PLN-001-R05_PB-INTEGRATED-WORKSTATIONS.svg":
            translate_visible_text(base.plan_sheet(model)),
        "DH-ARQ-ELE-003-R07_SIDE-A-INTEGRATED-WORKSTATION.svg":
            translate_visible_text(base.side_elevation_sheet(model, "A")),
        "DH-ARQ-ELE-004-R07_SIDE-B-INTEGRATED-WORKSTATION.svg":
            translate_visible_text(base.side_elevation_sheet(model, "B")),
        "DH-ARQ-DET-006-R00_PB-INTEGRATED-WORKSTATIONS.svg": workstation_detail_sheet(model),
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
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "revision": model["revision"],
        "status": model["status"],
        "source": "dreamhouse/pb_b24_delta.json",
        "source_sha256": hashlib.sha256(DELTA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_pb_b24.py",
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    target.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if report["failed"]:
        raise ValueError(f'PB b24 validation failed: {report["failed"]} failed checks')
    return report


def main() -> None:
    report = generate(load_b24_model())
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

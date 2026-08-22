"""Build the first presentation-only ground-floor SVG pilot.

The pilot deliberately consumes the promoted SVG instead of reconstructing the
architectural model.  Source geometry is copied without coordinate changes and placed
inside one canvas transform.  Only presentation attributes and annotation placement are
changed.  The output is not a current issue and has no construction authority.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import textwrap
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "planos/actual/DH-ARQ-PLN-001_CURRENT-GROUND-FLOOR.svg"
OUTPUT_DIR = ROOT / "planos/piloto_grafico_v0.1"
OUTPUT = OUTPUT_DIR / "DH-ARQ-PLN-001-GP01_GROUND-FLOOR-READABILITY-PILOT.svg"
MANIFEST = OUTPUT_DIR / "manifest.json"

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


PALETTE = {
    "#fbfaf7": "#FFFDFA",
    "#243238": "#172A32",
    "#26363b": "#172A32",
    "#45545a": "#536168",
    "#526168": "#536168",
    "#f1eee7": "#F7F4EC",
    "#d6e0e4": "#E9F0F2",
    "#e6d7c7": "#F2E8DE",
    "#ead4b6": "#F5E8D4",
    "#e7d3b9": "#F3E6D5",
    "#27859a": "#1D7480",
    "#246b7a": "#1D6873",
    "#b47d16": "#8A5A16",
    "#8a6518": "#765018",
    "#b14e35": "#A33F31",
    "#9a3d2a": "#92382D",
    "#b95336": "#A33F31",
    "#873923": "#92382D",
    "#f9f3e8": "#172A32",
    "#332923": "#172A32",
}


KEYED_NOTES = {
    "RC / ELECTRONICS MODULAR BENCH · 6 × 1.50 m · 3 ADJUSTABLE": "P01",
    "CENTRAL RC ASSEMBLY ISLAND · 3 × 1.50 m · TOP +0.84": "P02",
    "LiPo · SEPARATE / VENTILATED": "P03",
    "PROJECT-CAR MODULAR BENCH · 6 × 1.50 m · +0.84 / +0.90": "P04",
    "LIFT / VEHICLE EXCLUSION ENVELOPE": "P05",
    "SIDE A SHARED WORKSTATION · 7.20 × 3.00 m CLEAR": "P06",
    "WORKSTATION 2 · 3 × 3 m CLEAR": "P07",
    "4.00 m SOFA": "P08",
    "100-IN TV · SIDE B WALL": "P09",
    "1.10 m CHAIR / WALK CLEARANCE ENVELOPE": "P10",
    "7.20 m FULL-SPAN ISLAND · DRY PREP + 8 SEATS": "P11",
}


KEYED_NOTE_DETAILS = {
    **{label: (code, label) for label, code in KEYED_NOTES.items()},
    "RC / ELECTRONICS MODULAR BENCH · 6 × 1.50 m · 3 ADJUSTABLE": (
        "P01",
        "RC / ELECTRONICS MODULAR BENCH · 6 × 1.50 m · 3 ADJUSTABLE; "
        "1.20 m CLEAR BENCH OPERATING STRIP",
    ),
    "PROJECT-CAR MODULAR BENCH · 6 × 1.50 m · +0.84 / +0.90": (
        "P04",
        "PROJECT-CAR MODULAR BENCH · 6 × 1.50 m · +0.84 / +0.90; "
        "1.20 m BENCH OPERATING STRIP · LIFT OVERLAP OPEN",
    ),
}


KEY_POSITIONS = {
    "PROJECT-CAR MODULAR BENCH · 6 × 1.50 m · +0.84 / +0.90": (466, 600),
}


RELOCATED_ZONE_NOTES = {
    "PROJECT CAR · approx. 70.4 m² net": (
        "Z01",
        "PROJECT CAR · approx. 70.4 m² net",
        466,
        544,
    ),
}


RELOCATED_SECONDARY_NOTES = {
    "1.20 m CLEAR BENCH OPERATING STRIP": "P01",
    "1.20 m BENCH OPERATING STRIP · LIFT OVERLAP OPEN": "P04",
}


PRIMARY_LABELS = {
    "RC / DIY · approx. 70.4 m² net",
    "BREATHING BUFFER",
    "DOUBLE-HEIGHT SOCIAL HALL",
    "FULL-SPAN KITCHEN",
    "DINING OPPOSITE KITCHEN",
    "CLEAR PERCEPTUAL PEDESTRIAN AXIS · 4.00 m",
    "LIVING / 100-IN TV LOUNGE",
}


CORE_NOTES = {
    "Homelab / technical": ("R01", "Homelab / technical · 20.7 m² gross", "194"),
    "Ground-floor bathroom": ("R02", "Ground-floor bathroom · 10.8 m² gross", "294"),
    "Protected stair": ("R03", "Protected stair · 16.2 m² gross", "359"),
    "Storage": ("R04", "Storage · 22.5 m² gross", "505"),
    "Pantry / clean support": ("R05", "Pantry / clean support · 10.8 m² gross", "586"),
}


SECONDARY_LABELS = {
    "10.8 m² gross",
    "22.5 m² gross",
    "16.2 m² gross",
    "20.7 m² gross",
    "1.35 m WORKING AISLE",
    "≥1.50 m SOCIAL SIDE",
    "4.10 m VIEW",
    "12P · 3.20 × 1.10",
    "36.00 m nominal external length",
}


COORDINATION_BASIS = [
    "Wall thicknesses remain study values; D-083 aligns desk-window sills at +0.75 m "
    "and retains the repeated 1.20 m P2 bedroom-window family.",
    "The Great Wall, flush service doors and legible stair portal remain unchanged.",
    "Slab, lift, drainage, structure, fire, extraction and MEP remain professional design gates.",
    "Worktops and equipment remain coordination envelopes pending real product data.",
]


CSS = """
:root {
  --paper: #F4F0E7;
  --panel: #FFFDFA;
  --ink: #172A32;
  --muted: #536168;
  --info: #1D7480;
  --open: #8A5A16;
  --conflict: #A33F31;
  --hypothesis: #66538A;
  --material: #74543C;
}
text {
  font-family: Inter, "IBM Plex Sans", "Liberation Sans", Arial, sans-serif;
  text-rendering: geometricPrecision;
}
.new-title { fill: var(--ink); font-weight: 700; letter-spacing: .15px; }
.new-eyebrow { fill: var(--info); font-weight: 700; letter-spacing: .9px; }
.new-body { fill: var(--ink); }
.new-muted { fill: var(--muted); }
.new-open { fill: var(--open); font-weight: 700; }
.new-conflict { fill: var(--conflict); font-weight: 700; }
.new-on-dark { fill: #FFFDFA; }
.new-on-dark-muted { fill: #DDE4E2; }
.new-on-dark-alert { fill: #FFB4A8; font-weight: 800; }
.key-tag {
  fill: var(--ink);
  stroke: var(--panel);
  stroke-width: 4px;
  paint-order: stroke fill;
  font-weight: 800;
  letter-spacing: .25px;
}
.model-primary {
  fill: var(--ink);
  stroke: var(--panel);
  stroke-width: 2.4px;
  paint-order: stroke fill;
  font-weight: 650;
}
.model-secondary { font-weight: 550; }
.sheet-rule { stroke: #B9C0BD; stroke-width: 1; }
.panel-rule { stroke: #CBD0CC; stroke-width: 1; }
""".strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text_value(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _set_text(element: ET.Element, value: str) -> None:
    for child in list(element):
        element.remove(child)
    element.text = value


def _restyle_source_node(node: ET.Element) -> None:
    """Apply presentation tokens while preserving every geometry attribute."""

    for element in node.iter():
        for attr in ("fill", "stroke"):
            value = element.get(attr)
            if value and value.lower() in PALETTE:
                element.set(attr, PALETTE[value.lower()])

        if element.tag != q("text"):
            continue

        label = _text_value(element)
        if label in KEYED_NOTES:
            _set_text(element, KEYED_NOTES[label])
            element.set("class", "key-tag")
            element.set("font-size", "8.8")
            element.set("data-text-role", "key")
            if label in KEY_POSITIONS:
                x, y = KEY_POSITIONS[label]
                element.set("x", str(x))
                element.set("y", str(y))
        elif label in RELOCATED_ZONE_NOTES:
            code, _description, x, y = RELOCATED_ZONE_NOTES[label]
            _set_text(element, code)
            element.set("class", "key-tag")
            element.set("font-size", "8.8")
            element.set("x", str(x))
            element.set("y", str(y))
            element.set("data-text-role", "key")
        elif label in RELOCATED_SECONDARY_NOTES:
            element.set("display", "none")
            element.set("data-relocated-to", RELOCATED_SECONDARY_NOTES[label])
        elif label in CORE_NOTES:
            code, _description, new_y = CORE_NOTES[label]
            _set_text(element, code)
            element.set("class", "key-tag")
            element.set("font-size", "8.8")
            element.set("y", new_y)
            element.set("data-text-role", "key")
        elif label.endswith("m² gross") and float(element.get("x", "0")) > 1100:
            element.set("display", "none")
            element.set("data-relocated-to", "service-core-key")
        elif label in PRIMARY_LABELS:
            element.set("class", "model-primary")
            element.set("font-size", "10.4")
            element.set("data-text-role", "primary")
        elif label in SECONDARY_LABELS:
            element.set("class", "model-secondary")
            element.set("font-size", "8.8")
            element.set("data-text-role", "secondary")
        else:
            size = float(element.get("font-size", "0") or 0)
            if size >= 8:
                element.set("font-size", "9.2")
                element.set("data-text-role", "secondary")
            elif len(label) <= 13 and size < 6.8:
                element.set("font-size", "6.8")
                element.set("data-text-role", "micro")

        if "WINDOW ·" in label:
            element.set("font-size", "8.4")
            element.set("data-text-role", "opening")

        if label == "FRÍO":
            _set_text(element, "COLD")
        elif label == "LIMPIEZA":
            _set_text(element, "CLEAN")


def _add_text(
    parent: ET.Element,
    x: float,
    y: float,
    value: str,
    *,
    size: float,
    css_class: str = "new-body",
    anchor: str | None = None,
    weight: int | None = None,
) -> ET.Element:
    attrs = {
        "x": f"{x:g}",
        "y": f"{y:g}",
        "font-size": f"{size:g}",
        "class": css_class,
    }
    if anchor:
        attrs["text-anchor"] = anchor
    if weight:
        attrs["font-weight"] = str(weight)
    element = ET.SubElement(parent, q("text"), attrs)
    element.text = value
    return element


def _add_wrapped_text(
    parent: ET.Element,
    x: float,
    y: float,
    value: str,
    *,
    width_chars: int,
    size: float = 9.6,
    line_height: float = 12.4,
    css_class: str = "new-body",
) -> tuple[ET.Element, float]:
    lines = textwrap.wrap(value, width=width_chars, break_long_words=False, break_on_hyphens=False)
    element = ET.SubElement(
        parent,
        q("text"),
        {"x": f"{x:g}", "y": f"{y:g}", "font-size": f"{size:g}", "class": css_class},
    )
    for index, line in enumerate(lines):
        tspan = ET.SubElement(
            element,
            q("tspan"),
            {"x": f"{x:g}", "dy": "0" if index == 0 else f"{line_height:g}"},
        )
        tspan.text = line
    return element, y + line_height * max(1, len(lines))


def _add_rule(parent: ET.Element, y: float) -> None:
    ET.SubElement(
        parent,
        q("line"),
        {
            "x1": "1324",
            "y1": f"{y:g}",
            "x2": "1628",
            "y2": f"{y:g}",
            "class": "sheet-rule",
        },
    )


def build_svg(source: Path = SOURCE) -> ET.ElementTree:
    source_root = ET.parse(source).getroot()
    children = list(source_root)
    if len(children) < 253 or children[2].tag != q("defs"):
        raise ValueError("Unexpected ground-floor source structure; review the pilot adapter")

    root = ET.Element(
        q("svg"),
        {
            "width": "1684",
            "height": "1191",
            "viewBox": "0 0 1684 1191",
            "preserveAspectRatio": "xMidYMid meet",
            "role": "img",
            "aria-labelledby": "gp01-title gp01-desc",
            "data-sheet-id": "DH-ARQ-PLN-001",
            "data-revision": "GP01",
            "data-status": "graphic-pilot-not-current",
            "data-construction-authority": "false",
        },
    )
    title = ET.SubElement(root, q("title"), {"id": "gp01-title"})
    title.text = "Ground-floor readability pilot GP01"
    desc = ET.SubElement(root, q("desc"), {"id": "gp01-desc"})
    desc.text = (
        "Presentation-only pilot of the coordinated ground-floor plan. Architectural geometry, "
        "dimensions, programme and open design gates are copied from the current R15 source."
    )
    metadata = ET.SubElement(root, q("metadata"))
    metadata.text = json.dumps(
        {
            "construction_authority": False,
            "date": "2026-08-21",
            "pilot": "GP01",
            "revision": "GP01",
            "sheet": "DH-ARQ-PLN-001",
            "source": source.relative_to(ROOT).as_posix(),
            "source_revision": "PLN-001-R15 / 0.3-draft-37-PB",
            "source_sha256": sha256(source),
            "status": "presentation-only graphic pilot; not current; not for construction",
        },
        sort_keys=True,
    )
    style = ET.SubElement(root, q("style"))
    style.text = CSS
    root.append(copy.deepcopy(children[2]))

    background = ET.SubElement(root, q("g"), {"id": "layer-background", "data-layer": "background"})
    ET.SubElement(background, q("rect"), {"width": "1684", "height": "1191", "fill": "#F4F0E7"})
    panel_specs = (
        ("36", "116", "1250", "728"),
        ("36", "860", "1250", "148"),
        ("1304", "116", "344", "892"),
    )
    for x, y, width, height in panel_specs:
        ET.SubElement(
            background,
            q("rect"),
            {
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "rx": "5",
                "fill": "#FFFDFA",
                "class": "panel-rule",
            },
        )

    model = ET.SubElement(
        root,
        q("g"),
        {
            "id": "layer-model",
            "data-layer": "model-geometry-and-annotations",
            "transform": "translate(-86.6 -10.6) scale(1.15)",
        },
    )
    for source_index, source_node in enumerate(children[3:247], start=3):
        node = copy.deepcopy(source_node)
        node.set("data-source-index", str(source_index))
        node.set("data-model-id", f"PB-SOURCE-{source_index:03d}")
        _restyle_source_node(node)
        model.append(node)

    annotations = ET.SubElement(
        root, q("g"), {"id": "layer-annotations", "data-layer": "legend-and-keynotes"}
    )
    _add_text(annotations, 58, 886, "READING HIERARCHY", size=11.5, css_class="new-eyebrow")
    _add_text(
        annotations,
        58,
        910,
        "Heavy dark lines = enclosing/cut geometry",
        size=10,
        css_class="new-body",
    )
    _add_text(
        annotations,
        58,
        932,
        "Fine grey lines = fixtures, furniture and reference geometry",
        size=10,
        css_class="new-body",
    )
    _add_text(
        annotations,
        58,
        954,
        "Amber dashed = clearance or open coordination envelope",
        size=10,
        css_class="new-open",
    )
    _add_text(
        annotations,
        58,
        976,
        "Red dashed = exclusion / unresolved safety interface",
        size=10,
        css_class="new-conflict",
    )

    swatches = [
        (560, "#E9F0F2", "Technical / workshop"),
        (755, "#F7F4EC", "Breathing buffer"),
        (925, "#F2E8DE", "Living / hall"),
        (1085, "#F5E8D4", "Kitchen / dining"),
    ]
    for x, fill, label in swatches:
        ET.SubElement(
            annotations,
            q("rect"),
            {
                "x": str(x),
                "y": "901",
                "width": "18",
                "height": "18",
                "rx": "2",
                "fill": fill,
                "stroke": "#536168",
            },
        )
        _add_wrapped_text(
            annotations,
            x + 26,
            912,
            label,
            width_chars=17,
            size=9.7,
            line_height=12,
        )
    _add_wrapped_text(
        annotations,
        560,
        966,
        "Colour is an entry aid only. Linework, labels and status wording remain the "
        "technical reading authority.",
        width_chars=95,
        size=9.7,
        line_height=12,
        css_class="new-muted",
    )

    sidebar = ET.SubElement(
        root,
        q("g"),
        {"id": "layer-status", "data-layer": "status-and-keyed-notes"},
    )
    _add_text(sidebar, 1324, 146, "KEYED COORDINATION ITEMS", size=12.5, css_class="new-title")
    _add_wrapped_text(
        sidebar,
        1324,
        168,
        "Codes replace long labels inside the plan; the source wording is retained here.",
        width_chars=43,
        size=9.7,
        line_height=12.2,
        css_class="new-muted",
    )
    y = 214.0
    for label, code in KEYED_NOTES.items():
        _add_text(sidebar, 1324, y, code, size=9.8, css_class="new-eyebrow")
        detail = KEYED_NOTE_DETAILS.get(label, (code, label))[1]
        _, bottom = _add_wrapped_text(
            sidebar,
            1362,
            y,
            detail,
            width_chars=35,
            size=10.2,
            line_height=11.8,
        )
        y = bottom + 8

    zone_rule_y = y + 2
    _add_rule(sidebar, zone_rule_y)
    _add_text(
        sidebar,
        1324,
        zone_rule_y + 26,
        "RELOCATED ZONE LABEL",
        size=12.5,
        css_class="new-title",
    )
    y = zone_rule_y + 50
    for _label, (code, description, _x, _y) in RELOCATED_ZONE_NOTES.items():
        _add_text(sidebar, 1324, y, code, size=9.8, css_class="new-eyebrow")
        _, bottom = _add_wrapped_text(
            sidebar,
            1362,
            y,
            description,
            width_chars=35,
            size=10.2,
            line_height=12.2,
        )
        y = bottom + 7

    core_rule_y = y + 2
    _add_rule(sidebar, core_rule_y)
    _add_text(sidebar, 1324, core_rule_y + 26, "SERVICE CORE", size=12.5, css_class="new-title")
    y = core_rule_y + 50
    for _label, (code, description, _new_y) in CORE_NOTES.items():
        _add_text(sidebar, 1324, y, code, size=9.8, css_class="new-eyebrow")
        _, bottom = _add_wrapped_text(
            sidebar,
            1362,
            y,
            description,
            width_chars=35,
            size=10.2,
            line_height=12.2,
        )
        y = bottom + 7

    rule_y = y + 3
    _add_rule(sidebar, rule_y)
    _add_text(sidebar, 1324, rule_y + 28, "COORDINATION BASIS", size=12.5, css_class="new-title")
    y = rule_y + 52
    for note in COORDINATION_BASIS:
        _add_text(sidebar, 1324, y, "•", size=10, css_class="new-open")
        _, bottom = _add_wrapped_text(
            sidebar,
            1340,
            y,
            note,
            width_chars=43,
            size=10.2,
            line_height=12.2,
        )
        y = bottom + 8

    sheet = ET.SubElement(root, q("g"), {"id": "layer-sheet", "data-layer": "titleblock"})
    _add_text(
        sheet,
        36,
        34,
        "GRAPHIC PILOT 01 · PRESENTATION ONLY",
        size=10.5,
        css_class="new-eyebrow",
    )
    _add_text(sheet, 36, 70, "GROUND FLOOR · COORDINATED READING", size=24, css_class="new-title")
    _add_text(
        sheet,
        36,
        96,
        "Same R15 geometry and values · reduced annotation competition · professional "
        "core + didactic overlay",
        size=11,
        css_class="new-muted",
    )
    _add_text(sheet, 1648, 56, "DH-ARQ-PLN-001", size=15, css_class="new-title", anchor="end")
    _add_text(
        sheet,
        1648,
        80,
        "GP01 · NOT CURRENT",
        size=10.5,
        css_class="new-conflict",
        anchor="end",
    )
    ET.SubElement(
        sheet,
        q("line"),
        {"x1": "36", "y1": "105", "x2": "1648", "y2": "105", "class": "sheet-rule"},
    )

    ET.SubElement(
        sheet,
        q("rect"),
        {
            "x": "36",
            "y": "1026",
            "width": "1612",
            "height": "129",
            "rx": "5",
            "fill": "#172A32",
        },
    )
    _add_text(sheet, 56, 1056, "NOT FOR CONSTRUCTION", size=13, css_class="new-on-dark-alert")
    _add_text(
        sheet,
        56,
        1082,
        "Graphic review only. This file is not the current drawing and creates no design, "
        "procurement or construction authority.",
        size=10.2,
        css_class="new-on-dark",
    )
    _add_text(
        sheet,
        56,
        1107,
        "Source: PLN-001-R15 / 0.3-draft-37-PB · Decision basis: D-083 · Model coordinates "
        "and displayed values preserved.",
        size=9.8,
        css_class="new-on-dark-muted",
    )
    _add_text(
        sheet,
        56,
        1132,
        "Open gates: site · solar/privacy · structure · safe glazing · building physics · "
        "operation · drainage · cost",
        size=9.8,
        css_class="new-on-dark-muted",
    )
    _add_text(
        sheet,
        1628,
        1132,
        "2026-08-21",
        size=9.8,
        css_class="new-on-dark-muted",
        anchor="end",
    )

    return ET.ElementTree(root)


def write_outputs(source: Path = SOURCE, output: Path = OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    tree = build_svg(source)
    ET.indent(tree, space="  ")
    tree.write(output, encoding="utf-8", xml_declaration=True)
    manifest = {
        "construction_authority": False,
        "date": "2026-08-21",
        "generator": "dreamhouse/svg/pilot_ground_floor.py",
        "output": output.name,
        "output_sha256": sha256(output),
        "pilot": "GP01",
        "sheet": "DH-ARQ-PLN-001",
        "source": source.relative_to(ROOT).as_posix(),
        "source_revision": "PLN-001-R15 / 0.3-draft-37-PB",
        "source_sha256": sha256(source),
        "status": "presentation-only graphic pilot; not current; not for construction",
    }
    manifest_path = output.parent / MANIFEST.name
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    write_outputs(args.source, args.output)


if __name__ == "__main__":
    main()

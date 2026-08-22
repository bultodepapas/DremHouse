"""Build the presentation-only P2 wall-family SVG pilot GP04.

The two controlled R22 wall build-ups are copied without non-text coordinate changes
and enlarged in independent sheet transforms.  The schedule and evidence are editorial
recomposition only.  The output is not current and has no construction authority.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.svg.layout import (
    Bounds,
    LayoutRegion,
    SHEET_FOOTER_REGION,
    SHEET_HEADER_REGION,
    register_text_regions,
)
from dreamhouse.svg.sheet import (
    add_footer,
    add_header,
    add_text,
    add_wrapped_text,
    create_document,
    q,
    sha256,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "planos/actual/DH-ARQ-DET-003_CURRENT-P2-ACOUSTIC-PARTITION.svg"
OUTPUT_DIR = ROOT / "planos/piloto_grafico_v0.1"
OUTPUT = OUTPUT_DIR / "DH-ARQ-DET-003-GP04_P2-WALL-FAMILY-READABILITY-PILOT.svg"
MANIFEST = OUTPUT_DIR / "DH-ARQ-DET-003-GP04.manifest.json"

LAYOUT_REGIONS = (
    SHEET_HEADER_REGION,
    LayoutRegion.with_inset("build-ups", Bounds(36, 116, 930, 594), 8),
    LayoutRegion.with_inset("schedule", Bounds(982, 116, 666, 594), 8),
    LayoutRegion.with_inset("keys", Bounds(36, 726, 500, 282), 8),
    LayoutRegion.with_inset("control", Bounds(552, 726, 500, 282), 8),
    LayoutRegion.with_inset("open", Bounds(1068, 726, 580, 282), 8),
    SHEET_FOOTER_REGION,
)

W01A_SOURCE_RANGE = range(18, 39)
W01B_SOURCE_RANGE = range(41, 81)

SCHEDULE_ROWS = (
    ("P2-W01A", "90 mm", "dry wall inside one suite"),
    ("P2-W01B", "200 mm", "suite-to-suite / suite-to-common"),
    ("P2-W02", "150 mm", "wet / service wall; shafts thicken locally"),
    ("P2-W02S", "200 mm", "sauna / hot-side reserve; separate detail"),
    ("P2-W03", "200 mm", "stair / protected-core reserve only"),
    ("P2-W04R", "200 mm", "retained bedroom ends at hall edge"),
    ("P2-W05", "230 mm", "insulated shell + independent inner lining"),
    ("P2-W06", "90 mm", "reversible phase closure; upgrade if required"),
)

SOURCE_SCHEDULE_INDEXES = (
    (89, 90, 91),
    (93, 94, 95),
    (97, 98, 99),
    (101, 102, 103),
    (105, 106, 107),
    (109, 110, 111),
    (113, 114, 115),
    (117, 118, 119),
)

LAYER_KEYS = {
    "P2-W01A": (
        ("1", "new visible board · 12.5 mm", "new-board"),
        ("2", "insulated frame · 64 mm", "insulated-frame"),
        ("3", "new visible board · 12.5 mm", "new-board"),
    ),
    "P2-W01B": (
        ("1", "new visible board · 12.5 mm", "new-board"),
        ("2", "reclaimed concealed board · 12.5 mm", "reclaimed-board"),
        ("3", "insulated frame · 64 mm", "insulated-frame"),
        ("4", "clear decoupling cavity · 20 mm", "air-cavity"),
        ("5", "insulated frame · 64 mm", "insulated-frame"),
        ("6", "reclaimed concealed board · 12.5 mm", "reclaimed-board"),
        ("7", "new visible board · 12.5 mm", "new-board"),
    ),
}


def _text_value(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _add_patterns(root: ET.Element) -> None:
    defs = ET.SubElement(root, q("defs"))

    new_board = ET.SubElement(
        defs,
        q("pattern"),
        {
            "id": "gp04-new-board",
            "width": "8",
            "height": "8",
            "patternUnits": "userSpaceOnUse",
        },
    )
    ET.SubElement(new_board, q("rect"), {"width": "8", "height": "8", "fill": "#FFFDFA"})
    ET.SubElement(
        new_board,
        q("line"),
        {"x1": "0", "y1": "7.5", "x2": "8", "y2": "7.5", "stroke": "#AEB8B5"},
    )

    reclaimed = ET.SubElement(
        defs,
        q("pattern"),
        {
            "id": "gp04-reclaimed-board",
            "width": "7",
            "height": "7",
            "patternUnits": "userSpaceOnUse",
        },
    )
    ET.SubElement(reclaimed, q("rect"), {"width": "7", "height": "7", "fill": "#E5DED2"})
    ET.SubElement(
        reclaimed,
        q("path"),
        {"d": "M0 7 L7 0 M-3 3 L3 -3 M4 10 L10 4", "stroke": "#74543C", "stroke-width": ".8"},
    )

    insulated = ET.SubElement(
        defs,
        q("pattern"),
        {
            "id": "gp04-insulated-frame",
            "width": "10",
            "height": "10",
            "patternUnits": "userSpaceOnUse",
        },
    )
    ET.SubElement(insulated, q("rect"), {"width": "10", "height": "10", "fill": "#E1EEE7"})
    ET.SubElement(
        insulated,
        q("path"),
        {"d": "M-2 10 L10 -2 M3 13 L13 3", "stroke": "#39765A", "stroke-width": "1"},
    )

    air = ET.SubElement(
        defs,
        q("pattern"),
        {
            "id": "gp04-air-cavity",
            "width": "8",
            "height": "8",
            "patternUnits": "userSpaceOnUse",
        },
    )
    ET.SubElement(air, q("rect"), {"width": "8", "height": "8", "fill": "#FFFFFF"})
    ET.SubElement(
        air,
        q("circle"),
        {"cx": "4", "cy": "4", "r": ".8", "fill": "#798582"},
    )


def _validate_source(children: list[ET.Element]) -> None:
    if len(children) != 145 or children[3].tag != q("defs"):
        raise ValueError("Unexpected P2 wall-family source structure; review the GP04 adapter")

    for row, indexes in zip(SCHEDULE_ROWS, SOURCE_SCHEDULE_INDEXES, strict=True):
        source_row = tuple(_text_value(children[index]) for index in indexes)
        if source_row != row:
            raise ValueError(
                f"P2 wall schedule changed at {row[0]}; review the GP04 editorial adapter"
            )

    expected_labels = {
        16: "P2-W01A · 90 mm · SAME-SUITE DRY WALL",
        38: "90 mm NOMINAL · 89 mm ILLUSTRATIVE SUM",
        39: "P2-W01B · 200 mm · SUITE / COMMON SEPARATION",
        80: "200 mm NOMINAL · 198 mm ILLUSTRATIVE SUM",
    }
    for index, expected in expected_labels.items():
        if _text_value(children[index]) != expected:
            raise ValueError(f"P2 wall build-up changed at source node {index}; review GP04")


def _restyle_model_node(node: ET.Element) -> None:
    for element in node.iter():
        if element.tag in {
            q("line"),
            q("path"),
            q("rect"),
            q("circle"),
            q("polygon"),
            q("polyline"),
        }:
            element.set("vector-effect", "non-scaling-stroke")
        if element.tag == q("rect"):
            css_class = element.get("class", "")
            fills = {
                "wall-layer new-gypsum-board": "url(#gp04-new-board)",
                "wall-layer reclaimed-gypsum-board": "url(#gp04-reclaimed-board)",
                "wall-layer metal-stud-frame-with-glass-wool-infill": (
                    "url(#gp04-insulated-frame)"
                ),
                "wall-layer clear-air-cavity": "url(#gp04-air-cavity)",
            }
            if css_class in fills:
                element.set("fill", fills[css_class])
                element.set("stroke", "#172A32")
                element.set("stroke-width", "1.2")
        elif element.tag == q("line"):
            if element.get("stroke", "").lower() == "#2e7252":
                element.set("stroke", "#39765A")
                element.set("opacity", ".35")
            elif element.get("stroke", "").lower() == "#168aa3":
                element.set("stroke", "#1D7480")
        elif element.tag == q("text"):
            element.set("font-family", "Inter, IBM Plex Sans, Liberation Sans, Arial, sans-serif")
            element.set("data-source-font-size", element.get("font-size", ""))
            element.set("font-size", "9")
            if element.get("fill", "").lower() == "#168aa3":
                element.set("fill", "#1D7480")
            else:
                element.set("fill", "#172A32")


def _copy_build_up(
    parent: ET.Element,
    children: list[ET.Element],
    *,
    source_range: range,
    wall_id: str,
    transform: str,
) -> ET.Element:
    group = ET.SubElement(
        parent,
        q("g"),
        {
            "id": f"model-{wall_id.lower()}",
            "data-model-id": wall_id,
            "data-source-range": f"{source_range.start}:{source_range.stop}",
            "transform": transform,
        },
    )
    for source_index in source_range:
        node = copy.deepcopy(children[source_index])
        node.set("data-source-index", str(source_index))
        node.set("data-model-id", wall_id)
        _restyle_model_node(node)
        group.append(node)
    return group


def _panel(
    parent: ET.Element,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    css_class: str = "panel-rule",
) -> None:
    ET.SubElement(
        parent,
        q("rect"),
        {
            "x": f"{x:g}",
            "y": f"{y:g}",
            "width": f"{width:g}",
            "height": f"{height:g}",
            "rx": "5",
            "fill": "#FFFDFA",
            "class": css_class,
        },
    )


def _panel_heading(parent: ET.Element, x: float, y: float, value: str, width: float) -> None:
    add_text(parent, x, y, value, size=12.5, css_class="new-title")
    ET.SubElement(
        parent,
        q("line"),
        {
            "x1": f"{x:g}",
            "y1": f"{y + 12:g}",
            "x2": f"{x + width:g}",
            "y2": f"{y + 12:g}",
            "class": "panel-rule",
        },
    )


def _add_swatch(parent: ET.Element, x: float, y: float, pattern: str) -> None:
    ET.SubElement(
        parent,
        q("rect"),
        {
            "x": f"{x:g}",
            "y": f"{y - 12:g}",
            "width": "16",
            "height": "16",
            "fill": f"url(#gp04-{pattern})",
            "stroke": "#172A32",
            "stroke-width": "1",
        },
    )


def _add_key_rows(
    parent: ET.Element,
    *,
    x: float,
    y: float,
    wall_id: str,
    spacing: float,
) -> None:
    add_text(parent, x, y, wall_id, size=10.5, css_class="new-eyebrow")
    for index, (key, label, pattern) in enumerate(LAYER_KEYS[wall_id]):
        row_y = y + 27 + index * spacing
        _add_swatch(parent, x, row_y, pattern)
        add_text(parent, x + 24, row_y, key, size=9.8, css_class="key-tag")
        add_text(parent, x + 43, row_y, label, size=9.8, css_class="new-body")


def build_svg(source: Path = SOURCE) -> ET.ElementTree:
    source_root = ET.parse(source).getroot()
    children = list(source_root)
    _validate_source(children)
    source_metadata = json.loads(source_root.findtext(q("metadata"), default="{}"))

    root = create_document(
        title_id="gp04-title",
        desc_id="gp04-desc",
        accessible_title="P2 differentiated wall-family readability pilot GP04",
        description=(
            "Presentation-only pilot of the D-080 P2 wall family. The controlled R22 "
            "P2-W01A and P2-W01B build-up geometry is copied without coordinate changes. "
            "All eight 90, 150, 200 and 230 millimetre coordination types are retained, "
            "with no acoustic, fire, structural, thermal or moisture rating claimed."
        ),
        sheet_id="DH-ARQ-DET-003",
        revision="GP04",
        status="graphic-pilot-not-current",
        metadata={
            "construction_authority": False,
            "date": "2026-08-21",
            "decision_ids": ["D-080"],
            "acoustic_rating_claimed": False,
            "fire_rating_claimed": False,
            "model_sha256": source_metadata["model_sha256"],
            "pilot": "GP04",
            "rating_claimed": False,
            "structural_rating_claimed": False,
            "thermal_rating_claimed": False,
            "moisture_rating_claimed": False,
            "sheet": "DH-ARQ-DET-003",
            "source": source.relative_to(ROOT).as_posix(),
            "source_revision": "DET-003-R22 / 0.3-draft-25-P2",
            "source_sha256": sha256(source),
            "status": "presentation-only graphic pilot; not current; not for construction",
            "wall_types": [row[0] for row in SCHEDULE_ROWS],
        },
    )
    _add_patterns(root)

    background = ET.SubElement(root, q("g"), {"id": "layer-background", "data-layer": "background"})
    ET.SubElement(background, q("rect"), {"width": "1684", "height": "1191", "fill": "#F4F0E7"})
    _panel(background, 36, 116, 930, 594)
    _panel(background, 982, 116, 666, 594)
    _panel(background, 36, 726, 500, 282)
    _panel(background, 552, 726, 500, 282)
    _panel(background, 1068, 726, 580, 282, css_class="status-open-box")

    model = ET.SubElement(
        root,
        q("g"),
        {"id": "layer-model", "data-layer": "controlled-build-up-geometry"},
    )
    _copy_build_up(
        model,
        children,
        source_range=W01A_SOURCE_RANGE,
        wall_id="P2-W01A",
        transform="translate(-88.4 -105) scale(1.32)",
    )
    _copy_build_up(
        model,
        children,
        source_range=W01B_SOURCE_RANGE,
        wall_id="P2-W01B",
        transform="translate(-42.4 -100.4) scale(1.12)",
    )

    annotations = ET.SubElement(
        root,
        q("g"),
        {
            "id": "layer-annotations",
            "data-layer": "schedule-and-layer-keys",
            "data-contrast-bg": "#FFFDFA",
        },
    )
    _panel_heading(
        annotations,
        56,
        145,
        "01 · CONTROLLED REFERENCE BUILD-UPS",
        890,
    )
    add_text(
        annotations,
        56,
        184,
        "P2-W01A · 90 mm · SAME-SUITE DRY WALL",
        size=12,
        css_class="new-eyebrow",
    )
    add_text(
        annotations,
        56,
        205,
        "12.5 + 64 + 12.5 = 89 mm illustrative sum · no rating claimed",
        size=9.8,
        css_class="new-muted",
    )
    add_text(annotations, 500, 235, "LOW-RISK DUTY ONLY", size=11, css_class="new-open")
    add_text(annotations, 500, 268, "90 mm nominal", size=17, css_class="new-title")
    add_wrapped_text(
        annotations,
        500,
        296,
        "Use only for dry boundaries within one suite. Do not use at suite-to-suite or "
        "suite-to-common privacy boundaries.",
        width_chars=55,
        size=9.8,
        line_height=12.5,
    )
    add_text(
        annotations,
        56,
        462,
        "P2-W01B · 200 mm · SUITE / COMMON SEPARATION",
        size=12,
        css_class="new-eyebrow",
    )
    add_text(
        annotations,
        56,
        483,
        "12.5 + 12.5 + 64 + 20 clear + 64 + 12.5 + 12.5 = 198 mm illustrative sum",
        size=9.8,
        css_class="new-muted",
    )
    add_text(annotations, 800, 542, "PRIVACY DUTY", size=10.5, css_class="new-eyebrow")
    add_text(annotations, 800, 574, "200 mm", size=17, css_class="new-title")
    add_wrapped_text(
        annotations,
        800,
        603,
        "Twin independent insulated frames. No STC/Rw or fire rating claimed.",
        width_chars=24,
        size=9.8,
        line_height=12,
    )

    _panel_heading(annotations, 1002, 145, "COORDINATION SCHEDULE", 626)
    add_text(annotations, 1002, 186, "TYPE", size=9.8, css_class="new-muted", weight=700)
    add_text(annotations, 1118, 186, "NOMINAL", size=9.8, css_class="new-muted", weight=700)
    add_text(annotations, 1225, 186, "DUTY / LIMIT", size=9.8, css_class="new-muted", weight=700)
    for index, (wall_id, nominal, duty) in enumerate(SCHEDULE_ROWS):
        top = 199 + index * 56
        row_colour = "#EEF2F0" if index % 2 == 0 else "#F8F6F0"
        row = ET.SubElement(annotations, q("g"), {"data-contrast-bg": row_colour})
        ET.SubElement(
            row,
            q("rect"),
            {
                "x": "1002",
                "y": f"{top:g}",
                "width": "626",
                "height": "48",
                "fill": row_colour,
            },
        )
        baseline = top + 22
        add_text(row, 1014, baseline, wall_id, size=10, css_class="new-eyebrow")
        add_text(row, 1128, baseline, nominal, size=10, css_class="new-title")
        add_wrapped_text(
            row,
            1225,
            baseline,
            duty,
            width_chars=49,
            size=9.8,
            line_height=11.5,
        )
    add_text(
        annotations,
        1002,
        681,
        "Nominal schematic coordination zones · local increases and selected systems remain open.",
        size=9.8,
        css_class="new-muted",
    )

    _panel_heading(annotations, 56, 757, "REDUNDANT LAYER KEYS", 460)
    _add_key_rows(annotations, x=56, y=790, wall_id="P2-W01A", spacing=36)
    _add_key_rows(annotations, x=258, y=790, wall_id="P2-W01B", spacing=25.6)
    add_text(
        annotations,
        56,
        989,
        "Numbering follows room-side → room-side model order.",
        size=9.8,
        css_class="new-muted",
    )

    status = ET.SubElement(
        root,
        q("g"),
        {"id": "layer-status", "data-layer": "authority-and-open-gates"},
    )
    control_status = ET.SubElement(status, q("g"), {"data-contrast-bg": "#FFFDFA"})
    _panel_heading(control_status, 572, 757, "D-080 · CONTROL / ECONOMY", 460)
    add_text(
        control_status,
        572,
        799,
        "ACTIVE SCHEMATIC COORDINATION",
        size=11,
        css_class="new-eyebrow",
    )
    paragraphs = (
        "The 90 mm wall is restricted to low-risk same-suite boundaries; privacy "
        "boundaries keep twin independent frames.",
        "Nominal thickness is a design-control value, not a product order or construction "
        "dimension.",
        "Wet, hot-side, protected-core and exterior types remain subject to professional "
        "assembly selection.",
    )
    y = 829.0
    for paragraph in paragraphs:
        _, bottom = add_wrapped_text(
            control_status,
            572,
            y,
            paragraph,
            width_chars=66,
            size=9.7,
            line_height=12.3,
        )
        y = bottom + 15
    add_text(
        control_status,
        572,
        986,
        "No product selected · no saving booked · no target change",
        size=9.7,
        css_class="new-conflict",
    )

    open_status = ET.SubElement(status, q("g"), {"data-contrast-bg": "#FBF0D9"})
    _panel_heading(open_status, 1088, 757, "OPEN · DO NOT FREEZE", 540)
    gates = (
        "STC/Rw, fire, thermal and moisture performance",
        "tested local assemblies, acoustic doors and seals",
        "head tracks, anchors, bracing and steel interfaces",
        "plumbing stacks, local W02 depth and shaft access",
        "wet, sauna/hot-side and protected-core details",
        "facade core, wind, drainage and hygrothermal design",
        "mock-ups, products, measured quantities and quotations",
    )
    y = 799
    for gate in gates:
        add_text(open_status, 1088, y, "•", size=10, css_class="new-open")
        add_text(open_status, 1106, y, gate, size=9.7, css_class="new-body")
        y += 26
    add_text(
        open_status,
        1088,
        986,
        "Thickness alone proves no performance rating.",
        size=9.7,
        css_class="new-conflict",
    )

    add_header(
        root,
        eyebrow="GRAPHIC PILOT 04 · PRESENTATION ONLY",
        title="P2 WALL FAMILY · THICKNESS BY DUTY",
        subtitle=(
            "Same R22 values · enlarged controlled build-ups and schedule · numbered layer "
            "keys · pattern + text coding"
        ),
        sheet_id="DH-ARQ-DET-003",
        issue_label="GP04 · NOT CURRENT",
    )
    add_footer(
        root,
        authority_sentence=(
            "Graphic review only. This file is not the current drawing and creates no design, "
            "procurement or construction authority."
        ),
        source_sentence=(
            "Source: DET-003-R22 / 0.3-draft-25-P2 · Decision basis: D-080 · Controlled "
            "build-up source-space geometry preserved."
        ),
        gates_sentence=(
            "Open gates: tested systems · fire/acoustics · wet/sauna · structure/wind · "
            "building physics · products/mock-ups · measured cost"
        ),
        date="2026-08-21",
    )
    register_text_regions(root, LAYOUT_REGIONS)
    return ET.ElementTree(root)


def write_outputs(source: Path = SOURCE, output: Path = OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    tree = build_svg(source)
    ET.indent(tree, space="  ")
    tree.write(output, encoding="utf-8", xml_declaration=True)
    manifest = {
        "construction_authority": False,
        "date": "2026-08-21",
        "decision_ids": ["D-080"],
        "generator": "dreamhouse/svg/pilot_p2_wall_family.py",
        "output": output.name,
        "output_sha256": sha256(output),
        "pilot": "GP04",
        "sheet": "DH-ARQ-DET-003",
        "source": source.relative_to(ROOT).as_posix(),
        "source_revision": "DET-003-R22 / 0.3-draft-25-P2",
        "source_sha256": sha256(source),
        "status": "presentation-only graphic pilot; not current; not for construction",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    write_outputs(args.source, args.output)


if __name__ == "__main__":
    main()

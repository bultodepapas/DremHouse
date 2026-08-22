"""Build the presentation-only transverse roof-section SVG pilot GP03.

The technical content from the current R06 section is copied without coordinate changes
and placed in one uniform sheet transform.  Editorial text is translated under D-044;
the output remains not current and has no construction authority.
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
    add_level_marker,
    add_text,
    add_wrapped_text,
    create_document,
    q,
    sha256,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "planos/actual/DH-ARQ-SEC-002_CURRENT-TRANSVERSE.svg"
OUTPUT_DIR = ROOT / "planos/piloto_grafico_v0.1"
OUTPUT = OUTPUT_DIR / "DH-ARQ-SEC-002-GP03_TRANSVERSE-SECTION-READABILITY-PILOT.svg"
MANIFEST = OUTPUT_DIR / "DH-ARQ-SEC-002-GP03.manifest.json"

LAYOUT_REGIONS = (
    SHEET_HEADER_REGION,
    LayoutRegion.with_inset("main", Bounds(36, 116, 1612, 674), 8),
    LayoutRegion.with_inset("provisional", Bounds(36, 806, 500, 202), 8),
    LayoutRegion.with_inset("vertical", Bounds(552, 806, 500, 202), 8),
    LayoutRegion.with_inset("open", Bounds(1068, 806, 580, 202), 8),
    SHEET_FOOTER_REGION,
)

SOURCE_CONTENT_START = 2
SOURCE_CONTENT_END = 13


PALETTE = {
    "#20292e": "#172A32",
    "#172126": "#172A32",
    "#566269": "#536168",
    "#8f6f5a": "#74543C",
}


TRANSLATIONS = {
    "P2 PRIVADO · cielo horizontal 3,00–3,10 m + plenum variable": (
        "PRIVATE P2 ZONE · horizontal ceiling not shown · 3.00–3.10 m + variable plenum"
    ),
    "PB BAJO P2 · altura libre objetivo 3,05–3,20 m": (
        "PB BELOW P2 · target clear height 3.05–3.20 m"
    ),
    "LADO BAJO ≈ 7,20 m": "LOW SIDE · approx. +7.20 m",
    "LADO ALTO ≈ 7,80 m": "HIGH SIDE · approx. +7.80 m",
    "18,00 m · sentido bajo/alto reversible según predio y drenaje": (
        "18.00 m · low/high direction reversible pending site and drainage"
    ),
}


MODEL_IDS_BY_INDEX = {
    2: "PB-REFERENCE-LEVEL",
    3: "ROOF-SINGLE-PLANE",
    4: "ENV-LOW-SIDE",
    5: "ENV-HIGH-SIDE",
    6: "P2-FLOOR-DATUM",
    7: "P2-VERTICAL-ZONE-NOTE",
    8: "PB-CLEAR-HEIGHT-NOTE",
    9: "ROOF-LOW-EAVE-DATUM",
    10: "ROOF-HIGH-EAVE-DATUM",
    11: "HALL-WIDTH-DIMENSION",
    12: "HALL-WIDTH-DIMENSION",
}


def _text_value(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _set_text(element: ET.Element, value: str) -> None:
    for child in list(element):
        element.remove(child)
    element.text = value


def _restyle_source_node(node: ET.Element) -> None:
    for element in node.iter():
        for attribute in ("fill", "stroke"):
            value = element.get(attribute)
            if value and value.lower() in PALETTE:
                element.set(attribute, PALETTE[value.lower()])

        if element.tag != q("text"):
            continue
        label = _text_value(element)
        if label in TRANSLATIONS:
            _set_text(element, TRANSLATIONS[label])
            element.set("data-source-label", label)
        if label.startswith(("P2 PRIVADO", "PB BAJO P2")):
            element.set("font-size", "10.5")
            element.set("font-weight", "600")
            element.set("data-text-role", "primary")
        elif label.startswith(("LADO BAJO", "LADO ALTO")):
            element.set("font-size", "9.6")
            element.set("font-weight", "700")
            element.set("data-text-role", "level")
        elif label.startswith("18,00 m"):
            element.set("font-size", "9.6")
            element.set("data-text-role", "dimension")


def _panel(
    parent: ET.Element,
    x: float,
    width: float,
    *,
    css_class: str = "panel-rule",
) -> None:
    ET.SubElement(
        parent,
        q("rect"),
        {
            "x": f"{x:g}",
            "y": "806",
            "width": f"{width:g}",
            "height": "202",
            "rx": "5",
            "fill": "#FFFDFA",
            "class": css_class,
        },
    )


def build_svg(source: Path = SOURCE) -> ET.ElementTree:
    source_root = ET.parse(source).getroot()
    source_children = list(source_root)
    if len(source_children) != 2 or source_children[1].tag != q("g"):
        raise ValueError("Unexpected transverse-section source structure; review GP03 adapter")
    source_group_children = list(source_children[1])
    if len(source_group_children) != 15:
        raise ValueError("Unexpected transverse-section content count; review GP03 adapter")

    root = create_document(
        title_id="gp03-title",
        desc_id="gp03-desc",
        accessible_title="Transverse mono-pitch roof-section readability pilot GP03",
        description=(
            "Presentation-only pilot of the transverse section below P2. The R06 baseline, "
            "single roof plane, side walls, P2 floor datum, hall width and approximate levels "
            "are copied without coordinate changes. D-039 remains a provisional design-control "
            "value and final direction, drainage, structure and roof system remain open."
        ),
        sheet_id="DH-ARQ-SEC-002",
        revision="GP03",
        status="graphic-pilot-not-current",
        metadata={
            "construction_authority": False,
            "date": "2026-08-21",
            "decision_ids": ["D-039", "D-044"],
            "pilot": "GP03",
            "sheet": "DH-ARQ-SEC-002",
            "source": source.relative_to(ROOT).as_posix(),
            "source_revision": "SEC-002-R06 / 0.3-borrador-07-CUBIERTA",
            "source_sha256": sha256(source),
            "status": "presentation-only graphic pilot; not current; not for construction",
        },
    )

    background = ET.SubElement(root, q("g"), {"id": "layer-background", "data-layer": "background"})
    ET.SubElement(background, q("rect"), {"width": "1684", "height": "1191", "fill": "#F4F0E7"})
    ET.SubElement(
        background,
        q("rect"),
        {
            "x": "36",
            "y": "116",
            "width": "1612",
            "height": "674",
            "rx": "5",
            "fill": "#FFFDFA",
            "class": "panel-rule",
        },
    )
    _panel(background, 36, 500, css_class="status-hypothesis-box")
    _panel(background, 552, 500)
    _panel(background, 1068, 580, css_class="status-open-box")

    model = ET.SubElement(
        root,
        q("g"),
        {
            "id": "layer-model",
            "data-layer": "model-geometry-and-annotations",
            "transform": "translate(0 -238) scale(1.6)",
            "font-family": "Inter, IBM Plex Sans, Liberation Sans, Arial, sans-serif",
            "fill": "#172A32",
        },
    )
    for source_index, source_node in enumerate(
        source_group_children[SOURCE_CONTENT_START:SOURCE_CONTENT_END],
        start=SOURCE_CONTENT_START,
    ):
        node = copy.deepcopy(source_node)
        node.set("data-source-index", str(source_index))
        node.set("data-model-id", MODEL_IDS_BY_INDEX[source_index])
        _restyle_source_node(node)
        model.append(node)

    annotations = ET.SubElement(
        root,
        q("g"),
        {
            "id": "layer-annotations",
            "data-layer": "levels-and-evidence",
            "data-contrast-bg": "#FFFDFA",
        },
    )
    add_level_marker(
        annotations,
        target_x=272,
        y=682,
        label_x=92,
        label="PB reference · +0.00",
        relates_to="PB-REFERENCE-LEVEL",
    )
    add_level_marker(
        annotations,
        target_x=272,
        y=426.6,
        label_x=92,
        label="P2 finished floor · approx. +3.80 m",
        relates_to="P2-FLOOR-DATUM",
    )

    status = ET.SubElement(
        root,
        q("g"),
        {"id": "layer-status", "data-layer": "status-and-open-gates"},
    )
    provisional_status = ET.SubElement(status, q("g"), {"data-contrast-bg": "#F0ECF6"})
    add_text(
        provisional_status,
        56,
        838,
        "ACTIVE PROVISIONAL DCV · D-039",
        size=12.5,
        css_class="new-hypothesis",
    )
    add_wrapped_text(
        provisional_status,
        56,
        868,
        "One continuous mono-pitch exterior roof plane; no ridge or secondary roof form.",
        width_chars=63,
        size=10,
        line_height=13,
    )
    add_text(provisional_status, 56, 912, "Rise", size=10, css_class="new-eyebrow")
    add_text(
        provisional_status,
        138,
        912,
        "approx. 0.60 m across 18.00 m = 3.33%",
        size=10,
    )
    add_text(provisional_status, 56, 940, "Eaves", size=10, css_class="new-eyebrow")
    add_text(
        provisional_status,
        138,
        940,
        "low approx. +7.20 m · high approx. +7.80 m",
        size=10,
    )
    add_wrapped_text(
        provisional_status,
        56,
        970,
        "These values coordinate schematic design; they are not contractual dimensions or a "
        "selected roof system.",
        width_chars=67,
        size=9.8,
        line_height=12.5,
        css_class="new-muted",
    )

    vertical_status = ET.SubElement(status, q("g"), {"data-contrast-bg": "#FFFDFA"})
    add_text(vertical_status, 572, 838, "VERTICAL READING", size=12.5, css_class="new-title")
    vertical_items = [
        ("PB", "reference level +0.00"),
        ("P2", "finished floor approx. +3.80 m"),
        ("PB clear", "target 3.05–3.20 m below P2"),
        ("P2 ceiling", "horizontal 3.00–3.10 m + variable plenum"),
    ]
    y = 872
    for label, description in vertical_items:
        add_text(vertical_status, 572, y, label, size=10, css_class="new-eyebrow")
        add_text(vertical_status, 690, y, description, size=10, css_class="new-body")
        y += 31
    add_wrapped_text(
        vertical_status,
        572,
        985,
        "The section is diagrammatic: no assembly build-up, member size or ceiling detail is "
        "selected.",
        width_chars=62,
        size=9.8,
        line_height=12.5,
        css_class="new-muted",
    )

    open_status = ET.SubElement(status, q("g"), {"data-contrast-bg": "#FBF0D9"})
    add_text(
        open_status,
        1088,
        838,
        "OPEN · DO NOT FREEZE",
        size=12.5,
        css_class="new-open",
    )
    gates = [
        "Side A / Side B low-high assignment pending site and orientation",
        "Final slope pending selected panel, structure, tolerances and warranty",
        "Rainfall, gutter, overflow, downpipe and discharge design",
        "Wind, uplift, fasteners, penetrations and maintenance access",
        "Insulation, condensation, thermal bridges and ceiling interfaces",
    ]
    y = 868
    for gate in gates:
        add_text(open_status, 1088, y, "•", size=10, css_class="new-open")
        _, bottom = add_wrapped_text(
            open_status,
            1106,
            y,
            gate,
            width_chars=64,
            size=10,
            line_height=12.5,
        )
        y = bottom + 8

    add_header(
        root,
        eyebrow="GRAPHIC PILOT 03 · PRESENTATION ONLY",
        title="TRANSVERSE SECTION · MONO-PITCH ROOF",
        subtitle=(
            "Same R06 geometry and values · repaired scalable viewport · English editorial "
            "layer · provisional/open states"
        ),
        sheet_id="DH-ARQ-SEC-002",
        issue_label="GP03 · NOT CURRENT",
    )
    add_footer(
        root,
        authority_sentence=(
            "Graphic review only. This file is not the current drawing and creates no design, "
            "procurement or construction authority."
        ),
        source_sentence=(
            "Source: SEC-002-R06 / 0.3-borrador-07-CUBIERTA · Decision basis: D-039 / D-044 "
            "· Source-space geometry preserved."
        ),
        gates_sentence=(
            "Open gates: site/orientation · roof direction · structure/system · rainfall/drainage "
            "· wind/uplift · building physics · product/cost"
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
        "decision_ids": ["D-039", "D-044"],
        "generator": "dreamhouse/svg/pilot_transverse_section.py",
        "output": output.name,
        "output_sha256": sha256(output),
        "pilot": "GP03",
        "sheet": "DH-ARQ-SEC-002",
        "source": source.relative_to(ROOT).as_posix(),
        "source_revision": "SEC-002-R06 / 0.3-borrador-07-CUBIERTA",
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

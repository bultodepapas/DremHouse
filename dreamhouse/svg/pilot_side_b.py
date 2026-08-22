"""Build the presentation-only Side B elevation SVG pilot GP02.

The current R10 elevation geometry is copied without coordinate changes and placed in a
single sheet transform.  Only presentation attributes, direct labels and explanatory
panels change.  The output is not current and has no construction authority.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from xml.etree import ElementTree as ET

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
SOURCE = ROOT / "planos/actual/DH-ARQ-ELE-004_CURRENT-SIDE-B.svg"
OUTPUT_DIR = ROOT / "planos/piloto_grafico_v0.1"
OUTPUT = OUTPUT_DIR / "DH-ARQ-ELE-004-GP02_SIDE-B-READABILITY-PILOT.svg"
MANIFEST = OUTPUT_DIR / "DH-ARQ-ELE-004-GP02.manifest.json"

SOURCE_CONTENT_START = 3
SOURCE_CONTENT_END = 63


PALETTE = {
    "#aeb5b6": "#C7CDCB",
    "#90999b": "#9AA5A4",
    "#172126": "#172A32",
    "#243238": "#172A32",
    "#59666a": "#536168",
    "#59676c": "#536168",
    "#687579": "#68777A",
    "#345e69": "#2F6570",
    "#4f7078": "#376C77",
    "#426671": "#356A75",
    "#eff5f5": "#FFFDFA",
    "#536166": "#536168",
    "#d6d2ca": "#E4E0D7",
    "#858b89": "#77817F",
    "#5c4229": "#172A32",
}


DIRECT_LABELS = {
    "RC / AIRCRAFT WORKSHOP WINDOW": {
        "text": "GLZ-RC · 6 × 1.20 m MODULES",
        "size": "9.6",
    },
    "7.20 × 2.90 m · sill 0.90 m": {
        "text": "7.20 × 2.90 m · sill +0.90 m",
        "size": "9.6",
    },
    "WORKSTATION 2 WINDOW": {
        "text": "GLZ-WS-B · 3 MODULES",
        "size": "9.2",
        "y": "548",
        "fill": "#172A32",
    },
    "3.00 × 1.80 m · sill 0.75 m": {
        "text": "3.00 × 1.80 m · sill +0.75 m",
        "size": "8.6",
        "y": "558.5",
        "fill": "#172A32",
    },
    "INTEGRATED STEEL / TIMBER WORKTOP": {
        "text": "PB-WS-B",
        "size": "8.6",
        "y": "638",
        "fill": "#172A32",
    },
    "CHILD 2 BEDROOM · NEAR FLOOR TO CEILING": {
        "text": "W-H2 · 3 × 1.20",
        "size": "9.6",
    },
    "GUEST BEDROOM · NEAR FLOOR TO CEILING": {
        "text": "W-G · 3 × 1.20",
        "size": "9.6",
        "x": "1080",
    },
}


MODEL_IDS_BY_INDEX = {
    **{index: "ENV-SIDE-B" for index in range(3, 10)},
    **{index: "GLZ-RC" for index in range(10, 21)},
    **{index: "GLZ-WS-B" for index in range(21, 38)},
    **{index: "W-H2" for index in range(38, 41)},
    **{index: "W-G" for index in range(41, 44)},
    **{index: "STRUCTURAL-GRID-REFERENCE" for index in range(44, 50)},
    **{index: "EXTERNAL-LEVEL-REFERENCE" for index in range(50, 52)},
    **{index: "LONGITUDINAL-DIMENSIONS" for index in range(52, 63)},
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
        direct = DIRECT_LABELS.get(label)
        if direct:
            _set_text(element, direct["text"])
            element.set("font-size", direct["size"])
            element.set("font-weight", "700")
            element.set("data-source-label", label)
            element.set("data-text-role", "opening")
            if "y" in direct:
                element.set("y", direct["y"])
            if "x" in direct:
                element.set("x", direct["x"])
            if "fill" in direct:
                element.set("fill", direct["fill"])
            continue

        if label == "REAR UPPER FLOOR · 15.00 m":
            _set_text(element, "P2 · 15.00 m")
            element.set("font-size", "9.6")
            element.set("x", "978")
            element.set("data-source-label", label)
            element.set("data-text-role", "primary")
        elif label in {
            "HIGH EAVE ≈ 7.80 m",
            "EXTERNAL LEVEL / PERIMETER DRAINAGE PENDING SURVEY",
        }:
            element.set("font-size", "9.6")
            element.set("data-text-role", "primary")
        elif label == "36.00 m":
            element.set("font-size", "11.5")
            element.set("data-text-role", "dimension")
        elif label.endswith(("technical", "monumental", "domestic", "core")):
            element.set("font-size", "9.6")
            element.set("data-text-role", "dimension")


def _panel(parent: ET.Element, x: float, width: float, *, css_class: str = "panel-rule") -> None:
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
    children = list(source_root)
    if len(children) != 66 or children[2].tag != q("defs"):
        raise ValueError("Unexpected Side B source structure; review the GP02 adapter")

    root = create_document(
        title_id="gp02-title",
        desc_id="gp02-desc",
        accessible_title="Side B elevation readability pilot GP02",
        description=(
            "Presentation-only pilot of the Side B facade elevation. The current R10 envelope, "
            "openings, levels and dimensions are copied without coordinate changes. Adopted "
            "D-083 openings, the excluded dining-window study and open professional gates are "
            "identified in separate evidence panels."
        ),
        sheet_id="DH-ARQ-ELE-004",
        revision="GP02",
        status="graphic-pilot-not-current",
        metadata={
            "construction_authority": False,
            "date": "2026-08-21",
            "decision_ids": ["D-083"],
            "pilot": "GP02",
            "sheet": "DH-ARQ-ELE-004",
            "source": source.relative_to(ROOT).as_posix(),
            "source_revision": "ELE-004-R10 / 0.3-draft-37-PB",
            "source_sha256": sha256(source),
            "status": "presentation-only graphic pilot; not current; not for construction",
        },
    )
    root.append(copy.deepcopy(children[2]))

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
    _panel(background, 36, 760)
    _panel(background, 812, 390, css_class="status-hypothesis-box")
    _panel(background, 1218, 430, css_class="status-open-box")

    model = ET.SubElement(
        root,
        q("g"),
        {
            "id": "layer-model",
            "data-layer": "model-geometry-and-annotations",
            "transform": "translate(14 -268) scale(1.2)",
        },
    )
    for source_index, source_node in enumerate(
        children[SOURCE_CONTENT_START:SOURCE_CONTENT_END],
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
            "data-layer": "annotations-and-evidence",
            "data-contrast-bg": "#FFFDFA",
        },
    )
    add_text(
        annotations,
        56,
        838,
        "ADOPTED SCHEMATIC OPENINGS · D-083",
        size=12.5,
        css_class="new-title",
    )
    rows = [
        ("GLZ-RC", "7.20 × 2.90 m · sill +0.90 m · 6 modules · RC / aircraft workshop"),
        ("GLZ-WS-B", "3.00 × 1.80 m · sill +0.75 m · 3 modules · workstation datum"),
        ("W-H2", "3.60 × 2.90 m · sill +0.05 m · head +2.95 m · 3 modules"),
        ("W-G", "3.60 × 2.90 m · sill +0.05 m · head +2.95 m · 3 modules"),
    ]
    y = 868
    for opening_id, description in rows:
        add_text(annotations, 56, y, opening_id, size=10.2, css_class="new-eyebrow")
        add_text(annotations, 160, y, description, size=10, css_class="new-body")
        y += 32
    add_text(
        annotations,
        56,
        991,
        "PB-WS-B worktop +0.75 m · window/worktop structures remain independent across a "
        "maintainable 30–50 mm gap.",
        size=9.8,
        css_class="new-muted",
    )

    status = ET.SubElement(
        root,
        q("g"),
        {"id": "layer-status", "data-layer": "status-and-conflicts"},
    )
    excluded_status = ET.SubElement(status, q("g"), {"data-contrast-bg": "#F0ECF6"})
    add_text(excluded_status, 832, 838, "NOT ADOPTED", size=12.5, css_class="new-hypothesis")
    add_text(excluded_status, 832, 868, "GLZ-DINING-STUDY-B", size=11, css_class="new-title")
    add_text(
        excluded_status,
        832,
        892,
        "4.80 × 1.80 m · sill +0.75 m",
        size=10,
        css_class="new-body",
    )
    add_wrapped_text(
        excluded_status,
        832,
        922,
        "Excluded from the façade geometry, active opening quantities and pricing. The "
        "dining bay remains solid in this pilot.",
        width_chars=49,
        size=10,
        line_height=13,
        css_class="new-muted",
    )

    open_status = ET.SubElement(status, q("g"), {"data-contrast-bg": "#FBF0D9"})
    add_text(
        open_status,
        1238,
        838,
        "OPEN · DO NOT FREEZE",
        size=12.5,
        css_class="new-open",
    )
    gates = [
        "Site and cardinal orientation",
        "Solar control, glare, views and privacy",
        "Safe glazing, fall protection and operability",
        "Headers, jambs, girts, anchors and wind",
        "Thermal bridges, condensation and drainage",
        "Selected products, quantities and local cost",
    ]
    y = 868
    for gate in gates:
        add_text(open_status, 1238, y, "•", size=10, css_class="new-open")
        add_text(open_status, 1256, y, gate, size=10, css_class="new-body")
        y += 24

    add_header(
        root,
        eyebrow="GRAPHIC PILOT 02 · PRESENTATION ONLY",
        title="SIDE B · OPENING COORDINATION",
        subtitle=(
            "Same R10 geometry and values · larger elevation · direct IDs · adopted / excluded "
            "/ open states"
        ),
        sheet_id="DH-ARQ-ELE-004",
        issue_label="GP02 · NOT CURRENT",
    )
    add_footer(
        root,
        authority_sentence=(
            "Graphic review only. This file is not the current drawing and creates no design, "
            "procurement or construction authority."
        ),
        source_sentence=(
            "Source: ELE-004-R10 / 0.3-draft-37-PB · Decision basis: D-083 · Source-space "
            "geometry and displayed dimensions preserved."
        ),
        gates_sentence=(
            "Open gates: site/orientation · solar/privacy · structure/wind · safe glazing/fall · "
            "building physics/drainage · products/cost"
        ),
        date="2026-08-21",
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
        "decision_ids": ["D-083"],
        "generator": "dreamhouse/svg/pilot_side_b.py",
        "output": output.name,
        "output_sha256": sha256(output),
        "pilot": "GP02",
        "sheet": "DH-ARQ-ELE-004",
        "source": source.relative_to(ROOT).as_posix(),
        "source_revision": "ELE-004-R10 / 0.3-draft-37-PB",
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

"""Build the presentation-only E1 structural-synthesis SVG pilot GP05.

The six calculation-linked technical diagrams from the current R01 sheet are copied
without coordinate changes.  Text, evidence rows, panel frames and authority hierarchy
are recomposed at the shared preview-size floor.  The output remains fail-closed,
not current and not for construction.
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
from dreamhouse.svg.theme import colour as theme_colour


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "planos/actual/DH-EST-E1-001_CURRENT-SYNTHESIS.svg"
OUTPUT_DIR = ROOT / "planos/piloto_grafico_v0.1"
OUTPUT = OUTPUT_DIR / "DH-EST-E1-001-GP05_STRUCTURAL-EVIDENCE-READABILITY-PILOT.svg"
MANIFEST = OUTPUT_DIR / "DH-EST-E1-001-GP05.manifest.json"

SOURCE_GROUPS = {
    "integrated-plan": 15,
    "reference-truss": 38,
    "connection-detail": 80,
    "foundation-detail": 84,
    "erection-detail": 88,
    "fire-detail": 92,
}

MODEL_TRANSFORMS = {
    "erection-detail": "translate(0 -10)",
}

EVIDENCE_ROWS = (
    ("HSS LOCAL / BIAXIAL", "PASS*", "interaction 0.653", "BLOCKED"),
    ("CHORD LOCAL BENDING", "PASS*", "12.51 kN·m / 0.369", "BLOCKED"),
    ("MEMBER SECOND ORDER", "PASS*", "B1 1.255", "BLOCKED"),
    ("GENERIC JOINT PARTS", "PASS*", "ratio 0.387; HSS wall open", "BLOCKED"),
    ("TRIAL LATERAL BAYS", "PASS*", "63.2 kN / 0.622", "BLOCKED"),
    ("ROOF DIAPHRAGM", "DEMAND", "8.77 kN/m; deck open", "BLOCKED"),
    ("FIRE SENSITIVITY", "FAIL@550", "ratios 0.65 / 1.05 / 2.84", "BLOCKED"),
    ("ERECTION / TRANSPORT", "DEMAND", "hook 15.8 kN; ≥2 pieces", "BLOCKED"),
    ("BASE + TRIAL FOOTING", "PASS*", "qmax 37.3 kPa; plate 0.205", "BLOCKED"),
)

DETAIL_TEXT = {
    "reference-truss": (
        "ILLUSTRATIVE TRANSPORT SPLIT",
        "TOP RESTRAINT @ 1.50 m",
        "BOTTOM RESTRAINT @ 6.00 m",
        "LOADS AT PANEL POINTS",
        "18.00 m TRANSVERSE SPAN · 6 PANELS · VARIABLE DEPTH 0.99→1.80 m",
    ),
    "connection-detail": (
        "HSS CHORD",
        "6-M20 · plate 12 mm · weld 8 mm",
        "component ratio 0.387 · demand 209.8 kN",
        "HSS wall / weld access / eccentricity BLOCKED",
    ),
    "foundation-detail": (
        "≈ HEA200",
        "300×300×20",
        "2.0×2.0×0.5 m",
        "qmax 37.3 kPa · plate ratio 0.205",
        "anchors / shear / moment / geotech / RC BLOCKED",
    ),
    "erection-detail": (
        "HOOK 15.8 kN",
        "9.1 kN",
        "9.1 kN",
        "18 m requires ≥2 pieces at 12 m transport limit",
        "crane chart / lugs / splice / weather / temporary bracing BLOCKED",
    ),
    "fire-detail": (
        "400°C",
        "0.65",
        "550°C",
        "1.05",
        "700°C",
        "2.84",
        "period / scenario / section factor / tested protection BLOCKED",
        "400°C pass is sensitivity only; 550°C and 700°C fail",
    ),
}

SHAPE_TAGS = {
    q("line"),
    q("path"),
    q("polygon"),
    q("polyline"),
    q("rect"),
    q("circle"),
}


def _text_value(element: ET.Element) -> str:
    return " ".join(" ".join(piece.split()) for piece in element.itertext())


def _group_texts(group: ET.Element) -> tuple[str, ...]:
    return tuple(_text_value(text) for text in group.iter(q("text")))


def _validate_source(children: list[ET.Element]) -> dict[str, object]:
    if len(children) != 108 or children[3].tag != q("defs"):
        raise ValueError("Unexpected E1 synthesis source structure; review the GP05 adapter")

    for group_id, source_index in SOURCE_GROUPS.items():
        source_group = children[source_index]
        if source_group.tag != q("g") or source_group.get("id") != group_id:
            raise ValueError(f"E1 source group {group_id!r} moved; review the GP05 adapter")

    matrix = children[33]
    if matrix.get("id") != "evidence-gates":
        raise ValueError("E1 evidence matrix moved; review the GP05 adapter")
    matrix_text = _group_texts(matrix)
    source_rows = tuple(
        tuple(matrix_text[4 + row * 4 : 8 + row * 4])
        for row in range(len(EVIDENCE_ROWS))
    )
    if source_rows != EVIDENCE_ROWS:
        raise ValueError("E1 evidence values changed; review the GP05 editorial adapter")

    for group_id, expected in DETAIL_TEXT.items():
        actual = _group_texts(children[SOURCE_GROUPS[group_id]])
        if actual != expected:
            raise ValueError(f"E1 detail text changed in {group_id}; review GP05")

    metadata = json.loads(children[2].text or "{}")
    if metadata.get("sheet") != "DH-EST-E1-001" or metadata.get("revision") != "R01":
        raise ValueError("Unexpected E1 source metadata; review the GP05 adapter")
    if metadata.get("selection_or_construction_authority") is not False:
        raise ValueError("E1 source must remain explicitly without selection authority")
    return metadata


def _copy_source_defs(root: ET.Element, source_defs: ET.Element) -> None:
    defs = ET.SubElement(root, q("defs"), {"id": "gp05-source-symbols"})
    for child in source_defs:
        if child.tag == q("style"):
            continue
        defs.append(copy.deepcopy(child))


def _copy_geometry_group(
    parent: ET.Element,
    source_group: ET.Element,
    *,
    model_id: str,
) -> ET.Element:
    group = ET.SubElement(
        parent,
        q("g"),
        {
            "id": f"model-{model_id}",
            "data-model-id": model_id,
            "data-source-group": source_group.get("id", ""),
        },
    )
    if model_id in MODEL_TRANSFORMS:
        group.set("transform", MODEL_TRANSFORMS[model_id])
    for source_index, source_node in enumerate(source_group):
        if source_node.tag not in SHAPE_TAGS:
            continue
        node = copy.deepcopy(source_node)
        node.set("data-source-index", str(source_index))
        node.set("data-model-id", model_id)
        node.set("vector-effect", "non-scaling-stroke")
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


def _add_rotated_text(
    parent: ET.Element,
    x: float,
    y: float,
    value: str,
    *,
    size: float = 9.8,
    angle: float = -90,
    css_class: str = "new-body",
    anchor: str = "middle",
    contrast_bg: str | None = None,
) -> ET.Element:
    element = add_text(parent, x, y, value, size=size, css_class=css_class, anchor=anchor)
    element.set("transform", f"rotate({angle:g} {x:g} {y:g})")
    if contrast_bg is not None:
        element.set("data-contrast-bg", contrast_bg)
    return element


def _badge(
    parent: ET.Element,
    *,
    x: float,
    y: float,
    width: float,
    label: str,
    colour: str,
) -> None:
    ET.SubElement(
        parent,
        q("rect"),
        {
            "x": f"{x:g}",
            "y": f"{y:g}",
            "width": f"{width:g}",
            "height": "23",
            "rx": "11.5",
            "fill": "none",
            "stroke": colour,
            "stroke-width": "1",
        },
    )
    css_class = "new-conflict" if colour == "#A33F31" else "new-eyebrow"
    text = add_text(
        parent,
        x + width / 2,
        y + 16,
        label,
        size=9.8,
        css_class=css_class,
        anchor="middle",
    )
    text.set("fill", colour)


def _draw_plan_annotations(parent: ET.Element) -> None:
    _panel_heading(parent, 56, 136, "01 · INTEGRATED ROOF / P2 LOAD-PATH PLAN", 970)

    for x, label in zip((100, 232, 364, 496, 628, 760, 892), "ABCDEFG", strict=True):
        add_text(parent, x, 161.5, label, size=9.8, css_class="new-title", anchor="middle")
    add_text(
        parent,
        727,
        190,
        "P2 18 × 15 m · +3.80",
        size=9.8,
        css_class="new-eyebrow",
        anchor="middle",
    )
    _add_rotated_text(
        parent,
        215.5,
        372,
        "RL-CAR",
        css_class="new-title",
        contrast_bg=theme_colour("rooflight-surface"),
    )
    _add_rotated_text(
        parent,
        446.5,
        372,
        "RL-RC",
        css_class="new-title",
        contrast_bg=theme_colour("rooflight-surface"),
    )
    _add_rotated_text(
        parent,
        842.5,
        367.6,
        "D-048 CORE",
        css_class="new-hypothesis",
    )
    add_text(
        parent,
        496,
        356,
        "DIAPHRAGM DEMAND · 8.77 kN/m",
        size=10.2,
        css_class="key-tag",
        anchor="middle",
    )
    _add_rotated_text(parent, 569, 374.2, "EDGE · X=21", css_class="new-eyebrow")
    _add_rotated_text(
        parent,
        804,
        372,
        "HIDDEN FRAME · X=31.5",
        css_class="new-title",
    )
    add_text(
        parent,
        848,
        543.6,
        "4.50 m OVERHANG",
        size=9.8,
        css_class="key-tag",
        anchor="middle",
    )
    for x in (166, 298, 430, 562, 694, 826):
        add_text(parent, x, 588, "6.00", size=9.8, css_class="new-muted", anchor="middle")
    add_text(parent, 496, 606, "36.00 m", size=10.5, css_class="new-title", anchor="middle")
    _add_rotated_text(parent, 80, 372, "18.00 m", size=10.5, css_class="new-title")

    add_text(parent, 910, 184, "GRAPHIC STATUS", size=10.2, css_class="new-title")
    legend = (
        ("#172A32", "7 M60 ROOF"),
        ("#3D7186", "P2 GRAVITY"),
        ("#1D7480", "D-054 RL / q"),
        ("#66538A", "D-048 CORE"),
        ("#BD7626", "TRIAL BAYS"),
        ("#A33F31", "OPEN GATE"),
    )
    for index, (colour, label) in enumerate(legend):
        y = 207 + index * 31
        ET.SubElement(
            parent,
            q("line"),
            {
                "x1": "910",
                "y1": f"{y:g}",
                "x2": "932",
                "y2": f"{y:g}",
                "stroke": colour,
                "stroke-width": "5",
            },
        )
        add_text(parent, 940, y + 4, label, size=9.8, css_class="new-body")

    trial_note = ET.SubElement(parent, q("g"), {"data-contrast-bg": "#FBF0D9"})
    ET.SubElement(
        trial_note,
        q("rect"),
        {
            "x": "910",
            "y": "403",
            "width": "116",
            "height": "145",
            "rx": "4",
            "fill": "#FBF0D9",
            "stroke": "#A33F31",
            "stroke-dasharray": "6 4",
        },
    )
    add_text(trial_note, 922, 425, "TRIAL ONLY", size=10.2, css_class="new-conflict")
    add_wrapped_text(
        trial_note,
        922,
        448,
        "Bay locations are diagrammatic. Openings, collectors, reversal and joints remain "
        "unresolved.",
        width_chars=17,
        size=9.8,
        line_height=12.3,
    )


def _draw_evidence_matrix(parent: ET.Element) -> None:
    _panel_heading(parent, 1082, 140, "02 · CALCULATION ≠ DESIGN", 546)
    add_text(parent, 1082, 177, "PHENOMENON", size=9.8, css_class="new-muted", weight=700)
    add_text(parent, 1288, 177, "CALC", size=9.8, css_class="new-muted", weight=700)
    add_text(parent, 1374, 177, "EVIDENCE", size=9.8, css_class="new-muted", weight=700)
    add_text(parent, 1574, 177, "DESIGN", size=9.8, css_class="new-muted", weight=700)

    for index, (phenomenon, calc, evidence, design) in enumerate(EVIDENCE_ROWS):
        top = 188 + index * 42
        row_background = "#EEF2F0" if index % 2 else "#FFFDFA"
        row = ET.SubElement(parent, q("g"), {"data-contrast-bg": row_background})
        if index % 2:
            ET.SubElement(
                row,
                q("rect"),
                {
                    "x": "1074",
                    "y": f"{top:g}",
                    "width": "558",
                    "height": "37",
                    "rx": "3",
                    "fill": "#EEF2F0",
                },
            )
        baseline = top + 23
        add_text(row, 1082, baseline, phenomenon, size=9.8, css_class="new-title")
        calc_colour = "#A33F31" if calc.startswith("FAIL") else "#1D7480"
        _badge(row, x=1278, y=top + 7, width=82, label=calc, colour=calc_colour)
        add_text(row, 1374, baseline, evidence, size=9.8, css_class="new-body")
        _badge(row, x=1560, y=top + 7, width=72, label=design, colour="#A33F31")

    add_text(
        parent,
        1082,
        592,
        "PASS* = narrow component screen only · every system-level design gate remains open",
        size=9.8,
        css_class="new-conflict",
    )


def _metric_card(
    parent: ET.Element,
    *,
    x: float,
    title: str,
    value: str,
    note: str,
    note_class: str = "new-muted",
    value_two: str | None = None,
) -> None:
    card = ET.SubElement(parent, q("g"), {"data-contrast-bg": "#EEF2F0"})
    ET.SubElement(
        card,
        q("rect"),
        {
            "x": f"{x:g}",
            "y": "920",
            "width": "181",
            "height": "59",
            "rx": "5",
            "fill": "#EEF2F0",
            "stroke": "#CBD0CC",
        },
    )
    add_text(card, x + 10, 938, title, size=9.8, css_class="new-muted", weight=700)
    add_text(card, x + 10, 956, value, size=10.2, css_class="new-title")
    if value_two is None:
        add_text(card, x + 10, 973, note, size=9.8, css_class=note_class)
    else:
        add_text(card, x + 10, 973, value_two, size=9.8, css_class="new-title")
        add_text(card, x + 171, 938, note, size=9.8, css_class=note_class, anchor="end")


def _draw_truss_annotations(parent: ET.Element) -> None:
    _panel_heading(
        parent,
        56,
        655,
        "03 · REFERENCE ROOF TRUSS + EXPLICIT RESTRAINT ASSUMPTIONS",
        970,
    )
    add_text(parent, 98, 682, "TOP RESTRAINT @ 1.50 m", size=9.8, css_class="new-eyebrow")
    add_text(parent, 98, 700, "BOTTOM RESTRAINT @ 6.00 m", size=9.8, css_class="new-open")
    add_text(
        parent,
        447,
        682,
        "ILLUSTRATIVE TRANSPORT SPLIT",
        size=9.8,
        css_class="new-conflict",
    )
    add_text(
        parent,
        958,
        682,
        "LOADS AT PANEL POINTS",
        size=9.8,
        css_class="new-conflict",
        anchor="end",
    )
    add_text(
        parent,
        530,
        906,
        "18.00 m TRANSVERSE SPAN · 6 PANELS · VARIABLE DEPTH 0.99→1.80 m",
        size=9.8,
        css_class="new-title",
        anchor="middle",
    )

    cards = (
        (
            58,
            "TRIAL SECTIONS",
            "HSS120×120×6",
            "NOT SELECTED",
            "new-conflict",
            "HSS100×100×6",
        ),
        (251, "INTERACTION", "0.653", "local M 12.51 kN·m", "new-muted", None),
        (444, "SECOND ORDER", "B1 1.255", "Euler ratio 0.203", "new-muted", None),
        (637, "ENVELOPE", "Nmax 209.8 kN", "Rdown 79.7 kN", "new-muted", None),
        (830, "SPECIMEN", "1241 kg / truss", "deflection 16.9 mm", "new-muted", None),
    )
    for x, title, value, note, note_class, value_two in cards:
        _metric_card(
            parent,
            x=x,
            title=title,
            value=value,
            note=note,
            note_class=note_class,
            value_two=value_two,
        )
    add_text(
        parent,
        58,
        998,
        "GRAVITY: roof/openings → purlins → M60 trusses → columns → base/footing → ground · "
        "lateral path, collectors, connections and foundations BLOCKED",
        size=9.8,
        css_class="new-conflict",
    )


def _draw_detail_annotations(parent: ET.Element) -> None:
    _panel_heading(parent, 1082, 655, "04 · GENERIC JOINT PARTS", 244)
    add_text(parent, 1082, 680, "6-M20 · plate 12 mm · weld 8 mm", size=9.8, css_class="new-title")
    add_text(parent, 1156, 716, "HSS CHORD", size=9.8, css_class="key-tag", anchor="middle")
    add_text(
        parent,
        1082,
        790,
        "ratio 0.387 · demand 209.8 kN",
        size=9.8,
        css_class="new-eyebrow",
    )
    add_text(
        parent,
        1082,
        808,
        "BLOCKED · HSS wall / weld access / eccentricity",
        size=9.8,
        css_class="new-conflict",
    )

    _panel_heading(parent, 1384, 655, "05 · TRIAL BASE / FOOTING", 244)
    add_text(parent, 1497, 680, "≈ HEA200", size=9.8, css_class="key-tag", anchor="middle")
    add_text(parent, 1497, 746, "300×300×20", size=9.8, css_class="key-tag", anchor="middle")
    add_text(parent, 1497, 779, "2.0×2.0×0.5 m", size=9.8, css_class="key-tag", anchor="middle")
    add_text(
        parent,
        1384,
        798,
        "qmax 37.3 kPa · plate ratio 0.205",
        size=9.8,
        css_class="new-eyebrow",
    )
    add_text(
        parent,
        1384,
        814,
        "BLOCKED · anchors / shear / moment / geotech / RC",
        size=9.8,
        css_class="new-conflict",
    )

    _panel_heading(parent, 1082, 860, "06 · ERECTION ENVELOPE", 244)
    add_text(parent, 1202, 885, "HOOK 15.8 kN", size=9.8, css_class="key-tag", anchor="middle")
    add_text(parent, 1140, 931, "9.1 kN", size=9.8, css_class="new-open", anchor="middle")
    add_text(parent, 1264, 931, "9.1 kN", size=9.8, css_class="new-open", anchor="middle")
    add_text(
        parent,
        1082,
        982,
        "18 m → ≥2 pieces at 12 m transport limit",
        size=9.8,
        css_class="new-title",
    )
    add_text(
        parent,
        1082,
        1000,
        "BLOCKED · crane / lugs / splice / weather / bracing",
        size=9.8,
        css_class="new-conflict",
    )

    fire_annotations = ET.SubElement(parent, q("g"), {"data-contrast-bg": "#FBF0D9"})
    _panel_heading(
        fire_annotations,
        1384,
        860,
        "07 · FIRE SENSITIVITY · NOT A RATING",
        244,
    )
    for y, temperature, ratio, css_class in (
        (908, "400°C", "0.65", "new-eyebrow"),
        (943, "550°C", "1.05", "new-conflict"),
        (978, "700°C", "2.84", "new-conflict"),
    ):
        add_text(fire_annotations, 1384, y, temperature, size=9.8, css_class="new-title")
        add_text(fire_annotations, 1582, y, ratio, size=9.8, css_class=css_class)
    add_text(
        fire_annotations,
        1384,
        1000,
        "BLOCKED · 400°C sensitivity only; 550/700°C fail",
        size=9.8,
        css_class="new-conflict",
    )


def build_svg(source: Path = SOURCE) -> ET.ElementTree:
    source_root = ET.parse(source).getroot()
    children = list(source_root)
    source_metadata = _validate_source(children)

    root = create_document(
        title_id="gp05-title",
        desc_id="gp05-desc",
        accessible_title="Integrated structural E1 evidence readability pilot GP05",
        description=(
            "Presentation-only pilot of the fail-closed E1 structural synthesis. The "
            "integrated plan, reference truss, generic joint, trial base, erection envelope "
            "and fire-sensitivity geometry are copied without coordinate changes. Narrow "
            "calculations remain distinct from blocked system design and no structural system, "
            "section, quantity, product or construction release is created."
        ),
        sheet_id="DH-EST-E1-001",
        revision="GP05",
        status="graphic-pilot-not-current",
        metadata={
            "construction_authority": False,
            "date": "2026-08-22",
            "decision_ids": ["D-043", "D-045", "D-047", "D-048", "D-054"],
            "input_sha256": source_metadata["input_sha256"],
            "pilot": "GP05",
            "selection_authority": False,
            "sheet": "DH-EST-E1-001",
            "source": source.relative_to(ROOT).as_posix(),
            "source_revision": "R01 / 0.3 + E1 0.2",
            "source_sha256": sha256(source),
            "status": "presentation-only graphic pilot; not current; not for construction",
        },
    )
    _copy_source_defs(root, children[3])

    background = ET.SubElement(root, q("g"), {"id": "layer-background", "data-layer": "background"})
    ET.SubElement(background, q("rect"), {"width": "1684", "height": "1191", "fill": "#F4F0E7"})
    _panel(background, 36, 116, 1010, 494)
    _panel(background, 1062, 116, 586, 494)
    _panel(background, 36, 626, 1010, 382)
    _panel(background, 1062, 626, 284, 198)
    _panel(background, 1364, 626, 284, 198)
    _panel(background, 1062, 832, 284, 176)
    _panel(background, 1364, 832, 284, 176, css_class="status-open-box")

    model = ET.SubElement(
        root,
        q("g"),
        {"id": "layer-model", "data-layer": "calculation-linked-technical-geometry"},
    )
    for group_id, source_index in SOURCE_GROUPS.items():
        _copy_geometry_group(
            model,
            children[source_index],
            model_id=group_id,
        )

    annotations = ET.SubElement(
        root,
        q("g"),
        {
            "id": "layer-annotations",
            "data-layer": "technical-labels-and-evidence",
            "data-contrast-bg": theme_colour("panel"),
        },
    )
    _draw_plan_annotations(annotations)
    _draw_evidence_matrix(annotations)
    _draw_truss_annotations(annotations)
    _draw_detail_annotations(annotations)

    add_header(
        root,
        eyebrow="GRAPHIC PILOT 05 · PRESENTATION ONLY",
        title="INTEGRATED STRUCTURAL E1 · FAIL-CLOSED EVIDENCE",
        subtitle=(
            "Same R01 calculation-linked geometry and values · seven technical panels + "
            "authority block · narrow calculation ≠ system design"
        ),
        sheet_id="DH-EST-E1-001",
        issue_label="GP05 · NOT CURRENT",
    )
    add_footer(
        root,
        authority_sentence=(
            "Research screening complete; design blocked. No system, profile, PE-1 quantity, "
            "procurement, fabrication or construction release."
        ),
        source_sentence=(
            "Source: E1-001-R01 / 0.3 + E1 0.2 · D-043 / D-045 / D-047 / D-048 / D-054 · "
            "calculation-linked technical geometry preserved."
        ),
        gates_sentence=(
            "Open gates: lateral system/collectors · roof/deck/restraints · joints · "
            "foundation/geotech · erection · fire scenario/protection"
        ),
        date="2026-08-22",
    )
    return ET.ElementTree(root)


def write_outputs(source: Path = SOURCE, output: Path = OUTPUT) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    tree = build_svg(source)
    ET.indent(tree, space="  ")
    tree.write(output, encoding="utf-8", xml_declaration=True)
    manifest = {
        "construction_authority": False,
        "date": "2026-08-22",
        "decision_ids": ["D-043", "D-045", "D-047", "D-048", "D-054"],
        "generator": "dreamhouse/svg/pilot_e1_synthesis.py",
        "output": output.name,
        "output_sha256": sha256(output),
        "pilot": "GP05",
        "selection_authority": False,
        "sheet": "DH-EST-E1-001",
        "source": source.relative_to(ROOT).as_posix(),
        "source_revision": "R01 / 0.3 + E1 0.2",
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

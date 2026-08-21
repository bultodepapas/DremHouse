"""Shared sheet-frame helpers for presentation-only SVG migration pilots.

The helpers in this module create document-control and explanatory regions only.  They
do not create or modify architectural model geometry.
"""

from __future__ import annotations

import hashlib
import json
import textwrap
from collections.abc import Mapping
from pathlib import Path
from xml.etree import ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

SHEET_WIDTH = 1684
SHEET_HEIGHT = 1191


def q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


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
.new-hypothesis { fill: var(--hypothesis); font-weight: 700; }
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
.status-open-box {
  fill: #FBF0D9;
  stroke: var(--open);
  stroke-width: 1.5;
  stroke-dasharray: 7 5;
}
.status-hypothesis-box {
  fill: #F0ECF6;
  stroke: var(--hypothesis);
  stroke-width: 1.5;
  stroke-dasharray: 7 5;
}
""".strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_document(
    *,
    title_id: str,
    desc_id: str,
    accessible_title: str,
    description: str,
    sheet_id: str,
    revision: str,
    status: str,
    metadata: Mapping[str, object],
) -> ET.Element:
    """Create an accessible, explicitly non-construction SVG pilot root."""

    if metadata.get("construction_authority") is not False:
        raise ValueError("SVG migration pilots must set construction_authority to false")
    if not accessible_title.strip() or not description.strip():
        raise ValueError("Accessible title and description are required")

    root = ET.Element(
        q("svg"),
        {
            "width": str(SHEET_WIDTH),
            "height": str(SHEET_HEIGHT),
            "viewBox": f"0 0 {SHEET_WIDTH} {SHEET_HEIGHT}",
            "preserveAspectRatio": "xMidYMid meet",
            "role": "img",
            "aria-labelledby": f"{title_id} {desc_id}",
            "data-sheet-id": sheet_id,
            "data-revision": revision,
            "data-status": status,
            "data-construction-authority": "false",
        },
    )
    title = ET.SubElement(root, q("title"), {"id": title_id})
    title.text = accessible_title
    desc = ET.SubElement(root, q("desc"), {"id": desc_id})
    desc.text = description
    metadata_element = ET.SubElement(root, q("metadata"))
    metadata_element.text = json.dumps(dict(metadata), sort_keys=True)
    style = ET.SubElement(root, q("style"))
    style.text = CSS
    return root


def add_text(
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


def add_wrapped_text(
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
    lines = textwrap.wrap(
        value,
        width=width_chars,
        break_long_words=False,
        break_on_hyphens=False,
    )
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


def add_header(
    root: ET.Element,
    *,
    eyebrow: str,
    title: str,
    subtitle: str,
    sheet_id: str,
    issue_label: str,
) -> ET.Element:
    group = ET.SubElement(root, q("g"), {"id": "layer-sheet-header", "data-layer": "titleblock"})
    add_text(group, 36, 34, eyebrow, size=10.5, css_class="new-eyebrow")
    add_text(group, 36, 70, title, size=24, css_class="new-title")
    add_text(group, 36, 96, subtitle, size=11, css_class="new-muted")
    add_text(group, 1648, 56, sheet_id, size=15, css_class="new-title", anchor="end")
    add_text(group, 1648, 80, issue_label, size=10.5, css_class="new-conflict", anchor="end")
    ET.SubElement(
        group,
        q("line"),
        {"x1": "36", "y1": "105", "x2": "1648", "y2": "105", "class": "sheet-rule"},
    )
    return group


def add_footer(
    root: ET.Element,
    *,
    authority_sentence: str,
    source_sentence: str,
    gates_sentence: str,
    date: str,
) -> ET.Element:
    group = ET.SubElement(root, q("g"), {"id": "layer-sheet", "data-layer": "titleblock"})
    ET.SubElement(
        group,
        q("rect"),
        {"x": "36", "y": "1026", "width": "1612", "height": "129", "rx": "5", "fill": "#172A32"},
    )
    add_text(group, 56, 1056, "NOT FOR CONSTRUCTION", size=13, css_class="new-on-dark-alert")
    add_text(group, 56, 1082, authority_sentence, size=10.2, css_class="new-on-dark")
    add_text(group, 56, 1107, source_sentence, size=9.8, css_class="new-on-dark-muted")
    add_text(group, 56, 1132, gates_sentence, size=9.8, css_class="new-on-dark-muted")
    add_text(group, 1628, 1132, date, size=9.8, css_class="new-on-dark-muted", anchor="end")
    return group

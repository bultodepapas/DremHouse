"""Pure, read-only SVG review projections for coordinated model snapshots.

These views are evidence panels for coordination. They do not alter source geometry,
select missing geometry, or grant construction authority.
"""

from __future__ import annotations

import html
import json
import math
import re
import textwrap
from collections.abc import Mapping
from typing import Any
from xml.etree import ElementTree as ET

from dreamhouse.svg.theme import THEME_COLOURS

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

SHEET_WIDTH = 1440
SHEET_HEIGHT = 960
COLOURS = {
    "paper": THEME_COLOURS["paper"],
    "panel": THEME_COLOURS["panel"],
    "ink": THEME_COLOURS["ink"],
    "muted": THEME_COLOURS["muted"],
    "info": THEME_COLOURS["info"],
    "open": THEME_COLOURS["open"],
    "fail": THEME_COLOURS["conflict"],
    "pass": THEME_COLOURS["material-insulation-edge"],
    "study": THEME_COLOURS["hypothesis"],
    "material": THEME_COLOURS["material"],
    "rule": THEME_COLOURS["sheet-rule"],
    "open_surface": THEME_COLOURS["open-surface"],
    "study_surface": THEME_COLOURS["hypothesis-surface"],
    "context": THEME_COLOURS["table-row"],
    "space": THEME_COLOURS["program-living"],
    "equipment": THEME_COLOURS["program-technical"],
}

SVG_STYLE = """
text { font-family: Inter, "IBM Plex Sans", "Liberation Sans", Arial, sans-serif;
       text-rendering: geometricPrecision; }
.sheet-title { fill: var(--ink); font-size: 26px; font-weight: 700; }
.eyebrow { fill: var(--info); font-size: 11px; font-weight: 700; letter-spacing: 1px; }
.body { fill: var(--ink); font-size: 12px; }
.small { fill: var(--muted); font-size: 10px; }
.panel-title { fill: var(--ink); font-size: 15px; font-weight: 700; }
.finding-heading { font-weight: 700; }
.warning { fill: #FFFDFA; font-size: 13px; font-weight: 800; letter-spacing: .6px; }
.dimension { fill: var(--ink); font-size: 11px; font-weight: 700; }
.entity-shape { vector-effect: non-scaling-stroke; }
.entity-occurrence.is-selected .entity-shape { stroke: #BD7626 !important; stroke-width: 4px !important; }
.entity-occurrence.is-selected .entity-label { fill: #8A5A16; font-weight: 800; }
.finding-marker { font-size: 11px; font-weight: 800; }
""".strip()


def _q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _n(value: float) -> str:
    return f"{value:.3f}".rstrip("0").rstrip(".") if value else "0"


def _dim(value: float) -> str:
    return f"{value:.2f} m"


def _token(value: Any) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-.")
    return token or "item"


def _text(
    parent: ET.Element,
    x: float,
    y: float,
    value: Any,
    *,
    size: float = 12,
    css: str = "body",
    anchor: str | None = None,
    **attrs: str,
) -> ET.Element:
    values = {"x": _n(x), "y": _n(y), "font-size": _n(size), "class": css}
    if anchor:
        values["text-anchor"] = anchor
    values.update(attrs)
    node = ET.SubElement(parent, _q("text"), values)
    node.text = str(value)
    return node


def _line(
    parent: ET.Element,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    stroke: str,
    width: float = 1,
    dash: str | None = None,
    **attrs: str,
) -> ET.Element:
    values = {
        "x1": _n(x1),
        "y1": _n(y1),
        "x2": _n(x2),
        "y2": _n(y2),
        "stroke": stroke,
        "stroke-width": _n(width),
    }
    if dash:
        values["stroke-dasharray"] = dash
    values.update(attrs)
    return ET.SubElement(parent, _q("line"), values)


def _rect(
    parent: ET.Element,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str,
    stroke_width: float = 1,
    rx: float = 0,
    **attrs: str,
) -> ET.Element:
    values = {
        "x": _n(x),
        "y": _n(y),
        "width": _n(max(0, width)),
        "height": _n(max(0, height)),
        "fill": fill,
        "stroke": stroke,
        "stroke-width": _n(stroke_width),
    }
    if rx:
        values["rx"] = _n(rx)
    values.update(attrs)
    return ET.SubElement(parent, _q("rect"), values)


def _circle(
    parent: ET.Element,
    cx: float,
    cy: float,
    radius: float,
    *,
    fill: str,
    stroke: str,
    stroke_width: float = 1,
    **attrs: str,
) -> ET.Element:
    values = {
        "cx": _n(cx),
        "cy": _n(cy),
        "r": _n(radius),
        "fill": fill,
        "stroke": stroke,
        "stroke-width": _n(stroke_width),
    }
    values.update(attrs)
    return ET.SubElement(parent, _q("circle"), values)


def _serialized(root: ET.Element) -> str:
    return ET.tostring(root, encoding="unicode", short_empty_elements=True)


def _snapshot_meta(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": snapshot.get("schema_version"),
        "scenario_id": snapshot.get("scenario_id"),
        "input_hash": snapshot.get("input_hash"),
        "model_hash": snapshot.get("model_hash"),
        "status": "coordination projection",
        "construction_authority": False,
    }


def _root(
    snapshot: Mapping[str, Any],
    view_id: str,
    title: str,
    description: str,
    *,
    height: int = SHEET_HEIGHT,
) -> ET.Element:
    title_id = f"{view_id}-accessible-title"
    desc_id = f"{view_id}-accessible-description"
    root = ET.Element(
        _q("svg"),
        {
            "id": f"{view_id}-root",
            "width": str(SHEET_WIDTH),
            "height": str(height),
            "viewBox": f"0 0 {SHEET_WIDTH} {height}",
            "preserveAspectRatio": "xMidYMid meet",
            "role": "img",
            "aria-labelledby": f"{title_id} {desc_id}",
            "data-view-id": view_id,
            "data-scenario-id": str(snapshot.get("scenario_id", "unknown")),
            "data-input-hash": str(snapshot.get("input_hash", "")),
            "data-model-hash": str(snapshot.get("model_hash", "")),
            "data-status": "coordination projection",
            "data-construction-authority": "false",
        },
    )
    ET.SubElement(root, _q("title"), {"id": title_id}).text = title
    ET.SubElement(root, _q("desc"), {"id": desc_id}).text = description
    ET.SubElement(root, _q("metadata")).text = json.dumps(
        _snapshot_meta(snapshot), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    ET.SubElement(root, _q("style")).text = (
        ":root {\n"
        + "\n".join(f"  --{key}: {value};" for key, value in COLOURS.items())
        + "\n}\n"
        + SVG_STYLE
    )
    _rect(root, 0, 0, SHEET_WIDTH, height, fill=COLOURS["paper"], stroke="none", stroke_width=0)
    return root


def _frame(
    root: ET.Element,
    snapshot: Mapping[str, Any],
    view_id: str,
    title: str,
    subtitle: str,
    *,
    height: int = SHEET_HEIGHT,
) -> None:
    _text(root, 40, 30, "DREAM HOUSE · GENERATED REVIEW VIEW", size=10, css="eyebrow")
    _text(root, 40, 70, title, size=26, css="sheet-title")
    _text(root, 40, 96, subtitle, size=11, css="small")
    _rect(root, 1085, 25, 315, 31, fill=COLOURS["fail"], stroke=COLOURS["fail"], rx=3)
    _text(root, 1242.5, 46, "NOT FOR CONSTRUCTION", size=13, css="warning", anchor="middle")
    _text(
        root, 1085, 77, f"Scenario: {snapshot.get('scenario_id', 'unknown')}", size=10, css="body"
    )
    _text(root, 1085, 96, f"Input: {str(snapshot.get('input_hash', ''))[:18]}", size=9, css="small")
    _line(root, 40, 116, 1400, 116, stroke=COLOURS["rule"], width=1)
    footer_y = height - 60
    _line(root, 40, footer_y, 1400, footer_y, stroke=COLOURS["rule"], width=1)
    _rect(root, 40, footer_y + 14, 260, 27, fill=COLOURS["ink"], stroke=COLOURS["ink"], rx=2)
    _text(
        root, 170, footer_y + 33, "COORDINATION PROJECTION", size=10, css="warning", anchor="middle"
    )
    _text(
        root,
        320,
        footer_y + 31,
        f"Schema {snapshot.get('schema_version', 'unknown')} · model {str(snapshot.get('model_hash', ''))[:18]}",
        size=9,
        css="small",
    )
    _text(root, 1400, footer_y + 31, view_id.upper(), size=9, css="small", anchor="end")


def _entity_pairs(snapshot: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    entities = snapshot.get("entities", {})
    if not isinstance(entities, Mapping):
        return []
    return [(str(key), entity) for key, entity in entities.items() if isinstance(entity, Mapping)]


def _geom(entity: Mapping[str, Any]) -> Mapping[str, Any]:
    result = entity.get("geometry", {})
    return result if isinstance(result, Mapping) else {}


def _params(entity: Mapping[str, Any]) -> Mapping[str, Any]:
    result = entity.get("parameters", {})
    return result if isinstance(result, Mapping) else {}


def _bounds_attrs(geometry: Mapping[str, Any]) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for axis in ("x0", "x1", "y0", "y1", "z0", "z1"):
        value = _number(geometry.get(axis))
        attrs[f"data-world-{axis}"] = "" if value is None else _n(value)
    attrs["data-geometry-shape"] = str(geometry.get("shape", "unknown"))
    return attrs


def _display_id(key: str, entity: Mapping[str, Any]) -> str:
    return str(entity.get("id", key))


def _entity_group(
    parent: ET.Element, view_id: str, key: str, entity: Mapping[str, Any], occurrence: int
) -> ET.Element:
    geometry = _geom(entity)
    entity_id = _display_id(key, entity)
    source = entity.get("source", {})
    source = source if isinstance(source, Mapping) else {}
    roof_context = str(_params(entity).get("facade", "")).upper() == "ROOF"
    label = str(entity.get("label", ""))
    group = ET.SubElement(
        parent,
        _q("g"),
        {
            "id": f"{view_id}-entity-{occurrence:04d}-{_token(entity_id)}",
            "class": "entity-occurrence",
            "data-entity-id": entity_id,
            "data-entity-key": key,
            "data-kind": str(entity.get("kind", "unknown")),
            "data-level": str(entity.get("level", "unknown")),
            "data-status": str(entity.get("status", "unknown")),
            "data-projection-context": "overhead" if roof_context else "direct",
            "data-source-path": str(source.get("path", "")),
            "data-source-key": str(source.get("key", "")),
            **_bounds_attrs(geometry),
        },
    )
    source_label = " · ".join(
        str(value) for value in (source.get("path"), source.get("key")) if value
    )
    ET.SubElement(group, _q("title")).text = " · ".join(
        value for value in (entity_id, label, source_label) if value
    )
    ET.SubElement(group, _q("desc")).text = (
        f"{entity.get('kind', 'element')} · {entity.get('level', 'level unknown')} · "
        f"{entity.get('status', 'status unknown')}"
    )
    return group


def _style_for(entity: Mapping[str, Any]) -> tuple[str, str, str | None]:
    kind = str(entity.get("kind", "unknown")).lower()
    status = str(entity.get("status", "active")).lower()
    if kind == "opening" and str(_params(entity).get("facade", "")).upper() == "ROOF":
        return COLOURS["context"], COLOURS["info"], "5 4"
    if status == "study":
        return COLOURS["study_surface"], COLOURS["study"], "6 4"
    if status == "context":
        return COLOURS["context"], COLOURS["muted"], "4 4"
    if kind == "wall":
        return COLOURS["ink"], COLOURS["ink"], None
    if kind in {"opening", "door"}:
        return "#DCE9EC", COLOURS["info"], None
    if kind == "space":
        return COLOURS["space"], COLOURS["muted"], "3 3"
    if kind in {"column", "stair"}:
        return "#E4E0D7", COLOURS["material"], None
    if kind == "equipment":
        return COLOURS["equipment"], COLOURS["info"], None
    if kind == "reservation":
        return COLOURS["study_surface"], COLOURS["study"], "7 5"
    return COLOURS["panel"], COLOURS["muted"], "4 3"


def _rect_geometry(geometry: Mapping[str, Any]) -> tuple[float, float, float, float] | None:
    values = tuple(_number(geometry.get(axis)) for axis in ("x0", "x1", "y0", "y1"))
    if any(value is None for value in values):
        return None
    x0, x1, y0, y1 = (float(value) for value in values)
    return min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)


def _draw_plan_shape(
    group: ET.Element, entity: Mapping[str, Any], transform: Any
) -> tuple[float, float] | None:
    geometry = _geom(entity)
    shape = str(geometry.get("shape", "unknown")).lower()
    fill, stroke, dash = _style_for(entity)
    if shape == "point":
        point_x = _number(geometry.get("x0"))
        point_y = _number(geometry.get("y0"))
        if point_x is None or point_y is None:
            return None
        cx, cy = transform(point_x, point_y)
        _circle(
            group,
            cx,
            cy,
            4,
            fill=stroke,
            stroke=stroke,
            **{"class": "entity-shape", "vector-effect": "non-scaling-stroke"},
        )
        return cx, cy
    bounds = _rect_geometry(geometry)
    if bounds is None:
        return None
    x0, x1, y0, y1 = bounds
    px0, py0 = transform(x0, y1)
    px1, py1 = transform(x1, y0)
    width, height = abs(px1 - px0), abs(py1 - py0)
    common = {"class": "entity-shape", "vector-effect": "non-scaling-stroke"}
    if dash:
        common["stroke-dasharray"] = dash
    if shape == "line":
        _line(
            group,
            px0,
            py0,
            px1,
            py1,
            stroke=stroke,
            width=2,
            dash=dash,
            **{"class": "entity-shape"},
        )
        return (px0 + px1) / 2, (py0 + py1) / 2
    if shape not in {"rect", "box", "opening", "point"}:
        return None
    if width < 0.8 or height < 0.8:
        _line(
            group,
            px0,
            py0,
            px1,
            py1,
            stroke=stroke,
            width=3 if entity.get("kind") == "wall" else 2,
            dash=dash,
            **{"class": "entity-shape"},
        )
    else:
        _rect(
            group,
            min(px0, px1),
            min(py0, py1),
            width,
            height,
            fill=fill,
            stroke=stroke,
            stroke_width=2 if entity.get("kind") == "wall" else 1.5,
            **common,
        )
    return (px0 + px1) / 2, (py0 + py1) / 2


def _finding_records(evaluation: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    records = evaluation.get("findings", [])
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, Mapping)]


def _entity_warnings(
    entity_id: str,
    evaluation: Mapping[str, Any],
    visible_finding_indices: Mapping[int, tuple[int, int]],
) -> list[tuple[int, Mapping[str, Any], int]]:
    records = _finding_records(evaluation)
    grouped: dict[int, tuple[Mapping[str, Any], int]] = {}
    for index, record in enumerate(records):
        if index not in visible_finding_indices:
            continue
        if str(record.get("status", "")).upper() not in {"OPEN", "FAIL"}:
            continue
        if entity_id not in [str(value) for value in record.get("entity_ids", [])]:
            continue
        representative, _count = visible_finding_indices[index]
        previous = grouped.get(representative)
        grouped[representative] = (records[representative], (previous[1] + 1) if previous else 1)
    return [(index, record, count) for index, (record, count) in grouped.items()]


def _finding_marker(
    group: ET.Element,
    x: float,
    y: float,
    findings: list[tuple[int, Mapping[str, Any], int]],
    view_id: str,
    entity_id: str,
    marker_offset: int = 0,
) -> None:
    if not findings:
        return
    finding_index, finding, count = next(
        (
            (index, item, count)
            for index, item, count in findings
            if str(item.get("status", "")).upper() == "FAIL"
        ),
        findings[0],
    )
    group_count = count
    status = str(finding.get("status", "OPEN")).upper()
    rule_id = str(finding.get("rule_id", "finding"))
    fill = COLOURS["fail"] if status == "FAIL" else COLOURS["open"]
    marker_id = f"{view_id}-marker-{_token(entity_id)}-{finding_index:04d}"
    rules = ", ".join(str(item.get("rule_id", "finding")) for _, item, _ in findings)
    anchor = ET.SubElement(
        group,
        _q("a"),
        {
            "id": marker_id,
            "href": f"#{view_id}-finding-{_token(rule_id)}-{finding_index:04d}",
            "data-finding-id": rule_id,
            "data-finding-index": str(finding_index),
            "data-finding-count": str(group_count),
            "aria-label": f"{group_count} related finding record(s) for {entity_id}; {rules}",
        },
    )
    ET.SubElement(
        anchor, _q("title")
    ).text = f"{group_count} related finding record(s): {rules}. Select to reach {rule_id}."
    marker_x = x + ((marker_offset % 5) - 2) * 9
    marker_y = y - 12 + (((marker_offset // 5) % 3) - 1) * 9
    _circle(
        anchor,
        marker_x,
        marker_y,
        8,
        fill=fill,
        stroke=COLOURS["panel"],
        stroke_width=1,
        **{"class": "finding-marker"},
    )
    _text(
        anchor,
        marker_x,
        marker_y + 3.5,
        "!" if status == "FAIL" else "?",
        size=10,
        css="warning",
        anchor="middle",
    )


def _draw_finding_panel(
    root: ET.Element, view_id: str, evaluation: Mapping[str, Any], visible_ids: set[str]
) -> dict[int, tuple[int, int]]:
    x, y, width, height = 1010, 152, 390, 720
    _rect(root, x, y, width, height, fill=COLOURS["panel"], stroke=COLOURS["rule"], rx=5)
    _text(root, x + 20, y + 30, "Evidence and rule findings", size=15, css="panel-title")
    active: list[dict[str, Any]] = []
    group_index: dict[tuple[str, str, str], int] = {}
    for finding_index, record in enumerate(_finding_records(evaluation)):
        status = str(record.get("status", "")).upper()
        ids = {str(value) for value in record.get("entity_ids", [])}
        if status in {"OPEN", "FAIL"} and (not ids or ids.intersection(visible_ids)):
            rule_id = str(record.get("rule_id", "finding"))
            message = str(record.get("message", ""))
            key = (status, rule_id, message)
            if key not in group_index:
                group_index[key] = len(active)
                active.append(
                    {
                        "representative": finding_index,
                        "record": record,
                        "count": 0,
                        "entity_ids": set(),
                    }
                )
            summary = active[group_index[key]]
            summary["count"] += 1
            summary["entity_ids"].update(ids)
    if not active:
        _text(
            root,
            x + 20,
            y + 58,
            "No OPEN or FAIL findings linked to this view.",
            size=11,
            css="small",
        )
        _text(
            root,
            x + 20,
            y + 78,
            "PASS results remain in the HTML evidence index.",
            size=10,
            css="small",
        )
        return {}
    visible_indices: dict[int, tuple[int, int]] = {}
    records = _finding_records(evaluation)
    # Definite failures take priority over standing professional/unknown-data gates.
    active.sort(key=lambda item: str(item["record"].get("status", "")).upper() != "FAIL")
    for slot, summary in enumerate(active[:8]):
        finding_index = summary["representative"]
        finding = summary["record"]
        finding_count = summary["count"]
        top = y + 51 + slot * 78
        status = str(finding.get("status", "OPEN")).upper()
        rule_id = str(finding.get("rule_id", "finding"))
        color = COLOURS["fail"] if status == "FAIL" else COLOURS["open"]
        panel_id = f"{view_id}-finding-{_token(rule_id)}-{finding_index:04d}"
        card = _rect(
            root,
            x + 14,
            top,
            width - 28,
            66,
            fill=COLOURS["open_surface"],
            stroke=color,
            rx=3,
            id=panel_id,
            **{
                "data-finding-id": rule_id,
                "data-finding-index": str(finding_index),
                "data-finding-count": str(finding_count),
            },
        )
        heading = f"{status} · {rule_id}" + (
            f" · {finding_count} records" if finding_count > 1 else ""
        )
        message = str(finding.get("message", ""))
        ET.SubElement(card, _q("title")).text = f"{heading}. {message}"
        heading_lines = textwrap.wrap(
            heading, width=42, break_long_words=True, break_on_hyphens=True
        )[:2]
        for line_index, line in enumerate(heading_lines):
            _text(
                root,
                x + 26,
                top + 17 + line_index * 12,
                line,
                size=10.5,
                css="finding-heading",
                fill=color,
            )
        lines = textwrap.wrap(message, width=52, break_long_words=True, break_on_hyphens=True)
        if len(lines) > 2:
            lines = [*lines[:1], lines[1][:51].rstrip() + "…"]
        message_y = top + (40 if len(heading_lines) <= 1 else 43)
        for line_index, line in enumerate(lines[:2]):
            _text(root, x + 26, message_y + line_index * 11, line, size=9, css="small")
        for index, record in enumerate(records):
            if (
                str(record.get("status", "")).upper() == status
                and str(record.get("rule_id", "finding")) == rule_id
                and str(record.get("message", "")) == str(finding.get("message", ""))
            ):
                visible_indices[index] = (finding_index, finding_count)
    if len(active) > 8:
        _text(
            root,
            x + 20,
            y + height - 20,
            f"{len(active) - 8} additional findings are listed in index.html.",
            size=9,
            css="small",
        )
    return visible_indices


def _selected_levels(entity: Mapping[str, Any], levels: set[str]) -> bool:
    return str(entity.get("level", "")).upper() in levels


def _render_plan(
    snapshot: Mapping[str, Any],
    evaluation: Mapping[str, Any],
    *,
    view_id: str,
    level: str,
    title: str,
) -> str:
    root = _root(
        snapshot,
        view_id,
        title,
        f"Read-only {level} plan projection from the supplied model snapshot. "
        "Omitted or unknown geometry is not inferred.",
    )
    subtitle = (
        "P2 footprint projected within source extents · entities retain world coordinates"
        if level == "P2"
        else "Model geometry projected in plan · hall outline is source geometry context"
    )
    _frame(root, snapshot, view_id, title, subtitle)
    geometry = snapshot.get("geometry", {})
    geometry = geometry if isinstance(geometry, Mapping) else {}
    hall = geometry.get("hall", {})
    hall_length = _number(hall.get("length_m")) if isinstance(hall, Mapping) else None
    hall_width = _number(hall.get("width_m")) if isinstance(hall, Mapping) else None
    p2 = geometry.get("p2", {})
    p2_x = _number(p2.get("x_m")) if isinstance(p2, Mapping) else None
    p2_length = _number(p2.get("length_m")) if isinstance(p2, Mapping) else None
    p2_width = _number(p2.get("width_m")) if isinstance(p2, Mapping) else None
    if (
        level == "P2"
        and p2_x is not None
        and p2_length is not None
        and p2_width is not None
        and p2_length > 0
        and p2_width > 0
    ):
        origin_x, length, width = p2_x, p2_length, p2_width
        envelope_label, envelope_source = "P2 ENVELOPE · SOURCE GEOMETRY", "snapshot.geometry.p2"
    elif hall_length is not None and hall_width is not None and hall_length > 0 and hall_width > 0:
        origin_x, length, width = 0.0, hall_length, hall_width
        envelope_source = "snapshot.geometry.hall"
        envelope_label = (
            "HALL ENVELOPE · CONTEXT ONLY (P2 EXTENT UNAVAILABLE)"
            if level == "P2"
            else "HALL ENVELOPE · MODEL CONTEXT"
        )
        if level == "P2":
            _text(
                root,
                70,
                145,
                "P2 extent unavailable; hall bounds shown as context only.",
                size=10,
                css="small",
            )
    else:
        origin_x, length, width = 0.0, 36.0, 18.0
        envelope_source = "unavailable"
        envelope_label = "NO MODEL EXTENT · FALLBACK VIEWPORT"
        _text(
            root,
            70,
            145,
            f"{level} extent unavailable; fallback viewport is schematic only.",
            size=10,
            css="small",
        )
    show_hall = envelope_source != "unavailable"

    px, py, pw, ph = 80.0, 188.0, 860.0, 620.0
    scale = min((pw - 110) / length, (ph - 115) / width)
    drawn_width, drawn_height = length * scale, width * scale
    left = px + (pw - drawn_width) / 2
    top = py + (ph - drawn_height) / 2 + 16

    def transform(world_x: float, world_y: float) -> tuple[float, float]:
        return left + (world_x - origin_x) * scale, top + (width - world_y) * scale

    if show_hall:
        x0, y0 = transform(origin_x, width)
        x1, y1 = transform(origin_x + length, 0)
        extent_attrs = {
            "data-context": "p2-envelope" if envelope_source.endswith(".p2") else "hall-envelope",
            "data-source": envelope_source,
            "data-world-x0": _n(origin_x),
            "data-world-y0": "0",
            "data-world-x1": _n(origin_x + length),
            "data-world-y1": _n(width),
        }
        _rect(
            root,
            x0,
            y0,
            x1 - x0,
            y1 - y0,
            fill="none",
            stroke=COLOURS["ink"] if level == "PB" else COLOURS["muted"],
            stroke_width=2 if level == "PB" else 1.5,
            stroke_dasharray="none" if level == "PB" else "8 6",
            **extent_attrs,
        )
        _text(root, x0 + 2, y0 - 10, envelope_label, size=9, css="small")
        _horizontal_dimension(
            root, x0, x1, y1, y1 + 35, length, f"{view_id}-hall-plan-length", None
        )
        _vertical_dimension(root, x0, y0, y1, x0 - 35, width, f"{view_id}-hall-plan-width", None)

    _rect(root, px, py, pw, ph, fill="none", stroke=COLOURS["rule"], rx=3)
    _text(root, px + 12, py + 22, f"{level} · plan coordinates X/Y (m)", size=11, css="panel-title")
    visible_ids: set[str] = set()
    occurrences = 0
    omitted: list[str] = []
    pending_markers: list[tuple[ET.Element, float, float, str, int]] = []
    for key, entity in _entity_pairs(snapshot):
        if not _selected_levels(entity, {level, "PROJECT"}):
            continue
        bounds = _rect_geometry(_geom(entity))
        if (
            level == "P2"
            and bounds is not None
            and (
                bounds[1] < origin_x
                or bounds[0] > origin_x + length
                or bounds[3] < 0
                or bounds[2] > width
            )
        ):
            continue
        group = _entity_group(root, view_id, key, entity, occurrences)
        anchor = _draw_plan_shape(group, entity, transform)
        if anchor is None:
            omitted.append(_display_id(key, entity))
            root.remove(group)
            continue
        entity_id = _display_id(key, entity)
        visible_ids.add(entity_id)
        occurrences += 1
        rect_bounds = _rect_geometry(_geom(entity))
        label = entity_id
        if entity.get("label") and str(entity.get("label")) != entity_id:
            label = f"{entity_id} · {entity.get('label')}"
        if str(_params(entity).get("facade", "")).upper() == "ROOF":
            label = f"ROOF OVERHEAD · {label}"
        roof_context = str(_params(entity).get("facade", "")).upper() == "ROOF"
        if roof_context or (
            rect_bounds
            and abs(rect_bounds[1] - rect_bounds[0]) * scale > 48
            and abs(rect_bounds[3] - rect_bounds[2]) * scale > 18
        ):
            _text(
                group,
                anchor[0],
                anchor[1] + 3,
                label[:48],
                size=9,
                css="entity-label",
                anchor="middle",
                **{"data-label-for": entity_id},
            )
        pending_markers.append((group, anchor[0] + 4, anchor[1] - 2, entity_id, occurrences - 1))
    if occurrences == 0:
        _text(
            root,
            px + pw / 2,
            py + ph / 2,
            f"No {level} geometry with known plan bounds in this snapshot.",
            size=13,
            css="small",
            anchor="middle",
        )
    _text(
        root,
        80,
        835,
        f"{occurrences} {level}/project entities projected from the snapshot; outlines retain source bounds.",
        size=9,
        css="small",
    )
    if omitted:
        omitted_text = f"Not projected · {len(omitted)} unresolved plan bounds: " + ", ".join(
            omitted[:7]
        )
        if len(omitted) > 7:
            omitted_text += f" +{len(omitted) - 7}"
        _text(
            root,
            80,
            851,
            textwrap.shorten(omitted_text, width=145, placeholder="…"),
            size=9,
            css="small",
        )
    visible_findings = _draw_finding_panel(root, view_id, evaluation, visible_ids)
    for group, marker_x, marker_y, entity_id, offset in pending_markers:
        _finding_marker(
            group,
            marker_x,
            marker_y,
            _entity_warnings(entity_id, evaluation, visible_findings),
            view_id,
            entity_id,
            marker_offset=offset,
        )
    return _serialized(root)


def _horizontal_dimension(
    parent: ET.Element,
    x0: float,
    x1: float,
    y_object: float,
    y_dimension: float,
    value: float,
    dimension_id: str,
    entity_id: str | None,
    dimension_source: str = "geometry",
) -> None:
    _line(
        parent,
        x0,
        y_object,
        x0,
        y_dimension + (5 if y_dimension > y_object else -5),
        stroke=COLOURS["muted"],
        width=0.8,
    )
    _line(
        parent,
        x1,
        y_object,
        x1,
        y_dimension + (5 if y_dimension > y_object else -5),
        stroke=COLOURS["muted"],
        width=0.8,
    )
    _line(parent, x0, y_dimension, x1, y_dimension, stroke=COLOURS["ink"], width=1)
    for x in (x0, x1):
        _line(
            parent, x - 4, y_dimension - 4, x + 4, y_dimension + 4, stroke=COLOURS["ink"], width=1
        )
    attrs = {
        "id": f"dimension-{_token(dimension_id)}",
        "data-dimension-for": entity_id or dimension_id,
        "data-dimension-value": _n(value),
        "data-dimension-source": dimension_source,
    }
    _text(
        parent,
        (x0 + x1) / 2,
        y_dimension - 5 if y_dimension > y_object else y_dimension - 7,
        _dim(value),
        size=10,
        css="dimension",
        anchor="middle",
        **attrs,
    )


def _vertical_dimension(
    parent: ET.Element,
    x_object: float,
    y0: float,
    y1: float,
    x_dimension: float,
    value: float,
    dimension_id: str,
    entity_id: str | None,
    dimension_source: str = "geometry",
) -> None:
    _line(
        parent,
        x_object,
        y0,
        x_dimension + (5 if x_dimension > x_object else -5),
        y0,
        stroke=COLOURS["muted"],
        width=0.8,
    )
    _line(
        parent,
        x_object,
        y1,
        x_dimension + (5 if x_dimension > x_object else -5),
        y1,
        stroke=COLOURS["muted"],
        width=0.8,
    )
    _line(parent, x_dimension, y0, x_dimension, y1, stroke=COLOURS["ink"], width=1)
    for y in (y0, y1):
        _line(
            parent, x_dimension - 4, y - 4, x_dimension + 4, y + 4, stroke=COLOURS["ink"], width=1
        )
    attrs = {
        "id": f"dimension-{_token(dimension_id)}",
        "data-dimension-for": entity_id or dimension_id,
        "data-dimension-value": _n(value),
        "data-dimension-source": dimension_source,
    }
    _text(
        parent,
        x_dimension + (8 if x_dimension > x_object else -8),
        (y0 + y1) / 2,
        _dim(value),
        size=10,
        css="dimension",
        anchor="start" if x_dimension > x_object else "end",
        **attrs,
    )


def _vertical_extent(entity: Mapping[str, Any]) -> tuple[float, float, str] | None:
    geometry = _geom(entity)
    z0, z1 = _number(geometry.get("z0")), _number(geometry.get("z1"))
    if z0 is not None and z1 is not None:
        return min(z0, z1), max(z0, z1), "geometry"
    if str(entity.get("kind", "")).lower() != "opening":
        return None
    params = _params(entity)
    level = _number(params.get("level_m"))
    sill = _number(params.get("sill_m"))
    height = _number(params.get("height_m"))
    if level is None or sill is None or height is None or height <= 0:
        return None
    return level + sill, level + sill + height, "opening-parameters"


def _facade_spec(
    facade: str, hall_length: float, hall_width: float
) -> tuple[str, float, float, str]:
    if facade == "A":
        return "x", 0.0, hall_width, "Y=0 m"
    if facade == "B":
        return "x", hall_width, hall_width, f"Y={hall_width:g} m"
    if facade == "FRONT":
        return "y", 0.0, hall_length, "X=0 m"
    return "y", hall_length, hall_length, f"X={hall_length:g} m"


def _entity_on_facade(
    entity: Mapping[str, Any], facade: str, hall_length: float, hall_width: float
) -> bool:
    params = _params(entity)
    stated = str(params.get("facade", "")).upper()
    if stated == facade:
        return True
    geometry = _geom(entity)
    bounds = _rect_geometry(geometry)
    if bounds is None:
        return False
    x0, x1, y0, y1 = bounds
    if facade == "A":
        return y0 <= 0 <= y1
    if facade == "B":
        return y0 <= hall_width <= y1
    if facade == "FRONT":
        return x0 <= 0 <= x1
    return x0 <= hall_length <= x1


def _horizontal_extent(entity: Mapping[str, Any], axis: str) -> tuple[float, float] | None:
    geometry = _geom(entity)
    a, b = ("x0", "x1") if axis == "x" else ("y0", "y1")
    first, second = _number(geometry.get(a)), _number(geometry.get(b))
    if first is None or second is None:
        return None
    return min(first, second), max(first, second)


def _render_elevation(
    snapshot: Mapping[str, Any],
    evaluation: Mapping[str, Any],
    *,
    view_id: str,
    facade: str,
    title: str,
) -> str:
    description = (
        f"Read-only {facade} elevation projection of supplied entities. "
        "The shell and roof are omitted wherever the snapshot provides no geometry."
    )
    root = _root(snapshot, view_id, title, description)
    _frame(
        root,
        snapshot,
        view_id,
        title,
        "Facade projection · only supplied horizontal and vertical extents are shown",
    )
    hall = snapshot.get("geometry", {}).get("hall", {})
    hall_length = _number(hall.get("length_m")) if isinstance(hall, Mapping) else None
    hall_width = _number(hall.get("width_m")) if isinstance(hall, Mapping) else None
    hall_length = hall_length if hall_length is not None else 36.0
    hall_width = hall_width if hall_width is not None else 18.0
    axis, _, _, plane_label = _facade_spec(facade, hall_length, hall_width)

    candidates: list[
        tuple[str, Mapping[str, Any], tuple[float, float], tuple[float, float, str]]
    ] = []
    omitted: list[str] = []
    for key, entity in _entity_pairs(snapshot):
        if not _selected_levels(entity, {"PB", "P2", "PROJECT"}):
            continue
        if not _entity_on_facade(entity, facade, hall_length, hall_width):
            continue
        horizontal = _horizontal_extent(entity, axis)
        vertical = _vertical_extent(entity)
        if horizontal is None or vertical is None:
            omitted.append(_display_id(key, entity))
            continue
        if horizontal[1] <= horizontal[0] or vertical[1] <= vertical[0]:
            omitted.append(_display_id(key, entity))
            continue
        candidates.append((key, entity, horizontal, vertical))

    gx, gy, gw, gh = 80.0, 188.0, 860.0, 620.0
    _rect(root, gx, gy, gw, gh, fill=COLOURS["panel"], stroke=COLOURS["rule"], rx=3)
    _text(
        root,
        gx + 12,
        gy + 22,
        f"{facade} facade · {plane_label} · horizontal model {axis.upper()} (m)",
        size=11,
        css="panel-title",
    )
    visible_ids: set[str] = set()
    pending_markers: list[tuple[ET.Element, float, float, str, int]] = []
    if candidates:
        h0 = min(0.0, min(item[2][0] for item in candidates))
        h1 = max(hall_length if axis == "x" else hall_width, max(item[2][1] for item in candidates))
        z0 = min(0.0, min(item[3][0] for item in candidates))
        z1 = max(item[3][1] for item in candidates)
        p2_level = _number((snapshot.get("geometry", {}).get("p2") or {}).get("level_m"))
        if p2_level is not None:
            z1 = max(z1, p2_level)
        pad_x = max((h1 - h0) * 0.08, 0.2)
        pad_z = max((z1 - z0) * 0.08, 0.15)
        h0 -= pad_x
        h1 += pad_x
        z0 -= pad_z
        z1 += pad_z
        available_w, available_h = gw - 110, gh - 120
        scale = min(available_w / (h1 - h0), available_h / (z1 - z0))
        drawing_w = (h1 - h0) * scale
        drawing_h = (z1 - z0) * scale
        left = gx + (gw - drawing_w) / 2
        bottom = gy + 55 + (available_h + drawing_h) / 2

        def to_screen(horizontal: float, elevation: float) -> tuple[float, float]:
            return left + (horizontal - h0) * scale, bottom - (elevation - z0) * scale

        for index, (key, entity, horizontal, vertical) in enumerate(candidates):
            group = _entity_group(root, view_id, key, entity, index)
            entity_id = _display_id(key, entity)
            visible_ids.add(entity_id)
            x0, y1 = to_screen(horizontal[0], vertical[1])
            x1, y0 = to_screen(horizontal[1], vertical[0])
            fill, stroke, dash = _style_for(entity)
            common = {"class": "entity-shape", "vector-effect": "non-scaling-stroke"}
            if dash:
                common["stroke-dasharray"] = dash
            _rect(
                group,
                min(x0, x1),
                min(y0, y1),
                abs(x1 - x0),
                abs(y1 - y0),
                fill=fill,
                stroke=stroke,
                stroke_width=1.7,
                **common,
            )
            label = entity_id
            if entity.get("label") and str(entity.get("label")) != entity_id:
                label = f"{entity_id} · {entity.get('label')}"
            _text(
                group,
                (x0 + x1) / 2,
                (y0 + y1) / 2 + 3,
                label[:42],
                size=9,
                css="entity-label",
                anchor="middle",
                **{"data-label-for": entity_id},
            )
            pending_markers.append((group, x1 + 3, y0 - 2, entity_id, index))
            if str(entity.get("kind", "")).lower() in {"opening", "door"}:
                measured_width = horizontal[1] - horizontal[0]
                _horizontal_dimension(
                    group,
                    x0,
                    x1,
                    y0,
                    y0 + 22,
                    measured_width,
                    f"{view_id}-{entity_id}-width",
                    entity_id,
                )
                measured_height = vertical[1] - vertical[0]
                _vertical_dimension(
                    group,
                    x1,
                    y0,
                    y1,
                    x1 + 20,
                    measured_height,
                    f"{view_id}-{entity_id}-height",
                    entity_id,
                    dimension_source=vertical[2],
                )
                params = _params(entity)
                sill = _number(params.get("sill_m"))
                level = _number(params.get("level_m"))
                if sill is not None:
                    baseline = "" if level is None else f" above level {_dim(level)}"
                    _text(
                        group,
                        x0,
                        y1 - 9,
                        f"Sill {_dim(sill)}{baseline}",
                        size=8.5,
                        css="small",
                        **{"data-note-for": entity_id},
                    )
        datums = [("PB", 0.0)]
        if p2_level is not None:
            datums.append(("P2", p2_level))
        for level_id, elevation in datums:
            _, datum_y = to_screen(h0, elevation)
            _line(
                root,
                left,
                datum_y,
                left + drawing_w,
                datum_y,
                stroke=COLOURS["muted"],
                width=0.8,
                dash="5 4",
                **{"data-datum-level": level_id, "data-elevation-m": _n(elevation)},
            )
            _text(
                root,
                left,
                datum_y - 7,
                f"{level_id} {elevation:+.2f} m",
                size=9,
                css="small",
            )
        coverage = f"Projected {len(candidates)} entity/entities. No roof outline or wall build-up is implied."
        if omitted:
            coverage += f" Omitted ({len(omitted)} incomplete extents): " + ", ".join(omitted[:6])
            if len(omitted) > 6:
                coverage += f" +{len(omitted) - 6}"
        _text(
            root,
            gx + 15,
            gy + gh - 18,
            textwrap.shorten(coverage, width=130, placeholder="…"),
            size=8.5,
            css="small",
        )
    else:
        _text(
            root,
            gx + gw / 2,
            gy + 270,
            "No facade entities with known horizontal and vertical extents.",
            size=13,
            css="small",
            anchor="middle",
        )
        _text(
            root,
            gx + gw / 2,
            gy + 294,
            "Unknown extents are omitted rather than assigned a dimension.",
            size=10,
            css="small",
            anchor="middle",
        )
    visible_findings = _draw_finding_panel(root, view_id, evaluation, visible_ids)
    for group, marker_x, marker_y, entity_id, offset in pending_markers:
        _finding_marker(
            group,
            marker_x,
            marker_y,
            _entity_warnings(entity_id, evaluation, visible_findings),
            view_id,
            entity_id,
            marker_offset=offset,
        )
    return _serialized(root)


def _render_window_details(snapshot: Mapping[str, Any], evaluation: Mapping[str, Any]) -> str:
    openings = [
        (key, entity)
        for key, entity in _entity_pairs(snapshot)
        if str(entity.get("kind", "")).lower() == "opening"
    ]
    view_id = "window-details"
    row_count = max(1, math.ceil(len(openings) / 2))
    card_top = 154
    card_width = 440
    card_height = 205
    row_step = card_height + 14
    height = max(SHEET_HEIGHT, card_top + row_count * row_step + 82)
    root = _root(
        snapshot,
        view_id,
        "Opening detail review",
        "Combined opening geometry diagrams from supplied snapshot bounds and parameters.",
        height=height,
    )
    _frame(
        root,
        snapshot,
        view_id,
        "Opening detail review",
        "Opening geometry diagrams · no frame, reveal, flashing, glass make-up or installation detail is inferred",
        height=height,
    )
    _text(
        root,
        48,
        142,
        "Projected geometry dimensions · parameter-only diagrams show shape and size, not plan location or assembly.",
        size=9,
        css="small",
    )
    visible_ids: set[str] = set()
    pending_markers: list[tuple[ET.Element, float, float, str, int]] = []
    for index, (key, entity) in enumerate(openings):
        col, row = index % 2, index // 2
        x, y = 48 + col * 458, card_top + row * row_step
        card = ET.SubElement(root, _q("g"), {"id": f"window-card-{index:04d}"})
        _rect(
            card, x, y, card_width, card_height, fill=COLOURS["panel"], stroke=COLOURS["rule"], rx=4
        )
        group = _entity_group(card, view_id, key, entity, index)
        entity_id = _display_id(key, entity)
        visible_ids.add(entity_id)
        label = str(entity.get("label", ""))
        _text(
            group,
            x + 18,
            y + 27,
            f"{entity_id} · {label}" if label and label != entity_id else entity_id,
            size=13,
            css="panel-title",
            **{"data-label-for": entity_id},
        )
        params = _params(entity)
        facade = str(params.get("facade", "facade unspecified"))
        is_roof = facade.upper() == "ROOF"
        _text(
            group,
            x + 18,
            y + 48,
            f"{entity.get('level', 'Level unknown')} · {facade} · {entity.get('status', 'status unknown')}",
            size=9,
            css="small",
        )
        geometry = _geom(entity)
        horizontal_axis = "y" if facade.upper() in {"FRONT", "REAR"} else "x"
        projected = _horizontal_extent(entity, horizontal_axis)
        vertical = _vertical_extent(entity)
        plan_bounds = _rect_geometry(geometry) if is_roof else None
        geom_width = projected[1] - projected[0] if projected else None
        param_width = _number(params.get("width_m"))
        display_width = (
            plan_bounds[1] - plan_bounds[0]
            if plan_bounds
            else geom_width
            if geom_width is not None and geom_width > 0
            else param_width
        )
        display_height = (
            plan_bounds[3] - plan_bounds[2]
            if plan_bounds
            else vertical[1] - vertical[0]
            if vertical
            else _number(params.get("height_m"))
        )
        if (
            display_width is not None
            and display_height is not None
            and display_width > 0
            and display_height > 0
        ):
            scale = min(190 / display_width, 82 / display_height)
            shape_width, shape_height = display_width * scale, display_height * scale
            shape_x, shape_y = x + 28, y + 76 + (84 - shape_height) / 2
            fill, stroke, dash = _style_for(entity)
            attrs = {"class": "entity-shape", "vector-effect": "non-scaling-stroke"}
            if dash:
                attrs["stroke-dasharray"] = dash
            _rect(
                group,
                shape_x,
                shape_y,
                shape_width,
                shape_height,
                fill=fill,
                stroke=stroke,
                stroke_width=2,
                **attrs,
            )
            width_source = (
                "geometry"
                if plan_bounds or (geom_width is not None and geom_width > 0)
                else "opening-parameters"
            )
            _horizontal_dimension(
                group,
                shape_x,
                shape_x + shape_width,
                shape_y + shape_height,
                shape_y + shape_height + 18,
                display_width,
                f"{view_id}-{entity_id}-detail-width",
                entity_id,
                dimension_source="geometry" if width_source == "geometry" else "opening-parameters",
            )
            if vertical or is_roof:
                _vertical_dimension(
                    group,
                    shape_x + shape_width,
                    shape_y,
                    shape_y + shape_height,
                    shape_x + shape_width + 18,
                    display_height,
                    f"{view_id}-{entity_id}-detail-span",
                    entity_id,
                    dimension_source="geometry" if is_roof else vertical[2],
                )
            vertical_label = (
                f"Plan span {_dim(display_height)}" if is_roof else f"Height {_dim(display_height)}"
            )
            height_text = _text(
                group,
                x + 286,
                y + 101,
                vertical_label,
                size=9,
                css="dimension",
                **{
                    "data-dimension-for": entity_id,
                    "data-dimension-value": _n(display_height),
                    "data-dimension-source": "geometry"
                    if is_roof
                    else vertical[2]
                    if vertical
                    else "opening-parameters",
                },
            )
            height_text.set("data-dimension-kind", "plan-span" if is_roof else "height")
            if is_roof:
                _text(group, x + 286, y + 119, "Roof build-up unresolved", size=8.5, css="small")
            elif width_source == "opening-parameters":
                _text(
                    group, x + 286, y + 119, "Width from opening parameters", size=8.5, css="small"
                )
        else:
            _text(
                group,
                x + 28,
                y + 108,
                "Geometry incomplete · no opening outline or dimensions shown.",
                size=10,
                css="small",
            )
        sill = None if is_roof else _number(params.get("sill_m"))
        level = _number(params.get("level_m"))
        if sill is not None:
            level_note = f"; floor level {_dim(level)}" if level is not None else ""
            _text(
                group,
                x + 286,
                y + 137,
                f"Sill {_dim(sill)}{level_note}",
                size=9,
                css="small",
                **{"data-sill-for": entity_id, "data-sill-value": _n(sill)},
            )
        source = entity.get("source", {})
        source = source if isinstance(source, Mapping) else {}
        source_text = f"Source: {source.get('path', 'not supplied')} · {source.get('key', 'key not supplied')}"
        source_node = _text(
            group,
            x + 14,
            y + card_height - 10,
            textwrap.shorten(source_text, width=74, placeholder="…"),
            size=8,
            css="small",
            **{"data-source-for": entity_id},
        )
        ET.SubElement(source_node, _q("title")).text = source_text
        pending_markers.append((group, x + card_width - 30, y + 30, entity_id, index))
    if not openings:
        _text(
            root,
            720,
            430,
            "No opening entities in the snapshot.",
            size=13,
            css="small",
            anchor="middle",
        )
    visible_findings = _draw_finding_panel(root, view_id, evaluation, visible_ids)
    for group, marker_x, marker_y, entity_id, offset in pending_markers:
        _finding_marker(
            group,
            marker_x,
            marker_y,
            _entity_warnings(entity_id, evaluation, visible_findings),
            view_id,
            entity_id,
            marker_offset=offset,
        )
    return _serialized(root)


def _svg_index_items(views: Mapping[str, str]) -> str:
    return "\n".join(
        f'<section class="view" id="section-{html.escape(name[:-4], quote=True)}" '
        f'aria-label="{html.escape(name[:-4].replace("-", " ").title(), quote=True)}">{content}</section>'
        for name, content in views.items()
    )


def _render_html(
    snapshot: Mapping[str, Any], evaluation: Mapping[str, Any], views: Mapping[str, str]
) -> str:
    entities = _entity_pairs(snapshot)
    scenario = html.escape(str(snapshot.get("scenario_id", "unknown")))
    schema = html.escape(str(snapshot.get("schema_version", "unknown")))
    input_hash = html.escape(str(snapshot.get("input_hash", "")))
    model_hash = html.escape(str(snapshot.get("model_hash", "")))
    findings = _finding_records(evaluation)
    entity_rows: list[str] = []
    for index, (key, entity) in enumerate(entities):
        entity_id = _display_id(key, entity)
        source = entity.get("source", {})
        source = source if isinstance(source, Mapping) else {}
        aliases = entity.get("aliases", [])
        aliases_text = (
            ", ".join(str(alias) for alias in aliases) if isinstance(aliases, list) else ""
        )
        geometry = _geom(entity)
        shape = str(geometry.get("shape", "unknown"))
        plan_known = (
            (_number(geometry.get("x0")) is not None and _number(geometry.get("y0")) is not None)
            if shape == "point"
            else _rect_geometry(geometry) is not None
        )
        vertical = _vertical_extent(entity)
        geometry_coverage = (
            f"{shape} · plan bounds {'known' if plan_known else 'unresolved'} · "
            f"vertical extent {vertical[2] if vertical else 'unresolved'}"
        )
        evidence = " · ".join(
            part
            for part in (
                f"{entity.get('kind', 'element')} {entity_id}",
                str(entity.get("label", "")),
                f"level {entity.get('level', 'unknown')}",
                f"status {entity.get('status', 'unknown')}",
                geometry_coverage,
                f"source {source.get('path', 'not supplied')} / {source.get('key', 'not supplied')}",
                f"aliases {aliases_text}" if aliases_text else "",
            )
            if part
        )
        searchable = html.escape(f"{entity_id} {key} {evidence}".lower(), quote=True)
        entity_rows.append(
            f'<li class="entity-row" id="entity-row-{index}" data-search="{searchable}">'
            f'<button type="button" class="entity-select" data-select-entity="{html.escape(entity_id, quote=True)}" '
            f'data-evidence="{html.escape(evidence, quote=True)}" aria-pressed="false">'
            f"<strong>{html.escape(entity_id)}</strong><span>{html.escape(str(entity.get('label', '')))}</span>"
            f"<small>{html.escape(str(entity.get('kind', 'element')))} · "
            f"{html.escape(str(entity.get('level', 'unknown')))} · "
            f"{html.escape(str(entity.get('status', 'unknown')))}</small>"
            f"<small>{html.escape(geometry_coverage)}</small></button></li>"
        )
    if not entity_rows:
        entity_rows.append('<li class="empty">No entities in snapshot.</li>')

    finding_rows: list[str] = []
    for index, finding in enumerate(findings):
        status = str(finding.get("status", "unknown")).upper()
        rule_id = str(finding.get("rule_id", f"finding-{index + 1}"))
        linked_ids = [str(value) for value in finding.get("entity_ids", [])]
        links = (
            " ".join(
                f'<button type="button" class="evidence-entity" data-select-entity="{html.escape(entity_id, quote=True)}">'
                f"{html.escape(entity_id)}</button>"
                for entity_id in linked_ids
            )
            or "No entity links supplied"
        )
        finding_rows.append(
            f'<li class="finding status-{html.escape(status.lower(), quote=True)}" id="html-finding-{index}" '
            f'data-entity-ids="{html.escape(json.dumps(linked_ids, ensure_ascii=False), quote=True)}">'
            f"<strong>{html.escape(status)} · {html.escape(rule_id)}</strong>"
            f"<p>{html.escape(str(finding.get('message', '')))}</p>"
            f"<small>Coverage: {html.escape(str(finding.get('coverage', 'not supplied')))} · "
            f"Severity: {html.escape(str(finding.get('severity', 'not supplied')))}</small>"
            f'<div class="finding-entities">{links}</div></li>'
        )
    if not finding_rows:
        finding_rows.append('<li class="empty">No evaluation findings supplied.</li>')

    sections = _svg_index_items(views)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dream House coordination review · {scenario}</title>
<style>
:root {{ color-scheme: light; font-family: Inter, "IBM Plex Sans", "Liberation Sans", Arial, sans-serif;
  color: #172A32; background: #F4F0E7; }}
body {{ margin: 0; }}
header {{ position: sticky; top: 0; z-index: 2; padding: 14px 22px; background: #172A32; color: #FFFDFA; }}
header h1 {{ margin: 0 0 6px; font-size: 1.25rem; }}
header p {{ margin: 0; font-size: .84rem; color: #DDE4E2; }}
nav {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }}
nav a {{ color: #FFFDFA; border: 1px solid #9AA5A4; border-radius: 3px; padding: 5px 8px; text-decoration: none; }}
.authority {{ display: inline-block; margin-top: 8px; padding: 5px 8px; background: #A33F31; font-weight: 800; }}
.layout {{ display: grid; grid-template-columns: minmax(260px, 330px) minmax(0, 1fr); gap: 16px; padding: 16px; align-items: start; }}
aside {{ position: sticky; top: 160px; max-height: calc(100vh - 178px); overflow: auto; }}
.panel {{ background: #FFFDFA; border: 1px solid #B9C0BD; border-radius: 5px; margin-bottom: 12px; padding: 12px; }}
h2 {{ font-size: 1rem; margin: 0 0 9px; }}
label {{ display: block; font-size: .8rem; margin-bottom: 5px; }}
input[type="search"] {{ width: 100%; box-sizing: border-box; padding: 8px; border: 1px solid #536168; border-radius: 3px; }}
ul {{ list-style: none; padding: 0; margin: 0; }}
.entity-row {{ border-top: 1px solid #EEF2F0; }}
.entity-select {{ display: grid; width: 100%; gap: 3px; border: 0; padding: 8px 5px; text-align: left; color: inherit; background: transparent; cursor: pointer; }}
.entity-select:hover, .entity-select[aria-pressed="true"] {{ background: #FBF0D9; }}
.entity-select small, .finding small {{ color: #536168; }}
.evidence-entity {{ margin: 4px 5px 0 0; border: 1px solid #536168; border-radius: 2px; background: #FFFDFA; cursor: pointer; }}
.finding {{ border-top: 1px solid #CBD0CC; padding: 9px 0; }}
.finding p {{ margin: 5px 0; font-size: .85rem; }}
.status-open strong {{ color: #8A5A16; }} .status-fail strong {{ color: #A33F31; }}
.empty, .helper {{ color: #536168; font-size: .82rem; }}
.view {{ margin: 0 auto 18px; max-width: 1440px; scroll-margin-top: 165px; }}
.view svg {{ display: block; width: 100%; height: auto; border: 1px solid #B9C0BD; background: #F4F0E7; }}
svg .entity-occurrence.is-selected {{ filter: drop-shadow(0 0 3px #BD7626); }}
@media (max-width: 900px) {{ .layout {{ grid-template-columns: 1fr; }} aside {{ position: static; max-height: 45vh; }} header {{ position: static; }} }}
</style>
</head>
<body>
<header>
  <h1>Dream House · coordination review views</h1>
  <p>Scenario {scenario} · schema {schema} · input {input_hash} · model {model_hash}</p>
  <span class="authority">NOT FOR CONSTRUCTION</span>
  <nav>{"".join(f'<a href="#section-{html.escape(name[:-4], quote=True)}">{html.escape(name[:-4].replace("-", " ").title())}</a>' for name in views)}</nav>
</header>
<div class="layout">
  <aside aria-label="Read-only element and evidence index">
    <section class="panel">
      <h2>Elements</h2>
      <label for="entity-search">Search snapshot elements</label>
      <input id="entity-search" type="search" autocomplete="off" spellcheck="false">
      <p class="helper">Select an element to highlight every projection of the same source identity.</p>
      <ul id="entity-list">{"".join(entity_rows)}</ul>
      <p id="selection-status" class="helper" aria-live="polite">No element selected.</p>
      <div id="selected-evidence" class="helper">Element source and status will appear here.</div>
    </section>
    <section class="panel">
      <h2>Evaluation evidence</h2>
      <p id="finding-filter-status" class="helper" aria-live="polite">Showing all {len(findings)} findings.</p>
      <ul>{"".join(finding_rows)}</ul>
    </section>
    <section class="panel helper">
      Review only. This page has no model editing or write-back capability. Search and selection affect presentation only.
    </section>
  </aside>
  <main aria-label="Generated coordination projections">{sections}</main>
</div>
<script>
(() => {{
  const search = document.getElementById('entity-search');
  const rows = [...document.querySelectorAll('.entity-row[data-search]')];
  const findingRows = [...document.querySelectorAll('.finding[data-entity-ids]')];
  const status = document.getElementById('selection-status');
  const evidence = document.getElementById('selected-evidence');
  const findingStatus = document.getElementById('finding-filter-status');
  let selectedId = null;
  function filterFindings(entityId) {{
    let visible = 0;
    findingRows.forEach((row) => {{
      const entityIds = JSON.parse(row.dataset.entityIds);
      const show = !entityId || entityIds.length === 0 || entityIds.includes(entityId);
      row.hidden = !show;
      if (show) visible += 1;
    }});
    findingStatus.textContent = entityId
      ? 'Showing ' + visible + ' findings linked to ' + entityId + '.'
      : 'Showing all ' + findingRows.length + ' findings.';
  }}
  function selectEntity(entityId, sourceButton) {{
    selectedId = entityId;
    document.querySelectorAll('[data-entity-id]').forEach((node) => {{
      node.classList.toggle('is-selected', node.dataset.entityId === entityId);
    }});
    document.querySelectorAll('[data-select-entity]').forEach((button) => {{
      const active = button.dataset.selectEntity === entityId;
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    }});
    status.textContent = 'Selected: ' + entityId;
    evidence.textContent = sourceButton?.dataset.evidence || entityId;
    filterFindings(entityId);
  }}
  document.addEventListener('click', (event) => {{
    const button = event.target.closest('[data-select-entity]');
    if (button) selectEntity(button.dataset.selectEntity, button);
  }});
  search.addEventListener('input', () => {{
    const query = search.value.trim().toLowerCase();
    rows.forEach((row) => {{ row.hidden = query !== '' && !row.dataset.search.includes(query); }});
  }});
  document.addEventListener('keydown', (event) => {{
    if (event.key === 'Escape' && selectedId) {{
      document.querySelectorAll('.is-selected').forEach((node) => node.classList.remove('is-selected'));
      document.querySelectorAll('[data-select-entity]').forEach((button) => button.setAttribute('aria-pressed', 'false'));
      selectedId = null;
      status.textContent = 'No element selected.';
      evidence.textContent = 'Element source and status will appear here.';
      filterFindings(null);
    }}
  }});
}})();
</script>
</body>
</html>"""


def render_views(snapshot: dict, evaluation: dict) -> dict[str, str]:
    """Return standalone SVG review projections and a self-contained HTML index.

    The function is deterministic and performs no filesystem or network operations.
    Geometry is read from ``snapshot`` only; findings are presented from ``evaluation``
    without being modified or recomputed.
    """
    if not isinstance(snapshot, Mapping) or not isinstance(evaluation, Mapping):
        raise TypeError("snapshot and evaluation must be mappings")
    views = {
        "plan-pb.svg": _render_plan(
            snapshot, evaluation, view_id="plan-pb", level="PB", title="Ground floor plan (PB)"
        ),
        "plan-p2.svg": _render_plan(
            snapshot, evaluation, view_id="plan-p2", level="P2", title="Upper floor plan (P2)"
        ),
        "elevation-side-a.svg": _render_elevation(
            snapshot, evaluation, view_id="elevation-side-a", facade="A", title="Side A elevation"
        ),
        "elevation-side-b.svg": _render_elevation(
            snapshot, evaluation, view_id="elevation-side-b", facade="B", title="Side B elevation"
        ),
        "elevation-front.svg": _render_elevation(
            snapshot, evaluation, view_id="elevation-front", facade="FRONT", title="Front elevation"
        ),
        "elevation-rear.svg": _render_elevation(
            snapshot, evaluation, view_id="elevation-rear", facade="REAR", title="Rear elevation"
        ),
        "window-details.svg": _render_window_details(snapshot, evaluation),
    }
    views["index.html"] = _render_html(snapshot, evaluation, views)
    return views

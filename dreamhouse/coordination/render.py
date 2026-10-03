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
.semantic-anchor { fill: var(--paper); stroke: var(--info); stroke-width: 1; }
.semantic-anchor-label { fill: var(--info); font-size: 8px; font-weight: 700; }
.entity-shape { vector-effect: non-scaling-stroke; }
.entity-occurrence.is-selected .entity-shape { stroke: #BD7626 !important; stroke-width: 4px !important; }
.semantic-anchor.is-selected { fill: #F5DBA7; stroke: #BD7626; stroke-width: 2.5px; }
.dimension.is-selected { fill: #8A5A16; font-weight: 800; }
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


def _raw_n(value: float) -> str:
    """Keep model precision in semantic metadata; visual labels use ``_n``/``_dim``."""
    return format(value, ".12g") if value else "0"


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


def _semantic_anchor(
    parent: ET.Element,
    view_id: str,
    entity_id: str,
    name: str,
    x: float,
    y: float,
    *,
    world: Mapping[str, float | None] | None = None,
    source: str = "geometry",
    radius: float = 2.6,
    context_id: str | None = None,
) -> tuple[str, str]:
    """Add a stable semantic anchor with a unique target in this SVG view."""
    semantic_id = f"{entity_id}.{name}"
    target_id = f"{view_id}-anchor-{_token(entity_id)}-{_token(name)}"
    attrs = {
        "id": target_id,
        "class": "semantic-anchor",
        "data-anchor-id": semantic_id,
        "data-anchor-name": name,
        "data-anchor-status": "resolved",
        "data-anchor-source": source,
    }
    attrs["data-anchor-context-id" if context_id else "data-anchor-entity-id"] = (
        context_id if context_id else entity_id
    )
    for axis in ("x", "y", "z"):
        value = _number((world or {}).get(axis))
        if value is not None:
            attrs[f"data-world-{axis}"] = _raw_n(value)
    _circle(
        parent,
        x,
        y,
        radius,
        fill=COLOURS["paper"],
        stroke=COLOURS["info"],
        stroke_width=1,
        **attrs,
    )
    return semantic_id, target_id


def _unresolved_anchor(
    parent: ET.Element,
    view_id: str,
    entity_id: str,
    name: str,
    reason: str,
    *,
    context_id: str | None = None,
    unowned: bool = False,
) -> tuple[str, str]:
    semantic_id = f"{entity_id}.{name}"
    target_id = f"{view_id}-anchor-{_token(entity_id)}-{_token(name)}"
    node = ET.SubElement(
        parent,
        _q("g"),
        {
            "id": target_id,
            "data-anchor-id": semantic_id,
            "data-anchor-name": name,
            "data-anchor-status": "unresolved",
            "data-anchor-reason": reason,
        },
    )
    if context_id:
        node.set("data-anchor-context-id", context_id)
    elif not unowned:
        node.set("data-anchor-entity-id", entity_id)
    return semantic_id, target_id


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
        attrs[f"data-world-{axis}"] = "" if value is None else _raw_n(value)
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
    root: ET.Element,
    view_id: str,
    evaluation: Mapping[str, Any],
    visible_ids: set[str],
    *,
    include_unlinked: bool = True,
) -> dict[int, tuple[int, int]]:
    x, y, width, height = 1010, 152, 390, 720
    _rect(root, x, y, width, height, fill=COLOURS["panel"], stroke=COLOURS["rule"], rx=5)
    _text(root, x + 20, y + 30, "Evidence and rule findings", size=15, css="panel-title")
    active: list[dict[str, Any]] = []
    group_index: dict[tuple[str, str, str], int] = {}
    for finding_index, record in enumerate(_finding_records(evaluation)):
        status = str(record.get("status", "")).upper()
        ids = {str(value) for value in record.get("entity_ids", [])}
        if status in {"OPEN", "FAIL"} and (
            ids.intersection(visible_ids) or (include_unlinked and not ids)
        ):
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
    # Show definite failures first, then the evidence linked to this view before
    # unlocated discipline benchmarks can fill the limited panel.
    active.sort(
        key=lambda item: (
            str(item["record"].get("status", "")).upper() != "FAIL",
            not bool(item["entity_ids"].intersection(visible_ids)),
        )
    )
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
            "data-world-x0": _raw_n(origin_x),
            "data-world-y0": "0",
            "data-world-x1": _raw_n(origin_x + length),
            "data-world-y1": _raw_n(width),
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
        envelope_id = "PROJECT.P2" if envelope_source.endswith(".p2") else "PROJECT.PB"
        length_anchor_refs = (f"{envelope_id}.extent.x0", f"{envelope_id}.extent.x1")
        width_anchor_refs = (f"{envelope_id}.extent.y0", f"{envelope_id}.extent.y1")
        length_anchor_targets = (
            _semantic_anchor(
                root,
                view_id,
                envelope_id,
                "extent.x0",
                x0,
                y1,
                world={"x": origin_x, "y": 0},
                source="snapshot.geometry.p2"
                if envelope_id == "PROJECT.P2"
                else "snapshot.geometry.hall",
                context_id=envelope_id,
            )[1],
            _semantic_anchor(
                root,
                view_id,
                envelope_id,
                "extent.x1",
                x1,
                y1,
                world={"x": origin_x + length, "y": 0},
                source="snapshot.geometry.p2"
                if envelope_id == "PROJECT.P2"
                else "snapshot.geometry.hall",
                context_id=envelope_id,
            )[1],
        )
        width_anchor_targets = (
            _semantic_anchor(
                root,
                view_id,
                envelope_id,
                "extent.y0",
                x0,
                y1,
                world={"x": origin_x, "y": 0},
                source="snapshot.geometry.p2"
                if envelope_id == "PROJECT.P2"
                else "snapshot.geometry.hall",
                context_id=envelope_id,
            )[1],
            _semantic_anchor(
                root,
                view_id,
                envelope_id,
                "extent.y1",
                x0,
                y0,
                world={"x": origin_x, "y": width},
                source="snapshot.geometry.p2"
                if envelope_id == "PROJECT.P2"
                else "snapshot.geometry.hall",
                context_id=envelope_id,
            )[1],
        )
        _horizontal_dimension(
            root,
            x0,
            x1,
            y1,
            y1 + 35,
            length,
            f"{view_id}-{envelope_id}-plan-length",
            envelope_id,
            anchor_refs=length_anchor_refs,
            anchor_targets=length_anchor_targets,
            datum=f"{envelope_source}.x",
        )
        _vertical_dimension(
            root,
            x0,
            y0,
            y1,
            x0 - 35,
            width,
            f"{view_id}-{envelope_id}-plan-width",
            envelope_id,
            anchor_refs=width_anchor_refs,
            anchor_targets=width_anchor_targets,
            datum=f"{envelope_source}.y",
        )

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
        if str(entity.get("kind", "")).lower() == "opening":
            bounds = _rect_geometry(_geom(entity))
            facade = str(_params(entity).get("facade", "")).upper()
            z_anchor = _number(_geom(entity).get("z0"))
            if bounds is not None and facade != "ROOF":
                x_start, x_end, y_start, y_end = bounds
                if facade in {"FRONT", "REAR"}:
                    start_xy, end_xy = (x_start, y_start), (x_start, y_end)
                else:
                    start_xy, end_xy = (x_start, y_start), (x_end, y_start)
                for name, world_point in (("opening.start", start_xy), ("opening.end", end_xy)):
                    point_x, point_y = transform(*world_point)
                    _semantic_anchor(
                        group,
                        view_id,
                        entity_id,
                        name,
                        point_x,
                        point_y,
                        world={"x": world_point[0], "y": world_point[1], "z": z_anchor},
                        source="snapshot.entities.geometry",
                    )
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
    anchor_refs: tuple[str, str] | None = None,
    anchor_targets: tuple[str, str] | None = None,
    datum: str | None = None,
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
        "data-dimension-id": dimension_id,
        "data-dimension-for": entity_id or dimension_id,
        "data-dimension-value": _raw_n(value),
        "data-dimension-source": dimension_source,
        "data-dimension-direction": "horizontal",
        "data-dimension-status": "resolved" if anchor_refs and anchor_targets else "unanchored",
    }
    if anchor_refs:
        attrs["data-anchor-refs"] = " ".join(anchor_refs)
    if anchor_targets:
        attrs["data-anchor-targets"] = " ".join(anchor_targets)
    if datum:
        attrs["data-datum"] = datum
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
    anchor_refs: tuple[str, str] | None = None,
    anchor_targets: tuple[str, str] | None = None,
    datum: str | None = None,
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
        "data-dimension-id": dimension_id,
        "data-dimension-for": entity_id or dimension_id,
        "data-dimension-value": _raw_n(value),
        "data-dimension-source": dimension_source,
        "data-dimension-direction": "vertical",
        "data-dimension-status": "resolved" if anchor_refs and anchor_targets else "unanchored",
    }
    if anchor_refs:
        attrs["data-anchor-refs"] = " ".join(anchor_refs)
    if anchor_targets:
        attrs["data-anchor-targets"] = " ".join(anchor_targets)
    if datum:
        attrs["data-datum"] = datum
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
            opening_anchors: dict[str, tuple[str, str]] = {}
            dimensionable_kind = str(entity.get("kind", "")).lower()
            if dimensionable_kind in {"opening", "door"}:
                geometry = _geom(entity)
                params = _params(entity)
                fixed_a = _number(geometry.get("y0" if axis == "x" else "x0"))
                fixed_b = _number(geometry.get("y1" if axis == "x" else "x1"))
                fixed = (
                    (fixed_a + fixed_b) / 2 if fixed_a is not None and fixed_b is not None else None
                )
                sill_level = vertical[0]
                head_level = vertical[1]
                anchor_specs = (
                    (
                        ("opening.start", horizontal[0], sill_level),
                        ("opening.end", horizontal[1], sill_level),
                        ("opening.sill", (horizontal[0] + horizontal[1]) / 2, sill_level),
                        ("opening.head", (horizontal[0] + horizontal[1]) / 2, head_level),
                    )
                    if dimensionable_kind == "opening"
                    else (
                        ("extent.start", horizontal[0], sill_level),
                        ("extent.end", horizontal[1], sill_level),
                        ("extent.bottom", (horizontal[0] + horizontal[1]) / 2, sill_level),
                        ("extent.top", (horizontal[0] + horizontal[1]) / 2, head_level),
                    )
                )
                for name, along, elevation in anchor_specs:
                    screen_x, screen_y = to_screen(along, elevation)
                    world = (
                        {"x": along, "y": fixed, "z": elevation}
                        if axis == "x"
                        else {"x": fixed, "y": along, "z": elevation}
                    )
                    opening_anchors[name] = _semantic_anchor(
                        group,
                        view_id,
                        entity_id,
                        name,
                        screen_x,
                        screen_y,
                        world=world,
                        source=vertical[2],
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
                    anchor_refs=(
                        f"{entity_id}.{('opening' if dimensionable_kind == 'opening' else 'extent')}.start",
                        f"{entity_id}.{('opening' if dimensionable_kind == 'opening' else 'extent')}.end",
                    )
                    if opening_anchors
                    else None,
                    anchor_targets=(
                        opening_anchors[
                            "opening.start" if dimensionable_kind == "opening" else "extent.start"
                        ][1],
                        opening_anchors[
                            "opening.end" if dimensionable_kind == "opening" else "extent.end"
                        ][1],
                    )
                    if opening_anchors
                    else None,
                    datum=f"facade {plane_label} · model {axis.upper()}",
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
                    anchor_refs=(
                        f"{entity_id}.{('opening' if dimensionable_kind == 'opening' else 'extent')}.{('sill' if dimensionable_kind == 'opening' else 'bottom')}",
                        f"{entity_id}.{('opening' if dimensionable_kind == 'opening' else 'extent')}.{('head' if dimensionable_kind == 'opening' else 'top')}",
                    )
                    if opening_anchors
                    else None,
                    anchor_targets=(
                        opening_anchors[
                            "opening.sill" if dimensionable_kind == "opening" else "extent.bottom"
                        ][1],
                        opening_anchors[
                            "opening.head" if dimensionable_kind == "opening" else "extent.top"
                        ][1],
                    )
                    if opening_anchors
                    else None,
                    datum="project elevation above PB ±0.00 m",
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
                    if dimensionable_kind == "opening" and opening_anchors:
                        _text(
                            group,
                            x0,
                            y1 - 21,
                            "SILL DATUM",
                            size=7.5,
                            css="semantic-anchor-label",
                            **{
                                "data-anchor-ref": f"{entity_id}.opening.sill",
                                "data-anchor-target": opening_anchors["opening.sill"][1],
                            },
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
            opening_anchors: dict[str, tuple[str, str]] = {}
            if is_roof and plan_bounds:
                px0, px1, py0, py1 = plan_bounds
                for name, screen_x, screen_y, world_x, world_y in (
                    ("plan.x0", shape_x, shape_y + shape_height, px0, py0),
                    ("plan.x1", shape_x + shape_width, shape_y + shape_height, px1, py0),
                    ("plan.y0", shape_x, shape_y + shape_height, px0, py0),
                    ("plan.y1", shape_x, shape_y, px0, py1),
                ):
                    opening_anchors[name] = _semantic_anchor(
                        group,
                        view_id,
                        entity_id,
                        name,
                        screen_x,
                        screen_y,
                        world={"x": world_x, "y": world_y},
                        source="snapshot.entities.geometry",
                    )
            elif not is_roof:
                geometry_z = _number(geometry.get("z0"))
                geometry_head = _number(geometry.get("z1"))
                along = _horizontal_extent(entity, horizontal_axis)
                plan_extent = _rect_geometry(geometry)
                fixed_world = (
                    (plan_extent[2] + plan_extent[3]) / 2
                    if plan_extent and horizontal_axis == "x"
                    else (plan_extent[0] + plan_extent[1]) / 2
                    if plan_extent
                    else None
                )

                def detail_world(
                    along_value: float | None,
                    elevation: float | None,
                    horizontal_axis: str = horizontal_axis,
                    fixed_world: float | None = fixed_world,
                ) -> dict[str, float | None]:
                    if horizontal_axis == "x":
                        return {"x": along_value, "y": fixed_world, "z": elevation}
                    return {"x": fixed_world, "y": along_value, "z": elevation}

                opening_anchors["opening.start"] = _semantic_anchor(
                    group,
                    view_id,
                    entity_id,
                    "opening.start",
                    shape_x,
                    shape_y + shape_height,
                    world=detail_world(along[0] if along else None, geometry_z),
                    source=vertical[2] if vertical else "opening-parameters",
                )
                opening_anchors["opening.end"] = _semantic_anchor(
                    group,
                    view_id,
                    entity_id,
                    "opening.end",
                    shape_x + shape_width,
                    shape_y + shape_height,
                    world=detail_world(along[1] if along else None, geometry_z),
                    source=vertical[2] if vertical else "opening-parameters",
                )
                if display_height is not None:
                    sill_z = vertical[0] if vertical else geometry_z
                    head_z = vertical[1] if vertical else geometry_head
                    opening_anchors["opening.sill"] = _semantic_anchor(
                        group,
                        view_id,
                        entity_id,
                        "opening.sill",
                        shape_x + shape_width / 2,
                        shape_y + shape_height,
                        world=detail_world((along[0] + along[1]) / 2 if along else None, sill_z),
                        source=vertical[2] if vertical else "opening-parameters",
                    )
                    opening_anchors["opening.head"] = _semantic_anchor(
                        group,
                        view_id,
                        entity_id,
                        "opening.head",
                        shape_x + shape_width / 2,
                        shape_y,
                        world=detail_world((along[0] + along[1]) / 2 if along else None, head_z),
                        source=vertical[2] if vertical else "opening-parameters",
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
                anchor_refs=(
                    (f"{entity_id}.plan.x0", f"{entity_id}.plan.x1")
                    if is_roof
                    else (f"{entity_id}.opening.start", f"{entity_id}.opening.end")
                )
                if opening_anchors
                else None,
                anchor_targets=(
                    (opening_anchors["plan.x0"][1], opening_anchors["plan.x1"][1])
                    if is_roof
                    else (
                        opening_anchors["opening.start"][1],
                        opening_anchors["opening.end"][1],
                    )
                )
                if opening_anchors
                else None,
                datum=f"facade {facade} · opening width axis",
            )
            if vertical or is_roof or display_height is not None:
                _vertical_dimension(
                    group,
                    shape_x + shape_width,
                    shape_y,
                    shape_y + shape_height,
                    shape_x + shape_width + 18,
                    display_height,
                    f"{view_id}-{entity_id}-detail-span",
                    entity_id,
                    dimension_source="geometry"
                    if is_roof
                    else vertical[2]
                    if vertical
                    else "opening-parameters",
                    anchor_refs=(
                        (f"{entity_id}.plan.y0", f"{entity_id}.plan.y1")
                        if is_roof
                        else (f"{entity_id}.opening.sill", f"{entity_id}.opening.head")
                    )
                    if opening_anchors and (is_roof or "opening.sill" in opening_anchors)
                    else None,
                    anchor_targets=(
                        (opening_anchors["plan.y0"][1], opening_anchors["plan.y1"][1])
                        if is_roof
                        else (
                            opening_anchors["opening.sill"][1],
                            opening_anchors["opening.head"][1],
                        )
                    )
                    if opening_anchors and (is_roof or "opening.sill" in opening_anchors)
                    else None,
                    datum="project elevation above PB ±0.00 m",
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
                    "data-dimension-id": f"{view_id}-{entity_id}-height",
                    "data-dimension-for": entity_id,
                    "data-dimension-value": _raw_n(display_height),
                    "data-dimension-source": "geometry"
                    if is_roof
                    else vertical[2]
                    if vertical
                    else "opening-parameters",
                    "data-dimension-direction": "vertical",
                    "data-dimension-status": "resolved"
                    if opening_anchors and (is_roof or "opening.sill" in opening_anchors)
                    else "unanchored",
                    "data-anchor-refs": (
                        f"{entity_id}.plan.y0 {entity_id}.plan.y1"
                        if is_roof
                        else f"{entity_id}.opening.sill {entity_id}.opening.head"
                    )
                    if opening_anchors and (is_roof or "opening.sill" in opening_anchors)
                    else "",
                    "data-anchor-targets": " ".join(
                        (opening_anchors["plan.y0"][1], opening_anchors["plan.y1"][1])
                        if is_roof
                        else (
                            opening_anchors["opening.sill"][1],
                            opening_anchors["opening.head"][1],
                        )
                    )
                    if opening_anchors and (is_roof or "opening.sill" in opening_anchors)
                    else "",
                    "data-datum": "project elevation above PB ±0.00 m",
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
            if opening_anchors and "opening.sill" in opening_anchors:
                _text(
                    group,
                    x + 286,
                    y + 154,
                    "SILL DATUM",
                    size=7.5,
                    css="semantic-anchor-label",
                    **{
                        "data-anchor-ref": f"{entity_id}.opening.sill",
                        "data-anchor-target": opening_anchors["opening.sill"][1],
                    },
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


def _quantity_record(evaluation: Mapping[str, Any], record_id: str) -> Mapping[str, Any] | None:
    ledger = evaluation.get("quantity_ledger", {})
    records = ledger.get("records", []) if isinstance(ledger, Mapping) else []
    if not isinstance(records, list):
        return None
    return next(
        (
            record
            for record in records
            if isinstance(record, Mapping) and str(record.get("id", "")) == record_id
        ),
        None,
    )


def _workstation_for_opening(
    snapshot: Mapping[str, Any], opening_id: str
) -> Mapping[str, Any] | None:
    discipline_inputs = snapshot.get("discipline_inputs", {})
    discipline_inputs = discipline_inputs if isinstance(discipline_inputs, Mapping) else {}
    equipment = discipline_inputs.get("equipment", {})
    equipment = equipment if isinstance(equipment, Mapping) else {}
    pb = equipment.get("pb", {})
    pb = pb if isinstance(pb, Mapping) else {}
    workstations = pb.get("workstations", [])
    if isinstance(workstations, Mapping):
        workstations = list(workstations.values())
    if not isinstance(workstations, list):
        return None
    return next(
        (
            record
            for record in workstations
            if isinstance(record, Mapping) and str(record.get("window_id", "")) == opening_id
        ),
        None,
    )


def _render_window_sections(snapshot: Mapping[str, Any], evaluation: Mapping[str, Any]) -> str:
    """Render a bounded, source-derived opening section and unresolved interface plate."""
    view_id = "window-sections"
    opening_id = "GLZ-WS-A"
    entities = dict(_entity_pairs(snapshot))
    opening = entities.get(opening_id)
    if not isinstance(opening, Mapping) or str(opening.get("kind", "")).lower() != "opening":
        opening = None
    source = opening.get("source", {}) if opening else {}
    source = source if isinstance(source, Mapping) else {}
    params = _params(opening) if opening else {}
    geometry = _geom(opening) if opening else {}
    vertical = _vertical_extent(opening) if opening else None
    horizontal = _horizontal_extent(opening, "x") if opening else None
    level = _number(params.get("level_m"))
    sill_relative = _number(params.get("sill_m"))
    sill_absolute = vertical[0] if vertical else None
    head_absolute = vertical[1] if vertical else None
    opening_height = (
        head_absolute - sill_absolute
        if head_absolute is not None and sill_absolute is not None
        else None
    )
    opening_width = horizontal[1] - horizontal[0] if horizontal else None
    midspan = (horizontal[0] + horizontal[1]) / 2 if horizontal else None
    facade = str(params.get("facade", "A")).upper()
    elevation_view = {
        "A": "elevation-side-a",
        "B": "elevation-side-b",
        "FRONT": "elevation-front",
        "REAR": "elevation-rear",
    }.get(facade, "elevation-side-a")
    relationships = opening.get("relationships", {}) if opening else {}
    relationships = relationships if isinstance(relationships, Mapping) else {}
    host_id = str(relationships.get("host_id") or "")
    host = entities.get(host_id) if host_id else None
    host_geometry = _geom(host) if isinstance(host, Mapping) else {}
    host_shape = str(host_geometry.get("shape", "unknown"))
    host_vertical_known = (
        _number(host_geometry.get("z0")) is not None
        and _number(host_geometry.get("z1")) is not None
    )
    worktop = _workstation_for_opening(snapshot, opening_id) if opening else None
    worktop_id = str(worktop.get("id", "PB-WS-A")) if worktop else "WORKTOP-UNRESOLVED"
    worktop_height = _number(worktop.get("worktop_height")) if worktop else None
    worktop_depth = _number(worktop.get("worktop_depth")) if worktop else None
    worktop_absolute = (
        level + worktop_height if level is not None and worktop_height is not None else None
    )
    worktop_delta = (
        worktop_height - sill_relative
        if worktop_height is not None and sill_relative is not None
        else None
    )
    quantity = _quantity_record(evaluation, f"Q-{opening_id}-AREA")

    root = _root(
        snapshot,
        view_id,
        "Window section and interface review",
        "Source-derived opening sill and head datums with an explicit worktop level comparison. "
        "Host thickness, glazing assembly, support, drainage and control-layer paths remain unresolved.",
    )
    root.set("data-view-purpose", "coordination section and interface evidence")
    root.set("data-projection-basis", "section datum comparison in project elevation")
    root.set("data-section-id", "WS-A-01")
    root.set("data-cut-plane-axis", "X")
    if midspan is not None:
        root.set("data-cut-plane-value-m", _raw_n(midspan))
        root.set("data-cut-plane", f"X={_n(midspan)} m · GLZ-WS-A source midspan")
    else:
        root.set("data-cut-plane", "X unavailable · opening bounds unresolved")
    root.set("data-cut-depth-range", "unknown · host solid thickness is not supplied")
    root.set("data-section-members", opening_id if opening else "")
    _frame(
        root,
        snapshot,
        view_id,
        "Window section and interface review",
        "GLZ-WS-A · source datums, linked worktop context and unresolved envelope interfaces",
    )

    _rect(
        root,
        60,
        145,
        890,
        345,
        fill=COLOURS["panel"],
        stroke=COLOURS["rule"],
        rx=4,
        id=f"{view_id}-section-panel",
        **{
            "data-panel-id": "section-datum-comparison",
            "data-cut-intent": "vertical level section through opening source midspan",
            "data-cut-depth-range": "unknown",
        },
    )
    _text(root, 78, 174, "A–A · OPENING / WORKTOP ELEVATION DATUMS", size=13, css="panel-title")
    _text(
        root,
        78,
        193,
        "Section intent: compare source elevations only. Horizontal spacing is schematic; no wall profile or glazing is represented.",
        size=9,
        css="small",
    )

    opening_anchor_nodes: dict[str, tuple[str, str]] = {}
    worktop_anchor: tuple[str, str] | None = None
    unresolved_opening_reason = "opening sill/head geometry or parameters are unavailable"
    if opening and vertical and horizontal and opening_height is not None and opening_height > 0:
        panel_top, panel_bottom = 222.0, 446.0
        candidate_levels = [vertical[0], vertical[1]]
        if level is not None:
            candidate_levels.append(level)
        if worktop_absolute is not None:
            candidate_levels.append(worktop_absolute)
        z_min, z_max = min(candidate_levels), max(candidate_levels)
        z_margin = max((z_max - z_min) * 0.14, 0.18)
        z_min -= z_margin
        z_max += z_margin

        def to_level_y(elevation: float) -> float:
            return panel_bottom - (elevation - z_min) * (panel_bottom - panel_top) / (z_max - z_min)

        opening_x = 325.0
        sill_y, head_y = to_level_y(sill_absolute), to_level_y(head_absolute)
        section_group = _entity_group(root, view_id, opening_id, opening, 0)
        section_group.set("data-section-membership", "cut-envelope")
        _text(root, 103, 221, "PROJECT Z (m)", size=8, css="eyebrow")
        _line(
            section_group,
            opening_x,
            head_y,
            opening_x,
            sill_y,
            stroke=COLOURS["info"],
            width=2,
            dash="7 4",
            **{
                "id": f"{view_id}-entity-{_token(opening_id)}-section-extent",
                "data-section-membership": "opening vertical extent only",
                "data-section-geometry": "source-derived datum line; no filling or host profile",
            },
        )
        opening_anchor_nodes["opening.sill"] = _semantic_anchor(
            section_group,
            view_id,
            opening_id,
            "opening.sill",
            opening_x,
            sill_y,
            world={"x": midspan, "y": _number(geometry.get("y0")), "z": sill_absolute},
            source=vertical[2],
        )
        opening_anchor_nodes["opening.head"] = _semantic_anchor(
            section_group,
            view_id,
            opening_id,
            "opening.head",
            opening_x,
            head_y,
            world={"x": midspan, "y": _number(geometry.get("y0")), "z": head_absolute},
            source=vertical[2],
        )
        datum_label = f"PB level {level:+.2f} m" if level is not None else "PB level unavailable"
        if level is not None:
            datum_y = to_level_y(level)
            _line(root, 110, datum_y, 868, datum_y, stroke=COLOURS["muted"], width=0.8, dash="4 4")
            datum_ref, _datum_target = _semantic_anchor(
                root,
                view_id,
                "PROJECT.PB",
                "finished-floor",
                110,
                datum_y,
                world={"z": level},
                source="snapshot PB datum",
                context_id="PROJECT.PB",
            )
            _text(root, 115, datum_y - 5, datum_label, size=8, css="small")
            if sill_relative is not None:
                floor_target = f"{view_id}-anchor-{_token('PROJECT.PB')}-{_token('finished-floor')}"
                _vertical_dimension(
                    root,
                    opening_x,
                    datum_y,
                    sill_y,
                    opening_x - 54,
                    sill_relative,
                    f"{view_id}-{opening_id}-sill-above-level",
                    opening_id,
                    dimension_source="opening-parameters",
                    anchor_refs=(datum_ref, f"{opening_id}.opening.sill"),
                    anchor_targets=(floor_target, opening_anchor_nodes["opening.sill"][1]),
                    datum="PB finished-floor level",
                )
        _vertical_dimension(
            root,
            opening_x,
            head_y,
            sill_y,
            opening_x + 62,
            opening_height,
            f"{view_id}-{opening_id}-opening-height",
            opening_id,
            dimension_source=vertical[2],
            anchor_refs=(f"{opening_id}.opening.sill", f"{opening_id}.opening.head"),
            anchor_targets=(
                opening_anchor_nodes["opening.sill"][1],
                opening_anchor_nodes["opening.head"][1],
            ),
            datum="opening sill to head",
        )
        _text(
            root,
            opening_x,
            head_y - 11,
            f"HEAD +{head_absolute:.2f} m",
            size=8,
            css="small",
            anchor="middle",
        )
        _text(
            root,
            opening_x,
            sill_y + 15,
            f"SILL +{sill_absolute:.2f} m",
            size=8,
            css="small",
            anchor="middle",
        )
        _text(root, 225, 460, "OPENING PLANE · extent only", size=8, css="small", anchor="middle")

        if worktop_height is not None and worktop_absolute is not None:
            worktop_y = to_level_y(worktop_absolute)
            _line(
                root,
                540,
                worktop_y,
                855,
                worktop_y,
                stroke=COLOURS["study"],
                width=1.8,
                dash="6 4",
                **{
                    "data-context-entity-id": worktop_id,
                    "data-section-membership": "worktop datum context only",
                    "data-source-context": f"discipline_inputs.equipment.pb.workstations[{worktop_id}].worktop_height",
                },
            )
            worktop_anchor = _semantic_anchor(
                root,
                view_id,
                worktop_id,
                "worktop.top",
                540,
                worktop_y,
                world={"z": worktop_absolute},
                source=f"discipline_inputs.equipment.pb.workstations[{worktop_id}].worktop_height",
                context_id=worktop_id,
            )
            _text(
                root,
                548,
                worktop_y - 8,
                f"{worktop_id} worktop top · +{worktop_height:.2f} m from PB floor",
                size=8,
                css="small",
            )
            if worktop_depth is not None:
                _text(
                    root,
                    548,
                    worktop_y + 14,
                    f"Source depth {_dim(worktop_depth)}; position relative to glazing unresolved.",
                    size=8,
                    css="small",
                )
            if worktop_delta is not None:
                delta_text = _text(
                    root,
                    555,
                    455,
                    f"Δz worktop − sill = {worktop_delta:+.2f} m",
                    size=9,
                    css="dimension",
                    **{
                        "data-dimension-id": f"{view_id}-{opening_id}-worktop-sill-level-difference",
                        "data-dimension-for": opening_id,
                        "data-dimension-value": _raw_n(worktop_delta),
                        "data-dimension-unit": "m",
                        "data-dimension-source": "opening parameters + discipline equipment context",
                        "data-dimension-direction": "vertical level comparison",
                        "data-dimension-status": "resolved",
                        "data-anchor-refs": f"{opening_id}.opening.sill {worktop_id}.worktop.top",
                        "data-anchor-targets": " ".join(
                            (opening_anchor_nodes["opening.sill"][1], worktop_anchor[1])
                        ),
                        "data-datum": "PB finished-floor level",
                    },
                )
                ET.SubElement(delta_text, _q("title")).text = (
                    "Level comparison only; it does not establish physical contact, clearance, "
                    "support or interface continuity."
                )
        else:
            missing_worktop_anchor = _unresolved_anchor(
                root,
                view_id,
                worktop_id,
                "worktop.top",
                "worktop height or PB floor datum is unavailable in the current snapshot",
                context_id=worktop_id if worktop else None,
                unowned=worktop is None,
            )
            worktop_unavailable_text = (
                "Worktop datum unavailable in snapshot; no value inferred."
                if worktop_height is None
                else "PB floor datum unavailable; worktop elevation cannot be placed."
            )
            _text(
                root,
                540,
                310,
                worktop_unavailable_text,
                size=9,
                css="small",
            )
            unresolved = _text(
                root,
                540,
                332,
                "Δz worktop − sill · unresolved",
                size=9,
                css="dimension",
                **{
                    "data-dimension-id": f"{view_id}-{opening_id}-worktop-sill-level-difference",
                    "data-dimension-for": opening_id,
                    "data-dimension-source": "missing discipline equipment context",
                    "data-dimension-direction": "vertical level comparison",
                    "data-dimension-status": "unresolved",
                    "data-anchor-refs": f"{opening_id}.opening.sill {worktop_id}.worktop.top",
                    "data-anchor-targets": " ".join(
                        (opening_anchor_nodes["opening.sill"][1], missing_worktop_anchor[1])
                    ),
                    "data-datum": "PB finished-floor level",
                },
            )
            ET.SubElement(
                unresolved, _q("title")
            ).text = "The sill anchor is resolved; the source worktop-height anchor is unavailable."
        full_source_note = (
            f"Source opening bounds: {source.get('path', 'path not supplied')} · "
            f"{source.get('key', 'key not supplied')}. Host reference {host_id or 'unresolved'}; "
            f"host shape {host_shape}; vertical solid extent "
            f"{'known' if host_vertical_known else 'unknown'}; wall depth remains unresolved."
        )
        source_note = _text(
            root,
            80,
            478,
            textwrap.shorten(full_source_note, width=148, placeholder="…"),
            size=8,
            css="small",
            **{
                "data-entity-ref": host_id,
                "data-section-membership": "related host reference only",
                "data-host-depth-status": "unresolved",
            },
        )
        ET.SubElement(source_note, _q("title")).text = full_source_note
    else:
        if opening:
            _unresolved_anchor(root, view_id, opening_id, "opening.sill", unresolved_opening_reason)
            _unresolved_anchor(root, view_id, opening_id, "opening.head", unresolved_opening_reason)
        _text(
            root,
            505,
            335,
            "GLZ-WS-A source opening extent is incomplete; section dimensions remain unresolved.",
            size=11,
            css="small",
            anchor="middle",
        )
        _text(root, 80, 478, "No wall or glazing profile is inferred.", size=8, css="small")

    interface_items = (
        ("head", "opening.head", "Header / head interface"),
        ("sill", "opening.sill", "Sill / drainage interface"),
        ("jamb", "opening.start opening.end", "Jamb interfaces"),
    )
    for index, (interface_id, anchor_names, title) in enumerate(interface_items):
        x = 60 + index * 300
        y = 510
        card = _rect(
            root,
            x,
            y,
            285,
            252,
            fill=COLOURS["panel"],
            stroke=COLOURS["rule"],
            rx=4,
            id=f"{view_id}-interface-{interface_id}",
            **{
                "data-interface-id": f"{opening_id}.{interface_id}",
                "data-interface-status": "unknown",
                "data-schematic-only": "true",
            },
        )
        refs = [f"{opening_id}.{name}" for name in anchor_names.split()]
        target_ids = [
            f"{elevation_view}-anchor-{_token(opening_id)}-{_token(name)}"
            for name in anchor_names.split()
        ]
        callout_resolved = bool(opening and vertical and horizontal)
        card.set("data-callout-id", f"{view_id}-callout-{interface_id}")
        if callout_resolved:
            card.set("data-callout-refs", " ".join(refs))
            card.set("data-callout-target-view-id", elevation_view)
            card.set("data-callout-targets", " ".join(target_ids))
        else:
            card.set("data-callout-status", "unresolved")
            card.set(
                "data-callout-reason", "required opening anchors are unavailable in the snapshot"
            )
        _text(root, x + 14, y + 25, title, size=10, css="panel-title")
        badge_parent = root
        if callout_resolved:
            badge_link = ET.SubElement(
                root,
                _q("a"),
                {
                    "href": f"{elevation_view}.svg#{target_ids[0]}",
                    "aria-label": f"Open {elevation_view} at {refs[0]}",
                    "data-callout-link": f"{view_id}-callout-{interface_id}",
                },
            )
            badge_parent = badge_link
        badge = _circle(
            badge_parent,
            x + 260,
            y + 21,
            11,
            fill="#FFFDFA",
            stroke="#8A5A16",
            stroke_width=1.5,
            **{"class": "callout"},
        )
        badge.set("data-callout-status", "resolved" if callout_resolved else "unresolved")
        _text(
            badge_parent,
            x + 260,
            y + 24,
            chr(65 + index),
            size=9,
            css="body",
            anchor="middle",
            fill="#172A32",
            **{"font-weight": "700"},
        )
        _text(root, x + 14, y + 47, "Water", size=8.5, css="small")
        _text(root, x + 14, y + 77, "Air control", size=8.5, css="small")
        _text(root, x + 14, y + 107, "Thermal", size=8.5, css="small")
        for lane in range(3):
            cy = y + 44 + lane * 30
            _line(root, x + 78, cy, x + 135, cy, stroke=COLOURS["muted"], width=1.5, dash="4 3")
            _line(root, x + 151, cy, x + 202, cy, stroke=COLOURS["muted"], width=1.5, dash="4 3")
            _line(root, x + 137, cy - 5, x + 145, cy + 5, stroke=COLOURS["open"], width=1.2)
            _line(root, x + 145, cy - 5, x + 153, cy + 5, stroke=COLOURS["open"], width=1.2)
        _text(
            root,
            x + 14,
            y + 145,
            "Continuity path: unresolved",
            size=9,
            css="finding-heading",
            fill=COLOURS["open"],
        )
        _text(
            root, x + 14, y + 165, "No assembly layer, material, fixing or", size=8.5, css="small"
        )
        _text(
            root,
            x + 14,
            y + 180,
            "tolerance is supplied for this interface.",
            size=8.5,
            css="small",
        )
        _text(
            root,
            x + 14,
            y + 212,
            "Callout references the same GLZ-WS-A opening.",
            size=8,
            css="small",
        )

    _rect(
        root,
        60,
        765,
        890,
        125,
        fill=COLOURS["panel"],
        stroke=COLOURS["rule"],
        rx=4,
        **{"data-panel-id": "quantity-and-interface-evidence"},
    )
    _text(root, 78, 792, "SOURCE-DERIVED OPENING MEASUREMENT", size=10, css="panel-title")
    width_anchor_targets: tuple[str, str] | None = None
    width_anchor_refs = (f"{opening_id}.opening.start", f"{opening_id}.opening.end")
    if opening and horizontal is not None:
        width_y = 818.0
        width_anchor_targets = (
            _semantic_anchor(
                root,
                view_id,
                opening_id,
                "opening.start",
                82,
                width_y,
                world={"x": horizontal[0], "y": _number(geometry.get("y0")), "z": sill_absolute},
                source="snapshot.entities.geometry",
            )[1],
            _semantic_anchor(
                root,
                view_id,
                opening_id,
                "opening.end",
                250,
                width_y,
                world={"x": horizontal[1], "y": _number(geometry.get("y0")), "z": sill_absolute},
                source="snapshot.entities.geometry",
            )[1],
        )
        _horizontal_dimension(
            root,
            82,
            250,
            width_y,
            845,
            opening_width,
            f"{view_id}-{opening_id}-width-summary",
            opening_id,
            dimension_source="snapshot.entities.geometry",
            anchor_refs=width_anchor_refs,
            anchor_targets=width_anchor_targets,
            datum=f"facade {facade} · source opening width axis",
        )
        _text(root, 78, 866, "Opening width basis · façade axis", size=8, css="small")
    else:
        _text(root, 78, 834, "Opening width anchors unresolved.", size=9, css="small")
    if opening_height is not None and opening_anchor_nodes:
        _text(
            root,
            300,
            840,
            f"Height {_dim(opening_height)}",
            size=9,
            css="body",
            **{
                "data-dimension-id": f"{view_id}-{opening_id}-height-summary",
                "data-dimension-for": opening_id,
                "data-dimension-value": _raw_n(opening_height),
                "data-dimension-unit": "m",
                "data-dimension-source": vertical[2] if vertical else "opening-parameters",
                "data-dimension-direction": "vertical",
                "data-dimension-status": "resolved",
                "data-anchor-refs": f"{opening_id}.opening.sill {opening_id}.opening.head",
                "data-anchor-targets": " ".join(
                    (
                        opening_anchor_nodes["opening.sill"][1],
                        opening_anchor_nodes["opening.head"][1],
                    )
                ),
                "data-datum": "project elevation above PB ±0.00 m",
            },
        )
    else:
        _text(root, 300, 840, "Height anchors unresolved.", size=9, css="small")
    anchors_for_quantity = (
        bool(opening_anchor_nodes)
        and width_anchor_targets is not None
        and "opening.sill" in opening_anchor_nodes
        and "opening.head" in opening_anchor_nodes
    )
    if (
        quantity is not None
        and _number(quantity.get("quantity")) is not None
        and anchors_for_quantity
    ):
        quantity_value = float(_number(quantity.get("quantity")))
        quantity_unit = str(quantity.get("unit", "unit unknown"))
        q_text = _text(
            root,
            460,
            825,
            f"Nominal opening area {quantity_value:.2f} {quantity_unit}",
            size=9,
            css="body",
            **{
                "data-quantity-id": str(quantity.get("id")),
                "data-dimension-id": f"{view_id}-{quantity.get('id')}",
                "data-dimension-for": opening_id,
                "data-dimension-value": _raw_n(quantity_value),
                "data-dimension-unit": quantity_unit,
                "data-dimension-source": "evaluation.quantity_ledger",
                "data-dimension-formula": str(quantity.get("formula", "not supplied")),
                "data-dimension-status": "resolved",
                "data-anchor-refs": " ".join(
                    (
                        f"{opening_id}.opening.start",
                        f"{opening_id}.opening.end",
                        f"{opening_id}.opening.sill",
                        f"{opening_id}.opening.head",
                    )
                ),
                "data-anchor-targets": " ".join(
                    (
                        width_anchor_targets[0],
                        width_anchor_targets[1],
                        opening_anchor_nodes["opening.sill"][1],
                        opening_anchor_nodes["opening.head"][1],
                    )
                ),
                "data-datum": "snapshot opening width and project elevation anchors",
            },
        )
        ET.SubElement(q_text, _q("title")).text = str(quantity.get("measurement_status", ""))
    else:
        _text(
            root,
            500,
            840,
            "Nominal opening area unavailable or unanchored in evaluation ledger.",
            size=9,
            css="small",
        )
    _text(
        root,
        300,
        865,
        "Net glass, frame deductions, product performance and installed rate: unknown.",
        size=8,
        css="small",
    )
    _text(
        root,
        300,
        881,
        "Sill/worktop level agreement does not establish support, drainage or sealing.",
        size=8,
        css="small",
    )

    visible_ids = {opening_id} if opening else set()
    if host_id:
        visible_ids.add(host_id)
    _draw_finding_panel(root, view_id, evaluation, visible_ids, include_unlinked=False)
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
<nav aria-label="Generated view navigation">{"".join(f'<a href="#section-{html.escape(name[:-4], quote=True)}">{html.escape(name[:-4].replace("-", " ").title())}</a>' for name in views)}</nav>
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
    <section class="panel">
      <h2>Machine-readable review evidence</h2>
      <ul>
        <li><a href="disciplines.json">Discipline inputs and status</a></li>
        <li><a href="view_inventory.json">View, occurrence and annotation inventory</a></li>
        <li><a href="anchor_lifecycle.json">Anchor lifecycle</a></li>
        <li><a href="dependencies.json">Source dependency map</a></li>
      </ul>
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
    document.querySelectorAll('[data-entity-id], [data-anchor-entity-id], [data-dimension-for]').forEach((node) => {{
      const targetId = node.dataset.entityId || node.dataset.anchorEntityId || node.dataset.dimensionFor;
      node.classList.toggle('is-selected', targetId === entityId);
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
        "window-sections.svg": _render_window_sections(snapshot, evaluation),
    }
    views["index.html"] = _render_html(snapshot, evaluation, views)
    return views

"""Render the active drawing catalog from a resolved coordination snapshot.

Historical leaf renderers remain available to their original generators. This
adapter injects the captured native models and resolved entity geometry without
loading project files or consulting published SVGs.
"""

from __future__ import annotations

import copy
import html
import math
import re
import textwrap
from collections.abc import Callable
from typing import Any
from xml.etree import ElementTree as ET

from dreamhouse import (
    generate_p2_b09,
    generate_p2_b28,
    generate_pb_b05,
    generate_pb_b24,
    generate_pb_b27,
    generate_pb_b36,
    generate_pb_b37,
    generate_rooflight_b11,
    generate_structure_plan,
)
from dreamhouse.coordination.context_annotations import annotate_context_view
from dreamhouse.coordination.drawing_annotations import annotate_native_view
from dreamhouse.coordination.model import CoordinationError
from dreamhouse.coordination.native_notes import bind_native_notes
from dreamhouse.coordination.p2_context_annotations import (
    annotate_p2_context_view,
)
from dreamhouse.coordination.presentation_refinements import refine_native_svg
from dreamhouse.coordination.sheet_layout import append_view_references, recompose_screening
from dreamhouse.coordination.wall_context_annotations import (
    annotate_wall_context,
    render_wall_context,
)
from dreamhouse.envelope.openings import build_opening_schedule
from dreamhouse.structure.e1_screening import run_screening

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
EMBEDDED_FONT_FAMILY = "IBM Plex Sans"


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CoordinationError(f"Drawing input {label} must be numeric")
    number = float(value)
    if not math.isfinite(number):
        raise CoordinationError(f"Drawing input {label} must be finite")
    return number


def _index_by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in items}


def _entity(snapshot: dict[str, Any], identifier: str) -> dict[str, Any] | None:
    return snapshot.get("entities", {}).get(identifier)


def _assign_opening(
    target: dict[str, Any], entity: dict[str, Any], *, start: str, end: str | None = None
) -> None:
    parameters = entity.get("parameters", {})
    geometry = entity.get("geometry", {})
    facade = parameters.get("facade")
    if facade is not None:
        target["side"] = facade
    if "start_m" in parameters:
        target[start] = _number(parameters["start_m"], f"{entity['id']}.start_m")
    elif geometry.get("x0") is not None and start in {"x0", "from"}:
        target[start] = _number(geometry["x0"], f"{entity['id']}.x0")
    elif geometry.get("y0") is not None and start in {"from", "y"}:
        target[start] = _number(geometry["y0"], f"{entity['id']}.y0")
    if end is not None:
        width = parameters.get("width_m")
        if width is not None:
            target[end] = target[start] + _number(width, f"{entity['id']}.width_m")
        elif geometry.get("x1") is not None and end in {"x1", "to"}:
            target[end] = _number(geometry["x1"], f"{entity['id']}.x1")
        elif geometry.get("y1") is not None and end in {"to", "y1"}:
            target[end] = _number(geometry["y1"], f"{entity['id']}.y1")
    for target_key, source_key in (("sill", "sill_m"), ("height", "height_m"), ("modules", "modules")):
        if source_key in parameters and parameters[source_key] is not None:
            target[target_key] = parameters[source_key]
    if "head_m" in parameters:
        target["head"] = _number(parameters["head_m"], f"{entity['id']}.head_m")
    elif target.get("sill") is not None and target.get("height") is not None:
        target["head"] = float(target["sill"]) + float(target["height"])


def _synchronise_native_models(snapshot: dict[str, Any]) -> tuple[dict, dict, dict, dict]:
    try:
        disciplines = snapshot["discipline_inputs"]
        pb = copy.deepcopy(disciplines["equipment"]["pb"])
        p2 = copy.deepcopy(disciplines["programme"]["p2"])
        structure = disciplines["structure"]
        rooflights = copy.deepcopy(structure["rooflights"])
        stair = copy.deepcopy(structure["stair"])
        geometry = snapshot["geometry"]
    except (KeyError, TypeError) as error:
        raise CoordinationError(f"Drawing source context is incomplete: {error}") from error

    hall = geometry["hall"]
    p2_geometry = geometry["p2"]
    pb["envelope"]["length"] = _number(hall["length_m"], "hall.length_m")
    pb["envelope"]["width"] = _number(hall["width_m"], "hall.width_m")
    p2["envelope"].update(
        {
            "x": _number(p2_geometry["x_m"], "p2.x_m"),
            "length": _number(p2_geometry["length_m"], "p2.length_m"),
            "width": _number(p2_geometry["width_m"], "p2.width_m"),
        }
    )
    pb["stair_core"] = copy.deepcopy(stair)
    pb["_connected_snapshot"] = True
    p2["stair_core"] = copy.deepcopy(stair)
    p2["window_daylight_coordination"]["upper_floor_level_m"] = _number(
        p2_geometry["level_m"], "p2.level_m"
    )
    p2["_review_only_snapshot"] = True

    # PB vertical openings. Canonical geometry wins over inherited alias copies.
    for collection in ("technical_glazing", "workstation_glazing", "optional_opening_studies"):
        for item in pb.get(collection, []):
            source_id = item["id"]
            entity = _entity(snapshot, source_id)
            if entity is None:
                continue
            _assign_opening(item, entity, start="x0", end="x1")
    # P2 windows also own the five PB elevation aliases.
    p2_windows = _index_by_id(p2["windows"])
    for item in p2["windows"]:
        entity = _entity(snapshot, item["id"])
        if entity is None:
            continue
        parameters = entity.get("parameters", {})
        _assign_opening(item, entity, start="from", end="to")
        item["edge"] = {"A": "south", "B": "north", "REAR": "east"}.get(
            parameters.get("facade"), item["edge"]
        )
        item["from"] = _number(parameters.get("start_m", item["from"]), f"{item['id']}.from")
        item["to"] = item["from"] + _number(
            parameters.get("width_m", item["to"] - item["from"]), f"{item['id']}.width_m"
        )
    p2_window_source = p2.get("window_daylight_coordination", {}).get(
        "upper_floor_bedroom_windows", []
    )
    for item in p2_window_source:
        native = p2_windows.get(item["id"])
        if native:
            for key in ("from", "to", "sill", "height", "modules", "edge", "room_id"):
                if key in native:
                    item[key] = native[key]
    pb_bedroom_aliases = {item["p2_id"]: item for item in pb.get("bedroom_glazing", [])}
    for window_id, alias in pb_bedroom_aliases.items():
        source = p2_windows.get(window_id)
        if not source:
            continue
        alias.update(
            {
                "from": source["from"],
                "to": source["to"],
                "sill": source["sill"],
                "height": source["height"],
                "modules": source.get("modules"),
                "facade": {"south": "A", "north": "B", "east": "REAR"}[source["edge"]],
                "level": _number(p2_geometry["level_m"], "p2.level_m"),
            }
        )

    for opening in pb.get("front_openings", []):
        entity = _entity(snapshot, opening["id"])
        if entity is None:
            continue
        parameters = entity.get("parameters", {})
        for target, source in (("y0", "start_m"), ("width", "width_m"), ("height", "height_m"), ("sill", "sill_m")):
            if parameters.get(source) is not None:
                opening[target] = _number(parameters[source], f"{opening['id']}.{source}")

    # Opening schedule source is copied too; keep its adopted and excluded windows current.
    pb_windows = pb.get("window_daylight_coordination", {}).get(
        "upper_floor_bedroom_windows", []
    )
    for item in pb_windows:
        native = p2_windows.get(item["id"])
        if native:
            for key in ("from", "to", "sill", "height", "modules", "edge", "room_id"):
                if key in native:
                    item[key] = native[key]

    # P2 room footprints are current snapshot geometry, not copied loader values.
    for space in p2["spaces"]:
        entity = _entity(snapshot, space["id"])
        if entity is None:
            continue
        shape = entity.get("geometry", {})
        for key, left, right in (("x", "x0", "x1"), ("y", "y0", "y1")):
            if shape.get(left) is not None and shape.get(right) is not None:
                start = _number(shape[left], f"{space['id']}.{left}")
                end = _number(shape[right], f"{space['id']}.{right}")
                space[key] = start
                dimension_key = "w" if key == "x" else "d"
                derived = end - start
                # Preserve native decimals when geometry agrees within floating
                # point noise; genuinely edited spans still replace the source.
                if not math.isclose(
                    derived,
                    float(space[dimension_key]),
                    rel_tol=0.0,
                    abs_tol=1e-9,
                ):
                    space[dimension_key] = derived
        parameters = entity.get("parameters", {})
        if "suite" in parameters:
            space["suite"] = parameters["suite"]
        if "space_kind" in parameters:
            space["kind"] = parameters["space_kind"]

    # Current P2 door parameters have one axis/fixed/start convention.
    for door in p2["doors"]:
        entity = _entity(snapshot, door["id"])
        if entity is None:
            continue
        parameters = entity.get("parameters", {})
        axis = parameters.get("axis")
        if axis in {"X", "Y"}:
            door["wall"] = "horizontal" if axis == "X" else "vertical"
            fixed = _number(parameters.get("fixed_m"), f"{door['id']}.fixed_m")
            door["at"] = _number(parameters.get("start_m"), f"{door['id']}.start_m")
            door["width"] = _number(parameters.get("width_m"), f"{door['id']}.width_m")
            door["x" if axis == "Y" else "y"] = fixed
            door.pop("y" if axis == "Y" else "x", None)
        if parameters.get("swing") is not None:
            door["swing"] = parameters["swing"]
        if parameters.get("door_kind") is not None:
            door["kind"] = parameters["door_kind"]

    # The PB source has unresolved door anchors under CF-013. Do not use its old
    # b36 coordinates in architecture or structural consumers.
    for room in pb.get("core", []):
        entity = _entity(snapshot, f"PB-DOOR-{room['id']}")
        if entity is not None and entity.get("geometry", {}).get("shape") == "unresolved":
            room["door_y"] = None
    for door in pb.get("exterior_doors", []):
        entity = _entity(snapshot, door["id"])
        if entity is not None and entity.get("geometry", {}).get("shape") == "unresolved":
            door["y"] = None
    egress = p2.get("egress_reserve")
    if egress and egress.get("pb_opening_screen"):
        screen = egress["pb_opening_screen"]
        screen["status"] = "OPEN: CF-013 PB opening locations unresolved; CF-011 level unresolved"
        for key in ("nearest_opening_id", "nearest_opening_to_y", "clear_zone_from_y"):
            screen[key] = None

    # Rooflights are driven by the resolver's canonical entities.
    for item in rooflights.get("rooflights", []):
        entity = _entity(snapshot, item["id"])
        if entity is None:
            continue
        parameters = entity.get("parameters", {})
        for field, parameter in (("x", "x_m"), ("y", "y_m"), ("length", "length_m"), ("width", "width_m")):
            if parameter in parameters:
                item[field] = _number(parameters[parameter], f"{item['id']}.{parameter}")
        item["area"] = float(item["length"]) * float(item["width"])

    return pb, p2, rooflights, {"system": copy.deepcopy(structure["system"]), "roof_space": copy.deepcopy(structure["roof_space"]), "e1_space": copy.deepcopy(structure["e1_space"]), "stair": stair}


def _roof_longitudinal(pb: dict, p2: dict, stair: dict) -> str:
    length = float(pb["envelope"]["length"])
    p2_start = float(p2["envelope"]["x"])
    p2_end = p2_start + float(p2["envelope"]["length"])
    p2_level = float(stair["levels"]["p2_finished_floor"])
    section_y = float(pb["envelope"]["width"]) / 2
    roof = pb["roof"]
    mean_roof_level = (float(roof["low_eave"]) + float(roof["high_eave"])) / 2
    x0, base, scale = 110.0, 360.0, 22.0
    roof_y = base - mean_roof_level * scale
    floor_y = base - p2_level * scale
    return f'''<svg xmlns="{SVG_NS}" width="1120" height="520" viewBox="0 0 1120 520">
<rect width="1120" height="520" fill="#fbfaf7"/><g font-family="Arial" fill="#20292e">
<text x="75" y="48" font-size="25" font-weight="700">LONGITUDINAL SECTION · Y={section_y:.2f} m REFERENCE</text>
<text x="75" y="75" font-size="13" fill="#566269">Source-derived plan datums and roof ordinate; structural build-ups and clear heights are unresolved.</text>
<line data-context-feature="ground-datum" x1="{x0}" y1="{base}" x2="{x0 + length * scale}" y2="{base}" stroke="#172126" stroke-width="3"/>
<line data-context-feature="roof-ordinate" x1="{x0}" y1="{roof_y}" x2="{x0 + length * scale}" y2="{roof_y}" stroke="#172126" stroke-width="4"/>
<line x1="{x0}" y1="{base}" x2="{x0}" y2="{roof_y}" stroke="#778387" stroke-width="1.5" stroke-dasharray="5 5"/>
<line x1="{x0 + length * scale}" y1="{base}" x2="{x0 + length * scale}" y2="{roof_y}" stroke="#778387" stroke-width="1.5" stroke-dasharray="5 5"/>
<line data-context-feature="p2-datum" x1="{x0 + p2_start * scale}" y1="{floor_y}" x2="{x0 + p2_end * scale}" y2="{floor_y}" stroke="#8f6f5a" stroke-width="3"/>
<line x1="{x0 + p2_start * scale}" y1="{floor_y}" x2="{x0 + p2_start * scale}" y2="{base}" stroke="#798589" stroke-width="1.2" stroke-dasharray="5 4"/>
<text x="{x0 + p2_start * scale + (p2_end - p2_start) * scale / 2}" y="{floor_y - 12}" text-anchor="middle" font-size="13">P2 PLAN EXTENT · {p2_start:.2f}–{p2_end:.2f} m · DATUM +{p2_level:.2f} m</text>
<text x="{x0 + length * scale / 2}" y="{roof_y - 12}" text-anchor="middle" font-size="12">ROOF ORDINATE AT Y={section_y:.2f} m · +{mean_roof_level:.2f} m INTERPOLATED FROM EAVES</text>
<text x="{x0 + p2_start * scale / 2}" y="{base - 28}" text-anchor="middle" font-size="11">DOUBLE-HEIGHT PLAN ZONE</text>
<text x="{x0 + (p2_start + length) * scale / 2}" y="{base - 28}" text-anchor="middle" font-size="11">GROUND-FLOOR PLAN ZONE</text>
<rect x="75" y="430" width="970" height="62" fill="#fff3dc" stroke="#b95336"/><text x="95" y="458" font-size="15" font-weight="700" fill="#8e3825">COORDINATION SECTION · NOT FOR CONSTRUCTION</text><text x="95" y="481" font-size="10">No floor thickness, roof assembly, wall solid, stair clearance or finished room height is asserted.</text>
</g></svg>'''


def _roof_transverse(pb: dict, p2: dict, stair: dict) -> str:
    width = float(pb["envelope"]["width"])
    p2_level = float(stair["levels"]["p2_finished_floor"])
    roof = pb["roof"]
    low_side = roof["low_side"]
    low, high = float(roof["low_eave"]), float(roof["high_eave"])
    y_a, y_b = (low, high) if low_side == "A" else (high, low)
    rise = high - low
    slope = rise / width * 100.0
    x0, base, scale = 170.0, 575.0, 42.0
    low_y, high_y = base - y_a * scale, base - y_b * scale
    p2_y = base - p2_level * scale
    return f'''<svg xmlns="{SVG_NS}" width="1120" height="720" viewBox="0 0 1120 720">
<rect width="1120" height="720" fill="#fbfaf7"/><g font-family="Arial" fill="#20292e">
<text x="75" y="48" font-size="25" font-weight="700">TRANSVERSE ROOF PROFILE · SOURCE DATUMS</text>
<text x="75" y="75" font-size="13" fill="#566269">One reference profile across the {width:.2f} m hall; eave heights remain schematic coordination values.</text>
<line data-context-feature="ground-datum" x1="{x0}" y1="{base}" x2="{x0 + width * scale}" y2="{base}" stroke="#172126" stroke-width="3"/>
<line data-context-feature="roof-ordinate" x1="{x0}" y1="{low_y}" x2="{x0 + width * scale}" y2="{high_y}" stroke="#172126" stroke-width="4"/>
<line x1="{x0}" y1="{base}" x2="{x0}" y2="{low_y}" stroke="#778387" stroke-width="1.5" stroke-dasharray="5 5"/>
<line x1="{x0 + width * scale}" y1="{base}" x2="{x0 + width * scale}" y2="{high_y}" stroke="#778387" stroke-width="1.5" stroke-dasharray="5 5"/>
<line data-context-feature="p2-datum" x1="{x0}" y1="{p2_y}" x2="{x0 + width * scale}" y2="{p2_y}" stroke="#8f6f5a" stroke-width="3"/>
<text x="{x0 + 10}" y="{low_y - 12}" font-size="11">SIDE A {"LOW" if low_side == "A" else "HIGH"} EAVE · +{y_a:.2f} m</text>
<text x="{x0 + width * scale - 10}" y="{high_y - 12}" text-anchor="end" font-size="11">SIDE B {"HIGH" if low_side == "A" else "LOW"} EAVE · +{y_b:.2f} m</text>
<text x="{x0 + width * scale / 2}" y="{p2_y - 12}" text-anchor="middle" font-size="11">P2 FINISHED-FLOOR DATUM +{p2_level:.2f} m · NO SLAB THICKNESS IMPLIED</text>
<text x="{x0 + width * scale / 2}" y="{base + 39}" text-anchor="middle" font-size="12">{width:.2f} m · ROOF RISE {rise:.2f} m · SLOPE {slope:.2f}%</text>
<rect x="75" y="650" width="970" height="48" fill="#fff3dc" stroke="#b95336"/><text x="95" y="680" font-size="15" font-weight="700" fill="#8e3825">ROOF ASSEMBLY, SUPPORTS, DRAINAGE AND ROOM CLEAR HEIGHTS REMAIN OPEN</text>
</g></svg>'''


def _decorate_svg(
    svg: str,
    row: dict,
    evidence: dict,
    render_status: str,
    scenario_id: str,
    conflict_ids: list[str],
) -> str:
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as error:
        raise CoordinationError(f"Invalid generated SVG for {row['id']}: {error}") from error
    root.set("data-view-id", row["id"])
    root.set("data-catalog-id", row["id"])
    root.set("data-source-revision", str(evidence["source_revision"]))
    root.set("data-source-sha256", str(evidence["source_sha256"]))
    root.set("data-source-manifest-sha256", str(evidence["manifest_sha256"]))
    root.set("data-render-status", render_status)
    root.set("font-family", EMBEDDED_FONT_FAMILY)
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag in {"text", "tspan"} or "font-family" in element.attrib:
            element.set("font-family", EMBEDDED_FONT_FAMILY)
        style_attr = element.get("style")
        if style_attr and "font-family" in style_attr.lower():
            element.set(
                "style",
                re.sub(
                    r"font-family\s*:[^;]+",
                    f"font-family:{EMBEDDED_FONT_FAMILY}",
                    style_attr,
                    flags=re.IGNORECASE,
                ),
            )
        if tag == "style" and element.text and "font-family" in element.text.lower():
            element.text = re.sub(
                r"font-family\s*:[^;}{]+",
                f"font-family:{EMBEDDED_FONT_FAMILY}",
                element.text,
                flags=re.IGNORECASE,
            )
    title_tag = f"{{{SVG_NS}}}title"
    desc_tag = f"{{{SVG_NS}}}desc"
    title = root.find(title_tag)
    if title is None:
        title = ET.Element(title_tag)
        root.insert(0, title)
    title.text = row["title"]
    desc = root.find(desc_tag)
    if desc is None:
        desc = ET.Element(desc_tag)
        root.insert(1, desc)
    desc.text = (
        f"{row['alt']} Source issue {evidence['source_revision']}; current rendering status: "
        f"{render_status}. This schematic is not construction authority."
    )
    view_box = root.get("viewBox")
    if view_box:
        bounds = [float(value) for value in view_box.replace(",", " ").split()]
        if len(bounds) == 4:
            x, y, width, height = bounds
            banner_height = 62.0
            root.set("viewBox", f"{x:g} {y:g} {width:g} {height + banner_height:g}")
            raw_height = root.get("height", "")
            try:
                numeric_height = float(raw_height.removesuffix("px"))
            except ValueError:
                numeric_height = height
            root.set("height", f"{numeric_height + banner_height:g}")
            banner = ET.Element(f"{{{SVG_NS}}}g", {"id": "review-status-banner"})
            ET.SubElement(
                banner,
                f"{{{SVG_NS}}}rect",
                {
                    "x": f"{x:g}", "y": f"{y + height:g}", "width": f"{width:g}",
                    "height": f"{banner_height:g}", "fill": "#7c2f27",
                },
            )
            label = ET.SubElement(
                banner,
                f"{{{SVG_NS}}}text",
                {
                    "x": f"{x + 24:g}", "y": f"{y + height + 20:g}",
                    "font-family": EMBEDDED_FONT_FAMILY, "font-size": "13",
                    "font-weight": "700", "fill": "#ffffff",
                },
            )
            label.text = (
                f"REVIEW ONLY · NOT DESIGN ADOPTION · {scenario_id} · SOURCE {evidence['source_revision']}"
            )
            warning = ET.SubElement(
                banner,
                f"{{{SVG_NS}}}text",
                {
                    "x": f"{x + 24:g}", "y": f"{y + height + 38:g}",
                    "font-family": EMBEDDED_FONT_FAMILY, "font-size": "8.5",
                    "fill": "#fff4df",
                },
            )
            explanations = {
                "CF-013": "PB rear-door anchors unresolved; historic positions withheld",
                "CF-011": "rear stair-discharge level unresolved",
                "CF-009": "P2 bearing-line wall mass is absent from the structure load path",
                "CF-014": "P2 W05 layer sum 229 mm vs 230 mm nominal; inherited 297/300 mm note remains unresolved",
            }
            gate_text = "; ".join(
                explanations.get(item, item) for item in conflict_ids
            ) or "professional design and site validation"
            lines = textwrap.wrap(
                "OPEN GATES: " + gate_text,
                width=max(72, int(width / 5.0)),
            )
            warning.text = lines[0]
            if len(lines) > 1:
                warning_more = ET.SubElement(
                    banner,
                    f"{{{SVG_NS}}}text",
                    {
                        "x": f"{x + 24:g}", "y": f"{y + height + 54:g}",
                        "font-family": EMBEDDED_FONT_FAMILY, "font-size": "8.5",
                        "fill": "#fff4df",
                    },
                )
                warning_more.text = lines[1]
            root.append(banner)
    if row["id"].startswith((
        "structure-", "architecture-ground-floor", "architecture-front-elevation",
        "architecture-rear-elevation", "architecture-side-a-elevation",
        "architecture-side-b-elevation", "architecture-great-wall-elevation",
    )):
        from dreamhouse.coordination.drawing_language import translate_current_drawing_text

        root = ET.fromstring(translate_current_drawing_text(ET.tostring(root, encoding="unicode")))
    return ET.tostring(root, encoding="unicode")


def _drawings_index(rows: list[dict], inventory: dict) -> str:
    sections = []
    for group in ("Architecture", "Structure"):
        items = [row for row in rows if row["group"] == group]
        if not items:
            continue
        cards = []
        for row in items:
            cards.append(
                "<li>"
                f"<a href=\"{html.escape(row['id'], quote=True)}.svg\"><img class=\"thumb\" loading=\"lazy\" src=\"{html.escape(row['id'], quote=True)}.svg\" alt=\"Preview: {html.escape(row['title'], quote=True)}\"></a>"
                f"<h3><a href=\"{html.escape(row['id'], quote=True)}.svg\">{html.escape(row['title'])}</a></h3>"
                f"<p>{html.escape(row['summary'])}</p>"
                f"<p><strong>Source:</strong> {html.escape(row['source_revision'])} · "
                f"<strong>Rendering:</strong> {html.escape(row['render_status'])}</p>"
                f"<p><code>{html.escape(row['source_sha256'])}</code></p></li>"
            )
        sections.append(f"<section><h2>{html.escape(group)}</h2><ul class=\"cards\">{''.join(cards)}</ul></section>")
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>Connected drawing catalog</title><style>"
        "body{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#172a33}"
        "a{color:#155d70}.cards{list-style:none;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:1rem}"
        ".cards li{margin:0;padding:1rem;background:#f6f3ec;border-left:4px solid #168aa3}"
        ".thumb{display:block;width:100%;height:auto;max-height:260px;object-fit:contain;background:#fff;border:1px solid #ccd4d5}"
        "code{overflow-wrap:anywhere;font-size:.75em}section{margin:2rem 0}"
        "</style></head><body><main><h1>Connected drawing catalog</h1>"
        "<p>Read-only candidate consumers rendered from one resolved source snapshot. "
        "Historical published aliases are unchanged; these outputs do not grant construction authority.</p>"
        "<nav aria-label=\"Review artifacts\"><a href=\"../index.html\">Review index</a> · "
        "<a href=\"../drawing_inventory.json\">Drawing inventory</a> · "
        "<a href=\"../view_inventory.json\">View inventory</a> · "
        "<a href=\"../anchor_lifecycle.json\">Anchor lifecycle</a> · "
        "<a href=\"../dependencies.json\">Dependencies</a> · "
        "<a href=\"../disciplines.json\">Discipline findings</a></nav>"
        f"<p>{inventory['drawing_count']} catalog drawings rendered; all unresolved inputs remain explicit.</p>"
        f"{''.join(sections)}</main></body></html>"
    )


def render_drawings(snapshot: dict, evaluation: dict) -> dict[str, Any]:
    """Render the 27 catalog consumers without reading files or changing sources."""

    catalog = snapshot.get("drawing_catalog", {})
    rows = catalog.get("drawings", [])
    evidence_by_id = snapshot.get("drawing_source_evidence", {})
    if len(rows) != 27 or set(evidence_by_id) != {row.get("id") for row in rows}:
        raise CoordinationError("Connected drawing catalog requires 27 source-evidence records")

    pb, p2, rooflights, structure = _synchronise_native_models(snapshot)
    p2_report = generate_p2_b09._report(p2)
    roof_report = generate_rooflight_b11.validate(rooflights, pb, parameterize=True)
    schedule = build_opening_schedule(pb, p2, rooflights)
    structural_screening = run_screening(
        structure["system"],
        structure["roof_space"],
        structure["e1_space"],
        pb,
        p2,
        rooflights,
        enforce_expected_compatible_ids=False,
    )
    structure_outputs = generate_structure_plan.build_sheets_from_sources(
        structure["system"],
        pb,
        p2,
        rooflights,
        structure["roof_space"],
        structure["e1_space"],
        enforce_expected_compatible_ids=False,
        allow_open_continuity_geometry=True,
        screening_result=structural_screening,
    )
    pb_eng = generate_pb_b24.translate_visible_text

    renderers: dict[str, Callable[[], str]] = {
        "architecture-ground-floor": lambda: pb_eng(generate_pb_b05.plan_sheet(pb, parameterize=True)),
        "architecture-upper-floor": lambda: generate_p2_b09.build_plan(p2, p2_report),
        "architecture-roof-plan": lambda: generate_rooflight_b11.plan(rooflights, {
            "passed": sum(item["status"] == "PASS" for item in roof_report),
            "failed": sum(item["status"] == "FAIL" for item in roof_report),
            "open": sum(item["status"] == "OPEN" for item in roof_report),
        }, parameterize=True),
        "architecture-roof-daylight-section": lambda: generate_rooflight_b11.section(rooflights, parameterize=True),
        "architecture-roof-longitudinal-section": lambda: _roof_longitudinal(
            pb, p2, structure["stair"]
        ),
        "architecture-roof-transverse-section": lambda: _roof_transverse(
            pb, p2, structure["stair"]
        ),
        "architecture-front-elevation": lambda: pb_eng(generate_pb_b05.front_elevation_sheet(pb, parameterize=True)),
        "architecture-rear-elevation": lambda: generate_pb_b37.rear_elevation_sheet(pb, p2, parameterize=True),
        "architecture-side-a-elevation": lambda: pb_eng(generate_pb_b05.side_elevation_sheet(pb, "A", parameterize=True)),
        "architecture-side-b-elevation": lambda: pb_eng(generate_pb_b05.side_elevation_sheet(pb, "B", parameterize=True)),
        "architecture-great-wall-elevation": lambda: pb_eng(generate_pb_b05.wall_elevation_sheet(pb)),
        "architecture-ground-floor-core": lambda: pb_eng(generate_pb_b05.core_sheet(pb)),
        "architecture-pb-media-wall": lambda: pb_eng(generate_pb_b27.perimeter_media_sheet(pb)),
        "architecture-pb-integrated-workstations": lambda: generate_pb_b37.workstation_detail(
            pb, parameterize=True
        ),
        "architecture-pb-technical-workbenches": lambda: pb_eng(
            generate_pb_b36.technical_workbench_detail_sheet(pb, parameterize=True)
        ),
        "architecture-p2-bedroom-windows": lambda: generate_p2_b28.bedroom_window_detail_sheet(
            p2,
            snapshot["build_dependencies"]["dreamhouse/window_daylight_d083.json"],
            parameterize=True,
        ),
        "architecture-window-schedule": lambda: generate_pb_b37.opening_schedule_sheet(
            pb, p2, schedule, parameterize=True
        ),
        "architecture-access-egress": lambda: generate_p2_b09.build_access_diagram(
            p2, p2_report
        ),
        "architecture-owner-priorities": lambda: generate_p2_b09.build_owner_priorities_detail(p2),
        "architecture-p2-acoustic-partition": lambda: generate_p2_b09.build_acoustic_partition_detail(p2),
        "architecture-p2-hall-edge": lambda: generate_p2_b09.build_hall_edge_detail(p2),
        "architecture-p2-exterior-wall": lambda: generate_p2_b09.build_integrated_exterior_wall_detail(p2),
    }
    for row in rows:
        if row["id"].startswith("structure-"):
            # Sheet names are keyed by the native structure generator; the explicit
            # lookup below is based on catalog identity, never published SVG content.
            sheet_key = {
                "structure-coordination-plan": "DH-EST-E0-002_ESTRUCTURA-INSPECCION.svg",
                "structure-lateral-a": "DH-EST-E0-003_ESTRUCTURA-LATERAL-A.svg",
                "structure-great-wall": "DH-EST-E0-004_PARED-HIBRIDA.svg",
                "structure-e1-synthesis": "DH-EST-E1-001_SINTESIS-ESTRUCTURAL.svg",
                "structure-vertical-continuity": "DH-EST-E1-002_CONTINUIDAD-VERTICAL-ESCALERA.svg",
            }[row["id"]]
            renderers[row["id"]] = lambda key=sheet_key: structure_outputs[key]

    files: dict[str, str] = {}
    inventory_rows = []
    for row in rows:
        identifier = row["id"]
        if identifier not in renderers:
            raise CoordinationError(f"No connected renderer is registered for {identifier}")
        svg = render_wall_context(snapshot, identifier) or renderers[identifier]()
        svg = refine_native_svg(snapshot, identifier, svg)
        svg = recompose_screening(svg, identifier)
        svg = append_view_references(svg, identifier)
        evidence = evidence_by_id[identifier]
        structural = identifier.startswith("structure-")
        render_status = (
            "current-source bounded screening; not engineering approval"
            if structural
            else "current native source geometry rendered from resolved snapshot; schematic, not for construction"
        )
        conflict_ids = []
        if identifier in {
            "architecture-ground-floor", "architecture-ground-floor-core",
            "architecture-great-wall-elevation", "architecture-rear-elevation", "architecture-access-egress",
            "structure-coordination-plan", "structure-lateral-a", "structure-great-wall",
            "structure-e1-synthesis", "structure-vertical-continuity",
        }:
            conflict_ids.extend(("CF-013", "CF-011"))
        if identifier in {"architecture-upper-floor", "architecture-p2-exterior-wall",
                          "architecture-p2-acoustic-partition", "architecture-p2-hall-edge"}:
            conflict_ids.append("CF-014")
        if p2_report["failed"] and identifier.startswith(("architecture-upper-floor", "architecture-access-egress", "architecture-owner-priorities", "architecture-p2-")):
            conflict_ids.append(f"P2 CHECKS FAIL: {p2_report['failed']}")
        if structural:
            conflict_ids.append("CF-009")
        svg = _decorate_svg(
            svg, row, evidence, render_status, snapshot["scenario_id"], conflict_ids
        )
        svg_root = ET.fromstring(svg)
        bind_native_notes(snapshot, svg_root)
        annotation_coverage = (
            annotate_context_view(snapshot, svg_root)
            or annotate_wall_context(snapshot, svg_root)
            or annotate_p2_context_view(snapshot, svg_root)
            or annotate_native_view(snapshot, svg_root)
        )
        svg = ET.tostring(svg_root, encoding="unicode")
        files[f"drawings/{identifier}.svg"] = svg
        inventory_rows.append(
            {
                "id": identifier,
                "file": f"drawings/{identifier}.svg",
                "title": row["title"],
                "summary": row["summary"],
                "group": row["group"],
                "source": evidence["source"],
                "source_revision": evidence["source_revision"],
                "source_status": evidence["source_status"],
                "source_sha256": evidence["source_sha256"],
                "source_manifest": evidence["source_manifest"],
                "manifest_sha256": evidence["manifest_sha256"],
                "generator": evidence["generator"],
                "render_status": render_status,
                "annotation_coverage": annotation_coverage,
            }
        )

    supported_annotations = [
        row for row in inventory_rows if row["annotation_coverage"]["status"] == "supported"
    ]
    unsupported_annotations = [
        row for row in inventory_rows if row["annotation_coverage"]["status"] == "unsupported"
    ]
    not_applicable_annotations = [
        row for row in inventory_rows if row["annotation_coverage"]["status"] == "not_applicable"
    ]

    inventory = {
        "schema_version": 1,
        "scenario_id": snapshot["scenario_id"],
        "input_hash": snapshot["input_hash"],
        "catalog_version": catalog.get("version"),
        "drawing_count": len(inventory_rows),
        "rendered_catalog_ids": [row["id"] for row in inventory_rows],
        "drawings": inventory_rows,
        "coverage_claim": "All 27 current catalog consumers are regenerated from resolved snapshot sources. Source-bound feature and dimension coverage, unresolved geometry and non-metric sheets are identified individually below.",
        "annotation_migration": {
            "status": "partial" if unsupported_annotations else "source_backed_scope_complete",
            "supported_sheet_count": len(supported_annotations),
            "supported_sheets": [row["id"] for row in supported_annotations],
            "named_dimension_count": sum(
                row["annotation_coverage"]["dimensions"] for row in supported_annotations
            ),
            "source_checked_context_dimension_count": sum(
                row["annotation_coverage"].get("context_dimensions", 0) for row in supported_annotations
            ),
            "unsupported_sheet_count": len(unsupported_annotations),
            "unsupported_sheets": [
                {"id": row["id"], "reason": row["annotation_coverage"]["reason"]}
                for row in unsupported_annotations
            ],
            "not_applicable_sheet_count": len(not_applicable_annotations),
            "not_applicable_sheets": [
                {"id": row["id"], "reason": row["annotation_coverage"]["reason"]}
                for row in not_applicable_annotations
            ],
            "limitation": "Coverage represents only registered source-to-SVG projections and does not establish design adoption, engineering adequacy, or construction authority.",
        },
        "limitations": [
            "PB core and rear door coordinates remain omitted under CF-013; the historic b36 coordinates are not reused. CF-011 rear stair discharge level also remains open.",
            "Structural sheets are live E0/E1 coordination and bounded screening evidence only; no member, system, connection, fire strategy or foundation is approved.",
            "CF-009 P2 bearing-line wall mass and its transfer into the structure model remain an unresolved input gap.",
            "CF-014 records the current 229 mm P2 W05 layer sum against the 230 mm nominal assembly and inherited 297/300 mm detail note; the conflict is not resolved by this rendering.",
            "SVG entity-occurrence and named-dimension annotation coverage is audited separately by the view inventory; this catalog inventory does not claim complete annotation migration.",
        ],
        "construction_authority": False,
        "published_aliases_promoted": False,
    }
    files["drawings/index.html"] = _drawings_index(inventory_rows, inventory)
    return {"files": files, "inventory": inventory, "structural_screening": structural_screening}

"""Source-bound annotations for native catalog geometry with trusted projections.

This module only annotates native SVG features whose renderer has an explicit,
reviewed mapping from source coordinates to SVG coordinates. Unsupported sheets
remain visible in the migration ledger without receiving invented dimensions.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from typing import Any
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import CoordinationError

SVG_NS = "http://www.w3.org/2000/svg"

# Each projection maps a source axis into one SVG axis. `scale` and `offset`
# come from the native renderer, never from the observed occurrence rectangle.
# Bench-window X coordinates are local to the corresponding bench origin.
NATIVE_VIEW_PROJECTIONS: dict[str, dict[str, Any]] = {
    "architecture-front-elevation": {
        "projection_id": "pb-front-elevation-v1",
        "entity_ids": ["CAR", "PED", "RC"],
        "x": {
            "axis": "y", "start": "y0", "end": "y1", "scale": 62.0,
            "offset": 140.0, "dimension": "width",
        },
        "y": {
            "axis": "z", "start": "z0", "end": "z1", "scale": -62.0,
            "offset": 645.0, "dimension": "height",
        },
        "dimension_side": "top",
    },
    "architecture-side-a-elevation": {
        "projection_id": "pb-side-a-elevation-v1",
        "entity_ids": ["GLZ-CAR", "GLZ-WS-A", "W-H1", "W-M-LAT-A"],
        "x": {
            "axis": "x", "start": "x0", "end": "x1", "scale": 32.5,
            "offset": 105.0, "dimension": "width",
        },
        "y": {
            "axis": "z", "start": "z0", "end": "z1", "scale": -32.5,
            "offset": 645.0, "dimension": "height",
        },
        "dimension_side": "top",
    },
    "architecture-side-b-elevation": {
        "projection_id": "pb-side-b-elevation-v1",
        "entity_ids": ["GLZ-RC", "GLZ-WS-B", "W-H2", "W-G"],
        "x": {
            "axis": "x", "start": "x0", "end": "x1", "scale": 32.5,
            "offset": 105.0, "dimension": "width",
        },
        "y": {
            "axis": "z", "start": "z0", "end": "z1", "scale": -32.5,
            "offset": 645.0, "dimension": "height",
        },
        "dimension_side": "top",
    },
    "architecture-roof-plan": {
        "projection_id": "roof-plan-v1",
        "entity_ids": ["RL-CAR", "RL-RC"],
        "x": {
            "axis": "x", "start": "x0", "end": "x1", "scale": 36.0,
            "offset": 95.0, "dimension": "length",
        },
        "y": {
            "axis": "y", "start": "y0", "end": "y1", "scale": 36.0,
            "offset": 185.0, "dimension": "width",
        },
        "dimension_side": "top",
    },
    "architecture-pb-technical-workbenches": {
        "projection_id": "pb-workbench-window-elevations-v1",
        "entity_ids": ["GLZ-CAR", "GLZ-RC"],
        "x": {
            "axis": "x", "start": "x0", "end": "x1", "scale": 50.0,
            "offset": 75.0, "dimension": "width", "bench_context": True,
        },
        "y": {
            "axis": "z", "start": "z0", "end": "z1", "scale": -50.0,
            "offsets_by_entity": {"GLZ-CAR": 315.0, "GLZ-RC": 600.0},
            "dimension": "height",
        },
        "dimension_side": "bottom",
    },
}

_BENCH_BY_WINDOW = {"GLZ-CAR": "PB-BENCH-CAR", "GLZ-RC": "PB-BENCH-RC"}
_NON_METRIC_SHEETS = {
    "architecture-owner-priorities": "This sheet is a priority and coordination matrix, not a measured geometric projection.",
    "architecture-window-schedule": "This sheet is a tabular opening schedule; its values have no projected geometric feature to anchor.",
    "structure-coordination-plan": "This is a bounded structural screening diagram without source-linked member geometry or a dimensioned drawing transform.",
    "structure-e1-synthesis": "This is a structural evidence synthesis, not a dimensioned plan, elevation, or section projection.",
    "structure-great-wall": "This is a structural screening schematic without source-linked member geometry or a dimensioned drawing transform.",
    "structure-lateral-a": "This is a structural screening schematic without source-linked member geometry or a dimensioned drawing transform.",
    "structure-vertical-continuity": "This is a structural continuity screening schematic, not a dimensioned geometric projection.",
}
_UNSUPPORTED_SHEETS = {
    "architecture-rear-elevation": "Visible openings have no stable source entity occurrences in this native renderer; PB door anchors remain unresolved under CF-013.",
    "architecture-roof-daylight-section": "Rooflights are projected as section lines; this renderer does not declare a complete source-to-SVG transform for those line features.",
}


def _q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CoordinationError(f"Native annotation source {label} is not numeric")
    number = float(value)
    if not math.isfinite(number):
        raise CoordinationError(f"Native annotation source {label} is not finite")
    return number


def _token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-.") or "item"


def _entity_value(snapshot: Mapping[str, Any], entity_id: str, field: str) -> float:
    try:
        value = snapshot["entities"][entity_id]["geometry"][field]
    except (KeyError, TypeError) as error:
        raise CoordinationError(f"Native annotation source is missing {entity_id}.geometry.{field}") from error
    return _finite(value, f"{entity_id}.geometry.{field}")


def _bench_origin(snapshot: Mapping[str, Any], entity_id: str) -> float:
    bench_id = _BENCH_BY_WINDOW.get(entity_id)
    if bench_id is None:
        raise CoordinationError(f"No native workbench context is registered for {entity_id}")
    try:
        benches = snapshot["discipline_inputs"]["equipment"]["pb"]["built_in_benches"]
    except (KeyError, TypeError) as error:
        raise CoordinationError("Native workbench source context is incomplete") from error
    matches = [item for item in benches if item.get("id") == bench_id]
    if len(matches) != 1:
        raise CoordinationError(f"Native workbench context {bench_id} is missing or duplicated")
    return _finite(matches[0].get("x0"), f"{bench_id}.x0")


def _axis_source_value(
    snapshot: Mapping[str, Any], entity_id: str, axis: Mapping[str, Any], field: str
) -> float:
    return _entity_value(snapshot, entity_id, field)


def _project_coordinate(
    snapshot: Mapping[str, Any], entity_id: str, axis: Mapping[str, Any], field: str
) -> float:
    source = _axis_source_value(snapshot, entity_id, axis, field)
    context = _bench_origin(snapshot, entity_id) if axis.get("bench_context") else 0.0
    offset = axis.get("offset")
    if offset is None:
        offset = axis["offsets_by_entity"][entity_id]
    return float(offset) + float(axis["scale"]) * (source - context)


def _rect_occurrences(root: ET.Element) -> dict[str, ET.Element]:
    occurrences: dict[str, ET.Element] = {}
    def visit(element: ET.Element, ancestor_transformed: bool = False) -> None:
        style = element.get("style", "")
        style_transform = re.search(r"(?:^|;)\s*transform\s*:", style, flags=re.IGNORECASE)
        transformed = ancestor_transformed or bool(element.get("transform")) or bool(style_transform)
        entity_id = element.get("data-entity-id")
        if entity_id is not None:
            if transformed:
                raise CoordinationError(
                    f"Transformed native geometry is unsupported for {root.get('data-view-id')}/{entity_id}"
                )
            if element.tag.rsplit("}", 1)[-1] != "rect":
                raise CoordinationError(
                    f"Native metric feature {entity_id} in {root.get('data-view-id')} is not a rectangle"
                )
            if entity_id in occurrences:
                raise CoordinationError(
                    f"Native metric feature {entity_id} occurs more than once in {root.get('data-view-id')}"
                )
            if not element.get("id"):
                raise CoordinationError(f"Native metric feature {entity_id} has no stable occurrence ID")
            occurrences[entity_id] = element
        for child in element:
            visit(child, transformed)

    visit(root)
    return occurrences


def audit_native_geometry(snapshot: dict, root: ET.Element) -> dict:
    """Check tagged native rectangles against registered source-to-SVG transforms.

    The registered transform is independent of the observed rectangle, so changing
    the geometry element without changing its source is rejected before annotation.
    """
    view_id = root.get("data-view-id")
    projection = NATIVE_VIEW_PROJECTIONS.get(str(view_id))
    if projection is None:
        return {
            "state": "unsupported",
            "view_id": view_id,
            "reason": "No registered source-to-SVG metric projection is available for this view.",
            "feature_count": 0,
        }

    occurrences = _rect_occurrences(root)
    if not occurrences:
        raise CoordinationError(f"Registered native projection {view_id} has no tagged geometry")
    expected_ids = set(projection["entity_ids"])
    if set(occurrences) != expected_ids:
        missing = sorted(expected_ids - set(occurrences))
        unexpected = sorted(set(occurrences) - expected_ids)
        raise CoordinationError(
            f"Native metric feature set changed in {view_id}: "
            f"missing={missing}, unexpected={unexpected}"
        )
    features = []
    for entity_id, element in sorted(occurrences.items()):
        entity = snapshot.get("entities", {}).get(entity_id)
        if entity is None:
            raise CoordinationError(f"Native metric feature {entity_id} is absent from the source snapshot")
        geometry = entity.get("geometry", {})
        if geometry.get("shape") not in {"opening", "rect"}:
            raise CoordinationError(f"Native metric feature {entity_id} has unsupported source geometry")
        expected: dict[str, float] = {}
        for screen_axis in ("x", "y"):
            axis = projection[screen_axis]
            start = _axis_source_value(snapshot, entity_id, axis, axis["start"])
            end = _axis_source_value(snapshot, entity_id, axis, axis["end"])
            if end <= start:
                raise CoordinationError(f"Native metric feature {entity_id} has a nonpositive source span")
            start_px = _project_coordinate(snapshot, entity_id, axis, axis["start"])
            end_px = _project_coordinate(snapshot, entity_id, axis, axis["end"])
            expected[screen_axis] = min(start_px, end_px)
            expected["width" if screen_axis == "x" else "height"] = abs(end_px - start_px)
        actual = {}
        for attribute in ("x", "y", "width", "height"):
            raw = element.get(attribute)
            if raw is None:
                raise CoordinationError(f"Native metric feature {entity_id} is missing SVG {attribute}")
            try:
                parsed = float(raw)
            except (TypeError, ValueError, OverflowError) as error:
                raise CoordinationError(
                    f"Native metric feature {entity_id} has invalid SVG {attribute}"
                ) from error
            actual[attribute] = _finite(parsed, f"{entity_id}.svg.{attribute}")
            if not math.isclose(actual[attribute], expected[attribute], rel_tol=0, abs_tol=1e-6):
                raise CoordinationError(
                    f"Native geometry projection mismatch for {view_id}/{entity_id} {attribute}: "
                    f"rendered {actual[attribute]:.9g}, source projects to {expected[attribute]:.9g}"
                )
        features.append(
            {
                "entity_id": entity_id,
                "occurrence_id": element.get("id"),
                "source_shape": geometry["shape"],
                "expected_svg_rect": {key: _number_text(value) for key, value in expected.items()},
                "actual_svg_rect": {key: _number_text(value) for key, value in actual.items()},
            }
        )
    return {
        "state": "evaluated",
        "view_id": view_id,
        "projection_id": projection["projection_id"],
        "feature_count": len(features),
        "features": features,
        "numerical_tolerance_px": 1e-6,
        "construction_tolerance": False,
    }


def _number_text(value: float) -> str:
    return format(value, ".12g") if value else "0"


def _add_anchor(
    parent: ET.Element,
    snapshot: Mapping[str, Any],
    view_id: str,
    entity_id: str,
    name: str,
    axis: Mapping[str, Any],
    field: str,
    x: float,
    y: float,
) -> tuple[str, str]:
    semantic_id = f"{entity_id}.{name}"
    dom_id = f"{_token(view_id)}-anchor-{_token(entity_id)}-{_token(name)}"
    world_axis = str(axis["axis"])
    binding = json.dumps(
        {world_axis: ["entities", entity_id, "geometry", field]},
        sort_keys=True,
        separators=(",", ":"),
    )
    ET.SubElement(
        parent,
        _q("circle"),
        {
            "id": dom_id,
            "class": "semantic-anchor native-source-anchor",
            "cx": _number_text(x),
            "cy": _number_text(y),
            "r": "2.4",
            "fill": "#fffdf8",
            "stroke": "#126c83",
            "stroke-width": "1.1",
            "data-anchor-id": semantic_id,
            "data-anchor-name": name,
            "data-anchor-entity-id": entity_id,
            "data-anchor-status": "resolved",
            "data-anchor-source": "snapshot entity geometry",
            "data-anchor-bindings": binding,
            f"data-world-{world_axis}": _number_text(_entity_value(snapshot, entity_id, field)),
        },
    )
    return semantic_id, dom_id


def _line(parent: ET.Element, x1: float, y1: float, x2: float, y2: float, *, extension: bool = False) -> None:
    ET.SubElement(
        parent,
        _q("line"),
        {
            "x1": _number_text(x1),
            "y1": _number_text(y1),
            "x2": _number_text(x2),
            "y2": _number_text(y2),
            "stroke": "#126c83" if not extension else "#6e8d94",
            "stroke-width": "1.1" if not extension else ".7",
            "vector-effect": "non-scaling-stroke",
            "class": "native-dimension-line",
        },
    )


def _append_dimension(
    parent: ET.Element,
    snapshot: Mapping[str, Any],
    *,
    view_id: str,
    entity_id: str,
    dimension_name: str,
    axis: Mapping[str, Any],
    start_field: str,
    end_field: str,
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    dimension_line: tuple[tuple[float, float], tuple[float, float]],
    label_point: tuple[float, float],
    direction: str,
    rotate: bool = False,
) -> None:
    start_value = _axis_source_value(snapshot, entity_id, axis, start_field)
    end_value = _axis_source_value(snapshot, entity_id, axis, end_field)
    value = end_value - start_value
    if value <= 0:
        raise CoordinationError(f"Native dimension {entity_id}.{dimension_name} has a nonpositive source value")
    start_ref, start_target = _add_anchor(
        parent,
        snapshot,
        view_id,
        entity_id,
        f"{dimension_name}.start",
        axis,
        start_field,
        *start_point,
    )
    end_ref, end_target = _add_anchor(
        parent,
        snapshot,
        view_id,
        entity_id,
        f"{dimension_name}.end",
        axis,
        end_field,
        *end_point,
    )
    (line_start, line_end) = dimension_line
    _line(parent, *line_start, *line_end)
    if direction == "horizontal":
        tick = 3.5
        for x, y in (line_start, line_end):
            _line(parent, x, y - tick, x, y + tick)
        _line(parent, start_point[0], start_point[1], line_start[0], line_start[1], extension=True)
        _line(parent, end_point[0], end_point[1], line_end[0], line_end[1], extension=True)
    else:
        tick = 3.5
        for x, y in (line_start, line_end):
            _line(parent, x - tick, y, x + tick, y)
        _line(parent, start_point[0], start_point[1], line_start[0], line_start[1], extension=True)
        _line(parent, end_point[0], end_point[1], line_end[0], line_end[1], extension=True)

    semantic_dimension_id = f"{entity_id}.{dimension_name}"
    text_attrs = {
        "id": f"{_token(view_id)}-dimension-{_token(entity_id)}-{_token(dimension_name)}",
        "x": _number_text(label_point[0]),
        "y": _number_text(label_point[1]),
        "fill": "#124c5c",
        "stroke": "#fffdf8",
        "stroke-width": "2.4",
        "paint-order": "stroke",
        "font-family": "IBM Plex Sans",
        "font-size": "9",
        "font-weight": "700",
        "text-anchor": "middle",
        "class": "dimension native-source-dimension",
        "data-dimension-id": semantic_dimension_id,
        "data-anchor-refs": f"{start_ref} {end_ref}",
        "data-anchor-targets": f"{start_target} {end_target}",
        "data-dimension-status": "resolved",
        "data-dimension-datum": f"source {axis['axis']} coordinate",
        "data-dimension-direction": direction,
        "data-dimension-value": _number_text(value),
        "data-dimension-unit": "m",
        "data-dimension-source": (
            f"entities.{entity_id}.geometry.{start_field} → "
            f"entities.{entity_id}.geometry.{end_field}"
        ),
        "data-dimension-label-format": "fixed-2-m",
    }
    if rotate:
        text_attrs["transform"] = f"rotate(-90 {_number_text(label_point[0])} {_number_text(label_point[1])})"
    text = ET.SubElement(parent, _q("text"), text_attrs)
    text.text = f"{value:.2f} m"


def _add_feature_annotations(
    parent: ET.Element,
    snapshot: Mapping[str, Any],
    view_id: str,
    projection: Mapping[str, Any],
    entity_id: str,
    element: ET.Element,
) -> None:
    x = float(element.get("x", "nan"))
    y = float(element.get("y", "nan"))
    width = float(element.get("width", "nan"))
    height = float(element.get("height", "nan"))
    left, right = x, x + width
    top, bottom = y, y + height
    h_axis = projection["x"]
    h_start, h_end = h_axis["start"], h_axis["end"]
    h_start_x = _project_coordinate(snapshot, entity_id, h_axis, h_start)
    h_end_x = _project_coordinate(snapshot, entity_id, h_axis, h_end)
    if not math.isclose(h_start_x, left, rel_tol=0, abs_tol=1e-6) or not math.isclose(
        h_end_x, right, rel_tol=0, abs_tol=1e-6
    ):
        raise CoordinationError(f"Horizontal anchor projection disagrees with {view_id}/{entity_id}")
    h_dim_y = top - 11.0 if projection["dimension_side"] == "top" else bottom + 10.0
    h_label_y = h_dim_y - 4.0 if projection["dimension_side"] == "top" else h_dim_y + 13.0
    _append_dimension(
        parent,
        snapshot,
        view_id=view_id,
        entity_id=entity_id,
        dimension_name=str(h_axis["dimension"]),
        axis=h_axis,
        start_field=h_start,
        end_field=h_end,
        start_point=(left, top if projection["dimension_side"] == "top" else bottom),
        end_point=(right, top if projection["dimension_side"] == "top" else bottom),
        dimension_line=((left, h_dim_y), (right, h_dim_y)),
        label_point=((left + right) / 2, h_label_y),
        direction="horizontal",
    )

    v_axis = projection["y"]
    v_start, v_end = v_axis["start"], v_axis["end"]
    v_start_y = _project_coordinate(snapshot, entity_id, v_axis, v_start)
    v_end_y = _project_coordinate(snapshot, entity_id, v_axis, v_end)
    if not math.isclose(min(v_start_y, v_end_y), top, rel_tol=0, abs_tol=1e-6) or not math.isclose(
        max(v_start_y, v_end_y), bottom, rel_tol=0, abs_tol=1e-6
    ):
        raise CoordinationError(f"Vertical anchor projection disagrees with {view_id}/{entity_id}")
    v_low_field, v_high_field = v_start, v_end
    # For a decreasing screen transform (elevations), the low world value is
    # physically at the bottom. For roof plans, the low world value is at top.
    if float(v_axis["scale"]) < 0:
        low_point, high_point = (right, bottom), (right, top)
    else:
        low_point, high_point = (right, top), (right, bottom)
    v_dim_x = right + 11.0
    label_x = v_dim_x + 12.0
    label_y = (top + bottom) / 2
    _append_dimension(
        parent,
        snapshot,
        view_id=view_id,
        entity_id=entity_id,
        dimension_name=str(v_axis["dimension"]),
        axis=v_axis,
        start_field=v_low_field,
        end_field=v_high_field,
        start_point=low_point,
        end_point=high_point,
        dimension_line=((v_dim_x, top), (v_dim_x, bottom)),
        label_point=(label_x, label_y),
        direction="vertical",
        rotate=True,
    )


def annotate_native_view(snapshot: dict, root: ET.Element) -> dict:
    """Append source-bound dimensions where the native SVG transform is known."""
    view_id = str(root.get("data-view-id") or "")
    projection = NATIVE_VIEW_PROJECTIONS.get(view_id)
    if projection is None:
        occurrences = [e for e in root.iter() if e.get("data-entity-id")]
        if view_id in _NON_METRIC_SHEETS:
            return {
                "status": "not_applicable",
                "reason": _NON_METRIC_SHEETS[view_id],
                "geometry_binding": {"state": "not_applicable", "feature_count": 0},
                "anchors": 0,
                "dimensions": 0,
            }
        reason = _UNSUPPORTED_SHEETS.get(view_id)
        if reason is None:
            reason = (
                "This geometric sheet has no stable source entity occurrence with a registered "
                "native source-to-SVG metric transform; dimensions are withheld."
                if view_id.startswith("architecture-")
                else "This sheet has no registered source-to-SVG metric transform for an editable feature."
            )
        return {
            "status": "unsupported",
            "reason": reason,
            "geometry_binding": {
                "state": "unsupported",
                "feature_count": len(occurrences),
                "reason": reason,
            },
            "anchors": 0,
            "dimensions": 0,
        }

    audit = audit_native_geometry(snapshot, root)
    if audit["state"] != "evaluated":
        raise CoordinationError(f"Native geometry projection was not evaluated for {view_id}")
    occurrences = _rect_occurrences(root)
    group = ET.Element(
        _q("g"),
        {
            "id": f"{_token(view_id)}-source-bound-dimensions",
            "data-annotation-scope": "source-bound-native-feature-dimensions",
            "data-geometry-projection-id": projection["projection_id"],
        },
    )
    for entity_id, element in sorted(occurrences.items()):
        _add_feature_annotations(group, snapshot, view_id, projection, entity_id, element)
    # Keep the review banner on top while placing dimensions above native geometry.
    banner = next((node for node in root if node.get("id") == "review-status-banner"), None)
    root.insert(list(root).index(banner) if banner is not None else len(root), group)
    return {
        "status": "supported",
        "reason": None,
        "geometry_binding": {
            "state": "evaluated",
            "projection_id": projection["projection_id"],
            "feature_count": audit["feature_count"],
            "numerical_tolerance_px": audit["numerical_tolerance_px"],
            "construction_tolerance": False,
        },
        "anchors": 4 * len(occurrences),
        "dimensions": 2 * len(occurrences),
        "supported_scope": "width/length and height/width dimensions for tagged source rectangles only",
    }

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
        "view_purpose": "source-bound front elevation review",
        "projection_basis": "orthographic Y-Z elevation from the front-opening source coordinates",
        "projected_axes": ["y", "z"],
        "world_to_view": {"axes": ["y", "z"], "scale": [62.0, -62.0], "offset": [140.0, 645.0]},
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
        "view_purpose": "source-bound side A elevation review",
        "projection_basis": "orthographic X-Z elevation from the native side A source coordinates",
        "projected_axes": ["x", "z"],
        "world_to_view": {"axes": ["x", "z"], "scale": [32.5, -32.5], "offset": [105.0, 645.0]},
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
        "view_purpose": "source-bound side B elevation review",
        "projection_basis": "orthographic X-Z elevation from the native side B source coordinates",
        "projected_axes": ["x", "z"],
        "world_to_view": {"axes": ["x", "z"], "scale": [32.5, -32.5], "offset": [105.0, 645.0]},
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
        "view_purpose": "source-bound rooflight plan review",
        "projection_basis": "orthographic X-Y plan from the rooflight source coordinates",
        "projected_axes": ["x", "y"],
        "world_to_view": {"axes": ["x", "y"], "scale": [36.0, 36.0], "offset": [95.0, 185.0]},
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
        "view_purpose": "source-bound technical-window detail review",
        "projection_basis": "two local X-Z elevation panels; each horizontal panel origin is its source workbench datum",
        "projected_axes": ["x", "z"],
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
    "architecture-ground-floor": {
        "projection_id": "pb-ground-floor-opening-lines-v1",
        "view_purpose": "source-bound ground-floor opening plan review",
        "projection_basis": "orthographic X-Y plan; opening lines are projected from resolved PB source coordinates",
        "projected_axes": ["x", "y"],
        "world_to_view": {"axes": ["x", "y"], "scale": [27.0, -27.0], "offset": [205.0, 641.0]},
        "geometry_kind": "line",
        "entity_ids": ["CAR", "PED", "RC", "GLZ-CAR", "GLZ-WS-A", "GLZ-RC", "GLZ-WS-B"],
        "dimension_normal": -1.0,
        "features": {
            **{
                entity_id: {
                    "axis": "y",
                    "dimension": "width",
                    "start": "y0",
                    "end": "y1",
                    "screen_x": {"source_field": "x0", "scale": 27.0, "offset": 205.0},
                    "screen_y": {"variable_axis": True, "scale": -27.0, "offset": 641.0},
                }
                for entity_id in ("CAR", "PED", "RC")
            },
            **{
                entity_id: {
                    "axis": "x",
                    "dimension": "width",
                    "start": "x0",
                    "end": "x1",
                    "screen_x": {"variable_axis": True, "scale": 27.0, "offset": 205.0},
                    "screen_y": {"source_field": "y0", "scale": -27.0, "offset": 641.0},
                }
                for entity_id in ("GLZ-CAR", "GLZ-WS-A", "GLZ-RC", "GLZ-WS-B")
            },
        },
    },
    "architecture-upper-floor": {
        "projection_id": "p2-plan-opening-lines-v1",
        "view_purpose": "source-bound upper-floor opening plan review",
        "projection_basis": "orthographic X-Y plan; opening lines are projected from resolved P2 source coordinates",
        "projected_axes": ["x", "y"],
        "world_to_view": {"axes": ["x", "y"], "scale": [40.0, -40.0], "offset": [-768.0, 953.0]},
        "geometry_kind": "line",
        "entity_ids": [
            "W-H1", "W-H2", "W-G", "W-M-LAT-A", "W-M-REAR", "W-WELL", "W-EGRESS-P2"
        ],
        "dimension_normal": -1.0,
        "features": {
            **{
                entity_id: {
                    "axis": "x",
                    "dimension": "width",
                    "start": "x0",
                    "end": "x1",
                    "screen_x": {"variable_axis": True, "scale": 40.0, "offset": -768.0},
                    "screen_y": {"source_field": "y0", "scale": -40.0, "offset": 953.0},
                    "selector": {"attribute": "data-opening-id", "value": entity_id},
                    "selector_class": "p2-w05-window-opening",
                }
                for entity_id in ("W-H1", "W-H2", "W-G", "W-M-LAT-A")
            },
            **{
                entity_id: {
                    "axis": "y",
                    "dimension": "width",
                    "start": "y0",
                    "end": "y1",
                    "screen_x": {"source_field": "x0", "scale": 40.0, "offset": -768.0},
                    "screen_y": {"variable_axis": True, "scale": -40.0, "offset": 953.0},
                    "selector": {"attribute": "data-opening-id", "value": entity_id},
                    "selector_class": "p2-w05-window-opening",
                }
                for entity_id in ("W-M-REAR", "W-WELL")
            },
            "W-EGRESS-P2": {
                "axis": "y",
                "dimension": "width",
                "start": "y0",
                "end": "y1",
                "screen_x": {"source_field": "x0", "scale": 40.0, "offset": -768.0},
                "screen_y": {"variable_axis": True, "scale": -40.0, "offset": 953.0},
                "selector": {"attribute": "data-opening-id", "value": "W-EGRESS-P2"},
                "selector_class": "p2-w05-window-opening",
            },
        },
    },
    "architecture-roof-daylight-section": {
        "projection_id": "rooflight-transverse-projection-v1",
        "view_purpose": "source-bound transverse rooflight projection review",
        "projection_basis": "orthographic Y-Z projection of each rooflight footprint onto the roof plane derived from current eaves",
        "projected_axes": ["y", "z"],
        "world_to_view": {"axes": ["y", "z"], "scale": [62.0, -62.0], "offset": [180.0, 850.0]},
        "geometry_kind": "line",
        "entity_ids": ["RL-CAR", "RL-RC"],
        "dimension_entity_ids": ["RL-CAR"],
        "dimension_normal": 1.0,
        "features": {
            entity_id: {
                "axis": "y",
                "dimension": "width",
                "start": "y0",
                "end": "y1",
                "selector": {"attribute": "id", "value": f"roof-projection-{entity_id}"},
                "screen_x": {"variable_axis": True, "scale": 62.0, "offset": 180.0},
                "screen_y": {"function": "roofline_by_y"},
            }
            for entity_id in ("RL-CAR", "RL-RC")
        },
    },
    "architecture-rear-elevation": {
        "projection_id": "pb-rear-elevation-p2-openings-v1",
        "view_purpose": "source-bound rear elevation opening review",
        "projection_basis": "orthographic Y-Z elevation of resolved P2 rear openings on the native rear envelope",
        "projected_axes": ["y", "z"],
        "world_to_view": {"axes": ["y", "z"], "scale": [62.0, -62.0], "offset": [140.0, 665.0]},
        "entity_ids": ["W-M-REAR", "W-WELL", "W-EGRESS-P2"],
        "dimension_side": "top",
        "features": {
            entity_id: {
                "x": {
                    "axis": "y", "start": "y0", "end": "y1", "scale": 62.0, "offset": 140.0,
                    "dimension": "width",
                },
                "y": {
                    "axis": "z", "start": "z0", "end": "z1", "scale": -62.0, "offset": 665.0,
                    "dimension": "height",
                },
                "dimension_side": "top",
            }
            for entity_id in ("W-M-REAR", "W-WELL", "W-EGRESS-P2")
        },
        "dimension_entity_ids": ["W-M-REAR", "W-WELL", "W-EGRESS-P2"],
    },
    "architecture-ground-floor-core": {
        "projection_id": "pb-core-room-plan-v1",
        "view_purpose": "source-bound PB core plan review",
        "projection_basis": "orthographic X-Y plan of resolved PB core room envelopes",
        "projected_axes": ["x", "y"],
        "world_to_view": {"axes": ["x", "y"], "scale": [36.0, 36.0], "offset": [-834.0, 115.0]},
        "entity_ids": ["PB-PAN", "PB-BOD", "PB-ESC", "PB-BAN", "PB-HOM"],
        "features": {
            entity_id: {
                "x": {
                    "axis": "x", "start": "x0", "end": "x1", "scale": 36.0, "offset": -834.0,
                    "dimension": "width",
                },
                "y": {
                    "axis": "y", "start": "y0", "end": "y1", "scale": 36.0, "offset": 115.0,
                    "dimension": "depth",
                },
                "dimension_side": "top",
                "horizontal_dimension_position": "inside",
                "horizontal_dimension_offset": 25.0,
            }
            for entity_id in ("PB-PAN", "PB-BOD", "PB-ESC", "PB-BAN", "PB-HOM")
        },
        "dimension_entity_ids": ["PB-BOD"],
    },
    "architecture-pb-integrated-workstations": {
        "projection_id": "pb-workstation-opening-detail-v1",
        "view_purpose": "source-bound PB workstation opening detail review",
        "projection_basis": "multi-panel section and elevation detail; horizontal placement uses fixed detail origins while opening spans and elevations follow source geometry",
        "projected_axes": ["x", "z"],
        "entity_ids": ["GLZ-WS-A"],
        "dimension_entity_ids": ["GLZ-WS-A"],
        "dimension_side": "top",
        "features": {
            "GLZ-WS-A": {
                "x": {
                    "axis": "x", "start": "x0", "end": "x1", "position_scale": 0.0,
                    "span_scale": 100.0, "offset": 510.0, "dimension": "width",
                },
                "y": {
                    "axis": "z", "start": "z0", "end": "z1", "scale": -100.0, "offset": 610.0,
                    "dimension": "height",
                },
                "dimension_side": "top",
            }
        },
    },
    "architecture-p2-bedroom-windows": {
        "projection_id": "p2-bedroom-window-family-detail-v1",
        "view_purpose": "source-bound P2 bedroom-window family detail review",
        "projection_basis": "multi-panel X-Z and Y-Z opening elevations; panel origins are fixed by the native detail layout",
        "projected_axes": ["x", "y", "z"],
        "entity_ids": ["W-H1", "W-M-LAT-A", "W-M-REAR"],
        "dimension_entity_ids": ["W-H1", "W-M-LAT-A", "W-M-REAR"],
        "dimension_side": "top",
        "features": {
            "W-H1": {
                "x": {
                    "axis": "x", "start": "x0", "end": "x1", "position_scale": 0.0,
                    "span_scale": 132.0, "offset": 145.0, "dimension": "width",
                },
                "y": {
                    "axis": "z", "start": "z0", "end": "z1", "scale": -132.0,
                    "offset": 1116.6, "dimension": "height",
                },
                "dimension_side": "top",
                "horizontal_dimension_offset": 35.0,
            },
            "W-M-LAT-A": {
                "x": {
                    "axis": "x", "start": "x0", "end": "x1", "position_scale": 0.0,
                    "span_scale": 90.0, "offset": 815.0, "dimension": "width",
                },
                "y": {
                    "axis": "z", "start": "z0", "end": "z1", "position_scale": 0.0,
                    "span_scale": -90.0, "offset": 496.0, "dimension": "height",
                },
                "dimension_side": "top",
                "horizontal_dimension_offset": 35.0,
            },
            "W-M-REAR": {
                "x": {
                    "axis": "y", "start": "y0", "end": "y1", "position_scale": 0.0,
                    "span_scale": 90.0, "offset": 1190.0, "dimension": "width",
                },
                "y": {
                    "axis": "z", "start": "z0", "end": "z1", "position_scale": 0.0,
                    "span_scale": -90.0, "offset": 496.0, "dimension": "height",
                },
                "dimension_side": "top",
                "horizontal_dimension_offset": 35.0,
            },
        },
    },
    "architecture-access-egress": {
        "projection_id": "p2-access-rescue-opening-plan-v1",
        "view_purpose": "source-bound P2 access and rescue-opening plan review",
        "projection_basis": "orthographic X-Y plan; rescue opening line is projected from resolved P2 source coordinates",
        "projected_axes": ["x", "y"],
        "world_to_view": {"axes": ["x", "y"], "scale": [36.0, -36.0], "offset": [-661.0, 910.0]},
        "geometry_kind": "line",
        "entity_ids": ["W-EGRESS-P2"],
        "dimension_normal": -1.0,
        "features": {
            "W-EGRESS-P2": {
                "axis": "y",
                "start": "y0",
                "end": "y1",
                "screen_x": {"source_field": "x0", "scale": 36.0, "offset": -661.0},
                "screen_y": {"variable_axis": True, "scale": -36.0, "offset": 910.0},
                "selector_class": "rescue-window",
            }
        },
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


def _axis_offset(axis: Mapping[str, Any], entity_id: str) -> float:
    offset = axis.get("offset")
    if offset is None:
        offset = axis["offsets_by_entity"][entity_id]
    return float(offset)


def _axis_origin(
    snapshot: Mapping[str, Any], entity_id: str, axis: Mapping[str, Any]
) -> float:
    if axis.get("bench_context"):
        return _bench_origin(snapshot, entity_id)
    origin_field = axis.get("origin_field")
    if origin_field is not None:
        return _entity_value(snapshot, entity_id, str(origin_field))
    return 0.0


def _axis_endpoints(
    snapshot: Mapping[str, Any], entity_id: str, axis: Mapping[str, Any]
) -> tuple[float, float, float, float]:
    start_field, end_field = str(axis["start"]), str(axis["end"])
    start_value = _axis_source_value(snapshot, entity_id, axis, start_field)
    end_value = _axis_source_value(snapshot, entity_id, axis, end_field)
    if end_value <= start_value:
        raise CoordinationError(f"Native metric feature {entity_id} has a nonpositive source span")
    position_scale = float(axis.get("position_scale", axis.get("scale", 0.0)))
    span_scale = float(axis.get("span_scale", axis.get("scale", 0.0)))
    origin = _axis_origin(snapshot, entity_id, axis)
    offset = _axis_offset(axis, entity_id)
    start_px = offset + position_scale * (start_value - origin)
    end_px = start_px + span_scale * (end_value - start_value)
    if not math.isfinite(start_px) or not math.isfinite(end_px):
        raise CoordinationError(f"Native projection for {entity_id} is not finite")
    return start_value, end_value, start_px, end_px


def _project_coordinate(
    snapshot: Mapping[str, Any], entity_id: str, axis: Mapping[str, Any], field: str
) -> float:
    start_field, end_field = str(axis["start"]), str(axis["end"])
    _, _, start_px, end_px = _axis_endpoints(snapshot, entity_id, axis)
    if field == start_field:
        return start_px
    if field == end_field:
        return end_px
    source = _axis_source_value(snapshot, entity_id, axis, field)
    position_scale = float(axis.get("position_scale", axis.get("scale", 0.0)))
    return _axis_offset(axis, entity_id) + position_scale * (source - _axis_origin(snapshot, entity_id, axis))


def _feature_projection(projection: Mapping[str, Any], entity_id: str) -> Mapping[str, Any]:
    return projection.get("features", {}).get(entity_id, projection)


def _geometry_kind(projection: Mapping[str, Any]) -> str:
    return str(projection.get("geometry_kind", "rect"))


def _expected_rect(
    snapshot: Mapping[str, Any], entity_id: str, feature: Mapping[str, Any]
) -> dict[str, float]:
    expected: dict[str, float] = {}
    for screen_axis in ("x", "y"):
        axis = feature[screen_axis]
        _, _, start_px, end_px = _axis_endpoints(snapshot, entity_id, axis)
        expected[screen_axis] = min(start_px, end_px)
        expected["width" if screen_axis == "x" else "height"] = abs(end_px - start_px)
    return expected


def _roofline_y(snapshot: Mapping[str, Any], y: float) -> float:
    try:
        roof = snapshot["discipline_inputs"]["structure"]["rooflights"]["roof"]
        low_side = roof["low_side"]
        low_eave = _finite(roof["low_eave"], "roof.low_eave")
        high_eave = _finite(roof["high_eave"], "roof.high_eave")
    except (KeyError, TypeError) as error:
        raise CoordinationError("Native roof-section source context is incomplete") from error
    if low_side not in {"A", "B"}:
        raise CoordinationError("Native roof-section source has an unknown low side")
    elevation_a, elevation_b = (low_eave, high_eave) if low_side == "A" else (high_eave, low_eave)
    y_a, y_b = 850.0 - elevation_a * 62.0, 850.0 - elevation_b * 62.0
    return y_a + (y_b - y_a) * y / 18.0


def _screen_point(
    snapshot: Mapping[str, Any],
    entity_id: str,
    feature: Mapping[str, Any],
    source_value: float,
) -> tuple[float, float]:
    entity = snapshot["entities"][entity_id]
    geometry = entity["geometry"]
    point: list[float] = []
    for screen_axis in ("screen_x", "screen_y"):
        transform = feature[screen_axis]
        if transform.get("function") == "roofline_by_y":
            value = _roofline_y(snapshot, source_value)
        elif transform.get("variable_axis"):
            value = float(transform["offset"]) + float(transform["scale"]) * source_value
        else:
            field = str(transform["source_field"])
            value = float(transform["offset"]) + float(transform["scale"]) * _finite(
                geometry[field], f"{entity_id}.geometry.{field}"
            )
        if not math.isfinite(value):
            raise CoordinationError(f"Native line projection for {entity_id} is not finite")
        point.append(value)
    return point[0], point[1]


def _expected_line(
    snapshot: Mapping[str, Any], entity_id: str, feature: Mapping[str, Any]
) -> dict[str, float]:
    geometry = snapshot["entities"][entity_id]["geometry"]
    start_value = _finite(geometry[str(feature["start"])], f"{entity_id}.{feature['start']}")
    end_value = _finite(geometry[str(feature["end"])], f"{entity_id}.{feature['end']}")
    if end_value <= start_value:
        raise CoordinationError(f"Native metric feature {entity_id} has a nonpositive source span")
    start_point = _screen_point(snapshot, entity_id, feature, start_value)
    end_point = _screen_point(snapshot, entity_id, feature, end_value)
    if math.dist(start_point, end_point) <= 1e-9:
        raise CoordinationError(f"Native metric feature {entity_id} has a zero-length projected line")
    return {
        "x1": start_point[0], "y1": start_point[1],
        "x2": end_point[0], "y2": end_point[1],
    }


def _element_line(element: ET.Element, entity_id: str) -> dict[str, float]:
    coordinates: dict[str, float] = {}
    for attribute in ("x1", "y1", "x2", "y2"):
        raw = element.get(attribute)
        if raw is None:
            raise CoordinationError(f"Native metric feature {entity_id} is missing SVG {attribute}")
        try:
            coordinates[attribute] = _finite(float(raw), f"{entity_id}.svg.{attribute}")
        except (TypeError, ValueError, OverflowError) as error:
            raise CoordinationError(f"Native metric feature {entity_id} has invalid SVG {attribute}") from error
    return coordinates


def _rect_occurrences(root: ET.Element, projection: Mapping[str, Any]) -> dict[str, ET.Element]:
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
            expected_tag = _geometry_kind(projection)
            if element.tag.rsplit("}", 1)[-1] != expected_tag:
                raise CoordinationError(
                    f"Native metric feature {entity_id} in {root.get('data-view-id')} is not a {expected_tag}"
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


def _element_rect(element: ET.Element, entity_id: str) -> dict[str, float]:
    actual: dict[str, float] = {}
    for attribute in ("x", "y", "width", "height"):
        raw = element.get(attribute)
        if raw is None:
            raise CoordinationError(f"Native metric feature {entity_id} is missing SVG {attribute}")
        try:
            actual[attribute] = _finite(float(raw), f"{entity_id}.svg.{attribute}")
        except (TypeError, ValueError, OverflowError) as error:
            raise CoordinationError(f"Native metric feature {entity_id} has invalid SVG {attribute}") from error
    return actual


def _coordinates_match(actual: Mapping[str, float], expected: Mapping[str, float]) -> bool:
    return all(
        math.isclose(float(actual[key]), float(expected[key]), rel_tol=0, abs_tol=1e-6)
        for key in expected
    )


def _line_coordinates_match(actual: Mapping[str, float], expected: Mapping[str, float]) -> bool:
    direct = _coordinates_match(actual, expected)
    reversed_endpoints = _coordinates_match(
        actual,
        {"x1": expected["x2"], "y1": expected["y2"], "x2": expected["x1"], "y2": expected["y1"]},
    )
    return direct or reversed_endpoints


def _selector_matches(element: ET.Element, feature: Mapping[str, Any]) -> bool:
    selector = feature.get("selector")
    if selector and element.get(str(selector["attribute"])) != str(selector["value"]):
        return False
    selector_class = feature.get("selector_class")
    return not selector_class or str(selector_class) in element.get("class", "").split()


def tag_native_source_occurrences(snapshot: dict, root: ET.Element) -> None:
    """Attach stable entity identities to existing native geometry by source projection.

    The function only tags a uniquely matching shape already emitted by its renderer. It
    never adds or changes visible geometry; absent or ambiguous features remain a build
    error so an annotation cannot certify a detached overlay.
    """
    view_id = str(root.get("data-view-id") or "")
    projection = NATIVE_VIEW_PROJECTIONS.get(view_id)
    if projection is None:
        return
    kind = _geometry_kind(projection)
    expected_tag = _q(kind)
    for entity_id in projection["entity_ids"]:
        feature = _feature_projection(projection, entity_id)
        expected = (
            _expected_line(snapshot, entity_id, feature)
            if kind == "line"
            else _expected_rect(snapshot, entity_id, feature)
        )
        matches = []
        for element in root.iter(expected_tag):
            if not _selector_matches(element, feature):
                continue
            try:
                actual = _element_line(element, entity_id) if kind == "line" else _element_rect(element, entity_id)
            except CoordinationError:
                if element.get("data-entity-id") == entity_id:
                    raise
                continue
            if (_line_coordinates_match(actual, expected) if kind == "line" else _coordinates_match(actual, expected)):
                matches.append(element)
        existing = [element for element in root.iter() if element.get("data-entity-id") == entity_id]
        if existing:
            if len(existing) != 1 or (matches and existing[0] is not matches[0]):
                raise CoordinationError(f"Native source occurrence identity changed in {view_id}/{entity_id}")
            if not matches:
                matches = existing
        if len(matches) != 1:
            raise CoordinationError(
                f"Native source feature occurrence is {'missing' if not matches else 'ambiguous'} "
                f"in {view_id}/{entity_id} ({len(matches)} matches)"
            )
        element = matches[0]
        if element.get("data-entity-id") not in {None, entity_id}:
            raise CoordinationError(f"Native source feature has an unexpected identity in {view_id}/{entity_id}")
        element.set("data-entity-id", entity_id)
        if not element.get("id"):
            element.set("id", f"{_token(view_id)}-native-{_token(entity_id)}")
        element.set("data-representation-role", str(feature.get("representation_role", "native-source-projection")))
        element.set("data-native-projection-id", str(projection["projection_id"]))


def audit_native_geometry(snapshot: dict, root: ET.Element) -> dict:
    """Check tagged native geometry against independent source-to-SVG transforms.

    The registered transform is independent of the observed native element, so changing
    the feature without changing its source is rejected before annotation.
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

    kind = _geometry_kind(projection)
    occurrences = _rect_occurrences(root, projection)
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
        feature = _feature_projection(projection, entity_id)
        if kind == "line":
            expected = _expected_line(snapshot, entity_id, feature)
            actual = _element_line(element, entity_id)
            if not _line_coordinates_match(actual, expected):
                raise CoordinationError(
                    f"Native geometry projection mismatch for {view_id}/{entity_id}: "
                    f"rendered {actual}, source projects to {expected}"
                )
            features.append(
                {
                    "entity_id": entity_id,
                    "occurrence_id": element.get("id"),
                    "source_shape": geometry["shape"],
                    "projected_shape": "line",
                    "expected_svg_line": {key: _number_text(value) for key, value in expected.items()},
                    "actual_svg_line": {key: _number_text(value) for key, value in actual.items()},
                    "dimension_axis": feature["axis"],
                    "dimension_start": feature["start"],
                    "dimension_end": feature["end"],
                }
            )
        else:
            expected = _expected_rect(snapshot, entity_id, feature)
            actual = _element_rect(element, entity_id)
            for attribute in ("x", "y", "width", "height"):
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
                    "projected_shape": "rect",
                    "expected_svg_rect": {key: _number_text(value) for key, value in expected.items()},
                    "actual_svg_rect": {key: _number_text(value) for key, value in actual.items()},
                }
            )
    return {
        "state": "evaluated",
        "view_id": view_id,
        "projection_id": projection["projection_id"],
        "geometry_kind": kind,
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
    horizontal_position = projection.get("horizontal_dimension_position", "outside")
    horizontal_offset = float(projection.get("horizontal_dimension_offset", 11.0))
    if horizontal_position == "inside":
        h_dim_y = top + horizontal_offset
        h_label_y = h_dim_y - 4.0
    elif projection["dimension_side"] == "top":
        h_dim_y = top - horizontal_offset
        h_label_y = h_dim_y - 4.0
    else:
        h_dim_y = bottom + horizontal_offset - 1.0
        h_label_y = h_dim_y + 13.0
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
    if float(v_axis.get("span_scale", v_axis.get("scale", 0.0))) < 0:
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


def _add_line_feature_annotation(
    parent: ET.Element,
    snapshot: Mapping[str, Any],
    view_id: str,
    entity_id: str,
    feature: Mapping[str, Any],
    normal_sign: float,
) -> None:
    axis_name = str(feature["axis"])
    start_field, end_field = str(feature["start"]), str(feature["end"])
    start_value = _axis_source_value(snapshot, entity_id, {}, start_field)
    end_value = _axis_source_value(snapshot, entity_id, {}, end_field)
    value = end_value - start_value
    if value <= 0:
        raise CoordinationError(f"Native dimension {entity_id} has a nonpositive source value")
    start_point = _screen_point(snapshot, entity_id, feature, start_value)
    end_point = _screen_point(snapshot, entity_id, feature, end_value)
    dx, dy = end_point[0] - start_point[0], end_point[1] - start_point[1]
    length = math.hypot(dx, dy)
    if length <= 1e-9:
        raise CoordinationError(f"Native dimension {entity_id} has a zero-length screen span")
    normal = (-dy / length * normal_sign, dx / length * normal_sign)
    offset = float(feature.get("dimension_offset", 12.0))
    dim_start = (start_point[0] + normal[0] * offset, start_point[1] + normal[1] * offset)
    dim_end = (end_point[0] + normal[0] * offset, end_point[1] + normal[1] * offset)
    start_ref, start_target = _add_anchor(
        parent,
        snapshot,
        view_id,
        entity_id,
        f"{feature.get('dimension', 'span')}.start",
        {"axis": axis_name},
        start_field,
        *start_point,
    )
    end_ref, end_target = _add_anchor(
        parent,
        snapshot,
        view_id,
        entity_id,
        f"{feature.get('dimension', 'span')}.end",
        {"axis": axis_name},
        end_field,
        *end_point,
    )
    _line(parent, *dim_start, *dim_end)
    tick = 3.5
    for x, y in (dim_start, dim_end):
        _line(
            parent,
            x - normal[0] * tick,
            y - normal[1] * tick,
            x + normal[0] * tick,
            y + normal[1] * tick,
        )
    _line(parent, *start_point, *dim_start, extension=True)
    _line(parent, *end_point, *dim_end, extension=True)
    dimension_name = str(feature.get("dimension", "span"))
    angle = math.degrees(math.atan2(dy, dx))
    if angle > 90 or angle < -90:
        angle += 180
    mid_x = (dim_start[0] + dim_end[0]) / 2
    mid_y = (dim_start[1] + dim_end[1]) / 2
    label_point = (mid_x + normal[0] * 4.0, mid_y + normal[1] * 4.0)
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
        "data-dimension-id": f"{entity_id}.{dimension_name}",
        "data-anchor-refs": f"{start_ref} {end_ref}",
        "data-anchor-targets": f"{start_target} {end_target}",
        "data-dimension-status": "resolved",
        "data-dimension-datum": f"source {axis_name} coordinate",
        "data-dimension-direction": "parallel",
        "data-dimension-value": _number_text(value),
        "data-dimension-unit": "m",
        "data-dimension-source": (
            f"entities.{entity_id}.geometry.{start_field} → "
            f"entities.{entity_id}.geometry.{end_field}"
        ),
        "data-dimension-label-format": "fixed-2-m",
        "transform": f"rotate({_number_text(angle)} {_number_text(label_point[0])} {_number_text(label_point[1])})",
    }
    text = ET.SubElement(parent, _q("text"), text_attrs)
    text.text = f"{value:.2f} m"


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
        reason = (
            "No entity-based native projection is registered here. Source-context sheets "
            "are dispatched through their dedicated adapters by render_drawings; unknown "
            "projections withhold entity-based dimensions."
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

    tag_native_source_occurrences(snapshot, root)
    root.set("data-view-purpose", str(projection["view_purpose"]))
    root.set("data-projection-basis", str(projection["projection_basis"]))
    root.set("data-projected-axes", " ".join(projection["projected_axes"]))
    transform = projection.get("world_to_view")
    if transform is not None:
        root.set("data-world-to-view", json.dumps(transform, sort_keys=True, separators=(",", ":")))

    audit = audit_native_geometry(snapshot, root)
    if audit["state"] != "evaluated":
        raise CoordinationError(f"Native geometry projection was not evaluated for {view_id}")
    occurrences = _rect_occurrences(root, projection)
    kind = _geometry_kind(projection)
    group = ET.Element(
        _q("g"),
        {
            "id": f"{_token(view_id)}-source-bound-dimensions",
            "data-annotation-scope": "source-bound-native-feature-dimensions",
            "data-geometry-projection-id": projection["projection_id"],
        },
    )
    dimension_entity_ids = set(projection.get("dimension_entity_ids", projection["entity_ids"]))
    dimensions = 0
    anchors = 0
    for entity_id, element in sorted(occurrences.items()):
        if entity_id not in dimension_entity_ids:
            continue
        feature = _feature_projection(projection, entity_id)
        if kind == "line":
            _add_line_feature_annotation(
                group,
                snapshot,
                view_id,
                entity_id,
                feature,
                float(projection.get("dimension_normal", -1.0)),
            )
            dimensions += 1
            anchors += 2
        else:
            _add_feature_annotations(group, snapshot, view_id, feature, entity_id, element)
            dimensions += 2
            anchors += 4
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
        "anchors": anchors,
        "dimensions": dimensions,
        "supported_scope": (
            "source-coordinate span dimensions for tagged native lines"
            if kind == "line"
            else "width/length and height/depth dimensions for tagged source rectangles"
        ),
    }

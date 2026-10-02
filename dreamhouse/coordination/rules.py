"""Pure geometry, opening-measurement, and coordination-rule evaluation.

The evaluator consumes one already-resolved snapshot. It reads no project files and
does not treat schematic geometry as professional design approval.
"""

from __future__ import annotations

import math
from collections import defaultdict
from itertools import combinations
from typing import Any

from dreamhouse.quantities.ledger import _ASSEMBLY_BY_SOURCE_AND_KIND

TOLERANCE_M = 1e-6
_COVERAGE_STATES = ("evaluated", "unsupported", "inapplicable", "not_run")
_PHYSICAL_KINDS = {"opening", "door", "column", "wall", "equipment", "stair", "reservation"}
_OPENING_KINDS = {"opening", "door"}
_ROOFLIGHT_FAMILY = "ROOFLIGHTS.rooflights"

# Metadata is part of the public evaluator result so each finding can be read with
# its required inputs and limits. These are schematic coordination rules only.
RULE_REGISTRY: tuple[dict[str, Any], ...] = (
    {
        "rule_id": "OPENING-DIMENSION-AREA",
        "description": "Measure a nominal opening area from declared dimensions.",
        "required_geometry": ["opening family", "width and height, or rooflight length and width"],
        "dependencies": ["entity.parameters"],
        "tolerances": {"length_m": TOLERANCE_M, "area_m2": 0.001},
        "limits": ["Area is a gross nominal opening area; net glass area is unknown."],
    },
    {
        "rule_id": "OPENING-MODULE-CONSISTENCY",
        "description": "Check declared window width against its declared module count and width.",
        "required_geometry": ["width_m", "modules", "module_width_m"],
        "dependencies": ["entity.parameters"],
        "tolerances": {"length_m": TOLERANCE_M},
        "limits": ["The check runs only when the source snapshot declares module_width_m."],
    },
    {
        "rule_id": "OPENING-QUANTITY-FAMILY",
        "description": "Map an opening family to a named quantity assembly.",
        "required_geometry": ["entity.family"],
        "dependencies": ["explicit family-to-assembly map"],
        "tolerances": {},
        "limits": ["A mapping does not establish product selection, price, or budget eligibility."],
    },
    {
        "rule_id": "OPENING-IN-HOST-EXTENT",
        "description": "Check that an opening fits within its declared host extent.",
        "required_geometry": ["opening XY bounds and vertical extent", "host extent"],
        "dependencies": ["relationships.host_id"],
        "tolerances": {"length_m": TOLERANCE_M},
        "limits": [
            "A facade reference line without a known vertical extent cannot pass this check."
        ],
    },
    {
        "rule_id": "OPENING-IN-SPACE-BOUNDARY",
        "description": "Check that a room-linked window lies on and within each declared space boundary.",
        "required_geometry": ["opening XY bounds", "space XY bounds"],
        "dependencies": ["relationships.space_ids", "space geometry"],
        "tolerances": {"length_m": TOLERANCE_M},
        "limits": [
            "This is a plan-only room-boundary check; it does not check sill or head clearances."
        ],
    },
    {
        "rule_id": "ROOFLIGHT-IN-HALL-EXTENT",
        "description": "Check that a rooflight footprint lies within the hall plan extent.",
        "required_geometry": ["rooflight XY bounds", "hall length and width"],
        "dependencies": ["snapshot.geometry.hall", "entity.geometry"],
        "tolerances": {"length_m": TOLERANCE_M},
        "limits": [
            "This is a plan-only extent check; it does not verify roof structure or curb design."
        ],
    },
    {
        "rule_id": "RESERVATION-OPENING-PLAN",
        "description": "Expose plan-overlap candidates between openings and structural reservations.",
        "required_geometry": ["reservation XY bounds", "opening XY bounds"],
        "dependencies": ["entity.geometry", "entity.kind", "entity.status"],
        "tolerances": {"length_m": TOLERANCE_M},
        "limits": [
            "A plan overlap is an OPEN review candidate, not a confirmed 3D clash; a reservation is not a structural member."
        ],
    },
    {
        "rule_id": "ENTITY-GEOMETRY-CAPABILITY",
        "description": "Expose enrolled entities whose geometry is explicitly unresolved.",
        "required_geometry": ["entity.geometry.shape"],
        "dependencies": ["entity.status", "entity.geometry", "entity.parameters", "entity.source"],
        "tolerances": {},
        "limits": [
            "No geometry is inferred; geometry-based checks for this entity remain unperformed."
        ],
    },
    {
        "rule_id": "SAME-HOST-OVERLAP",
        "description": "Check hosted elements for positive-volume overlap.",
        "required_geometry": ["shared host", "known compatible element bounds"],
        "dependencies": ["relationships.host_id", "entity.geometry or facade parameters"],
        "tolerances": {"length_m": TOLERANCE_M},
        "limits": ["Intentional host-to-opening containment is handled by OPENING-IN-HOST-EXTENT."],
    },
    {
        "rule_id": "COLUMN-OPENING-INTERFERENCE",
        "description": "Check known column boxes against opening extents in plan and height.",
        "required_geometry": [
            "column box XY bounds and z0/z1",
            "opening XY bounds and vertical extent",
        ],
        "dependencies": [
            "entity.geometry",
            "opening level, sill, and height when z bounds are absent",
        ],
        "tolerances": {"length_m": TOLERANCE_M},
        "limits": [
            "Unknown column shape or height remains OPEN; no structural capacity is calculated."
        ],
    },
    {
        "rule_id": "RESERVATION-EXTENT-COVERAGE",
        "description": "Expose the limits of plan-only structural reservations.",
        "required_geometry": ["reservation plan bounds", "vertical extent for 3D clearance"],
        "dependencies": ["entity.geometry", "entity.status"],
        "tolerances": {"length_m": TOLERANCE_M},
        "limits": [
            "A reservation is not a structural member and unknown z cannot be certified clash-free."
        ],
    },
    {
        "rule_id": "PROFESSIONAL-DESIGN-GATE",
        "description": "Keep relevant professional design checks visibly open.",
        "required_geometry": ["entity kind and identity"],
        "dependencies": ["entity.kind", "entity.id or aliases"],
        "tolerances": {},
        "limits": [
            "This evaluator does not perform signed structural, fire, egress, glazing, or building-physics design."
        ],
    },
)

_RULE_IDS = {item["rule_id"] for item in RULE_REGISTRY}


def _number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _entities(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = snapshot.get("entities", {})
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if not isinstance(value, dict):
            continue
        identifier = str(value.get("id", key))
        result[identifier] = value
    return result


def _entity_status(entity: dict[str, Any]) -> str:
    return str(entity.get("status", "active"))


def _is_active(entity: dict[str, Any]) -> bool:
    return _entity_status(entity) == "active"


def _parameter(entity: dict[str, Any], name: str) -> float | None:
    parameters = entity.get("parameters")
    return _number(parameters.get(name)) if isinstance(parameters, dict) else None


def _source_reference(source: object) -> str | None:
    if isinstance(source, dict):
        path = source.get("path")
        key = source.get("key")
        if path and key:
            return f"{path}#{key}"
        if path:
            return str(path)
    return None


def _source_path(entity: dict[str, Any]) -> str:
    working_source = _source_reference(entity.get("working_source"))
    if working_source:
        return working_source
    source = _source_reference(entity.get("source"))
    if source:
        return source
    return str(entity.get("family", "unknown"))


def _source_provenance(entity: dict[str, Any]) -> dict[str, str]:
    result = {"source_model": _source_path(entity)}
    working_source = _source_reference(entity.get("working_source"))
    baseline_source = _source_reference(entity.get("source"))
    if working_source and baseline_source and working_source != baseline_source:
        result["baseline_source_model"] = baseline_source
    return result


def _opening_assembly(family: object) -> str | None:
    family_name = str(family) if family is not None else ""
    expected_kind = "rooflight" if family_name == _ROOFLIGHT_FAMILY else "vertical_glazing"
    return _ASSEMBLY_BY_SOURCE_AND_KIND.get((family_name, expected_kind))


def _opening_measurement(entity: dict[str, Any]) -> dict[str, float | None]:
    family = entity.get("family")
    if family == _ROOFLIGHT_FAMILY:
        length = _parameter(entity, "length_m")
        width = _parameter(entity, "width_m")
        if length is None or width is None or length <= 0 or width <= 0:
            return {
                "length_m": length,
                "width_m": width,
                "height_m": None,
                "area_m2": None,
                "perimeter_m": None,
            }
        return {
            "length_m": length,
            "width_m": width,
            "height_m": None,
            "area_m2": round(length * width, 3),
            "perimeter_m": round(2 * (length + width), 3),
        }

    width = _parameter(entity, "width_m")
    height = _parameter(entity, "height_m")
    if width is None or height is None or width <= 0 or height <= 0:
        return {
            "length_m": None,
            "width_m": width,
            "height_m": height,
            "area_m2": None,
            "perimeter_m": None,
        }
    return {
        "length_m": None,
        "width_m": width,
        "height_m": height,
        "area_m2": round(width * height, 3),
        "perimeter_m": round(2 * (width + height), 3),
    }


def _vertical_bounds(entity: dict[str, Any]) -> tuple[float, float] | None:
    geometry = entity.get("geometry")
    if isinstance(geometry, dict):
        z0, z1 = _number(geometry.get("z0")), _number(geometry.get("z1"))
        if z0 is not None and z1 is not None and z1 >= z0:
            return z0, z1

    level = _parameter(entity, "level_m")
    sill = _parameter(entity, "sill_m")
    height = _parameter(entity, "height_m")
    if level is None or sill is None or height is None or height <= 0:
        return None
    return level + sill, level + sill + height


def _xy_bounds(entity: dict[str, Any]) -> tuple[float, float, float, float] | None:
    geometry = entity.get("geometry")
    if not isinstance(geometry, dict):
        return None
    bounds = tuple(_number(geometry.get(key)) for key in ("x0", "x1", "y0", "y1"))
    if any(value is None for value in bounds):
        return None
    x0, x1, y0, y1 = bounds
    if x1 < x0 or y1 < y0:
        return None
    return x0, x1, y0, y1


def _box_bounds(entity: dict[str, Any], *, require_box: bool = False) -> tuple[float, ...] | None:
    geometry = entity.get("geometry")
    if not isinstance(geometry, dict):
        return None
    shape = geometry.get("shape")
    if require_box and shape != "box":
        return None
    if shape not in {"box", "rect", "opening", "line"}:
        return None
    xy = _xy_bounds(entity)
    z = _vertical_bounds(entity)
    if xy is None or z is None:
        return None
    x0, x1, y0, y1 = xy
    z0, z1 = z
    return x0, x1, y0, y1, z0, z1


def _positive_overlap(a0: float, a1: float, b0: float, b1: float) -> float:
    return min(a1, b1) - max(a0, b0)


def _bounds_overlap(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[bool, tuple[float, ...]]:
    overlaps = tuple(
        _positive_overlap(a[index], a[index + 1], b[index], b[index + 1]) for index in (0, 2, 4)
    )
    return all(value > TOLERANCE_M for value in overlaps), overlaps


def _column_opening_overlap(
    column: tuple[float, ...], opening: tuple[float, ...]
) -> tuple[bool, tuple[float, float, float]]:
    """Treat a supported vertical opening plane as intersecting a box that spans it.

    The opening representation can be a zero-thickness facade plane. Such a plane
    intersects a column footprint when it lies strictly inside the column bounds;
    equality at the column face remains touching, not a clash.
    """

    intersections = []
    for index in (0, 2):
        low, high = opening[index], opening[index + 1]
        column_low, column_high = column[index], column[index + 1]
        if high - low <= TOLERANCE_M:
            intersects = column_low + TOLERANCE_M < low < column_high - TOLERANCE_M
            intersections.append(0.0)
            if not intersects:
                return False, (intersections[0], 0.0, 0.0)
        else:
            overlap = _positive_overlap(column_low, column_high, low, high)
            intersections.append(overlap)
            if overlap <= TOLERANCE_M:
                return False, (intersections[0], intersections[1], 0.0)

    vertical = _positive_overlap(column[4], column[5], opening[4], opening[5])
    intersections.append(vertical)
    return vertical > TOLERANCE_M, tuple(intersections)  # type: ignore[return-value]


def _facade_region(entity: dict[str, Any]) -> tuple[float, float, float, float] | None:
    start = _parameter(entity, "start_m")
    width = _parameter(entity, "width_m")
    vertical = _vertical_bounds(entity)
    if start is None or width is None or width <= 0 or vertical is None:
        return None
    return start, start + width, vertical[0], vertical[1]


def _regions_overlap(
    a: tuple[float, float, float, float], b: tuple[float, float, float, float]
) -> tuple[bool, tuple[float, float]]:
    along = _positive_overlap(a[0], a[1], b[0], b[1])
    vertical = _positive_overlap(a[2], a[3], b[2], b[3])
    return along > TOLERANCE_M and vertical > TOLERANCE_M, (along, vertical)


def _line_axis(host_geometry: dict[str, Any]) -> tuple[str, float, float, float] | None:
    x0, x1, y0, y1 = (_number(host_geometry.get(key)) for key in ("x0", "x1", "y0", "y1"))
    if None in (x0, x1, y0, y1):
        return None
    if x1 < x0 or y1 < y0:
        return None
    if abs(y1 - y0) <= TOLERANCE_M and x1 - x0 > TOLERANCE_M:
        return "x", y0, x0, x1
    if abs(x1 - x0) <= TOLERANCE_M and y1 - y0 > TOLERANCE_M:
        return "y", x0, y0, y1
    return None


def _host_extent_result(
    opening: dict[str, Any], host: dict[str, Any]
) -> tuple[str, str, dict[str, Any]]:
    """Return coverage, status, and evidence for a box or facade-reference-line host."""

    opening_xy = _xy_bounds(opening)
    host_geometry = host.get("geometry")
    if opening_xy is None or not isinstance(host_geometry, dict):
        return "unsupported", "OPEN", {"reason": "Opening or host bounds are incomplete."}

    shape = host_geometry.get("shape")
    if shape == "line":
        axis = _line_axis(host_geometry)
        if axis is None:
            return (
                "unsupported",
                "OPEN",
                {
                    "host_shape": "line",
                    "reason": "Facade reference line lacks a usable horizontal extent.",
                },
            )
        direction, fixed, along0, along1 = axis
        x0, x1, y0, y1 = opening_xy
        along_open0, along_open1 = (x0, x1) if direction == "x" else (y0, y1)
        across0, across1 = (y0, y1) if direction == "x" else (x0, x1)
        horizontal_ok = (
            along_open0 >= along0 - TOLERANCE_M
            and along_open1 <= along1 + TOLERANCE_M
            and across0 - TOLERANCE_M <= fixed <= across1 + TOLERANCE_M
        )
        opening_z = _vertical_bounds(opening)
        host_z = _vertical_bounds(host)
        if not horizontal_ok:
            return (
                "evaluated",
                "FAIL",
                {
                    "host_shape": "line",
                    "line_axis": direction,
                    "host_along_m": [along0, along1],
                    "opening_along_m": [along_open0, along_open1],
                    "horizontal_contained": False,
                    "vertical_check": "not required to establish horizontal overrun",
                    "tolerance_m": TOLERANCE_M,
                },
            )
        if opening_z is None or host_z is None:
            return (
                "unsupported",
                "OPEN",
                {
                    "host_shape": "line",
                    "line_axis": direction,
                    "host_along_m": [along0, along1],
                    "opening_along_m": [along_open0, along_open1],
                    "horizontal_contained": True,
                    "host_vertical_m": list(host_z) if host_z else None,
                    "opening_vertical_m": list(opening_z) if opening_z else None,
                    "reason": "Horizontal extent fits, but a vertical extent is unknown.",
                    "tolerance_m": TOLERANCE_M,
                },
            )
        vertical_ok = (
            opening_z[0] >= host_z[0] - TOLERANCE_M and opening_z[1] <= host_z[1] + TOLERANCE_M
        )
        return (
            "evaluated",
            "PASS" if vertical_ok else "FAIL",
            {
                "host_shape": "line",
                "line_axis": direction,
                "host_along_m": [along0, along1],
                "opening_along_m": [along_open0, along_open1],
                "host_vertical_m": list(host_z),
                "opening_vertical_m": list(opening_z),
                "horizontal_contained": horizontal_ok,
                "vertical_contained": vertical_ok,
                "tolerance_m": TOLERANCE_M,
            },
        )

    host_xy = _xy_bounds(host)
    if host_xy is None:
        return (
            "unsupported",
            "OPEN",
            {
                "reason": "Host requires supported horizontal bounds.",
                "host_shape": shape,
            },
        )
    horizontal_ok = (
        opening_xy[0] >= host_xy[0] - TOLERANCE_M
        and opening_xy[1] <= host_xy[1] + TOLERANCE_M
        and opening_xy[2] >= host_xy[2] - TOLERANCE_M
        and opening_xy[3] <= host_xy[3] + TOLERANCE_M
    )
    if not horizontal_ok:
        return (
            "evaluated",
            "FAIL",
            {
                "host_shape": shape,
                "host_bounds_xy": list(host_xy),
                "opening_bounds_xy": list(opening_xy),
                "horizontal_contained": False,
                "vertical_check": "not required to establish horizontal overrun",
                "tolerance_m": TOLERANCE_M,
            },
        )
    opening_z = _vertical_bounds(opening)
    host_z = _vertical_bounds(host)
    if opening_z is None or host_z is None:
        return (
            "unsupported",
            "OPEN",
            {
                "host_shape": shape,
                "host_bounds_xy": list(host_xy),
                "opening_bounds_xy": list(opening_xy),
                "horizontal_contained": True,
                "host_vertical_m": list(host_z) if host_z else None,
                "opening_vertical_m": list(opening_z) if opening_z else None,
                "reason": "Horizontal extent fits, but a vertical extent is unknown.",
                "tolerance_m": TOLERANCE_M,
            },
        )
    vertical_ok = (
        opening_z[0] >= host_z[0] - TOLERANCE_M and opening_z[1] <= host_z[1] + TOLERANCE_M
    )
    return (
        "evaluated",
        "PASS" if vertical_ok else "FAIL",
        {
            "host_shape": shape,
            "host_bounds_xy": list(host_xy),
            "opening_bounds_xy": list(opening_xy),
            "host_vertical_m": list(host_z),
            "opening_vertical_m": list(opening_z),
            "horizontal_contained": True,
            "vertical_contained": vertical_ok,
            "tolerance_m": TOLERANCE_M,
        },
    )


def _space_boundary_result(
    opening: dict[str, Any], space: dict[str, Any]
) -> tuple[str, str, dict[str, Any]]:
    opening_xy = _xy_bounds(opening)
    space_xy = _xy_bounds(space)
    geometry = space.get("geometry")
    if (
        opening_xy is None
        or space_xy is None
        or not isinstance(geometry, dict)
        or geometry.get("shape") != "rect"
    ):
        return (
            "unsupported",
            "OPEN",
            {
                "reason": "Opening or declared space lacks a supported rectangular plan extent.",
                "space_shape": geometry.get("shape") if isinstance(geometry, dict) else None,
            },
        )

    x0, x1, y0, y1 = opening_xy
    sx0, sx1, sy0, sy1 = space_xy
    fits = (
        x0 >= sx0 - TOLERANCE_M
        and x1 <= sx1 + TOLERANCE_M
        and y0 >= sy0 - TOLERANCE_M
        and y1 <= sy1 + TOLERANCE_M
    )
    # The bounds check above ensures the coincident edge spans only the declared
    # room edge; test it separately for clear evidence in the finding.
    boundary_match = (
        (abs(x0 - sx0) <= TOLERANCE_M and y0 >= sy0 - TOLERANCE_M and y1 <= sy1 + TOLERANCE_M)
        or (abs(x1 - sx1) <= TOLERANCE_M and y0 >= sy0 - TOLERANCE_M and y1 <= sy1 + TOLERANCE_M)
        or (abs(y0 - sy0) <= TOLERANCE_M and x0 >= sx0 - TOLERANCE_M and x1 <= sx1 + TOLERANCE_M)
        or (abs(y1 - sy1) <= TOLERANCE_M and x0 >= sx0 - TOLERANCE_M and x1 <= sx1 + TOLERANCE_M)
    )
    passed = fits and boundary_match
    return (
        "evaluated",
        "PASS" if passed else "FAIL",
        {
            "opening_bounds_xy": list(opening_xy),
            "space_bounds_xy": list(space_xy),
            "fits_within_space": fits,
            "lies_on_space_boundary": boundary_match,
            "tolerance_m": TOLERANCE_M,
        },
    )


def _rooflight_hall_result(
    rooflight: dict[str, Any], hall: object
) -> tuple[str, str, dict[str, Any]]:
    footprint = _xy_bounds(rooflight)
    if footprint is None or not isinstance(hall, dict):
        return (
            "unsupported",
            "OPEN",
            {"reason": "Rooflight footprint or hall plan extent is unavailable."},
        )

    hall_length = _number(hall.get("length_m"))
    hall_width = _number(hall.get("width_m"))
    x0, x1, y0, y1 = footprint
    x_outside = hall_length is not None and (x0 < -TOLERANCE_M or x1 > hall_length + TOLERANCE_M)
    y_outside = hall_width is not None and (y0 < -TOLERANCE_M or y1 > hall_width + TOLERANCE_M)
    evidence = {
        "rooflight_bounds_xy": list(footprint),
        "hall_length_m": hall_length,
        "hall_width_m": hall_width,
        "x_within_hall": None if hall_length is None else not x_outside,
        "y_within_hall": None if hall_width is None else not y_outside,
        "tolerance_m": TOLERANCE_M,
    }
    if x_outside or y_outside:
        return "evaluated", "FAIL", evidence
    if hall_length is None or hall_width is None:
        return (
            "unsupported",
            "OPEN",
            {
                **evidence,
                "reason": "A hall plan dimension is unknown; full containment cannot be evaluated.",
            },
        )
    return "evaluated", "PASS", evidence


def _reservation_opening_plan_result(
    reservation: dict[str, Any], opening: dict[str, Any]
) -> tuple[bool | None, dict[str, Any]]:
    reservation_geometry = reservation.get("geometry")
    opening_geometry = opening.get("geometry")
    reservation_xy = _xy_bounds(reservation)
    opening_xy = _xy_bounds(opening)
    supported_opening_shapes = {"opening", "rect", "box", "line"}
    if (
        reservation_xy is None
        or opening_xy is None
        or not isinstance(reservation_geometry, dict)
        or reservation_geometry.get("shape") not in {"rect", "box"}
        or not isinstance(opening_geometry, dict)
        or opening_geometry.get("shape") not in supported_opening_shapes
    ):
        return None, {
            "reservation_bounds_xy": list(reservation_xy) if reservation_xy else None,
            "opening_bounds_xy": list(opening_xy) if opening_xy else None,
            "reason": "Reservation or opening lacks supported plan bounds.",
        }

    rx0, rx1, ry0, ry1 = reservation_xy
    ox0, ox1, oy0, oy1 = opening_xy
    reservation_spans = ((rx0, rx1), (ry0, ry1))
    opening_spans = ((ox0, ox1), (oy0, oy1))
    intersection_lengths: list[float] = []
    plane_axes: list[str] = []
    overlaps_each_axis: list[bool] = []
    for axis, (reservation_span, opening_span) in enumerate(
        zip(reservation_spans, opening_spans, strict=True)
    ):
        reservation_low, reservation_high = reservation_span
        opening_low, opening_high = opening_span
        if reservation_high - reservation_low <= TOLERANCE_M:
            return None, {
                "reservation_bounds_xy": list(reservation_xy),
                "opening_bounds_xy": list(opening_xy),
                "reason": "Reservation plan footprint has a zero-width axis.",
            }
        if opening_high - opening_low <= TOLERANCE_M:
            coordinate = (opening_low + opening_high) / 2
            crosses = reservation_low + TOLERANCE_M < coordinate < reservation_high - TOLERANCE_M
            overlaps_each_axis.append(crosses)
            intersection_lengths.append(0.0)
            if crosses:
                plane_axes.append("xy"[axis])
        else:
            intersection = _positive_overlap(
                reservation_low, reservation_high, opening_low, opening_high
            )
            intersection_lengths.append(max(intersection, 0.0))
            overlaps_each_axis.append(intersection > TOLERANCE_M)

    overlaps = all(overlaps_each_axis)
    return overlaps, {
        "reservation_bounds_xy": list(reservation_xy),
        "opening_bounds_xy": list(opening_xy),
        "intersection_lengths_m": [round(value, 6) for value in intersection_lengths],
        "opening_plane_axes_inside_reservation": plane_axes,
        "plan_overlap_candidate": overlaps,
        "reservation_vertical_bounds_known": _vertical_bounds(reservation) is not None,
        "opening_vertical_bounds_known": _vertical_bounds(opening) is not None,
        "three_dimensional_clash": "not evaluated",
        "reservation_is_structural_member": False,
        "tolerance_m": TOLERANCE_M,
    }


def _finding_id(rule_id: str, entity_ids: tuple[str, ...]) -> str:
    return f"{rule_id}:" + ":".join(sorted(set(entity_ids)))


def _evaluate_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    entities = _entities(snapshot)
    findings: list[dict[str, Any]] = []
    coverage_rows: dict[str, dict[str, Any]] = {
        rule_id: {
            "counts": {state: 0 for state in _COVERAGE_STATES},
            "entity_ids": {state: set() for state in _COVERAGE_STATES},
        }
        for rule_id in _RULE_IDS
    }

    def emit(
        rule_id: str,
        status: str,
        coverage: str,
        severity: str,
        message: str,
        entity_ids: tuple[str, ...] = (),
        evidence: dict[str, Any] | None = None,
    ) -> None:
        ordered_ids = tuple(sorted(set(entity_ids)))
        finding = {
            "finding_id": _finding_id(rule_id, ordered_ids),
            "rule_id": rule_id,
            "status": status,
            "coverage": coverage,
            "severity": severity,
            "message": message,
            "entity_ids": list(ordered_ids),
            "evidence": evidence or {},
            "scenario_id": snapshot.get("scenario_id"),
            "input_hash": snapshot.get("input_hash"),
            "model_hash": snapshot.get("model_hash"),
        }
        findings.append(finding)
        row = coverage_rows[rule_id]
        row["counts"][coverage] += 1
        row["entity_ids"][coverage].update(ordered_ids)

    opening_entities = {
        identifier: item
        for identifier, item in entities.items()
        if item.get("kind") in _OPENING_KINDS
    }

    # Active opening measurements, explicit family mappings, and an auditable
    # schedule. Study items remain visible but never contribute to totals.
    schedule_items: list[dict[str, Any]] = []
    study_items: list[dict[str, Any]] = []
    quantity_records: list[dict[str, Any]] = []
    quantity_totals: dict[str, dict[str, float]] = {}

    for identifier in sorted(opening_entities):
        entity = opening_entities[identifier]
        status = _entity_status(entity)
        if status not in {"active", "study", "context"}:
            continue
        measurement = _opening_measurement(entity)
        family = entity.get("family")
        assembly = _opening_assembly(family)
        is_rooflight = family == _ROOFLIGHT_FAMILY
        dimensions_known = measurement["area_m2"] is not None
        schedule_item = {
            "id": identifier,
            "kind": entity.get("kind"),
            "family": family,
            "status": status,
            **_source_provenance(entity),
            "facade": (entity.get("parameters") or {}).get("facade")
            if isinstance(entity.get("parameters"), dict)
            else None,
            "start_m": _parameter(entity, "start_m"),
            "length_m": measurement["length_m"],
            "width_m": measurement["width_m"],
            "height_m": measurement["height_m"],
            "sill_m": _parameter(entity, "sill_m"),
            "level_m": _parameter(entity, "level_m"),
            "area_m2": measurement["area_m2"],
            "perimeter_m": measurement["perimeter_m"],
            "net_glass_area_m2": None,
            "measurement_status": (
                "model-derived nominal opening area; net glass area unknown"
                if dimensions_known
                else "required dimensions pending"
            ),
            "quantity_assembly": assembly,
            "quantity_included": status == "active" and assembly is not None and dimensions_known,
        }
        if status == "study":
            schedule_item["quantity_included"] = False
            schedule_item["exclusion_reason"] = (
                "Study-status entity; excluded from active quantity totals."
            )
            study_items.append(schedule_item)
        else:
            schedule_items.append(schedule_item)

        module_width = _parameter(entity, "module_width_m")
        if module_width is not None:
            parameters = entity.get("parameters")
            module_count = (
                _number(parameters.get("modules")) if isinstance(parameters, dict) else None
            )
            declared_width = measurement["width_m"]
            if (
                module_width <= 0
                or module_count is None
                or module_count <= 0
                or not module_count.is_integer()
                or declared_width is None
            ):
                emit(
                    "OPENING-MODULE-CONSISTENCY",
                    "OPEN",
                    "unsupported",
                    "warning",
                    "The source declares a module width but lacks a positive integer module count or opening width.",
                    (identifier,),
                    {
                        "module_width_m": module_width,
                        "modules": module_count,
                        "width_m": declared_width,
                    },
                )
            else:
                computed_width = module_count * module_width
                consistent = abs(declared_width - computed_width) <= TOLERANCE_M
                emit(
                    "OPENING-MODULE-CONSISTENCY",
                    "PASS" if consistent else "FAIL",
                    "evaluated",
                    "info" if consistent else "error",
                    "Declared opening width matches its module schedule."
                    if consistent
                    else "Declared opening width does not match its module schedule.",
                    (identifier,),
                    {
                        "width_m": declared_width,
                        "modules": int(module_count),
                        "module_width_m": module_width,
                        "computed_width_m": round(computed_width, 6),
                        "difference_m": round(declared_width - computed_width, 6),
                        "tolerance_m": TOLERANCE_M,
                    },
                )

        if status != "active":
            continue

        if dimensions_known:
            emit(
                "OPENING-DIMENSION-AREA",
                "PASS",
                "evaluated",
                "info",
                "Positive declared dimensions produce a nominal opening area; net glass remains unknown.",
                (identifier,),
                {
                    "family": family,
                    "width_m": measurement["width_m"],
                    "height_m": measurement["height_m"],
                    "length_m": measurement["length_m"],
                    "area_m2": measurement["area_m2"],
                    "perimeter_m": measurement["perimeter_m"],
                    "net_glass_area_m2": None,
                    "formula": "length_m * width_m" if is_rooflight else "width_m * height_m",
                },
            )
        else:
            reason = (
                "Rooflight length and width are required; height is not substituted for either dimension."
                if is_rooflight
                else "Positive width and height are required; a missing door height remains pending."
            )
            emit(
                "OPENING-DIMENSION-AREA",
                "OPEN",
                "unsupported",
                "warning",
                reason,
                (identifier,),
                {
                    "width_m": measurement["width_m"],
                    "height_m": measurement["height_m"],
                    "length_m": measurement["length_m"],
                    "area_m2": None,
                },
            )

        if assembly is None:
            emit(
                "OPENING-QUANTITY-FAMILY",
                "OPEN",
                "unsupported",
                "warning",
                "No explicit quantity assembly is mapped for this active opening family.",
                (identifier,),
                {"family": family, "source_model": _source_path(entity)},
            )
        else:
            emit(
                "OPENING-QUANTITY-FAMILY",
                "PASS",
                "evaluated",
                "info",
                "The declared opening family maps to an explicit model-derived quantity assembly.",
                (identifier,),
                {"family": family, "assembly_id": assembly},
            )

        # Preserve measured but unmapped records for review; only mapped records
        # enter totals consumed by the existing cost-reconciliation interface.
        if dimensions_known:
            area_record = {
                "id": f"Q-{identifier}-AREA",
                "assembly_id": assembly,
                "description": f"{identifier} nominal opening area (not net glass)",
                "quantity": measurement["area_m2"],
                "unit": "m2",
                **_source_provenance(entity),
                "formula": "length_m * width_m" if is_rooflight else "width_m * height_m",
                "measurement_status": "model-derived nominal opening area; not procurement quantity",
                "net_glass_area_m2": None,
            }
            quantity_records.append(area_record)
            if assembly is not None:
                quantity_totals.setdefault(assembly, {})
                quantity_totals[assembly]["m2"] = round(
                    quantity_totals[assembly].get("m2", 0.0) + float(measurement["area_m2"]), 3
                )

            if is_rooflight and measurement["perimeter_m"] is not None:
                curb_record = {
                    "id": f"Q-{identifier}-CURB",
                    "assembly_id": "ROOFLIGHT-CURB",
                    "description": f"{identifier} curb perimeter",
                    "quantity": measurement["perimeter_m"],
                    "unit": "m",
                    **_source_provenance(entity),
                    "formula": "2 * (length_m + width_m)",
                    "measurement_status": "model-derived schematic curb perimeter",
                }
                quantity_records.append(curb_record)
                quantity_totals.setdefault("ROOFLIGHT-CURB", {})
                quantity_totals["ROOFLIGHT-CURB"]["m"] = round(
                    quantity_totals["ROOFLIGHT-CURB"].get("m", 0.0)
                    + float(measurement["perimeter_m"]),
                    3,
                )

    # Check each active opening against the host explicitly named by the model.
    for identifier in sorted(opening_entities):
        opening = opening_entities[identifier]
        if not _is_active(opening):
            continue
        relationships = opening.get("relationships")
        host_id = relationships.get("host_id") if isinstance(relationships, dict) else None
        if not host_id:
            emit(
                "OPENING-IN-HOST-EXTENT",
                "OPEN",
                "unsupported",
                "warning",
                "No host_id is available for the opening extent check.",
                (identifier,),
                {"reason": "Missing relationships.host_id."},
            )
            continue
        host = entities.get(str(host_id))
        if host is None:
            emit(
                "OPENING-IN-HOST-EXTENT",
                "OPEN",
                "unsupported",
                "warning",
                "The declared host entity is unavailable in this snapshot.",
                (identifier, str(host_id)),
                {"host_id": str(host_id)},
            )
            continue
        coverage, result, evidence = _host_extent_result(opening, host)
        message = (
            "Opening bounds fit within the declared host extent."
            if result == "PASS"
            else "Opening bounds extend beyond the declared host extent."
            if result == "FAIL"
            else "Host or opening bounds are incomplete, so containment remains unresolved."
        )
        emit(
            "OPENING-IN-HOST-EXTENT",
            result,
            coverage,
            "error" if result == "FAIL" else "info" if result == "PASS" else "warning",
            message,
            (identifier, str(host_id)),
            evidence,
        )

    # Check room-linked vertical windows against every declared room boundary
    # in plan. This remains independent of opening sill/head heights.
    for identifier in sorted(opening_entities):
        opening = opening_entities[identifier]
        if (
            not _is_active(opening)
            or opening.get("kind") != "opening"
            or opening.get("family") == _ROOFLIGHT_FAMILY
        ):
            continue
        relationships = opening.get("relationships")
        space_ids = relationships.get("space_ids") if isinstance(relationships, dict) else None
        if not isinstance(space_ids, list) or not space_ids:
            continue
        for raw_space_id in space_ids:
            if raw_space_id is None or not str(raw_space_id):
                emit(
                    "OPENING-IN-SPACE-BOUNDARY",
                    "OPEN",
                    "unsupported",
                    "warning",
                    "A declared space reference is empty, so the room-boundary check is unresolved.",
                    (identifier,),
                    {"reason": "relationships.space_ids contains an empty reference."},
                )
                continue
            space_id = str(raw_space_id)
            space = entities.get(space_id)
            if space is None:
                emit(
                    "OPENING-IN-SPACE-BOUNDARY",
                    "OPEN",
                    "unsupported",
                    "warning",
                    "The declared space entity is unavailable in this snapshot.",
                    (identifier, space_id),
                    {"space_id": space_id, "reason": "Missing declared space entity."},
                )
                continue
            coverage, result, evidence = _space_boundary_result(opening, space)
            message = (
                "Opening lies on and within the declared room boundary."
                if result == "PASS"
                else "Opening lies outside the declared room boundary or does not lie on its edge."
                if result == "FAIL"
                else "Opening or room plan bounds are incomplete, so room containment remains unresolved."
            )
            emit(
                "OPENING-IN-SPACE-BOUNDARY",
                result,
                coverage,
                "error" if result == "FAIL" else "info" if result == "PASS" else "warning",
                message,
                (identifier, space_id),
                evidence,
            )

    # Rooflight footprints are checked directly against the declared hall plan
    # envelope, including study entities whose proposed geometry is exploratory.
    geometry = snapshot.get("geometry")
    hall = geometry.get("hall") if isinstance(geometry, dict) else None
    for identifier, rooflight in sorted(entities.items()):
        if rooflight.get("family") != _ROOFLIGHT_FAMILY or _entity_status(rooflight) not in {
            "active",
            "study",
        }:
            continue
        coverage, result, evidence = _rooflight_hall_result(rooflight, hall)
        message = (
            "Rooflight footprint fits within the hall plan extent."
            if result == "PASS"
            else "Rooflight footprint extends beyond the hall plan extent."
            if result == "FAIL"
            else "Rooflight or hall plan bounds are incomplete, so containment remains unresolved."
        )
        emit(
            "ROOFLIGHT-IN-HALL-EXTENT",
            result,
            coverage,
            "error" if result == "FAIL" else "info" if result == "PASS" else "warning",
            message,
            (identifier,),
            evidence,
        )

    # Reservations are schematic plan envelopes, not members. Report positive
    # XY intersections as unresolved coordination candidates without asserting a
    # three-dimensional clash or clearance result.
    for reservation_id, reservation in sorted(entities.items()):
        if reservation.get("kind") != "reservation" or _entity_status(reservation) not in {
            "active",
            "context",
        }:
            continue
        for opening_id, opening in sorted(entities.items()):
            if (
                not _is_active(opening)
                or opening.get("kind") not in _OPENING_KINDS
                or opening.get("family") == _ROOFLIGHT_FAMILY
            ):
                continue
            overlaps, evidence = _reservation_opening_plan_result(reservation, opening)
            if overlaps is not True:
                continue
            emit(
                "RESERVATION-OPENING-PLAN",
                "OPEN",
                "evaluated",
                "warning",
                "Opening and reservation overlap in plan; vertical coordination remains unresolved.",
                (reservation_id, opening_id),
                evidence,
            )

    # Compare active hosted pairs. The host itself is an intentional relation and
    # is never passed to this overlap test as a collision candidate.
    host_groups: dict[str, list[str]] = defaultdict(list)
    for identifier, entity in entities.items():
        if not _is_active(entity) or entity.get("kind") not in _PHYSICAL_KINDS:
            continue
        relationships = entity.get("relationships")
        host_id = relationships.get("host_id") if isinstance(relationships, dict) else None
        if host_id:
            host_groups[str(host_id)].append(identifier)

    for host_id in sorted(host_groups):
        hosted_ids = sorted(set(host_groups[host_id]))
        for first_id, second_id in combinations(hosted_ids, 2):
            first, second = entities[first_id], entities[second_id]
            # Column/opening pairs receive the more explicit vertical check below.
            kinds = {first.get("kind"), second.get("kind")}
            if "column" in kinds and kinds.intersection(_OPENING_KINDS):
                continue
            if first.get("kind") in _OPENING_KINDS and second.get("kind") in _OPENING_KINDS:
                first_region = _facade_region(first)
                second_region = _facade_region(second)
                if first_region is not None and second_region is not None:
                    overlaps, intersection = _regions_overlap(first_region, second_region)
                    emit(
                        "SAME-HOST-OVERLAP",
                        "FAIL" if overlaps else "PASS",
                        "evaluated",
                        "error" if overlaps else "info",
                        "Hosted openings overlap with positive width and height."
                        if overlaps
                        else "Hosted openings are separate or only touch at a boundary.",
                        (first_id, second_id),
                        {
                            "host_id": host_id,
                            "coordinate_basis": "facade start and vertical bounds",
                            "intersection_width_m": round(intersection[0], 6),
                            "intersection_height_m": round(intersection[1], 6),
                            "tolerance_m": TOLERANCE_M,
                        },
                    )
                    continue

            first_bounds = _box_bounds(first)
            second_bounds = _box_bounds(second)
            if first_bounds is None or second_bounds is None:
                emit(
                    "SAME-HOST-OVERLAP",
                    "OPEN",
                    "unsupported",
                    "warning",
                    "Hosted element bounds are incomplete or use unsupported geometry.",
                    (first_id, second_id),
                    {"host_id": host_id, "required_geometry": "compatible x/y/z bounds"},
                )
                continue
            overlaps, intersections = _bounds_overlap(first_bounds, second_bounds)
            emit(
                "SAME-HOST-OVERLAP",
                "FAIL" if overlaps else "PASS",
                "evaluated",
                "error" if overlaps else "info",
                "Hosted elements overlap with positive volume."
                if overlaps
                else "Hosted elements are separate or touch only at a boundary.",
                (first_id, second_id),
                {
                    "host_id": host_id,
                    "intersection_xyz_m": [round(value, 6) for value in intersections],
                    "tolerance_m": TOLERANCE_M,
                },
            )

    # Plan overlap alone is not a clash. Both the column box and the opening
    # elevation must be known before a pair can pass or fail this rule.
    active_columns = {
        identifier: item
        for identifier, item in entities.items()
        if _is_active(item) and item.get("kind") == "column"
    }
    active_openings = {
        identifier: item
        for identifier, item in opening_entities.items()
        if _is_active(item) and item.get("family") != _ROOFLIGHT_FAMILY
    }
    for column_id in sorted(active_columns):
        column = active_columns[column_id]
        column_bounds = _box_bounds(column, require_box=True)
        for opening_id in sorted(active_openings):
            opening = active_openings[opening_id]
            opening_bounds = _box_bounds(opening)
            if column_bounds is None or opening_bounds is None:
                emit(
                    "COLUMN-OPENING-INTERFERENCE",
                    "OPEN",
                    "unsupported",
                    "warning",
                    "Column/opening interference cannot be resolved without known box coordinates and height.",
                    (column_id, opening_id),
                    {
                        "column_shape": (column.get("geometry") or {}).get("shape")
                        if isinstance(column.get("geometry"), dict)
                        else None,
                        "column_bounds_known": column_bounds is not None,
                        "opening_bounds_known": opening_bounds is not None,
                    },
                )
                continue
            overlaps, intersections = _column_opening_overlap(column_bounds, opening_bounds)
            emit(
                "COLUMN-OPENING-INTERFERENCE",
                "FAIL" if overlaps else "PASS",
                "evaluated",
                "error" if overlaps else "info",
                "Column box and opening overlap in plan and height."
                if overlaps
                else "Known column box and opening bounds do not have positive-volume overlap.",
                (column_id, opening_id),
                {
                    "column_bounds_xyz": list(column_bounds),
                    "opening_bounds_xyz": list(opening_bounds),
                    "intersection_xyz_m": [round(value, 6) for value in intersections],
                    "tolerance_m": TOLERANCE_M,
                    "authority": "schematic geometry check; no structural capacity calculation",
                },
            )

    # Reservations remain visible even when they are context-only plan rectangles.
    # They are not promoted to columns and missing vertical bounds stay OPEN.
    for identifier, entity in sorted(entities.items()):
        if entity.get("kind") != "reservation" or _entity_status(entity) == "study":
            continue
        bounds = _box_bounds(entity, require_box=True)
        plan_bounds = _xy_bounds(entity)
        if bounds is None:
            emit(
                "RESERVATION-EXTENT-COVERAGE",
                "OPEN",
                "unsupported",
                "warning",
                "Plan-only reservation has no supported 3D solid extent; clearance cannot be certified.",
                (identifier,),
                {
                    "status": _entity_status(entity),
                    "plan_bounds_xy": list(plan_bounds) if plan_bounds else None,
                    "geometry_shape": (entity.get("geometry") or {}).get("shape")
                    if isinstance(entity.get("geometry"), dict)
                    else None,
                    "reason": "Reservation vertical extent is unknown or geometry is not a box.",
                },
            )
        else:
            emit(
                "RESERVATION-EXTENT-COVERAGE",
                "OPEN",
                "evaluated",
                "warning",
                "Reservation bounds are available, but a reservation is not a structural member or clearance approval.",
                (identifier,),
                {
                    "status": _entity_status(entity),
                    "bounds_xyz": list(bounds),
                    "reason": "Member design and clearance review remain open.",
                },
            )

    for identifier, entity in sorted(entities.items()):
        geometry_data = entity.get("geometry")
        if (
            _entity_status(entity) not in {"active", "context"}
            or not isinstance(geometry_data, dict)
            or geometry_data.get("shape") != "unresolved"
        ):
            continue
        parameters = entity.get("parameters")
        reason = parameters.get("reason") if isinstance(parameters, dict) else None
        emit(
            "ENTITY-GEOMETRY-CAPABILITY",
            "OPEN",
            "unsupported",
            "warning",
            "Entity geometry is explicitly unresolved; geometry-based coordination remains open.",
            (identifier,),
            {
                "kind": entity.get("kind"),
                "status": _entity_status(entity),
                "geometry_shape": "unresolved",
                "reason": reason,
                **_source_provenance(entity),
            },
        )

    # These gates make the boundary of automated geometry checks explicit.
    for identifier, entity in sorted(entities.items()):
        if _entity_status(entity) not in {"active", "context"}:
            continue
        kind = entity.get("kind")
        if kind not in {"opening", "door", "column", "wall", "stair"}:
            continue
        aliases = entity.get("aliases") if isinstance(entity.get("aliases"), list) else []
        identity_text = " ".join([identifier, *(str(alias) for alias in aliases)]).upper()
        governance_refs: list[str] = []
        parameters = entity.get("parameters")
        declared_door_opening = (
            isinstance(parameters, dict) and parameters.get("door_kind") == "opening"
        )
        if (kind == "opening" and entity.get("family") != _ROOFLIGHT_FAMILY) or (
            kind == "door" and declared_door_opening
        ):
            governance_refs.append("CF-009")
        if kind == "column":
            governance_refs.append("CF-009")
        if kind == "column" and ("STAIR" in identity_text or "EDGE" in identity_text):
            governance_refs.append("CF-010")
        if kind == "wall" and entity.get("level") == "P2":
            governance_refs.append("CF-009")
        if kind == "wall" and entity.get("level") == "P2" and "FRONT" in identity_text:
            governance_refs.append("CF-010")
        if kind == "door" and (
            entity.get("family") == "PB.exterior_doors" or "PB-DOOR-ESC" in identity_text
        ):
            governance_refs.append("CF-011")
        if kind == "stair":
            governance_refs.append("CF-011")
        if "EGRESS" in identity_text or "RESCUE" in identity_text:
            governance_refs.append("CF-012")
        if governance_refs:
            emit(
                "PROFESSIONAL-DESIGN-GATE",
                "OPEN",
                "evaluated",
                "warning",
                "Schematic rules do not replace the applicable professional design and review gates.",
                (identifier,),
                {
                    "governance_refs": sorted(set(governance_refs)),
                    "not_performed": [
                        "signed structural design",
                        "fire and egress design",
                        "glazing and fall-protection design",
                        "building-physics design",
                    ],
                },
            )

    # Rules without candidates are counted as inapplicable, not silently passed.
    for rule_id, row in coverage_rows.items():
        if not any(row["counts"].values()):
            row["counts"]["inapplicable"] = 1

    coverage_rules = []
    coverage_totals = {state: 0 for state in _COVERAGE_STATES}
    registry_by_id = {item["rule_id"]: item for item in RULE_REGISTRY}
    for rule_id in sorted(_RULE_IDS):
        row = coverage_rows[rule_id]
        for state in _COVERAGE_STATES:
            coverage_totals[state] += row["counts"][state]
        coverage_rules.append(
            {
                **registry_by_id[rule_id],
                "counts": dict(row["counts"]),
                "entity_ids_by_coverage": {
                    state: sorted(row["entity_ids"][state]) for state in _COVERAGE_STATES
                },
            }
        )

    findings.sort(key=lambda item: (item["rule_id"], item["finding_id"]))
    schedule_items.sort(key=lambda item: item["id"])
    study_items.sort(key=lambda item: item["id"])
    quantity_records.sort(key=lambda item: item["id"])
    quantity_ledger = {
        "revision": "coordination-quantity-ledger-v1",
        "status": "model-derived schematic quantities; not procurement authority",
        "coverage": {
            "scope": "opening-only nominal quantities",
            "included": [
                "active openings whose family has an explicit assembly mapping",
                "rooflight curb perimeter when length and width are known",
            ],
            "excluded": [
                "study-status and context entities",
                "unmapped door and opening families from assembly totals",
                "gross-floor-area and programme-area metrics from the legacy ledger",
                "net glass, operable area, deductions, and non-opening construction quantities",
            ],
            "not_a_full_takeoff": True,
        },
        "records": quantity_records,
        "totals_by_assembly": quantity_totals,
        "approved_budget_total_cop": None,
        "note": "Nominal opening areas are not net glass; no rate or budget approval is implied.",
    }
    return {
        "findings": findings,
        "coverage": {"totals": coverage_totals, "rules": coverage_rules},
        "rule_registry": [dict(item) for item in RULE_REGISTRY],
        "opening_schedule": {
            "revision": "coordination-opening-schedule-v1",
            "status": "derived schematic measurements; not procurement authority",
            "items": schedule_items,
            "study_items_excluded_from_totals": study_items,
        },
        "quantity_ledger": quantity_ledger,
    }


def _snapshot_changes(current: dict[str, Any], baseline: dict[str, Any] | None) -> dict[str, Any]:
    if baseline is None:
        return {"baseline_scenario_id": None, "added": [], "removed": [], "modified": []}

    current_entities = _entities(current)
    baseline_entities = _entities(baseline)
    current_ids, baseline_ids = set(current_entities), set(baseline_entities)
    modified = []
    compared_fields = ("kind", "status", "family", "geometry", "parameters", "relationships")
    for identifier in sorted(current_ids & baseline_ids):
        before, after = baseline_entities[identifier], current_entities[identifier]
        deltas = []
        for field in compared_fields:
            before_value = before.get(field)
            after_value = after.get(field)
            if before_value == after_value:
                continue
            if isinstance(before_value, dict) or isinstance(after_value, dict):
                before_map = before_value if isinstance(before_value, dict) else {}
                after_map = after_value if isinstance(after_value, dict) else {}
                nested_keys = sorted(set(before_map) | set(after_map))
                for key in nested_keys:
                    if before_map.get(key) != after_map.get(key):
                        deltas.append(
                            {
                                "path": f"{field}.{key}",
                                "before": before_map.get(key),
                                "after": after_map.get(key),
                            }
                        )
            else:
                deltas.append({"path": field, "before": before_value, "after": after_value})
        if deltas:
            modified.append({"entity_id": identifier, "deltas": deltas})

    return {
        "baseline_scenario_id": baseline.get("scenario_id", current.get("scenario_id")),
        "added": sorted(current_ids - baseline_ids),
        "removed": sorted(baseline_ids - current_ids),
        "modified": modified,
    }


def _lifecycle_absence_state(
    previous: dict[str, Any], current_entities: dict[str, dict[str, Any]]
) -> str:
    entity_ids = previous["entity_ids"]
    if any(identifier not in current_entities for identifier in entity_ids):
        return "removed"

    entities = [current_entities[identifier] for identifier in entity_ids]
    rule_id = previous["rule_id"]
    if rule_id in {"OPENING-DIMENSION-AREA", "OPENING-QUANTITY-FAMILY"}:
        applicable = (
            len(entities) == 1
            and _is_active(entities[0])
            and entities[0].get("kind") in _OPENING_KINDS
        )
    elif rule_id == "OPENING-IN-HOST-EXTENT":
        if len(entities) != 2:
            applicable = False
        else:
            opening = next((item for item in entities if item.get("kind") in _OPENING_KINDS), None)
            host = next((item for item in entities if item.get("kind") not in _OPENING_KINDS), None)
            relationships = opening.get("relationships") if isinstance(opening, dict) else None
            host_id = relationships.get("host_id") if isinstance(relationships, dict) else None
            applicable = bool(
                opening and host and _is_active(opening) and host_id == host.get("id")
            )
    elif rule_id == "OPENING-IN-SPACE-BOUNDARY":
        if len(entities) != 2:
            applicable = False
        else:
            opening = next((item for item in entities if item.get("kind") == "opening"), None)
            space = next((item for item in entities if item.get("kind") == "space"), None)
            relationships = opening.get("relationships") if isinstance(opening, dict) else None
            space_ids = relationships.get("space_ids") if isinstance(relationships, dict) else None
            applicable = bool(
                opening
                and space
                and _is_active(opening)
                and opening.get("family") != _ROOFLIGHT_FAMILY
                and isinstance(space_ids, list)
                and space.get("id") in {str(item) for item in space_ids}
            )
    elif rule_id == "ROOFLIGHT-IN-HALL-EXTENT":
        applicable = (
            len(entities) == 1
            and entities[0].get("family") == _ROOFLIGHT_FAMILY
            and _entity_status(entities[0]) in {"active", "study"}
        )
    elif rule_id == "RESERVATION-OPENING-PLAN":
        if len(entities) != 2:
            applicable = False
        else:
            reservation = next(
                (item for item in entities if item.get("kind") == "reservation"), None
            )
            opening = next((item for item in entities if item.get("kind") in _OPENING_KINDS), None)
            if (
                reservation is None
                or opening is None
                or _entity_status(reservation) not in {"active", "context"}
                or not _is_active(opening)
                or opening.get("family") == _ROOFLIGHT_FAMILY
            ):
                applicable = False
            else:
                overlaps, _ = _reservation_opening_plan_result(reservation, opening)
                applicable = overlaps is not False
    elif rule_id == "SAME-HOST-OVERLAP":
        if len(entities) != 2 or not all(
            _is_active(item) and item.get("kind") in _PHYSICAL_KINDS for item in entities
        ):
            applicable = False
        else:
            host_ids = []
            for entity in entities:
                relationships = entity.get("relationships")
                host_ids.append(
                    relationships.get("host_id") if isinstance(relationships, dict) else None
                )
            applicable = bool(host_ids[0] and host_ids[0] == host_ids[1])
    elif rule_id == "COLUMN-OPENING-INTERFERENCE":
        applicable = (
            len(entities) == 2
            and any(_is_active(item) and item.get("kind") == "column" for item in entities)
            and any(
                _is_active(item)
                and item.get("kind") in _OPENING_KINDS
                and item.get("family") != _ROOFLIGHT_FAMILY
                for item in entities
            )
        )
    elif rule_id == "RESERVATION-EXTENT-COVERAGE":
        applicable = (
            len(entities) == 1
            and entities[0].get("kind") == "reservation"
            and _entity_status(entities[0]) != "study"
        )
    elif rule_id == "PROFESSIONAL-DESIGN-GATE":
        applicable = (
            len(entities) == 1
            and _entity_status(entities[0]) in {"active", "context"}
            and entities[0].get("kind") in {"opening", "door", "column", "wall", "stair"}
        )
    elif rule_id == "ENTITY-GEOMETRY-CAPABILITY":
        applicable = (
            len(entities) == 1
            and _entity_status(entities[0]) in {"active", "context"}
            and isinstance(entities[0].get("geometry"), dict)
            and entities[0]["geometry"].get("shape") == "unresolved"
        )
    else:
        applicable = False
    return "unevaluated" if applicable else "inapplicable"


def _finding_lifecycle(
    current_findings: list[dict[str, Any]],
    baseline_findings: list[dict[str, Any]],
    current_entities: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    current_by_id = {item["finding_id"]: item for item in current_findings}
    baseline_by_id = {item["finding_id"]: item for item in baseline_findings}
    lifecycle = []

    for finding_id, current in current_by_id.items():
        if current["status"] == "PASS":
            continue
        previous = baseline_by_id.get(finding_id)
        state = "new" if previous is None or previous["status"] == "PASS" else "persisting"
        lifecycle.append(
            {
                "finding_id": finding_id,
                "rule_id": current["rule_id"],
                "state": state,
                "before_status": previous["status"] if previous else None,
                "after_status": current["status"],
                "entity_ids": current["entity_ids"],
                "before_evidence": previous["evidence"] if previous else None,
                "after_evidence": current["evidence"],
            }
        )

    for finding_id, previous in baseline_by_id.items():
        if previous["status"] == "PASS":
            continue
        current = current_by_id.get(finding_id)
        if current is not None and current["status"] == "PASS":
            lifecycle.append(
                {
                    "finding_id": finding_id,
                    "rule_id": previous["rule_id"],
                    "state": "resolved",
                    "before_status": previous["status"],
                    "after_status": current["status"],
                    "entity_ids": previous["entity_ids"],
                    "before_evidence": previous["evidence"],
                    "after_evidence": current["evidence"],
                }
            )
        elif current is None:
            lifecycle.append(
                {
                    "finding_id": finding_id,
                    "rule_id": previous["rule_id"],
                    "state": _lifecycle_absence_state(previous, current_entities),
                    "before_status": previous["status"],
                    "after_status": None,
                    "entity_ids": previous["entity_ids"],
                    "before_evidence": previous["evidence"],
                    "after_evidence": None,
                }
            )
    lifecycle.sort(key=lambda item: (item["rule_id"], item["finding_id"], item["state"]))
    return {"items": lifecycle}


def evaluate(snapshot: dict[str, Any], baseline: dict[str, Any] | None = None) -> dict[str, Any]:
    """Evaluate one resolved snapshot and optionally compare findings to a baseline.

    No source file is read and no dimensional geometry is inferred when the
    snapshot leaves it unknown. ``baseline`` is evaluated once internally, without
    recursively invoking this public function.
    """

    result = _evaluate_snapshot(snapshot)
    result["changes"] = _snapshot_changes(snapshot, baseline)
    if baseline is None:
        result["finding_lifecycle"] = {"baseline_scenario_id": None, "items": []}
    else:
        baseline_result = _evaluate_snapshot(baseline)
        lifecycle = _finding_lifecycle(
            result["findings"], baseline_result["findings"], _entities(snapshot)
        )
        result["finding_lifecycle"] = {
            "baseline_scenario_id": baseline.get("scenario_id", snapshot.get("scenario_id")),
            **lifecycle,
        }
    return result


__all__ = ["RULE_REGISTRY", "evaluate"]

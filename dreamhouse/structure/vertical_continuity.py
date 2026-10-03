"""Geometry audit for continuous columns and a stair-enclosure steel frame.

This module does not size a lateral system.  It identifies column lines that can
continue from foundation to roof without silently crossing active rooms, doors,
or full-height glazing.  It also separates the stair enclosure frame from the
stair flights: the latter must either accommodate drift or be explicitly included
in the structural model and detailed for the resulting actions.
"""

from __future__ import annotations

import math
from typing import Any


class VerticalContinuityError(ValueError):
    """The architectural inputs cannot support a deterministic continuity audit."""


def _finite(value: object, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise VerticalContinuityError(f"{label} must be finite")
    return number


def _interval_contains(value: float, start: float, end: float, tolerance: float) -> bool:
    return start - tolerance <= value <= end + tolerance


def _point_relation_to_space(
    x: float,
    y: float,
    space: dict[str, Any],
    tolerance: float,
) -> str | None:
    x0 = _finite(space["x"], f"{space['id']} x")
    y0 = _finite(space["y"], f"{space['id']} y")
    x1 = x0 + _finite(space["w"], f"{space['id']} width")
    y1 = y0 + _finite(space["d"], f"{space['id']} depth")
    if not (_interval_contains(x, x0, x1, tolerance) and _interval_contains(y, y0, y1, tolerance)):
        return None
    on_boundary = (
        math.isclose(x, x0, abs_tol=tolerance)
        or math.isclose(x, x1, abs_tol=tolerance)
        or math.isclose(y, y0, abs_tol=tolerance)
        or math.isclose(y, y1, abs_tol=tolerance)
    )
    return "boundary" if on_boundary else "interior"


def _window_conflicts(
    x: float,
    y: float,
    p2: dict[str, Any],
    tolerance: float,
) -> list[str]:
    conflicts: list[str] = []
    envelope = p2["envelope"]
    x_min = _finite(envelope["x"], "P2 envelope x")
    x_max = x_min + _finite(envelope["length"], "P2 envelope length")
    y_min = 0.0
    y_max = _finite(envelope["width"], "P2 envelope width")
    for window in p2.get("windows", []):
        edge = window["edge"]
        start = _finite(window["from"], f"{window['id']} from")
        end = _finite(window["to"], f"{window['id']} to")
        conflict = False
        if edge == "south":
            conflict = math.isclose(y, y_min, abs_tol=tolerance) and _interval_contains(
                x, start, end, tolerance
            )
        elif edge == "north":
            conflict = math.isclose(y, y_max, abs_tol=tolerance) and _interval_contains(
                x, start, end, tolerance
            )
        elif edge == "east":
            conflict = math.isclose(x, x_max, abs_tol=tolerance) and _interval_contains(
                y, start, end, tolerance
            )
        if conflict:
            conflicts.append(window["id"])
    return conflicts


def _door_conflicts(
    x: float,
    y: float,
    pb: dict[str, Any],
    wall_x: float,
    rear_x: float,
    tolerance: float,
) -> list[str]:
    conflicts: list[str] = []
    if math.isclose(x, wall_x, abs_tol=tolerance):
        for room in pb["core"]:
            if room.get("door_y") is None:
                continue
            start = _finite(room["door_y"], f"{room['id']} door y") - 0.10
            end = start + _finite(room["door_width"], f"{room['id']} door width")
            if _interval_contains(y, start, end, tolerance):
                conflicts.append(f"GW-{room['id']}")
    if math.isclose(x, rear_x, abs_tol=tolerance):
        for door in pb.get("exterior_doors", []):
            if door.get("y") is None:
                continue
            start = _finite(door["y"], f"{door['id']} y") - 0.50
            end = start + _finite(door["width"], f"{door['id']} width")
            if _interval_contains(y, start, end, tolerance):
                conflicts.append(door["id"])
    return conflicts


def _unresolved_door_locations(
    x: float,
    pb: dict[str, Any],
    wall_x: float,
    rear_x: float,
    tolerance: float,
) -> list[str]:
    unresolved: list[str] = []
    if math.isclose(x, wall_x, abs_tol=tolerance):
        unresolved.extend(
            f"GW-{room['id']}"
            for room in pb["core"]
            if room.get("door_y") is None
        )
    if math.isclose(x, rear_x, abs_tol=tolerance):
        unresolved.extend(
            door["id"] for door in pb.get("exterior_doors", []) if door.get("y") is None
        )
    return unresolved


def _audit_candidate(
    candidate: dict[str, Any],
    pb: dict[str, Any],
    p2: dict[str, Any],
    stair: dict[str, Any],
    wall_x: float,
    rear_x: float,
    tolerance: float,
) -> dict[str, Any]:
    x = _finite(candidate["x_m"], f"{candidate['id']} x")
    y = _finite(candidate["y_m"], f"{candidate['id']} y")
    space_relations = [
        {"space_id": space["id"], "relation": relation}
        for space in p2["spaces"]
        if (relation := _point_relation_to_space(x, y, space, tolerance)) is not None
    ]
    interior_nonstair = [
        item["space_id"]
        for item in space_relations
        if item["relation"] == "interior" and item["space_id"] != stair["id"]
    ]
    windows = _window_conflicts(x, y, p2, tolerance)
    doors = _door_conflicts(x, y, pb, wall_x, rear_x, tolerance)
    unresolved_doors = _unresolved_door_locations(x, pb, wall_x, rear_x, tolerance)
    stair_x0 = _finite(stair["x"], "stair x")
    stair_x1 = stair_x0 + _finite(stair["w"], "stair width")
    stair_y0 = _finite(stair["y"], "stair y")
    stair_y1 = stair_y0 + _finite(stair["d"], "stair depth")
    stair_corner = any(
        math.isclose(x, corner_x, abs_tol=tolerance)
        and math.isclose(y, corner_y, abs_tol=tolerance)
        for corner_x in (stair_x0, stair_x1)
        for corner_y in (stair_y0, stair_y1)
    )
    compatible = (
        stair_corner
        and not interior_nonstair
        and not windows
        and not doors
        and not unresolved_doors
    )
    reasons: list[str] = []
    if not stair_corner:
        reasons.append("not_on_stair_enclosure_corner")
    if interior_nonstair:
        reasons.append("crosses_p2_space:" + ",".join(interior_nonstair))
    if windows:
        reasons.append("interrupts_glazing:" + ",".join(windows))
    if doors:
        reasons.append("interrupts_door:" + ",".join(doors))
    if unresolved_doors:
        reasons.append("door_location_unresolved:" + ",".join(unresolved_doors))
    result = {
        "id": candidate["id"],
        "source": candidate["source"],
        "x_m": x,
        "y_m": y,
        "existing_to_p2": bool(candidate["existing_to_p2"]),
        "space_relations": space_relations,
        "interior_nonstair_spaces": interior_nonstair,
        "window_conflicts": windows,
        "door_conflicts": doors,
        "aligned_with_stair_enclosure_corner": stair_corner,
        "geometry_compatible_for_full_height_study": compatible,
        "rejection_reasons": reasons,
    }
    if unresolved_doors:
        result["unresolved_door_locations"] = unresolved_doors
    return result


def evaluate_current_support_line_plan(
    candidate: dict[str, Any],
    spaces: list[dict[str, Any]],
    openings: list[dict[str, Any]],
    *,
    stair_space_ids: set[str] | frozenset[str] = frozenset(),
    tolerance_m: float = 0.01,
    reservation_bounds: tuple[float, float, float, float] | None = None,
) -> dict[str, Any]:
    """Compare a support-line hypothesis with current room/opening plan geometry.

    This is the reusable geometric core for current-snapshot adapters. It has no
    expected candidate list and makes no vertical-clearance or capacity claim. A
    reservation bounds box is used only as a plan envelope; it is not interpreted
    as a selected column section.
    """

    def finite_number(value: object, label: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise VerticalContinuityError(f"{label} must be a finite number")
        number = float(value)
        if not math.isfinite(number):
            raise VerticalContinuityError(f"{label} must be a finite number")
        return number

    tolerance_m = finite_number(tolerance_m, "geometry tolerance")
    if tolerance_m <= 0.0:
        raise VerticalContinuityError("Geometry tolerance must be positive")
    x = finite_number(candidate["x_m"], "support line x")
    y = finite_number(candidate["y_m"], "support line y")
    if reservation_bounds is not None:
        if len(reservation_bounds) != 4:
            raise VerticalContinuityError("Reservation bounds must contain four finite values")
        rx0, rx1, ry0, ry1 = tuple(
            finite_number(item, "reservation bound") for item in reservation_bounds
        )
        if rx1 < rx0 or ry1 < ry0:
            raise VerticalContinuityError("Reservation bounds are reversed")
    else:
        rx0 = rx1 = x
        ry0 = ry1 = y

    space_relations = [
        {"space_id": space["id"], "relation": relation}
        for space in spaces
        if (relation := _point_relation_to_space(x, y, space, tolerance_m)) is not None
    ]
    interior_nonstair = [
        item["space_id"]
        for item in space_relations
        if item["relation"] == "interior" and item["space_id"] not in stair_space_ids
    ]

    plan_opening_candidates: list[dict[str, Any]] = []
    unsupported_openings: list[str] = []
    for opening in openings:
        identifier = str(opening.get("id", "unknown"))
        geometry = opening.get("geometry")
        if not isinstance(geometry, dict) or geometry.get("shape") not in {"opening", "line"}:
            unsupported_openings.append(identifier)
            continue
        raw_bounds = tuple(geometry.get(key) for key in ("x0", "x1", "y0", "y1"))
        if any(value is None for value in raw_bounds):
            unsupported_openings.append(identifier)
            continue
        bounds = tuple(finite_number(value, f"{identifier} opening bound") for value in raw_bounds)
        x0, x1, y0, y1 = bounds
        if x1 < x0 or y1 < y0:
            unsupported_openings.append(identifier)
            continue
        if reservation_bounds is None:
            intersects = (
                x0 - tolerance_m <= x <= x1 + tolerance_m
                and y0 - tolerance_m <= y <= y1 + tolerance_m
            )
        elif abs(x1 - x0) <= tolerance_m and y1 - y0 > tolerance_m:
            intersects = (
                rx0 - tolerance_m <= x0 <= rx1 + tolerance_m
                and max(ry0, y0) < min(ry1, y1) + tolerance_m
            )
        elif abs(y1 - y0) <= tolerance_m and x1 - x0 > tolerance_m:
            intersects = (
                ry0 - tolerance_m <= y0 <= ry1 + tolerance_m
                and max(rx0, x0) < min(rx1, x1) + tolerance_m
            )
        else:
            # A broad or non-line shape is not a known opening plane.
            unsupported_openings.append(identifier)
            continue
        if intersects:
            raw_z0, raw_z1 = geometry.get("z0"), geometry.get("z1")
            z0 = finite_number(raw_z0, f"{identifier} z0") if raw_z0 is not None else None
            z1 = finite_number(raw_z1, f"{identifier} z1") if raw_z1 is not None else None
            plan_opening_candidates.append(
                {
                    "opening_id": identifier,
                    "opening_vertical_bounds_m": [z0, z1],
                    "opening_vertical_bounds_known": z0 is not None and z1 is not None,
                    "candidate_vertical_bounds_known": False,
                    "three_dimensional_conflict": "not evaluated",
                }
            )

    return {
        "candidate_source_ref": candidate.get("source_ref", candidate.get("id")),
        "candidate_entity_id": candidate.get("id"),
        "x_m": x,
        "y_m": y,
        "plan_reservation_bounds_m": [rx0, rx1, ry0, ry1]
        if reservation_bounds is not None
        else None,
        "space_relations": space_relations,
        "interior_nonstair_spaces": interior_nonstair,
        "opening_plan_candidates": plan_opening_candidates,
        "unsupported_opening_ids": sorted(unsupported_openings),
        "candidate_vertical_bounds_known": False,
        "vertical_relation": "unknown: no selected structural member extent",
        "tolerance_m": tolerance_m,
        "plan_conflict_status": "candidate"
        if interior_nonstair or plan_opening_candidates
        else "no plan candidate observed",
    }


def evaluate_vertical_continuity(
    cfg: dict[str, Any],
    pb: dict[str, Any],
    p2: dict[str, Any],
    continuity: dict[str, Any],
    *,
    enforce_expected_compatible_ids: bool = True,
) -> dict[str, Any]:
    """Audit the proposed foundation-to-roof column and stair-frame geometry."""

    tolerance = _finite(continuity.get("geometry_tolerance_m", 0.01), "geometry tolerance")
    if tolerance <= 0.0:
        raise VerticalContinuityError("Geometry tolerance must be positive")
    geometry = cfg["geometry"]
    wall_x = _finite(geometry["great_wall_x_m"], "Great Wall x")
    rear_x = _finite(geometry["p2_start_x_m"], "P2 start x") + _finite(
        geometry["p2_length_m"], "P2 length"
    )
    pb_stair = next((room for room in pb["core"] if room["id"] == "ESC"), None)
    p2_stair = next((space for space in p2["spaces"] if space["id"] == "ESC"), None)
    if pb_stair is None or p2_stair is None:
        raise VerticalContinuityError("PB and P2 must each contain the ESC stair enclosure")

    alignment_checks = {
        "great_wall_matches_p2_stair_front": math.isclose(
            wall_x, _finite(p2_stair["x"], "P2 stair x"), abs_tol=tolerance
        ),
        "rear_facade_matches_p2_stair_back": math.isclose(
            rear_x,
            _finite(p2_stair["x"], "P2 stair x") + _finite(p2_stair["w"], "P2 stair width"),
            abs_tol=tolerance,
        ),
        "pb_p2_stair_y0_aligned": math.isclose(
            _finite(pb_stair["y0"], "PB stair y0"),
            _finite(p2_stair["y"], "P2 stair y"),
            abs_tol=tolerance,
        ),
        "pb_p2_stair_y1_aligned": math.isclose(
            _finite(pb_stair["y1"], "PB stair y1"),
            _finite(p2_stair["y"], "P2 stair y") + _finite(p2_stair["d"], "P2 stair depth"),
            abs_tol=tolerance,
        ),
    }
    if not all(alignment_checks.values()):
        raise VerticalContinuityError(
            "PB/P2 stair enclosure and Great Wall geometry are not aligned"
        )

    candidates = [
        _audit_candidate(
            candidate,
            pb,
            p2,
            p2_stair,
            wall_x,
            rear_x,
            tolerance,
        )
        for candidate in continuity["candidate_columns"]
    ]
    compatible = [
        candidate
        for candidate in candidates
        if candidate["geometry_compatible_for_full_height_study"]
    ]
    compatible_ids = [candidate["id"] for candidate in compatible]
    expected_ids = list(continuity["expected_compatible_column_ids"])
    if enforce_expected_compatible_ids and compatible_ids != expected_ids:
        raise VerticalContinuityError(
            f"Compatible full-height columns changed: {compatible_ids!r} != {expected_ids!r}"
        )

    y0 = _finite(p2_stair["y"], "P2 stair y")
    y1 = y0 + _finite(p2_stair["d"], "P2 stair depth")
    x0 = _finite(p2_stair["x"], "P2 stair x")
    x1 = x0 + _finite(p2_stair["w"], "P2 stair width")
    braced_planes = [
        {
            "id": "STAIR-SIDE-S",
            "resisting_direction": "X_longitudinal",
            "plane": f"Y={y0:.2f}",
            "bay_length_m": x1 - x0,
            "diagonal_bracing_geometry_possible": True,
            "opening_conflict": None,
            "architectural_and_egress_clearance_validated": False,
        },
        {
            "id": "STAIR-SIDE-N",
            "resisting_direction": "X_longitudinal",
            "plane": f"Y={y1:.2f}",
            "bay_length_m": x1 - x0,
            "diagonal_bracing_geometry_possible": True,
            "opening_conflict": None,
            "architectural_and_egress_clearance_validated": False,
        },
        {
            "id": "STAIR-FRONT",
            "resisting_direction": "Y_transverse",
            "plane": f"X={x0:.2f}",
            "bay_length_m": y1 - y0,
            "diagonal_bracing_geometry_possible": False,
            "opening_conflict": "protected_stair_portal_in_Great_Wall",
            "architectural_and_egress_clearance_validated": False,
        },
        {
            "id": "STAIR-REAR",
            "resisting_direction": "Y_transverse",
            "plane": f"X={x1:.2f}",
            "bay_length_m": y1 - y0,
            "diagonal_bracing_geometry_possible": False,
            "opening_conflict": "stair_discharge_door",
            "architectural_and_egress_clearance_validated": False,
        },
    ]
    existing_reused = sum(candidate["existing_to_p2"] for candidate in compatible)
    new_columns = len(compatible) - existing_reused
    return {
        "configuration": continuity,
        "alignment_checks": alignment_checks,
        "stair_enclosure": {
            "x0_m": x0,
            "x1_m": x1,
            "y0_m": y0,
            "y1_m": y1,
            "width_x_m": x1 - x0,
            "width_y_m": y1 - y0,
            "p2_level_m": _finite(geometry["p2_floor_level_m"], "P2 floor level"),
        },
        "candidates": candidates,
        "compatible_column_ids": compatible_ids,
        "compatible_column_count": len(compatible),
        "existing_great_wall_columns_reused": existing_reused,
        "new_rear_columns_required": new_columns,
        "braced_planes": braced_planes,
        "geometry_screen_pass": len(compatible) == 4,
        "stair_enclosure_frame_preferred_over_stair_flights_as_primary_system": True,
        "stair_stringers_in_primary_lateral_system": False,
        "stair_drift_compatible_connection_required": True,
        "landing_beams_as_column_restraints_resolved": False,
        "roof_gravity_support_role_resolved": False,
        "roof_diaphragm_collector_connection_resolved": False,
        "p2_diaphragm_collector_connection_resolved": False,
        "complete_orthogonal_lateral_system_resolved": False,
        "member_connection_base_and_foundation_design_resolved": False,
        "fire_egress_and_encasement_resolved": False,
        "overall_design_resolved": False,
    }

"""Pure, source-bounded calculations for currently captured project extensions.

This module consumes only the resolved snapshot.  It does not reopen source files,
create wall instances, select products, or promote coordination reservations into
installed or approved work.
"""

from __future__ import annotations

import math
import re
from copy import deepcopy
from itertools import combinations
from typing import Any

_COVERAGE_STATES = ("evaluated", "unsupported", "inapplicable", "not_run")
_TOL = 1e-8

_RULE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "WALL-EXTERIOR-LINE-SCHEDULE": {
        "description": "Measure the scheduled P2 exterior plan lines and deduct the union of current registered opening spans.",
        "required_data": [
            "P2 exterior assembly edge scope and bounds",
            "every scheduled P2 exterior opening registered with current resolved geometry",
            "opening intervals within their scheduled wall edge",
            "non-overlapping current opening geometry",
        ],
        "limits": [
            "Results are plan-line measurements; they are not wall instances, wall areas, material volumes, or mass quantities.",
            "Wall height, selected assembly and verified mass per area remain unknown.",
        ],
    },
    "WALL-HALL-EDGE-PHASE-LENGTHS": {
        "description": "Measure the retained P2-W04R bedroom-edge spans and the explicitly open family frontage.",
        "required_data": [
            "P2 hall-edge partition source extents and explicit open-frontage limits",
            "current P2 bedroom-space bounds at the retained edge",
        ],
        "limits": [
            "A plan length does not verify guard performance, fire/smoke, acoustic, structural, or temporary-works design.",
        ],
    },
    "WALL-W01A-DRY-BOUNDARY-REMAINDER": {
        "description": "Measure current same-suite dry room-boundary candidates compatible with the P2-W01A use rule and their registered opening spans.",
        "required_data": [
            "current P2 rectangular space bounds, suite tags, and space-kind tags",
            "P2-W01A same-suite dry-boundary use rule",
            "current normalized door geometry and space relationships",
        ],
        "limits": [
            "These are rule-compatible boundary candidates, not registered or selected wall instances.",
            "Wall height, finish, assembly selection, service interruptions, area, volume, and mass are not calculated.",
        ],
    },
    "SC01-CROSS-LEVEL-DATUMS": {
        "description": "Reconcile the captured PB, intermediate landing and P2 stair levels with flight rise and run arithmetic.",
        "required_data": [
            "SC-01 PB, landing and P2 levels",
            "flight riser and tread counts, going, and flight/landing vertical bounds",
            "current normalized D-STAIR geometry and opening relationship",
        ],
        "limits": [
            "Arithmetic consistency does not verify headroom, egress compliance, fire strategy, stair solids, or construction dimensions.",
        ],
    },
    "SC01-REAR-DISCHARGE-RELATIONSHIP": {
        "description": "Expose the captured PB rear-door datum against the current SC-01 intermediate landing datum.",
        "required_data": [
            "resolved EXT-ESC plan and vertical geometry",
            "sectioned and professionally reviewed rear discharge alternative",
            "resolution of CF-011 and CF-013",
        ],
        "limits": [
            "The current EXT-ESC anchor is unresolved; a scalar source reference is not a resolved discharge or exit.",
        ],
    },
    "SC01-STRUCTURAL-INTERFACE-COVERAGE": {
        "description": "Record the live SC-01 structural interfaces that have no selected members or verified connections.",
        "required_data": [
            "selected frame/member sections and current reactions",
            "landing-beam restraints, connections, bases and foundations",
            "verified flight, landing, door and headroom clearances",
            "responsible structural and life-safety review",
        ],
        "limits": [
            "Captured column reservations are plan hypotheses, not structural members or a capacity check.",
        ],
    },
    "P2-PHASE-RESERVATION-COVERAGE": {
        "description": "Sum source-tagged P2 plan areas and expose the phase-boundary, temporary closure and guard reservations.",
        "required_data": [
            "current P2 room bounds and phase tags",
            "source phase-boundary coordinate and temporary-closure rule",
            "source family-frontage and guard extents",
            "temporary-works and phase acceptance records",
        ],
        "limits": [
            "Area sums are tagged rectangular plan areas, not surveyed or certified net/gross areas.",
            "A closure/guard reservation is not evidence that temporary works have been installed or approved.",
        ],
    },
    "PB-SERVICE-OPERATING-RESERVATIONS": {
        "description": "Measure source-defined PB workbench operating strips and support-equipment separation against the current PB coordination reservations.",
        "required_data": [
            "current source bench and operating-strip bounds",
            "current support-equipment reservation bounds",
            "structured minimum-clearance value where the source states a numerical target",
        ],
        "limits": [
            "These measurements do not select, install, anchor, or structurally verify benches or equipment.",
        ],
    },
    "PB-SERVICE-ROUTE-COVERAGE": {
        "description": "Capture actual PB kitchen/service strategies and state the route, point, capacity and maintenance evidence that is absent.",
        "required_data": [
            "coordinated route centerlines and endpoints for water, drainage, extraction, power and data",
            "equipment/fixture connection points, capacities and isolation/access details",
            "selected products and responsible engineering review",
        ],
        "limits": [
            "A narrative service strategy is not a routed, sized, coordinated or approved services design.",
        ],
    },
    "ASSET-MAINTENANCE-RECORD-COVERAGE": {
        "description": "Keep source-specified equipment/rooflight reservations and their lifecycle/maintenance evidence states explicit.",
        "required_data": [
            "selected manufacturer, model, serial and installed product data",
            "installation, testing and commissioning records",
            "warranty, manuals, safe access and replacement method",
            "maintenance tasks, intervals, accountable owner and completed inspection records",
        ],
        "limits": [
            "Source reservations and coordination hypotheses do not establish physical installation or completed lifecycle events.",
        ],
    },
}


def _entities(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = snapshot.get("entities")
    if not isinstance(raw, dict):
        return {}
    return {
        str(value.get("id", key)): value for key, value in raw.items() if isinstance(value, dict)
    }


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _same_number(first: object, second: object) -> bool:
    a, b = _number(first), _number(second)
    return a is not None and b is not None and math.isclose(a, b, abs_tol=_TOL)


def _coverage_record(
    rows: dict[str, dict[str, Any]], rule_id: str, state: str, entity_ids: tuple[str, ...]
) -> None:
    if state not in _COVERAGE_STATES:
        raise ValueError(f"Unknown coverage state {state!r}")
    row = rows.setdefault(
        rule_id,
        {
            "counts": {item: 0 for item in _COVERAGE_STATES},
            "entity_ids": {item: set() for item in _COVERAGE_STATES},
        },
    )
    row["counts"][state] += 1
    row["entity_ids"][state].update(entity_ids)


def _finding_id(rule_id: str, entity_ids: tuple[str, ...]) -> str:
    suffix = ":".join(sorted(set(entity_ids))) or "PROJECT"
    return f"{rule_id}:{suffix}"


def _emit(
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
    snapshot: dict[str, Any],
    rule_id: str,
    status: str,
    coverage: str,
    message: str,
    entity_ids: tuple[str, ...] = (),
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entities = _entities(snapshot)
    normalized_ids = tuple(
        sorted({identifier for identifier in entity_ids if identifier in entities})
    )
    finding = {
        "finding_id": _finding_id(rule_id, normalized_ids),
        "rule_id": rule_id,
        "status": status,
        "coverage": coverage,
        "severity": "coordination",
        "message": message,
        "entity_ids": list(normalized_ids),
        "evidence": evidence or {},
        "scenario_id": snapshot.get("scenario_id"),
        "input_hash": snapshot.get("input_hash"),
        "model_hash": snapshot.get("model_hash"),
    }
    findings.append(finding)
    _coverage_record(coverage_rows, rule_id, coverage, normalized_ids)
    return finding


def _merge_intervals(
    intervals: list[tuple[float, float]],
) -> tuple[list[list[float]], float, float]:
    """Return union intervals, union length, and overlap length (not double-counted)."""
    ordered = sorted(intervals)
    if not ordered:
        return [], 0.0, 0.0
    merged: list[list[float]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1] + _TOL:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    raw_length = sum(end - start for start, end in ordered)
    union_length = sum(end - start for start, end in merged)
    return merged, union_length, max(0.0, raw_length - union_length)


def _p2_source(snapshot: dict[str, Any]) -> dict[str, Any] | None:
    inputs = snapshot.get("discipline_inputs")
    programme = inputs.get("programme") if isinstance(inputs, dict) else None
    p2 = programme.get("p2") if isinstance(programme, dict) else None
    return p2 if isinstance(p2, dict) else None


def _structure_sources(snapshot: dict[str, Any]) -> dict[str, Any]:
    inputs = snapshot.get("discipline_inputs")
    structure = inputs.get("structure") if isinstance(inputs, dict) else None
    return structure if isinstance(structure, dict) else {}


def _p2_spaces(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        identifier: entity
        for identifier, entity in _entities(snapshot).items()
        if entity.get("kind") == "space" and entity.get("level") == "P2"
    }


def _source_ref(*path: str) -> str:
    return "discipline_inputs." + ".".join(path)


def _source_valid_opening(entity: dict[str, Any]) -> tuple[float, float, str | None]:
    geometry = entity.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("shape") != "opening":
        return 0.0, 0.0, "normalized opening geometry is absent or unsupported"
    x0, x1 = _number(geometry.get("x0")), _number(geometry.get("x1"))
    y0, y1 = _number(geometry.get("y0")), _number(geometry.get("y1"))
    if None in (x0, x1, y0, y1):
        return 0.0, 0.0, "normalized opening bounds are incomplete or non-finite"
    if x1 > x0 + _TOL and abs(y1 - y0) <= _TOL:
        return x0, x1, None
    if y1 > y0 + _TOL and abs(x1 - x0) <= _TOL:
        return y0, y1, None
    return 0.0, 0.0, "opening is not represented as a straight plan interval"


def _exterior_wall_schedule(
    snapshot: dict[str, Any],
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    p2 = _p2_source(snapshot)
    entities = _entities(snapshot)
    required = [
        _source_ref("programme", "p2", "exterior_wall_assembly"),
        _source_ref("programme", "p2", "envelope"),
        _source_ref("programme", "p2", "windows"),
        "entities[registered P2 exterior openings].geometry",
    ]
    if p2 is None or not isinstance(p2.get("exterior_wall_assembly"), dict):
        evidence = {
            "calculation_state": "unsupported",
            "gross_plan_line_m": None,
            "opening_union_m": None,
            "net_plan_line_m": None,
            "plan_line_without_aperture_span_m": None,
            "wall_area_m2": None,
            "wall_volume_m3": None,
            "wall_mass_kg": None,
            "required_inputs_missing": required,
            "next_evidence_required": _RULE_DEFINITIONS["WALL-EXTERIOR-LINE-SCHEDULE"][
                "required_data"
            ],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "WALL-EXTERIOR-LINE-SCHEDULE",
            "OPEN",
            "unsupported",
            "The resolved snapshot does not contain the current P2 exterior wall scope and opening context.",
            evidence=evidence,
        )
        return evidence

    envelope = p2.get("envelope")
    assembly = p2["exterior_wall_assembly"]
    windows = p2.get("windows")
    x0 = _number(envelope.get("x")) if isinstance(envelope, dict) else None
    y0 = 0.0
    length = _number(envelope.get("length")) if isinstance(envelope, dict) else None
    width = _number(envelope.get("width")) if isinstance(envelope, dict) else None
    if None in (x0, length, width) or not isinstance(windows, list):
        evidence = {
            "calculation_state": "unsupported",
            "gross_plan_line_m": None,
            "opening_union_m": None,
            "net_plan_line_m": None,
            "plan_line_without_aperture_span_m": None,
            "wall_area_m2": None,
            "wall_volume_m3": None,
            "wall_mass_kg": None,
            "required_inputs_missing": required,
            "next_evidence_required": _RULE_DEFINITIONS["WALL-EXTERIOR-LINE-SCHEDULE"][
                "required_data"
            ],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "WALL-EXTERIOR-LINE-SCHEDULE",
            "OPEN",
            "unsupported",
            "P2 exterior bounds or scheduled openings are incomplete; no net plan-line measurement is claimed.",
            evidence=evidence,
        )
        return evidence

    x1, y1 = x0 + length, y0 + width
    edge_specs = {
        "south": {"fixed": y0, "lo": x0, "hi": x1, "axis": "x"},
        "north": {"fixed": y1, "lo": x0, "hi": x1, "axis": "x"},
        "east": {"fixed": x1, "lo": y0, "hi": y1, "axis": "y"},
    }
    declared_edges = assembly.get("edges")
    if (
        not isinstance(declared_edges, list)
        or not declared_edges
        or any(item not in edge_specs for item in declared_edges)
    ):
        errors = ["exterior assembly edge scope is missing or unsupported"]
    else:
        errors = []

    edge_sequence = declared_edges if isinstance(declared_edges, list) else []
    by_edge: dict[str, list[dict[str, Any]]] = {edge: [] for edge in edge_sequence}
    issue_details: list[dict[str, Any]] = []
    expected_ids: set[str] = set()
    for source_window in windows:
        if not isinstance(source_window, dict):
            errors.append("P2 source window row is not an object")
            continue
        identifier = source_window.get("id")
        edge = source_window.get("edge")
        if not isinstance(identifier, str) or edge not in by_edge:
            errors.append(f"scheduled exterior opening {identifier!r} has no supported wall edge")
            continue
        expected_ids.add(identifier)
        entity = entities.get(identifier)
        if entity is None or entity.get("kind") != "opening" or entity.get("level") != "P2":
            issue_details.append(
                {"entity_id": identifier, "issue": "current normalized P2 opening is missing"}
            )
            errors.append(f"normalized P2 opening {identifier} is missing")
            continue
        _, _, geometry_error = _source_valid_opening(entity)
        if geometry_error:
            issue_details.append({"entity_id": identifier, "issue": geometry_error})
            errors.append(f"normalized P2 opening {identifier}: {geometry_error}")
            continue
        spec = edge_specs[edge]
        geometry = entity["geometry"]
        if spec["axis"] == "x":
            interval_lo, interval_hi = _number(geometry.get("x0")), _number(geometry.get("x1"))
            line_start = _number(geometry.get("y0"))
            line_end = _number(geometry.get("y1"))
            edge_coordinate = line_start
            line_matches = (
                line_start is not None
                and line_end is not None
                and abs(line_start - line_end) <= _TOL
            )
        else:
            interval_lo, interval_hi = _number(geometry.get("y0")), _number(geometry.get("y1"))
            line_start = _number(geometry.get("x0"))
            line_end = _number(geometry.get("x1"))
            edge_coordinate = line_start
            line_matches = (
                line_start is not None
                and line_end is not None
                and abs(line_start - line_end) <= _TOL
            )
        if (
            interval_lo is None
            or interval_hi is None
            or edge_coordinate is None
            or not line_matches
            or abs(edge_coordinate - spec["fixed"]) > _TOL
        ):
            issue_details.append(
                {"entity_id": identifier, "issue": f"opening is not on scheduled {edge} edge"}
            )
            errors.append(f"normalized P2 opening {identifier} is not on the scheduled {edge} edge")
            continue
        clipped_lo, clipped_hi = max(spec["lo"], interval_lo), min(spec["hi"], interval_hi)
        out_of_bounds = interval_lo < spec["lo"] - _TOL or interval_hi > spec["hi"] + _TOL
        if out_of_bounds:
            errors.append(
                f"normalized P2 opening {identifier} extends beyond the scheduled {edge} edge"
            )
            issue_details.append(
                {
                    "entity_id": identifier,
                    "issue": "opening extends beyond scheduled wall edge",
                    "interval_m": [interval_lo, interval_hi],
                    "clipped_diagnostic_interval_m": [clipped_lo, clipped_hi],
                }
            )
        if clipped_hi <= clipped_lo + _TOL:
            errors.append(
                f"normalized P2 opening {identifier} has no interval inside the scheduled edge"
            )
            continue
        by_edge[edge].append(
            {
                "entity_id": identifier,
                "interval_m": [interval_lo, interval_hi],
                "diagnostic_clipped_interval_m": [clipped_lo, clipped_hi],
                "source_window_edge": edge,
                "opening_status": entity.get("status"),
                "out_of_bounds": out_of_bounds,
                "_interval": (clipped_lo, clipped_hi),
            }
        )

    current_exterior_opening_ids = {
        identifier
        for identifier, entity in entities.items()
        if entity.get("kind") == "opening"
        and entity.get("level") == "P2"
        and isinstance(entity.get("parameters"), dict)
        and entity["parameters"].get("facade") in {"A", "B", "REAR"}
    }
    unscheduled_ids = current_exterior_opening_ids - expected_ids
    for identifier in sorted(unscheduled_ids):
        expected_ids.add(identifier)
        errors.append(
            f"normalized P2 exterior opening {identifier} is missing from the source wall schedule"
        )
        issue_details.append(
            {
                "entity_id": identifier,
                "issue": "registered exterior opening is not listed in scheduled P2 windows",
            }
        )

    edge_rows: list[dict[str, Any]] = []
    gross_total = 0.0
    union_total = 0.0
    raw_total = 0.0
    overlap_total = 0.0
    for edge in edge_sequence:
        spec = edge_specs.get(edge)
        if spec is None:
            continue
        gross = spec["hi"] - spec["lo"]
        intervals = [row["_interval"] for row in by_edge.get(edge, [])]
        union, union_length, overlap = _merge_intervals(intervals)
        raw = sum(end - start for start, end in intervals)
        gross_total += gross
        union_total += union_length
        raw_total += raw
        overlap_total += overlap
        if overlap > _TOL:
            errors.append(
                f"normalized P2 openings overlap on scheduled {edge} edge by {overlap:.6g} m"
            )
            issue_details.append(
                {"edge": edge, "issue": "opening intervals overlap", "overlap_m": overlap}
            )
        edge_rows.append(
            {
                "edge": edge,
                "gross_plan_line_m": gross,
                "opening_interval_ids": [row["entity_id"] for row in by_edge.get(edge, [])],
                "opening_intervals_m": [
                    {key: value for key, value in row.items() if key != "_interval"}
                    for row in by_edge.get(edge, [])
                ],
                "opening_union_intervals_m": union,
                "opening_union_m": union_length,
                "raw_opening_span_sum_m": raw,
                "opening_overlap_m": overlap,
                "plan_line_without_aperture_span_m": (gross - union_length if not errors else None),
            }
        )

    intervals_resolved = len(expected_ids) == sum(len(items) for items in by_edge.values())
    valid = not errors and intervals_resolved
    if not valid:
        for edge_row in edge_rows:
            edge_row["plan_line_without_aperture_span_m"] = None
    layer_rows = assembly.get("outside_to_inside_layers")
    layer_thicknesses = (
        [_number(item.get("nominal_mm")) for item in layer_rows if isinstance(item, dict)]
        if isinstance(layer_rows, list)
        else []
    )
    layer_sum_mm = (
        sum(layer_thicknesses)
        if layer_thicknesses and all(value is not None for value in layer_thicknesses)
        else None
    )
    layer_sum_note = assembly.get("layer_sum_note")
    note_match = (
        re.search(r"approximately\s+([0-9]+(?:\.[0-9]+)?)\s*mm", layer_sum_note, re.IGNORECASE)
        if isinstance(layer_sum_note, str)
        else None
    )
    stated_layer_sum_mm = float(note_match.group(1)) if note_match else None
    thickness_conflict = (
        layer_sum_mm is not None
        and stated_layer_sum_mm is not None
        and not math.isclose(layer_sum_mm, stated_layer_sum_mm, abs_tol=1.0)
    )
    evidence = {
        "calculation_state": "measured" if valid else "invalid_or_incomplete",
        "schedule_family_id": assembly.get("id"),
        "nominal_schedule_thickness_m": _number(assembly.get("nominal_total_m")),
        "source_layer_nominal_sum_mm": layer_sum_mm,
        "source_note_layer_sum_mm": stated_layer_sum_mm,
        "source_layer_sum_note": layer_sum_note,
        "source_thickness_basis_conflict": thickness_conflict,
        "conflict_ids": ["CF-014"] if thickness_conflict else [],
        "source_consistency_issues": (
            [
                "Structured layer dimensions total 229 mm while the source note states approximately 297 mm and draws 300 mm nominal."
            ]
            if thickness_conflict
            else []
        ),
        "source_refs": [
            _source_ref("programme", "p2", "exterior_wall_assembly"),
            _source_ref("programme", "p2", "envelope"),
            _source_ref("programme", "p2", "windows"),
            "entities[normalized current P2 exterior openings].geometry",
        ],
        "edge_measurements": edge_rows,
        "gross_plan_line_m": gross_total if declared_edges else None,
        "opening_union_m": union_total if intervals_resolved else None,
        "raw_opening_span_sum_m": raw_total if intervals_resolved else None,
        "opening_overlap_m": overlap_total if intervals_resolved else None,
        "plan_line_without_aperture_span_m": gross_total - union_total if valid else None,
        "quantity_valid": valid,
        "wall_area_m2": None,
        "wall_volume_m3": None,
        "wall_mass_kg": None,
        "required_inputs_missing": sorted(set(errors)),
        "next_evidence_required": [
            "resolve any discrepancy between structured layer dimensions and the source's stated layer sum",
            "verified wall height and end/return conditions",
            "selected and professionally coordinated wall assembly",
            "verified product mass per area and component mass for load take-down",
            "current vertical opening extents and reveal/perimeter detailing",
        ],
        "interpretation": (
            "Aperture spans subtract only their plan footprints from the scheduled line. Wall remains above and below openings;"
            " this is not a net wall area or opaque-material quantity."
        ),
    }
    data_incomplete = any(
        marker in error.lower()
        for error in errors
        for marker in ("missing", "incomplete", "no supported", "not an object", "absent")
    )
    status = "OPEN" if valid or data_incomplete else "FAIL"
    coverage = "unsupported" if data_incomplete else "evaluated" if edge_rows else "unsupported"
    message = (
        f"P2-W05 covers {gross_total:.2f} m of scheduled exterior plan line; current opening intervals occupy "
        f"{union_total:.2f} m in plan. Wall area and mass remain unknown."
        if valid
        else "Current P2 exterior opening data are incomplete or inconsistent with the scheduled wall edge; no net line quantity is claimed."
    )
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "WALL-EXTERIOR-LINE-SCHEDULE",
        status,
        coverage,
        message,
        tuple(sorted(expected_ids)),
        evidence,
    )
    return evidence


def _pair_boundary(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any] | None:
    first_geom, second_geom = first.get("geometry"), second.get("geometry")
    if not isinstance(first_geom, dict) or not isinstance(second_geom, dict):
        return None
    a = {key: _number(first_geom.get(key)) for key in ("x0", "x1", "y0", "y1")}
    b = {key: _number(second_geom.get(key)) for key in ("x0", "x1", "y0", "y1")}
    if any(value is None for value in (*a.values(), *b.values())):
        return None
    for edge_a, edge_b in (("x1", "x0"), ("x0", "x1")):
        start, end = max(a["y0"], b["y0"]), min(a["y1"], b["y1"])
        if abs(a[edge_a] - b[edge_b]) <= _TOL and end - start > _TOL:
            return {
                "axis": "y",
                "fixed_m": (a[edge_a] + b[edge_b]) / 2,
                "start_m": start,
                "end_m": end,
            }
    for edge_a, edge_b in (("y1", "y0"), ("y0", "y1")):
        start, end = max(a["x0"], b["x0"]), min(a["x1"], b["x1"])
        if abs(a[edge_a] - b[edge_b]) <= _TOL and end - start > _TOL:
            return {
                "axis": "x",
                "fixed_m": (a[edge_a] + b[edge_b]) / 2,
                "start_m": start,
                "end_m": end,
            }
    return None


def _door_boundary_interval(door: dict[str, Any]) -> tuple[str, float, float, float] | None:
    geometry = door.get("geometry")
    if not isinstance(geometry, dict):
        return None
    coords = {key: _number(geometry.get(key)) for key in ("x0", "x1", "y0", "y1")}
    if any(value is None for value in coords.values()):
        return None
    if abs(coords["x1"] - coords["x0"]) <= _TOL and coords["y1"] - coords["y0"] > _TOL:
        return "y", (coords["x0"] + coords["x1"]) / 2, coords["y0"], coords["y1"]
    if abs(coords["y1"] - coords["y0"]) <= _TOL and coords["x1"] - coords["x0"] > _TOL:
        return "x", (coords["y0"] + coords["y1"]) / 2, coords["x0"], coords["x1"]
    return None


def _dry_boundary_candidates(
    snapshot: dict[str, Any],
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    p2 = _p2_source(snapshot)
    entities = _entities(snapshot)
    spaces = _p2_spaces(snapshot)
    if p2 is None or not isinstance(p2.get("spaces"), list) or not spaces:
        evidence = {
            "calculation_state": "unsupported",
            "schedule_family_id": "P2-W01A",
            "candidate_boundaries": [],
            "gross_candidate_line_m": None,
            "opening_union_m": None,
            "remaining_candidate_line_m": None,
            "required_inputs_missing": [
                _source_ref("programme", "p2", "spaces"),
                "entities[current P2 spaces and doors].geometry and relationships",
            ],
            "next_evidence_required": _RULE_DEFINITIONS["WALL-W01A-DRY-BOUNDARY-REMAINDER"][
                "required_data"
            ],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "WALL-W01A-DRY-BOUNDARY-REMAINDER",
            "OPEN",
            "unsupported",
            "Current P2 dry-boundary geometry and suite tags are unavailable; no boundary length is claimed.",
            evidence=evidence,
        )
        return evidence

    source_spaces = {
        item.get("id"): item
        for item in p2["spaces"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    missing_space_entities = sorted(set(source_spaces) - set(spaces))
    unlisted_space_entities = sorted(set(spaces) - set(source_spaces))
    invalid_space_bounds = []
    for identifier, entity in spaces.items():
        geometry = entity.get("geometry")
        coords = (
            [_number(geometry.get(key)) for key in ("x0", "x1", "y0", "y1")]
            if isinstance(geometry, dict) and geometry.get("shape") == "rect"
            else []
        )
        if len(coords) != 4 or any(value is None for value in coords):
            invalid_space_bounds.append(identifier)
    if missing_space_entities or unlisted_space_entities or invalid_space_bounds:
        evidence = {
            "calculation_state": "unsupported",
            "schedule_family_id": "P2-W01A",
            "candidate_boundaries": [],
            "gross_candidate_line_m": None,
            "opening_union_m": None,
            "remaining_candidate_line_m": None,
            "registered_wall_instances": 0,
            "required_inputs_missing": [
                *[f"normalized P2 space {item} is missing" for item in missing_space_entities],
                *[
                    f"normalized P2 space {item} has no current P2 source row"
                    for item in unlisted_space_entities
                ],
                *[
                    f"normalized P2 space {item} has invalid or incomplete rectangular bounds"
                    for item in invalid_space_bounds
                ],
            ],
            "next_evidence_required": _RULE_DEFINITIONS["WALL-W01A-DRY-BOUNDARY-REMAINDER"][
                "required_data"
            ],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "WALL-W01A-DRY-BOUNDARY-REMAINDER",
            "OPEN",
            "unsupported",
            "Current P2 room identity/geometry is incomplete; no dry-boundary schedule candidate is claimed.",
            evidence=evidence,
        )
        return evidence
    dry_exclusions = {"bath", "wellness", "vertical", "shared", "deck"}
    candidates: list[dict[str, Any]] = []
    for first_id, second_id in combinations(sorted(spaces), 2):
        first, second = spaces[first_id], spaces[second_id]
        first_parameters = first.get("parameters", {})
        second_parameters = second.get("parameters", {})
        first_source, second_source = source_spaces.get(first_id), source_spaces.get(second_id)
        if not isinstance(first_source, dict) or not isinstance(second_source, dict):
            continue
        suite = first_parameters.get("suite")
        if (
            not suite
            or suite != second_parameters.get("suite")
            or first_parameters.get("space_kind") in dry_exclusions
            or second_parameters.get("space_kind") in dry_exclusions
        ):
            continue
        boundary = _pair_boundary(first, second)
        if boundary is None:
            continue
        source_doors = p2.get("doors")
        source_doors = source_doors if isinstance(source_doors, list) else []
        expected_door_ids = {
            item.get("id")
            for item in source_doors
            if isinstance(item, dict)
            and isinstance(item.get("connects"), list)
            and set(item["connects"]) == {first_id, second_id}
            and isinstance(item.get("id"), str)
        }
        doors = []
        for entity in entities.values():
            relationships = entity.get("relationships")
            space_ids = relationships.get("space_ids") if isinstance(relationships, dict) else None
            if (
                entity.get("kind") == "door"
                and isinstance(space_ids, list)
                and set(space_ids) == {first_id, second_id}
            ):
                doors.append(entity)
        seen_door_ids = {door.get("id") for door in doors}
        missing_doors = sorted(expected_door_ids - seen_door_ids)
        pair_errors = [
            f"normalized opening/door {identifier} for boundary {first_id}/{second_id} is missing"
            for identifier in missing_doors
        ]
        intervals: list[tuple[float, float]] = []
        opening_records: list[dict[str, Any]] = []
        for door in doors:
            door_id = door.get("id")
            interval = _door_boundary_interval(door)
            if interval is None:
                pair_errors.append(f"door {door_id} has unresolved or unsupported plan geometry")
                opening_records.append(
                    {"entity_id": door_id, "interval_on_boundary_m": None, "valid": False}
                )
                continue
            axis, fixed, start, end = interval
            if axis != boundary["axis"] or abs(fixed - boundary["fixed_m"]) > _TOL:
                pair_errors.append(
                    f"door {door_id} no longer lies on its current room-pair boundary"
                )
                opening_records.append(
                    {
                        "entity_id": door_id,
                        "interval_m": [start, end],
                        "valid": False,
                        "issue": "not on boundary",
                    }
                )
                continue
            clip_start = max(start, boundary["start_m"])
            clip_end = min(end, boundary["end_m"])
            if (
                start < boundary["start_m"] - _TOL
                or end > boundary["end_m"] + _TOL
                or clip_end <= clip_start + _TOL
            ):
                pair_errors.append(f"door {door_id} extends beyond its current room-pair boundary")
                opening_records.append(
                    {
                        "entity_id": door_id,
                        "interval_m": [start, end],
                        "clipped_diagnostic_interval_m": [clip_start, clip_end],
                        "valid": False,
                    }
                )
                if clip_end > clip_start + _TOL:
                    intervals.append((clip_start, clip_end))
                continue
            intervals.append((start, end))
            opening_records.append(
                {"entity_id": door_id, "interval_m": [start, end], "valid": True}
            )
        union, opening_union, overlap = _merge_intervals(intervals)
        if overlap > _TOL:
            pair_errors.append(f"door/opening intervals overlap by {overlap:.6g} m")
        gross = boundary["end_m"] - boundary["start_m"]
        valid = not pair_errors
        remaining = gross - opening_union if valid else None
        if remaining is not None and remaining < -_TOL:
            pair_errors.append("opening union exceeds boundary length")
            valid, remaining = False, None
        family_assignment = (
            "P2-W01A" if valid and remaining is not None and remaining > _TOL else None
        )
        unavailable = bool(missing_doors) or any("unresolved" in error for error in pair_errors)
        record = {
            "space_ids": [first_id, second_id],
            "suite_id": suite,
            "boundary_axis": boundary["axis"],
            "fixed_coordinate_m": boundary["fixed_m"],
            "boundary_interval_m": [boundary["start_m"], boundary["end_m"]],
            "gross_shared_boundary_m": gross,
            "registered_openings": opening_records,
            "opening_union_intervals_m": union,
            "opening_union_m": opening_union,
            "opening_overlap_m": overlap,
            "remaining_plan_line_m": remaining,
            "rule_compatible_family_candidate": family_assignment,
            "registered_wall_instance": False,
            "valid": valid,
            "issues": pair_errors,
        }
        candidates.append(record)
        pair_ids = tuple(
            sorted((first_id, second_id, *(item["entity_id"] for item in opening_records)))
        )
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "WALL-W01A-DRY-BOUNDARY-REMAINDER",
            "OPEN" if valid or unavailable else "FAIL",
            "unsupported" if unavailable else "evaluated",
            (
                f"{first_id}/{second_id} share {gross:.2f} m of same-suite dry boundary; registered opening union "
                f"is {opening_union:.2f} m. Candidate remainder is not a wall instance."
                if valid
                else f"{first_id}/{second_id} boundary/opening geometry is inconsistent; no remainder quantity is claimed."
            ),
            pair_ids,
            {
                "schedule_family_candidate": family_assignment,
                "source_refs": [
                    _source_ref("programme", "p2", "spaces"),
                    _source_ref("programme", "p2", "internal_partition"),
                    "entities[current P2 doors].geometry and relationships",
                ],
                **record,
                "required_inputs_missing": pair_errors,
                "next_evidence_required": _RULE_DEFINITIONS["WALL-W01A-DRY-BOUNDARY-REMAINDER"][
                    "required_data"
                ],
                "wall_area_m2": None,
                "wall_mass_kg": None,
            },
        )

    measured = [item for item in candidates if item["valid"]]
    totals_valid = len(measured) == len(candidates)
    aggregate = {
        "calculation_state": "measured_candidates"
        if candidates and totals_valid
        else "invalid_or_incomplete"
        if candidates
        else "unsupported",
        "schedule_family_id": "P2-W01A",
        "rule_compatible_same_suite_dry_predicate": "same nonempty suite; neither adjacent space is bath, wellness, vertical, shared or deck",
        "candidate_boundaries": candidates,
        "gross_candidate_line_m": sum(item["gross_shared_boundary_m"] for item in measured)
        if totals_valid
        else None,
        "opening_union_m": sum(item["opening_union_m"] for item in measured)
        if totals_valid
        else None,
        "remaining_candidate_line_m": sum(item["remaining_plan_line_m"] or 0.0 for item in measured)
        if totals_valid
        else None,
        "registered_wall_instances": 0,
        "wall_area_m2": None,
        "wall_mass_kg": None,
        "unassigned_interior_boundaries": "Other P2 boundaries are not assigned a wall type or instance by this adapter.",
        "required_inputs_missing": sorted(
            {error for item in candidates for error in item["issues"]}
        ),
        "next_evidence_required": _RULE_DEFINITIONS["WALL-W01A-DRY-BOUNDARY-REMAINDER"][
            "required_data"
        ],
    }
    if not candidates:
        aggregate["required_inputs_missing"] = [
            "no supported same-suite dry shared boundary was found"
        ]
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "WALL-W01A-DRY-BOUNDARY-REMAINDER",
            "OPEN",
            "unsupported",
            "No same-suite dry shared-boundary candidate could be measured from the current resolved spaces.",
            evidence=aggregate,
        )
    return aggregate


def _hall_edge_lengths(
    snapshot: dict[str, Any],
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    p2 = _p2_source(snapshot)
    spaces = _p2_spaces(snapshot)
    hall = p2.get("hall_edge_partition") if p2 else None
    balcony = p2.get("family_balcony") if p2 else None
    required = [
        _source_ref("programme", "p2", "hall_edge_partition"),
        _source_ref("programme", "p2", "family_balcony"),
        "entities[H1-D,H2-D].geometry",
    ]
    if (
        not isinstance(hall, dict)
        or not isinstance(balcony, dict)
        or not all(identifier in spaces for identifier in ("H1-D", "H2-D"))
    ):
        evidence = {
            "calculation_state": "unsupported",
            "retained_length_m": None,
            "open_frontage_length_m": None,
            "total_edge_length_m": None,
            "required_inputs_missing": required,
            "next_evidence_required": _RULE_DEFINITIONS["WALL-HALL-EDGE-PHASE-LENGTHS"][
                "required_data"
            ],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "WALL-HALL-EDGE-PHASE-LENGTHS",
            "OPEN",
            "unsupported",
            "P2 hall-edge extents or normalized bedroom bounds are unavailable.",
            evidence=evidence,
        )
        return evidence
    edge_x = _number(hall.get("axis_x"))
    open_start = _number(balcony.get("from_y"))
    open_end = _number(balcony.get("to_y"))
    edge_start = _number(hall.get("from_y"))
    edge_end = _number(hall.get("to_y"))
    bedroom_bounds = []
    for identifier in ("H1-D", "H2-D"):
        geom = spaces[identifier].get("geometry", {})
        values = [_number(geom.get(key)) for key in ("x0", "y0", "x1", "y1")]
        if any(value is None for value in values):
            bedroom_bounds = []
            break
        bedroom_bounds.append((identifier, *values))
    invalid = None in (edge_x, open_start, open_end, edge_start, edge_end) or not bedroom_bounds
    if not invalid:
        invalid = (
            open_start < edge_start - _TOL
            or open_end > edge_end + _TOL
            or open_end <= open_start
            or any(abs(x0 - edge_x) > _TOL for _, x0, _y0, _x1, _y1 in bedroom_bounds)
        )
    if invalid:
        evidence = {
            "calculation_state": "invalid_or_incomplete",
            "retained_length_m": None,
            "open_frontage_length_m": None,
            "total_edge_length_m": None,
            "required_inputs_missing": [
                "source retained/open limits do not reconcile with current P2 bedroom geometry"
            ],
            "next_evidence_required": _RULE_DEFINITIONS["WALL-HALL-EDGE-PHASE-LENGTHS"][
                "required_data"
            ],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "WALL-HALL-EDGE-PHASE-LENGTHS",
            "FAIL",
            "evaluated",
            "The retained/open source line does not reconcile with current room-edge geometry; no wall-length schedule is claimed.",
            tuple(identifier for identifier, *_ in bedroom_bounds),
            evidence,
        )
        return evidence
    bedroom_intervals = sorted((y0, y1) for _identifier, _x0, y0, _x1, y1 in bedroom_bounds)
    retained_intervals = [[edge_start, open_start], [open_end, edge_end]]
    retained = sum(end - start for start, end in retained_intervals)
    open_length = open_end - open_start
    edge_length = edge_end - edge_start
    consistent = (
        len(bedroom_intervals) == len(retained_intervals)
        and all(
            math.isclose(actual[0], expected[0], abs_tol=_TOL)
            and math.isclose(actual[1], expected[1], abs_tol=_TOL)
            for actual, expected in zip(bedroom_intervals, retained_intervals, strict=True)
        )
        and math.isclose(edge_length, retained + open_length, abs_tol=_TOL)
        and math.isclose(
            edge_length,
            _number(hall.get("to_y")) - _number(hall.get("from_y")),
            abs_tol=_TOL,
        )
    )
    evidence = {
        "calculation_state": "measured" if consistent else "invalid_or_incomplete",
        "schedule_family_id": hall.get("id"),
        "nominal_schedule_thickness_m": _number(hall.get("nominal_total_m")),
        "retained_segments_y_m": retained_intervals,
        "retained_length_m": retained if consistent else None,
        "open_family_frontage_y_m": [open_start, open_end],
        "open_frontage_length_m": open_length if consistent else None,
        "total_edge_length_m": edge_length if consistent else None,
        "source_bedroom_edge_intervals_m": [list(item) for item in bedroom_intervals],
        "wall_area_m2": None,
        "wall_mass_kg": None,
        "required_inputs_missing": []
        if consistent
        else ["retained P2-W04R length differs from the current bedroom-edge bounds"],
        "next_evidence_required": [
            "verified wall height and selected acoustic/fire assembly",
            "guard design, anchors and temporary-works sequence",
            "edge-beam/structure interface and fire/smoke review",
        ],
    }
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "WALL-HALL-EDGE-PHASE-LENGTHS",
        "OPEN" if consistent else "FAIL",
        "evaluated",
        (
            f"P2-W04R retains {retained:.2f} m at the bedroom ends, with {open_length:.2f} m of intentionally open family frontage."
            if consistent
            else "P2-W04R lengths conflict with current normalized bedroom bounds."
        ),
        ("H1-D", "H2-D"),
        evidence,
    )
    return evidence


def _phase_reservations(
    snapshot: dict[str, Any],
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    p2 = _p2_source(snapshot)
    spaces = _p2_spaces(snapshot)
    required = [
        _source_ref("programme", "p2", "spaces"),
        _source_ref("programme", "p2", "phase_boundary_y"),
        _source_ref("programme", "p2", "central_distributor"),
        _source_ref("programme", "p2", "family_balcony"),
    ]
    source_spaces = p2.get("spaces") if p2 else None
    if not isinstance(source_spaces, list) or not spaces:
        evidence = {
            "calculation_state": "unsupported",
            "gross_tagged_area_m2_by_phase": None,
            "required_inputs_missing": required,
            "next_evidence_required": _RULE_DEFINITIONS["P2-PHASE-RESERVATION-COVERAGE"][
                "required_data"
            ],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "P2-PHASE-RESERVATION-COVERAGE",
            "OPEN",
            "unsupported",
            "Current P2 phase tags or resolved room bounds are unavailable.",
            evidence=evidence,
        )
        return evidence
    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    seen: set[str] = set()
    for source_row in source_spaces:
        if not isinstance(source_row, dict) or not isinstance(source_row.get("id"), str):
            missing.append("P2 space row has no identity")
            continue
        identifier = source_row["id"]
        seen.add(identifier)
        phase = source_row.get("phase")
        entity = spaces.get(identifier)
        geom = entity.get("geometry") if entity else None
        if type(phase) is not int or phase not in (1, 2) or not isinstance(geom, dict):
            missing.append(
                f"space {identifier} is missing a valid phase tag or normalized geometry"
            )
            continue
        x0, x1 = _number(geom.get("x0")), _number(geom.get("x1"))
        y0, y1 = _number(geom.get("y0")), _number(geom.get("y1"))
        if None in (x0, x1, y0, y1) or x1 <= x0 or y1 <= y0:
            missing.append(
                f"space {identifier} has incomplete or invalid current rectangular bounds"
            )
            continue
        rows.append(
            {
                "space_id": identifier,
                "phase": phase,
                "plan_rectangle_m": {"x0": x0, "x1": x1, "y0": y0, "y1": y1},
                "tagged_rectangle_area_m2": (x1 - x0) * (y1 - y0),
            }
        )
    for identifier in sorted(set(spaces) - seen):
        missing.append(f"normalized P2 space {identifier} has no source phase tag")
    overlaps: list[dict[str, Any]] = []
    for first, second in combinations(rows, 2):
        a, b = first["plan_rectangle_m"], second["plan_rectangle_m"]
        overlap_x = min(a["x1"], b["x1"]) - max(a["x0"], b["x0"])
        overlap_y = min(a["y1"], b["y1"]) - max(a["y0"], b["y0"])
        if overlap_x > _TOL and overlap_y > _TOL:
            overlaps.append(
                {
                    "space_ids": [first["space_id"], second["space_id"]],
                    "overlap_area_m2": overlap_x * overlap_y,
                }
            )
    areas = {
        phase: sum(row["tagged_rectangle_area_m2"] for row in rows if row["phase"] == phase)
        for phase in (1, 2)
    }
    phase_boundary = _number(p2.get("phase_boundary_y"))
    central = p2.get("central_distributor")
    balcony = p2.get("family_balcony")
    if not isinstance(central, dict) or not isinstance(balcony, dict):
        missing.append("phase closure or family-frontage source reservation is incomplete")
    close_y = (
        _number(central.get("temporary_phase_boundary_y")) if isinstance(central, dict) else None
    )
    frontage_start = _number(balcony.get("from_y")) if isinstance(balcony, dict) else None
    frontage_end = _number(balcony.get("to_y")) if isinstance(balcony, dict) else None
    entities = _entities(snapshot)
    closure = entities.get("D-FAM-N")
    closure_geometry = closure.get("geometry") if closure else None
    closure_span = None
    if isinstance(closure_geometry, dict):
        coords = [_number(closure_geometry.get(key)) for key in ("x0", "x1", "y0", "y1")]
        if None not in coords and abs(coords[3] - coords[2]) <= _TOL:
            closure_span = [coords[0], coords[1]]
    closure_valid = (
        phase_boundary is not None
        and close_y is not None
        and math.isclose(phase_boundary, close_y, abs_tol=_TOL)
        and isinstance(closure, dict)
        and closure_span is not None
        and _same_number(closure_geometry.get("y0"), phase_boundary)
        and _same_number(closure_span[0], spaces.get("FAM", {}).get("geometry", {}).get("x0"))
        and _same_number(closure_span[1], spaces.get("FAM", {}).get("geometry", {}).get("x1"))
    )
    if not closure_valid:
        missing.append("current D-FAM-N opening does not resolve the source temporary-closure line")
    envelope = p2.get("envelope", {})
    envelope_length = _number(envelope.get("length")) if isinstance(envelope, dict) else None
    envelope_width = _number(envelope.get("width")) if isinstance(envelope, dict) else None
    gross_envelope = (
        envelope_length * envelope_width
        if envelope_length is not None and envelope_width is not None
        else None
    )
    area_sum = sum(areas.values())
    covers_envelope = (
        gross_envelope is not None
        and not overlaps
        and math.isclose(area_sum, gross_envelope, abs_tol=1e-6)
    )
    guard_phase_1 = None if None in (frontage_start, close_y) else close_y - frontage_start
    guard_phase_2 = (
        None if None in (frontage_start, frontage_end) else frontage_end - frontage_start
    )
    valid = not missing and not overlaps and len(rows) == len(source_spaces) and closure_valid
    evidence = {
        "calculation_state": "measured" if valid else "invalid_or_incomplete",
        "tagged_space_count": len(rows),
        "gross_tagged_area_m2_by_phase": {str(key): value for key, value in areas.items()}
        if valid
        else None,
        "total_tagged_plan_area_m2": area_sum if valid else None,
        "source_envelope_area_m2": gross_envelope,
        "tagged_rectangles_cover_envelope_without_overlap": covers_envelope if valid else None,
        "phase_space_records": rows,
        "space_overlap_records": overlaps,
        "phase_boundary_y_m": phase_boundary,
        "temporary_phase_closure": {
            "source_rule": central.get("phase_rule") if isinstance(central, dict) else None,
            "boundary_y_m": close_y,
            "current_registered_opening_id": "D-FAM-N" if closure else None,
            "current_opening_span_x_m": closure_span,
            "required_during_phase_1": True,
            "physical_installation_state": "unknown",
            "geometry_matches_reservation": closure_valid,
        },
        "family_frontage_guard_reservation": {
            "axis_x_m": _number(balcony.get("axis_x")) if isinstance(balcony, dict) else None,
            "phase_1_y_interval_m": [frontage_start, close_y],
            "phase_1_length_m": guard_phase_1,
            "phase_2_y_interval_m": [frontage_start, frontage_end],
            "phase_2_length_m": guard_phase_2,
            "physical_installation_state": "unknown",
            "source_rule": balcony.get("phasing_rule") if isinstance(balcony, dict) else None,
        },
        "required_inputs_missing": missing,
        "next_evidence_required": _RULE_DEFINITIONS["P2-PHASE-RESERVATION-COVERAGE"][
            "required_data"
        ],
    }
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "P2-PHASE-RESERVATION-COVERAGE",
        "OPEN" if valid else "FAIL",
        "evaluated" if rows else "unsupported",
        (
            f"Current P2 space rectangles total {areas[1]:.2f} m² in Phase 1 and {areas[2]:.2f} m² in Phase 2; "
            "temporary closure and guard installation evidence remain unknown."
            if valid
            else "P2 phase tags, room bounds or temporary-closure geometry are incomplete or inconsistent."
        ),
        tuple(sorted(set(spaces) | ({"D-FAM-N"} if closure else set()))),
        evidence,
    )
    return evidence


def _stair_relationships(
    snapshot: dict[str, Any],
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source = _structure_sources(snapshot)
    stair_model = source.get("stair")
    entities = _entities(snapshot)
    required_refs = [
        _source_ref("structure", "stair", "levels"),
        _source_ref("structure", "stair", "stair"),
        "entities[ST-F1,ST-F2,ST-L1,D-STAIR,EXT-ESC]",
    ]
    if not isinstance(stair_model, dict) or not all(
        identifier in entities for identifier in ("ST-F1", "ST-F2", "ST-L1", "D-STAIR")
    ):
        evidence = {
            "calculation_state": "unsupported",
            "levels_m": None,
            "required_inputs_missing": required_refs,
            "next_evidence_required": _RULE_DEFINITIONS["SC01-CROSS-LEVEL-DATUMS"]["required_data"],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "SC01-CROSS-LEVEL-DATUMS",
            "OPEN",
            "unsupported",
            "SC-01 source data or normalized stair/opening entities are incomplete.",
            evidence=evidence,
        )
        return {"cross_level": evidence}
    levels, stair = stair_model.get("levels"), stair_model.get("stair")
    try:
        pb = _number(levels.get("pb_finished_floor"))
        landing = _number(levels.get("intermediate_landing"))
        p2 = _number(levels.get("p2_finished_floor"))
        total_risers = stair.get("total_risers")
        risers_by_flight = stair.get("risers_per_flight")
        treads_by_flight = stair.get("treads_per_flight")
        going = _number(stair.get("going"))
        lower = stair.get("lower_flight")
        upper = stair.get("upper_flight")
        landing_source = stair.get("intermediate_landing")
        valid_scalars = (
            all(value is not None for value in (pb, landing, p2, going))
            and type(total_risers) is int
            and isinstance(risers_by_flight, list)
            and all(type(value) is int for value in risers_by_flight)
            and isinstance(treads_by_flight, list)
            and all(type(value) is int for value in treads_by_flight)
            and len(risers_by_flight) == 2
            and len(treads_by_flight) == 2
            and isinstance(lower, dict)
            and isinstance(upper, dict)
            and isinstance(landing_source, dict)
        )
    except (AttributeError, TypeError):
        valid_scalars = False
    if not valid_scalars:
        evidence = {
            "calculation_state": "unsupported",
            "levels_m": None,
            "required_inputs_missing": [
                "SC-01 levels, positive finite going, integer riser/tread counts, or flight datums are invalid"
            ],
            "next_evidence_required": _RULE_DEFINITIONS["SC01-CROSS-LEVEL-DATUMS"]["required_data"],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "SC01-CROSS-LEVEL-DATUMS",
            "OPEN",
            "unsupported",
            "SC-01 cross-level inputs are invalid; derived stair measurements are withheld.",
            evidence=evidence,
        )
        return {"cross_level": evidence}
    total_rise = p2 - pb
    per_flight_rise = [landing - pb, p2 - landing]
    riser_height = total_rise / total_risers if total_risers > 0 else None
    runs = [going * value for value in treads_by_flight]
    stair_entities = {}
    for key in ("ST-F1", "ST-F2", "ST-L1"):
        geometry = entities[key].get("geometry")
        stair_entities[key] = geometry if isinstance(geometry, dict) else {}
    geometry_flight_runs = []
    for identifier in ("ST-F1", "ST-F2"):
        geometry = stair_entities[identifier]
        x0, x1 = _number(geometry.get("x0")), _number(geometry.get("x1"))
        geometry_flight_runs.append(x1 - x0 if x0 is not None and x1 is not None else None)
    landing_x0 = _number(stair_entities["ST-L1"].get("x0"))
    landing_x1 = _number(stair_entities["ST-L1"].get("x1"))
    landing_depth_geometry = (
        landing_x1 - landing_x0 if landing_x0 is not None and landing_x1 is not None else None
    )
    landing_depth_source = _number(stair.get("intermediate_landing_depth"))
    flight_runs_match = all(
        actual is not None and math.isclose(actual, expected, abs_tol=_TOL)
        for actual, expected in zip(geometry_flight_runs, runs, strict=True)
    )
    landing_intersection_matches = (
        landing_x0 is not None
        and _same_number(stair_entities["ST-F1"].get("x1"), landing_x0)
        and _same_number(stair_entities["ST-F2"].get("x1"), landing_x0)
        and landing_depth_geometry is not None
        and landing_depth_source is not None
        and math.isclose(landing_depth_geometry, landing_depth_source, abs_tol=_TOL)
    )
    source_consistent = (
        total_rise > 0
        and total_risers == sum(risers_by_flight)
        and math.isclose(per_flight_rise[0], per_flight_rise[1], abs_tol=_TOL)
        and all(
            _number(flight.get(key)) is not None
            for flight in (lower, upper)
            for key in ("z0", "z1")
        )
        and math.isclose(_number(lower.get("z0")), pb, abs_tol=_TOL)
        and math.isclose(_number(lower.get("z1")), landing, abs_tol=_TOL)
        and math.isclose(_number(upper.get("z0")), landing, abs_tol=_TOL)
        and math.isclose(_number(upper.get("z1")), p2, abs_tol=_TOL)
        and math.isclose(_number(landing_source.get("level")), landing, abs_tol=_TOL)
        and _same_number(stair_entities["ST-F1"].get("z0"), pb)
        and _same_number(stair_entities["ST-F1"].get("z1"), landing)
        and _same_number(stair_entities["ST-F2"].get("z0"), landing)
        and _same_number(stair_entities["ST-F2"].get("z1"), p2)
        and _same_number(stair_entities["ST-L1"].get("z0"), landing)
        and _same_number(stair_entities["ST-L1"].get("z1"), landing)
        and flight_runs_match
        and landing_intersection_matches
        and going > 0
    )
    door = entities["D-STAIR"]
    raw_door_geometry = door.get("geometry")
    door_geometry = raw_door_geometry if isinstance(raw_door_geometry, dict) else {}
    raw_door_parameters = door.get("parameters")
    door_parameters = raw_door_parameters if isinstance(raw_door_parameters, dict) else {}
    p2_access = stair.get("p2_access_platform")
    door_y0, door_y1 = _number(door_geometry.get("y0")), _number(door_geometry.get("y1"))
    door_x = _number(door_geometry.get("x0"))
    door_width = _number(door_parameters.get("width_m"))
    enclosure_source = stair_model.get("enclosure")
    enclosure_x0 = (
        _number(enclosure_source.get("x0")) if isinstance(enclosure_source, dict) else None
    )
    p2_access_matches = (
        isinstance(p2_access, dict)
        and door_x is not None
        and door_y0 is not None
        and door_y1 is not None
        and door_width is not None
        and _number(p2_access.get("door_y0")) is not None
        and _number(p2_access.get("door_width")) is not None
        and _number(upper.get("y0")) is not None
        and _number(upper.get("y1")) is not None
        and enclosure_x0 is not None
        and _number(door_geometry.get("z0")) is not None
        and math.isclose(door_y0, _number(p2_access.get("door_y0")), abs_tol=_TOL)
        and math.isclose(door_y1 - door_y0, _number(p2_access.get("door_width")), abs_tol=_TOL)
        and math.isclose(door_width, _number(p2_access.get("door_width")), abs_tol=_TOL)
        and math.isclose(door_x, enclosure_x0, abs_tol=_TOL)
        and door_y0 >= _number(upper.get("y0")) - _TOL
        and door_y1 <= _number(upper.get("y1")) + _TOL
        and math.isclose(_number(door_geometry.get("z0")), p2, abs_tol=_TOL)
    )
    if not p2_access_matches:
        source_consistent = False
    evidence = {
        "calculation_state": "measured" if source_consistent else "invalid_or_incomplete",
        "source_revision": stair_model.get("revision"),
        "levels_m": {"PB": pb, "intermediate_landing": landing, "P2": p2},
        "flight_risers": list(risers_by_flight),
        "total_risers": total_risers,
        "riser_height_m": riser_height,
        "riser_height_mm": 1000.0 * riser_height if riser_height is not None else None,
        "flight_rise_m": per_flight_rise,
        "treads_per_flight": list(treads_by_flight),
        "going_m": going,
        "flight_plan_run_m": runs,
        "normalized_flight_plan_run_m": geometry_flight_runs,
        "flight_run_geometry_matches_treads": flight_runs_match,
        "landing_plan_bounds_m": {
            "x0": landing_x0,
            "x1": landing_x1,
            "depth_m": landing_depth_geometry,
            "source_depth_m": landing_depth_source,
            "joins_both_flight_ends": landing_intersection_matches,
        },
        "two_risers_plus_going_m": 2.0 * riser_height + going if riser_height is not None else None,
        "normalized_stair_entities": stair_entities,
        "p2_access_opening": {
            "entity_id": "D-STAIR",
            "geometry_y_m": [door_y0, door_y1],
            "source_access_platform": deepcopy(p2_access),
            "opening_matches_p2_access_reservation": p2_access_matches,
        },
        "levels_and_flights_reconcile": source_consistent,
        "required_inputs_missing": []
        if source_consistent
        else [
            "current normalized flight/door geometry does not reconcile with SC-01 source levels/access platform"
        ],
        "next_evidence_required": [
            "longitudinal/transverse stair sections, nosing and headroom verification",
            "resolved finish build-ups, nosings, guards, handrails and fire/smoke design",
            "responsible professional review against the applicable code basis",
        ],
    }
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "SC01-CROSS-LEVEL-DATUMS",
        "PASS" if source_consistent else "FAIL",
        "evaluated",
        (
            f"SC-01 datum arithmetic reconciles PB {pb:.2f} m, landing {landing:.2f} m and P2 {p2:.2f} m "
            f"with {total_risers} source risers. This is coordination arithmetic only."
            if source_consistent
            else "Current SC-01 cross-level or P2 access-opening data are inconsistent; no stair compliance conclusion is drawn."
        ),
        ("ST-F1", "ST-F2", "ST-L1", "D-STAIR"),
        evidence,
    )

    conflict = next(
        (
            item
            for item in stair_model.get("open_conflicts", [])
            if isinstance(item, dict) and item.get("id") == "CF-011"
        ),
        None,
    )
    rear_door = entities.get("EXT-ESC")
    rear_level = _number(conflict.get("rear_door_level")) if conflict else None
    landing_at_door = (
        _number(conflict.get("landing_level_at_rear_door_plane")) if conflict else None
    )
    mismatch = landing_at_door - rear_level if None not in (rear_level, landing_at_door) else None
    discharge = {
        "conflict_id": "CF-011",
        "rear_door_id": conflict.get("rear_door_id") if conflict else "EXT-ESC",
        "rear_door_level_m": rear_level,
        "landing_level_at_rear_door_plane_m": landing_at_door,
        "level_difference_m": mismatch,
        "rear_door_geometry_shape": rear_door.get("geometry", {}).get("shape")
        if rear_door
        else None,
        "rear_door_source_y_m": _number(rear_door.get("parameters", {}).get("source_y"))
        if rear_door
        else None,
        "rear_door_width_m": _number(rear_door.get("parameters", {}).get("width_m"))
        if rear_door
        else None,
        "discharge_resolved": False,
        "required_inputs_missing": [
            "resolved EXT-ESC plan anchor and clear width/height",
            "sectioned landing-to-exterior route",
            "professionally reviewed and selected discharge alternative",
        ],
    }
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "SC01-REAR-DISCHARGE-RELATIONSHIP",
        "OPEN",
        "evaluated" if conflict and rear_door else "unsupported",
        (
            f"CF-011 remains open: the captured rear-door level is {rear_level:.2f} m while the landing at that plane is "
            f"{landing_at_door:.2f} m; EXT-ESC geometry is {discharge['rear_door_geometry_shape']}."
            if mismatch is not None
            else "CF-011 is not fully represented by current source context; rear discharge remains unresolved."
        ),
        ("EXT-ESC", "ST-L1"),
        discharge,
    )

    raw_structural_source = stair_model.get("structure")
    structural_source = raw_structural_source if isinstance(raw_structural_source, dict) else {}
    raw_code_screen = stair_model.get("code_screen")
    code_screen = raw_code_screen if isinstance(raw_code_screen, dict) else {}
    unresolved = {
        "selected_member_sections": structural_source.get("member_sections_selected") is not True,
        "landing_beam_restraints": structural_source.get(
            "landing_beams_as_column_restraints_resolved"
        )
        is not True,
        "connections_bases_foundations": structural_source.get(
            "connections_bases_foundations_fire_resolved"
        )
        is not True,
        "headroom": code_screen.get("headroom_verified") is not True,
        "guard_handrail_fire_smoke": code_screen.get("guard_handrail_fire_smoke_verified")
        is not True,
    }
    structural = {
        "source_column_reservations": deepcopy(structural_source.get("column_reservations", [])),
        "member_sections_selected": structural_source.get("member_sections_selected") is True,
        "unresolved_interfaces": unresolved,
        "engineering_status": "not evaluated",
        "required_inputs_missing": _RULE_DEFINITIONS["SC01-STRUCTURAL-INTERFACE-COVERAGE"][
            "required_data"
        ],
    }
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "SC01-STRUCTURAL-INTERFACE-COVERAGE",
        "OPEN",
        "evaluated",
        "SC-01 retains plan-level column reservations; selected member, support, connection, headroom and professional evidence are absent.",
        tuple(
            item.get("id")
            for item in structural_source.get("column_reservations", [])
            if isinstance(item, dict)
        )
        if isinstance(structural_source.get("column_reservations", []), list)
        else (),
        structural,
    )
    return {
        "cross_level": evidence,
        "rear_discharge": discharge,
        "structural_interfaces": structural,
    }


def _service_records(
    snapshot: dict[str, Any],
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    inputs = snapshot.get("discipline_inputs")
    equipment = inputs.get("equipment") if isinstance(inputs, dict) else None
    pb = equipment.get("pb") if isinstance(equipment, dict) else None
    if not isinstance(pb, dict):
        missing = [
            _source_ref("equipment", "pb", "built_in_benches"),
            _source_ref("equipment", "pb", "kitchen", "service_strategy"),
        ]
        evidence = {
            "calculation_state": "unsupported",
            "bench_reservations": [],
            "support_equipment_clearances": [],
            "required_inputs_missing": missing,
            "next_evidence_required": _RULE_DEFINITIONS["PB-SERVICE-OPERATING-RESERVATIONS"][
                "required_data"
            ],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "PB-SERVICE-OPERATING-RESERVATIONS",
            "OPEN",
            "unsupported",
            "Current PB service/bench source context is missing.",
            evidence=evidence,
        )
        route_evidence = {
            "strategy_statements": [],
            "route_geometry": None,
            "service_points": None,
            "required_inputs_missing": [
                _RULE_DEFINITIONS["PB-SERVICE-ROUTE-COVERAGE"]["required_data"]
            ],
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "PB-SERVICE-ROUTE-COVERAGE",
            "OPEN",
            "unsupported",
            "Current PB services source context is missing.",
            evidence=route_evidence,
        )
        return {"operating_reservations": evidence, "routes": route_evidence}

    benches_raw = pb.get("built_in_benches")
    benches_raw = benches_raw if isinstance(benches_raw, list) else []
    benches: list[dict[str, Any]] = []
    missing: list[str] = []
    for bench in benches_raw:
        if not isinstance(bench, dict) or not isinstance(bench.get("id"), str):
            missing.append("built-in bench source row has no identity")
            continue
        values = {
            key: _number(bench.get(key))
            for key in (
                "x0",
                "y0",
                "length",
                "depth",
                "operating_strip_y0",
                "operating_strip_y1",
                "operating_strip_depth",
            )
        }
        if any(value is None for value in values.values()):
            missing.append(f"bench {bench['id']} has incomplete plan bounds or operating strip")
            continue
        x1 = values["x0"] + values["length"]
        bench_y1 = values["y0"] + values["depth"]
        side = bench.get("mounting")
        if side == "side_a_perimeter":
            adjacent = math.isclose(values["operating_strip_y0"], bench_y1, abs_tol=_TOL)
        elif side == "side_b_perimeter":
            adjacent = math.isclose(values["operating_strip_y1"], values["y0"], abs_tol=_TOL)
        else:
            adjacent = False
            missing.append(f"bench {bench['id']} mounting orientation is unsupported")
        strip_width = values["operating_strip_y1"] - values["operating_strip_y0"]
        longitudinal = math.isclose(strip_width, values["operating_strip_depth"], abs_tol=_TOL)
        record = {
            "source_asset_id": bench["id"],
            "mounting": side,
            "bench_plan_bounds_m": {
                "x0": values["x0"],
                "x1": x1,
                "y0": values["y0"],
                "y1": bench_y1,
            },
            "operating_strip_bounds_m": {
                "x0": values["x0"],
                "x1": x1,
                "y0": values["operating_strip_y0"],
                "y1": values["operating_strip_y1"],
            },
            "operating_strip_area_m2": values["length"] * strip_width,
            "strip_depth_m": strip_width,
            "bench_strip_adjacency_matches_source": adjacent,
            "strip_depth_matches_declared_depth": longitudinal,
            "reservation_state": "source design reservation",
            "installed_state": "unknown",
            "tested_state": "unknown",
            "commissioned_state": "unknown",
            "support_specification": bench.get("support_family"),
        }
        benches.append(record)
        if not adjacent or not longitudinal:
            missing.append(
                f"bench {bench['id']} operating strip does not reconcile with its source bounds"
            )

    rc_bench = next((row for row in benches if row.get("source_asset_id") == "PB-BENCH-RC"), None)
    support_equipment = pb.get("rc_support_equipment")
    separation_rule = None
    if isinstance(support_equipment, dict) and isinstance(support_equipment.get("reason"), str):
        match = re.search(
            r"at least\s+([0-9]+(?:\.[0-9]+)?)\s*m",
            support_equipment["reason"],
            flags=re.IGNORECASE,
        )
        separation_rule = float(match.group(1)) if match else None
    if separation_rule is None:
        missing.append(
            "source does not provide a structured numeric support-equipment clearance criterion"
        )
    clearance_rows: list[dict[str, Any]] = []
    if rc_bench and isinstance(support_equipment, dict):
        bench_rect = rc_bench["bench_plan_bounds_m"]
        for equipment_id in ("printer_zone", "lipo_zone"):
            zone = support_equipment.get(equipment_id)
            if not isinstance(zone, dict):
                missing.append(f"PB support-equipment envelope {equipment_id} is missing")
                continue
            x, y, w, d = (_number(zone.get(key)) for key in ("x", "y", "w", "d"))
            if None in (x, y, w, d) or w <= 0 or d <= 0:
                missing.append(
                    f"PB support-equipment envelope {equipment_id} has invalid plan bounds"
                )
                continue
            overlap_x = min(bench_rect["x1"], x + w) - max(bench_rect["x0"], x)
            if overlap_x <= _TOL:
                missing.append(
                    f"PB support-equipment envelope {equipment_id} does not overlap RC bench longitudinally; clearance axis cannot be inferred"
                )
                gap = None
            else:
                gap = bench_rect["y0"] - (y + d)
            clearance_rows.append(
                {
                    "source_asset_id": equipment_id,
                    "zone_bounds_m": {"x0": x, "x1": x + w, "y0": y, "y1": y + d},
                    "overlap_with_bench_in_x_m": max(0.0, overlap_x),
                    "plan_gap_to_bench_m": gap,
                    "source_stated_minimum_m": separation_rule,
                    "meets_source_stated_minimum": gap is not None
                    and separation_rule is not None
                    and gap + _TOL >= separation_rule,
                }
            )
    clearance_valid = (
        bool(clearance_rows)
        and separation_rule is not None
        and all(item["plan_gap_to_bench_m"] is not None for item in clearance_rows)
    )
    clearance_fails = any(
        item["plan_gap_to_bench_m"] is not None
        and item["source_stated_minimum_m"] is not None
        and item["plan_gap_to_bench_m"] + _TOL < item["source_stated_minimum_m"]
        for item in clearance_rows
    )
    operating_valid = not missing and len(benches) == len(benches_raw) and clearance_valid
    operating = {
        "calculation_state": "measured" if operating_valid else "invalid_or_incomplete",
        "bench_reservations": benches,
        "support_equipment_clearances": clearance_rows,
        "required_inputs_missing": missing,
        "next_evidence_required": [
            "selected workbench/rail product dimensions, installed mass and support reactions",
            "anchorage and secondary-steel design and connections",
            "current service-point locations and access/maintenance routes",
            "installation, inspection and acceptance records",
        ],
    }
    status = "FAIL" if clearance_fails else "OPEN"
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "PB-SERVICE-OPERATING-RESERVATIONS",
        status,
        "evaluated" if benches or clearance_rows else "unsupported",
        (
            "PB workbench operating strips and support-equipment plan gaps reconcile with their source reservations; installation and support design remain open."
            if operating_valid and not clearance_fails
            else "PB workbench/service reservation geometry is incomplete or conflicts with a numerical source clearance; no installation approval is implied."
        ),
        (),
        operating,
    )

    kitchen = pb.get("kitchen") if isinstance(pb.get("kitchen"), dict) else {}
    strategy = kitchen.get("service_strategy")
    route = {
        "strategy_statements": [strategy] if isinstance(strategy, str) and strategy.strip() else [],
        "wall_run_bounds_m": deepcopy(kitchen.get("wall_run")),
        "island_reservation_m": deepcopy(kitchen.get("island")),
        "route_geometry": None,
        "service_point_coordinates": None,
        "route_status": "not supplied by captured source",
        "required_inputs_missing": [
            "water and drainage route centerlines, points, gradients and isolation locations",
            "extraction duct route/termination, fan and access/cleaning points",
            "island power/data points, loads, circuits and service connection details",
            "selected fixture/equipment connection data and maintenance access",
        ],
        "next_evidence_required": _RULE_DEFINITIONS["PB-SERVICE-ROUTE-COVERAGE"]["required_data"],
    }
    strategy_available = bool(route["strategy_statements"])
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "PB-SERVICE-ROUTE-COVERAGE",
        "OPEN",
        "evaluated" if strategy_available else "unsupported",
        (
            "PB kitchen service intent is captured, but the source contains no routed, sized or located service points."
            if strategy_available
            else "No current PB service strategy is available in the resolved source context."
        ),
        (),
        route,
    )
    return {"operating_reservations": operating, "routes": route}


def _maintenance_records(
    snapshot: dict[str, Any],
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    inputs = snapshot.get("discipline_inputs")
    equipment = inputs.get("equipment") if isinstance(inputs, dict) else None
    pb = equipment.get("pb") if isinstance(equipment, dict) else None
    structure = _structure_sources(snapshot)
    roof_context = structure.get("rooflights")
    entities = _entities(snapshot)
    assets: list[dict[str, Any]] = []
    missing: list[str] = []
    if isinstance(roof_context, dict) and isinstance(roof_context.get("rooflights"), list):
        for item in roof_context["rooflights"]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                missing.append("rooflight source row has no ID")
                continue
            identifier = item["id"]
            entity = entities.get(identifier)
            if entity is None or entity.get("kind") != "opening":
                missing.append(f"normalized rooflight opening {identifier} is missing")
            assets.append(
                {
                    "source_asset_id": identifier,
                    "normalized_entity_id": identifier if entity is not None else None,
                    "source_ref": _source_ref("structure", "rooflights", "rooflights"),
                    "source_status": roof_context.get("status"),
                    "reservation_state": "coordination hypothesis",
                    "installed_state": "unknown",
                    "tested_state": "unknown",
                    "commissioned_state": "unknown",
                    "maintenance_intervals": None,
                    "source_open_maintenance_items": list(roof_context.get("open_items", [])),
                }
            )
    if isinstance(pb, dict):
        for item in pb.get("built_in_benches", []):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                continue
            assets.append(
                {
                    "source_asset_id": item["id"],
                    "normalized_entity_id": None,
                    "source_ref": _source_ref("equipment", "pb", "built_in_benches"),
                    "source_status": item.get("reservation"),
                    "reservation_state": "source design reservation",
                    "installed_state": "unknown",
                    "tested_state": "unknown",
                    "commissioned_state": "unknown",
                    "replaceable_module_count": item.get("module_count"),
                    "maintenance_intervals": None,
                    "source_open_maintenance_items": [],
                }
            )
    ids = tuple(
        sorted(
            {item["normalized_entity_id"] for item in assets if item.get("normalized_entity_id")}
        )
    )
    supported = bool(assets) and not missing
    evidence = {
        "calculation_state": "recorded_source_assets" if supported else "unsupported_or_incomplete",
        "assets": assets,
        "lifecycle_vocabulary": [
            "reserved",
            "installed",
            "tested",
            "commissioned",
            "maintained",
            "decommissioned",
        ],
        "recorded_lifecycle_events": [],
        "required_inputs_missing": missing,
        "next_evidence_required": _RULE_DEFINITIONS["ASSET-MAINTENANCE-RECORD-COVERAGE"][
            "required_data"
        ],
    }
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "ASSET-MAINTENANCE-RECORD-COVERAGE",
        "OPEN",
        "evaluated" if supported else "unsupported",
        "Source rooflight/bench reservations are recorded; no installed, tested, commissioned or maintenance events are captured.",
        ids,
        evidence,
    )
    return evidence


def _coverage_summary(
    findings: list[dict[str, Any]], coverage_rows: dict[str, dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    definitions = deepcopy(_RULE_DEFINITIONS)
    rules = []
    totals = {state: 0 for state in _COVERAGE_STATES}
    for rule_id in sorted(definitions):
        row = coverage_rows.get(
            rule_id,
            {
                "counts": {state: 0 for state in _COVERAGE_STATES},
                "entity_ids": {state: set() for state in _COVERAGE_STATES},
            },
        )
        if not any(row["counts"].values()):
            row["counts"]["not_run"] = 1
        for state in _COVERAGE_STATES:
            totals[state] += row["counts"][state]
        rules.append(
            {
                "rule_id": rule_id,
                **definitions[rule_id],
                "counts": dict(row["counts"]),
                "entity_ids_by_coverage": {
                    state: sorted(row["entity_ids"][state]) for state in _COVERAGE_STATES
                },
            }
        )
    findings.sort(key=lambda item: (item["rule_id"], item["finding_id"]))
    return {"totals": totals, "rules": rules}, [
        {"rule_id": rule_id, **definition} for rule_id, definition in sorted(definitions.items())
    ]


def evaluate_extensions(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Calculate supported wall, stair, phase, service and maintenance records."""
    findings: list[dict[str, Any]] = []
    coverage_rows: dict[str, dict[str, Any]] = {}
    wall_schedule = {
        "exterior": _exterior_wall_schedule(snapshot, findings, coverage_rows),
        "same_suite_dry_boundary_candidates": _dry_boundary_candidates(
            snapshot, findings, coverage_rows
        ),
        "hall_edge": _hall_edge_lengths(snapshot, findings, coverage_rows),
    }
    stair_relationships = _stair_relationships(snapshot, findings, coverage_rows)
    phase_reservations = _phase_reservations(snapshot, findings, coverage_rows)
    service_interfaces = _service_records(snapshot, findings, coverage_rows)
    maintenance = _maintenance_records(snapshot, findings, coverage_rows)
    coverage, registry = _coverage_summary(findings, coverage_rows)
    return {
        "findings": findings,
        "coverage": coverage,
        "rule_registry": registry,
        "extensions": {
            "wall_schedule": wall_schedule,
            "stair_relationships": stair_relationships,
            "phase_reservations": phase_reservations,
            "service_interfaces": service_interfaces,
            "maintenance": maintenance,
        },
    }


__all__ = ["evaluate_extensions"]

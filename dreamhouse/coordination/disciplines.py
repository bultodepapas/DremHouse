"""Pure adapters that apply existing discipline checks to a resolved snapshot.

The adapters never load repository files. Legacy dictionaries are copied from the
resolver context, then current entity geometry is overlaid before an existing pure
check is called. Discipline coverage stays separate from the geometric findings in
``rules`` and from professional approval.
"""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

from dreamhouse.architecture.program import evaluate_room_program
from dreamhouse.equipment.models import EquipmentCatalog, ProductEnvelope
from dreamhouse.equipment.validators import validate_equipment
from dreamhouse.structure.vertical_continuity import evaluate_current_support_line_plan

_COVERAGE_STATES = ("evaluated", "unsupported", "inapplicable", "not_run")
_PROGRAM_RULES = (
    "PROGRAM-PRIMARY-BATH-17",
    "PROGRAM-PRIMARY-CLOSET-15",
    "PROGRAM-PRIMARY-TOTAL-75",
)

_RULE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "PROGRAM-PRIMARY-BATH-17": {
        "description": "Compare tagged primary-bath components with the recorded 17 m2 study target.",
        "required_data": ["P2 space identity", "suite and kind tags", "rectangular plan bounds"],
        "limits": ["Tagged component area is not a surveyed boundary or net-area certification."],
    },
    "PROGRAM-PRIMARY-CLOSET-15": {
        "description": "Compare tagged primary-closet components with the recorded 15 m2 study target.",
        "required_data": ["P2 space identity", "suite and kind tags", "rectangular plan bounds"],
        "limits": ["Tagged component area is not a surveyed boundary or net-area certification."],
    },
    "PROGRAM-PRIMARY-TOTAL-75": {
        "description": "Expose the 75 m2 owner target and the unresolved gross/net measurement basis.",
        "required_data": [
            "all tagged primary-suite space bounds",
            "owner-approved gross/net measurement basis",
        ],
        "limits": ["Shared circulation is excluded and no boundary survey is represented."],
    },
    "WORKSTATION-WINDOW-DATUM": {
        "description": "Check each workstation opening span and sill against its current workstation zone and worktop datum.",
        "required_data": [
            "current window bounds and sill",
            "workstation zone bounds",
            "worktop height",
        ],
        "limits": [
            "This checks the adopted schematic datum only; it is not a glazing or structural design check."
        ],
    },
    "EQUIPMENT-BENCHMARK-LAYOUT-APPLICABILITY": {
        "description": "State that equipment geometry checks use an unadopted benchmark layout.",
        "required_data": [
            "current room geometry",
            "versioned equipment catalogue",
            "versioned placement hypothesis",
            "owner-selected products and positions",
        ],
        "limits": [
            "Benchmark fit results are evidence about the stated layout, not selected-product clearance approval."
        ],
    },
    "EQUIPMENT-LIFT-SELECTION-COVERAGE": {
        "description": "Expose the schematic car-lift envelope while actual lift selection remains unknown.",
        "required_data": [
            "manufacturer and model",
            "installed dimensions and post/arm geometry",
            "operating envelope",
            "support reactions and anchorage",
        ],
        "limits": [
            "A schematic envelope and post pair do not establish a selected lift or slab design."
        ],
    },
    "EQUIPMENT-MASS-COVERAGE": {
        "description": "Expose missing installed equipment masses for structural coordination.",
        "required_data": [
            "selected product and installed mass for each equipment item",
            "lift and vehicle support reactions",
        ],
        "limits": [
            "Catalogue envelopes contain dimensions, not a complete installed-mass schedule."
        ],
    },
    "EQUIPMENT-ENGINEERING-COVERAGE": {
        "description": "Keep equipment support, services, anchorage, and professional checks open.",
        "required_data": [
            "verified support reactions",
            "slab and anchorage design",
            "service and operating requirements",
            "professional review",
        ],
        "limits": ["No equipment engineering capacity check is performed by this adapter."],
    },
    "STRUCTURE-CURRENT-SNAPSHOT-COVERAGE": {
        "description": "Require structural evidence tied to the evaluated resolved-model fingerprint.",
        "required_data": [
            "structural analysis input fingerprint equal to the current model hash",
            "current loads and selected members",
            "current connection/support design",
        ],
        "limits": [
            "Archived E0/E1 screening outputs are not recalculated or represented as results for this snapshot."
        ],
    },
    "STRUCTURE-VERTICAL-CONTINUITY-COVERAGE": {
        "description": "Expose the gap between plan-only support reservations and a current vertical continuity check.",
        "required_data": [
            "selected column identities and sections",
            "verified vertical extents",
            "current window and door extents",
            "current stair and landing interfaces",
        ],
        "limits": [
            "Plan reservations are not structural members; this adapter does not claim three-dimensional clearance."
        ],
    },
    "STRUCTURE-SUPPORT-LINE-PLAN-INTERACTION": {
        "description": "Compare current candidate support lines with enrolled room and window/door plan geometry.",
        "required_data": [
            "source support-line coordinates",
            "current room bounds",
            "current window and door bounds",
        ],
        "limits": [
            "A plan comparison is not a selected-column check; member size, vertical overlap, capacity, and connections remain unknown."
        ],
    },
    "STRUCTURE-MASS-COVERAGE": {
        "description": "Expose missing current element and assembly masses for structural load take-down.",
        "required_data": [
            "selected wall assemblies and mass per area",
            "installed equipment masses",
            "member schedule",
            "verified dead loads",
        ],
        "limits": [
            "Hypothetical surface loads or trial sections are not treated as measured project mass."
        ],
    },
    "STRUCTURE-ENGINEERING-COVERAGE": {
        "description": "Keep site-specific structural actions and professional design checks visible.",
        "required_data": [
            "site and geotechnical data",
            "normative wind/seismic/rain actions",
            "member stability and connections",
            "foundations and fire design",
            "responsible engineer review",
        ],
        "limits": ["No structural design calculation or approval is performed by this adapter."],
    },
    "STRUCTURE-LIFT-LOAD-COVERAGE": {
        "description": "Distinguish a preliminary lift-load hypothesis from actual equipment reactions.",
        "required_data": [
            "selected lift model",
            "manufacturer support reactions",
            "anchor layout",
            "slab and foundation verification",
        ],
        "limits": ["A load hypothesis is not an adopted design action or verified equipment load."],
    },
}


def _entity_map(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = snapshot.get("entities", {})
    if not isinstance(raw, dict):
        return {}
    return {
        str(value.get("id", key)): value for key, value in raw.items() if isinstance(value, dict)
    }


def _id(rule_id: str, entity_ids: tuple[str, ...]) -> str:
    return f"{rule_id}:" + ":".join(sorted(set(entity_ids)))


def _finite(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _record_coverage(
    coverage_rows: dict[str, dict[str, Any]],
    rule_id: str,
    state: str,
    entity_ids: tuple[str, ...] = (),
) -> None:
    if state not in _COVERAGE_STATES:
        raise ValueError(f"Unknown discipline coverage state: {state}")
    row = coverage_rows.setdefault(
        rule_id,
        {
            "counts": {item: 0 for item in _COVERAGE_STATES},
            "entity_ids": {item: set() for item in _COVERAGE_STATES},
        },
    )
    row["counts"][state] += 1
    row["entity_ids"][state].update(entity_ids)


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
    finding_suffix: str | None = None,
) -> dict[str, Any]:
    entities = _entity_map(snapshot)
    normalized_ids = tuple(sorted({item for item in entity_ids if item in entities}))
    finding = {
        "finding_id": _id(rule_id, normalized_ids)
        + (f":{finding_suffix}" if finding_suffix else ""),
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
    _record_coverage(coverage_rows, rule_id, coverage, normalized_ids)
    return finding


def _overlay_p2(
    snapshot: dict[str, Any], p2_source: object
) -> tuple[dict[str, Any] | None, tuple[str, ...], str | None]:
    """Project registered P2 spaces/windows into a copy of the resolved legacy model."""
    if not isinstance(p2_source, dict):
        return None, (), "Resolver did not provide the current P2 source context."
    p2 = deepcopy(p2_source)
    if not isinstance(p2.get("spaces"), list):
        return None, (), "Current P2 source has no usable space list."
    entities = _entity_map(snapshot)
    registered_spaces = {
        identifier: entity
        for identifier, entity in entities.items()
        if entity.get("kind") == "space" and entity.get("level") == "P2"
    }
    source_ids = {str(item.get("id")) for item in p2["spaces"] if isinstance(item, dict)}
    if not source_ids or source_ids != set(registered_spaces):
        return (
            None,
            tuple(sorted(registered_spaces)),
            "P2 source spaces and normalized snapshot identities do not agree.",
        )

    for space in p2["spaces"]:
        entity = registered_spaces[str(space["id"])]
        geometry = entity.get("geometry")
        parameters = entity.get("parameters")
        if not isinstance(geometry, dict) or geometry.get("shape") != "rect":
            return (
                None,
                tuple(sorted(registered_spaces)),
                f"{space['id']} has unsupported P2 space geometry.",
            )
        x0, x1, y0, y1 = (_finite(geometry.get(key)) for key in ("x0", "x1", "y0", "y1"))
        if None in (x0, x1, y0, y1) or x1 <= x0 or y1 <= y0:
            return (
                None,
                tuple(sorted(registered_spaces)),
                f"{space['id']} has incomplete or nonpositive P2 bounds.",
            )
        if (
            not isinstance(parameters, dict)
            or "suite" not in parameters
            or not parameters.get("space_kind")
        ):
            return (
                None,
                tuple(sorted(registered_spaces)),
                f"{space['id']} lacks current suite/kind tags.",
            )
        space.update(
            x=x0,
            y=y0,
            w=x1 - x0,
            d=y1 - y0,
            suite=parameters["suite"],
            kind=parameters["space_kind"],
        )

    for collection in ("windows", "doors"):
        records = p2.get(collection)
        if not isinstance(records, list):
            continue
        for record in records:
            entity = entities.get(str(record.get("id")))
            if (
                not entity
                or entity.get("level") != "P2"
                or entity.get("kind") not in {"opening", "door"}
            ):
                continue
            parameters = entity.get("parameters")
            if not isinstance(parameters, dict):
                continue
            if collection == "windows":
                start = _finite(parameters.get("start_m"))
                width = _finite(parameters.get("width_m"))
                if start is not None and width is not None:
                    record["from"], record["to"] = start, start + width
                for source_name, target_name in (
                    ("height_m", "height"),
                    ("sill_m", "sill"),
                    ("modules", "modules"),
                ):
                    if parameters.get(source_name) is not None:
                        record[target_name] = parameters[source_name]
                facade = parameters.get("facade")
                edge = {"A": "south", "B": "north", "REAR": "east"}.get(facade)
                if edge:
                    record["edge"] = edge
            else:
                for source_name, target_name in (
                    ("width_m", "width"),
                    ("start_m", "at"),
                    ("door_kind", "kind"),
                    ("swing", "swing"),
                ):
                    if parameters.get(source_name) is not None:
                        record[target_name] = parameters[source_name]
    return p2, tuple(sorted(registered_spaces)), None


def _evaluate_programme(
    snapshot: dict[str, Any],
    p2: dict[str, Any] | None,
    space_ids: tuple[str, ...],
    error: str | None,
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if p2 is None:
        result = {
            "status": "OPEN",
            "checks": [],
            "suite_component_areas_m2": {},
            "measurement_warning": error,
        }
        for rule_id in _PROGRAM_RULES:
            _emit(
                findings,
                coverage_rows,
                snapshot,
                rule_id,
                "OPEN",
                "unsupported",
                error or "Current programme inputs are unsupported.",
                space_ids,
                {
                    "required_data": _RULE_DEFINITIONS[rule_id]["required_data"],
                    "missing_or_unsupported": error,
                },
            )
        return result

    result = evaluate_room_program(p2)
    check_by_id = {item["rule_id"]: item for item in result["checks"]}
    spaces = p2["spaces"]
    primary_bath_m2 = round(
        sum(
            float(item["w"]) * float(item["d"])
            for item in spaces
            if item.get("suite") == "M" and item.get("kind") == "bath"
        ),
        2,
    )
    primary_closet_m2 = round(
        sum(
            float(item["w"]) * float(item["d"])
            for item in spaces
            if item.get("suite") == "M" and item.get("kind") == "closet"
        ),
        2,
    )
    primary_ids = tuple(item["id"] for item in spaces if item.get("suite") == "M")
    evidence_by_rule = {
        "PROGRAM-PRIMARY-BATH-17": {
            "measured_area_m2": primary_bath_m2,
            "study_target_m2": 17.0,
            "measurement_basis": "tagged components",
        },
        "PROGRAM-PRIMARY-CLOSET-15": {
            "measured_area_m2": primary_closet_m2,
            "study_target_m2": 15.0,
            "measurement_basis": "tagged components",
        },
        "PROGRAM-PRIMARY-TOTAL-75": {
            "measured_area_m2": result["suite_component_areas_m2"].get("M", 0.0),
            "owner_target_m2": 75.0,
            "measurement_basis": "tagged components; shared circulation excluded",
            "gross_net_basis_resolved": False,
        },
    }
    for rule_id in _PROGRAM_RULES:
        check = check_by_id.get(rule_id)
        if check is None:
            # The legacy check emits only an OPEN total-area item below its target.
            # Preserve that behaviour while showing that its input was evaluated.
            _record_coverage(coverage_rows, rule_id, "evaluated", primary_ids)
            continue
        if rule_id == "PROGRAM-PRIMARY-CLOSET-15":
            rebalance = p2.get("primary_suite_rebalance")
            current_area = (
                _finite(rebalance.get("dressing_gross_area_m2"))
                if isinstance(rebalance, dict)
                else None
            )
            if current_area is not None:
                aligned = math.isclose(primary_closet_m2, current_area, abs_tol=0.01, rel_tol=0.0)
                _emit(
                    findings,
                    coverage_rows,
                    snapshot,
                    rule_id,
                    "OPEN",
                    "inapplicable" if aligned else "evaluated",
                    (
                        f"The legacy 15 m2 closet study target is not the current adopted spatial basis; "
                        f"the P2 rebalance source records {current_area:.2f} m2 gross and the resolved "
                        f"tagged area is {primary_closet_m2:.2f} m2. No new closet minimum is asserted."
                        if aligned
                        else f"The current study measures {primary_closet_m2:.2f} m2 against its recorded "
                        f"{current_area:.2f} m2 dressing basis; review this study change without applying "
                        "the superseded 15 m2 benchmark as a requirement."
                    ),
                    tuple(check.get("entity_ids", ())),
                    {
                        **evidence_by_rule[rule_id],
                        "legacy_check": check,
                        "legacy_target_applicable": False,
                        "current_criterion_source": "P2 primary_suite_rebalance.dressing_gross_area_m2",
                        "current_criterion_area_m2": current_area,
                        "current_basis_matches_resolved_area": aligned,
                        "required_data": _RULE_DEFINITIONS[rule_id]["required_data"],
                    },
                )
                continue
        status = check["status"]
        entity_ids = tuple(check.get("entity_ids", ()))
        if rule_id == "PROGRAM-PRIMARY-CLOSET-15" and status == "FAIL":
            # Without an explicit current criterion, an old study target cannot be
            # promoted to a binding requirement by this adapter.
            status = "OPEN"
        _emit(
            findings,
            coverage_rows,
            snapshot,
            rule_id,
            status,
            "evaluated",
            check["message"],
            entity_ids,
            {
                **evidence_by_rule[rule_id],
                "legacy_check": check,
                "required_data": _RULE_DEFINITIONS[rule_id]["required_data"],
            },
        )
    return result


def _evaluate_workstation_datums(
    snapshot: dict[str, Any],
    pb: object,
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    entities = _entity_map(snapshot)
    workstations = pb.get("workstations") if isinstance(pb, dict) else None
    if not isinstance(workstations, list):
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "WORKSTATION-WINDOW-DATUM",
            "OPEN",
            "unsupported",
            "Current PB workstation source data is unavailable.",
            (),
            {"required_data": _RULE_DEFINITIONS["WORKSTATION-WINDOW-DATUM"]["required_data"]},
        )
        return []

    details = []
    for workstation in workstations:
        window_id = str(workstation.get("window_id", ""))
        window = entities.get(window_id)
        if not window or not isinstance(window.get("geometry"), dict):
            _emit(
                findings,
                coverage_rows,
                snapshot,
                "WORKSTATION-WINDOW-DATUM",
                "OPEN",
                "unsupported",
                f"{workstation.get('id', 'Workstation')} has no normalized linked window.",
                (),
                {
                    "workstation_source_id": workstation.get("id"),
                    "window_source_id": window_id,
                    "missing_or_unsupported": "normalized linked window",
                },
            )
            continue
        geometry = window["geometry"]
        parameters = window.get("parameters") or {}
        width = _finite(parameters.get("width_m"))
        sill = _finite(parameters.get("sill_m"))
        worktop = _finite(workstation.get("worktop_height"))
        zone_x0 = _finite(workstation.get("zone_x0"))
        zone_x1 = _finite(workstation.get("zone_x1"))
        bounds = [_finite(geometry.get(key)) for key in ("x0", "x1")]
        expected_width = zone_x1 - zone_x0 if zone_x0 is not None and zone_x1 is not None else None
        if None in (width, sill, worktop, expected_width, *bounds) or expected_width <= 0:
            _emit(
                findings,
                coverage_rows,
                snapshot,
                "WORKSTATION-WINDOW-DATUM",
                "OPEN",
                "unsupported",
                f"{workstation.get('id', window_id)} lacks a finite worktop, sill, or opening-span datum.",
                (window_id,),
                {
                    "workstation_source_id": workstation.get("id"),
                    "window_source_id": window_id,
                    "worktop_height_m": worktop,
                    "sill_m": sill,
                    "opening_width_m": width,
                    "zone_width_m": expected_width,
                    "required_data": _RULE_DEFINITIONS["WORKSTATION-WINDOW-DATUM"]["required_data"],
                },
            )
            continue
        sill_ok = math.isclose(sill, worktop, abs_tol=1e-6, rel_tol=0.0)
        width_ok = math.isclose(width, expected_width, abs_tol=1e-6, rel_tol=0.0)
        bounds_ok = math.isclose(bounds[0], zone_x0, abs_tol=1e-6, rel_tol=0.0) and math.isclose(
            bounds[1], zone_x1, abs_tol=1e-6, rel_tol=0.0
        )
        passed = sill_ok and width_ok and bounds_ok
        evidence = {
            "workstation_source_id": workstation.get("id"),
            "window_entity_id": window_id,
            "window_source": window.get("working_source") or window.get("source"),
            "sill_m": sill,
            "worktop_height_m": worktop,
            "opening_width_m": width,
            "workstation_zone_width_m": round(expected_width, 6),
            "opening_x_m": bounds,
            "workstation_zone_x_m": [zone_x0, zone_x1],
            "sill_matches_worktop": sill_ok,
            "width_matches_zone": width_ok,
            "bounds_match_zone": bounds_ok,
            "tolerance_m": 1e-6,
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "WORKSTATION-WINDOW-DATUM",
            "PASS" if passed else "FAIL",
            "evaluated",
            f"{window_id} {'matches' if passed else 'does not match'} the linked workstation opening span and sill/worktop datum.",
            (window_id,),
            evidence,
        )
        details.append(evidence)
    return details


def _equipment_catalog(raw: object) -> EquipmentCatalog | None:
    if not isinstance(raw, dict) or not isinstance(raw.get("products"), list):
        return None
    try:
        products = {item["id"]: ProductEnvelope.from_mapping(item) for item in raw["products"]}
    except (KeyError, TypeError, ValueError):
        return None
    return EquipmentCatalog(
        metadata={key: value for key, value in raw.items() if key != "products"},
        products=products,
    )


def _overlay_pb(snapshot: dict[str, Any], pb_source: object) -> dict[str, Any] | None:
    if not isinstance(pb_source, dict):
        return None
    pb = deepcopy(pb_source)
    entities = _entity_map(snapshot)
    envelope = snapshot.get("geometry", {}).get("hall", {})
    if isinstance(pb.get("envelope"), dict):
        if _finite(envelope.get("length_m")) is not None:
            pb["envelope"]["length"] = envelope["length_m"]
        if _finite(envelope.get("width_m")) is not None:
            pb["envelope"]["width"] = envelope["width_m"]
    for room in pb.get("core", []):
        entity = entities.get("PB-" + str(room.get("id")))
        if not entity:
            continue
        geometry = entity.get("geometry") or {}
        y0, y1 = _finite(geometry.get("y0")), _finite(geometry.get("y1"))
        if y0 is not None and y1 is not None:
            room["y0"], room["y1"] = y0, y1
        door = entities.get("PB-DOOR-" + str(room.get("id")))
        if door:
            width = _finite((door.get("parameters") or {}).get("width_m"))
            if width is not None:
                room["door_width"] = width
    return pb


def _evaluate_equipment(
    snapshot: dict[str, Any],
    p2: dict[str, Any] | None,
    p2_error: str | None,
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    inputs = snapshot.get("discipline_inputs")
    equipment_inputs = inputs.get("equipment") if isinstance(inputs, dict) else None
    if not isinstance(equipment_inputs, dict):
        equipment_inputs = {}
    layout = equipment_inputs.get("layout")
    catalog = _equipment_catalog(equipment_inputs.get("catalog"))
    pb = _overlay_pb(snapshot, equipment_inputs.get("pb"))
    placements = layout.get("placements") if isinstance(layout, dict) else None
    error = p2_error or ("Current PB equipment context is unavailable." if pb is None else None)
    if catalog is None:
        error = error or "Current equipment catalogue is absent or invalid."
    if not isinstance(placements, list):
        error = error or "Current equipment benchmark layout is absent or invalid."
    if error:
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "EQUIPMENT-BENCHMARK-LAYOUT-APPLICABILITY",
            "OPEN",
            "unsupported",
            error,
            (),
            {
                "missing_or_unsupported": error,
                "required_data": _RULE_DEFINITIONS["EQUIPMENT-BENCHMARK-LAYOUT-APPLICABILITY"][
                    "required_data"
                ],
            },
        )
        return {
            "status": "OPEN",
            "checks": [],
            "placements": [],
            "layout_revision": layout.get("revision") if isinstance(layout, dict) else None,
        }

    missing_products = sorted(
        {
            str(item.get("product_id"))
            for item in placements
            if item.get("product_id") not in catalog.products
        }
    )
    if missing_products:
        error = "Benchmark placements refer to products absent from the captured catalogue."
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "EQUIPMENT-BENCHMARK-LAYOUT-APPLICABILITY",
            "OPEN",
            "unsupported",
            error,
            (),
            {
                "missing_product_ids": missing_products,
                "required_data": _RULE_DEFINITIONS["EQUIPMENT-BENCHMARK-LAYOUT-APPLICABILITY"][
                    "required_data"
                ],
            },
        )
        return {
            "status": "OPEN",
            "checks": [],
            "placements": [],
            "layout_revision": layout.get("revision"),
        }

    raw = validate_equipment(pb, p2, catalog=catalog, layout=layout)
    input_ids = _entity_map(snapshot)
    layout_revision = layout.get("revision")
    product_by_placement = {
        str(item["id"]): catalog.products[str(item["product_id"])] for item in placements
    }
    checks_by_id = {item["id"]: item for item in raw["placements"]}
    for check in raw["checks"]:
        raw_status = check["status"]
        normalized = tuple(item for item in check.get("entity_ids", ()) if item in input_ids)
        benchmark_ids = [item for item in check.get("entity_ids", ()) if item not in input_ids]
        related_placements = sorted(
            {item for item in benchmark_ids if item in product_by_placement}
            | {key for key in checks_by_id if key in check.get("entity_ids", ())}
        )
        measured = [checks_by_id[item] for item in related_placements if item in checks_by_id]
        if raw_status == "FAIL":
            message = f"Unadopted equipment benchmark geometry does not satisfy this check: {check['message']} Review the applicability and layout before design decisions."
        elif raw_status == "PASS":
            message = f"Unadopted equipment benchmark geometry satisfies this geometric check only: {check['message']} This is not selected-product clearance approval."
        else:
            message = f"Equipment benchmark review remains open: {check['message']}"
        evidence = {
            "benchmark_geometry_status": raw_status,
            "benchmark_check_message": check["message"],
            "layout_revision": layout_revision,
            "layout_status": layout.get("status"),
            "product_catalog_revision": catalog.metadata.get("revision"),
            "benchmark_source_ids": sorted(set(benchmark_ids)),
            "evaluated_placements": measured,
            "product_envelopes": {
                item: dict(product_by_placement[item].__dict__)
                for item in related_placements
                if item in product_by_placement
            },
            "installed_mass_kg": None,
            "required_data": [
                "catalogue body width/depth and operating depth",
                "benchmark placement origin and orientation",
                "current host bounds",
                "selected product and installed mass",
            ],
            "applicability": "layout and products remain coordination hypotheses; no PASS is issued for selected-product clearance",
        }
        _emit(
            findings,
            coverage_rows,
            snapshot,
            check["rule_id"],
            "OPEN",
            "evaluated",
            message,
            normalized,
            evidence,
        )

    _emit(
        findings,
        coverage_rows,
        snapshot,
        "EQUIPMENT-BENCHMARK-LAYOUT-APPLICABILITY",
        "OPEN",
        "evaluated",
        "The captured equipment layout is a coordination hypothesis; product and placement applicability remains to be confirmed.",
        (),
        {
            "layout_revision": layout_revision,
            "layout_status": layout.get("status"),
            "catalog_revision": catalog.metadata.get("revision"),
            "placement_source_ids": [item.get("id") for item in placements],
            "raw_geometric_outcomes": {item["rule_id"]: item["status"] for item in raw["checks"]},
            "required_data": _RULE_DEFINITIONS["EQUIPMENT-BENCHMARK-LAYOUT-APPLICABILITY"][
                "required_data"
            ],
        },
    )

    car_lift = (
        (equipment_inputs.get("pb") or {}).get("car_lift_layout")
        if isinstance(equipment_inputs.get("pb"), dict)
        else None
    )
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "EQUIPMENT-LIFT-SELECTION-COVERAGE",
        "OPEN",
        "unsupported",
        "The PB source contains a schematic car/lift envelope, but no selected lift product is enrolled in the equipment catalogue/layout.",
        (),
        {
            "schematic_car_lift_layout": car_lift,
            "canonical_equipment_entity_present": False,
            "selected_lift_product": None,
            "actual_installed_mass_kg": None,
            "required_data": _RULE_DEFINITIONS["EQUIPMENT-LIFT-SELECTION-COVERAGE"][
                "required_data"
            ],
        },
    )
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "EQUIPMENT-MASS-COVERAGE",
        "OPEN",
        "unsupported",
        "No selected, installed equipment-mass schedule is present in the resolved benchmark inputs.",
        (),
        {
            "installed_mass_kg_by_equipment": None,
            "catalogue_dimensions_available": bool(catalog.products),
            "catalogue_mass_fields_present": any(
                "mass_kg" in item
                for item in (equipment_inputs.get("catalog") or {}).get("products", [])
            ),
            "required_data": _RULE_DEFINITIONS["EQUIPMENT-MASS-COVERAGE"]["required_data"],
        },
    )
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "EQUIPMENT-ENGINEERING-COVERAGE",
        "OPEN",
        "not_run",
        "Equipment support, anchorage, service capacity, and professional design have not been evaluated.",
        (),
        {
            "engineering_status": "unknown/not evaluated",
            "required_data": _RULE_DEFINITIONS["EQUIPMENT-ENGINEERING-COVERAGE"]["required_data"],
        },
    )
    return {
        **raw,
        "status": "OPEN",
        "layout_revision": layout_revision,
        "catalog_revision": catalog.metadata.get("revision"),
        "applicability_status": "unadopted coordination benchmark",
    }


def _changed_entities(snapshot: dict[str, Any]) -> tuple[str, ...]:
    current = _entity_map(snapshot)
    baseline = snapshot.get("baseline")
    prior = _entity_map(baseline) if isinstance(baseline, dict) else {}
    changed = (
        set(snapshot.get("changes_requested", {}))
        if isinstance(snapshot.get("changes_requested"), dict)
        else set()
    )
    for identifier in current.keys() & prior.keys():
        left, right = current[identifier], prior[identifier]
        if any(
            left.get(field) != right.get(field)
            for field in ("geometry", "parameters", "relationships", "status")
        ):
            changed.add(identifier)
    return tuple(sorted(item for item in changed if item in current))


def _evaluate_structure(
    snapshot: dict[str, Any],
    p2: dict[str, Any] | None,
    findings: list[dict[str, Any]],
    coverage_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    inputs = snapshot.get("discipline_inputs")
    structure_inputs = inputs.get("structure") if isinstance(inputs, dict) else None
    if not isinstance(structure_inputs, dict):
        structure_inputs = {}
    system = (
        structure_inputs.get("system") if isinstance(structure_inputs.get("system"), dict) else {}
    )
    stair = structure_inputs.get("stair") if isinstance(structure_inputs.get("stair"), dict) else {}
    entities = _entity_map(snapshot)
    changed = _changed_entities(snapshot)
    changed_relevant = tuple(
        identifier
        for identifier in changed
        if entities[identifier].get("kind")
        in {"opening", "door", "space", "stair", "reservation", "wall", "column"}
    )
    reservations = tuple(
        sorted(
            identifier for identifier, item in entities.items() if item.get("kind") == "reservation"
        )
    )
    stairs = tuple(
        sorted(identifier for identifier, item in entities.items() if item.get("kind") == "stair")
    )
    opening_entities = [
        item
        for item in entities.values()
        if item.get("kind") in {"opening", "door"} and item.get("status") == "active"
    ]
    vertical_known = []
    vertical_unknown = []
    for item in opening_entities:
        geometry = item.get("geometry") or {}
        if _finite(geometry.get("z0")) is not None and _finite(geometry.get("z1")) is not None:
            vertical_known.append(item["id"])
        else:
            vertical_unknown.append(item["id"])
    reservation_z_known = [
        identifier
        for identifier in reservations
        if _finite((entities[identifier].get("geometry") or {}).get("z0")) is not None
        and _finite((entities[identifier].get("geometry") or {}).get("z1")) is not None
    ]
    project_meta = system.get("project") if isinstance(system.get("project"), dict) else {}
    live = (
        (system.get("loads") or {}).get("live", {}) if isinstance(system.get("loads"), dict) else {}
    )
    lift_hypothesis = (
        _finite(live.get("lift_point_kN_per_column_hypothesis")) if isinstance(live, dict) else None
    )
    mass_present = any("mass_kg" in (item.get("parameters") or {}) for item in entities.values())
    model_hash = snapshot.get("model_hash")

    # Candidate lines retain their source identity. SC-01 reservations already
    # have normalized entity IDs; E0 trial column lines remain source references.
    candidates: list[dict[str, Any]] = []
    stair_source = stair.get("structure") if isinstance(stair.get("structure"), dict) else {}
    for reservation in stair_source.get("column_reservations", []):
        identifier = str(reservation.get("id", ""))
        entity = entities.get(identifier)
        geometry = entity.get("geometry") if isinstance(entity, dict) else None
        if not isinstance(geometry, dict):
            continue
        bounds = tuple(_finite(geometry.get(key)) for key in ("x0", "x1", "y0", "y1"))
        if any(value is None for value in bounds):
            continue
        x0, x1, y0, y1 = bounds
        candidates.append(
            {
                "id": identifier,
                "source_ref": f"dreamhouse/stair_core.json#structure.column_reservations[id={identifier}]",
                "x_m": (x0 + x1) / 2.0,
                "y_m": (y0 + y1) / 2.0,
                "source_status": stair.get("status"),
                "reservation_bounds": bounds,
                "candidate_kind": "SC-01 plan reservation; not selected column",
            }
        )

    geometry = system.get("geometry") if isinstance(system.get("geometry"), dict) else {}
    great_wall_x = _finite(geometry.get("great_wall_x_m"))
    floor_options = (
        geometry.get("p2_floor_options")
        if isinstance(geometry.get("p2_floor_options"), list)
        else []
    )
    great_wall_option = next(
        (item for item in floor_options if item.get("id") == "GRAN-MURO"), None
    )
    hidden_y = (
        great_wall_option.get("hidden_column_y_m") if isinstance(great_wall_option, dict) else None
    )
    if great_wall_x is not None and isinstance(hidden_y, list):
        for index, raw_y in enumerate(hidden_y):
            y = _finite(raw_y)
            if y is None:
                continue
            candidates.append(
                {
                    "source_ref": f"dreamhouse/structure/structure_system.json#geometry.p2_floor_options[id=GRAN-MURO].hidden_column_y_m[{index}]",
                    "x_m": great_wall_x,
                    "y_m": y,
                    "source_status": project_meta.get("status"),
                    "candidate_kind": "E0 hidden-column trial line; no canonical element identity or selected section",
                }
            )

    space_geometry: list[dict[str, Any]] = []
    for entity in entities.values():
        if entity.get("kind") != "space":
            continue
        box = entity.get("geometry") or {}
        x0, x1, y0, y1 = (_finite(box.get(key)) for key in ("x0", "x1", "y0", "y1"))
        if box.get("shape") == "rect" and None not in (x0, x1, y0, y1) and x1 > x0 and y1 > y0:
            space_geometry.append(
                {"id": entity["id"], "x": x0, "y": y0, "w": x1 - x0, "d": y1 - y0}
            )

    stair_space_ids = {"ESC", "PB-ESC"}
    if p2 is not None:
        p2_stair = next((item for item in p2.get("spaces", []) if item.get("id") == "ESC"), None)
        if p2_stair:
            stair_space_ids.add(str(p2_stair["id"]))
    interaction_openings = [
        item
        for item in entities.values()
        if item.get("kind") in {"opening", "door"}
        and item.get("parameters", {}).get("facade") != "ROOF"
        and (
            item.get("status") == "active"
            or (item.get("status") == "context" and item.get("kind") == "door")
        )
    ]
    opening_by_id = {item["id"]: item for item in interaction_openings}
    for candidate in candidates:
        bounds = candidate.get("reservation_bounds")
        interaction = evaluate_current_support_line_plan(
            candidate,
            space_geometry,
            interaction_openings,
            stair_space_ids=stair_space_ids,
            reservation_bounds=bounds,
        )
        plan_opening_ids = tuple(
            sorted(item["opening_id"] for item in interaction["opening_plan_candidates"])
        )
        plan_space_ids = tuple(interaction["interior_nonstair_spaces"])
        link_ids = tuple(
            sorted(
                set(plan_opening_ids)
                | set(plan_space_ids)
                | ({candidate["id"]} if candidate.get("id") in entities else set())
            )
        )
        conflicts = bool(plan_opening_ids or plan_space_ids)
        message = (
            "The current candidate line has a plan relationship requiring review with the listed room/opening geometry; vertical member extent and clearance remain unknown."
            if conflicts
            else "No room-interior or window/door plan intersection was found for this source candidate; vertical member extent, clearance, and capacity remain unknown."
        )
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "STRUCTURE-SUPPORT-LINE-PLAN-INTERACTION",
            "OPEN",
            "evaluated",
            message,
            link_ids,
            {
                **interaction,
                "candidate_kind": candidate["candidate_kind"],
                "candidate_source_status": candidate.get("source_status"),
                "current_opening_geometry_sources": {
                    identifier: opening_by_id[identifier].get("working_source")
                    or opening_by_id[identifier].get("source")
                    for identifier in plan_opening_ids
                },
                "current_model_hash": model_hash,
                "plan_only_result": True,
                "required_data": _RULE_DEFINITIONS["STRUCTURE-SUPPORT-LINE-PLAN-INTERACTION"][
                    "required_data"
                ],
            },
            finding_suffix=candidate["source_ref"] if candidate.get("id") not in entities else None,
        )

    common_evidence = {
        "resolved_model_hash": model_hash,
        "structural_result_model_hash": None,
        "structural_result_evaluated_for_current_snapshot": False,
        "changed_entity_ids": list(changed_relevant),
        "e0_source": {
            "id": project_meta.get("id"),
            "revision": project_meta.get("revision"),
            "status": project_meta.get("status"),
            "model_validity": project_meta.get("model_validity"),
        },
        "stair_source": {"revision": stair.get("revision"), "status": stair.get("status")},
        "active_opening_count": len(opening_entities),
        "active_opening_vertical_bounds_known_ids": sorted(vertical_known),
        "active_opening_vertical_bounds_unknown_ids": sorted(vertical_unknown),
        "plan_only_reservation_ids": list(reservations),
        "reservation_vertical_bounds_known_ids": reservation_z_known,
        "mass_input_present": mass_present,
    }
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "STRUCTURE-CURRENT-SNAPSHOT-COVERAGE",
        "OPEN",
        "not_run",
        "No enrolled structural result carries the current resolved-model fingerprint; archived screening outputs are not current results for this snapshot.",
        changed_relevant,
        {
            **common_evidence,
            "invalidation_reason": "Structural result fingerprint is absent or does not equal the current model hash.",
            "required_data": _RULE_DEFINITIONS["STRUCTURE-CURRENT-SNAPSHOT-COVERAGE"][
                "required_data"
            ],
        },
    )
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "STRUCTURE-VERTICAL-CONTINUITY-COVERAGE",
        "OPEN",
        "unsupported",
        "Current stair and column inputs include plan reservations, but no current selected-member vertical continuity result is evaluated.",
        reservations + stairs + changed_relevant,
        {
            **common_evidence,
            "stair_entity_ids": list(stairs),
            "reservation_entity_ids": list(reservations),
            "support_line_plan_interaction_count": len(candidates),
            "active_window_and_door_geometry_count": len(interaction_openings),
            "reservation_capability": "plan-only; reservation is not a structural member",
            "required_data": _RULE_DEFINITIONS["STRUCTURE-VERTICAL-CONTINUITY-COVERAGE"][
                "required_data"
            ],
        },
    )
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "STRUCTURE-MASS-COVERAGE",
        "OPEN",
        "unsupported",
        "Current resolved entities do not contain a selected assembly/member mass schedule.",
        changed_relevant,
        {
            **common_evidence,
            "element_mass_kg": None,
            "wall_assembly_mass_kg_m2": None,
            "installed_equipment_mass_kg": None,
            "required_data": _RULE_DEFINITIONS["STRUCTURE-MASS-COVERAGE"]["required_data"],
        },
    )
    _emit(
        findings,
        coverage_rows,
        snapshot,
        "STRUCTURE-ENGINEERING-COVERAGE",
        "OPEN",
        "not_run",
        "Site actions, selected-member design, connections, foundations, and professional review remain unevaluated for this snapshot.",
        changed_relevant,
        {
            **common_evidence,
            "engineering_status": "unknown/not evaluated",
            "site_specific_actions_resolved": False,
            "member_selection_resolved": False,
            "connections_and_foundations_resolved": False,
            "required_data": _RULE_DEFINITIONS["STRUCTURE-ENGINEERING-COVERAGE"]["required_data"],
        },
    )
    if lift_hypothesis is not None:
        _emit(
            findings,
            coverage_rows,
            snapshot,
            "STRUCTURE-LIFT-LOAD-COVERAGE",
            "OPEN",
            "unsupported",
            "The E0 source contains a per-column lift-load hypothesis; actual lift reactions and support design remain unknown.",
            (),
            {
                "hypothetical_lift_point_load_kN_per_column": lift_hypothesis,
                "hypothesis_is_verified_design_action": False,
                "actual_lift_reactions_kN": None,
                "required_data": _RULE_DEFINITIONS["STRUCTURE-LIFT-LOAD-COVERAGE"]["required_data"],
            },
        )
    return {
        "status": "OPEN",
        "resolved_model_hash": model_hash,
        "changed_relevant_entity_ids": list(changed_relevant),
        "current_structural_result": None,
        "mass_kg": None,
        "engineering_status": "unknown/not evaluated",
        "source_status": project_meta.get("status"),
        "lift_point_load_hypothesis_kN": lift_hypothesis,
        "vertical_continuity": {
            "active_opening_count": len(opening_entities),
            "openings_with_known_vertical_bounds": len(vertical_known),
            "openings_with_unknown_vertical_bounds": len(vertical_unknown),
            "plan_only_reservation_count": len(reservations),
            "reservations_with_known_vertical_bounds": len(reservation_z_known),
            "support_line_plan_interaction_count": len(candidates),
        },
    }


def evaluate_disciplines(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Evaluate programme, equipment, workstation datum, and structural coverage.

    The input is an immutable-by-convention resolver snapshot. Copies of legacy
    source dictionaries are overlaid with canonical entity geometry before existing
    programme/equipment functions run. Missing or unsupported data stays OPEN and
    carries an explicit coverage state.
    """
    findings: list[dict[str, Any]] = []
    coverage_rows: dict[str, dict[str, Any]] = {}
    inputs = snapshot.get("discipline_inputs")
    inputs = inputs if isinstance(inputs, dict) else {}
    programme_inputs = inputs.get("programme")
    p2_source = programme_inputs.get("p2") if isinstance(programme_inputs, dict) else None
    p2, space_ids, p2_error = _overlay_p2(snapshot, p2_source)
    programme = _evaluate_programme(snapshot, p2, space_ids, p2_error, findings, coverage_rows)
    equipment = _evaluate_equipment(snapshot, p2, p2_error, findings, coverage_rows)
    equipment_inputs = inputs.get("equipment")
    pb_source = equipment_inputs.get("pb") if isinstance(equipment_inputs, dict) else None
    workstation_datums = _evaluate_workstation_datums(snapshot, pb_source, findings, coverage_rows)
    structure = _evaluate_structure(snapshot, p2, findings, coverage_rows)

    rules = []
    totals = {state: 0 for state in _COVERAGE_STATES}
    definitions = deepcopy(_RULE_DEFINITIONS)
    for finding in findings:
        definitions.setdefault(
            finding["rule_id"],
            {
                "description": "Evaluate the captured equipment benchmark against the resolved coordination snapshot.",
                "required_data": finding.get("evidence", {}).get("required_data")
                or ["current host geometry", "captured product envelope", "captured placement"],
                "limits": [
                    "This rule evaluates an unadopted equipment benchmark and is not product or procurement approval."
                ],
            },
        )
    for rule_id in sorted(set(definitions) | set(coverage_rows)):
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
        definition = definitions.get(rule_id, {})
        rules.append(
            {
                "rule_id": rule_id,
                **definition,
                "counts": dict(row["counts"]),
                "entity_ids_by_coverage": {
                    state: sorted(row["entity_ids"][state]) for state in _COVERAGE_STATES
                },
            }
        )
    findings.sort(key=lambda item: (item["rule_id"], item["finding_id"]))
    return {
        "findings": findings,
        "coverage": {"totals": totals, "rules": rules},
        "rule_registry": [
            {"rule_id": rule_id, **definition}
            for rule_id, definition in sorted(definitions.items())
        ],
        "disciplines": {
            "programme": programme,
            "equipment": equipment,
            "workstation_datums": workstation_datums,
            "structure": structure,
        },
    }


__all__ = ["evaluate_disciplines"]

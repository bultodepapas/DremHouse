"""Report purpose-specific information needs from the captured snapshot.

The profiles follow the coordination, procurement, installation and maintenance uses
described in the project coordination plan. They report absent evidence as absent; they
do not create source values, select products, or grant professional approval.
"""

from __future__ import annotations

import math
from typing import Any

from dreamhouse.coordination.model import digest

_PROFILES = (
    ("coordination", "schematic coordination"),
    ("procurement", "product selection and procurement"),
    ("installation", "installation and commissioning"),
    ("maintenance", "handover and operations"),
)
_COMPONENT_KINDS = {"opening", "door"}
_COORDINATION_SOURCE = "docs/06_gestion_y_obra/connected_project_coordination_next_step.md#43-views-and-dimensions-must-declare-what-they-represent"
_PURPOSE_SOURCE = "docs/08_investigacion/connected_coordination_delivery_research_2026_10.md#r20"


def _present(value: Any) -> bool:
    if value is None or value == "":
        return False
    return not (isinstance(value, (list, dict, tuple, set)) and not value)


def _source_reference(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    path, key = value.get("path"), value.get("key")
    if not isinstance(path, str) or not path or not isinstance(key, str) or not key:
        return None
    return f"{path}#{key}"


def _info(
    identifier: str,
    description: str,
    status: str,
    *,
    observed: Any = None,
    source_refs: list[str] | None = None,
    basis: str = _PURPOSE_SOURCE,
) -> dict:
    return {
        "id": identifier,
        "description": description,
        "status": status,
        "observed": observed,
        "source_refs": sorted(set(source_refs or [])),
        "basis": basis,
    }


def _finite(value: Any) -> bool:
    return type(value) in {int, float} and math.isfinite(value)


def _coordinate_requirements(entity: dict, entities: dict[str, dict]) -> list[dict]:
    source_ref = _source_reference(entity.get("source"))
    refs = [source_ref] if source_ref else []
    geometry = entity.get("geometry") if isinstance(entity.get("geometry"), dict) else {}
    parameters = entity.get("parameters") if isinstance(entity.get("parameters"), dict) else {}
    relationships = (
        entity.get("relationships") if isinstance(entity.get("relationships"), dict) else {}
    )
    kind = entity.get("kind")
    requirements = [
        _info(
            "stable-identity",
            "Stable entity identity, kind, level and lifecycle status.",
            "met"
            if all(_present(entity.get(key)) for key in ("id", "kind", "level", "status"))
            else "missing",
            observed={key: entity.get(key) for key in ("id", "kind", "level", "status")},
            source_refs=refs,
            basis=_COORDINATION_SOURCE,
        ),
        _info(
            "source-reference",
            "Traceable source file and source key for the represented entity.",
            "met" if source_ref else "missing",
            observed=entity.get("source"),
            source_refs=refs,
            basis=_COORDINATION_SOURCE,
        ),
    ]

    plan_bounds = {key: geometry.get(key) for key in ("x0", "x1", "y0", "y1")}
    has_plan_bounds = geometry.get("shape") != "unresolved" and all(
        _finite(value) for value in plan_bounds.values()
    )
    requirements.append(
        _info(
            "plan-location-and-dimensions",
            "Source-derived plan envelope with resolvable horizontal extents.",
            "met" if has_plan_bounds else "missing",
            observed={"shape": geometry.get("shape"), **plan_bounds},
            source_refs=refs,
            basis=_COORDINATION_SOURCE,
        )
    )

    is_roof_opening = kind in _COMPONENT_KINDS and parameters.get("facade") == "ROOF"
    needs_vertical_bounds = kind in _COMPONENT_KINDS and not is_roof_opening
    if needs_vertical_bounds:
        vertical_bounds = {key: geometry.get(key) for key in ("z0", "z1")}
        has_vertical_bounds = all(_finite(value) for value in vertical_bounds.values())
        requirements.append(
            _info(
                "vertical-location-and-dimensions",
                "Source-derived sill/head or door vertical extent for a vertical opening.",
                "met" if has_vertical_bounds else "missing",
                observed=vertical_bounds,
                source_refs=refs,
                basis=_COORDINATION_SOURCE,
            )
        )
    else:
        requirements.append(
            _info(
                "vertical-location-and-dimensions",
                "Vertical extent where it applies to the represented component.",
                "not_applicable",
                observed=None,
                source_refs=refs,
                basis=_COORDINATION_SOURCE,
            )
        )

    if kind in _COMPONENT_KINDS and not is_roof_opening:
        host_id = relationships.get("host_id")
        host = entities.get(host_id) if isinstance(host_id, str) else None
        host_is_wall = isinstance(host, dict) and host.get("kind") == "wall"
        requirements.append(
            _info(
                "host-relationship",
                "Opening or door is linked to a normalized wall/host reference.",
                "met" if host_is_wall else "missing",
                observed=host_id,
                source_refs=refs,
                basis=_COORDINATION_SOURCE,
            )
        )
    if kind in _COMPONENT_KINDS and entity.get("level") == "P2":
        space_ids = relationships.get("space_ids")
        spaces_resolve = (
            isinstance(space_ids, list)
            and bool(space_ids)
            and all(
                isinstance(space_id, str)
                and isinstance(entities.get(space_id), dict)
                and entities[space_id].get("kind") == "space"
                for space_id in space_ids
            )
        )
        requirements.append(
            _info(
                "space-relationship",
                "Upper-floor opening or door is linked to its affected space or spaces.",
                "met" if spaces_resolve else "missing",
                observed=space_ids,
                source_refs=refs,
                basis=_COORDINATION_SOURCE,
            )
        )
    return requirements


def _quantity_by_entity(evaluation: dict) -> dict[str, dict]:
    ledger = evaluation.get("quantity_ledger", {})
    records = ledger.get("records", []) if isinstance(ledger, dict) else []
    quantities = {}
    for row in records:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            continue
        identifier = row["id"]
        if not identifier.startswith("Q-") or not identifier.endswith("-AREA"):
            continue
        entity_id = identifier[2:-5]
        quantities[entity_id] = row
    return quantities


def _finding_refs(evaluation: dict, entity_id: str) -> list[dict]:
    rows = evaluation.get("findings", [])
    if not isinstance(rows, list):
        return []
    return sorted(
        (
            {
                "finding_id": row.get("finding_id"),
                "rule_id": row.get("rule_id"),
                "status": row.get("status"),
                "coverage": row.get("coverage"),
            }
            for row in rows
            if isinstance(row, dict) and entity_id in row.get("entity_ids", [])
        ),
        key=lambda row: str(row.get("finding_id")),
    )


def _maintenance_assets(evaluation: dict) -> list[dict]:
    extensions = evaluation.get("extensions", {})
    maintenance = extensions.get("maintenance", {}) if isinstance(extensions, dict) else {}
    assets = maintenance.get("assets", []) if isinstance(maintenance, dict) else []
    return (
        [asset for asset in assets if isinstance(asset, dict)] if isinstance(assets, list) else []
    )


def _requirements_for(
    purpose: str,
    entity: dict,
    entities: dict[str, dict],
    evaluation: dict,
    quantities: dict[str, dict],
    maintenance_assets: list[dict],
    source_asset: dict | None = None,
) -> tuple[str, list[dict]]:
    entity_id = entity.get("id") if isinstance(entity, dict) else None
    kind = entity.get("kind") if isinstance(entity, dict) else None
    if purpose == "coordination":
        return "applicable", _coordinate_requirements(entity, entities)

    asset = source_asset or next(
        (
            item
            for item in maintenance_assets
            if item.get("normalized_entity_id") == entity_id
            or (entity_id is None and item.get("source_asset_id") == entity.get("source_asset_id"))
        ),
        None,
    )
    applicable = kind in _COMPONENT_KINDS or (purpose == "maintenance" and asset is not None)
    if not applicable:
        return "not_applicable", []

    finding_refs = _finding_refs(evaluation, entity_id) if isinstance(entity_id, str) else []
    source_ref = _source_reference(entity.get("source")) if isinstance(entity, dict) else None
    refs = [source_ref] if source_ref else []
    if asset and isinstance(asset.get("source_ref"), str):
        refs.append(asset["source_ref"])

    if purpose == "procurement":
        quantity = quantities.get(entity_id) if isinstance(entity_id, str) else None
        if quantity:
            quantity_state = (
                "met"
                if "procurement" in str(quantity.get("measurement_status", "")).lower()
                and quantity.get("net_glass_area_m2") is not None
                else "incomplete"
            )
            quantity_observation = {
                key: value for key, value in quantity.items() if key != "description"
            }
            quantity_refs = [f"evaluation.quantity_ledger.records[id={quantity['id']}]", *refs]
        else:
            quantity_state = "missing"
            quantity_observation = None
            quantity_refs = refs
        requirements = [
            _info(
                "procurement-quantity-basis",
                "Quantity basis appropriate to the selected product and procurement scope.",
                quantity_state,
                observed=quantity_observation,
                source_refs=quantity_refs,
            ),
            _info(
                "selected-product",
                "Selected manufacturer, model and product reference.",
                "missing",
                observed=None,
                source_refs=[],
            ),
            _info(
                "product-performance-evidence",
                "Reviewed product performance evidence for the project requirements.",
                "missing",
                observed=None,
                source_refs=[],
            ),
            _info(
                "comparable-price-evidence",
                "Comparable supplier quotation or approved rate for the selected product.",
                "missing",
                observed=None,
                source_refs=[],
            ),
            _info(
                "procurement-professional-review",
                "Responsible professional review linked to the selected product evidence.",
                "missing",
                observed=None,
                source_refs=[row["finding_id"] for row in finding_refs if row.get("finding_id")],
            ),
        ]
        return "applicable", requirements

    if purpose == "installation":
        requirements = [
            _info(
                "installation-product-reference",
                "Selected product and installation instructions for the installed assembly.",
                "missing",
                observed=None,
                source_refs=[],
            ),
            _info(
                "installation-interface-detail",
                "Reviewed setting-out, host interface, fixings and tolerance information.",
                "missing",
                observed=None,
                source_refs=refs,
            ),
            _info(
                "installation-method-and-review",
                "Approved installation method and responsible professional review.",
                "missing",
                observed=None,
                source_refs=[row["finding_id"] for row in finding_refs if row.get("finding_id")],
            ),
            _info(
                "installation-inspection-record",
                "Recorded installation inspection, testing and commissioning evidence.",
                "missing",
                observed=None,
                source_refs=[],
            ),
        ]
        return "applicable", requirements

    if purpose == "maintenance":
        asset_id = (
            asset.get("source_asset_id")
            if asset
            else (entity_id if isinstance(entity_id, str) else entity.get("source_asset_id"))
        )
        installed_state = asset.get("installed_state") if asset else None
        tested_state = asset.get("tested_state") if asset else None
        commissioned_state = asset.get("commissioned_state") if asset else None
        intervals = asset.get("maintenance_intervals") if asset else None
        open_items = asset.get("source_open_maintenance_items", []) if asset else []
        asset_ref = f"evaluation.extensions.maintenance.assets[id={asset_id}]" if asset else None
        asset_refs = [asset_ref] if asset_ref else []
        if refs:
            asset_refs.extend(refs)
        lifecycle = {
            "installed": installed_state,
            "tested": tested_state,
            "commissioned": commissioned_state,
        }
        lifecycle_complete = all(value not in (None, "unknown") for value in lifecycle.values())
        requirements = [
            _info(
                "maintainable-asset-registration",
                "Maintainable asset has a source record and stable asset identity.",
                "met" if asset and _present(asset_id) else "missing",
                observed={"source_asset_id": asset_id, "normalized_entity_id": entity_id},
                source_refs=asset_refs,
            ),
            _info(
                "installed-product-identity",
                "Installed manufacturer, model and serial or equivalent product identifier.",
                "missing",
                observed=None,
                source_refs=asset_refs,
            ),
            _info(
                "warranty-and-manuals",
                "Product warranty, operation manual and maintenance instructions.",
                "missing",
                observed=None,
                source_refs=asset_refs,
            ),
            _info(
                "lifecycle-records",
                "Installed, tested and commissioned states supported by recorded evidence.",
                "met" if lifecycle_complete else "missing",
                observed=lifecycle,
                source_refs=asset_refs,
            ),
            _info(
                "maintenance-plan-and-access",
                "Maintenance tasks, intervals, accountable owner, safe access and replacement method.",
                "met" if _present(intervals) and not open_items else "missing",
                observed={"maintenance_intervals": intervals, "source_open_items": open_items},
                source_refs=asset_refs,
            ),
            _info(
                "inspection-history",
                "Completed inspection and maintenance records.",
                "met" if asset and _present(asset.get("maintenance_events")) else "missing",
                observed=asset.get("maintenance_events") if asset else None,
                source_refs=asset_refs,
            ),
        ]
        return "applicable", requirements

    raise ValueError(f"Unsupported information purpose: {purpose}")


def _record(
    *,
    record_id: str,
    purpose: str,
    milestone: str,
    entity: dict,
    entities: dict[str, dict],
    evaluation: dict,
    quantities: dict[str, dict],
    maintenance_assets: list[dict],
    source_asset: dict | None = None,
) -> dict:
    entity_id = entity.get("id") if isinstance(entity, dict) else None
    applicability, requirements = _requirements_for(
        purpose,
        entity,
        entities,
        evaluation,
        quantities,
        maintenance_assets,
        source_asset,
    )
    missing = [item["id"] for item in requirements if item["status"] in {"missing", "incomplete"}]
    status = (
        "not_applicable"
        if applicability == "not_applicable"
        else "incomplete"
        if missing
        else "complete"
    )
    label = entity.get("label") if isinstance(entity, dict) else None
    evidence_basis = {
        "record_id": record_id,
        "purpose": purpose,
        "milestone": milestone,
        "requirements": [
            {
                "id": item["id"],
                "status": item["status"],
                "observed": item["observed"],
                "source_refs": item["source_refs"],
            }
            for item in requirements
        ],
    }
    return {
        "record_id": record_id,
        "entity_id": entity_id,
        "source_asset_id": entity.get("source_asset_id") if entity_id is None else None,
        "label": label,
        "kind": entity.get("kind") if isinstance(entity, dict) else None,
        "purpose": purpose,
        "milestone": milestone,
        "applicability": applicability,
        "status": status,
        "requirements": requirements,
        "missing_information": missing,
        "evidence_fingerprint": digest(evidence_basis),
        "fingerprint_policy": "purpose-specific observed information and source references; display labels excluded",
    }


def information_requirements(snapshot: dict, evaluation: dict) -> dict:
    """Return per-entity information coverage for the four declared project purposes.

    The returned profiles describe information completeness only. A complete
    coordination record does not imply procurement, installation, maintenance or
    professional approval.
    """
    raw_entities = snapshot.get("entities", {})
    entities = (
        {
            str(value.get("id", key)): value
            for key, value in raw_entities.items()
            if isinstance(value, dict)
        }
        if isinstance(raw_entities, dict)
        else {}
    )
    quantities = _quantity_by_entity(evaluation)
    maintenance_assets = _maintenance_assets(evaluation)
    records = []
    for purpose, milestone in _PROFILES:
        for entity_id, entity in sorted(entities.items()):
            records.append(
                _record(
                    record_id=f"entity:{entity_id}:{purpose}",
                    purpose=purpose,
                    milestone=milestone,
                    entity=entity,
                    entities=entities,
                    evaluation=evaluation,
                    quantities=quantities,
                    maintenance_assets=maintenance_assets,
                )
            )
        if purpose == "maintenance":
            normalized_ids = {
                asset.get("normalized_entity_id")
                for asset in maintenance_assets
                if isinstance(asset.get("normalized_entity_id"), str)
            }
            for asset in sorted(
                maintenance_assets,
                key=lambda item: str(item.get("source_asset_id", "")),
            ):
                if asset.get("normalized_entity_id") in normalized_ids:
                    continue
                source_asset_id = asset.get("source_asset_id")
                if not isinstance(source_asset_id, str) or not source_asset_id:
                    continue
                source_entity = {
                    "source_asset_id": source_asset_id,
                    "kind": "source asset reservation",
                    "source": None,
                }
                records.append(
                    _record(
                        record_id=f"asset:{source_asset_id}:{purpose}",
                        purpose=purpose,
                        milestone=milestone,
                        entity=source_entity,
                        entities=entities,
                        evaluation=evaluation,
                        quantities=quantities,
                        maintenance_assets=maintenance_assets,
                        source_asset=asset,
                    )
                )

    summary = {}
    for purpose, milestone in _PROFILES:
        scoped = [row for row in records if row["purpose"] == purpose]
        summary[purpose] = {
            "milestone": milestone,
            "applicable": sum(row["applicability"] == "applicable" for row in scoped),
            "complete": sum(row["status"] == "complete" for row in scoped),
            "incomplete": sum(row["status"] == "incomplete" for row in scoped),
            "not_applicable": sum(row["status"] == "not_applicable" for row in scoped),
        }
    return {
        "schema_version": 1,
        "scenario_id": snapshot.get("scenario_id"),
        "input_hash": snapshot.get("input_hash"),
        "model_hash": snapshot.get("model_hash"),
        "profiles_source": _PURPOSE_SOURCE,
        "records": records,
        "summary_by_purpose": summary,
        "limitation": "Information coverage does not establish geometric adequacy, professional approval, product suitability, procurement authority, or construction authority.",
    }

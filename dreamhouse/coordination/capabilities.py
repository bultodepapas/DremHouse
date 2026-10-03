"""Report actual source, operation, drawing and rule coverage for every enrolled family."""

from __future__ import annotations

from dreamhouse.coordination.model import editable_fields


def capability_report(snapshot: dict, evaluation: dict, views: dict, drawings: dict) -> dict:
    families = {}
    for identifier, entity in sorted(snapshot["entities"].items()):
        family = families.setdefault(entity["family"], {"family": entity["family"], "entities": []})
        related = [f for f in evaluation["findings"] if identifier in f["entity_ids"]]
        family["entities"].append(
            {
                "id": identifier,
                "source": entity["source"],
                "kind": entity["kind"],
                "geometry_capability": entity["geometry"]["shape"],
                "editable_fields": list(editable_fields(entity)),
                "occurrences": views["by_entity"].get(identifier, []),
                "rule_coverage": [
                    {
                        "finding_id": f["finding_id"],
                        "rule_id": f["rule_id"],
                        "status": f["status"],
                        "coverage": f["coverage"],
                    }
                    for f in related
                ],
            }
        )
    return {
        "schema_version": 1,
        "scenario_id": snapshot["scenario_id"],
        "input_hash": snapshot["input_hash"],
        "model_hash": snapshot["model_hash"],
        "families": list(families.values()),
        "entity_count": len(snapshot["entities"]),
        "entities_with_editable_parameters": sum(
            bool(editable_fields(e)) for e in snapshot["entities"].values()
        ),
        "drawing_inventory": "drawing_inventory.json",
        "catalog_drawing_count": len(drawings.get("drawings", [])),
        "source_context_records": "extensions.json",
        "unsupported_study_operations": [
            "add or delete an entity",
            "reassign a host",
            "resolve CF-013 door placement",
            "adopt a product",
            "edit wall/room/stair/service geometry",
        ],
        "extension_policy": "Context families use their declared source files and versioned adapters; study parameter editing is limited to fields listed here. A represented entity is not proof of engineering or complete annotation coverage.",
    }

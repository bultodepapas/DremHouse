"""Expose conservative consumer dependencies and changed-evidence review obligations."""

from __future__ import annotations

from dreamhouse.coordination.model import digest


def dependency_report(snapshot: dict, evaluation: dict, inventory: dict) -> dict:
    """Describe registered consumers; always rebuild all of them, without cached passes.

    Entities are not the whole input set: programme/equipment context and code are
    dependencies too. Unknown professional evidence is kept outstanding, never invented.
    """
    entities = snapshot["entities"]
    consumers = []
    for view in inventory["views"]:
        consumers.append(
            {
                "id": f"view:{view['view_id']}",
                "artifact": view["file"],
                "entity_ids": sorted({v["entity_id"] for v in view["occurrences"]}),
                "context_inputs": ["geometry", "discipline_inputs"],
                "depends_on": ["evaluation"],
                "state": "recomputed",
            }
        )
    for family, artifact in (
        ("opening_schedule", "openings.json"),
        ("quantity_ledger", "quantities.json"),
    ):
        consumers.append(
            {
                "id": family,
                "artifact": artifact,
                "entity_ids": sorted(
                    k for k, e in entities.items() if e["kind"] in {"opening", "door"}
                ),
                "context_inputs": [],
                "depends_on": ["evaluation"],
                "state": "recomputed",
            }
        )
    consumers.extend(
        [
            {
                "id": "evaluation",
                "artifact": "findings.json",
                "entity_ids": sorted(entities),
                "context_inputs": ["geometry", "discipline_inputs"],
                "depends_on": [],
                "state": "recomputed",
            },
            {
                "id": "cost",
                "artifact": "cost.json",
                "entity_ids": [],
                "context_inputs": ["cost_mapping.json", "rate_book.json"],
                "depends_on": ["quantity_ledger"],
                "state": "recomputed; unapproved costs unknown",
            },
        ]
    )
    changes = evaluation["changes"]
    changed = (
        set(changes["added"])
        | set(changes["removed"])
        | {row["entity_id"] for row in changes["modified"]}
    )
    context_changes = {row["path"] for row in changes.get("context_changes", [])}
    related = set(changed)
    for key, entity in entities.items():
        refs = entity.get("relationships", {})
        if key in changed:
            related.update(refs.get("space_ids", []))
            if refs.get("host_id"):
                related.add(refs["host_id"])
        if refs.get("host_id") in changed or changed.intersection(refs.get("space_ids", [])):
            related.add(key)
    affected = {
        row["id"]
        for row in consumers
        if related.intersection(row["entity_ids"])
        or any(
            path == declared or path.startswith(declared + ".")
            for path in context_changes
            for declared in row["context_inputs"]
        )
    }
    while True:
        expanded = affected | {
            row["id"] for row in consumers if affected.intersection(row["depends_on"])
        }
        if expanded == affected:
            break
        affected = expanded
    evidence = [
        {
            "conflict_id": conflict,
            "status": "outstanding",
            "review_required_for_changed_scenario": bool(changed or context_changes),
            "reasons": sorted(changed | context_changes),
            "evidence_fingerprint": digest(
                {"conflict": conflict, "model_hash": snapshot["model_hash"]}
            ),
            "approved_evidence_attached": False,
        }
        for conflict in snapshot.get("open_conflicts", [])
    ]
    return {
        "schema_version": 1,
        "scenario_id": snapshot["scenario_id"],
        "model_hash": snapshot["model_hash"],
        "input_hash": snapshot["input_hash"],
        "policy": "conservative full rebuild; impact is an explanation, not a cache or minimal closure",
        "source_dependencies": snapshot["build_dependencies"],
        "entities": {
            key: {
                "source": entity.get("source"),
                "working_source": entity.get("working_source"),
                "relationships": entity.get("relationships", {}),
            }
            for key, entity in sorted(entities.items())
        },
        "consumers": consumers,
        "change_impact": {
            "changed_entity_ids": sorted(changed),
            "changed_context_paths": sorted(context_changes),
            "related_entity_ids": sorted(related),
            "affected_consumer_ids": sorted(affected),
            "recomputed_consumer_ids": sorted(row["id"] for row in consumers),
        },
        "professional_evidence": evidence,
        "publication": "Current catalog consumers remain unmigrated; this report does not certify their freshness against a study.",
    }

"""Expose conservative consumer dependencies and changed-evidence review obligations."""

from __future__ import annotations

from dreamhouse.coordination.model import CoordinationError, digest


def validate_consumers(consumers: list[dict]) -> list[str]:
    """Validate consumer references and return a deterministic dependency-first order."""
    by_id = {item["id"]: item for item in consumers}
    if len(by_id) != len(consumers):
        raise CoordinationError("Duplicate calculation/view consumer identity")
    visiting, complete, order = set(), set(), []

    def visit(identifier: str) -> None:
        if identifier not in by_id:
            raise CoordinationError(f"Unknown consumer dependency: {identifier}")
        if identifier in visiting:
            raise CoordinationError(f"Cyclic calculation/view dependency at {identifier}")
        if identifier in complete:
            return
        visiting.add(identifier)
        for dependency in sorted(by_id[identifier]["depends_on"]):
            visit(dependency)
        visiting.remove(identifier)
        complete.add(identifier)
        order.append(identifier)

    for identifier in sorted(by_id):
        visit(identifier)
    return order


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
                "context_inputs": ["geometry", "discipline_inputs", "view_settings"],
                "depends_on": ["structural_screening"]
                if view["view_id"].startswith("structure-")
                else ["evaluation"],
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
    consumers.append(
        {
            "id": "house_extensions",
            "artifact": "extensions.json",
            "entity_ids": sorted(entities),
            "context_inputs": ["geometry", "discipline_inputs"],
            "depends_on": ["evaluation"],
            "state": "recomputed; missing engineering data remains unknown",
        }
    )
    consumers.append(
        {
            "id": "structural_screening",
            "artifact": "structural_screening.json",
            "entity_ids": sorted(entities),
            "context_inputs": ["geometry", "discipline_inputs.structure"],
            "depends_on": ["evaluation"],
            "state": "recomputed from source hypotheses; no engineering approval",
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
    for identifier, artifact in (
        ("information_requirements", "information_requirements.json"),
        ("evidence", "evidence.json"),
        ("viewpoints", "viewpoints.json"),
        ("phase_gates", "phase_gates.json"),
    ):
        consumers.append(
            {
                "id": identifier,
                "artifact": artifact,
                "entity_ids": sorted(entities),
                "context_inputs": [
                    "geometry",
                    "discipline_inputs",
                    "view_settings",
                    "evidence_records",
                ],
                "depends_on": ["evaluation"]
                + (
                    [f"view:{v['view_id']}" for v in inventory["views"]]
                    if identifier in {"viewpoints", "phase_gates"}
                    else []
                )
                + (
                    [
                        "opening_schedule",
                        "quantity_ledger",
                        "house_extensions",
                        "cost",
                        "information_requirements",
                        "evidence",
                        "viewpoints",
                    ]
                    if identifier == "phase_gates"
                    else ["quantity_ledger", "house_extensions"]
                    if identifier == "information_requirements"
                    else []
                ),
                "state": "recomputed; source and purpose coverage remain explicit",
            }
        )
    changes = evaluation["changes"]
    dependency_order = validate_consumers(consumers)
    changed = (
        set(changes["added"])
        | set(changes["removed"])
        | {row["entity_id"] for row in changes["modified"]}
    )
    context_changes = {row["path"] for row in changes.get("context_changes", [])}
    # These authored review inputs differ from the source baseline without
    # changing the physical model or triggering design-evidence claims.
    review_inputs = {key for key in ("view_settings", "evidence_records") if snapshot.get(key)}
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
            for path in context_changes | review_inputs
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
        "dependency_order": dependency_order,
        "change_impact": {
            "changed_entity_ids": sorted(changed),
            "changed_context_paths": sorted(context_changes),
            "changed_review_inputs": sorted(review_inputs),
            "related_entity_ids": sorted(related),
            "affected_consumer_ids": sorted(affected),
            "recomputed_consumer_ids": sorted(row["id"] for row in consumers),
        },
        "professional_evidence": evidence,
        "publication": "Catalog consumer coverage is recorded in drawing_inventory.json; review release and adopted historical aliases retain separate authority.",
    }

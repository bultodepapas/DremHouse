"""Build deterministic, package-bound issue viewpoints from review evidence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from dreamhouse.coordination.model import CoordinationError, digest


def build_viewpoints(snapshot: dict, evaluation: dict, inventory: dict) -> dict:
    """Bind evaluated findings to the exact snapshot and inventoried occurrences.

    The records are navigation evidence only. A destination is available only when the
    finding, snapshot and view inventory identify the same scenario/input and the
    inventory's entity, view, file, occurrence and captured view definition all agree.
    """
    if not isinstance(snapshot, dict) or not isinstance(evaluation, dict) or not isinstance(
        inventory, dict
    ):
        raise TypeError("snapshot, evaluation and inventory must be dictionaries")

    scenario_id = _identity(snapshot.get("scenario_id"))
    input_hash = _identity(snapshot.get("input_hash"))
    model_hash = _identity(snapshot.get("model_hash"))
    snapshot_ref = {
        "scenario_id": scenario_id,
        "input_hash": input_hash,
        "model_hash": model_hash,
    }

    package_problems = []
    if not scenario_id or not input_hash or not model_hash:
        package_problems.append("snapshot scenario, input or model identity is missing")
    for label, source in (("evaluation", evaluation), ("view inventory", inventory)):
        for key, expected in (("scenario_id", scenario_id), ("input_hash", input_hash)):
            actual = source.get(key)
            if actual is not None and actual != expected:
                package_problems.append(
                    f"{label} {key} does not match the snapshot package"
                )
            elif label == "view inventory" and actual is None:
                package_problems.append(f"view inventory {key} is unavailable")
        actual_model = source.get("model_hash")
        if actual_model is not None and actual_model != model_hash:
            package_problems.append(f"{label} model_hash does not match the snapshot package")

    entities = snapshot.get("entities", {})
    entities = entities if isinstance(entities, dict) else {}
    views = inventory.get("views", [])
    views = views if isinstance(views, list) else []
    views_by_id: dict[str, list[dict[str, Any]]] = {}
    for view in views:
        if isinstance(view, dict) and isinstance(view.get("view_id"), str):
            views_by_id.setdefault(view["view_id"], []).append(view)
    by_entity = inventory.get("by_entity", {})
    by_entity = by_entity if isinstance(by_entity, dict) else {}

    raw_findings = evaluation.get("findings", [])
    if not isinstance(raw_findings, list):
        raise CoordinationError("Evaluation findings must be a list")
    seen_finding_ids: set[str] = set()
    issues = []
    for finding in raw_findings:
        if not isinstance(finding, dict):
            continue
        finding_id = _identity(finding.get("finding_id"))
        if not finding_id:
            raise CoordinationError("Evaluation finding is missing its stable finding_id")
        if finding_id in seen_finding_ids:
            raise CoordinationError(f"Duplicate evaluation finding_id: {finding_id}")
        seen_finding_ids.add(finding_id)

        finding_problems = list(package_problems)
        for key, expected in snapshot_ref.items():
            actual = finding.get(key)
            if actual != expected:
                finding_problems.append(f"finding {key} does not match the snapshot package")
        finding_available = not finding_problems
        issue_id = _stable_id(
            "issue", scenario_id, input_hash, model_hash, finding_id
        )
        finding_ref = {
            **snapshot_ref,
            "finding_id": finding_id,
            "state": "available" if finding_available else "unavailable",
            "reasons": sorted(set(finding_problems)),
        }

        raw_entity_ids = finding.get("entity_ids", [])
        entity_ids = sorted(
            {item for item in raw_entity_ids if isinstance(item, str)}
            if isinstance(raw_entity_ids, list)
            else set()
        )
        entity_refs = []
        available_destinations: dict[tuple[str, str], dict[str, Any]] = {}
        for entity_id in entity_ids:
            entity = entities.get(entity_id)
            entity_exists = isinstance(entity, dict)
            entity_ref = {
                "entity_id": entity_id,
                "label": entity.get("label", entity_id) if entity_exists else entity_id,
                "state": "available" if entity_exists else "unavailable",
                "destinations": [],
            }
            references = by_entity.get(entity_id)
            if not entity_exists:
                entity_ref["state"] = "unavailable"
                entity_ref["reason"] = "finding references an entity absent from the snapshot"

            if not entity_exists:
                if isinstance(references, list) and references:
                    entity_ref["destinations"].extend(
                        _unavailable_destination_from_reference(
                            entity_id,
                            reference,
                            "finding references an entity absent from the snapshot",
                        )
                        for reference in references
                    )
                else:
                    entity_ref["destinations"].append(
                        _unavailable_destination(
                            entity_id,
                            None,
                            None,
                            None,
                            "finding references an entity absent from the snapshot",
                        )
                    )
            elif not isinstance(references, list) or not references:
                entity_ref["destinations"].append(
                    _unavailable_destination(
                        entity_id,
                        None,
                        None,
                        None,
                        "no occurrence destination is registered in the view inventory",
                    )
                )
            else:
                seen_destinations: set[tuple[str, str, str]] = set()
                for reference in references:
                    destination = _resolve_destination(
                        entity_id, reference, views_by_id
                    )
                    if destination is None:
                        entity_ref["destinations"].append(
                            _unavailable_destination_from_reference(
                                entity_id,
                                reference,
                                _destination_problem(entity_id, reference, views_by_id),
                            )
                        )
                        continue
                    key = (
                        destination["view_id"],
                        destination["view_file"],
                        destination["occurrence_id"],
                    )
                    if key in seen_destinations:
                        entity_ref["destinations"].append(
                            _unavailable_destination(
                                entity_id,
                                *key,
                                "duplicate occurrence reference in the view inventory",
                            )
                        )
                        continue
                    seen_destinations.add(key)

                    view_id, view_file, occurrence_id = key
                    if not finding_available:
                        entity_ref["destinations"].append(
                            _unavailable_destination(
                                entity_id,
                                view_id,
                                view_file,
                                occurrence_id,
                                "; ".join(sorted(set(finding_problems))),
                            )
                        )
                        continue
                    view = views_by_id[view_id][0]
                    definition = view.get("definition")
                    if not isinstance(definition, dict) or not definition:
                        entity_ref["destinations"].append(
                            _unavailable_destination(
                                entity_id,
                                view_id,
                                view_file,
                                occurrence_id,
                                "the original view definition is not captured",
                            )
                        )
                        continue
                    definition_hash = digest(definition)
                    destination_record = {
                        "entity_id": entity_id,
                        "view_id": view_id,
                        "view_file": view_file,
                        "occurrence_id": occurrence_id,
                        "view_definition_hash": definition_hash,
                        "state": "available",
                        "reason": None,
                    }
                    entity_ref["destinations"].append(destination_record)
                    group = available_destinations.setdefault(
                        (view_id, view_file),
                        {
                            "view_id": view_id,
                            "view_file": view_file,
                            "view_definition_hash": definition_hash,
                            "view_definition": deepcopy(definition),
                            "selected_occurrences": [],
                        },
                    )
                    group["selected_occurrences"].append(
                        {"entity_id": entity_id, "occurrence_id": occurrence_id}
                    )

            entity_ref["destinations"].sort(key=_destination_sort_key)
            entity_refs.append(entity_ref)

        viewpoints = []
        for (view_id, view_file), destination in sorted(available_destinations.items()):
            destination["selected_occurrences"].sort(
                key=lambda item: (item["entity_id"], item["occurrence_id"])
            )
            viewpoint_id = _stable_id("viewpoint", issue_id, view_id, view_file)
            viewpoints.append(
                {
                    "viewpoint_id": viewpoint_id,
                    "view_id": view_id,
                    "view_file": view_file,
                    "state": "available",
                    "view_definition_ref": {
                        "view_id": view_id,
                        "view_file": view_file,
                        "definition_hash": destination["view_definition_hash"],
                        "definition": destination["view_definition"],
                    },
                    "selected_occurrences": destination["selected_occurrences"],
                }
            )

        unavailable = [
            {
                "kind": "finding",
                "finding_id": finding_id,
                "state": "unavailable",
                "reason": reason,
            }
            for reason in sorted(set(finding_problems))
        ]
        if not entity_ids:
            unavailable.append(
                {
                    "kind": "viewpoint",
                    "finding_id": finding_id,
                    "view_id": None,
                    "view_file": None,
                    "occurrence_id": None,
                    "state": "unavailable",
                    "reason": "finding has no linked entity from which to select a view",
                }
            )
        for entity_ref in entity_refs:
            if entity_ref["state"] == "unavailable":
                unavailable.append(
                    {
                        "kind": "entity",
                        "entity_id": entity_ref["entity_id"],
                        "state": "unavailable",
                        "reason": entity_ref.get("reason", "entity reference is unresolved"),
                    }
                )
            for destination in entity_ref["destinations"]:
                if destination["state"] != "available":
                    unavailable.append(
                        {
                            "kind": "destination",
                            "entity_id": destination["entity_id"],
                            "view_id": destination["view_id"],
                            "view_file": destination["view_file"],
                            "occurrence_id": destination["occurrence_id"],
                            "state": "unavailable",
                            "reason": destination["reason"],
                        }
                    )
        summary = {
            key: finding.get(key)
            for key in ("rule_id", "status", "coverage", "severity", "message")
        }
        issues.append(
            {
                "issue_id": issue_id,
                "finding_id": finding_id,
                "finding_ref": finding_ref,
                "summary": summary,
                "entity_refs": entity_refs,
                "viewpoints": viewpoints,
                "unavailable_references": unavailable,
            }
        )

    return {
        "schema_version": 1,
        "snapshot_ref": snapshot_ref,
        "view_inventory_ref": {
            "scenario_id": inventory.get("scenario_id"),
            "input_hash": inventory.get("input_hash"),
            "schema_version": inventory.get("schema_version"),
        },
        "issues": issues,
        "limitation": (
            "Saved viewpoints reference captured package evidence and actual SVG occurrences; "
            "they do not store or edit geometry."
        ),
    }


def _identity(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _stable_id(prefix: str, *parts: str | None) -> str:
    return f"{prefix}-{digest(list(parts))[:20]}"


def _safe_relative_svg(value: object) -> bool:
    if not isinstance(value, str) or not value or any(ord(char) < 32 for char in value):
        return False
    if "\\" in value or "%" in value or "?" in value or "#" in value:
        return False
    from urllib.parse import urlsplit

    address = urlsplit(value)
    if address.scheme or address.netloc or address.path != value or value.startswith("/"):
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} for part in parts) and value.lower().endswith(
        ".svg"
    )


def _resolve_destination(
    entity_id: str, reference: object, views_by_id: dict[str, list[dict[str, Any]]]
) -> dict[str, str] | None:
    if not isinstance(reference, dict):
        return None
    view_id = reference.get("view_id")
    view_file = reference.get("view")
    occurrence_id = reference.get("occurrence_id")
    if not all(isinstance(item, str) and item for item in (view_id, view_file, occurrence_id)):
        return None
    if not _safe_relative_svg(view_file):
        return None
    matching = views_by_id.get(view_id, [])
    if len(matching) != 1:
        return None
    view = matching[0]
    if view.get("file") != view_file:
        return None
    occurrences = view.get("occurrences", [])
    if not isinstance(occurrences, list) or not any(
        isinstance(item, dict)
        and item.get("entity_id") == entity_id
        and item.get("occurrence_id") == occurrence_id
        for item in occurrences
    ):
        return None
    definition = view.get("definition")
    if not isinstance(definition, dict) or not definition:
        return None
    return {"view_id": view_id, "view_file": view_file, "occurrence_id": occurrence_id}


def _destination_problem(
    entity_id: str, reference: object, views_by_id: dict[str, list[dict[str, Any]]]
) -> str:
    if not isinstance(reference, dict):
        return "occurrence reference is malformed"
    view_id = reference.get("view_id")
    view_file = reference.get("view")
    occurrence_id = reference.get("occurrence_id")
    if not all(isinstance(item, str) and item for item in (view_id, view_file, occurrence_id)):
        return "view ID, SVG file or occurrence ID is missing"
    if not _safe_relative_svg(view_file):
        return "SVG path is unsafe or is not a package-relative .svg path"
    matching = views_by_id.get(view_id, [])
    if not matching:
        return "view ID is absent from the view inventory"
    if len(matching) != 1:
        return "view ID is ambiguous in the view inventory"
    view = matching[0]
    if view.get("file") != view_file:
        return "view file does not match the inventoried view ID"
    occurrences = view.get("occurrences", [])
    if not isinstance(occurrences, list) or not any(
        isinstance(item, dict)
        and item.get("entity_id") == entity_id
        and item.get("occurrence_id") == occurrence_id
        for item in occurrences
    ):
        return "occurrence ID is absent for this entity in the inventoried view"
    definition = view.get("definition")
    if not isinstance(definition, dict) or not definition:
        return "the original view definition is not captured"
    return "occurrence reference is unresolved"


def _unavailable_destination(
    entity_id: str,
    view_id: str | None,
    view_file: str | None,
    occurrence_id: str | None,
    reason: str,
) -> dict[str, Any]:
    return {
        "entity_id": entity_id,
        "view_id": view_id,
        "view_file": view_file,
        "occurrence_id": occurrence_id,
        "state": "unavailable",
        "reason": reason,
    }


def _unavailable_destination_from_reference(
    entity_id: str, reference: object, reason: str
) -> dict[str, Any]:
    if not isinstance(reference, dict):
        return _unavailable_destination(entity_id, None, None, None, reason)
    return _unavailable_destination(
        entity_id,
        _identity(reference.get("view_id")),
        _identity(reference.get("view")),
        _identity(reference.get("occurrence_id")),
        reason,
    )


def _destination_sort_key(destination: dict[str, Any]) -> tuple[str, str, str]:
    return tuple(
        destination.get(key) or "" for key in ("view_id", "view_file", "occurrence_id")
    )


__all__ = ["build_viewpoints"]

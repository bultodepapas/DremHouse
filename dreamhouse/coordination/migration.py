"""Prepare an explicitly reviewable semantic rebase of a coordination study.

Rebasing updates only the study's baseline fingerprint. Every requested field must
still satisfy its original expected-value precondition against the current baseline.
The resulting study remains an unadopted candidate and must be fully reevaluated.
"""

from __future__ import annotations

import math
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

from .model import (
    CoordinationError,
    _number,
    _validate_changes,
    _validate_entities,
    digest,
    editable_fields,
    json_text,
    model_digest,
)

_STUDY_FIELDS = {
    "schema_version",
    "scenario_id",
    "base",
    "status",
    "base_model_hash",
    "changes",
    "view_settings",
    "evidence_records",
}


def _validate_study_document(document: Any) -> dict:
    if not isinstance(document, dict):
        raise CoordinationError("Study must be a JSON object")
    unknown = set(document) - _STUDY_FIELDS
    if unknown:
        raise CoordinationError(f"Unknown project fields: {sorted(unknown)}")
    missing = {"schema_version", "scenario_id", "base", "base_model_hash", "changes"} - set(
        document
    )
    if missing:
        raise CoordinationError(f"Missing project fields: {sorted(missing)}")
    if type(document.get("schema_version")) is not int or document["schema_version"] != 1:
        raise CoordinationError("Expected schema_version 1 and base PB_B37_P2_B28")
    if document.get("base") != "PB_B37_P2_B28":
        raise CoordinationError("Expected schema_version 1 and base PB_B37_P2_B28")
    if not isinstance(document.get("scenario_id"), str) or not document["scenario_id"].strip():
        raise CoordinationError("scenario_id must be nonempty")
    if "status" in document and (
        not isinstance(document["status"], str) or not document["status"].strip()
    ):
        raise CoordinationError("status must be a nonempty string")
    old_hash = document.get("base_model_hash")
    if old_hash is not None and (not isinstance(old_hash, str) or not old_hash.strip()):
        raise CoordinationError("base_model_hash must be a nonempty string or null")
    if not isinstance(document.get("changes"), dict):
        raise CoordinationError("changes must be an object keyed by canonical entity ID")
    return document


def _current_baseline(snapshot: Any) -> tuple[dict, str, str]:
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("baseline"), dict):
        raise CoordinationError("Current snapshot must include a resolved baseline")
    baseline = snapshot["baseline"]
    if not all(isinstance(baseline.get(key), dict) for key in ("geometry", "entities")):
        raise CoordinationError("Current snapshot baseline is missing geometry or entities")
    discipline_inputs = baseline.get("discipline_inputs", {})
    if not isinstance(discipline_inputs, dict):
        raise CoordinationError("Current snapshot baseline discipline_inputs must be an object")
    computed_hash = model_digest(baseline["geometry"], baseline["entities"], discipline_inputs)
    snapshot_hash = snapshot.get("base_model_hash")
    if not isinstance(snapshot_hash, str) or computed_hash != snapshot_hash:
        raise CoordinationError("Current snapshot baseline fingerprint is inconsistent")
    input_hash = snapshot.get("input_hash")
    if not isinstance(input_hash, str) or not input_hash.strip():
        raise CoordinationError("Current snapshot input_hash is missing")
    return baseline, computed_hash, input_hash


def _same_expected_value(expected: Any, current: Any, field: str) -> bool:
    """Mirror the model validator's numeric tolerance without accepting booleans."""
    if isinstance(expected, bool):
        raise CoordinationError(f"expected.{field} must be a finite number or null")
    if expected is not None:
        expected = _number(expected, f"expected.{field}")
    if isinstance(current, bool):
        raise CoordinationError(f"Current baseline value for {field} is invalid")
    if isinstance(current, (int, float)):
        if expected is None:
            return False
        current = _number(current, f"current.{field}")
        return math.isclose(expected, current, rel_tol=0, abs_tol=1e-9)
    return expected == current


def _validate_and_compare(document: dict, baseline: dict, current_hash: str) -> dict:
    changes = document["changes"]
    entities = baseline["entities"]
    report_changes: dict[str, dict] = {}
    validator_changes: dict[str, dict] = {}
    conflicts: list[dict] = []

    for entity_id, change in changes.items():
        if not isinstance(entity_id, str) or entity_id not in entities:
            raise CoordinationError(
                f"Unknown canonical entity ID {entity_id}; aliases are read-only"
            )
        entity = entities[entity_id]
        if entity["kind"] not in {"opening", "door"} or entity["geometry"]["shape"] == "unresolved":
            raise CoordinationError(f"{entity_id} has no supported editable source parameters yet")
        if entity["status"] != "active":
            raise CoordinationError(
                f"{entity_id} is not active; adoption requires a separate decision"
            )
        if not isinstance(change, dict) or set(change) != {"expected", "set"}:
            raise CoordinationError(f"{entity_id}: supply exactly expected and set objects")
        expected, setters = change["expected"], change["set"]
        if (
            not isinstance(setters, dict)
            or not setters
            or not isinstance(expected, dict)
            or set(expected) != set(setters)
        ):
            raise CoordinationError(f"{entity_id}: expected must cover exactly the changed fields")

        supported = editable_fields(entity)
        field_report = {}
        rebased_expected = {}
        for field, requested in setters.items():
            if field not in supported:
                raise CoordinationError(f"{entity_id}.{field}: unsupported authoring field")
            old_value = expected[field]
            current_value = entity["parameters"].get(field)
            matches = _same_expected_value(old_value, current_value, field)
            field_status = "ready" if matches else "conflict"
            field_report[field] = {
                "expected": deepcopy(old_value),
                "current": deepcopy(current_value),
                "requested": deepcopy(requested),
                "precondition_matches": matches,
                "status": field_status,
            }
            rebased_expected[field] = deepcopy(current_value)
            if not matches:
                conflict = {
                    "entity_id": entity_id,
                    "field": field,
                    "expected": deepcopy(old_value),
                    "current": deepcopy(current_value),
                    "requested": deepcopy(requested),
                }
                conflicts.append(conflict)

        report_changes[entity_id] = {"fields": field_report}
        validator_changes[entity_id] = {
            "expected": rebased_expected,
            "set": deepcopy(setters),
        }

    # Exercise the same field, range, numeric, and geometry contracts used by project
    # resolution, using current values only in a disposable validator copy. This checks
    # setter validity even when the original expected values produce reportable conflicts.
    validator_entities = deepcopy(entities)
    _validate_changes(
        {"base_model_hash": current_hash, "changes": validator_changes},
        validator_entities,
        current_hash,
        baseline["geometry"],
    )
    _validate_entities(validator_entities)
    return {"changes": report_changes, "conflicts": conflicts}


def prepare_migration(document: dict, current_snapshot: dict) -> dict:
    """Return a review report and, only if safe, a study pinned to the current baseline.

    A ready result proves that every edited field's original expected value still
    matches the current baseline under the model's existing 1e-9 numeric tolerance.
    It does not establish equivalence of unchanged context or authorize adoption.
    """
    source = _validate_study_document(document)
    from .view_definitions import validate_view_settings

    validate_view_settings(source.get("view_settings", {}))
    from .evidence import validate_records

    validate_records(source.get("evidence_records", []))
    baseline, current_hash, current_input_hash = _current_baseline(current_snapshot)
    comparison = _validate_and_compare(source, baseline, current_hash)
    ready = not comparison["conflicts"]

    report = {
        "schema_version": 1,
        "operation": "study-semantic-rebase",
        "scenario_id": source["scenario_id"],
        "base": source["base"],
        "source_document_fingerprint": digest(source),
        "source_base_model_hash": source.get("base_model_hash"),
        "current_base_model_hash": current_hash,
        "current_snapshot_input_hash": current_input_hash,
        "source_hash_matches_current": source.get("base_model_hash") == current_hash,
        "ready_to_apply": ready,
        "context_equivalence": "not_asserted",
        "authority": "unadopted coordination candidate; no design or publication authority",
        "required_next_step": "fully reevaluate the migrated study against the current baseline",
        "changes": comparison["changes"],
        "conflicts": comparison["conflicts"],
    }

    candidate = None
    if ready:
        candidate = deepcopy(source)
        candidate["base_model_hash"] = current_hash
    return {"study": candidate, "report": report}


def _stage(path: Path, content: str) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def _publish_exclusive(temporary: Path, destination: Path) -> None:
    """Atomically link a completed sibling temp file without replacing a destination."""
    os.link(temporary, destination)


def _unlink_if_ours(destination: Path, temporary: Path) -> None:
    try:
        created, staged = destination.stat(), temporary.stat()
        if (created.st_dev, created.st_ino) == (staged.st_dev, staged.st_ino):
            destination.unlink()
    except FileNotFoundError:
        pass


def write_migration(
    plan: dict,
    study_path: Path | str,
    report_path: Path | str | None = None,
) -> dict[str, str]:
    """Exclusively write a migration report and, when ready, the new study.

    A blocked plan writes the report only. Destinations must have existing parent
    directories. Existing destinations are never overwritten. If publishing either
    member of a ready pair fails, any study created by this call is removed.
    """
    if not isinstance(plan, dict) or not isinstance(plan.get("report"), dict):
        raise CoordinationError("Migration plan must contain a report")
    report = plan["report"]
    study = plan.get("study")
    ready = report.get("ready_to_apply") is True
    if ready != (study is not None):
        raise CoordinationError("Migration plan readiness and study candidate disagree")

    requested_destination = Path(study_path)
    requested_report = (
        Path(report_path)
        if report_path is not None
        else requested_destination.with_suffix(".migration.json")
    )
    for target in (requested_destination, requested_report):
        if target.is_symlink():
            raise CoordinationError(f"Destination must not be a symlink: {target}")
    destination = requested_destination.resolve()
    report_destination = requested_report.resolve()
    if destination == report_destination:
        raise CoordinationError("Study and migration report destinations must be different")
    for target in (destination, report_destination):
        if not target.parent.is_dir():
            raise CoordinationError(f"Destination directory does not exist: {target.parent}")

    report_temporary = None
    study_temporary = None
    created_study = False
    try:
        report_temporary = _stage(report_destination, json_text(report))
        if study is not None:
            study_temporary = _stage(destination, json_text(study))
        if study_temporary is not None:
            _publish_exclusive(study_temporary, destination)
            created_study = True
        _publish_exclusive(report_temporary, report_destination)
    except BaseException:
        if created_study and study_temporary is not None:
            _unlink_if_ours(destination, study_temporary)
        raise
    finally:
        if report_temporary is not None:
            report_temporary.unlink(missing_ok=True)
        if study_temporary is not None:
            study_temporary.unlink(missing_ok=True)

    result = {"report": str(report_destination)}
    if study is not None:
        result["study"] = str(destination)
    return result

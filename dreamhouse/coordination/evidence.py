"""Retain authored review records and invalidate them against their declared dependencies.

A current record verifies traceability, never reviewer competence or design approval.
"""

from __future__ import annotations

import re
from copy import deepcopy
from pathlib import Path, PurePosixPath

from dreamhouse.coordination.model import CoordinationError, digest, file_hash

_HASH = re.compile(r"^[0-9a-f]{64}$")


def validate_records(records: object) -> list[dict]:
    if not isinstance(records, list):
        raise CoordinationError("evidence_records must be a list")
    seen = set()
    fields = {
        "id",
        "entity_ids",
        "context_paths",
        "purpose",
        "milestone",
        "responsible_role",
        "recorded_status",
        "reviewed_fingerprint",
        "source",
    }
    for record in records:
        if not isinstance(record, dict) or set(record) != fields:
            raise CoordinationError("Evidence record fields are incomplete or unknown")
        for key in ["id", "purpose", "milestone", "responsible_role"]:
            if not isinstance(record[key], str) or not record[key].strip():
                raise CoordinationError(f"Evidence {key} must be nonempty")
        if record["id"] in seen:
            raise CoordinationError("Duplicate evidence identity")
        seen.add(record["id"])
        if not isinstance(record["recorded_status"], str) or record["recorded_status"] not in {
            "submitted",
            "reviewed",
            "accepted",
            "rejected",
        }:
            raise CoordinationError("Unknown evidence recorded_status")
        for key in ["entity_ids", "context_paths"]:
            values = record[key]
            if (
                not isinstance(values, list)
                or any(not isinstance(v, str) or not v for v in values)
                or len(values) != len(set(values))
            ):
                raise CoordinationError(f"Invalid evidence {key}")
        if not record["entity_ids"] and not record["context_paths"]:
            raise CoordinationError("Evidence must declare dependencies")
        for path in record["context_paths"]:
            if path.split(".")[0] not in {"geometry", "discipline_inputs"}:
                raise CoordinationError("Evidence context must name geometry or discipline_inputs")
        if not isinstance(record["reviewed_fingerprint"], str) or not _HASH.fullmatch(
            record["reviewed_fingerprint"]
        ):
            raise CoordinationError("Evidence reviewed_fingerprint must be a SHA-256 value")
        source = record["source"]
        if not isinstance(source, dict) or set(source) != {"path", "sha256"}:
            raise CoordinationError("Evidence source requires path and sha256")
        raw = source["path"]
        if (
            not isinstance(raw, str)
            or not raw
            or "\\" in raw
            or PurePosixPath(raw).is_absolute()
            or ".." in PurePosixPath(raw).parts
        ):
            raise CoordinationError("Evidence source must be repository-relative")
        if not isinstance(source["sha256"], str) or not _HASH.fullmatch(source["sha256"]):
            raise CoordinationError("Evidence source sha256 is invalid")
    return deepcopy(records)


def evidence_source_paths(records: list[dict], root: Path) -> list[Path]:
    paths = []
    for record in validate_records(records):
        path = root / record["source"]["path"]
        if not path.resolve().is_relative_to(root.resolve()):
            raise CoordinationError("Evidence source escapes repository")
        # Missing historical evidence remains an explicit missing dependency.
        if path.is_file():
            paths.append(path)
    return paths


def dependency_fingerprint(snapshot: dict, entity_ids: list[str], context_paths: list[str]) -> dict:
    entities = {}
    context = {}
    missing = []
    for identifier in sorted(entity_ids):
        entity = snapshot.get("entities", {}).get(identifier)
        if entity is None:
            missing.append(identifier)
            continue
        entities[identifier] = {
            k: entity.get(k)
            for k in [
                "id",
                "kind",
                "family",
                "level",
                "status",
                "geometry",
                "parameters",
                "relationships",
            ]
        }
    for path in sorted(context_paths):
        value = snapshot
        try:
            for key in path.split("."):
                value = value[key]
        except (KeyError, TypeError):
            missing.append(path)
            continue
        context[path] = value
    return {
        "fingerprint": None if missing else digest({"entities": entities, "context": context}),
        "missing_dependencies": missing,
    }


def assess_evidence(snapshot: dict) -> dict:
    rows = []
    for record in snapshot.get("evidence_records", []):
        dependency = dependency_fingerprint(snapshot, record["entity_ids"], record["context_paths"])
        observed = snapshot.get("evidence_source_hashes", {}).get(record["source"]["path"])
        source_state = (
            "missing"
            if observed is None
            else "current"
            if observed == record["source"]["sha256"]
            else "changed"
        )
        dependency_state = (
            "unavailable"
            if dependency["missing_dependencies"]
            else "current"
            if dependency["fingerprint"] == record["reviewed_fingerprint"]
            else "changed"
        )
        rows.append(
            dict(
                record,
                current_fingerprint=dependency["fingerprint"],
                missing_dependencies=dependency["missing_dependencies"],
                source_state=source_state,
                dependency_state=dependency_state,
                review_required=source_state != "current" or dependency_state != "current",
                approval_verified=False,
            )
        )
    return {
        "schema_version": 1,
        "scenario_id": snapshot.get("scenario_id"),
        "input_hash": snapshot.get("input_hash"),
        "records": rows,
        "engineering_approval": False,
        "limitation": "Recorded reviewer status is authored evidence metadata. Freshness does not authenticate a reviewer or close governance conflicts.",
    }


def capture_source_hashes(records: list[dict], root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): file_hash(p) for p in evidence_source_paths(records, root)
    }

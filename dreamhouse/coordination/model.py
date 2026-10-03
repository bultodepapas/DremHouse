"""Resolve archived design sources and explicit study changes into one shared snapshot.

Historical loaders retain their design assertions. This adapter does not rewrite their
sources: changed geometry lives in a versioned JSON study with optimistic base checks.
"""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

from dreamhouse.generate_p2_b28 import load_b28_model
from dreamhouse.generate_pb_b37 import load_b37_model

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROJECT = Path(__file__).with_name("project.json")
HASH_POLICY = "python-json-sort-keys-utf8-v1; finite numbers; not RFC8785/JCS"


class CoordinationError(ValueError):
    """Invalid inputs, ambiguous ownership, or stale source assumptions."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CoordinationError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> Any:
    def reject(value: str) -> None:
        raise CoordinationError(f"Non-finite JSON number in {path}: {value}")

    def finite_float(value: str) -> float:
        number = float(value)
        if not math.isfinite(number):
            reject(value)
        return number

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=reject,
        parse_float=finite_float,
    )


def json_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2) + "\n"


def digest(value: Any) -> str:
    return hashlib.sha256(json_text(value).encode("utf-8")).hexdigest()


def model_digest(geometry: dict, entities: dict, discipline_inputs: dict | None = None) -> str:
    """Hash resolved meaning separately from source paths and build provenance."""
    return digest(
        {
            "geometry": geometry,
            "discipline_inputs": discipline_inputs or {},
            "entities": {
                key: {
                    field: value
                    for field, value in entity.items()
                    if field not in {"source", "working_source"}
                }
                for key, entity in entities.items()
            },
        }
    )


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependency_hashes(project_path: Path) -> dict[str, str]:
    """Conservative full rebuild: all package code/data plus publication/governance inputs.

    This deliberately over-invalidates. It never claims a minimal dependency closure.
    Generated review packages are outside these roots and cannot hash themselves.
    """
    paths = {
        p
        for p in (ROOT / "dreamhouse").rglob("*")
        if p.is_file() and p.suffix in {".py", ".json"} and "__pycache__" not in p.parts
    }
    paths.update(
        ROOT / name
        for name in (
            "pyproject.toml",
            "planos/actual/catalog.json",
            "docs/00_gobernanza/constitucion_del_proyecto.md",
            "docs/00_gobernanza/fuentes_precedencia_y_conflictos.md",
            "docs/00_gobernanza/registro_decisiones.md",
            "docs/00_gobernanza/language_and_translation_policy.md",
        )
    )
    catalog = read_json(ROOT / "planos/actual/catalog.json")
    for entry in catalog["drawings"]:
        source = ROOT / entry["source"]
        paths.add(source)
        paths.update(source.parent.glob("*manifest*.json"))
    paths.update((ROOT / "showcase").rglob("*.woff*"))
    paths.update((ROOT / "dreamhouse/coordination/fonts").glob("*.ttf"))
    paths.add(project_path.resolve())
    result = {}
    for path in sorted(paths):
        # Validate even historical JSON before legacy permissive loaders read it.
        if path.suffix == ".json":
            read_json(path)
        key = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        result[key] = file_hash(path)
    return result


def _number(value: Any, field: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise CoordinationError(f"{field} must be a finite number")
    if positive and value <= 0:
        raise CoordinationError(f"{field} must be greater than zero")
    return float(value)


def _geometry(shape: str, x0=None, x1=None, y0=None, y1=None, z0=None, z1=None) -> dict:
    return {"shape": shape, "x0": x0, "x1": x1, "y0": y0, "y1": y1, "z0": z0, "z1": z1}


def _entity(
    entity_id: str,
    kind: str,
    level: str,
    family: str,
    source: str,
    key: str,
    geometry: dict,
    parameters=None,
    *,
    host=None,
    spaces=(),
    aliases=(),
    status="active",
    label=None,
) -> dict:
    return {
        "id": entity_id,
        "kind": kind,
        "label": label or entity_id,
        "level": level,
        "family": family,
        "aliases": list(aliases),
        "status": status,
        "source": {"path": source, "key": key},
        "geometry": geometry,
        "parameters": parameters or {},
        "relationships": {"host_id": host, "space_ids": list(spaces)},
    }


def _opening_geometry(p: dict, hall: dict) -> dict:
    if p.get("facade") == "ROOF":
        return _geometry(
            "rect", p["x_m"], p["x_m"] + p["length_m"], p["y_m"], p["y_m"] + p["width_m"]
        )
    start, end = p["start_m"], p["start_m"] + p["width_m"]
    face = p.get("facade")
    if face in {"A", "B"}:
        x0, x1, y0, y1 = start, end, 0 if face == "A" else hall["width_m"], 0
        y1 = y0
    elif face in {"FRONT", "REAR"}:
        x0 = x1 = 0 if face == "FRONT" else hall["length_m"]
        y0, y1 = start, end
    elif face == "INTERIOR":
        if p["axis"] == "X":
            x0, x1, y0, y1 = start, end, p["fixed_m"], p["fixed_m"]
        else:
            x0, x1, y0, y1 = p["fixed_m"], p["fixed_m"], start, end
    else:
        return _geometry("unresolved")
    level, sill, height = p.get("level_m"), p.get("sill_m"), p.get("height_m")
    z0 = level + sill if level is not None and sill is not None else None
    z1 = z0 + height if z0 is not None and height is not None else None
    return _geometry("opening", x0, x1, y0, y1, z0, z1)


def _baseline() -> tuple[dict, dict, dict]:
    pb, p2 = load_b37_model(), load_b28_model()
    roof = read_json(ROOT / "dreamhouse/rooflight_b12.json")
    stair = read_json(ROOT / "dreamhouse/stair_core.json")
    hall = {"length_m": float(pb["envelope"]["length"]), "width_m": float(pb["envelope"]["width"])}
    geometry = {
        "hall": hall,
        "p2": {
            "x_m": p2["envelope"]["x"],
            "length_m": p2["envelope"]["length"],
            "width_m": p2["envelope"]["width"],
            "level_m": stair["levels"]["p2_finished_floor"],
        },
        "axes": "X front-to-rear; Y Side A-to-B; Z above PB; units m",
    }
    entities = {}

    def add(e):
        if e["id"] in entities:
            raise CoordinationError(f"Duplicate entity ID: {e['id']}")
        entities[e["id"]] = e

    # Reference planes provide a host location, never a selected wall assembly/solid.
    for level in ("PB", "P2"):
        for face in ("A", "B", "FRONT", "REAR"):
            low = geometry["p2"]["x_m"] if level == "P2" and face in {"A", "B"} else 0.0
            width = hall["length_m"] - low if face in {"A", "B"} else hall["width_m"]
            params = {
                "facade": face,
                "start_m": low,
                "width_m": width,
                "level_m": 0 if level == "PB" else geometry["p2"]["level_m"],
                "sill_m": None,
                "height_m": None,
                "capability": "reference plane; no wall solid",
            }
            g = _opening_geometry(params, hall)
            if level == "P2" and face == "FRONT":
                g["x0"] = g["x1"] = geometry["p2"]["x_m"]
            g["shape"] = "line"
            add(
                _entity(
                    f"HOST-{level}-{face}",
                    "wall",
                    level,
                    "derived.facade_planes",
                    "dreamhouse/generate_pb_b37.py"
                    if level == "PB"
                    else "dreamhouse/generate_p2_b28.py",
                    "resolved envelope",
                    g,
                    params,
                    status="context",
                )
            )
    alias_map = {w["p2_id"]: [w["id"]] for w in pb["bedroom_glazing"]}
    for collection in ("technical_glazing", "workstation_glazing", "optional_opening_studies"):
        for w in pb[collection]:
            p = {
                "facade": w["side"],
                "start_m": w["x0"],
                "width_m": w["x1"] - w["x0"],
                "height_m": w["height"],
                "sill_m": w["sill"],
                "level_m": 0.0,
                "modules": w.get("modules"),
            }
            source = (
                "dreamhouse/pb_b05.json"
                if collection == "technical_glazing"
                else "dreamhouse/window_daylight_d083.json"
            )
            key = {
                "technical_glazing": "technical_glazing",
                "workstation_glazing": "ground_floor_workstation_glazing",
                "optional_opening_studies": "optional_dining_study",
            }[collection]
            add(
                _entity(
                    w["id"],
                    "opening",
                    "PB",
                    "PB." + collection,
                    source,
                    f"{key}[id={w['id']}]",
                    _opening_geometry(p, hall),
                    p,
                    host=f"HOST-PB-{w['side']}",
                    status="study" if collection == "optional_opening_studies" else "active",
                )
            )
    for w in p2["windows"]:
        face = {"south": "A", "north": "B", "east": "REAR"}[w["edge"]]
        p = {
            "facade": face,
            "start_m": w["from"],
            "width_m": w["to"] - w["from"],
            "height_m": w["height"],
            "sill_m": w["sill"],
            "level_m": geometry["p2"]["level_m"],
            "modules": w.get("modules"),
        }
        if w["id"] in alias_map:
            source = "dreamhouse/window_daylight_d083.json"
            source_key = f"upper_floor_bedroom_windows[id={w['id']}]"
            p["module_width_m"] = pb["window_daylight_coordination"]["module_width_m"]
        elif w["id"] == "W-WELL":
            source, source_key = "dreamhouse/p2_b15.json", "windows[id=W-WELL]"
        elif w["id"] == "W-EGRESS-P2":
            source, source_key = "dreamhouse/p2_b27_delta.json", "change.rescue_window"
        else:
            raise CoordinationError(f"Native window source owner missing: {w['id']}")
        add(
            _entity(
                w["id"],
                "opening",
                "P2",
                "P2.windows",
                source,
                source_key,
                _opening_geometry(p, hall),
                p,
                host=f"HOST-P2-{face}",
                spaces=[w["room_id"]],
                aliases=alias_map.get(w["id"], []),
            )
        )
    for w in roof["rooflights"]:
        p = {
            "facade": "ROOF",
            "x_m": w["x"],
            "y_m": w["y"],
            "length_m": w["length"],
            "width_m": w["width"],
            "height_m": None,
            "sill_m": None,
            "level_m": None,
        }
        add(
            _entity(
                w["id"],
                "opening",
                "PROJECT",
                "ROOFLIGHTS.rooflights",
                "dreamhouse/rooflight_b12.json",
                f"rooflights[id={w['id']}]",
                _opening_geometry(p, hall),
                p,
            )
        )
    for space in p2["spaces"]:
        add(
            _entity(
                space["id"],
                "space",
                "P2",
                "P2.spaces",
                "dreamhouse/generate_p2_b28.py",
                f"load_b28_model().spaces[id={space['id']}]",
                _geometry(
                    "rect",
                    space["x"],
                    space["x"] + space["w"],
                    space["y"],
                    space["y"] + space["d"],
                    geometry["p2"]["level_m"],
                ),
                {"suite": space.get("suite"), "space_kind": space.get("kind")},
            )
        )
    for space in pb["core"]:
        add(
            _entity(
                "PB-" + space["id"],
                "space",
                "PB",
                "PB.core",
                "dreamhouse/generate_pb_b37.py",
                f"load_b37_model().core[id={space['id']}]",
                _geometry(
                    "rect", pb["great_wall"]["x"], hall["length_m"], space["y0"], space["y1"], 0
                ),
                label=space["name"],
            )
        )
        add(
            _entity(
                "PB-DOOR-" + space["id"],
                "door",
                "PB",
                "PB.core.doors",
                "dreamhouse/generate_pb_b37.py",
                f"load_b37_model().core[id={space['id']}].door_y",
                _geometry("unresolved"),
                {
                    "width_m": space["door_width"],
                    "source_door_y": space["door_y"],
                    "height_m": None,
                    "reason": "CF-013: door_y anchor differs between archived renderers; endpoints unresolved",
                },
                spaces=["PB-" + space["id"]],
                status="context",
            )
        )
    for door in p2["doors"]:
        horizontal = door["wall"] == "horizontal"
        host = "HOST-P2-" + "--".join(sorted(door["connects"]))
        a, b = [entities[i]["geometry"] for i in door["connects"]]
        fixed = door["y"] if horizontal else door["x"]
        g = (
            _geometry("line", max(a["x0"], b["x0"]), min(a["x1"], b["x1"]), fixed, fixed)
            if horizontal
            else _geometry("line", fixed, fixed, max(a["y0"], b["y0"]), min(a["y1"], b["y1"]))
        )
        if host not in entities:
            add(
                _entity(
                    host,
                    "wall",
                    "P2",
                    "derived.space_boundaries",
                    "dreamhouse/generate_p2_b28.py",
                    "shared space boundary; assembly unassigned",
                    g,
                    status="context",
                )
            )
        p = {
            "facade": "INTERIOR",
            "axis": "X" if horizontal else "Y",
            "fixed_m": fixed,
            "start_m": door["at"],
            "width_m": door["width"],
            "height_m": None,
            "sill_m": 0.0,
            "level_m": geometry["p2"]["level_m"],
            "door_kind": door["kind"],
            "swing": door.get("swing"),
        }
        add(
            _entity(
                door["id"],
                "door",
                "P2",
                "P2.doors",
                "dreamhouse/generate_p2_b28.py",
                f"load_b28_model().doors[id={door['id']}]",
                _opening_geometry(p, hall),
                p,
                host=host,
                spaces=door["connects"],
            )
        )
    for door in pb["front_openings"]:
        p = {
            "facade": "FRONT",
            "start_m": door["y0"],
            "width_m": door["width"],
            "height_m": door["height"],
            "sill_m": 0.0,
            "level_m": 0.0,
        }
        add(
            _entity(
                door["id"],
                "door",
                "PB",
                "PB.front_openings",
                "dreamhouse/pb_b05.json",
                f"front_openings[id={door['id']}]",
                _opening_geometry(p, hall),
                p,
                host="HOST-PB-FRONT",
                label=door["name"],
            )
        )
    for door in pb["exterior_doors"]:
        # Archived plan and rear elevation disagree on the y anchor. Keep the ambiguity visible.
        add(
            _entity(
                door["id"],
                "door",
                "PB",
                "PB.exterior_doors",
                "dreamhouse/pb_b05.json",
                f"exterior_doors[id={door['id']}]",
                _geometry("unresolved"),
                {
                    "width_m": door["width"],
                    "height_m": None,
                    "source_y": door["y"],
                    "reason": "CF-013: rear door anchor differs between archived renderers; CF-011 also affects EXT-ESC level",
                },
                host="HOST-PB-REAR",
                status="context",
            )
        )
    for column in stair["structure"]["column_reservations"]:
        half = stair["structure"]["column_reservation_size"] / 2
        add(
            _entity(
                column["id"],
                "reservation",
                "PROJECT",
                "SC01.column_reservations",
                "dreamhouse/stair_core.json",
                f"structure.column_reservations[id={column['id']}]",
                _geometry(
                    "rect",
                    column["x"] - half,
                    column["x"] + half,
                    column["y"] - half,
                    column["y"] + half,
                ),
                {"capability": "plan reservation only; section and vertical extents unresolved"},
                status="context",
            )
        )
    for key in ("lower_flight", "upper_flight", "intermediate_landing"):
        s = stair["stair"][key]
        add(
            _entity(
                s["id"],
                "stair",
                "PROJECT",
                "SC01.stair",
                "dreamhouse/stair_core.json",
                f"stair.{key}",
                _geometry(
                    "rect",
                    s["x0"],
                    s["x1"],
                    s["y0"],
                    s["y1"],
                    s.get("z0", s.get("level")),
                    s.get("z1", s.get("level")),
                ),
                {"capability": "plan/rise envelope; not a stair solid or headroom verification"},
                status="context",
            )
        )
    # Context is captured once at the same source boundary as geometry. Adapters must
    # overlay normalized entity values rather than reread adopted opening definitions.
    discipline_inputs = {
        "equipment": {
            "pb": pb,
            "catalog": read_json(ROOT / "dreamhouse/equipment/catalog.json"),
            "layout": read_json(ROOT / "dreamhouse/equipment/layout_v04.json"),
        },
        "programme": {"p2": p2},
        "structure": {
            "system": read_json(ROOT / "dreamhouse/structure/structure_system.json"),
            "roof_space": read_json(ROOT / "dreamhouse/structure/roof_truss_space.json"),
            "e1_space": read_json(ROOT / "dreamhouse/structure/e1_screening_space.json"),
            "stair": stair,
            "rooflights": roof,
        },
    }
    return geometry, entities, discipline_inputs


def editable_fields(entity: dict) -> tuple[str, ...]:
    """Expose the exact authoring contract used by both validation and coverage."""
    if (
        entity["kind"] not in {"opening", "door"}
        or entity["geometry"]["shape"] == "unresolved"
        or entity["status"] != "active"
    ):
        return ()
    if entity["parameters"].get("facade") == "ROOF":
        return ("length_m", "width_m", "x_m", "y_m")
    if entity["kind"] == "door":
        return ("height_m", "sill_m", "start_m", "width_m")
    return ("height_m", "modules", "sill_m", "start_m", "width_m")


def _validate_changes(document: dict, entities: dict, base_hash: str, geometry: dict) -> None:
    changes = document.get("changes")
    if not isinstance(changes, dict):
        raise CoordinationError("changes must be an object keyed by canonical entity ID")
    if changes and document.get("base_model_hash") != base_hash:
        raise CoordinationError(
            "Study base_model_hash is stale or absent; regenerate and review the study template"
        )
    for entity_id, change in changes.items():
        if entity_id not in entities:
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
        allowed = editable_fields(entity)
        for field, value in setters.items():
            if field not in allowed:
                raise CoordinationError(f"{entity_id}.{field}: unsupported authoring field")
            old = entity["parameters"].get(field)
            expected_value = expected[field]
            matches = expected_value == old
            if isinstance(old, (int, float)) and not isinstance(expected_value, bool):
                expected_value = _number(expected_value, f"{entity_id}.expected.{field}")
                matches = math.isclose(expected_value, old, rel_tol=0, abs_tol=1e-9)
            if isinstance(expected_value, bool) or not matches:
                raise CoordinationError(
                    f"{entity_id}.{field}: stale expected value {expected[field]!r}; base is {old!r}"
                )
            value = _number(
                value,
                f"{entity_id}.{field}",
                positive=field in {"width_m", "height_m", "length_m", "modules"},
            )
            if field == "modules" and not value.is_integer():
                raise CoordinationError("modules must be a positive integer")
            if field == "sill_m" and value < 0:
                raise CoordinationError("sill_m cannot be negative")
            entity["parameters"][field] = int(value) if field == "modules" else value
        entity["geometry"] = _opening_geometry(entity["parameters"], geometry["hall"])
        entity["working_source"] = {"key": f"changes.{entity_id}.set"}


def _validate_entities(entities: dict) -> None:
    identities = set(entities)
    aliases: set[str] = set()
    for entity in entities.values():
        for alias in entity["aliases"]:
            if alias in identities or alias in aliases:
                raise CoordinationError(f"Identity/alias collision: {alias}")
            aliases.add(alias)
        for ref in [entity["relationships"]["host_id"], *entity["relationships"]["space_ids"]]:
            if ref is not None and ref not in entities:
                raise CoordinationError(f"Broken relationship {entity['id']} -> {ref}")
        for axis in ("x", "y", "z"):
            a, b = (entity["geometry"].get(axis + suffix) for suffix in ("0", "1"))
            for value in (a, b):
                if value is not None:
                    _number(value, entity["id"] + ".geometry." + axis)
            if a is not None and b is not None and a > b:
                raise CoordinationError(f"Reversed geometry extent for {entity['id']}: {axis}")


def resolve_project(project_path: Path | str = DEFAULT_PROJECT) -> dict:
    """Read inputs once, validate them, apply explicit changes, and return an independent snapshot."""
    path = Path(project_path).resolve()
    before = dependency_hashes(path)
    document = read_json(path)
    if (
        not isinstance(document, dict)
        or type(document.get("schema_version")) is not int
        or document.get("schema_version") != 1
        or document.get("base") != "PB_B37_P2_B28"
    ):
        raise CoordinationError("Expected schema_version 1 and base PB_B37_P2_B28")
    unknown = set(document) - {
        "schema_version",
        "scenario_id",
        "base",
        "status",
        "base_model_hash",
        "changes",
    }
    if unknown:
        raise CoordinationError(f"Unknown project fields: {sorted(unknown)}")
    if not isinstance(document.get("scenario_id"), str) or not document["scenario_id"].strip():
        raise CoordinationError("scenario_id must be nonempty")
    geometry, entities, discipline_inputs = _baseline()
    drawing_catalog, drawing_source_evidence = _drawing_sources()
    _validate_entities(entities)
    baseline = {
        "geometry": deepcopy(geometry),
        "entities": deepcopy(entities),
        "discipline_inputs": deepcopy(discipline_inputs),
    }
    base_hash = model_digest(geometry, entities, discipline_inputs)
    _validate_changes(document, entities, base_hash, geometry)
    _validate_entities(entities)
    after = dependency_hashes(path)
    if before != after:
        raise CoordinationError("Inputs changed while resolving; retry from a stable source set")
    for entity in entities.values():
        if "working_source" in entity:
            entity["working_source"]["path"] = (
                str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
            )
    return {
        "schema_version": 1,
        "scenario_id": document["scenario_id"],
        "status": "coordination candidate; not construction authority",
        "hash_policy": HASH_POLICY,
        "input_hash": digest({"dependencies": before, "scenario": document}),
        "model_hash": model_digest(geometry, entities, discipline_inputs),
        "base_model_hash": base_hash,
        "geometry": geometry,
        "entities": entities,
        "discipline_inputs": discipline_inputs,
        "drawing_catalog": drawing_catalog,
        "drawing_source_evidence": drawing_source_evidence,
        "baseline": baseline,
        "build_dependencies": before,
        "project_path": path.relative_to(ROOT).as_posix()
        if path.is_relative_to(ROOT)
        else str(path),
        "dependency_policy": "conservative full rebuild; no incremental cache",
        "changes_requested": deepcopy(document["changes"]),
        "open_conflicts": ["CF-009", "CF-010", "CF-011", "CF-012", "CF-013"],
    }


def study_template(snapshot: dict, scenario_id: str) -> dict:
    return {
        "schema_version": 1,
        "scenario_id": scenario_id,
        "base": "PB_B37_P2_B28",
        "status": "unadopted study; source changes require review",
        "base_model_hash": snapshot["base_model_hash"],
        "changes": {},
    }


def _drawing_sources() -> tuple[dict, dict]:
    """Capture publication provenance once, without making it dimensional authority."""
    catalog = read_json(ROOT / "planos/actual/catalog.json")
    evidence = {}
    canonical_names = set()
    for entry in catalog["drawings"]:
        identifier = entry["id"]
        if identifier in evidence or entry["canonical"] in canonical_names:
            raise CoordinationError("Duplicate publication drawing identity")
        canonical_names.add(entry["canonical"])
        source = (ROOT / entry["source"]).resolve()
        if not source.is_relative_to(ROOT / "planos") or source.suffix != ".svg":
            raise CoordinationError(f"Invalid drawing source: {entry['source']}")
        manifest_path = source.parent / "manifest.json"
        manifest = read_json(manifest_path)
        names = {
            value.get("path") if isinstance(value, dict) else value
            for value in manifest.get("outputs", [])
        }
        if source.name not in names or manifest.get("revision") != entry["source_revision"]:
            raise CoordinationError(f"Drawing provenance disagrees with catalog: {identifier}")
        evidence[identifier] = {
            "source": entry["source"],
            "source_revision": entry["source_revision"],
            "source_status": entry["status"],
            "source_sha256": file_hash(source),
            "source_manifest": manifest_path.relative_to(ROOT).as_posix(),
            "manifest_sha256": file_hash(manifest_path),
            "generator": manifest.get("generator", "undeclared"),
        }
    return catalog, evidence


def current_drawing_inventory() -> dict:
    catalog = read_json(ROOT / "planos/actual/catalog.json")
    return {
        "schema_version": 1,
        "status": "published aliases retained; isolated candidate views are separate",
        "drawings": [
            {
                "id": d["id"],
                "source": d["source"],
                "revision": d["source_revision"],
                "sha256": file_hash(ROOT / d["source"]),
                "shared_snapshot_consumer": False,
                "migration_status": "pending explicit consumer migration and publication",
            }
            for d in catalog["drawings"]
        ],
    }

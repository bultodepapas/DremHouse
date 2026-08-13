"""Load the canonical scenario manifest and fail closed on stale inputs."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema import CheckResult, ModelError, check

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = Path(__file__).with_name("project_v04.json")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ModelError(f"Cannot read project input {path}: {error}") from error
    if not isinstance(value, dict):
        raise ModelError(f"Project input must be a JSON object: {path}")
    return value


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_json_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ProjectModel:
    """Loaded scenario with exact sources, content hashes, and canonical geometry."""

    manifest: dict[str, Any]
    scenario_id: str
    geometry: dict[str, Any]
    models: dict[str, dict[str, Any]]
    source_paths: dict[str, Path]
    source_hashes: dict[str, str]
    checks: tuple[CheckResult, ...]

    @property
    def input_hash(self) -> str:
        return canonical_json_hash(
            {
                "manifest_revision": self.manifest["revision"],
                "scenario_id": self.scenario_id,
                "geometry": self.geometry,
                "source_hashes": self.source_hashes,
            }
        )

    def require_valid(self) -> None:
        failures = [item for item in self.checks if item.status == "FAIL"]
        if failures:
            detail = "; ".join(f"{item.rule_id}: {item.message}" for item in failures)
            raise ModelError(f"Canonical project model failed closed: {detail}")


def _close(a: object, b: object, tolerance: float = 1e-9) -> bool:
    return math.isclose(float(a), float(b), abs_tol=tolerance)


def _cross_model_checks(
    geometry: dict[str, Any],
    models: dict[str, dict[str, Any]],
    source_hashes: dict[str, str],
    expected_hashes: dict[str, str],
) -> list[CheckResult]:
    pb = models["pb"]
    p2 = models["p2"]
    rooflights = models["rooflights"]
    structure = models["structure"]
    sg = structure["geometry"]
    pg = pb["envelope"]
    p2g = p2["envelope"]
    roof = pb["roof"]
    canonical_roof = geometry["roof"]
    double_height = geometry["double_height"]

    checks = [
        check(
            "MODEL-SOURCE-HASHES",
            all(source_hashes.get(key) == value for key, value in expected_hashes.items()),
            "Every locked source hash matches the active manifest",
        ),
        check(
            "MODEL-HALL-ENVELOPE",
            _close(pg["length"], geometry["hall"]["length_m"])
            and _close(pg["width"], geometry["hall"]["width_m"])
            and _close(sg["nave_length_m"], geometry["hall"]["length_m"])
            and _close(sg["nave_width_m"], geometry["hall"]["width_m"]),
            "PB and structure match the canonical 36 x 18 m hall envelope",
        ),
        check(
            "MODEL-P2-ENVELOPE",
            _close(p2g["x"], geometry["p2"]["x_m"])
            and _close(p2g["length"], geometry["p2"]["length_m"])
            and _close(p2g["width"], geometry["p2"]["width_m"])
            and _close(sg["p2_start_x_m"], geometry["p2"]["x_m"])
            and _close(sg["p2_length_m"], geometry["p2"]["length_m"]),
            "P2 and structure match the canonical 15 x 18 m rear envelope",
        ),
        check(
            "MODEL-GREAT-WALL",
            _close(pb["great_wall"]["x"], geometry["great_wall_x_m"])
            and _close(sg["great_wall_x_m"], geometry["great_wall_x_m"]),
            "PB and structure use one canonical Great Wall plane",
        ),
        check(
            "MODEL-ROOF",
            all(
                _close(value, canonical_roof[key])
                for key, value in (
                    ("low_eave_m", roof["low_eave"]),
                    ("high_eave_m", roof["high_eave"]),
                    ("rise_m", roof["rise"]),
                )
            )
            and roof["low_side"] == canonical_roof["low_side"]
            and rooflights["roof"]["low_side"] == canonical_roof["low_side"],
            "PB and rooflights match the canonical mono-pitch roof",
        ),
        check(
            "MODEL-DOUBLE-HEIGHT",
            all(
                _close(rooflights["double_height"][key], value)
                for key, value in double_height.items()
                if key in {"x0", "x1", "y0", "y1"}
            ),
            "Rooflights use the canonical 21 x 18 m double-height zone",
        ),
    ]
    return checks


def load_project(
    scenario_id: str = "D054_HALF_CENTRES",
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    verify_hashes: bool = True,
) -> ProjectModel:
    """Load one declared scenario and verify every cross-model contract."""

    manifest = _read_json(manifest_path)
    scenarios = manifest.get("scenarios", {})
    if scenario_id not in scenarios:
        raise ModelError(f"Unknown scenario {scenario_id!r}; choose from {sorted(scenarios)}")
    source_specs = manifest.get("sources", {})
    scenario = scenarios[scenario_id]
    source_ids = scenario.get("sources", {})
    required_roles = {"pb", "p2", "rooflights", "structure", "roof_space", "e1_space"}
    if set(source_ids) != required_roles:
        raise ModelError(
            f"Scenario {scenario_id} must define exactly {sorted(required_roles)} sources"
        )

    models: dict[str, dict[str, Any]] = {}
    source_paths: dict[str, Path] = {}
    source_hashes: dict[str, str] = {}
    expected_hashes: dict[str, str] = {}
    for role, source_id in source_ids.items():
        if source_id not in source_specs:
            raise ModelError(f"Scenario {scenario_id} references unknown source {source_id}")
        spec = source_specs[source_id]
        path = REPOSITORY_ROOT / spec["path"]
        models[role] = _read_json(path)
        source_paths[role] = path
        source_hashes[role] = sha256_path(path)
        locked_hash = spec.get("sha256")
        if verify_hashes and locked_hash:
            expected_hashes[role] = locked_hash

    checks = _cross_model_checks(
        manifest["canonical_geometry"], models, source_hashes, expected_hashes
    )
    project = ProjectModel(
        manifest=manifest,
        scenario_id=scenario_id,
        geometry=manifest["canonical_geometry"],
        models=models,
        source_paths=source_paths,
        source_hashes=source_hashes,
        checks=tuple(checks),
    )
    project.require_valid()
    return project

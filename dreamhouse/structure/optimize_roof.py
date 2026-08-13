"""Deterministic roof-truss enumeration and Pareto exploration.

This module wraps the existing E0 inputs without changing them. It screens a
defined axial subproblem under vertical gravity and uplift components only.
Every output remains a research hypothesis and is ineligible for design or
cost selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .analysis import G
from .materials import Steel, materials_from_json
from .profiles import Profile, profile
from .truss import Truss2D, TrussAnalysisError, TrussMember
from .truss_grammar import TrussLayout, generate_roof_truss

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = Path(__file__).with_name("structure_system.json")
DEFAULT_SPACE = Path(__file__).with_name("roof_truss_space.json")
DEFAULT_JSON_OUTPUT = ROOT / "docs/08_investigacion/roof_truss_exploration_e0.json"
DEFAULT_REPORT_OUTPUT = ROOT / "docs/08_investigacion/roof_truss_exploration_e0.md"


@dataclass(frozen=True)
class RoofTrussCandidate:
    modulation_id: str
    bay_m: float
    n_bays: int
    topology: str
    panel_count: int
    depth_shape: str
    centre_depth_m: float
    end_depth_fraction: float

    @property
    def candidate_id(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
        return f"{self.modulation_id}-{self.topology}-{digest}"


@dataclass(frozen=True)
class PairEvaluation:
    screening_passed: bool
    chord_profile: str
    web_profile: str
    truss_mass_kg: float
    total_roof_truss_mass_kg: float
    max_strength_ratio: float
    max_deflection_ratio: float
    governing_ratio: float
    max_deflection_m: float
    controlling_combo: str
    controlling_member: int
    reaction_vertical_error_n: float
    failure_reasons: tuple[str, ...]


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _validate_space(space: dict, cfg: dict) -> None:
    modulation_ids = {item["id"] for item in cfg["geometry"]["modulations"]}
    requested = space.get("modulation_ids", [])
    if not requested or len(requested) != len(set(requested)):
        raise ValueError("The exploration requires unique modulation IDs")
    unknown = set(requested) - modulation_ids
    if unknown:
        raise ValueError(f"Unknown modulation IDs: {sorted(unknown)}")
    for key in ("topologies", "panel_counts", "depth_options"):
        if not space.get(key):
            raise ValueError(f"The exploration space has no {key}")
    choices = space.get("profile_choices", {})
    for group in ("chord", "web"):
        names = choices.get(group, [])
        if not names or len(names) != len(set(names)):
            raise ValueError(f"Profile group {group!r} must contain unique choices")
        for name in names:
            candidate = profile(name)
            if not name.startswith("HSS"):
                raise ValueError(
                    f"The axial truss explorer currently accepts HSS profiles only: {name}"
                )
            if candidate.area_m2 <= 0.0 or candidate.iy_m4 <= 0.0:
                raise ValueError(f"Invalid profile properties for {name}")


def build_candidates(cfg: dict, space: dict) -> list[RoofTrussCandidate]:
    _validate_space(space, cfg)
    modulation_by_id = {item["id"]: item for item in cfg["geometry"]["modulations"]}
    span = float(cfg["geometry"]["nave_width_m"])
    candidates: list[RoofTrussCandidate] = []
    for modulation_id in space["modulation_ids"]:
        modulation = modulation_by_id[modulation_id]
        for topology in space["topologies"]:
            for panel_count in space["panel_counts"]:
                for depth in space["depth_options"]:
                    ratio = float(depth["centre_depth_span_ratio"])
                    if not math.isfinite(ratio) or ratio <= 0.0:
                        raise ValueError("Depth/span ratios must be positive and finite")
                    candidates.append(
                        RoofTrussCandidate(
                            modulation_id=modulation_id,
                            bay_m=float(modulation["bay_m"]),
                            n_bays=int(modulation["n_bays"]),
                            topology=str(topology),
                            panel_count=int(panel_count),
                            depth_shape=str(depth["shape"]),
                            centre_depth_m=span / ratio,
                            end_depth_fraction=float(depth["end_depth_fraction"]),
                        )
                    )
    ids = [candidate.candidate_id for candidate in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("Candidate hashing produced duplicate IDs")
    return candidates


def _build_model(
    layout: TrussLayout,
    steel: Steel,
    chord: Profile,
    web: Profile,
) -> Truss2D:
    profiles = {"chord": chord, "web": web}
    members = [
        TrussMember(
            item.i,
            item.j,
            steel.e_pa,
            profiles[item.group].area_m2,
            group=item.group,
            profile_name=profiles[item.group].name,
        )
        for item in layout.members
    ]
    left, right = layout.support_nodes
    return Truss2D(
        nodes=list(layout.nodes),
        members=members,
        fixes={left: {"ux", "uz"}, right: {"uz"}},
    )


def _top_nodal_loads(layout: TrussLayout, line_load_down_n_m: float) -> np.ndarray:
    if not math.isfinite(line_load_down_n_m):
        raise ValueError("Roof line load must be finite")
    loads = np.zeros(2 * len(layout.nodes))
    xs = [layout.nodes[node][0] for node in layout.top_nodes]
    tributaries: list[float] = []
    for index, x in enumerate(xs):
        left = 0.0 if index == 0 else (xs[index - 1] + x) / 2.0
        right = xs[-1] if index == len(xs) - 1 else (x + xs[index + 1]) / 2.0
        tributaries.append(right - left)
    for node, tributary in zip(layout.top_nodes, tributaries):
        loads[2 * node + 1] -= line_load_down_n_m * tributary
    return loads


def _member_mass_kg(model: Truss2D, chord: Profile, web: Profile) -> float:
    profiles = {"chord": chord, "web": web}
    return sum(
        model.member_length(member) * profiles[member.group].mass_kg_m for member in model.members
    )


def _compression_capacity_n(
    member: TrussMember,
    length_m: float,
    member_profile: Profile,
    steel: Steel,
    phi_c: float,
    effective_length_factor: float,
) -> float:
    yield_capacity = steel.fy_pa * member.area_m2
    euler_capacity = (
        math.pi**2 * steel.e_pa * member_profile.iy_m4 / (effective_length_factor * length_m) ** 2
    )
    return phi_c * min(yield_capacity, euler_capacity)


def evaluate_profile_pair(
    candidate: RoofTrussCandidate,
    cfg: dict,
    space: dict,
    steel: Steel,
    chord: Profile,
    web: Profile,
) -> tuple[PairEvaluation, TrussLayout]:
    geometry = cfg["geometry"]
    layout = generate_roof_truss(
        topology=candidate.topology,
        depth_shape=candidate.depth_shape,
        span_m=float(geometry["nave_width_m"]),
        eave_low_m=float(geometry["eave_low_m"]),
        eave_high_m=float(geometry["eave_high_m"]),
        panel_count=candidate.panel_count,
        centre_depth_m=candidate.centre_depth_m,
        end_depth_fraction=candidate.end_depth_fraction,
    )
    model = _build_model(layout, steel, chord, web)
    truss_mass = _member_mass_kg(model, chord, web)
    span = float(geometry["nave_width_m"])
    self_weight_n_m = truss_mass * G / span
    roof_dead_n_m = cfg["loads"]["dead"]["roof_kpa"] * candidate.bay_m * 1e3
    roof_live_n_m = cfg["loads"]["live"]["roof_kpa"] * candidate.bay_m * 1e3
    wind = cfg["loads"]["wind"]
    external = (wind["Cp_roof_windward"] + wind["Cp_roof_leeward"]) / 2.0
    uplift_n_m = (
        wind["qz_eave_kpa_hypothesis"]
        * 1e3
        * (external - abs(wind.get("Cp_internal", 0.0)))
        * candidate.bay_m
    )
    case_loads = {
        "D": _top_nodal_loads(layout, roof_dead_n_m + self_weight_n_m),
        "L": _top_nodal_loads(layout, roof_live_n_m),
        "WU": _top_nodal_loads(layout, uplift_n_m),
    }

    phi_c = float(cfg["criteria"]["phi_axial"])
    effective_length = float(space["analysis"]["effective_length_factor"])
    profiles = {"chord": chord, "web": web}
    max_strength_ratio = 0.0
    controlling_combo = ""
    controlling_member = -1
    vertical_error = 0.0
    try:
        for combination in cfg["combinations"]:
            loads = sum(
                (
                    float(combination["factors"].get(case, 0.0)) * vector
                    for case, vector in case_loads.items()
                ),
                np.zeros(2 * len(layout.nodes)),
            )
            solution = model.solve(loads)
            support_vertical = sum(
                solution.reactions_n[2 * node + 1] for node in layout.support_nodes
            )
            vertical_error = max(
                vertical_error,
                abs(support_vertical + float(np.sum(loads[1::2]))),
            )
            for index, (member, force) in enumerate(zip(model.members, solution.member_forces_n)):
                member_profile = profiles[member.group]
                if force >= 0.0:
                    capacity = phi_c * steel.fy_pa * member.area_m2
                else:
                    capacity = _compression_capacity_n(
                        member,
                        model.member_length(member),
                        member_profile,
                        steel,
                        phi_c,
                        effective_length,
                    )
                ratio = abs(float(force)) / max(capacity, 1e-12)
                if ratio > max_strength_ratio:
                    max_strength_ratio = ratio
                    controlling_combo = str(combination["id"])
                    controlling_member = index

        service_factors = (
            {"D": 1.0, "L": 1.0},
            {"D": 1.0, "WU": 1.0},
        )
        max_deflection = 0.0
        for factors in service_factors:
            loads = sum(
                (factor * case_loads[case] for case, factor in factors.items()),
                np.zeros(2 * len(layout.nodes)),
            )
            solution = model.solve(loads)
            max_deflection = max(
                max_deflection,
                max(
                    abs(float(solution.displacements_m[2 * node + 1])) for node in layout.top_nodes
                ),
            )
    except TrussAnalysisError as exc:
        failed = PairEvaluation(
            screening_passed=False,
            chord_profile=chord.name,
            web_profile=web.name,
            truss_mass_kg=truss_mass,
            total_roof_truss_mass_kg=math.inf,
            max_strength_ratio=math.inf,
            max_deflection_ratio=math.inf,
            governing_ratio=math.inf,
            max_deflection_m=math.inf,
            controlling_combo="",
            controlling_member=-1,
            reaction_vertical_error_n=math.inf,
            failure_reasons=(f"analysis_error:{exc}",),
        )
        return failed, layout

    deflection_limit = span / float(str(cfg["criteria"]["deflection_roof_total"]).split("/")[-1])
    deflection_ratio = max_deflection / deflection_limit
    reasons: list[str] = []
    if max_strength_ratio > 1.0 + 1e-9:
        reasons.append("axial_strength_or_euler_buckling")
    if deflection_ratio > 1.0 + 1e-9:
        reasons.append("roof_deflection")
    if vertical_error > 1e-5:
        reasons.append("vertical_equilibrium")
    detail = float(cfg["criteria"]["detail_factor_principales"])
    total_mass = truss_mass * (candidate.n_bays + 1) * (1.0 + detail)
    governing_ratio = max(max_strength_ratio, deflection_ratio)
    return (
        PairEvaluation(
            screening_passed=not reasons,
            chord_profile=chord.name,
            web_profile=web.name,
            truss_mass_kg=truss_mass,
            total_roof_truss_mass_kg=total_mass,
            max_strength_ratio=max_strength_ratio,
            max_deflection_ratio=deflection_ratio,
            governing_ratio=governing_ratio,
            max_deflection_m=max_deflection,
            controlling_combo=controlling_combo,
            controlling_member=controlling_member,
            reaction_vertical_error_n=vertical_error,
            failure_reasons=tuple(reasons),
        ),
        layout,
    )


def evaluate_candidate(
    candidate: RoofTrussCandidate,
    cfg: dict,
    space: dict,
    steel: Steel,
) -> dict:
    evaluations: list[tuple[PairEvaluation, TrussLayout]] = []
    for chord_name in space["profile_choices"]["chord"]:
        for web_name in space["profile_choices"]["web"]:
            evaluations.append(
                evaluate_profile_pair(
                    candidate,
                    cfg,
                    space,
                    steel,
                    profile(chord_name),
                    profile(web_name),
                )
            )
    feasible = [item for item in evaluations if item[0].screening_passed]
    pool = feasible or evaluations
    selected, layout = min(
        pool,
        key=lambda item: (
            item[0].total_roof_truss_mass_kg,
            item[0].governing_ratio,
            item[0].chord_profile,
            item[0].web_profile,
        ),
    )
    crossing_penalty = float(space["analysis"]["fabrication_crossing_penalty"])
    fabrication_proxy = layout.member_count + crossing_penalty * layout.crossing_count

    def rounded_finite(value: float, digits: int) -> float | None:
        return round(value, digits) if math.isfinite(value) else None

    return {
        "candidate_id": candidate.candidate_id,
        **asdict(candidate),
        "screening_passed": selected.screening_passed,
        "selected_profiles": {
            "chord": selected.chord_profile,
            "web": selected.web_profile,
        },
        "truss_mass_kg": rounded_finite(selected.truss_mass_kg, 3),
        "total_roof_truss_mass_kg": rounded_finite(selected.total_roof_truss_mass_kg, 3),
        "max_strength_ratio": rounded_finite(selected.max_strength_ratio, 6),
        "max_deflection_ratio": rounded_finite(selected.max_deflection_ratio, 6),
        "governing_ratio": rounded_finite(selected.governing_ratio, 6),
        "max_deflection_m": rounded_finite(selected.max_deflection_m, 6),
        "controlling_combo": selected.controlling_combo,
        "controlling_member": selected.controlling_member,
        "reaction_vertical_error_n": rounded_finite(selected.reaction_vertical_error_n, 9),
        "member_count": layout.member_count,
        "joint_count": layout.joint_count,
        "crossing_count": layout.crossing_count,
        "max_node_degree": layout.max_node_degree,
        "fabrication_proxy": round(fabrication_proxy, 3),
        "evaluated_profile_pairs": len(evaluations),
        "failure_reasons": list(selected.failure_reasons),
        "analysis_scope": "vertical_gravity_and_global_uplift_axial_truss_screening_only",
        "ranking_eligible_for_design": False,
    }


def dominates(left: dict, right: dict, objectives: Iterable[str]) -> bool:
    keys = tuple(objectives)
    return all(left[key] <= right[key] for key in keys) and any(
        left[key] < right[key] for key in keys
    )


def pareto_front(rows: list[dict], objectives: Iterable[str]) -> list[dict]:
    keys = tuple(objectives)
    feasible = [row for row in rows if row["screening_passed"]]
    front = [
        candidate
        for candidate in feasible
        if not any(
            dominates(other, candidate, keys)
            for other in feasible
            if other["candidate_id"] != candidate["candidate_id"]
        )
    ]
    return sorted(
        front,
        key=lambda row: tuple(row[key] for key in keys) + (row["candidate_id"],),
    )


def explore(cfg: dict, space: dict) -> dict:
    steel = materials_from_json(cfg)["S355"]
    candidates = build_candidates(cfg, space)
    rows = [evaluate_candidate(candidate, cfg, space, steel) for candidate in candidates]
    objectives = tuple(space["analysis"]["pareto_objectives"])
    front = pareto_front(rows, objectives)
    input_payload = json.dumps(
        {"model": cfg, "space": space}, sort_keys=True, separators=(",", ":")
    )
    return {
        "project": space["project"],
        "input_sha256": hashlib.sha256(input_payload.encode("utf-8")).hexdigest(),
        "engine": "deterministic_enumeration_v1",
        "objectives_minimized": list(objectives),
        "candidate_count": len(rows),
        "screening_passed_count": sum(row["screening_passed"] for row in rows),
        "pareto_count": len(front),
        "scope_limitations": [
            "vertical gravity and global roof uplift components only",
            "linear elastic pin-jointed axial model",
            "Euler screening uses the single catalogue Iy value and K=1.0 hypothesis",
            "no local buckling, connection, chord local bending, second-order, fatigue, fire, diaphragm, lateral-system, erection, foundation, or code-compliance design",
            "mass covers roof trusses and the configured principal-detail allowance only; columns, secondary steel, connections, coatings, transport, and foundations are excluded",
        ],
        "pareto_front": front,
        "candidates": rows,
    }


def markdown_report(results: dict) -> str:
    front = results["pareto_front"]
    lines = [
        "# E0 Parametric Roof-Truss Exploration",
        "",
        "**Status:** research hypothesis; not for design, pricing, fabrication, or construction  ",
        f"**Version:** {results['project']['revision']}  ",
        f"**Date:** {results['project']['date']}  ",
        f"**Input SHA-256:** `{results['input_sha256']}`",
        "",
        "## Outcome",
        "",
        (
            f"The deterministic explorer evaluated **{results['candidate_count']}** geometries; "
            f"**{results['screening_passed_count']}** passed the defined axial subproblem and "
            f"**{results['pareto_count']}** remain non-dominated under the three declared proxies."
        ),
        (
            "No candidate selects D-019. The table is a shortlist for a competent structural "
            "engineer and a later E1 model."
        ),
        "",
        "| Candidate | Module | Topology | Panels | Depth | Chord / web | Roof truss mass | Members + crossings | Governing ratio |",
        "|---|---|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in front:
        lines.append(
            "| {candidate_id} | {modulation_id} | {topology} / {depth_shape} | "
            "{panel_count} | {centre_depth_m:.2f} m | {chord} / {web} | "
            "{mass:.1f} kg | {members} + {crossings} | {ratio:.3f} |".format(
                candidate_id=row["candidate_id"],
                modulation_id=row["modulation_id"],
                topology=row["topology"],
                depth_shape=row["depth_shape"],
                panel_count=row["panel_count"],
                centre_depth_m=row["centre_depth_m"],
                chord=row["selected_profiles"]["chord"],
                web=row["selected_profiles"]["web"],
                mass=row["total_roof_truss_mass_kg"],
                members=row["member_count"],
                crossings=row["crossing_count"],
                ratio=row["governing_ratio"],
            )
        )
    lines.extend(
        [
            "",
            "## Objective interpretation",
            "",
            "- `total_roof_truss_mass_kg`: all roof-truss lines plus the E0 principal-detail allowance; it is not total building steel.",
            "- `fabrication_proxy`: member count plus twice the number of unconnected diagonal crossings; it is dimensionless and is not a price.",
            "- `governing_ratio`: the larger of axial/Euler strength and L/180 roof-deflection ratios; lower means more screening reserve.",
            "",
            "## Mandatory E1 progression",
            "",
            *[f"- {item}" for item in results["scope_limitations"]],
            "",
            "The JSON companion contains every candidate, rejected alternatives, profile pair count, controlling combination, equilibrium residual, and reproducibility hash.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(results: dict, json_output: Path, report_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    report_output.write_text(markdown_report(results), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--space", type=Path, default=DEFAULT_SPACE)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    arguments = parser.parse_args(argv)
    cfg = _read_json(arguments.model)
    space = _read_json(arguments.space)
    results = explore(cfg, space)
    write_outputs(results, arguments.json_output, arguments.report_output)
    print(
        f"Evaluated {results['candidate_count']} candidates; "
        f"{results['screening_passed_count']} passed; "
        f"{results['pareto_count']} on the Pareto front."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

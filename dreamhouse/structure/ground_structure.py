"""Linear-programming ground-structure study for truss-form inspiration.

The formulation minimizes volume proxy with shared continuous member areas,
joint equilibrium, and symmetric axial-stress limits over multiple load cases.
It is a plastic lower-bound layout study: compatibility, displacement,
buckling, catalogue sections, joints, and fabrication are deliberately absent.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .materials import materials_from_json
from .optimize_roof import DEFAULT_MODEL, DEFAULT_SPACE, ROOT, _read_json
from .truss_grammar import generate_roof_truss

DEFAULT_JSON_OUTPUT = ROOT / "docs/08_investigacion/ground_structure_m60_e0.json"
DEFAULT_SVG_OUTPUT = ROOT / "docs/08_investigacion/ground_structure_m60_e0.svg"


class GroundStructureError(RuntimeError):
    """The linear ground-structure problem is invalid or infeasible."""


@dataclass(frozen=True)
class GroundMember:
    i: int
    j: int


@dataclass(frozen=True)
class ActiveGroundMember:
    i: int
    j: int
    area_cm2: float
    length_m: float
    force_by_case_kn: dict[str, float]


@dataclass(frozen=True)
class GroundStructureSolution:
    success: bool
    status: str
    objective_m_cm2: float
    areas_cm2: tuple[float, ...]
    forces_by_case_kn: dict[str, tuple[float, ...]]
    active_members: tuple[ActiveGroundMember, ...]
    max_equilibrium_error_kn: float


def _member_geometry(
    nodes: Sequence[tuple[float, float]], member: GroundMember
) -> tuple[float, float, float]:
    if not 0 <= member.i < len(nodes) or not 0 <= member.j < len(nodes):
        raise GroundStructureError(f"Ground member references missing nodes {member.i}, {member.j}")
    if member.i == member.j:
        raise GroundStructureError(f"Ground member {member.i}-{member.j} has zero topology")
    x1, z1 = nodes[member.i]
    x2, z2 = nodes[member.j]
    length = math.hypot(x2 - x1, z2 - z1)
    if not math.isfinite(length) or length <= 0.0:
        raise GroundStructureError(f"Degenerate ground member {member.i}-{member.j}")
    return length, (x2 - x1) / length, (z2 - z1) / length


def solve_ground_structure(
    *,
    nodes: Sequence[tuple[float, float]],
    members: Sequence[GroundMember],
    fixes: Mapping[int, set[str]],
    load_cases_kn: Mapping[str, np.ndarray],
    allowable_stress_mpa: float,
    active_area_threshold_cm2: float = 0.05,
) -> GroundStructureSolution:
    """Solve a continuous-area, multiple-load-case ground-structure LP."""

    try:
        from scipy.optimize import linprog
    except ImportError as exc:
        raise GroundStructureError(
            "SciPy is required for the ground-structure study; install .[optimization]"
        ) from exc

    if not nodes or not members or not load_cases_kn:
        raise GroundStructureError("Nodes, candidate members, and load cases are required")
    if not math.isfinite(allowable_stress_mpa) or allowable_stress_mpa <= 0.0:
        raise GroundStructureError("Allowable stress must be positive and finite")
    if not math.isfinite(active_area_threshold_cm2) or active_area_threshold_cm2 < 0.0:
        raise GroundStructureError("Active-area threshold must be finite and non-negative")
    pairs = [tuple(sorted((member.i, member.j))) for member in members]
    if len(pairs) != len(set(pairs)):
        raise GroundStructureError("Ground structure contains duplicate members")

    components = ("ux", "uz")
    for node, restraints in fixes.items():
        if not 0 <= node < len(nodes):
            raise GroundStructureError(f"Support references missing node {node}")
        unknown = set(restraints) - set(components)
        if unknown:
            raise GroundStructureError(f"Unknown support components: {sorted(unknown)}")
    free_dofs = [
        2 * node + component
        for node in range(len(nodes))
        for component in range(2)
        if components[component] not in fixes.get(node, set())
    ]
    if not free_dofs:
        raise GroundStructureError("Ground structure has no free degrees of freedom")

    case_names = tuple(load_cases_kn)
    member_count = len(members)
    case_count = len(case_names)
    lengths = np.zeros(member_count)
    equilibrium = np.zeros((2 * len(nodes), member_count))
    for index, member in enumerate(members):
        length, c, s = _member_geometry(nodes, member)
        lengths[index] = length
        equilibrium[2 * member.i, index] += c
        equilibrium[2 * member.i + 1, index] += s
        equilibrium[2 * member.j, index] -= c
        equilibrium[2 * member.j + 1, index] -= s

    # Variables: [areas_cm2, tension_case_1_kn, compression_case_1_kn, ...].
    variable_count = member_count * (1 + 2 * case_count)
    objective = np.zeros(variable_count)
    objective[:member_count] = lengths
    equality_matrix = np.zeros((len(free_dofs) * case_count, variable_count))
    equality_rhs = np.zeros(len(free_dofs) * case_count)
    inequality_matrix = np.zeros((member_count * case_count, variable_count))
    inequality_rhs = np.zeros(member_count * case_count)
    stress_kn_cm2 = allowable_stress_mpa * 0.1

    for case_index, case_name in enumerate(case_names):
        loads = np.asarray(load_cases_kn[case_name], dtype=float)
        expected = (2 * len(nodes),)
        if loads.shape != expected or not np.all(np.isfinite(loads)):
            raise GroundStructureError(
                f"Load case {case_name!r} has invalid vector shape or values"
            )
        row = slice(case_index * len(free_dofs), (case_index + 1) * len(free_dofs))
        tension_start = member_count * (1 + 2 * case_index)
        compression_start = tension_start + member_count
        equality_matrix[row, tension_start : tension_start + member_count] = equilibrium[
            free_dofs, :
        ]
        equality_matrix[row, compression_start : compression_start + member_count] = -equilibrium[
            free_dofs, :
        ]
        equality_rhs[row] = -loads[free_dofs]
        for member_index in range(member_count):
            constraint_row = case_index * member_count + member_index
            inequality_matrix[constraint_row, member_index] = -stress_kn_cm2
            inequality_matrix[constraint_row, tension_start + member_index] = 1.0
            inequality_matrix[constraint_row, compression_start + member_index] = 1.0

    result = linprog(
        objective,
        A_ub=inequality_matrix,
        b_ub=inequality_rhs,
        A_eq=equality_matrix,
        b_eq=equality_rhs,
        bounds=(0.0, None),
        method="highs",
    )
    if not result.success or result.x is None:
        raise GroundStructureError(f"Ground-structure LP failed: {result.message}")

    areas = np.asarray(result.x[:member_count], dtype=float)
    forces: dict[str, tuple[float, ...]] = {}
    max_error = 0.0
    for case_index, case_name in enumerate(case_names):
        tension_start = member_count * (1 + 2 * case_index)
        compression_start = tension_start + member_count
        signed = (
            result.x[tension_start : tension_start + member_count]
            - result.x[compression_start : compression_start + member_count]
        )
        forces[case_name] = tuple(float(value) for value in signed)
        residual = equilibrium @ signed + np.asarray(load_cases_kn[case_name], dtype=float)
        max_error = max(max_error, max(abs(float(residual[dof])) for dof in free_dofs))

    active: list[ActiveGroundMember] = []
    for index, (member, area) in enumerate(zip(members, areas)):
        if area <= active_area_threshold_cm2:
            continue
        active.append(
            ActiveGroundMember(
                i=member.i,
                j=member.j,
                area_cm2=float(area),
                length_m=float(lengths[index]),
                force_by_case_kn={name: forces[name][index] for name in case_names},
            )
        )
    return GroundStructureSolution(
        success=True,
        status=str(result.message),
        objective_m_cm2=float(result.fun),
        areas_cm2=tuple(float(value) for value in areas),
        forces_by_case_kn=forces,
        active_members=tuple(active),
        max_equilibrium_error_kn=max_error,
    )


def generate_ground_members(panel_count: int, max_panel_jump: int) -> list[GroundMember]:
    if panel_count < 4 or panel_count % 2:
        raise ValueError("Ground-structure panel count must be even and at least four")
    if max_panel_jump < 1:
        raise ValueError("Maximum panel jump must be at least one")
    members: list[GroundMember] = []
    # Node order from the grammar is top_i, bottom_i for every panel station.
    for station_a in range(panel_count + 1):
        for layer_a in range(2):
            node_a = 2 * station_a + layer_a
            for station_b in range(station_a, min(panel_count, station_a + max_panel_jump) + 1):
                for layer_b in range(2):
                    node_b = 2 * station_b + layer_b
                    if node_b <= node_a:
                        continue
                    if station_a == station_b and layer_a == layer_b:
                        continue
                    members.append(GroundMember(node_a, node_b))
    return members


def _nodal_line_load_kn(
    nodes: Sequence[tuple[float, float]], top_nodes: Sequence[int], line_load_down_kn_m: float
) -> np.ndarray:
    loads = np.zeros(2 * len(nodes))
    xs = [nodes[node][0] for node in top_nodes]
    for index, (node, x) in enumerate(zip(top_nodes, xs)):
        left = 0.0 if index == 0 else (xs[index - 1] + x) / 2.0
        right = xs[-1] if index == len(xs) - 1 else (x + xs[index + 1]) / 2.0
        loads[2 * node + 1] -= line_load_down_kn_m * (right - left)
    return loads


def run_study(cfg: dict, space: dict) -> dict:
    study = space["ground_structure"]
    modulation = next(
        item for item in cfg["geometry"]["modulations"] if item["id"] == study["modulation_id"]
    )
    span = float(cfg["geometry"]["nave_width_m"])
    layout = generate_roof_truss(
        topology="X",
        depth_shape="VARIABLE",
        span_m=span,
        eave_low_m=float(cfg["geometry"]["eave_low_m"]),
        eave_high_m=float(cfg["geometry"]["eave_high_m"]),
        panel_count=int(study["panel_count"]),
        centre_depth_m=span / float(study["centre_depth_span_ratio"]),
        end_depth_fraction=float(study["end_depth_fraction"]),
    )
    candidates = generate_ground_members(int(study["panel_count"]), int(study["max_panel_jump"]))
    bay = float(modulation["bay_m"])
    dead = float(cfg["loads"]["dead"]["roof_kpa"]) * bay
    live = float(cfg["loads"]["live"]["roof_kpa"]) * bay
    gravity = max(
        float(combo["factors"].get("D", 0.0)) * dead + float(combo["factors"].get("L", 0.0)) * live
        for combo in cfg["combinations"]
    )
    wind = cfg["loads"]["wind"]
    external = (wind["Cp_roof_windward"] + wind["Cp_roof_leeward"]) / 2.0
    uplift_component = (
        wind["qz_eave_kpa_hypothesis"] * (external - abs(wind.get("Cp_internal", 0.0))) * bay
    )
    load_cases = {
        "factored_gravity_envelope": _nodal_line_load_kn(layout.nodes, layout.top_nodes, gravity),
        "global_uplift_component_only": _nodal_line_load_kn(
            layout.nodes, layout.top_nodes, uplift_component
        ),
    }
    steel = materials_from_json(cfg)["S355"]
    solution = solve_ground_structure(
        nodes=layout.nodes,
        members=candidates,
        fixes={layout.support_nodes[0]: {"ux", "uz"}, layout.support_nodes[1]: {"uz"}},
        load_cases_kn=load_cases,
        allowable_stress_mpa=steel.fy_mpa * float(cfg["criteria"]["phi_axial"]),
        active_area_threshold_cm2=float(study["active_area_threshold_cm2"]),
    )
    payload = {
        "model_revision": cfg["project"]["revision"],
        "space_revision": space["project"]["revision"],
        "study": study,
        "nodes": layout.nodes,
        "candidate_members": [asdict(member) for member in candidates],
        "load_cases_kn": {name: vector.tolist() for name, vector in load_cases.items()},
    }
    input_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    active_members = [
        {
            "i": member.i,
            "j": member.j,
            "area_cm2": round(member.area_cm2, 9),
            "length_m": round(member.length_m, 9),
            "force_by_case_kn": {
                case: round(force, 9) for case, force in sorted(member.force_by_case_kn.items())
            },
        }
        for member in solution.active_members
    ]

    return {
        "project": {
            "id": "DH-EST-OPT-E0-GS-001",
            "revision": "0.1",
            "date": "2026-08-12",
            "status": "research_inspiration_not_a_design",
        },
        "input_sha256": input_hash,
        "modulation_id": modulation["id"],
        "candidate_member_count": len(candidates),
        "active_member_count": len(solution.active_members),
        "objective_m_cm2": round(solution.objective_m_cm2, 9),
        "max_equilibrium_error_kn": round(solution.max_equilibrium_error_kn, 9),
        "nodes": [list(node) for node in layout.nodes],
        "support_nodes": list(layout.support_nodes),
        "active_members": active_members,
        "limitations": [
            "continuous-area plastic lower-bound layout study only",
            "no elastic compatibility or displacement constraint",
            "no self-weight, buckling, catalogue profiles, connection geometry, crossing removal, or constructability",
            "the uplift component is included as a topology-reversal probe, not as a standalone code combination",
            "the output must be rationalized into a stable grammar and re-analysed before E1 comparison",
        ],
    }


def svg_report(results: dict) -> str:
    nodes = [tuple(node) for node in results["nodes"]]
    active = results["active_members"]
    width, height = 1400, 520
    margin_x, margin_z = 90.0, 90.0
    min_x = min(x for x, _z in nodes)
    max_x = max(x for x, _z in nodes)
    min_z = min(z for _x, z in nodes)
    max_z = max(z for _x, z in nodes)
    scale_x = (width - 2 * margin_x) / (max_x - min_x)
    scale_z = (height - 2 * margin_z) / (max_z - min_z)
    scale = min(scale_x, scale_z)

    def point(node: int) -> tuple[float, float]:
        x, z = nodes[node]
        return margin_x + (x - min_x) * scale, height - margin_z - (z - min_z) * scale

    max_area = max((member["area_cm2"] for member in active), default=1.0)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f5f1e8"/>',
        '<text x="70" y="42" font-family="Arial" font-size="24" fill="#16222a">M60 ground-structure load-path map</text>',
        '<text x="70" y="68" font-family="Arial" font-size="14" fill="#59636a">LP inspiration only · line width ∝ continuous optimized area · not a truss design</text>',
        '<line x1="1050" y1="42" x2="1090" y2="42" stroke="#c85a3c" stroke-width="5"/><text x="1100" y="47" font-family="Arial" font-size="13" fill="#59636a">compression under gravity</text>',
        '<line x1="1050" y1="65" x2="1090" y2="65" stroke="#267ea3" stroke-width="5"/><text x="1100" y="70" font-family="Arial" font-size="13" fill="#59636a">tension under gravity</text>',
    ]
    for member in active:
        x1, y1 = point(member["i"])
        x2, y2 = point(member["j"])
        area = float(member["area_cm2"])
        width_px = 0.7 + 8.0 * math.sqrt(area / max_area)
        gravity_force = float(member["force_by_case_kn"]["factored_gravity_envelope"])
        colour = "#c85a3c" if gravity_force < 0.0 else "#267ea3"
        lines.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{colour}" stroke-width="{width_px:.2f}" stroke-linecap="round" opacity="0.82"/>'
        )
    supports = set(results["support_nodes"])
    for index in range(len(nodes)):
        x, y = point(index)
        radius = 5.0 if index in supports else 2.8
        colour = "#16222a" if index in supports else "#6d777d"
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius}" fill="{colour}"/>')
    lines.append(
        f'<text x="70" y="{height - 28}" font-family="Arial" font-size="12" fill="#59636a">{html.escape("Continuous-area plastic LP; compatibility, deflection, buckling, catalogue profiles, connections, and fabrication are excluded.")}</text>'
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--space", type=Path, default=DEFAULT_SPACE)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--svg-output", type=Path, default=DEFAULT_SVG_OUTPUT)
    arguments = parser.parse_args(argv)
    results = run_study(_read_json(arguments.model), _read_json(arguments.space))
    arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
    arguments.svg_output.parent.mkdir(parents=True, exist_ok=True)
    arguments.json_output.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    arguments.svg_output.write_text(svg_report(results), encoding="utf-8")
    print(
        f"Ground structure: {results['active_member_count']} active of "
        f"{results['candidate_member_count']} candidate members."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

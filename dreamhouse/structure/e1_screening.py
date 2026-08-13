"""Generate the traceable E1 multi-phenomenon structural screening report.

This module intentionally separates calculations that can be performed from
the canonical E0 hypotheses from decisions blocked by site, manufacturer,
fire-strategy, erection-engineering, and geotechnical inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .materials import materials_from_json
from .optimize_roof import (
    DEFAULT_MODEL,
    DEFAULT_SPACE,
    ROOT,
    RoofTrussCandidate,
    _read_json,
    build_candidates,
    build_truss_model,
    evaluate_candidate,
    roof_load_cases,
)
from .profiles import profile
from .steel_checks import trial_gusset_connection
from .systems_checks import (
    base_plate_screen,
    braced_bay_screen,
    diaphragm_screen,
    erection_lift_screen,
    fire_capacity_screen,
    pad_foundation_screen,
)
from .truss_grammar import generate_roof_truss

DEFAULT_E1_SPACE = Path(__file__).with_name("e1_screening_space.json")
DEFAULT_JSON_OUTPUT = ROOT / "docs/08_investigacion/e1_structural_screening.json"
DEFAULT_REPORT_OUTPUT = ROOT / "docs/08_investigacion/e1_structural_screening.md"


def _reference_candidate(cfg: dict, roof_space: dict, e1_space: dict) -> RoofTrussCandidate:
    target = e1_space["reference_truss"]
    span = float(cfg["geometry"]["nave_width_m"])
    expected_depth = span / float(target["centre_depth_span_ratio"])
    matches = [
        candidate
        for candidate in build_candidates(cfg, roof_space)
        if candidate.modulation_id == target["modulation_id"]
        and candidate.topology == target["topology"]
        and candidate.panel_count == int(target["panel_count"])
        and candidate.depth_shape == target["depth_shape"]
        and math.isclose(candidate.centre_depth_m, expected_depth)
        and math.isclose(candidate.end_depth_fraction, float(target["end_depth_fraction"]))
    ]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one E1 reference truss, found {len(matches)}")
    return matches[0]


def _combination_results(
    candidate: RoofTrussCandidate,
    selected: dict,
    cfg: dict,
) -> tuple[dict, float]:
    steel = materials_from_json(cfg)["S355"]
    chord = profile(selected["selected_profiles"]["chord"])
    web = profile(selected["selected_profiles"]["web"])
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
    model = build_truss_model(layout, steel, chord, web)
    case_vectors, _case_lines, truss_mass = roof_load_cases(
        candidate, cfg, layout, model, chord, web
    )
    envelope = {
        "maximum_member_force_kn": 0.0,
        "maximum_member_force_index": -1,
        "maximum_member_force_combination": "",
        "maximum_support_downward_reaction_kn": 0.0,
        "maximum_support_uplift_reaction_kn": 0.0,
        "combinations": [],
    }
    for combination in cfg["combinations"]:
        loads = sum(
            (
                float(combination["factors"].get(case, 0.0)) * vector
                for case, vector in case_vectors.items()
            ),
            np.zeros(2 * len(layout.nodes)),
        )
        solution = model.solve(loads)
        member_forces = [float(force) / 1000.0 for force in solution.member_forces_n]
        reactions = [
            float(solution.reactions_n[2 * node + 1]) / 1000.0 for node in layout.support_nodes
        ]
        local_index = max(range(len(member_forces)), key=lambda index: abs(member_forces[index]))
        if abs(member_forces[local_index]) > envelope["maximum_member_force_kn"]:
            envelope["maximum_member_force_kn"] = abs(member_forces[local_index])
            envelope["maximum_member_force_index"] = local_index
            envelope["maximum_member_force_combination"] = combination["id"]
        envelope["maximum_support_downward_reaction_kn"] = max(
            envelope["maximum_support_downward_reaction_kn"], *reactions
        )
        envelope["maximum_support_uplift_reaction_kn"] = max(
            envelope["maximum_support_uplift_reaction_kn"],
            *(-reaction for reaction in reactions),
        )
        envelope["combinations"].append(
            {
                "id": combination["id"],
                "support_vertical_reactions_kn": reactions,
                "maximum_abs_member_force_kn": abs(member_forces[local_index]),
                "maximum_abs_member_force_index": local_index,
            }
        )
    envelope["maximum_support_uplift_reaction_kn"] = max(
        0.0, envelope["maximum_support_uplift_reaction_kn"]
    )
    return envelope, truss_mass


def _lateral_force_basis(cfg: dict, truss_mass_kg: float, portal_line_count: int) -> dict:
    geometry = cfg["geometry"]
    loads = cfg["loads"]
    wind = loads["wind"]
    average_eave = (float(geometry["eave_low_m"]) + float(geometry["eave_high_m"])) / 2.0
    gable_area = float(geometry["nave_width_m"]) * average_eave
    net_wall_coefficient = abs(float(wind["Cp_wall_windward"])) + abs(
        float(wind["Cp_wall_leeward"])
    )
    longitudinal_wind = float(wind["qz_eave_kpa_hypothesis"]) * net_wall_coefficient * gable_area

    roof_dead = float(loads["dead"]["roof_kpa"]) * (
        float(geometry["nave_length_m"]) * float(geometry["nave_width_m"])
    )
    p2_area = float(geometry["p2_length_m"]) * float(geometry["nave_width_m"])
    p2_dead = (
        float(loads["dead"]["floor_p2_kpa"])
        + float(loads["dead"]["partitions_p2_kpa"])
        + float(loads["dead"]["ceiling_mep_kpa"])
    ) * p2_area
    perimeter = 2.0 * (float(geometry["nave_length_m"]) + float(geometry["nave_width_m"]))
    facade_dead = float(loads["dead"]["facade_kpa"]) * perimeter * average_eave
    roof_truss_dead = truss_mass_kg * portal_line_count * 9.80665 / 1000.0
    declared_dead_lower_bound = roof_dead + p2_dead + facade_dead + roof_truss_dead
    seismic_lower_bound = (
        float(loads["seismic"]["cs_base_shear_hypothesis"]) * declared_dead_lower_bound
    )
    governing = max(longitudinal_wind, seismic_lower_bound)
    return {
        "longitudinal_wind_kn_hypothesis": longitudinal_wind,
        "declared_dead_load_lower_bound_kn": declared_dead_lower_bound,
        "seismic_base_shear_lower_bound_kn_hypothesis": seismic_lower_bound,
        "governing_preliminary_lateral_force_kn": governing,
        "governing_source": (
            "seismic_lower_bound"
            if seismic_lower_bound >= longitudinal_wind
            else "longitudinal_wind"
        ),
        "normative_site_actions_resolved": False,
    }


def _rounded(value):
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return round(value, 6)
    if isinstance(value, dict):
        return {key: _rounded(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_rounded(item) for item in value]
    return value


def run_screening(cfg: dict, roof_space: dict, e1_space: dict) -> dict:
    candidate = _reference_candidate(cfg, roof_space, e1_space)
    steel = materials_from_json(cfg)["S355"]
    selected = evaluate_candidate(candidate, cfg, roof_space, steel)
    envelope, truss_mass = _combination_results(candidate, selected, cfg)

    connection_cfg = e1_space["trial_connection"]
    connection = trial_gusset_connection(
        envelope["maximum_member_force_kn"],
        **{key: value for key, value in connection_cfg.items() if key != "description"},
    )

    modulation = next(
        item for item in cfg["geometry"]["modulations"] if item["id"] == candidate.modulation_id
    )
    lateral_basis = _lateral_force_basis(cfg, truss_mass, int(modulation["n_portal_lines"]))
    lateral_cfg = e1_space["lateral_system"]
    brace_profile = profile(lateral_cfg["trial_brace_profile"])
    brace_steel = materials_from_json(cfg)["S235"]
    lateral_bracing = braced_bay_screen(
        lateral_basis["governing_preliminary_lateral_force_kn"],
        parallel_braced_lines=int(lateral_cfg["parallel_braced_wall_lines"]),
        active_bays_per_line=int(lateral_cfg["active_bays_per_wall_line"]),
        bay_width_m=float(lateral_cfg["trial_bay_width_m"]),
        bay_height_m=float(lateral_cfg["trial_bay_height_m"]),
        brace_area_m2=brace_profile.area_m2,
        brace_fy_pa=brace_steel.fy_pa,
        brace_locations_validated=bool(lateral_cfg["brace_locations_validated_against_openings"]),
        connections_and_collectors_resolved=bool(
            lateral_cfg["brace_connections_and_collectors_resolved"]
        ),
    )
    diaphragm_cfg = e1_space["diaphragm"]
    diaphragm = diaphragm_screen(
        lateral_basis["governing_preliminary_lateral_force_kn"],
        float(cfg["geometry"]["nave_length_m"]),
        float(cfg["geometry"]["nave_width_m"]),
        nominal_capacity_kn_m=diaphragm_cfg["nominal_capacity_kn_m"],
        assembled_shear_stiffness_kn_mm=diaphragm_cfg["assembled_shear_stiffness_kn_mm"],
        collectors_defined=bool(diaphragm_cfg["collectors_defined"]),
        connections_defined=bool(diaphragm_cfg["connections_defined"]),
    )

    fire_cfg = e1_space["fire"]
    fire_screens = [
        fire_capacity_screen(
            float(selected["max_strength_ratio"]),
            float(temperature),
            fire_resistance_period_defined=fire_cfg["required_fire_resistance_minutes"] is not None,
            thermal_protection_system_defined=fire_cfg["thermal_protection_system"] is not None,
        )
        for temperature in fire_cfg["trial_steel_temperatures_c"]
    ]

    erection_cfg = e1_space["erection"]
    erection = erection_lift_screen(
        float(cfg["geometry"]["nave_width_m"]),
        truss_mass,
        dynamic_factor=float(erection_cfg["dynamic_factor"]),
        lift_point_count=int(erection_cfg["lift_point_count"]),
        sling_angle_deg_from_horizontal=float(erection_cfg["sling_angle_deg_from_horizontal"]),
        maximum_transport_piece_length_m=float(erection_cfg["maximum_transport_piece_length_m"]),
        crane_capacity_kn=erection_cfg["crane_capacity_kn_at_required_radius"],
        temporary_bracing_installed=bool(erection_cfg["temporary_bracing_installed"]),
        weather_limit_defined=bool(erection_cfg["weather_limit_defined"]),
    )

    foundation_cfg = e1_space["trial_foundation"]
    foundation_args = {
        "width_m": float(foundation_cfg["width_m"]),
        "length_m": float(foundation_cfg["length_m"]),
        "thickness_m": float(foundation_cfg["thickness_m"]),
        "embedment_m": float(foundation_cfg["embedment_m"]),
        "allowable_bearing_kpa": float(foundation_cfg["allowable_bearing_kpa_hypothesis"]),
        "base_friction_coefficient": float(foundation_cfg["base_friction_coefficient_hypothesis"]),
        "geotechnical_parameters_approved": bool(
            foundation_cfg["geotechnical_parameters_approved"]
        ),
        "reinforced_concrete_design_resolved": bool(
            foundation_cfg["reinforced_concrete_design_resolved"]
        ),
    }
    foundation_gravity = pad_foundation_screen(
        envelope["maximum_support_downward_reaction_kn"], 0.0, 0.0, **foundation_args
    )
    foundation_uplift = pad_foundation_screen(
        -envelope["maximum_support_uplift_reaction_kn"], 0.0, 0.0, **foundation_args
    )
    base_plate_cfg = e1_space["trial_base_plate"]
    base_plate = base_plate_screen(
        envelope["maximum_support_downward_reaction_kn"],
        envelope["maximum_support_uplift_reaction_kn"],
        plate_width_mm=float(base_plate_cfg["plate_width_mm"]),
        plate_length_mm=float(base_plate_cfg["plate_length_mm"]),
        plate_thickness_mm=float(base_plate_cfg["plate_thickness_mm"]),
        column_width_mm=float(base_plate_cfg["column_width_mm"]),
        column_depth_mm=float(base_plate_cfg["column_depth_mm"]),
        plate_fy_mpa=float(base_plate_cfg["plate_fy_mpa"]),
        concrete_fc_mpa=float(base_plate_cfg["concrete_fc_mpa_hypothesis"]),
        supporting_area_ratio=float(base_plate_cfg["supporting_area_ratio"]),
        anchor_group_tension_capacity_kn=base_plate_cfg["anchor_group_tension_capacity_kn"],
        shear_transfer_resolved=bool(base_plate_cfg["shear_transfer_resolved"]),
        moment_transfer_resolved=bool(base_plate_cfg["moment_transfer_resolved"]),
    )

    input_payload = json.dumps(
        {"model": cfg, "roof_space": roof_space, "e1_space": e1_space},
        sort_keys=True,
        separators=(",", ":"),
    )
    result = {
        "project": e1_space["project"],
        "input_sha256": hashlib.sha256(input_payload.encode("utf-8")).hexdigest(),
        "reference_truss": {
            "role": e1_space["reference_truss"]["role"],
            "candidate": asdict(candidate),
            "selected_screening_profiles": selected["selected_profiles"],
            "truss_mass_kg": truss_mass,
            "global_and_member_screen": selected,
            "force_and_reaction_envelope": envelope,
        },
        "checks": {
            "local_and_biaxial_member_stability": {
                "screened": True,
                "maximum_local_slenderness_ratio": selected["max_local_slenderness_ratio"],
                "maximum_axial_ratio": selected["max_axial_ratio"],
                "maximum_interaction_ratio": selected["max_strength_ratio"],
                "screen_pass": selected["screening_passed"],
                "design_resolved": False,
            },
            "chord_local_bending": {
                "screened": True,
                "maximum_local_moment_knm": selected["max_chord_local_moment_knm"],
                "maximum_local_bending_ratio": selected["max_local_bending_ratio"],
                "included_in_interaction": True,
                "design_resolved": False,
            },
            "member_second_order": {
                "screened": True,
                "maximum_compression_to_reduced_euler_ratio": selected[
                    "max_second_order_euler_ratio"
                ],
                "maximum_moment_magnifier": selected["max_second_order_magnifier"],
                "global_direct_analysis_resolved": False,
            },
            "trial_connection": {
                "configuration": connection_cfg,
                "result": asdict(connection),
            },
            "lateral_system": {
                "top_chord_unbraced_length_m": roof_space["analysis"][
                    "top_chord_out_of_plane_unbraced_m"
                ],
                "bottom_chord_unbraced_length_m": roof_space["analysis"][
                    "bottom_chord_out_of_plane_unbraced_m"
                ],
                "member_out_of_plane_buckling_screened": True,
                "trial_braced_bay_configuration": lateral_cfg,
                "trial_braced_bay_result": asdict(lateral_bracing),
                "complete_building_lateral_system_resolved": False,
                "site_actions_resolved": False,
            },
            "diaphragm": {
                "demand_basis": lateral_basis,
                "result": asdict(diaphragm),
            },
            "fire": {
                "required_fire_resistance_minutes": fire_cfg["required_fire_resistance_minutes"],
                "thermal_protection_system": fire_cfg["thermal_protection_system"],
                "temperature_sensitivity": [asdict(item) for item in fire_screens],
                "design_resolved": False,
            },
            "erection": {
                "configuration": erection_cfg,
                "result": asdict(erection),
                "engineered_erection_plan_resolved": False,
            },
            "foundation": {
                "configuration": foundation_cfg,
                "base_plate_configuration": base_plate_cfg,
                "base_plate_result": asdict(base_plate),
                "gravity_reaction_case": asdict(foundation_gravity),
                "uplift_reaction_case": asdict(foundation_uplift),
                "lateral_and_moment_allocation_resolved": False,
                "design_resolved": False,
            },
        },
        "overall_status": "research_screening_complete_design_blocked",
        "selection_or_construction_authority": False,
        "blocking_inputs": [
            "D-017 site, municipality, topography, normative wind and seismic actions",
            "geotechnical investigation and groundwater/settlement parameters",
            "complete three-dimensional lateral model and direct second-order analysis",
            "roof and floor deck manufacturer strength, stiffness, fasteners, sidelaps, and openings",
            "connection geometry including HSS local limit states and seismic demand hierarchy",
            "D-021 occupancy, fire-resistance target, fire scenario, and tested protection system",
            "fabricator splice strategy, crane chart/radius, temporary bracing, lift lugs, and weather limits",
            "reinforced-concrete footing, anchors, base plates, punching, shear, flexure, and development design",
        ],
    }
    return _rounded(result)


def markdown_report(results: dict) -> str:
    reference = results["reference_truss"]
    member = results["checks"]["local_and_biaxial_member_stability"]
    chord = results["checks"]["chord_local_bending"]
    second_order = results["checks"]["member_second_order"]
    connection = results["checks"]["trial_connection"]["result"]
    lateral = results["checks"]["lateral_system"]["trial_braced_bay_result"]
    diaphragm = results["checks"]["diaphragm"]["result"]
    erection = results["checks"]["erection"]["result"]
    foundation = results["checks"]["foundation"]
    lateral_system = results["checks"]["lateral_system"]
    gravity = foundation["gravity_reaction_case"]
    uplift = foundation["uplift_reaction_case"]
    base_plate = foundation["base_plate_result"]
    lines = [
        "# E1 Multi-Phenomenon Structural Screening",
        "",
        "**Status:** research screening complete; design remains blocked",
        f"**Version:** {results['project']['revision']}",
        f"**Date:** {results['project']['date']}",
        f"**Input SHA-256:** `{results['input_sha256']}`",
        "**Authority:** not for system selection, pricing, fabrication, or construction",
        "",
        "## Reference test specimen",
        "",
        (
            f"The neutral specimen is {reference['candidate']['modulation_id']} "
            f"{reference['candidate']['topology']} with {reference['candidate']['panel_count']} "
            f"panels, {reference['candidate']['centre_depth_m']:.2f} m centre depth, and "
            f"{reference['selected_screening_profiles']['chord']} / "
            f"{reference['selected_screening_profiles']['web']} chord/web trial sections. "
            "It is a reproducible test case, not a selected structural system."
        ),
        "",
        "## Screening matrix",
        "",
        "| Phenomenon | Calculated result | Current status |",
        "|---|---|---|",
        (
            "| HSS local and biaxial buckling | local slenderness "
            f"{member['maximum_local_slenderness_ratio']:.3f}; axial "
            f"{member['maximum_axial_ratio']:.3f} | trial screen passes; design unresolved |"
        ),
        (
            "| Chord local bending | "
            f"M={chord['maximum_local_moment_knm']:.2f} kN·m; local bending "
            f"ratio={chord['maximum_local_bending_ratio']:.3f}; combined "
            f"ratio={member['maximum_interaction_ratio']:.3f} | included; joint/load-introduction detail unresolved |"
        ),
        (
            "| Member second order | reduced-Euler ratio "
            f"{second_order['maximum_compression_to_reduced_euler_ratio']:.3f}; "
            f"B1 screen={second_order['maximum_moment_magnifier']:.3f} | member screen included; global direct analysis unresolved |"
        ),
        (
            "| Trial gusset components | demand "
            f"{connection['demand_kn']:.1f} kN; capacity "
            f"{connection['governing_trial_capacity_kn']:.1f} kN; ratio "
            f"{connection['trial_ratio']:.3f} | generic components "
            f"{'pass' if connection['trial_components_pass'] else 'fail'}; HSS wall limit states unresolved |"
        ),
        (
            "| Trial longitudinal braced bays | diagonal demand "
            f"{lateral['tension_brace_demand_kn']:.1f} kN; L50×5 gross-yield ratio "
            f"{lateral['strength_ratio']:.3f} | trial bar strength "
            f"{'passes' if lateral['trial_strength_pass'] else 'fails'}; locations, buckling in reversal, connections, collectors, and openings unresolved |"
        ),
        (
            "| Roof diaphragm | required unit shear "
            f"{diaphragm['required_unit_shear_kn_m']:.2f} kN/m; chord force "
            f"{diaphragm['required_chord_force_kn']:.1f} kN | blocked by manufacturer system, openings, fasteners, collectors, and stiffness |"
        ),
        (
            "| Erection | hook load "
            f"{erection['required_hook_load_kn']:.1f} kN; sling tension "
            f"{erection['sling_tension_each_kn']:.1f} kN; minimum transport pieces "
            f"{erection['minimum_transport_piece_count']} | crane chart, lift lugs, weather limit, splices, and temporary bracing unresolved |"
        ),
        (
            "| Trial foundation sensitivity | gravity qmax "
            f"{gravity['maximum_bearing_kpa']:.1f} kPa; gravity bearing ratio "
            f"{gravity['bearing_ratio']:.3f}; uplift net vertical "
            f"{uplift['net_vertical_kn']:.1f} kN | no foundation adopted; geotechnical and RC/anchor design unresolved |"
        ),
        (
            "| Trial base plate | concrete-bearing ratio "
            f"{base_plate['concrete_bearing_ratio']:.3f}; required/provided plate "
            f"thickness {base_plate['required_plate_thickness_mm']:.1f}/"
            f"{base_plate['provided_plate_thickness_mm']:.1f} mm | centred compression "
            "components pass; anchor group, shear, moment, grout, pedestal, and concrete "
            "anchor limit states unresolved |"
        ),
        "",
        "## Lateral-stability assumptions",
        "",
        (
            "The member screen assumes top-chord lateral restraint every "
            f"{lateral_system['top_chord_unbraced_length_m']:.2f} m and bottom-chord "
            f"restraint every {lateral_system['bottom_chord_unbraced_length_m']:.2f} m. "
            "The first requires qualified purlin-to-chord restraint and a complete roof-plane "
            "load path; the second is a new physical bracing requirement under uplift and is "
            "not present merely because it appears in the model."
        ),
        "",
        (
            "The four trial longitudinal braced bays are only a force-distribution hypothesis. "
            "Their locations have not been reconciled with the technical windows, upper-floor "
            "glazing, doors, or rooflights, and compression under load reversal has not been "
            "assigned to a tension-only L-angle."
        ),
        "",
        "## Fire sensitivity—not a fire rating",
        "",
        "The ambient governing ratio is conservatively divided by the Appendix 4 material-retention factors. This does not model a time–temperature curve, section factor, thermal gradients, restraint, load redistribution, or protection thickness.",
        "",
        "| Trial steel temperature | Fy retention | E retention | Conservative strength ratio | Trial result |",
        "|---:|---:|---:|---:|---|",
    ]
    for item in results["checks"]["fire"]["temperature_sensitivity"]:
        strength = item["conservative_strength_utilization"]
        lines.append(
            f"| {item['temperature_c']:.0f} °C | {item['yield_retention']:.3f} | "
            f"{item['stiffness_retention']:.3f} | "
            f"{strength:.3f} | {'passes sensitivity only' if item['trial_temperature_pass'] else 'fails sensitivity'} |"
        )
    lines.extend(
        [
            "",
            "D-021 must establish occupancy, required fire-resistance period, fire scenarios, compartmentation, and a tested protection system before fire design can close.",
            "",
            "## What remains genuinely blocked",
            "",
            *[f"- {item}" for item in results["blocking_inputs"]],
            "",
            "## Interpretation",
            "",
            "The new calculations remove the former one-axis Euler and node-only load simplifications from the roof-truss shortlist. They do not resolve the complete building. Member checks can pass while diaphragm, HSS joints, global stability, erection, fire, and foundations remain open; those open gates prevent D-019, PE-1 quantities, procurement, and construction use.",
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
    parser.add_argument("--roof-space", type=Path, default=DEFAULT_SPACE)
    parser.add_argument("--e1-space", type=Path, default=DEFAULT_E1_SPACE)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    arguments = parser.parse_args(argv)
    results = run_screening(
        _read_json(arguments.model),
        _read_json(arguments.roof_space),
        _read_json(arguments.e1_space),
    )
    write_outputs(results, arguments.json_output, arguments.report_output)
    print("E1 multi-phenomenon screening generated; design remains blocked by declared inputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

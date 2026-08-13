"""Subtotales de masa E0 por sistema y modulación.

No son cantidades de diseño: omiten o reservan componentes todavía no
dimensionados y no son elegibles para seleccionar D-019 ni presupuestar PE-1.
"""

from __future__ import annotations

import math

from .materials import Steel
from .portal import (
    P2_SIDE_COLUMN_SHARE,
    size_cercha_columns,
    size_cercha_roof,
    size_joists_and_beams,
    size_portal_frame,
)
from .profiles import profile
from .staggered import size_p2_great_wall, size_staggered_floor


def p2_tributary_m(bay_m: float, p2_start: float, length: float, x: float) -> float:
    lo = max(x - bay_m / 2.0, p2_start)
    hi = min(x + bay_m / 2.0, length)
    return max(0.0, hi - lo)


def frame_positions(n_bays: int, bay_m: float) -> list[float]:
    return [i * bay_m for i in range(n_bays + 1)]


def compute_quantities(cfg: dict, steel: Steel, bay_m: float, n_bays: int, phi_b: float, phi_c: float) -> dict:
    geom = cfg["geometry"]
    crit = cfg["criteria"]
    length = geom["nave_length_m"]
    p2_start = geom["p2_start_x_m"]
    p2_length = geom["p2_length_m"]
    width = geom["nave_width_m"]
    reference_floor_area = width * (length + p2_length)
    eave_low = geom["eave_low_m"]
    eave_high = geom["eave_high_m"]
    col_len = max(eave_low, eave_high)
    n_lines = n_bays + 1
    positions = frame_positions(n_bays, bay_m)
    tribs = [p2_tributary_m(bay_m, p2_start, length, x) for x in positions]
    active_tribs = [t for t in tribs if t > 0.0]
    n_p2_frames = len(active_tribs)

    floor_cases = [
        size_joists_and_beams(cfg, steel, bay_m, tributary, phi_b, phi_c)
        for tributary in active_tribs
    ]
    if floor_cases:
        floor = max(floor_cases, key=lambda case: case["beam"].mass_kg_m)
    else:
        floor = size_joists_and_beams(cfg, steel, bay_m, 0.0, phi_b, phi_c)
    staggered = size_staggered_floor(cfg, steel, bay_m, phi_b, phi_c)
    great_wall = size_p2_great_wall(cfg, steel, phi_b, phi_c)

    detail = crit["detail_factor_principales"]
    waste = crit["waste_factor"]

    result: dict = {
        "modulation": {"id": f"M{int(bay_m * 10)}", "bay_m": bay_m, "n_bays": n_bays, "n_portal_lines": n_lines},
        "systems": {},
    }

    for system in cfg["systems"]:
        sid = system["id"]
        if sid in ("PORTICO", "PORTICO-T", "PORTICO-F"):
            tie = bool(system.get("tie", False))
            fixed = bool(system.get("fixed_base", False))
            frame_results = [
                size_portal_frame(
                    cfg,
                    steel,
                    bay_m,
                    tributary,
                    True,
                    phi_b,
                    phi_c,
                    tie=tie,
                    fixed_base=fixed,
                )
                for tributary in tribs
            ]
            main_total = sum(frame_result.weight_kg for frame_result in frame_results)
            res = max(
                frame_results,
                key=lambda frame_result: (
                    frame_result.weight_kg,
                    frame_result.utilization,
                    frame_result.drift_m,
                ),
            )
            main_per_frame = res.weight_kg
            frames = {
                "type": "pórtico portal 18 m" + (" atado (tirante de alero)" if tie else "") + (" con bases fijas" if fixed else " con bases articuladas"),
                "column": res.column.name,
                "rafter": res.rafter.name,
                "tie_area_cm2": round(res.tie_area_cm2, 1),
                "tie_force_kn": round(res.tie_force_kn, 1),
                "weight_per_frame_kg": round(main_per_frame, 1),
                "rafter_moment_knm": round(res.rafter_moment_knm, 1),
                "rafter_axial_kn": round(res.rafter_axial_kn, 1),
                "column_moment_knm": round(res.column_moment_knm, 1),
                "column_axial_kn": round(res.column_axial_kn, 1),
                "rafter_deflection_m": round(res.rafter_deflection_m, 3),
                "drift_m": round(res.drift_m, 3),
                "gross_section_screening_ratio": round(res.utilization, 2),
                "screening_passed": res.screening_passed,
                "design_adequate": False,
                "analysis_status": res.analysis_status,
                "screening_checks": res.screening_checks,
                "governing_issues": list(res.governing_issues),
            }
        else:
            chord, truss_mass, truss_defl = size_cercha_roof(cfg, steel, bay_m, phi_b, phi_c)
            roof_d = cfg["loads"]["dead"]["roof_kpa"] * bay_m * 1e3
            roof_l = cfg["loads"]["live"]["roof_kpa"] * bay_m * 1e3
            floor_d = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3
            floor_l = cfg["loads"]["live"]["p2_residential_kpa"] * 1e3
            combos = cfg["combinations"]
            cercha_frames: list[tuple] = []
            for tributary in tribs:
                axial_max = 0.0
                for combo in combos:
                    fac = combo["factors"]
                    q = fac.get("D", 0.0) * roof_d + fac.get("L", 0.0) * roof_l
                    col_roof = q * width / 2.0
                    col_p2 = (
                        (fac.get("D", 0.0) * floor_d + fac.get("L", 0.0) * floor_l)
                        * tributary
                        * width
                        * P2_SIDE_COLUMN_SHARE
                    )
                    axial_max = max(axial_max, col_roof + col_p2)
                trial_col = size_cercha_columns(
                    cfg, steel, axial_max / 1e3, col_len, phi_c
                )
                trial_weight = (
                    2.0 * trial_col.mass_kg_m * col_len + truss_mass
                ) * (1.0 + detail)
                cercha_frames.append((trial_col, trial_weight, axial_max))
            col, main_per_frame, _axial = max(
                cercha_frames, key=lambda item: (item[1], item[2])
            )
            main_total = sum(item[1] for item in cercha_frames)
            frames = {
                "type": "cercha 18 m / L16 sobre columnas articuladas",
                "column": col.name,
                "truss_chord": chord.name,
                "truss_deflection_m": round(truss_defl, 3),
                "weight_per_frame_kg": round(main_per_frame, 1),
                "screening_passed": False,
                "design_adequate": False,
                "analysis_status": "incomplete_no_lateral_or_member_stability_analysis",
                "lateral_analysis_performed": False,
                "governing_issues": [
                    "lateral_system_not_analyzed",
                    "member_buckling_and_connections_not_checked",
                ],
            }

        joist = floor["joist"]
        beam = floor["beam"]
        edge = floor["edge"]
        aux_col = floor["aux_col"]
        joist_total = (math.ceil(width / crit["joist_spacing_m"]) + 1) * p2_length * joist.mass_kg_m
        beam_total = sum(
            width * floor_case["beam"].mass_kg_m for floor_case in floor_cases
        )
        edge_total = width * edge.mass_kg_m
        aux_total = 2.0 * 3.8 * aux_col.mass_kg_m
        interior_columns_total = n_p2_frames * 2 * 3.8 * aux_col.mass_kg_m
        floor_total = (joist_total + beam_total + edge_total + aux_total + interior_columns_total) * (1.0 + detail)
        floor_staggered_total = staggered["total_kg"] * (1.0 + detail)
        floor_greatwall_total = great_wall["total_kg"] * (1.0 + detail)

        roof_width = math.hypot(width, geom["roof_rise_m"])
        purlin_lines = math.ceil(roof_width / crit["purlin_spacing_m"]) + 1
        purlin_total = purlin_lines * length * profile("C200").mass_kg_m
        girt_lines = math.ceil((eave_low + eave_high) / 2.0 / crit["girt_spacing_m"])
        girt_gross_m = girt_lines * (2.0 * (length + width))
        girt_opening_factor = 0.85
        girt_net_m = girt_gross_m * girt_opening_factor
        girt_total = girt_net_m * profile("C200").mass_kg_m
        bracing_total = float(crit["bracing_mass_allowance_kg"])
        secondary_total = (purlin_total + girt_total + bracing_total) * (1.0 + waste)

        main_round = round(main_total, 0)
        floor_round = round(floor_total, 0)
        floor_staggered_round = round(floor_staggered_total, 0)
        floor_greatwall_round = round(floor_greatwall_total, 0)
        sec_round = round(secondary_total, 0)
        total_kg = main_round + floor_round + sec_round
        total_staggered_kg = main_round + floor_staggered_round + sec_round
        total_greatwall_kg = main_round + floor_greatwall_round + sec_round
        result["systems"][sid] = {
            "main_frames_kg": main_round,
            "p2_floor_kg": floor_round,
            "p2_floor_metaldeck_kg": floor_round,
            "p2_floor_staggered_kg": floor_staggered_round,
            "p2_floor_greatwall_kg": floor_greatwall_round,
            "secondary_kg": sec_round,
            "joist_profile": joist.name,
            "floor_beam_profile": beam.name,
            "floor_beam_profiles_by_active_line": [
                floor_case["beam"].name for floor_case in floor_cases
            ],
            "p2_tributaries_by_frame_m": [round(value, 3) for value in tribs],
            "edge_beam_profile": edge.name,
            "aux_columns_profile": aux_col.name,
            "p2_floor_mode": "D-043 activo para gravedad: pared híbrida de acero oculto · comparadores: metaldeck con apoyos y staggered",
            "staggered": staggered,
            "great_wall": great_wall,
            "purlins_m": round(purlin_total / profile("C200").mass_kg_m, 0),
            "girts_m": round(girt_net_m, 0),
            "girts_gross_m": round(girt_gross_m, 0),
            "girt_opening_factor": girt_opening_factor,
            "total_kg": total_kg,
            "total_t": round(total_kg / 1000.0, 1),
            "kg_m2": round(total_kg / reference_floor_area, 1),
            "total_staggered_kg": total_staggered_kg,
            "total_staggered_t": round(total_staggered_kg / 1000.0, 1),
            "total_greatwall_kg": total_greatwall_kg,
            "total_greatwall_t": round(total_greatwall_kg / 1000.0, 1),
            "kg_m2_greatwall": round(total_greatwall_kg / reference_floor_area, 1),
            "estimate_class": "screening_lower_bound_not_design_quantity",
            "ranking_eligible": False,
            "design_compliance_demonstrated": False,
            "bracing_basis": "mass_allowance_only_no_force_design",
            "excluded_or_unverified": [
                "member buckling and second-order effects",
                "connections, base plates, anchors and foundations",
                "designed longitudinal bracing, diaphragm and collectors",
                "rooflight/opening framing and local wind zones",
                "composite deck, studs, reinforcement and fire protection",
            ],
            "frames": frames,
        }

    return result

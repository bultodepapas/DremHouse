"""Cuantificación de tonelaje E0 por sistema y modulación."""

from __future__ import annotations

import math

from .materials import Steel
from .portal import size_cercha_columns, size_cercha_roof, size_joists_and_beams, size_portal_frame
from .profiles import profile
from .staggered import size_staggered_floor


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
    eave_low = geom["eave_low_m"]
    eave_high = geom["eave_high_m"]
    col_len = max(eave_low, eave_high)
    n_lines = n_bays + 1
    positions = frame_positions(n_bays, bay_m)
    tribs = [p2_tributary_m(bay_m, p2_start, length, x) for x in positions]
    n_p2_frames = sum(1 for t in tribs if t > 0.0)

    floor = size_joists_and_beams(cfg, steel, bay_m, bay_m, phi_b, phi_c)
    staggered = size_staggered_floor(cfg, steel, bay_m, phi_b, phi_c)

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
            res = size_portal_frame(cfg, steel, bay_m, bay_m, True, phi_b, phi_c, tie=tie, fixed_base=fixed)
            main_per_frame = res.weight_kg
            main_total = main_per_frame * n_lines
            frames = {
                "type": "pórtico portal 18 m" + (" atado (tirante de alero)" if tie else "") + (" con bases fijas" if fixed else " con bases articuladas"),
                "column": res.column.name,
                "rafter": res.rafter.name,
                "tie_area_cm2": round(res.tie_area_cm2, 1),
                "tie_force_kn": round(res.tie_force_kn, 1),
                "weight_per_frame_kg": round(main_per_frame, 1),
                "rafter_moment_knm": round(res.rafter_moment_knm, 1),
                "column_moment_knm": round(res.column_moment_knm, 1),
                "column_axial_kn": round(res.column_axial_kn, 1),
                "rafter_deflection_m": round(res.rafter_deflection_m, 3),
                "drift_m": round(res.drift_m, 3),
                "utilization": round(res.utilization, 2),
            }
        else:
            chord, truss_mass, truss_defl = size_cercha_roof(cfg, steel, bay_m, phi_b, phi_c)
            roof_d = cfg["loads"]["dead"]["roof_kpa"] * bay_m * 1e3
            roof_l = cfg["loads"]["live"]["roof_kpa"] * bay_m * 1e3
            floor_d = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3
            floor_l = cfg["loads"]["live"]["p2_residential_kpa"] * 1e3
            combos = cfg["combinations"]
            axial_max = 0.0
            for combo in combos:
                fac = combo["factors"]
                q = fac.get("D", 0.0) * roof_d + fac.get("L", 0.0) * roof_l
                col_roof = q * 18.0 / 2.0
                col_p2 = 0.0
                if n_p2_frames > 0:
                    trib = bay_m
                    col_p2 = (fac.get("D", 0.0) * floor_d + fac.get("L", 0.0) * floor_l) * trib * 18.0 / 2.0
                axial_max = max(axial_max, col_roof + col_p2)
            col = size_cercha_columns(cfg, steel, axial_max / 1e3, col_len, phi_c)
            main_per_frame = (2.0 * col.mass_kg_m * col_len + truss_mass) * (1.0 + detail)
            main_total = main_per_frame * n_lines
            frames = {
                "type": "cercha 18 m / L16 sobre columnas articuladas",
                "column": col.name,
                "truss_chord": chord.name,
                "truss_deflection_m": round(truss_defl, 3),
                "weight_per_frame_kg": round(main_per_frame, 1),
            }

        joist = floor["joist"]
        beam = floor["beam"]
        edge = floor["edge"]
        aux_col = floor["aux_col"]
        joist_total = (math.ceil(18.0 / crit["joist_spacing_m"]) + 1) * p2_length * joist.mass_kg_m
        beam_total = n_p2_frames * 18.0 * beam.mass_kg_m
        edge_total = 18.0 * edge.mass_kg_m
        aux_total = 2.0 * 3.8 * aux_col.mass_kg_m
        interior_columns_total = n_p2_frames * 2 * 3.8 * aux_col.mass_kg_m
        floor_total = (joist_total + beam_total + edge_total + aux_total + interior_columns_total) * (1.0 + detail)
        floor_staggered_total = staggered["total_kg"] * (1.0 + detail)

        roof_width = math.hypot(18.0, geom["roof_rise_m"])
        purlin_lines = math.ceil(roof_width / crit["purlin_spacing_m"]) + 1
        purlin_total = purlin_lines * length * profile("C200").mass_kg_m
        girt_lines = math.ceil((eave_low + eave_high) / 2.0 / crit["girt_spacing_m"])
        girt_total = girt_lines * (2.0 * (length + 18.0)) * profile("C200").mass_kg_m * 0.85
        bracing_total = 1.0 * 1000.0
        secondary_total = (purlin_total + girt_total + bracing_total) * (1.0 + waste)

        total_kg = main_total + floor_total + secondary_total
        result["systems"][sid] = {
            "main_frames_kg": round(main_total, 0),
            "p2_floor_kg": round(floor_total, 0),
            "p2_floor_metaldeck_kg": round(floor_total, 0),
            "p2_floor_staggered_kg": round(floor_staggered_total, 0),
            "secondary_kg": round(secondary_total, 0),
            "joist_profile": joist.name,
            "floor_beam_profile": beam.name,
            "edge_beam_profile": edge.name,
            "aux_columns_profile": aux_col.name,
            "p2_floor_mode": "STAGGERED (sin columnas interiores)",
            "staggered": staggered,
            "purlins_m": round(purlin_total / profile("C200").mass_kg_m, 0),
            "girts_m": round(girt_total / profile("C200").mass_kg_m / 0.85 / (1.0 + waste), 0),
            "total_kg": round(total_kg, 0),
            "total_t": round(total_kg / 1000.0, 1),
            "kg_m2": round(total_kg / 918.0, 1),
            "frames": frames,
        }

    return result

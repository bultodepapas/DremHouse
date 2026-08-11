"""Staggered truss para el entrepiso P2 — sin columnas interiores (E0/E1).

Sistema desarrollado por MIT / US Steel para hoteles y apartamentos: cerchas de
piso completo que cruzan el ancho del edificio apoyadas solo en las columnas de
los muros largos, escalonadas en planta, con la losa entre cerchas. Permite
areas libres de hasta ~18 m sin columnas interiores y canto de piso compacto.

Aqui se estima el tonelaje de las cerchas y de las viguetas de losa para el P2
de 18 x 15 m. Hipotesis de esquema; no apto para construir.
"""

from __future__ import annotations

import math

from .analysis import simply_supported_deflection, simply_supported_max_moment
from .materials import Steel
from .profiles import lightest_member, profile


def size_staggered_floor(
    cfg: dict,
    steel: Steel,
    bay_m: float,
    phi_b: float,
    phi_c: float,
) -> dict:
    geom = cfg["geometry"]
    crit = cfg["criteria"]
    width = geom["nave_width_m"]
    p2_length = geom["p2_length_m"]

    floor_d = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3
    floor_l = cfg["loads"]["live"]["p2_residential_kpa"] * 1e3
    options = next((o for o in geom.get("p2_floor_options", []) if o["id"] == "STAGGERED"), {})

    n_trusses = max(2, math.ceil(p2_length / bay_m))
    trib = p2_length / n_trusses
    ratio = float(options.get("truss_depth_span_ratio", 16.0))
    depth = width / ratio

    q = (floor_d + floor_l) * trib
    m_peak = simply_supported_max_moment(q, width) / 1e3
    chord_force_kn = m_peak / depth
    chord, _ = lightest_member(steel.fy_pa, phi_b, phi_c, 0.0, chord_force_kn, 2.0, "HSS", None, None)
    if chord.mass_kg_m < profile("HSS120x120x6").mass_kg_m:
        chord = profile("HSS120x120x6")

    web_ratio = 0.40
    truss_kg = 2.0 * chord.mass_kg_m * width * (1.0 + web_ratio)
    ei = steel.e_pa * 2.0 * chord.area_m2 * (depth / 2.0) ** 2
    defl = simply_supported_deflection(q, width, ei)

    joist_span = bay_m
    q_joist = (floor_d + floor_l) * crit["joist_spacing_m"]
    joist, _ = lightest_member(
        steel.fy_pa, phi_b, phi_c,
        simply_supported_max_moment(q_joist, joist_span) / 1e3, 0.0, joist_span, "IPE",
        joist_span * 1000.0 / 240.0, q_joist,
    )
    if joist.mass_kg_m < profile("IPE220").mass_kg_m:
        joist = profile("IPE220")
    n_joists = math.ceil(width / crit["joist_spacing_m"]) + 1
    joists_kg = n_joists * p2_length * joist.mass_kg_m

    total = n_trusses * truss_kg + joists_kg
    return {
        "n_trusses": n_trusses,
        "truss_depth_m": round(depth, 2),
        "chord": chord.name,
        "truss_kg": round(truss_kg, 0),
        "truss_deflection_m": round(defl, 3),
        "joist": joist.name,
        "joists_kg": round(joists_kg, 0),
        "total_kg": round(total, 0),
        "interior_columns": 0,
        "note": "cerchas escalonadas de 18 m entre muros largos; columnas solo en muros",
    }

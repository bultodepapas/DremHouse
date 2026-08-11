"""Staggered truss para el entrepiso P2 — sin columnas interiores (E0/E1).

Sistema desarrollado por MIT / US Steel para hoteles y apartamentos: cerchas de
piso de **canto completo** (altura del muro/entrepiso, d/L ≈ 0.13–0.19) que
cruzan el ancho del edificio apoyadas solo en las columnas de los muros largos,
escalonadas en planta, con la losa entre cerchas. Permite areas libres de hasta
~18 m sin columnas interiores y canto de piso compacto.

Segun la investigacion (AISC / archrecord / SCI P391):
- La cercha ocupa todo el alto del muro: aqui canto ≈ p2_headroom_m (3,0 m).
- Los paneles de losa cuelgan entre el cordon inferior de una cercha y el
  superior de la adyacente; con deck profundo (>200 mm) soportan hasta ~6 m sin
  apuntalar (ComFlor 210/225, SlimDek 210).
- Criterio de vibracion residencial AISC DG11: fn >= 5 Hz (0,2% g).

Aqui se estima el tonelaje de las cerchas y la frecuencia del panel de losa para
el P2 de 18 x 15 m. Hipotesis de esquema; no apto para construir.
"""

from __future__ import annotations

import math

from .analysis import G, simply_supported_deflection, simply_supported_max_moment
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
    options = next((o for o in geom.get("p2_floor_options", []) if o["id"] == "STAGGERED"), {})

    floor_d = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3
    floor_l = cfg["loads"]["live"]["p2_residential_kpa"] * 1e3

    # --- Cerchas de canto completo --------------------------------
    max_panel = float(options.get("max_unpropped_panel_span_m", 6.0))
    n_trusses = max(2, math.ceil(p2_length / max_panel))
    panel = p2_length / n_trusses
    trib = panel  # cada cercha recibe la franja del panel adyacente (medio panel por lado)

    depth = float(options.get("truss_depth_m", 0.0))
    if depth <= 0.0:
        depth = geom["p2_headroom_m"]  # canto completo: altura del muro del P2
    d_over_l = depth / width

    q = (floor_d + floor_l) * trib
    m_peak = simply_supported_max_moment(q, width) / 1e3
    chord_force_kn = m_peak / depth
    chord, _ = lightest_member(steel.fy_pa, phi_b, phi_c, 0.0, chord_force_kn, 2.4, "HSS", None, None)
    if chord.mass_kg_m < profile("HSS100x100x6").mass_kg_m:
        chord = profile("HSS100x100x6")

    web_ratio = float(options.get("web_ratio", 0.4))
    truss_kg = 2.0 * chord.mass_kg_m * width * (1.0 + web_ratio)
    ei = steel.e_pa * 2.0 * chord.area_m2 * (depth / 2.0) ** 2
    defl = simply_supported_deflection(q, width, ei)

    # --- Paneles de losa entre cerchas (deck profundo, sin viguetas) ---
    slab_t = float(options.get("slab_total_m", 0.22))
    e_c = 25.0e9  # modulo sostenido del concreto (hipotesis E0)
    i_strip = slab_t**3 / 12.0
    w_service = floor_d + 0.1 * floor_l  # 1 m de franja; 10% de carga viva
    delta_panel = simply_supported_deflection(w_service, panel, e_c * i_strip)
    fn_panel = 0.18 * math.sqrt(G / max(delta_panel, 1e-9))

    edge_allow = 800.0  # cerchas/vigas menores del borde X=21 (hipotesis E0)
    total = n_trusses * truss_kg + edge_allow

    return {
        "n_trusses": n_trusses,
        "panel_span_m": round(panel, 2),
        "truss_depth_m": round(depth, 2),
        "truss_d_over_l": round(d_over_l, 3),
        "chord": chord.name,
        "truss_kg": round(truss_kg, 0),
        "truss_deflection_m": round(defl, 3),
        "slab_total_m": round(slab_t, 2),
        "panel_deflection_m": round(delta_panel, 4),
        "panel_frequency_hz": round(fn_panel, 1),
        "joist": None,
        "joists_kg": 0.0,
        "total_kg": round(total, 0),
        "interior_columns": 0,
        "note": "cerchas de canto completo (d/L≈0.13–0.19) entre muros largos; paneles de deck profundo sin viguetas; fn>=5 Hz (DG11)",
    }

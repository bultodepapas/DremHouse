"""Alternativas de camino de cargas para el entrepiso P2 (cribado E0).

Sistema desarrollado por MIT / US Steel para hoteles y apartamentos: cerchas de
piso de **canto completo** (altura del muro/entrepiso, d/L ≈ 0.13–0.19) que
cruzan el ancho del edificio apoyadas solo en las columnas de los muros largos,
escalonadas en planta, con la losa entre cerchas. Permite areas libres de hasta
~18 m sin columnas interiores y canto de piso compacto.

Aquí solo se estima un subtotal inferior de acero principal. No se modelan el
deck compuesto, conectores, apuntalamiento, diafragma, vibración, fuego,
estabilidad de barras ni conexiones. Ninguna alternativa queda adoptada o
dimensionada por este archivo.
"""

from __future__ import annotations

import math

from .analysis import simply_supported_deflection, simply_supported_max_moment
from .checks import max_factored_gravity
from .materials import Steel
from .profiles import ProfileSelectionError, lightest_member, profile, series


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

    q_service = (floor_d + floor_l) * trib
    q_strength = max_factored_gravity(cfg, floor_d, floor_l) * trib
    m_peak = simply_supported_max_moment(q_strength, width) / 1e3
    chord_force_kn = m_peak / depth
    chord, _ = lightest_member(steel.fy_pa, phi_b, phi_c, 0.0, chord_force_kn, 2.4, "HSS", None, None)
    if chord.mass_kg_m < profile("HSS100x100x6").mass_kg_m:
        chord = profile("HSS100x100x6")

    web_ratio = float(options.get("web_ratio", 0.4))
    truss_kg = 2.0 * chord.mass_kg_m * width * (1.0 + web_ratio)
    ei = steel.e_pa * 2.0 * chord.area_m2 * (depth / 2.0) ** 2
    defl = simply_supported_deflection(q_service, width, ei)

    # --- Paneles de losa entre cerchas ---------------------------------
    # El E0 anterior trataba slab_total_m como una franja maciza de
    # concreto para rigidez, aunque 0,22 m de concreto pesan 5,50 kPa y la
    # carga muerta total configurada era 3,70 kPa. Sin ficha de deck no hay
    # sección compuesta ni frecuencia defendible: fallar cerrado.
    slab_t = float(options.get("slab_total_m", 0.22))

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
        "panel_deflection_m": None,
        "panel_frequency_hz": None,
        "panel_verification_status": "not_analyzed_manufacturer_composite_section_required",
        "joist": None,
        "joists_kg": 0.0,
        "total_kg": round(total, 0),
        "interior_columns": 0,
        "steel_subtotal_is_lower_bound": True,
        "ranking_eligible": False,
        "approval_status": options.get("approval_status", "not_adopted"),
        "design_status": "incomplete_no_member_stability_connections_or_floor_system",
        "note": "alternativa de cerchas de canto completo; deck, vibración, diafragma, estabilidad y conexiones no analizados",
    }


def size_p2_great_wall(
    cfg: dict,
    steel: Steel,
    phi_b: float,
    phi_c: float,
) -> dict:
    """Cribado de la pared estructural híbrida adoptada por D-043.

    Las vigas X=21→31,5 descargan en una viga superior continua que reparte
    sus reacciones a columnas HSS ocultas en los machones del gran muro. La
    fachada posterior X=36 recibe el extremo de la franja de 4,5 m. El borde
    X=21 se resuelve con una cercha de canto completo por encima del nivel P2.

    El cálculo solo prueba cabida gravitacional con fluencia de sección bruta.
    No atribuye capacidad lateral ni verifica pandeo, uniones, anclajes, fuego,
    diafragma o cimentación.
    """
    geom = cfg["geometry"]
    crit = cfg["criteria"]
    width = geom["nave_width_m"]
    p2_start = geom["p2_start_x_m"]
    p2_length = geom["p2_length_m"]
    wall_x = float(geom.get("great_wall_x_m", 31.5))
    wall_t = float(geom.get("great_wall_t_m", 0.20))
    options = next((o for o in geom.get("p2_floor_options", []) if o["id"] == "GRAN-MURO"), {})

    floor_d = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3
    floor_l = cfg["loads"]["live"]["p2_residential_kpa"] * 1e3
    q_service = floor_d + floor_l
    q_strength = max_factored_gravity(cfg, floor_d, floor_l)

    front = wall_x - p2_start
    rear = (p2_start + p2_length) - wall_x

    # Vigas longitudinales en el plenum (Y≈3/9/15), luz X = 21→31,5 (10,5 m).
    n_beams = max(2, int(options.get("n_longitudinal_beams", 3)))
    spacing = width / n_beams
    q_service_beam = q_service * spacing
    q_strength_beam = q_strength * spacing
    m_beam = simply_supported_max_moment(q_strength_beam, front) / 1e3
    beam, _ = lightest_member(
        steel.fy_pa, phi_b, phi_c, m_beam, 0.0, front, "IPE",
        front / 240.0, q_service_beam / 1e3, e_pa=steel.e_pa,
    )
    if beam.mass_kg_m < profile("IPE360").mass_kg_m:
        beam = profile("IPE360")
    front_beams_kg = n_beams * beam.mass_kg_m * front

    # Continuación posterior X=31,5→36. La revisión anterior llevaba su
    # reacción al muro, pero omitía físicamente estos 4,5 m de viga del peso.
    m_rear = simply_supported_max_moment(q_strength_beam, rear) / 1e3
    rear_beam, _ = lightest_member(
        steel.fy_pa,
        phi_b,
        phi_c,
        m_rear,
        0.0,
        rear,
        "IPE",
        rear / 240.0,
        q_service_beam / 1e3,
        e_pa=steel.e_pa,
    )
    if rear_beam.mass_kg_m < profile("IPE220").mass_kg_m:
        rear_beam = profile("IPE220")
    rear_beams_kg = n_beams * rear_beam.mass_kg_m * rear
    beams_kg = front_beams_kg + rear_beams_kg

    # Cercha de borde X=21 (luz 18 m en Y) que recibe medio frente.
    q_strength_edge = q_strength * front / 2.0
    m_edge = simply_supported_max_moment(q_strength_edge, width) / 1e3
    depth = width / float(options.get("edge_truss_depth_span_ratio", 16.0))
    chord_force_kn = m_edge / depth
    chord, _ = lightest_member(steel.fy_pa, phi_b, phi_c, 0.0, chord_force_kn, 2.4, "HSS", None, None)
    if chord.mass_kg_m < profile("HSS150x150x8").mass_kg_m:
        chord = profile("HSS150x150x8")
    web_ratio = float(options.get("web_ratio", 0.4))
    edge_kg = 2.0 * chord.mass_kg_m * width * (1.0 + web_ratio)

    # Franja del núcleo (X=31,5→36): el sistema de deck no se analiza sin
    # ficha de fabricante y sección compuesta efectiva.
    slab_t = float(options.get("slab_total_m", 0.22))
    beam_depth_m = float(beam.name.removeprefix("IPE")) / 1000.0
    trial_floor_zone_m = beam_depth_m + slab_t
    configured_floor_zone_m = geom["p2_floor_level_m"] - geom["headroom_below_p2_m"]
    trial_clear_below_m = geom["p2_floor_level_m"] - trial_floor_zone_m

    # Bastidor oculto. Las posiciones corresponden a los límites de pantry,
    # bodega, portal de escalera, baño y homelab de la elevación b05.
    beam_ys = [float(y) for y in options.get("beam_y_m", [3.0, 9.0, 15.0])]
    column_ys = [float(y) for y in options.get("hidden_column_y_m", [0.0, 2.4, 7.4, 11.0, 13.4, 18.0])]
    if (
        len(beam_ys) != n_beams
        or column_ys != sorted(column_ys)
        or column_ys[0] != 0.0
        or column_ys[-1] != width
    ):
        raise ValueError("La geometría del bastidor oculto no coincide con el ancho o las vigas")

    # Reacción en X=31,5 de cada línea longitudinal: mitad del tramo frontal
    # más mitad del tramo posterior. No se inventa un muro macizo de concreto.
    p_wall_strength = q_strength * spacing * (front + rear) / 2.0
    p_wall_service = q_service * spacing * (front + rear) / 2.0
    segment_load_positions: dict[int, list[float]] = {
        idx: [] for idx in range(len(column_ys) - 1)
    }
    column_reactions_n = [0.0 for _ in column_ys]
    for beam_y in beam_ys:
        for idx, (left_y, right_y) in enumerate(zip(column_ys, column_ys[1:])):
            if left_y <= beam_y <= right_y:
                span_y = right_y - left_y
                a = beam_y - left_y
                b = right_y - beam_y
                column_reactions_n[idx] += p_wall_strength * b / max(span_y, 1e-9)
                column_reactions_n[idx + 1] += p_wall_strength * a / max(span_y, 1e-9)
                segment_load_positions[idx].append(a)
                break
        else:
            raise ValueError(f"La viga longitudinal Y={beam_y} no cae entre columnas ocultas")

    def segment_max_moment(load_n: float, span_y: float, load_positions: list[float]) -> float:
        """Momento máximo de viga simple con cargas puntuales iguales."""
        if not load_positions:
            return 0.0
        reaction_left = sum(load_n * (span_y - a) / span_y for a in load_positions)
        stations = [0.0, *load_positions, span_y]
        return max(
            reaction_left * x - sum(load_n * (x - a) for a in load_positions if a <= x)
            for x in stations
        )

    def segment_max_deflection(
        load_n: float,
        span_y: float,
        load_positions: list[float],
        ei_n_m2: float,
    ) -> float:
        """Flecha elástica por superposición, evaluada en 101 estaciones."""
        if not load_positions:
            return 0.0
        maximum = 0.0
        for step in range(101):
            x = span_y * step / 100.0
            delta = 0.0
            for a in load_positions:
                b = span_y - a
                if x <= a:
                    delta += load_n * b * x * (span_y**2 - b**2 - x**2) / (6.0 * span_y * ei_n_m2)
                else:
                    xr = span_y - x
                    delta += load_n * a * xr * (span_y**2 - a**2 - xr**2) / (6.0 * span_y * ei_n_m2)
            maximum = max(maximum, abs(delta))
        return maximum

    segment_cases = [
        (column_ys[idx + 1] - column_ys[idx], positions)
        for idx, positions in segment_load_positions.items()
        if positions
    ]
    max_transfer_moment_knm = max(
        (
            segment_max_moment(p_wall_strength, span_y, positions) / 1e3
            for span_y, positions in segment_cases
        ),
        default=0.0,
    )

    min_transfer = profile(options.get("transfer_girder_min_profile", "IPE400"))
    transfer = None
    max_transfer_defl = 0.0
    for cand in series("IPE"):
        if cand.mass_kg_m < min_transfer.mass_kg_m:
            continue
        if cand.moment_capacity_knm(steel.fy_pa, phi_b) < max_transfer_moment_knm:
            continue
        deflections = [
            segment_max_deflection(
                p_wall_service,
                span_y,
                positions,
                steel.e_pa * cand.iy_m4,
            )
            for span_y, positions in segment_cases
        ]
        if all(
            delta <= span_y / 240.0
            for delta, (span_y, _positions) in zip(deflections, segment_cases)
        ):
            transfer = cand
            max_transfer_defl = max(deflections, default=0.0)
            break
    if transfer is None:
        raise ProfileSelectionError("La viga de transferencia del gran muro agota el catálogo IPE del E0")

    hidden_column = profile(options.get("hidden_column_trial_profile", "HSS150x150x8"))
    max_column_reaction_kn = max(column_reactions_n, default=0.0) / 1e3
    column_gross_ratio = max_column_reaction_kn / max(
        hidden_column.axial_capacity_kn(steel.fy_pa, phi_c), 1e-9
    )
    frame_kg = (
        transfer.mass_kg_m * width
        + hidden_column.mass_kg_m * geom["p2_floor_level_m"] * len(column_ys)
    )
    axial_kn_m = p_wall_strength * n_beams / width / 1e3

    total = beams_kg + edge_kg + frame_kg
    return {
        "wall_x_m": wall_x,
        "wall_t_m": wall_t,
        "structural_envelope_m": geom.get("great_wall_structural_envelope_m", [0.25, 0.35]),
        "n_beams": n_beams,
        "beam_profile": beam.name,
        "beam_span_m": round(front, 2),
        "front_beams_kg": round(front_beams_kg, 0),
        "rear_beam_profile": rear_beam.name,
        "rear_beam_span_m": round(rear, 2),
        "rear_beams_kg": round(rear_beams_kg, 0),
        "beams_kg": round(beams_kg, 0),
        "edge_chord": chord.name,
        "edge_kg": round(edge_kg, 0),
        "edge_truss_depth_m": round(depth, 2),
        "edge_truss_location": "full_story_above_p2_floor_no_drop_below_level_3_80",
        "nucleus_span_m": round(rear, 2),
        "slab_total_m": round(slab_t, 2),
        "trial_floor_zone_m": round(trial_floor_zone_m, 2),
        "configured_floor_zone_m": round(configured_floor_zone_m, 2),
        "trial_clear_below_m": round(trial_clear_below_m, 2),
        "floor_zone_margin_m": round(configured_floor_zone_m - trial_floor_zone_m, 2),
        "floor_zone_status": "geometric_trial_only_fire_services_tolerance_and_composite_action_pending",
        "panel_deflection_m": None,
        "panel_frequency_hz": None,
        "panel_verification_status": "not_analyzed_manufacturer_composite_section_required",
        "wall_axial_kn_m": round(axial_kn_m, 1),
        "wall_gravity_reaction_kn_m": round(axial_kn_m, 1),
        "wall_point_reaction_kn": round(p_wall_strength / 1e3, 1),
        "beam_y_m": beam_ys,
        "hidden_column_y_m": column_ys,
        "hidden_column_trial_profile": hidden_column.name,
        "hidden_column_max_reaction_kn": round(max_column_reaction_kn, 1),
        "hidden_column_gross_yield_ratio": round(column_gross_ratio, 3),
        "transfer_girder_trial_profile": transfer.name,
        "transfer_girder_max_moment_knm": round(max_transfer_moment_knm, 1),
        "transfer_girder_max_point_deflection_m": round(max_transfer_defl, 4),
        "hidden_frame_kg": round(frame_kg, 0),
        "total_kg": round(total, 0),
        "interior_columns": 0,
        "steel_subtotal_is_lower_bound": True,
        "ranking_eligible": False,
        "approval_status": options.get("approval_status", "active_gravity_concept_D-043_design_pending"),
        "design_status": "active_gravity_concept_incomplete_no_buckling_connections_fire_foundations_or_lateral_design",
        "lateral_role": "none_assumed_transverse_wall_does_not_stabilize_longitudinal_x",
        "note": "D-043 adopta apoyo gravitacional híbrido de acero oculto; perfiles son pruebas de cabida de sección bruta, no diseño",
    }

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

from .analysis import (
    G,
    overhanging_uniform_beam_response,
    simply_supported_beam_response,
    simply_supported_deflection,
    simply_supported_max_moment,
)
from .checks import max_factored_gravity, span_deflection_limit
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
    n_panels = max(2, math.ceil(p2_length / max_panel))
    n_trusses = n_panels + 1
    panel = p2_length / n_panels
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

    # Un conjunto de N paneles necesita N+1 líneas resistentes. El cálculo
    # anterior contó tres paneles como tres cerchas y sustituyó la cuarta por
    # una reserva arbitraria de 800 kg, subestimando el camino de borde.
    total = n_trusses * truss_kg

    return {
        "n_trusses": n_trusses,
        "n_panels": n_panels,
        "support_x_m": [
            round(geom["p2_start_x_m"] + k * panel, 3)
            for k in range(n_trusses)
        ],
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
    """Cribado de la pared híbrida D-043 con la hipótesis de vigas D-045.

    Las vigas continuas X=21→36 se apoyan en X=21 y X=31,5; los últimos 4,5 m
    vuelan sobre el núcleo para no inventar soportes en la fachada posterior.
    El gran muro reparte sus reacciones a columnas HSS ocultas y el borde X=21
    se resuelve con una cercha de canto completo sobre dos columnas perimetrales.

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

    front = wall_x - p2_start
    rear = (p2_start + p2_length) - wall_x

    # Vigas longitudinales continuas X=21→36, apoyadas en X=21 y en el gran
    # muro X=31,5. El núcleo posterior es un voladizo de 4,5 m: no se inventa
    # un apoyo ni columnas en la fachada X=36.
    n_beams = max(2, int(options.get("n_longitudinal_beams", 3)))
    beam_ys = [float(y) for y in options.get("beam_y_m", [3.0, 9.0, 15.0])]
    column_ys = [float(y) for y in options.get("hidden_column_y_m", [0.0, 2.4, 7.4, 11.0, 13.4, 18.0])]
    if (
        len(beam_ys) != n_beams
        or beam_ys != sorted(set(beam_ys))
        or not all(0.0 < y < width for y in beam_ys)
        or column_ys != sorted(set(column_ys))
        or len(column_ys) < 2
        or column_ys[0] != 0.0
        or column_ys[-1] != width
    ):
        raise ValueError("La geometría del bastidor oculto no coincide con el ancho o las vigas")

    tributary_boundaries = [
        0.0,
        *((left + right) / 2.0 for left, right in zip(beam_ys, beam_ys[1:])),
        width,
    ]
    tributary_widths = [
        right - left
        for left, right in zip(tributary_boundaries, tributary_boundaries[1:])
    ]
    max_tributary = max(tributary_widths)
    beam = None
    beam_strength_trial = None
    beam_service_trial = None
    beam_live_trial = None
    minimum_beam = profile("IPE360")
    for cand in series("IPE"):
        if cand.mass_kg_m < minimum_beam.mass_kg_m:
            continue
        dead_line = floor_d * max_tributary + cand.mass_kg_m * G
        live_line = floor_l * max_tributary
        strength_line = max_factored_gravity(cfg, dead_line, live_line)
        strength_response = overhanging_uniform_beam_response(
            front, rear, strength_line, steel.e_pa * cand.iy_m4
        )
        service_response = overhanging_uniform_beam_response(
            front, rear, dead_line + live_line, steel.e_pa * cand.iy_m4
        )
        live_response = overhanging_uniform_beam_response(
            front, rear, live_line, steel.e_pa * cand.iy_m4
        )
        if cand.moment_capacity_knm(steel.fy_pa, phi_b) < strength_response.max_abs_moment_nm / 1e3:
            continue
        if (
            service_response.max_main_span_deflection_m
            > span_deflection_limit(front, crit["deflection_floor_total"])
            or service_response.max_overhang_deflection_m
            > span_deflection_limit(rear, crit["deflection_floor_total"])
            or live_response.max_main_span_deflection_m
            > span_deflection_limit(front, crit["deflection_floor_live"])
            or live_response.max_overhang_deflection_m
            > span_deflection_limit(rear, crit["deflection_floor_live"])
        ):
            continue
        beam = cand
        beam_strength_trial = strength_response
        beam_service_trial = service_response
        beam_live_trial = live_response
        break
    if beam is None:
        raise ProfileSelectionError("Las vigas continuas con voladizo del P2 agotan el catálogo IPE del E0")

    beam_strength_responses = []
    beam_service_responses = []
    beam_live_responses = []
    for tributary in tributary_widths:
        dead_line = floor_d * tributary + beam.mass_kg_m * G
        live_line = floor_l * tributary
        beam_strength_responses.append(
            overhanging_uniform_beam_response(
                front,
                rear,
                max_factored_gravity(cfg, dead_line, live_line),
                steel.e_pa * beam.iy_m4,
            )
        )
        beam_service_responses.append(
            overhanging_uniform_beam_response(
                front, rear, dead_line + live_line, steel.e_pa * beam.iy_m4
            )
        )
        beam_live_responses.append(
            overhanging_uniform_beam_response(
                front, rear, live_line, steel.e_pa * beam.iy_m4
            )
        )
    front_beams_kg = n_beams * beam.mass_kg_m * front
    rear_beams_kg = n_beams * beam.mass_kg_m * rear
    beams_kg = front_beams_kg + rear_beams_kg

    # Cercha de borde X=21 (luz 18 m en Y) que recibe las reacciones reales
    # del apoyo izquierdo de cada viga longitudinal.
    depth = width / float(options.get("edge_truss_depth_span_ratio", 16.0))
    web_ratio = float(options.get("web_ratio", 0.4))
    edge_strength_points = [
        (y, response.reaction_left_n)
        for y, response in zip(beam_ys, beam_strength_responses)
    ]
    edge_service_points = [
        (y, response.reaction_left_n)
        for y, response in zip(beam_ys, beam_service_responses)
    ]
    edge_live_points = [
        (y, response.reaction_left_n)
        for y, response in zip(beam_ys, beam_live_responses)
    ]
    minimum_chord = profile("HSS150x150x8")
    chord = None
    edge_strength_response = None
    edge_service_response = None
    edge_live_response = None
    truss_kg = 0.0
    for cand in series("HSS"):
        if cand.mass_kg_m < minimum_chord.mass_kg_m:
            continue
        trial_truss_kg = 2.0 * cand.mass_kg_m * width * (1.0 + web_ratio)
        truss_dead_udl = trial_truss_kg * G / width
        strength_response = simply_supported_beam_response(
            width,
            edge_strength_points,
            udl_n_m=max_factored_gravity(cfg, truss_dead_udl, 0.0),
            ei_n_m2=steel.e_pa * 2.0 * cand.area_m2 * (depth / 2.0) ** 2,
        )
        service_response = simply_supported_beam_response(
            width,
            edge_service_points,
            udl_n_m=truss_dead_udl,
            ei_n_m2=steel.e_pa * 2.0 * cand.area_m2 * (depth / 2.0) ** 2,
        )
        live_response = simply_supported_beam_response(
            width,
            edge_live_points,
            ei_n_m2=steel.e_pa * 2.0 * cand.area_m2 * (depth / 2.0) ** 2,
        )
        chord_force_kn = strength_response.max_abs_moment_nm / depth / 1e3
        if cand.axial_capacity_kn(steel.fy_pa, phi_c) < chord_force_kn:
            continue
        if (
            service_response.max_abs_deflection_m
            > span_deflection_limit(width, crit["deflection_floor_total"])
            or live_response.max_abs_deflection_m
            > span_deflection_limit(width, crit["deflection_floor_live"])
        ):
            continue
        chord = cand
        truss_kg = trial_truss_kg
        edge_strength_response = strength_response
        edge_service_response = service_response
        edge_live_response = live_response
        break
    if chord is None:
        raise ProfileSelectionError("La cercha de borde X=21 agota el catálogo HSS del E0")

    edge_column = profile("HEA200")
    edge_column_height = geom["p2_floor_level_m"]
    edge_column_selfweight_n = max_factored_gravity(
        cfg, edge_column.mass_kg_m * G * edge_column_height, 0.0
    )
    edge_column_demand_n = max(
        edge_strength_response.reaction_left_n,
        edge_strength_response.reaction_right_n,
    ) + edge_column_selfweight_n
    edge_column_gross_ratio = edge_column_demand_n / (
        edge_column.axial_capacity_kn(steel.fy_pa, phi_c) * 1e3
    )
    if edge_column_gross_ratio > 1.0:
        raise ProfileSelectionError("Las columnas de borde X=21 agotan el perfil mínimo de prueba")
    edge_columns_kg = 2.0 * edge_column.mass_kg_m * edge_column_height
    edge_kg = truss_kg + edge_columns_kg

    # Franja del núcleo (X=31,5→36): el sistema de deck no se analiza sin
    # ficha de fabricante y sección compuesta efectiva.
    slab_t = float(options.get("slab_total_m", 0.22))
    beam_depth_m = float(beam.name.removeprefix("IPE")) / 1000.0
    trial_floor_zone_m = beam_depth_m + slab_t
    configured_floor_zone_m = geom["p2_floor_level_m"] - geom["headroom_below_p2_m"]
    trial_clear_below_m = geom["p2_floor_level_m"] - trial_floor_zone_m

    # Bastidor oculto. Las posiciones corresponden a los límites de pantry,
    # bodega, portal de escalera, baño y homelab de la elevación b05.
    wall_strength_reactions = [response.reaction_support_n for response in beam_strength_responses]
    wall_service_reactions = [response.reaction_support_n for response in beam_service_responses]
    wall_live_reactions = [response.reaction_support_n for response in beam_live_responses]
    segment_strength_loads: dict[int, list[tuple[float, float]]] = {
        idx: [] for idx in range(len(column_ys) - 1)
    }
    segment_service_loads: dict[int, list[tuple[float, float]]] = {
        idx: [] for idx in range(len(column_ys) - 1)
    }
    segment_live_loads: dict[int, list[tuple[float, float]]] = {
        idx: [] for idx in range(len(column_ys) - 1)
    }
    for beam_y, p_strength, p_service, p_live in zip(
        beam_ys,
        wall_strength_reactions,
        wall_service_reactions,
        wall_live_reactions,
    ):
        for idx, (left_y, right_y) in enumerate(zip(column_ys, column_ys[1:])):
            if left_y <= beam_y <= right_y:
                a = beam_y - left_y
                segment_strength_loads[idx].append((a, p_strength))
                segment_service_loads[idx].append((a, p_service))
                segment_live_loads[idx].append((a, p_live))
                break
        else:
            raise ValueError(f"La viga longitudinal Y={beam_y} no cae entre columnas ocultas")

    min_transfer = profile(options.get("transfer_girder_min_profile", "IPE400"))
    transfer = None
    max_transfer_defl = 0.0
    max_transfer_live_defl = 0.0
    max_transfer_moment_knm = 0.0
    transfer_strength_responses = []
    for cand in series("IPE"):
        if cand.mass_kg_m < min_transfer.mass_kg_m:
            continue
        transfer_dead_udl = cand.mass_kg_m * G
        trial_strength_responses = []
        trial_service_responses = []
        trial_live_responses = []
        for idx in range(len(column_ys) - 1):
            span_y = column_ys[idx + 1] - column_ys[idx]
            trial_strength_responses.append(
                simply_supported_beam_response(
                    span_y,
                    segment_strength_loads[idx],
                    udl_n_m=max_factored_gravity(cfg, transfer_dead_udl, 0.0),
                    ei_n_m2=steel.e_pa * cand.iy_m4,
                )
            )
            trial_service_responses.append(
                simply_supported_beam_response(
                    span_y,
                    segment_service_loads[idx],
                    udl_n_m=transfer_dead_udl,
                    ei_n_m2=steel.e_pa * cand.iy_m4,
                )
            )
            trial_live_responses.append(
                simply_supported_beam_response(
                    span_y,
                    segment_live_loads[idx],
                    ei_n_m2=steel.e_pa * cand.iy_m4,
                )
            )
        trial_moment_knm = max(
            response.max_abs_moment_nm for response in trial_strength_responses
        ) / 1e3
        if cand.moment_capacity_knm(steel.fy_pa, phi_b) < trial_moment_knm:
            continue
        total_deflection_ok = all(
            response.max_abs_deflection_m
            <= span_deflection_limit(column_ys[idx + 1] - column_ys[idx], crit["deflection_floor_total"])
            for idx, response in enumerate(trial_service_responses)
        )
        live_deflection_ok = all(
            response.max_abs_deflection_m
            <= span_deflection_limit(column_ys[idx + 1] - column_ys[idx], crit["deflection_floor_live"])
            for idx, response in enumerate(trial_live_responses)
        )
        if not total_deflection_ok or not live_deflection_ok:
            continue
        transfer = cand
        transfer_strength_responses = trial_strength_responses
        max_transfer_moment_knm = trial_moment_knm
        max_transfer_defl = max(
            response.max_abs_deflection_m for response in trial_service_responses
        )
        max_transfer_live_defl = max(
            response.max_abs_deflection_m for response in trial_live_responses
        )
        break
    if transfer is None:
        raise ProfileSelectionError("La viga de transferencia del gran muro agota el catálogo IPE del E0")

    hidden_column = profile(options.get("hidden_column_trial_profile", "HSS150x150x8"))
    column_reactions_n = [0.0 for _ in column_ys]
    for idx, response in enumerate(transfer_strength_responses):
        column_reactions_n[idx] += response.reaction_left_n
        column_reactions_n[idx + 1] += response.reaction_right_n
    hidden_column_height = geom["p2_floor_level_m"]
    hidden_column_selfweight_n = max_factored_gravity(
        cfg, hidden_column.mass_kg_m * G * hidden_column_height, 0.0
    )
    column_reactions_n = [reaction + hidden_column_selfweight_n for reaction in column_reactions_n]
    max_column_reaction_kn = max(column_reactions_n, default=0.0) / 1e3
    column_gross_ratio = max_column_reaction_kn / max(
        hidden_column.axial_capacity_kn(steel.fy_pa, phi_c), 1e-9
    )
    column_euler_kn = (
        math.pi**2 * steel.e_pa * hidden_column.iy_m4 / hidden_column_height**2 / 1e3
    )
    column_euler_major_ratio = max_column_reaction_kn / max(column_euler_kn, 1e-9)
    if column_gross_ratio > 1.0:
        raise ProfileSelectionError("La columna oculta de prueba agota la fluencia de sección bruta")
    frame_kg = (
        transfer.mass_kg_m * width
        + hidden_column.mass_kg_m * hidden_column_height * len(column_ys)
    )
    axial_kn_m = sum(wall_strength_reactions) / width / 1e3

    total = beams_kg + edge_kg + frame_kg
    return {
        "wall_x_m": wall_x,
        "wall_t_m": wall_t,
        "structural_envelope_m": geom.get("great_wall_structural_envelope_m", [0.25, 0.35]),
        "n_beams": n_beams,
        "beam_profile": beam.name,
        "beam_system": "continuous_supports_x21_x31_5_with_free_overhang_to_x36",
        "beam_total_length_m": round(front + rear, 2),
        "beam_span_m": round(front, 2),
        "front_beams_kg": round(front_beams_kg, 0),
        "rear_beam_profile": beam.name,
        "rear_beam_span_m": round(rear, 2),
        "rear_beams_kg": round(rear_beams_kg, 0),
        "beams_kg": round(beams_kg, 0),
        "beam_tributary_widths_m": [round(value, 3) for value in tributary_widths],
        "beam_max_moment_knm": round(beam_strength_trial.max_abs_moment_nm / 1e3, 1),
        "beam_support_moment_knm": round(beam_strength_trial.support_moment_nm / 1e3, 1),
        "beam_main_span_deflection_m": round(beam_service_trial.max_main_span_deflection_m, 4),
        "beam_overhang_deflection_m": round(beam_service_trial.max_overhang_deflection_m, 4),
        "beam_live_main_span_deflection_m": round(beam_live_trial.max_main_span_deflection_m, 4),
        "rear_support_assumption": "none_free_overhang_from_great_wall",
        "edge_chord": chord.name,
        "edge_kg": round(edge_kg, 0),
        "edge_truss_kg": round(truss_kg, 0),
        "edge_columns_profile": edge_column.name,
        "edge_columns_kg": round(edge_columns_kg, 0),
        "edge_column_max_reaction_kn": round(edge_column_demand_n / 1e3, 1),
        "edge_column_gross_yield_ratio": round(edge_column_gross_ratio, 3),
        "edge_truss_max_moment_knm": round(edge_strength_response.max_abs_moment_nm / 1e3, 1),
        "edge_truss_deflection_m": round(edge_service_response.max_abs_deflection_m, 4),
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
        "wall_point_reaction_kn": round(max(wall_strength_reactions) / 1e3, 1),
        "wall_point_reactions_kn": [round(value / 1e3, 1) for value in wall_strength_reactions],
        "beam_y_m": beam_ys,
        "hidden_column_y_m": column_ys,
        "hidden_column_trial_profile": hidden_column.name,
        "hidden_column_max_reaction_kn": round(max_column_reaction_kn, 1),
        "hidden_column_gross_yield_ratio": round(column_gross_ratio, 3),
        "hidden_column_euler_major_axis_ratio": round(column_euler_major_ratio, 3),
        "hidden_column_euler_scope": "major_axis_elastic_reference_only_weak_axis_and_code_curve_not_available",
        "transfer_girder_trial_profile": transfer.name,
        "transfer_girder_max_moment_knm": round(max_transfer_moment_knm, 1),
        "transfer_girder_max_point_deflection_m": round(max_transfer_defl, 4),
        "transfer_girder_max_live_deflection_m": round(max_transfer_live_defl, 4),
        "hidden_frame_kg": round(frame_kg, 0),
        "total_kg": round(total, 0),
        "interior_columns": 0,
        "steel_subtotal_is_lower_bound": True,
        "ranking_eligible": False,
        "approval_status": options.get("approval_status", "active_gravity_concept_D-043_design_pending"),
        "design_status": "active_gravity_concept_incomplete_no_code_buckling_connections_fire_foundations_or_lateral_design",
        "lateral_role": "none_assumed_transverse_wall_does_not_stabilize_longitudinal_x",
        "note": "D-043 adopta apoyo gravitacional híbrido; D-045 modela el núcleo posterior como voladizo sin apoyo X=36 solo para E0; perfiles son pruebas de cabida, no diseño",
    }

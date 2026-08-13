"""Construcción, carga y cribado del pórtico transversal E0.

El modelo separa gravedad, succión de cubierta y acciones laterales de ambos
signos. Cada miembro guarda sus cargas uniformes por caso; las combinaciones
aplican factores y el ensamble nodal equivalente se calcula después.

Las resistencias usadas aquí son límites superiores de fluencia de sección
bruta. No sustituyen las verificaciones de estabilidad y miembros de NSR-10.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .analysis import (
    Frame2D,
    FrameMember,
    G,
    max_axial_in_member,
    max_moment_in_member,
    simply_supported_deflection,
    simply_supported_max_moment,
)
from .checks import max_factored_gravity, span_deflection_limit
from .materials import Steel
from .profiles import Profile, lightest_member, profile, series

CASES = ("D", "L", "WU", "WX+", "WX-", "EX+", "EX-")
P2_SIDE_COLUMN_SHARE = 1.0 / 6.0


@dataclass
class FrameResults:
    column: Profile
    rafter: Profile
    column_axial_kn: float
    column_moment_knm: float
    rafter_moment_knm: float
    rafter_axial_kn: float
    rafter_deflection_m: float
    drift_m: float
    weight_kg: float
    utilization: float
    tie_force_kn: float = 0.0
    tie_area_cm2: float = 0.0
    screening_passed: bool = False
    design_adequate: bool = False
    analysis_status: str = "screening_incomplete"
    screening_checks: dict = field(default_factory=dict)
    governing_issues: tuple[str, ...] = ()


def build_frame_model(
    steel: Steel,
    eave_low: float,
    eave_high: float,
    p2_level: float,
    has_p2: bool,
    col: Profile,
    rafter: Profile,
    bay_m: float,
    cfg: dict,
    *,
    tie: bool = False,
    tie_area_m2: float = 1.0e-3,
    fixed_base: bool = False,
) -> tuple[Frame2D, dict]:
    width = float(cfg["geometry"]["nave_width_m"])
    nodes = [(0.0, 0.0)]
    if has_p2:
        nodes.append((0.0, p2_level))
    top_low = len(nodes)
    nodes.append((0.0, eave_low))
    base_high = len(nodes)
    nodes.append((width, 0.0))
    p2_high = None
    if has_p2:
        p2_high = len(nodes)
        nodes.append((width, p2_level))
    top_high = len(nodes)
    nodes.append((width, eave_high))
    roof_mid = len(nodes)
    nodes.append((width / 2.0, (eave_low + eave_high) / 2.0))

    members: list[FrameMember] = []
    if has_p2:
        members.append(FrameMember(0, 1, steel.e_pa, col.area_m2, col.iy_m4))
        members.append(FrameMember(1, top_low, steel.e_pa, col.area_m2, col.iy_m4))
    else:
        members.append(FrameMember(0, top_low, steel.e_pa, col.area_m2, col.iy_m4))

    if has_p2:
        members.append(FrameMember(base_high, p2_high, steel.e_pa, col.area_m2, col.iy_m4))
        members.append(FrameMember(p2_high, top_high, steel.e_pa, col.area_m2, col.iy_m4))
    else:
        members.append(FrameMember(base_high, top_high, steel.e_pa, col.area_m2, col.iy_m4))

    roof_d = cfg["loads"]["dead"]["roof_kpa"] * bay_m * 1e3
    roof_l = cfg["loads"]["live"]["roof_kpa"] * bay_m * 1e3
    qz = cfg["loads"]["wind"]["qz_eave_kpa_hypothesis"] * 1e3
    cp_roof_external = (
        cfg["loads"]["wind"]["Cp_roof_windward"]
        + cfg["loads"]["wind"]["Cp_roof_leeward"]
    ) / 2.0
    gcpi = abs(cfg["loads"]["wind"].get("Cp_internal", 0.0))
    # Peor succión global provisional: Cp externo negativo menos presión
    # interna positiva. WU permanece independiente del signo del viento lateral.
    uplift = qz * (cp_roof_external - gcpi) * bay_m
    rafter_sw = rafter.mass_kg_m * G

    rafter_members = []
    for m in (FrameMember(top_low, roof_mid, steel.e_pa, rafter.area_m2, rafter.iy_m4), FrameMember(roof_mid, top_high, steel.e_pa, rafter.area_m2, rafter.iy_m4)):
        members.append(m)
        rafter_members.append(m)
        _set_case_load(m, nodes, "D", roof_d + rafter_sw)
        _set_case_load(m, nodes, "L", roof_l)
        _set_case_load(m, nodes, "WU", uplift)

    tie_member = None
    if tie:
        tie_member = FrameMember(top_low, top_high, steel.e_pa, tie_area_m2, 1e-10)
        members.append(tie_member)

    fix_set = {"ux", "uz"} if not fixed_base else {"ux", "uz", "ry"}
    frame = Frame2D(nodes=nodes, members=members, fixes={0: set(fix_set), base_high: set(fix_set)})
    index = {
        "base_low": 0,
        "p2_low": 1 if has_p2 else None,
        "top_low": top_low,
        "base_high": base_high,
        "p2_high": p2_high,
        "top_high": top_high,
        "roof_mid": roof_mid,
        "tie_high": None,
        "tie_member": tie_member,
        "rafter_members": rafter_members,
    }
    return frame, index


def _set_case_load(m: FrameMember, nodes: list, case: str, w_vert_n_m: float) -> None:
    """Aplica una carga vertical uniforme por unidad de longitud HORIZONTAL.

    Convención: w_vert_n_m > 0 = gravedad (hacia abajo). La carga se proyecta
    sobre los ejes locales del miembro (axial y transversal) de modo que el
    ensamble nodal equivalente quede exactamente vertical, sin componente
    horizontal espuria, y el total vertical sea w·L_horiz.
    """
    x1, z1 = nodes[m.i]
    x2, z2 = nodes[m.j]
    length = np.hypot(x2 - x1, z2 - z1)
    c = (x2 - x1) / length
    s = (z2 - z1) / length
    m.w_cases[case] = (w_vert_n_m * c * c, -w_vert_n_m * s * c)


def build_point_loads(
    frame: Frame2D,
    index: dict,
    cfg: dict,
    bay_m: float,
    trib_p2_m: float,
    has_p2: bool,
    col: Profile,
    rafter: Profile,
    p2_col_share: float = P2_SIDE_COLUMN_SHARE,
) -> dict[str, np.ndarray]:
    n = 3 * len(frame.nodes)
    if not 0.0 <= p2_col_share <= 0.5:
        raise ValueError("La fracción gravitacional por columna lateral debe estar entre 0 y 0,5")
    f_pt = {c: np.zeros(n) for c in CASES}
    nodes = frame.nodes
    eave_low = cfg["geometry"]["eave_low_m"]
    eave_high = cfg["geometry"]["eave_high_m"]
    width = cfg["geometry"]["nave_width_m"]

    col_sw_low = col.mass_kg_m * G * eave_low
    col_sw_high = col.mass_kg_m * G * eave_high
    f_pt["D"][3 * index["top_low"] + 1] -= col_sw_low
    f_pt["D"][3 * index["top_high"] + 1] -= col_sw_high

    if has_p2 and trib_p2_m > 0.0:
        floor_d_col = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3 * trib_p2_m * width * p2_col_share
        floor_l_col = cfg["loads"]["live"]["p2_residential_kpa"] * 1e3 * trib_p2_m * width * p2_col_share
        for key in ("p2_low", "p2_high"):
            idx = index[key]
            f_pt["D"][3 * idx + 1] -= floor_d_col
            f_pt["L"][3 * idx + 1] -= floor_l_col

    qz = cfg["loads"]["wind"]["qz_eave_kpa_hypothesis"] * 1e3
    cp_windward = float(cfg["loads"]["wind"]["Cp_wall_windward"])
    cp_leeward = abs(float(cfg["loads"]["wind"]["Cp_wall_leeward"]))
    # Cada dirección intercambia barlovento/sotavento. El reparto anterior
    # promediaba 0,8 y 0,5 como 0,65 en ambos aleros; eso alteraba la torsión
    # del pórtico y ocultaba que las dos fachadas tienen alturas distintas.
    f_pt["WX+"][3 * index["top_low"]] += qz * cp_windward * bay_m * eave_low
    f_pt["WX+"][3 * index["top_high"]] += qz * cp_leeward * bay_m * eave_high
    f_pt["WX-"][3 * index["top_low"]] -= qz * cp_leeward * bay_m * eave_low
    f_pt["WX-"][3 * index["top_high"]] -= qz * cp_windward * bay_m * eave_high

    w_roof = cfg["loads"]["dead"]["roof_kpa"] * 1e3 * bay_m * width
    rafter_length = sum(frame.member_length(member) for member in index["rafter_members"])
    w_roof += (
        rafter.mass_kg_m * rafter_length
        + col.mass_kg_m * (eave_low + eave_high)
    ) * G
    w_p2 = 0.0
    if has_p2 and trib_p2_m > 0.0:
        w_p2 = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3 * trib_p2_m * width
    cs = cfg["loads"]["seismic"]["cs_base_shear_hypothesis"]
    v = cs * (w_roof + w_p2)
    f_roof = v * w_roof / max(w_roof + w_p2, 1.0)
    f_p2 = v - f_roof
    f_pt["EX+"][3 * index["top_low"]] += f_roof / 2.0
    f_pt["EX+"][3 * index["top_high"]] += f_roof / 2.0
    f_pt["EX-"][3 * index["top_low"]] -= f_roof / 2.0
    f_pt["EX-"][3 * index["top_high"]] -= f_roof / 2.0
    if has_p2:
        f_pt["EX+"][3 * index["p2_low"]] += f_p2 / 2.0
        f_pt["EX+"][3 * index["p2_high"]] += f_p2 / 2.0
        f_pt["EX-"][3 * index["p2_low"]] -= f_p2 / 2.0
        f_pt["EX-"][3 * index["p2_high"]] -= f_p2 / 2.0
    return f_pt


def apply_combo(frame: Frame2D, factors: dict, f_pt: dict[str, np.ndarray]) -> np.ndarray:
    unknown = set(factors) - set(CASES)
    if unknown:
        raise ValueError(f"Casos de carga desconocidos en combinación: {sorted(unknown)}")
    for case, factor in factors.items():
        if not isinstance(factor, (int, float)) or not np.isfinite(factor):
            raise ValueError(f"Factor inválido para {case}: {factor!r}")
    for m in frame.members:
        wy = 0.0
        wx = 0.0
        for case, (wy_c, wx_c) in m.w_cases.items():
            fac = factors.get(case, 0.0)
            wy += fac * wy_c
            wx += fac * wx_c
        m.w_y_n_m = wy
        m.w_x_n_m = wx
    f = frame.equivalent_nodal_loads()
    for case, vec in f_pt.items():
        fac = factors.get(case, 0.0)
        if fac != 0.0:
            if np.asarray(vec).shape != f.shape or not np.all(np.isfinite(vec)):
                raise ValueError(f"Vector nodal inválido para el caso {case}")
            f += fac * vec
    return f


def _reset_member_loads(frame: Frame2D) -> None:
    for m in frame.members:
        m.w_y_n_m = 0.0
        m.w_x_n_m = 0.0


def _member_region(frame: Frame2D, index: dict, m: FrameMember) -> str:
    tops = {index["top_low"], index["top_high"]}
    rafter_ids = {id(mr) for mr in index["rafter_members"]}
    tie = index.get("tie_member")
    if id(m) in rafter_ids:
        return "rafter"
    if tie is not None and id(m) == id(tie):
        return "tie"
    return "column"


def size_portal_frame(
    cfg: dict,
    steel: Steel,
    bay_m: float,
    trib_p2_m: float,
    has_p2: bool,
    phi_b: float,
    phi_c: float,
    p2_col_share: float = P2_SIDE_COLUMN_SHARE,
    *,
    tie: bool = False,
    fixed_base: bool = False,
) -> FrameResults:
    eave_low = cfg["geometry"]["eave_low_m"]
    eave_high = cfg["geometry"]["eave_high_m"]
    p2_level = cfg["geometry"]["p2_floor_level_m"]
    width = cfg["geometry"]["nave_width_m"]
    combos = cfg["combinations"]

    col = profile("HEA300")
    rafter = profile("IPE450")
    tie_area = 1.0e-3

    col_len = max(eave_low, eave_high)
    rafter_len = np.hypot(width, eave_high - eave_low)
    defl_limit = span_deflection_limit(rafter_len, cfg["criteria"]["deflection_roof_total"])
    drift_limit = span_deflection_limit(col_len, cfg["criteria"]["drift_allowance"])

    def envelope(frame: Frame2D, index: dict, f_pt: dict):
        env_m = {"column": 0.0, "rafter": 0.0, "tie": 0.0}
        env_n = {"column": 0.0, "rafter": 0.0, "tie": 0.0}
        for combo in combos:
            f = apply_combo(frame, combo["factors"], f_pt)
            d, _k = frame.solve(f)
            for m in frame.members:
                fl = frame.member_end_forces(m, d)
                region = _member_region(frame, index, m)
                env_m[region] = max(env_m[region], max_moment_in_member(frame, m, fl) / 1e3)
                env_n[region] = max(env_n[region], max_axial_in_member(fl) / 1e3)
            _reset_member_loads(frame)
        return env_m, env_n

    def service(frame: Frame2D, index: dict, f_pt: dict):
        rafter_defl = 0.0
        for service_factors in ({"D": 1.0, "L": 1.0}, {"D": 1.0, "WU": 1.0}):
            f = apply_combo(frame, service_factors, f_pt)
            d, _k = frame.solve(f)
            _reset_member_loads(frame)
            uz = {
                node: d[3 * node + 1]
                for node in (index["top_low"], index["top_high"], index["roof_mid"])
            }
            relative = abs(
                uz[index["roof_mid"]]
                - (uz[index["top_low"]] + uz[index["top_high"]]) / 2.0
            )
            rafter_defl = max(rafter_defl, relative)

        drift = 0.0
        for wind_case in ("WX+", "WX-"):
            f_sw = apply_combo(frame, {wind_case: 1.0}, f_pt)
            d_sw, _k = frame.solve(f_sw)
            _reset_member_loads(frame)
            drift = max(
                drift,
                abs(d_sw[3 * index["top_low"]]),
                abs(d_sw[3 * index["top_high"]]),
            )
        return rafter_defl, drift

    tie_force = 0.0
    screening_checks: dict[str, bool] = {}
    for _outer in range(12):
        frame, index = build_frame_model(steel, eave_low, eave_high, p2_level, has_p2, col, rafter, bay_m, cfg,
                                         tie=tie, tie_area_m2=tie_area, fixed_base=fixed_base)
        f_pt = build_point_loads(frame, index, cfg, bay_m, trib_p2_m, has_p2, col, rafter, p2_col_share)
        env_m, env_n = envelope(frame, index, f_pt)
        rafter_defl, drift = service(frame, index, f_pt)
        rafter_util = (
            env_n["rafter"]
            / max(rafter.axial_capacity_kn(steel.fy_pa, phi_c), 1e-9)
            + env_m["rafter"]
            / max(rafter.moment_capacity_knm(steel.fy_pa, phi_b), 1e-9)
        )
        rafter_strength_ok = rafter_util <= 1.0 + 1e-9
        rafter_defl_ok = rafter_defl <= defl_limit
        drift_ok = drift <= drift_limit
        col_util = env_n["column"] / max(col.axial_capacity_kn(steel.fy_pa, phi_c), 1e-9) + env_m["column"] / max(col.moment_capacity_knm(steel.fy_pa, phi_b), 1e-9)
        col_ok = col_util <= 1.0 + 1e-9
        tie_force = env_n["tie"] if tie else 0.0
        tie_capacity_kn = phi_b * steel.fy_pa * tie_area / 1e3
        tie_ok = (not tie) or tie_force <= tie_capacity_kn * (1.0 + 1e-9)
        screening_checks = {
            "rafter_gross_yield_interaction": bool(rafter_strength_ok),
            "rafter_deflection": bool(rafter_defl_ok),
            "frame_drift": bool(drift_ok),
            "column_gross_yield_interaction": bool(col_ok),
        }
        if tie:
            screening_checks["tie_gross_yield"] = bool(tie_ok)
        if rafter_strength_ok and rafter_defl_ok and drift_ok and col_ok and tie_ok:
            break
        changed = False
        if (not rafter_strength_ok or not rafter_defl_ok) and rafter.name != "IPE600":
            next_rafter = _next_ipe(rafter.name)
            changed = changed or next_rafter != rafter.name
            rafter = profile(next_rafter)
        if not drift_ok or not col_ok:
            next_col = _next_hea(col.name)
            changed = changed or next_col != col.name
            col = profile(next_col)
        if tie and not tie_ok:
            need = max(abs(tie_force) * 1e3 / (phi_b * steel.fy_pa), 2.0e-4)
            if need > tie_area:
                tie_area = need
                changed = True
        if not changed:
            break

    frame, index = build_frame_model(steel, eave_low, eave_high, p2_level, has_p2, col, rafter, bay_m, cfg,
                                     tie=tie, tie_area_m2=tie_area, fixed_base=fixed_base)
    f_pt = build_point_loads(frame, index, cfg, bay_m, trib_p2_m, has_p2, col, rafter, p2_col_share)
    env_m, env_n = envelope(frame, index, f_pt)
    rafter_defl, drift = service(frame, index, f_pt)

    mcap = rafter.moment_capacity_knm(steel.fy_pa, phi_b)
    rafter_acap = rafter.axial_capacity_kn(steel.fy_pa, phi_c)
    acap = col.axial_capacity_kn(steel.fy_pa, phi_c)
    col_util = env_n["column"] / max(acap, 1e-9) + env_m["column"] / max(col.moment_capacity_knm(steel.fy_pa, phi_b), 1e-9)
    rafter_util = env_n["rafter"] / max(rafter_acap, 1e-9) + env_m["rafter"] / max(mcap, 1e-9)
    utilization = max(col_util, rafter_util)
    screening_checks = {
        "rafter_gross_yield_interaction": bool(rafter_util <= 1.0 + 1e-9),
        "rafter_deflection": bool(rafter_defl <= defl_limit),
        "frame_drift": bool(drift <= drift_limit),
        "column_gross_yield_interaction": bool(col_util <= 1.0 + 1e-9),
    }
    if tie:
        screening_checks["tie_gross_yield"] = bool(
            env_n["tie"] <= phi_b * steel.fy_pa * tie_area / 1e3 * (1.0 + 1e-9)
        )
    screening_passed = all(screening_checks.values())
    governing_issues = tuple(name for name, passed in screening_checks.items() if not passed)
    analysis_status = (
        "screening_passed_but_stability_not_checked"
        if screening_passed
        else "catalog_exhausted_or_screening_failed"
    )

    detail = cfg["criteria"]["detail_factor_principales"]
    tie_kg = width * tie_area * steel.density_kg_m3 if tie else 0.0
    weight = (2.0 * col.mass_kg_m * col_len + rafter.mass_kg_m * rafter_len + tie_kg) * (1.0 + detail)

    return FrameResults(
        column=col,
        rafter=rafter,
        column_axial_kn=env_n["column"],
        column_moment_knm=env_m["column"],
        rafter_moment_knm=env_m["rafter"],
        rafter_axial_kn=env_n["rafter"],
        rafter_deflection_m=rafter_defl,
        drift_m=drift,
        weight_kg=weight,
        utilization=utilization,
        tie_force_kn=env_n["tie"],
        tie_area_cm2=tie_area * 1e4 if tie else 0.0,
        screening_passed=screening_passed,
        design_adequate=False,
        analysis_status=analysis_status,
        screening_checks=screening_checks,
        governing_issues=governing_issues,
    )


def _next_ipe(name: str) -> str:
    return _next_dominating_profile(name, ("IPE",))


def _next_hea(name: str) -> str:
    return _next_dominating_profile(name, ("HEA", "HEB"))


def _next_dominating_profile(name: str, prefixes: tuple[str, ...]) -> str:
    """Siguiente perfil más pesado que no reduce A, Iy ni Wy."""

    current = profile(name)
    candidates = sorted(
        (
            candidate
            for prefix in prefixes
            for candidate in series(prefix)
            if candidate.mass_kg_m > current.mass_kg_m
            and candidate.area_m2 >= current.area_m2
            and candidate.iy_m4 >= current.iy_m4
            and candidate.wy_m3 >= current.wy_m3
        ),
        key=lambda candidate: (candidate.mass_kg_m, candidate.name),
    )
    return candidates[0].name if candidates else current.name


def size_cercha_roof(
    cfg: dict,
    steel: Steel,
    bay_m: float,
    phi_b: float,
    phi_c: float,
) -> tuple[Profile, float, float]:
    roof_d = cfg["loads"]["dead"]["roof_kpa"] * bay_m * 1e3
    roof_l = cfg["loads"]["live"]["roof_kpa"] * bay_m * 1e3
    q_peak = max_factored_gravity(cfg, roof_d, roof_l)
    span = cfg["geometry"]["nave_width_m"]
    truss = next(s for s in cfg["systems"] if s["id"] == "CERCHA")
    depth = span / truss["truss_depth_span_ratio"]
    m_peak = simply_supported_max_moment(q_peak, span)
    chord_force_kn = m_peak / depth / 1e3
    panel = 1.5
    chord, _ = lightest_member(steel.fy_pa, phi_b, phi_c, 0.0, chord_force_kn, panel, "IPE", None, None)
    if chord.mass_kg_m < profile("IPE220").mass_kg_m:
        chord = profile("IPE220")
    web_ratio = 0.5
    truss_mass_kg = (2.0 * chord.mass_kg_m) * (1.0 + web_ratio) * span
    q_service = roof_d + roof_l
    ei = steel.e_pa * 2.0 * chord.area_m2 * (depth / 2.0) ** 2
    defl = simply_supported_deflection(q_service, span, ei)
    return chord, truss_mass_kg, defl


def size_cercha_columns(
    cfg: dict,
    steel: Steel,
    axial_kn: float,
    col_len: float,
    phi_c: float,
) -> Profile:
    col, _ = lightest_member(steel.fy_pa, 0.9, phi_c, 0.0, axial_kn, col_len, "HEA", None, None)
    if col.mass_kg_m < profile("HEA200").mass_kg_m:
        col = profile("HEA200")
    return col


def size_joists_and_beams(cfg: dict, steel: Steel, bay_m: float, trib_p2_m: float, phi_b: float, phi_c: float) -> dict:
    crit = cfg["criteria"]
    floor_d = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3
    floor_l = cfg["loads"]["live"]["p2_residential_kpa"] * 1e3
    spacing = crit["joist_spacing_m"]
    span = bay_m
    width = cfg["geometry"]["nave_width_m"]

    q_service_joist = (floor_d + floor_l) * spacing
    q_strength_joist = max_factored_gravity(cfg, floor_d, floor_l) * spacing
    joist, _ = lightest_member(
        steel.fy_pa, phi_b, phi_c,
        simply_supported_max_moment(q_strength_joist, span) / 1e3,
        0.0, span, "IPE",
        span_deflection_limit(span, crit["deflection_floor_total"]),
        q_service_joist / 1e3,
        e_pa=steel.e_pa,
        live_deflection_limit_m=span_deflection_limit(span, crit["deflection_floor_live"]),
        q_live_kn_m=floor_l * spacing / 1e3,
    )
    if joist.mass_kg_m < profile("IPE220").mass_kg_m:
        joist = profile("IPE220")

    q_service_beam = (floor_d + floor_l) * trib_p2_m
    q_strength_beam = max_factored_gravity(cfg, floor_d, floor_l) * trib_p2_m
    beam_span = width / 3.0  # dos apoyos intermedios por pórtico -> 3 tramos
    # Cribado conservador como tramo simplemente apoyado. La reducción /1,5
    # anterior no verificaba los momentos negativos de una viga continua.
    m_beam = simply_supported_max_moment(q_strength_beam, beam_span)
    beam, _ = lightest_member(
        steel.fy_pa, phi_b, phi_c, m_beam / 1e3, 0.0, beam_span, "IPE",
        span_deflection_limit(beam_span, crit["deflection_floor_total"]),
        q_service_beam / 1e3,
        e_pa=steel.e_pa,
        live_deflection_limit_m=span_deflection_limit(beam_span, crit["deflection_floor_live"]),
        q_live_kn_m=floor_l * trib_p2_m / 1e3,
    )

    q_service_edge = (floor_d + floor_l) * bay_m / 2.0
    q_strength_edge = max_factored_gravity(cfg, floor_d, floor_l) * bay_m / 2.0
    edge_span = width / 2.0
    edge, _ = lightest_member(
        steel.fy_pa, phi_b, phi_c,
        simply_supported_max_moment(q_strength_edge, edge_span) / 1e3,
        0.0, edge_span, "IPE",
        span_deflection_limit(edge_span, crit["deflection_floor_total"]),
        q_service_edge / 1e3,
        e_pa=steel.e_pa,
        live_deflection_limit_m=span_deflection_limit(edge_span, crit["deflection_floor_live"]),
        q_live_kn_m=floor_l * bay_m / 2.0 / 1e3,
    )

    aux_col = profile("HEA200")
    return {"joist": joist, "beam": beam, "edge": edge, "aux_col": aux_col}



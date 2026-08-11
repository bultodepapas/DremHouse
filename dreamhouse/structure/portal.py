"""Construcción, carga y dimensionamiento del pórtico transversal E0.

El modelo separa las cargas por caso (D, L, W, E). Cada miembro guarda sus
cargas uniformes por caso; las combinaciones aplican factores y el ensamble de
cargas nodales equivalentes se calcula con los factores ya aplicados.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .analysis import (
    Frame2D,
    FrameMember,
    G,
    deflection_at_midspan,
    max_axial_in_member,
    max_moment_in_member,
    simply_supported_deflection,
    simply_supported_max_moment,
)
from .materials import Steel
from .profiles import Profile, lightest_member, profile

CASES = ("D", "L", "W", "E")


@dataclass
class FrameResults:
    column: Profile
    rafter: Profile
    column_axial_kn: float
    column_moment_knm: float
    rafter_moment_knm: float
    rafter_deflection_m: float
    drift_m: float
    weight_kg: float
    utilization: float
    tie_force_kn: float = 0.0
    tie_area_cm2: float = 0.0


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
    nodes = [(0.0, 0.0)]
    if has_p2:
        nodes.append((0.0, p2_level))
    top_low = len(nodes)
    nodes.append((0.0, eave_low))
    base_high = len(nodes)
    nodes.append((18.0, 0.0))
    p2_high = None
    if has_p2:
        p2_high = len(nodes)
        nodes.append((18.0, p2_level))
    top_high = len(nodes)
    nodes.append((18.0, eave_high))
    roof_mid = len(nodes)
    nodes.append((9.0, (eave_low + eave_high) / 2.0))

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
    uplift = -qz * (cfg["loads"]["wind"]["Cp_roof_windward"] + cfg["loads"]["wind"]["Cp_roof_leeward"]) / 2.0 * bay_m
    rafter_sw = rafter.mass_kg_m * G

    rafter_members = []
    for m in (FrameMember(top_low, roof_mid, steel.e_pa, rafter.area_m2, rafter.iy_m4), FrameMember(roof_mid, top_high, steel.e_pa, rafter.area_m2, rafter.iy_m4)):
        members.append(m)
        rafter_members.append(m)
        _set_case_load(m, nodes, "D", roof_d + rafter_sw)
        _set_case_load(m, nodes, "L", roof_l)
        _set_case_load(m, nodes, "W", uplift)

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
    x1, z1 = nodes[m.i]
    x2, z2 = nodes[m.j]
    length = np.hypot(x2 - x1, z2 - z1)
    c = (x2 - x1) / length
    s = (z2 - z1) / length
    m.w_cases[case] = (w_vert_n_m * c, -w_vert_n_m * s)


def build_point_loads(
    frame: Frame2D,
    index: dict,
    cfg: dict,
    bay_m: float,
    trib_p2_m: float,
    has_p2: bool,
    col: Profile,
    rafter: Profile,
    p2_col_share: float = 0.25,
) -> dict[str, np.ndarray]:
    n = 3 * len(frame.nodes)
    f_pt = {c: np.zeros(n) for c in CASES}
    nodes = frame.nodes
    eave_low = cfg["geometry"]["eave_low_m"]
    eave_high = cfg["geometry"]["eave_high_m"]

    col_sw_low = col.mass_kg_m * G * eave_low
    col_sw_high = col.mass_kg_m * G * eave_high
    f_pt["D"][3 * index["top_low"] + 1] += col_sw_low
    f_pt["D"][3 * index["top_high"] + 1] += col_sw_high

    if has_p2 and trib_p2_m > 0.0:
        floor_d_col = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3 * trib_p2_m * 18.0 * p2_col_share
        floor_l_col = cfg["loads"]["live"]["p2_residential_kpa"] * 1e3 * trib_p2_m * 18.0 * p2_col_share
        for key in ("p2_low", "p2_high"):
            idx = index[key]
            f_pt["D"][3 * idx + 1] += floor_d_col
            f_pt["L"][3 * idx + 1] += floor_l_col

    qz = cfg["loads"]["wind"]["qz_eave_kpa_hypothesis"] * 1e3
    net_wall = qz * (cfg["loads"]["wind"]["Cp_wall_windward"] + cfg["loads"]["wind"]["Cp_wall_leeward"])
    wall_h = net_wall * bay_m * (eave_low + eave_high) / 2.0
    h_low = wall_h * eave_low / (eave_low + eave_high)
    h_high = wall_h - h_low
    f_pt["W"][3 * index["top_low"]] += h_low
    f_pt["W"][3 * index["top_high"]] += h_high

    w_roof = cfg["loads"]["dead"]["roof_kpa"] * 1e3 * bay_m * 18.0
    w_roof += (rafter.mass_kg_m * 18.5 + 2.0 * col.mass_kg_m * (eave_low + eave_high) / 2.0) * G
    w_p2 = 0.0
    if has_p2 and trib_p2_m > 0.0:
        w_p2 = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3 * trib_p2_m * 18.0
    cs = cfg["loads"]["seismic"]["cs_base_shear_hypothesis"]
    v = cs * (w_roof + w_p2)
    f_roof = v * w_roof / max(w_roof + w_p2, 1.0)
    f_p2 = v - f_roof
    f_pt["E"][3 * index["top_low"]] += f_roof / 2.0
    f_pt["E"][3 * index["top_high"]] += f_roof / 2.0
    if has_p2:
        f_pt["E"][3 * index["p2_low"]] += f_p2 / 2.0
        f_pt["E"][3 * index["p2_high"]] += f_p2 / 2.0
    return f_pt


def apply_combo(frame: Frame2D, factors: dict, f_pt: dict[str, np.ndarray]) -> np.ndarray:
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
    p2_col_share: float = 0.25,
    *,
    tie: bool = False,
    fixed_base: bool = False,
) -> FrameResults:
    eave_low = cfg["geometry"]["eave_low_m"]
    eave_high = cfg["geometry"]["eave_high_m"]
    p2_level = cfg["geometry"]["p2_floor_level_m"]
    combos = cfg["combinations"]

    col = profile("HEA300")
    rafter = profile("IPE450")
    tie_area = 1.0e-3

    col_len = max(eave_low, eave_high)
    rafter_len = np.hypot(18.0, eave_high - eave_low)
    defl_limit = rafter_len * 1000.0 / 180.0
    drift_limit = col_len / 200.0

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
        f = apply_combo(frame, {"D": 1.0, "L": 1.0}, f_pt)
        d, _k = frame.solve(f)
        _reset_member_loads(frame)
        uz = {node: d[3 * node + 1] for node in (index["top_low"], index["top_high"], index["roof_mid"])}
        rafter_defl = abs(uz[index["roof_mid"]] - (uz[index["top_low"]] + uz[index["top_high"]]) / 2.0)
        f_sw = apply_combo(frame, {"D": 1.0, "W": 1.0}, f_pt)
        d_sw, _k = frame.solve(f_sw)
        _reset_member_loads(frame)
        drift = max(abs(d_sw[3 * index["top_low"]]), abs(d_sw[3 * index["top_high"]]))
        return rafter_defl, drift

    tie_force = 0.0
    for _outer in range(8):
        frame, index = build_frame_model(steel, eave_low, eave_high, p2_level, has_p2, col, rafter, bay_m, cfg,
                                         tie=tie, tie_area_m2=tie_area, fixed_base=fixed_base)
        f_pt = build_point_loads(frame, index, cfg, bay_m, trib_p2_m, has_p2, col, rafter, p2_col_share)
        env_m, env_n = envelope(frame, index, f_pt)
        rafter_defl, drift = service(frame, index, f_pt)
        rafter_strength_ok = env_m["rafter"] <= rafter.moment_capacity_knm(steel.fy_pa, phi_b)
        rafter_defl_ok = rafter_defl <= defl_limit
        drift_ok = drift <= drift_limit or col.name in ("HEA500", "HEB400")
        if rafter_strength_ok and rafter_defl_ok and drift_ok:
            break
        if (not rafter_strength_ok or not rafter_defl_ok) and rafter.name != "IPE600":
            rafter = profile(_next_ipe(rafter.name))
        if not drift_ok:
            col = profile(_next_hea(col.name))
        if tie:
            tie_force = env_n["tie"]
            need = max(abs(tie_force) * 1e3 / (phi_c * steel.fy_pa), 2.0e-4)
            tie_area = max(tie_area, need)

    frame, index = build_frame_model(steel, eave_low, eave_high, p2_level, has_p2, col, rafter, bay_m, cfg,
                                     tie=tie, tie_area_m2=tie_area, fixed_base=fixed_base)
    f_pt = build_point_loads(frame, index, cfg, bay_m, trib_p2_m, has_p2, col, rafter, p2_col_share)
    env_m, env_n = envelope(frame, index, f_pt)
    rafter_defl, drift = service(frame, index, f_pt)

    mcap = rafter.moment_capacity_knm(steel.fy_pa, phi_b)
    acap = col.axial_capacity_kn(steel.fy_pa, phi_c)
    utilization = max(env_n["column"] / max(acap, 1e-9) + env_m["column"] / max(col.moment_capacity_knm(steel.fy_pa, phi_b), 1e-9), env_m["rafter"] / max(mcap, 1e-9))

    detail = cfg["criteria"]["detail_factor_principales"]
    tie_kg = 18.0 * tie_area * steel.density_kg_m3 if tie else 0.0
    weight = (2.0 * col.mass_kg_m * col_len + rafter.mass_kg_m * rafter_len + tie_kg) * (1.0 + detail)

    return FrameResults(
        column=col,
        rafter=rafter,
        column_axial_kn=env_n["column"],
        column_moment_knm=env_m["column"],
        rafter_moment_knm=env_m["rafter"],
        rafter_deflection_m=rafter_defl,
        drift_m=drift,
        weight_kg=weight,
        utilization=utilization,
        tie_force_kn=env_n["tie"],
        tie_area_cm2=tie_area * 1e4 if tie else 0.0,
    )


def _next_ipe(name: str) -> str:
    order = ["IPE200", "IPE220", "IPE240", "IPE270", "IPE300", "IPE330", "IPE360", "IPE400", "IPE450", "IPE500", "IPE550", "IPE600"]
    if name not in order:
        return "IPE600"
    i = order.index(name)
    return order[min(i + 1, len(order) - 1)]


def _next_hea(name: str) -> str:
    order = ["HEA200", "HEA240", "HEA300", "HEA340", "HEA400", "HEA500", "HEB200", "HEB240", "HEB300", "HEB340", "HEB400"]
    if name not in order:
        return "HEA400"
    i = order.index(name)
    return order[min(i + 1, len(order) - 1)]


def size_cercha_roof(
    cfg: dict,
    steel: Steel,
    bay_m: float,
    phi_b: float,
    phi_c: float,
) -> tuple[Profile, float, float]:
    roof_d = cfg["loads"]["dead"]["roof_kpa"] * bay_m * 1e3
    roof_l = cfg["loads"]["live"]["roof_kpa"] * bay_m * 1e3
    q_peak = max(roof_d + roof_l, 1.2 * roof_d + 1.6 * roof_l)
    span = 18.0
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

    q_joist = (floor_d + floor_l) * spacing
    joist, _ = lightest_member(steel.fy_pa, phi_b, phi_c, simply_supported_max_moment(q_joist, span) / 1e3, 0.0, span, "IPE", span * 1000.0 / 240.0, q_joist)
    if joist.mass_kg_m < profile("IPE220").mass_kg_m:
        joist = profile("IPE220")

    q_beam = (floor_d + floor_l) * trib_p2_m
    beam_span = 18.0 / 4.0
    m_beam = simply_supported_max_moment(q_beam, beam_span) / 1.5
    beam, _ = lightest_member(steel.fy_pa, phi_b, phi_c, m_beam / 1e3, 0.0, beam_span, "IPE", beam_span * 1000.0 / 240.0, q_beam)

    q_edge = (floor_d + floor_l) * bay_m / 2.0
    edge, _ = lightest_member(steel.fy_pa, phi_b, phi_c, simply_supported_max_moment(q_edge, 9.0) / 1e3, 0.0, 9.0, "IPE", 9.0 * 1000.0 / 240.0, q_edge)

    aux_col = profile("HEA200")
    return {"joist": joist, "beam": beam, "edge": edge, "aux_col": aux_col}



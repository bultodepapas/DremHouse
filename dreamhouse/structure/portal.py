"""Construcción, carga y dimensionamiento del pórtico transversal E0."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .analysis import Frame2D, FrameMember, G, deflection_at_midspan, max_axial_in_member, max_moment_in_member, simply_supported_max_moment, simply_supported_deflection
from .materials import Steel
from .profiles import Profile, lightest_member, profile

DOFS = ("ux", "uz", "ry")


@dataclass
class FrameResults:
    column_low: Profile
    column_high: Profile
    rafter: Profile
    column_axial_kn: float
    column_moment_knm: float
    rafter_moment_knm: float
    rafter_deflection_m: float
    drift_m: float
    rafter_utilization: float
    column_utilization: float
    weight_kg: float


def build_frame_model(
    steel: Steel,
    eave_low: float,
    eave_high: float,
    p2_level: float,
    has_p2: bool,
    col: Profile,
    rafter: Profile,
    roof_q_d_n_m: float,
    roof_q_l_n_m: float,
    roof_wind_uplift_n_m: float,
) -> tuple[Frame2D, dict]:
    nodes = [(0.0, 0.0)]
    if has_p2:
        nodes.append((0.0, p2_level))
    nodes.append((0.0, eave_low))
    nodes.append((18.0, 0.0))
    if has_p2:
        nodes.append((18.0, p2_level))
    nodes.append((18.0, eave_high))
    nodes.append((9.0, (eave_low + eave_high) / 2.0))

    members: list[FrameMember] = []
    if has_p2:
        members.append(FrameMember(0, 1, steel.e_pa, col.area_m2, col.iy_m4))
        members.append(FrameMember(1, 2, steel.e_pa, col.area_m2, col.iy_m4))
        members.append(FrameMember(3, 4, steel.e_pa, col.area_m2, col.iy_m4))
        members.append(FrameMember(4, 5, steel.e_pa, col.area_m2, col.iy_m4))
    else:
        members.append(FrameMember(0, 2, steel.e_pa, col.area_m2, col.iy_m4))
        members.append(FrameMember(3, 5, steel.e_pa, col.area_m2, col.iy_m4))

    c, s = _dir(0.0, eave_low, 9.0, (eave_low + eave_high) / 2.0)
    rafter_w_y = roof_q_d_n_m + roof_q_l_n_m + roof_wind_uplift_n_m
    rafter_w_y_local = rafter_w_y * c
    rafter_w_x_local = -rafter_w_y * s
    rafter_sw = rafter.mass_kg_m * G
    members.append(FrameMember(2, 6, steel.e_pa, rafter.area_m2, rafter.iy_m4, rafter_w_y_local + rafter_sw * c, rafter_w_x_local - rafter_sw * s))
    members.append(FrameMember(6, 5, steel.e_pa, rafter.area_m2, rafter.iy_m4, rafter_w_y_local + rafter_sw * c, rafter_w_x_local - rafter_sw * s))

    frame = Frame2D(nodes=nodes, members=members, fixes={0: {"ux", "uz"}, 3: {"ux", "uz"}})
    index = {"base_low": 0, "p2_low": 1 if has_p2 else None, "top_low": 2, "base_high": 3, "p2_high": 4 if has_p2 else None, "top_high": 5, "roof_mid": 6}
    return frame, index


def _dir(x1: float, z1: float, x2: float, z2: float) -> tuple[float, float]:
    length = np.hypot(x2 - x1, z2 - z1)
    return (x2 - x1) / length, (z2 - z1) / length


def _vertical_udl_on_member(frame: Frame2D, m: FrameMember, w_vert_n_m: float) -> None:
    c, s = frame.member_dir(m)
    m.w_y_n_m += w_vert_n_m * c
    m.w_x_n_m += -w_vert_n_m * s


def build_load_cases(
    frame: Frame2D,
    index: dict,
    cfg: dict,
    bay_m: float,
    trib_p2_m: float,
    has_p2: bool,
    col_low: Profile,
    col_high: Profile,
    rafter: Profile,
) -> dict[str, np.ndarray]:
    nodes = frame.nodes
    f_d = frame.equivalent_nodal_loads()
    f_l = np.zeros_like(f_d)
    f_w = np.zeros_like(f_d)
    f_e = np.zeros_like(f_d)

    roof_d = cfg["loads"]["dead"]["roof_kpa"] * bay_m * 1000.0
    roof_l = cfg["loads"]["live"]["roof_kpa"] * bay_m * 1000.0
    wind = cfg["loads"]["wind"]
    qz = wind["qz_eave_kpa_hypothesis"] * 1000.0
    net_wall = qz * (wind["Cp_wall_windward"] + wind["Cp_wall_leeward"])
    avg_eave = (cfg["geometry"]["eave_low_m"] + cfg["geometry"]["eave_high_m"]) / 2.0
    wall_h = net_wall * bay_m * avg_eave
    roof_uplift = qz * (wind["Cp_roof_windward"] + wind["Cp_roof_leeward"]) / 2.0 * bay_m
    roof_uplift_n_m = roof_uplift

    rafter_members = [m for m in frame.members if m.i == index["top_low"] or m.j == index["top_high"]]
    for m in rafter_members:
        _vertical_udl_on_member(frame, m, roof_d)
        _vertical_udl_on_member(frame, m, roof_l)
        _vertical_udl_on_member(frame, m, -roof_uplift_n_m)

    f_d += frame.equivalent_nodal_loads()
    _clear_member_udl(frame, rafter_members, roof_d, roof_l, -roof_uplift_n_m)
    f_l += frame.equivalent_nodal_loads()
    _clear_member_udl(frame, rafter_members, 0.0, 0.0, roof_uplift_n_m)
    f_w += frame.equivalent_nodal_loads()

    if has_p2 and trib_p2_m > 0.0:
        floor_d_col = cfg["loads"]["dead"]["floor_p2_kpa"] * 1000.0 * trib_p2_m * 18.0 / 2.0
        floor_part_col = cfg["loads"]["dead"]["partitions_p2_kpa"] * 1000.0 * trib_p2_m * 18.0 / 2.0
        floor_l_col = cfg["loads"]["live"]["p2_residential_kpa"] * 1000.0 * trib_p2_m * 18.0 / 2.0
        for node_key in ("p2_low", "p2_high"):
            idx = index[node_key]
            if idx is None:
                continue
            f_d[3 * idx + 1] += floor_d_col + floor_part_col
            f_l[3 * idx + 1] += floor_l_col

    col_sw = {}
    for key, col in (("top_low", col_low), ("top_high", col_high)):
        height = nodes[index[key]][1]
        col_sw[key] = col.mass_kg_m * G * height
        f_d[3 * index[key] + 1] += col_sw[key]

    h_low = wall_h * cfg["geometry"]["eave_low_m"] / (cfg["geometry"]["eave_low_m"] + cfg["geometry"]["eave_high_m"])
    h_high = wall_h - h_low
    f_w[3 * index["top_low"]] += h_low
    f_w[3 * index["top_high"]] += h_high

    w_roof = cfg["loads"]["dead"]["roof_kpa"] * 1000.0 * bay_m * 18.0
    w_roof += (rafter.mass_kg_m * 18.5 * 2.0 + col_low.mass_kg_m * nodes[index["top_low"]][1] + col_high.mass_kg_m * nodes[index["top_high"]][1]) * G
    w_p2 = 0.0
    if has_p2 and trib_p2_m > 0.0:
        w_p2 = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1000.0 * trib_p2_m * 18.0
    cs = cfg["loads"]["seismic"]["cs_base_shear_hypothesis"]
    v = cs * (w_roof + w_p2)
    f_roof = v * w_roof / max(w_roof + w_p2, 1.0)
    f_p2 = v - f_roof
    f_e[3 * index["top_low"]] += f_roof / 2.0
    f_e[3 * index["top_high"]] += f_roof / 2.0
    if has_p2:
        f_e[3 * index["p2_low"]] += f_p2 / 2.0
        f_e[3 * index["p2_high"]] += f_p2 / 2.0

    return {"D": f_d, "L": f_l, "W": f_w, "E": f_e}


def _clear_member_udl(frame: Frame2D, members: list, wd: float, wl: float, wu: float) -> None:
    for m in members:
        m.w_y_n_m = 0.0
        m.w_x_n_m = 0.0
    _ = (frame, wd, wl, wu)


def combine(factors: dict, cases: dict[str, np.ndarray]) -> np.ndarray:
    out = np.zeros_like(cases["D"])
    for key, factor in factors.items():
        if key in cases and factor != 0.0:
            out += factor * cases[key]
    return out


def size_portal_frame(
    cfg: dict,
    steel: Steel,
    bay_m: float,
    trib_p2_m: float,
    has_p2: bool,
    phi_b: float,
    phi_c: float,
) -> FrameResults:
    eave_low = cfg["geometry"]["eave_low_m"]
    eave_high = cfg["geometry"]["eave_high_m"]
    p2_level = cfg["geometry"]["p2_floor_level_m"]
    criteria = cfg["criteria"]

    col_low = profile("HEA300")
    col_high = profile("HEA300")
    rafter = profile("IPE450")

    for _iteration in range(3):
        frame, index = build_frame_model(
            steel, eave_low, eave_high, p2_level, has_p2, col_low, rafter,
            0.0, 0.0, 0.0,
        )
        cases = build_load_cases(frame, index, cfg, bay_m, trib_p2_m, has_p2, col_low, col_high, rafter)
        combos = cfg["combinations"]
        envelope_m: dict[int, float] = {}
        envelope_n: dict[int, float] = {}
        for combo in combos:
            f = combine(combo["factors"], cases)
            d, _k = frame.solve(f)
            for m in frame.members:
                fl = frame.member_end_forces(m, d)
                env_m = max_moment_in_member(frame, m, fl)
                env_n = max_axial_in_member(fl)
                envelope_m[id(m)] = max(envelope_m.get(id(m), 0.0), env_m)
                envelope_n[id(m)] = max(envelope_n.get(id(m), 0.0), env_n)

        col_members = [m for m in frame.members if m.i in (0, 1, 3, 4) or m.j in (1, 4)]
        col_peak_m = max(envelope_m.get(id(m), 0.0) for m in col_members) / 1e3
        col_peak_n = max(envelope_n.get(id(m), 0.0) for m in col_members) / 1e3
        rafter_members = [m for m in frame.members if m not in col_members]
        rafter_peak_m = max(envelope_m.get(id(m), 0.0) for m in rafter_members) / 1e3
        rafter_peak_n = max(envelope_n.get(id(m), 0.0) for m in rafter_members) / 1e3

        rafter_len = np.hypot(18.0, eave_high - eave_low)
        q_roof_service = (cfg["loads"]["dead"]["roof_kpa"] + cfg["loads"]["live"]["roof_kpa"]) * bay_m * 1e3
        defl_limit = rafter_len * 1000.0 / 180.0
        rafter, _ = lightest_member(steel.fy_pa, phi_b, phi_c, rafter_peak_m, rafter_peak_n, rafter_len, "IPE", defl_limit, q_roof_service)
        col_len = max(eave_low, eave_high)
        col, _ = lightest_member(steel.fy_pa, phi_b, phi_c, col_peak_m, col_peak_n, col_len, "HEA", None, None)
        col_low = col
        col_high = col

        frame, index = build_frame_model(steel, eave_low, eave_high, p2_level, has_p2, col, rafter, 0.0, 0.0, 0.0)
        cases = build_load_cases(frame, index, cfg, bay_m, trib_p2_m, has_p2, col, col, rafter)
        f = combine({"D": 1.0, "L": 1.0}, cases)
        d, _k = frame.solve(f)
        rafter_members = [m for m in frame.members if m.i == index["top_low"] or m.j == index["top_high"]]
        rafter_defl = max(deflection_at_midspan(frame, m, frame.member_end_forces(m, d)) for m in rafter_members)

        f_sw = combine({"D": 1.0, "W": 1.0}, cases)
        d_sw, _k = frame.solve(f_sw)
        drift = max(abs(d[3 * index["top_low"]]), abs(d[3 * index["top_high"]]))
        drift_limit = col_len / 200.0
        if drift > drift_limit and col.name not in ("HEA500",):
            col = profile(_next_hea(col.name))
            col_low = col
            col_high = col
            continue
        break

    frame, index = build_frame_model(steel, eave_low, eave_high, p2_level, has_p2, col, rafter, 0.0, 0.0, 0.0)
    cases = build_load_cases(frame, index, cfg, bay_m, trib_p2_m, has_p2, col, col, rafter)
    max_util = 0.0
    col_peak_m = col_peak_n = rafter_peak_m = 0.0
    for combo in combos:
        f = combine(combo["factors"], cases)
        d, _k = frame.solve(f)
        for m in frame.members:
            fl = frame.member_end_forces(m, d)
            mm = max_moment_in_member(frame, m, fl) / 1e3
            nn = max_axial_in_member(fl) / 1e3
            if m in col_members_ident(frame):
                col_peak_m = max(col_peak_m, mm)
                col_peak_n = max(col_peak_n, nn)
            else:
                rafter_peak_m = max(rafter_peak_m, mm)
                rafter_peak_n = max(rafter_peak_n, nn)
            mcap = (col if m in col_members_ident(frame) else rafter).moment_capacity_knm(steel.fy_pa, phi_b)
            acap = (col if m in col_members_ident(frame) else rafter).axial_capacity_kn(steel.fy_pa, phi_c)
            util = nn / max(acap, 1e-9) + mm / max(mcap, 1e-9)
            max_util = max(max_util, util)

    weight = (2.0 * col.mass_kg_m * col_len + rafter.mass_kg_m * rafter_len) * (1.0 + cfg["criteria"]["detail_factor_principales"])
    f_sw = combine({"D": 1.0, "W": 1.0}, cases)
    d_sw, _k = frame.solve(f_sw)
    drift = max(abs(d_sw[3 * index["top_low"]]), abs(d_sw[3 * index["top_high"]]))
    rafter_members = [m for m in frame.members if m.i == index["top_low"] or m.j == index["top_high"]]
    f_sv = combine({"D": 1.0, "L": 1.0}, cases)
    d_sv, _k = frame.solve(f_sv)
    rafter_defl = max(deflection_at_midspan(frame, m, frame.member_end_forces(m, d_sv)) for m in rafter_members)

    return FrameResults(
        column_low=col,
        column_high=col,
        rafter=rafter,
        column_axial_kn=col_peak_n,
        column_moment_knm=col_peak_m,
        rafter_moment_knm=rafter_peak_m,
        rafter_deflection_m=rafter_defl,
        drift_m=drift,
        rafter_utilization=max_util,
        column_utilization=max_util,
        weight_kg=weight,
    )


def col_members_ident(frame: Frame2D) -> list:
    return [m for m in frame.members if m.i in (0, 1, 3, 4) or m.j in (1, 4)]


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
    q_peak = max(
        roof_d + roof_l,
        1.2 * roof_d + 1.6 * roof_l,
    )
    span = 18.0
    depth = span / cfg["systems"][1]["truss_depth_span_ratio"]
    m_peak = simply_supported_max_moment(q_peak, span)
    chord_force_kn = m_peak / depth / 1e3
    panel = 1.5
    chord, _ = lightest_member(steel.fy_pa, phi_b, phi_c, 0.0, chord_force_kn, panel, "IPE", None, None)
    chord = max(chord, key=lambda p: p.mass_kg_m) if chord is None else chord
    if chord.mass_kg_m < profile("IPE220").mass_kg_m:
        chord = profile("IPE220")
    chord_mass = chord.mass_kg_m
    web_ratio = 0.5
    truss_mass_per_m = (2.0 * chord_mass) * (1.0 + web_ratio)
    truss_mass_kg = truss_mass_per_m * span
    q_service = roof_d + roof_l
    ei = steel.e_pa * 2.0 * chord.area_m2 * (depth / 2.0) ** 2
    defl = simply_supported_deflection(q_service, span, ei)
    return chord, truss_mass_kg, defl


def size_joists_and_beams(
    cfg: dict,
    steel: Steel,
    bay_m: float,
    trib_p2_m: float,
    phi_b: float,
    phi_c: float,
) -> dict:
    crit = cfg["criteria"]
    floor_d = (cfg["loads"]["dead"]["floor_p2_kpa"] + cfg["loads"]["dead"]["partitions_p2_kpa"]) * 1e3
    floor_l = cfg["loads"]["live"]["p2_residential_kpa"] * 1e3
    spacing = crit["joist_spacing_m"]
    span = bay_m
    q_joist = (floor_d + floor_l) * spacing
    defl_limit = span * 1000.0 / 240.0
    joist, _ = lightest_member(steel.fy_pa, phi_b, phi_c, simply_supported_max_moment(q_joist, span) / 1e3, 0.0, span, "IPE", defl_limit, q_joist)
    if joist.mass_kg_m < profile("IPE220").mass_kg_m:
        joist = profile("IPE220")

    q_beam = (floor_d + floor_l) * trib_p2_m
    m_beam = simply_supported_max_moment(q_beam, 18.0)
    defl_limit_beam = 18.0 * 1000.0 / 240.0
    beam, _ = lightest_member(steel.fy_pa, phi_b, phi_c, m_beam / 1e3, 0.0, 18.0, "IPE", defl_limit_beam, q_beam)

    q_edge = (floor_d + floor_l) * bay_m / 2.0
    m_edge = simply_supported_max_moment(q_edge, 9.0)
    edge, _ = lightest_member(steel.fy_pa, phi_b, phi_c, m_edge / 1e3, 0.0, 9.0, "IPE", 9.0 * 1000.0 / 240.0, q_edge)

    aux_col = profile("HEA200")
    return {"joist": joist, "beam": beam, "edge": edge, "aux_col": aux_col}

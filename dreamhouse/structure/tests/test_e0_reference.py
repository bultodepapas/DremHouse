"""Pruebas de referencia del modelo E0 (unittest).

Verifica el motor de análisis contra soluciones analíticas clásicas y saneza
las cuantificaciones del modelo estructural.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from dreamhouse.structure.analysis import (
    Frame2D,
    FrameAnalysisError,
    FrameMember,
    G,
    max_axial_in_member,
    max_moment_in_member,
    overhanging_uniform_beam_response,
    simply_supported_beam_response,
    simply_supported_deflection,
    simply_supported_max_moment,
)
from dreamhouse.structure.checks import max_factored_gravity, span_deflection_limit
from dreamhouse.structure.materials import materials_from_json
from dreamhouse.structure.portal import apply_combo, build_frame_model, build_point_loads, size_portal_frame
from dreamhouse.structure.profiles import ProfileSelectionError, lightest_member, profile
from dreamhouse.structure.quantities import compute_quantities
from dreamhouse.structure.staggered import size_p2_great_wall, size_staggered_floor

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "dreamhouse" / "structure" / "structure_system.json"
E = 2.0e11


def build_simple_beam(span: float, w_n_m: float, iy_m4: float, area_m2: float) -> tuple[Frame2D, FrameMember]:
    frame = Frame2D(
        nodes=[(0.0, 0.0), (span, 0.0)],
        members=[FrameMember(0, 1, E, area_m2, iy_m4, w_y_n_m=w_n_m)],
        fixes={0: {"ux", "uz"}, 1: {"ux", "uz"}},
    )
    return frame, frame.members[0]


class TestAnalysisReference(unittest.TestCase):
    def test_simply_supported_beam_moment_and_reaction(self):
        span = 6.0
        w = 5.0e3
        iy = profile("IPE300").iy_m4
        area = profile("IPE300").area_m2
        frame, member = build_simple_beam(span, w, iy, area)
        f = frame.equivalent_nodal_loads()
        d, _ = frame.solve(f)
        fl = frame.member_end_forces(member, d)
        v1, v2 = fl[1], fl[4]
        self.assertAlmostEqual(v1, w * span / 2.0, delta=w * span / 2.0 * 0.02)
        self.assertAlmostEqual(v2, w * span / 2.0, delta=w * span / 2.0 * 0.02)
        m_expected = simply_supported_max_moment(w, span)
        m_actual = max_moment_in_member(frame, member, fl)
        self.assertAlmostEqual(m_actual / m_expected, 1.0, delta=0.03)

    def test_simply_supported_beam_deflection(self):
        span = 6.0
        w = 5.0e3
        iy = profile("IPE300").iy_m4
        area = profile("IPE300").area_m2
        frame = Frame2D(
            nodes=[(0.0, 0.0), (span / 2.0, 0.0), (span, 0.0)],
            members=[
                FrameMember(0, 1, E, area, iy, w_y_n_m=w),
                FrameMember(1, 2, E, area, iy, w_y_n_m=w),
            ],
            fixes={0: {"ux", "uz"}, 2: {"ux", "uz"}},
        )
        f = frame.equivalent_nodal_loads()
        d, _ = frame.solve(f)
        expected = simply_supported_deflection(w, span, E * iy)
        mid = abs(d[3 * 1 + 1])
        self.assertAlmostEqual(mid, expected, delta=expected * 0.05)

    def test_simply_supported_beam_uplift_moment(self):
        """La succión uniforme debe producir el mismo |M|max que gravedad."""
        span = 6.0
        uplift = -5.0e3
        frame, member = build_simple_beam(
            span, uplift, profile("IPE300").iy_m4, profile("IPE300").area_m2
        )
        d, _ = frame.solve(frame.equivalent_nodal_loads())
        fl = frame.member_end_forces(member, d)
        actual = max_moment_in_member(frame, member, fl)
        expected = simply_supported_max_moment(abs(uplift), span)
        self.assertAlmostEqual(actual / expected, 1.0, delta=0.03)

    def test_cantilever_tip_deflection(self):
        length = 3.0
        p = 10.0e3
        iy = profile("HEA200").iy_m4
        area = profile("HEA200").area_m2
        frame = Frame2D(
            nodes=[(0.0, 0.0), (length, 0.0)],
            members=[FrameMember(0, 1, E, area, iy)],
            fixes={0: {"ux", "uz", "ry"}},
        )
        f = np.zeros(6)
        f[3 * 1 + 1] = -p
        d, _ = frame.solve(f)
        delta_expected = p * length**3 / (3.0 * E * iy)
        self.assertAlmostEqual(abs(d[3 * 1 + 1]), delta_expected, delta=delta_expected * 0.01)

    def test_cantilever_base_reaction(self):
        length = 3.0
        p = 10.0e3
        iy = profile("HEA200").iy_m4
        area = profile("HEA200").area_m2
        frame = Frame2D(
            nodes=[(0.0, 0.0), (length, 0.0)],
            members=[FrameMember(0, 1, E, area, iy)],
            fixes={0: {"ux", "uz", "ry"}},
        )
        f = np.zeros(6)
        f[3 * 1 + 1] = -p
        d, k = frame.solve(f)
        reactions = k @ d - f
        self.assertAlmostEqual(abs(reactions[3 * 0 + 1]), p, delta=p * 0.02)

    def test_point_load_beam_response_matches_closed_form(self):
        span = 8.0
        load = 120.0e3
        ei = E * profile("IPE400").iy_m4
        response = simply_supported_beam_response(
            span, [(span / 2.0, load)], ei_n_m2=ei
        )
        self.assertAlmostEqual(response.reaction_left_n, load / 2.0)
        self.assertAlmostEqual(response.reaction_right_n, load / 2.0)
        self.assertAlmostEqual(response.max_abs_moment_nm, load * span / 4.0, delta=1.0)
        self.assertAlmostEqual(
            response.max_abs_deflection_m,
            load * span**3 / (48.0 * ei),
            delta=load * span**3 / (48.0 * ei) * 0.002,
        )

    def test_overhang_response_matches_equilibrium_and_frame_model(self):
        support_span = 10.5
        overhang = 4.5
        total = support_span + overhang
        w = 18.0e3
        section = profile("IPE400")
        response = overhanging_uniform_beam_response(
            support_span, overhang, w, E * section.iy_m4
        )
        expected_wall = w * total**2 / (2.0 * support_span)
        self.assertAlmostEqual(response.reaction_support_n, expected_wall, delta=1.0)
        self.assertAlmostEqual(
            response.reaction_left_n + response.reaction_support_n,
            w * total,
            delta=1.0,
        )
        self.assertAlmostEqual(
            response.support_moment_nm,
            -w * overhang**2 / 2.0,
            delta=1.0,
        )

        step = 0.5
        nodes = [(i * step, 0.0) for i in range(int(total / step) + 1)]
        members = [
            FrameMember(i, i + 1, E, section.area_m2, section.iy_m4, w_y_n_m=w)
            for i in range(len(nodes) - 1)
        ]
        support_node = int(support_span / step)
        frame = Frame2D(
            nodes=nodes,
            members=members,
            fixes={0: {"ux", "uz"}, support_node: {"uz"}},
        )
        d, _ = frame.solve(frame.equivalent_nodal_loads())
        frame_main = max(abs(d[3 * i + 1]) for i in range(support_node + 1))
        frame_overhang = max(abs(d[3 * i + 1]) for i in range(support_node, len(nodes)))
        self.assertAlmostEqual(
            response.max_main_span_deflection_m, frame_main, delta=max(frame_main * 0.01, 1e-6)
        )
        self.assertAlmostEqual(
            response.max_overhang_deflection_m, frame_overhang, delta=max(frame_overhang * 0.01, 1e-6)
        )

    def test_invalid_or_unstable_frame_fails_clearly(self):
        section = profile("IPE300")
        degenerate = Frame2D(
            nodes=[(0.0, 0.0)],
            members=[FrameMember(0, 0, E, section.area_m2, section.iy_m4)],
            fixes={0: {"ux"}},
        )
        with self.assertRaises(FrameAnalysisError):
            degenerate.solve(np.zeros(3))

        unstable = Frame2D(
            nodes=[(0.0, 0.0), (3.0, 0.0)],
            members=[FrameMember(0, 1, E, section.area_m2, section.iy_m4)],
        )
        with self.assertRaises(FrameAnalysisError):
            unstable.solve(np.zeros(6))
        with self.assertRaises(FrameAnalysisError):
            build_simple_beam(3.0, 1.0e3, section.iy_m4, section.area_m2)[0].solve(np.zeros(5))


class TestLoadsNoSnow(unittest.TestCase):
    def test_no_snow_in_combinations(self):
        cfg = json.loads(DATA.read_text(encoding="utf-8"))
        for combo in cfg["combinations"]:
            self.assertNotIn("S", combo["factors"])
        self.assertIn("note_no_snow", cfg["loads"])
        self.assertIn("Boyac", cfg["loads"]["note_no_snow"])

    def test_geometry_dcv(self):
        cfg = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertEqual(cfg["geometry"]["nave_length_m"], 36.0)
        self.assertEqual(cfg["geometry"]["nave_width_m"], 18.0)
        self.assertEqual(cfg["geometry"]["p2_start_x_m"], 21.0)


class TestQuantities(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads(DATA.read_text(encoding="utf-8"))
        self.steel = materials_from_json(self.cfg)["S355"]

    def test_m60_portico_within_plausible_range(self):
        q = compute_quantities(self.cfg, self.steel, 6.0, 6, 0.9, 0.9)
        portico = q["systems"]["PORTICO"]
        self.assertGreater(portico["total_t"], 30.0)
        self.assertLess(portico["total_t"], 70.0)
        self.assertGreater(portico["p2_floor_kg"] / 1000.0, 8.0)
        self.assertLess(portico["p2_floor_kg"] / 1000.0, 20.0)

    def test_cercha_lighter_than_portico(self):
        q = compute_quantities(self.cfg, self.steel, 6.0, 6, 0.9, 0.9)
        self.assertLess(q["systems"]["CERCHA"]["total_t"], q["systems"]["PORTICO"]["total_t"])

    def test_more_frames_heavier_than_fewer(self):
        q45 = compute_quantities(self.cfg, self.steel, 4.5, 8, 0.9, 0.9)
        q90 = compute_quantities(self.cfg, self.steel, 9.0, 4, 0.9, 0.9)
        self.assertGreater(q45["systems"]["PORTICO"]["main_frames_kg"], q90["systems"]["PORTICO"]["main_frames_kg"])

    def test_reported_girt_length_matches_quantity_basis(self):
        q = compute_quantities(self.cfg, self.steel, 6.0, 6, 0.9, 0.9)
        result = q["systems"]["PORTICO"]
        average_eave = (
            self.cfg["geometry"]["eave_low_m"] + self.cfg["geometry"]["eave_high_m"]
        ) / 2.0
        lines = int(np.ceil(average_eave / self.cfg["criteria"]["girt_spacing_m"]))
        gross = lines * 2.0 * (
            self.cfg["geometry"]["nave_length_m"] + self.cfg["geometry"]["nave_width_m"]
        )
        self.assertAlmostEqual(result["girts_gross_m"], gross, delta=1.0)
        self.assertAlmostEqual(
            result["girts_m"], gross * result["girt_opening_factor"], delta=1.0
        )


class TestStaggeredFloor(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads(DATA.read_text(encoding="utf-8"))
        self.steel = materials_from_json(self.cfg)["S355"]

    def test_no_interior_columns(self):
        res = size_staggered_floor(self.cfg, self.steel, 6.0, 0.9, 0.9)
        self.assertEqual(res["interior_columns"], 0)

    def test_plausible_mass(self):
        for bay, n in ((4.5, 8), (6.0, 6), (9.0, 4)):
            res = size_staggered_floor(self.cfg, self.steel, bay, 0.9, 0.9)
            self.assertGreater(res["total_kg"], 1500.0)
            self.assertLess(res["total_kg"], 15000.0)
            self.assertGreater(res["n_trusses"], 1)

    def test_panel_count_includes_both_boundary_trusses(self):
        res = size_staggered_floor(self.cfg, self.steel, 6.0, 0.9, 0.9)
        self.assertEqual(res["n_trusses"], res["n_panels"] + 1)
        self.assertEqual(res["support_x_m"][0], self.cfg["geometry"]["p2_start_x_m"])
        self.assertEqual(
            res["support_x_m"][-1],
            self.cfg["geometry"]["p2_start_x_m"] + self.cfg["geometry"]["p2_length_m"],
        )

    def test_full_story_truss_depth(self):
        res = size_staggered_floor(self.cfg, self.steel, 6.0, 0.9, 0.9)
        self.assertEqual(res["truss_depth_m"], self.cfg["geometry"]["p2_headroom_m"])
        self.assertGreaterEqual(res["truss_d_over_l"], 0.10)
        self.assertLessEqual(res["truss_d_over_l"], 0.25)

    def test_panel_frequency_fails_closed_without_deck(self):
        for bay, n in ((4.5, 8), (6.0, 6), (9.0, 4)):
            res = size_staggered_floor(self.cfg, self.steel, bay, 0.9, 0.9)
            self.assertIsNone(res["panel_frequency_hz"])
            self.assertIn("not_analyzed", res["panel_verification_status"])
            self.assertIsNone(res["joist"])
            self.assertEqual(res["joists_kg"], 0.0)


class TestTiedAndFixedPortal(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads(DATA.read_text(encoding="utf-8"))
        self.steel = materials_from_json(self.cfg)["S355"]

    def test_tie_member_present_and_in_tension(self):
        col = profile("HEA300")
        rafter = profile("IPE450")
        frame, index = build_frame_model(
            self.steel, 7.2, 7.8, 3.8, True, col, rafter, 6.0, self.cfg,
            tie=True, tie_area_m2=1.0e-3,
        )
        self.assertIsNotNone(index["tie_member"])
        n = 3 * len(frame.nodes)
        f_pt = {c: np.zeros(n) for c in ("D", "L", "W", "E")}
        f = apply_combo(frame, {"D": 1.2, "L": 1.6}, f_pt)
        d, _ = frame.solve(f)
        fl = frame.member_end_forces(index["tie_member"], d)
        tie_axial = max_axial_in_member(fl)
        self.assertGreater(tie_axial, 0.0)

    def test_tied_portal_heavier_than_pinned(self):
        pinned = size_portal_frame(self.cfg, self.steel, 6.0, 6.0, True, 0.9, 0.9)
        tied = size_portal_frame(self.cfg, self.steel, 6.0, 6.0, True, 0.9, 0.9, tie=True)
        self.assertGreater(tied.weight_kg, pinned.weight_kg)
        self.assertGreater(tied.tie_area_cm2, 0.0)

    def test_fixed_base_reduces_drift_and_column(self):
        pinned = size_portal_frame(self.cfg, self.steel, 6.0, 6.0, True, 0.9, 0.9)
        fixed = size_portal_frame(self.cfg, self.steel, 6.0, 6.0, True, 0.9, 0.9, fixed_base=True)
        self.assertLess(fixed.drift_m, pinned.drift_m)
        self.assertLess(fixed.column.mass_kg_m, pinned.column.mass_kg_m)


class TestGreatWallFloor(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads(DATA.read_text(encoding="utf-8"))
        self.steel = materials_from_json(self.cfg)["S355"]

    def test_no_interior_columns_and_plausible_mass(self):
        res = size_p2_great_wall(self.cfg, self.steel, 0.9, 0.9)
        self.assertEqual(res["interior_columns"], 0)
        self.assertGreater(res["total_kg"], 4000.0)
        self.assertLess(res["total_kg"], 12000.0)

    def test_wall_and_beams(self):
        res = size_p2_great_wall(self.cfg, self.steel, 0.9, 0.9)
        self.assertEqual(res["wall_x_m"], 31.5)
        self.assertGreaterEqual(res["n_beams"], 2)
        self.assertGreater(res["wall_axial_kn_m"], 30.0)
        self.assertLess(res["wall_axial_kn_m"], 500.0)
        self.assertIsNone(res["panel_frequency_hz"])
        self.assertGreater(res["hidden_frame_kg"], 0.0)
        self.assertEqual(len(res["hidden_column_y_m"]), 6)
        self.assertEqual(res["n_beams"], 6)
        self.assertEqual(res["beam_profile"], "IPE400")
        self.assertGreater(res["rear_beams_kg"], 0.0)
        self.assertEqual(res["rear_beam_profile"], res["beam_profile"])
        self.assertEqual(res["rear_support_assumption"], "none_free_overhang_from_great_wall")
        self.assertEqual(res["beam_total_length_m"], 15.0)
        self.assertGreater(res["wall_point_reaction_kn"], 200.0)
        self.assertEqual(len(res["wall_point_reactions_kn"]), res["n_beams"])
        self.assertGreater(res["edge_columns_kg"], 0.0)
        self.assertEqual(res["edge_columns_profile"], "HEA200")
        self.assertAlmostEqual(
            res["edge_kg"], res["edge_truss_kg"] + res["edge_columns_kg"], delta=1.0
        )
        self.assertAlmostEqual(res["trial_floor_zone_m"], 0.55, places=2)
        self.assertGreaterEqual(res["floor_zone_margin_m"], 0.10)
        self.assertIn("active_gravity", res["approval_status"])
        self.assertIn("does_not_stabilize_longitudinal_x", res["lateral_role"])

    def test_lighter_than_metaldeck(self):
        res = size_p2_great_wall(self.cfg, self.steel, 0.9, 0.9)
        from dreamhouse.structure.quantities import compute_quantities
        q = compute_quantities(self.cfg, self.steel, 6.0, 6, 0.9, 0.9)["systems"]["CERCHA"]
        self.assertLess(res["total_kg"], q["p2_floor_metaldeck_kg"])


class TestLoadDirection(unittest.TestCase):
    """Sanidad física: gravedad hacia abajo, columnas en compresión, tirante en
    tensión y proyección vertical de cargas sobre miembros inclinados."""

    def setUp(self):
        self.cfg = json.loads(DATA.read_text(encoding="utf-8"))
        self.steel = materials_from_json(self.cfg)["S355"]

    def _frame_d(self):
        col = profile("HEA300")
        rafter = profile("IPE450")
        frame, index = build_frame_model(self.steel, 7.2, 7.8, 3.8, True, col, rafter, 6.0, self.cfg)
        f_pt = build_point_loads(frame, index, self.cfg, 6.0, 6.0, True, col, rafter)
        f = apply_combo(frame, {"D": 1.0}, f_pt)
        d, _ = frame.solve(f)
        return frame, index, d, f_pt

    def test_roof_deflects_down_under_dead(self):
        frame, index, d, _ = self._frame_d()
        for key in ("top_low", "roof_mid", "top_high"):
            self.assertLess(d[3 * index[key] + 1], 0.0, f"{key} debe hundirse bajo gravedad")

    def test_columns_in_compression_under_dead(self):
        frame, index, d, _ = self._frame_d()
        for m in frame.members:
            fl = frame.member_end_forces(m, d)
            if m.i in (index["base_low"], index["base_high"]):
                self.assertGreater(fl[0], 0.0, "convención del motor: axial positivo = compresión")

    def test_tie_is_nearly_inactive_two_force_member(self):
        col = profile("HEA300")
        rafter = profile("IPE450")
        frame, index = build_frame_model(self.steel, 7.2, 7.8, 3.8, True, col, rafter, 6.0, self.cfg,
                                         tie=True, tie_area_m2=1.0e-3)
        n = 3 * len(frame.nodes)
        f_pt = {c: np.zeros(n) for c in ("D", "L", "W", "E")}
        f = apply_combo(frame, {"D": 1.0, "L": 1.0}, f_pt)
        d, _ = frame.solve(f)
        fl = frame.member_end_forces(index["tie_member"], d)
        self.assertAlmostEqual(fl[0] + fl[3], 0.0, delta=1.0, msg="miembro de dos fuerzas en equilibrio")
        self.assertLess(abs(fl[0]), 30.0e3, "el faldón 1:30 casi plano no excita el tirante (hallazgo 3)")

    def test_rafter_loads_are_purely_vertical(self):
        col = profile("HEA300")
        rafter = profile("IPE450")
        frame, _index = build_frame_model(self.steel, 7.2, 7.8, 3.8, True, col, rafter, 6.0, self.cfg)
        f = apply_combo(frame, {"D": 1.0, "L": 1.0}, {})
        horiz = sum(f[3 * i] for i in range(len(frame.nodes)))
        vert = sum(f[3 * i + 1] for i in range(len(frame.nodes)))
        self.assertAlmostEqual(horiz, 0.0, delta=1.0, msg="la carga equivalente de las correas no debe tener componente horizontal")
        roof_d = self.cfg["loads"]["dead"]["roof_kpa"] * 6.0 * 1e3
        roof_l = self.cfg["loads"]["live"]["roof_kpa"] * 6.0 * 1e3
        rafter_sw = rafter.mass_kg_m * G
        expected = (roof_d + roof_l + rafter_sw) * 18.0
        self.assertAlmostEqual(-vert, expected, delta=expected * 0.01)

    def test_windward_and_leeward_coefficients_follow_direction(self):
        col = profile("HEA300")
        rafter = profile("IPE450")
        frame, index = build_frame_model(
            self.steel, 7.2, 7.8, 3.8, True, col, rafter, 6.0, self.cfg
        )
        f_pt = build_point_loads(frame, index, self.cfg, 6.0, 6.0, True, col, rafter)
        qz = self.cfg["loads"]["wind"]["qz_eave_kpa_hypothesis"] * 1e3
        cpw = self.cfg["loads"]["wind"]["Cp_wall_windward"]
        cpl = abs(self.cfg["loads"]["wind"]["Cp_wall_leeward"])
        self.assertAlmostEqual(
            f_pt["WX+"][3 * index["top_low"]], qz * cpw * 6.0 * 7.2
        )
        self.assertAlmostEqual(
            f_pt["WX+"][3 * index["top_high"]], qz * cpl * 6.0 * 7.8
        )
        self.assertAlmostEqual(
            f_pt["WX-"][3 * index["top_low"]], -qz * cpl * 6.0 * 7.2
        )
        self.assertAlmostEqual(
            f_pt["WX-"][3 * index["top_high"]], -qz * cpw * 6.0 * 7.8
        )

    def test_p2_side_column_gets_one_end_span_reaction(self):
        col = profile("HEA300")
        rafter = profile("IPE450")
        tributary = 5.0
        frame, index = build_frame_model(
            self.steel, 7.2, 7.8, 3.8, True, col, rafter, 6.0, self.cfg
        )
        f_pt = build_point_loads(
            frame, index, self.cfg, 6.0, tributary, True, col, rafter
        )
        floor_dead = (
            self.cfg["loads"]["dead"]["floor_p2_kpa"]
            + self.cfg["loads"]["dead"]["partitions_p2_kpa"]
        ) * 1e3
        expected_each_side = floor_dead * tributary * 18.0 / 6.0
        self.assertAlmostEqual(
            -f_pt["D"][3 * index["p2_low"] + 1], expected_each_side
        )
        self.assertAlmostEqual(
            -f_pt["D"][3 * index["p2_high"] + 1], expected_each_side
        )
        with self.assertRaises(ValueError):
            build_point_loads(
                frame, index, self.cfg, 6.0, tributary, True, col, rafter, p2_col_share=0.75
            )

    def test_each_basic_case_closes_global_equilibrium(self):
        col = profile("HEA300")
        rafter = profile("IPE450")
        frame, index = build_frame_model(
            self.steel, 7.2, 7.8, 3.8, True, col, rafter, 6.0, self.cfg
        )
        f_pt = build_point_loads(frame, index, self.cfg, 6.0, 5.0, True, col, rafter)
        for case in ("D", "L", "WU", "WX+", "WX-", "EX+", "EX-"):
            loads = apply_combo(frame, {case: 1.0}, f_pt)
            d, k = frame.solve(loads)
            reactions = k @ d - loads
            total = loads + reactions
            self.assertAlmostEqual(sum(total[::3]), 0.0, delta=1e-5, msg=case)
            self.assertAlmostEqual(sum(total[1::3]), 0.0, delta=1e-5, msg=case)
            moment = sum(
                x * total[3 * node + 1]
                - z * total[3 * node]
                + total[3 * node + 2]
                for node, (x, z) in enumerate(frame.nodes)
            )
            self.assertAlmostEqual(moment, 0.0, delta=1e-4, msg=case)

    def test_combinations_do_not_accumulate_previous_member_loads(self):
        col = profile("HEA300")
        rafter = profile("IPE450")
        frame, index = build_frame_model(
            self.steel, 7.2, 7.8, 3.8, True, col, rafter, 6.0, self.cfg
        )
        f_pt = build_point_loads(frame, index, self.cfg, 6.0, 5.0, True, col, rafter)
        dead_first = apply_combo(frame, {"D": 1.0}, f_pt).copy()
        apply_combo(frame, {"L": 1.0}, f_pt)
        dead_second = apply_combo(frame, {"D": 1.0}, f_pt)
        np.testing.assert_allclose(dead_first, dead_second)
        with self.assertRaises(ValueError):
            apply_combo(frame, {"TYPO": 1.0}, f_pt)


class TestDeflectionLimit(unittest.TestCase):
    def test_lightest_member_enforces_l_over_240_in_meters(self):
        fy = 355.0e6
        span = 12.0
        limit = span / 240.0
        q_service = 2.0  # kN/m
        q_factored = 1.2 * 2.0  # kN/m para resistencia
        m_req = simply_supported_max_moment(q_factored * 1e3, span) / 1e3
        cand, _ = lightest_member(fy, 0.9, 0.9, m_req, 0.0, span, "IPE", limit, q_service)
        self.assertEqual(cand.name, "IPE270")
        delta = simply_supported_deflection(q_service * 1e3, span, 2.0e11 * cand.iy_m4)
        self.assertLessEqual(delta, limit)

    def test_lightest_member_fails_when_catalog_is_exhausted(self):
        with self.assertRaises(ProfileSelectionError):
            lightest_member(355.0e6, 0.9, 0.9, 1.0e9, 0.0, 18.0, "IPE", None, None)

    def test_live_load_deflection_is_enforced(self):
        span = 8.0
        cand, _ = lightest_member(
            355.0e6,
            0.9,
            0.9,
            1.0,
            0.0,
            span,
            "IPE",
            span / 120.0,
            10.0,
            live_deflection_limit_m=span / 360.0,
            q_live_kn_m=10.0,
        )
        live_delta = simply_supported_deflection(10.0e3, span, E * cand.iy_m4)
        self.assertLessEqual(live_delta, span / 360.0)

    def test_profile_selection_rejects_negative_demands(self):
        with self.assertRaises(ValueError):
            lightest_member(355.0e6, 0.9, 0.9, -1.0, 0.0, 6.0, "IPE", None, None)


class TestConfigurationValidation(unittest.TestCase):
    def test_deflection_criterion_parser(self):
        self.assertAlmostEqual(span_deflection_limit(12.0, "L/240"), 0.05)
        self.assertAlmostEqual(span_deflection_limit(8.0, "H / 200"), 0.04)
        with self.assertRaises(ValueError):
            span_deflection_limit(8.0, "8 cm")

    def test_gravity_envelope_rejects_missing_combinations(self):
        with self.assertRaises(ValueError):
            max_factored_gravity({"combinations": []}, 1.0, 1.0)
        with self.assertRaises(ValueError):
            max_factored_gravity({"combinations": [{"factors": {"D": 1.2}}]}, -1.0, 1.0)


class TestQuantitiesSum(unittest.TestCase):
    def test_total_equals_parts(self):
        cfg = json.loads(DATA.read_text(encoding="utf-8"))
        steel = materials_from_json(cfg)["S355"]
        for mod in cfg["geometry"]["modulations"]:
            q = compute_quantities(cfg, steel, mod["bay_m"], mod["n_bays"], 0.9, 0.9)
            for sid, s in q["systems"].items():
                self.assertAlmostEqual(
                    s["total_kg"],
                    s["main_frames_kg"] + s["p2_floor_kg"] + s["secondary_kg"],
                    delta=1.0,
                    msg=f"{mod['id']}-{sid}: el total debe ser la suma de las partes",
                )


class TestHssCatalog(unittest.TestCase):
    def test_hss_profiles_available(self):
        for name in ("HSS100x100x6", "HSS120x120x6", "HSS150x150x8"):
            p = profile(name)
            self.assertGreater(p.area_m2, 0.0)
            self.assertGreater(p.mass_kg_m, 0.0)


if __name__ == "__main__":
    unittest.main()

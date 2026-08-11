"""Pruebas de referencia del modelo E0 (unittest).

Verifica el motor de análisis contra soluciones analíticas clásicas y saneza
las cuantificaciones del modelo estructural.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import numpy as np

from dreamhouse.structure.analysis import Frame2D, FrameMember, G, max_axial_in_member, max_moment_in_member, simply_supported_deflection, simply_supported_max_moment
from dreamhouse.structure.materials import materials_from_json
from dreamhouse.structure.portal import apply_combo, build_frame_model, size_portal_frame
from dreamhouse.structure.profiles import profile
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

    def test_full_story_truss_depth(self):
        res = size_staggered_floor(self.cfg, self.steel, 6.0, 0.9, 0.9)
        self.assertEqual(res["truss_depth_m"], self.cfg["geometry"]["p2_headroom_m"])
        self.assertGreaterEqual(res["truss_d_over_l"], 0.10)
        self.assertLessEqual(res["truss_d_over_l"], 0.25)

    def test_panel_frequency_above_5hz(self):
        for bay, n in ((4.5, 8), (6.0, 6), (9.0, 4)):
            res = size_staggered_floor(self.cfg, self.steel, bay, 0.9, 0.9)
            self.assertGreaterEqual(res["panel_frequency_hz"], 5.0)
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
        self.assertGreaterEqual(res["panel_frequency_hz"], 5.0)

    def test_lighter_than_metaldeck(self):
        res = size_p2_great_wall(self.cfg, self.steel, 0.9, 0.9)
        from dreamhouse.structure.quantities import compute_quantities
        q = compute_quantities(self.cfg, self.steel, 6.0, 6, 0.9, 0.9)["systems"]["CERCHA"]
        self.assertLess(res["total_kg"], q["p2_floor_metaldeck_kg"])


class TestHssCatalog(unittest.TestCase):
    def test_hss_profiles_available(self):
        for name in ("HSS100x100x6", "HSS120x120x6", "HSS150x150x8"):
            p = profile(name)
            self.assertGreater(p.area_m2, 0.0)
            self.assertGreater(p.mass_kg_m, 0.0)


if __name__ == "__main__":
    unittest.main()

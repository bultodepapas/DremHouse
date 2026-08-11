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
from dreamhouse.structure.portal import apply_combo, build_frame_model, build_point_loads, size_portal_frame
from dreamhouse.structure.profiles import lightest_member, profile
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

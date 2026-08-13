from __future__ import annotations

import json
import math
import unittest
from copy import deepcopy
from pathlib import Path

import numpy as np

from dreamhouse.structure.ground_structure import (
    GroundMember,
    run_study,
    solve_ground_structure,
    svg_report,
)
from dreamhouse.structure.materials import materials_from_json
from dreamhouse.structure.optimize_roof import (
    DEFAULT_MODEL,
    DEFAULT_SPACE,
    build_candidates,
    dominates,
    evaluate_candidate,
    explore,
    pareto_front,
)
from dreamhouse.structure.truss import Truss2D, TrussAnalysisError, TrussMember
from dreamhouse.structure.truss_grammar import generate_roof_truss


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestTruss2D(unittest.TestCase):
    def test_single_bar_matches_closed_form(self):
        elastic_modulus = 200.0e9
        area = 2.0e-3
        length = 3.0
        load = 120.0e3
        model = Truss2D(
            nodes=[(0.0, 0.0), (length, 0.0)],
            members=[TrussMember(0, 1, elastic_modulus, area)],
            fixes={0: {"ux", "uz"}, 1: {"uz"}},
        )
        loads = np.zeros(4)
        loads[2] = load
        result = model.solve(loads)
        self.assertAlmostEqual(result.displacements_m[2], load * length / (elastic_modulus * area))
        self.assertAlmostEqual(result.member_forces_n[0], load)
        self.assertAlmostEqual(result.reactions_n[0], -load)

    def test_symmetric_triangle_matches_joint_equilibrium(self):
        elastic_modulus = 200.0e9
        area = 4.0e-3
        load = 100.0e3
        model = Truss2D(
            nodes=[(0.0, 0.0), (4.0, 0.0), (2.0, 3.0)],
            members=[
                TrussMember(0, 1, elastic_modulus, area),
                TrussMember(0, 2, elastic_modulus, area),
                TrussMember(1, 2, elastic_modulus, area),
            ],
            fixes={0: {"ux", "uz"}, 1: {"uz"}},
        )
        loads = np.zeros(6)
        loads[5] = -load
        result = model.solve(loads)
        diagonal = -load * math.sqrt(13.0) / 6.0
        bottom = load / 3.0
        self.assertAlmostEqual(result.member_forces_n[0], bottom, places=6)
        self.assertAlmostEqual(result.member_forces_n[1], diagonal, places=6)
        self.assertAlmostEqual(result.member_forces_n[2], diagonal, places=6)
        self.assertAlmostEqual(result.reactions_n[1], load / 2.0, places=6)
        self.assertAlmostEqual(result.reactions_n[3], load / 2.0, places=6)

    def test_mechanism_fails_closed(self):
        model = Truss2D(
            nodes=[(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)],
            members=[
                TrussMember(0, 1, 200e9, 1e-3),
                TrussMember(1, 2, 200e9, 1e-3),
                TrussMember(2, 3, 200e9, 1e-3),
                TrussMember(3, 0, 200e9, 1e-3),
            ],
            fixes={0: {"ux", "uz"}, 1: {"uz"}},
        )
        with self.assertRaises(TrussAnalysisError):
            model.solve(np.zeros(8))

    def test_duplicate_member_is_rejected(self):
        model = Truss2D(
            nodes=[(0.0, 0.0), (1.0, 0.0)],
            members=[
                TrussMember(0, 1, 200e9, 1e-3),
                TrussMember(1, 0, 200e9, 1e-3),
            ],
            fixes={0: {"ux", "uz"}, 1: {"uz"}},
        )
        with self.assertRaises(TrussAnalysisError):
            model.solve(np.zeros(4))


class TestTrussGrammar(unittest.TestCase):
    def test_member_counts_are_deterministic(self):
        modified = generate_roof_truss(
            topology="WARREN_MODIFIED",
            depth_shape="CONSTANT",
            span_m=18.0,
            eave_low_m=7.2,
            eave_high_m=7.8,
            panel_count=6,
            centre_depth_m=1.5,
        )
        crossed = generate_roof_truss(
            topology="X",
            depth_shape="CONSTANT",
            span_m=18.0,
            eave_low_m=7.2,
            eave_high_m=7.8,
            panel_count=6,
            centre_depth_m=1.5,
        )
        self.assertEqual(modified.joint_count, 14)
        self.assertEqual(modified.member_count, 25)
        self.assertEqual(modified.crossing_count, 0)
        self.assertEqual(crossed.member_count, 31)
        self.assertEqual(crossed.crossing_count, 6)

    def test_variable_depth_preserves_straight_roof(self):
        layout = generate_roof_truss(
            topology="PRATT",
            depth_shape="VARIABLE",
            span_m=18.0,
            eave_low_m=7.2,
            eave_high_m=7.8,
            panel_count=8,
            centre_depth_m=1.8,
            end_depth_fraction=0.5,
        )
        top = [layout.nodes[node] for node in layout.top_nodes]
        bottom = [layout.nodes[node] for node in layout.bottom_nodes]
        for x, z in top:
            self.assertAlmostEqual(z, 7.2 + 0.6 * x / 18.0)
        self.assertAlmostEqual(top[0][1] - bottom[0][1], 0.9)
        self.assertAlmostEqual(top[len(top) // 2][1] - bottom[len(bottom) // 2][1], 1.8)

    def test_invalid_odd_panel_count_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_roof_truss(
                topology="HOWE",
                depth_shape="CONSTANT",
                span_m=18.0,
                eave_low_m=7.2,
                eave_high_m=7.8,
                panel_count=7,
                centre_depth_m=1.5,
            )


class TestRoofExplorer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_json(DEFAULT_MODEL)
        cls.space = load_json(DEFAULT_SPACE)

    def test_candidate_space_is_complete_and_stable(self):
        candidates = build_candidates(self.cfg, self.space)
        expected = 3 * 4 * 3 * 4
        self.assertEqual(len(candidates), expected)
        self.assertEqual(len({candidate.candidate_id for candidate in candidates}), expected)

    def test_candidate_evaluation_is_deterministic(self):
        candidate = build_candidates(self.cfg, self.space)[0]
        steel = materials_from_json(self.cfg)["S355"]
        first = evaluate_candidate(candidate, self.cfg, self.space, steel)
        second = evaluate_candidate(candidate, self.cfg, self.space, steel)
        self.assertEqual(first, second)
        self.assertTrue(first["screening_passed"])
        self.assertLessEqual(first["governing_ratio"], 1.0)
        self.assertLess(first["reaction_vertical_error_n"], 1e-5)
        self.assertFalse(first["ranking_eligible_for_design"])

    def test_analysis_failure_remains_strict_json(self):
        broken_cfg = deepcopy(self.cfg)
        broken_cfg["materials"]["S355"]["E_mpa"] = 0.0
        candidate = build_candidates(broken_cfg, self.space)[0]
        steel = materials_from_json(broken_cfg)["S355"]
        result = evaluate_candidate(candidate, broken_cfg, self.space, steel)
        self.assertFalse(result["screening_passed"])
        self.assertIsNone(result["governing_ratio"])
        self.assertTrue(result["failure_reasons"][0].startswith("analysis_error:"))
        json.dumps(result, allow_nan=False)

    def test_pareto_front_removes_dominated_rows(self):
        rows = [
            {"candidate_id": "a", "screening_passed": True, "mass": 1.0, "pieces": 2.0},
            {"candidate_id": "b", "screening_passed": True, "mass": 2.0, "pieces": 3.0},
            {"candidate_id": "c", "screening_passed": True, "mass": 0.5, "pieces": 5.0},
            {"candidate_id": "d", "screening_passed": False, "mass": 0.1, "pieces": 0.1},
        ]
        self.assertTrue(dominates(rows[0], rows[1], ("mass", "pieces")))
        front = pareto_front(rows, ("mass", "pieces"))
        self.assertEqual([row["candidate_id"] for row in front], ["c", "a"])

    def test_full_exploration_is_json_serializable(self):
        results = explore(self.cfg, self.space)
        encoded = json.dumps(results, allow_nan=False, sort_keys=True)
        self.assertEqual(results["candidate_count"], 144)
        self.assertGreater(results["screening_passed_count"], 0)
        self.assertGreater(results["pareto_count"], 1)
        self.assertIn("input_sha256", encoded)


class TestGroundStructure(unittest.TestCase):
    def test_triangle_lp_matches_static_member_areas(self):
        load = 100.0
        stress_mpa = 100.0
        nodes = [(0.0, 0.0), (4.0, 0.0), (2.0, 3.0)]
        members = [GroundMember(0, 1), GroundMember(0, 2), GroundMember(1, 2)]
        loads = np.zeros(6)
        loads[5] = -load
        result = solve_ground_structure(
            nodes=nodes,
            members=members,
            fixes={0: {"ux", "uz"}, 1: {"uz"}},
            load_cases_kn={"gravity": loads},
            allowable_stress_mpa=stress_mpa,
            active_area_threshold_cm2=1e-8,
        )
        expected_bottom_cm2 = (load / 3.0) / (stress_mpa * 0.1)
        expected_diagonal_cm2 = (load * math.sqrt(13.0) / 6.0) / (stress_mpa * 0.1)
        self.assertAlmostEqual(result.areas_cm2[0], expected_bottom_cm2)
        self.assertAlmostEqual(result.areas_cm2[1], expected_diagonal_cm2)
        self.assertAlmostEqual(result.areas_cm2[2], expected_diagonal_cm2)
        self.assertEqual(len(result.active_members), 3)
        self.assertLess(result.max_equilibrium_error_kn, 1e-8)

    def test_project_ground_structure_is_sparse_and_serializable(self):
        cfg = load_json(DEFAULT_MODEL)
        space = load_json(DEFAULT_SPACE)
        result = run_study(cfg, space)
        self.assertGreater(result["active_member_count"], 0)
        self.assertLess(result["active_member_count"], result["candidate_member_count"])
        self.assertLess(result["max_equilibrium_error_kn"], 1e-6)
        self.assertIn("<svg", svg_report(result))
        json.dumps(result, allow_nan=False)


if __name__ == "__main__":
    unittest.main()

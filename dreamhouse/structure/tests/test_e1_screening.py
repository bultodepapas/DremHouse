from __future__ import annotations

import copy
import json
import math
import unittest

from dreamhouse.structure.e1_screening import (
    DEFAULT_E1_SPACE,
    DEFAULT_P2,
    DEFAULT_PB,
    run_screening,
)
from dreamhouse.structure.materials import materials_from_json
from dreamhouse.structure.optimize_roof import DEFAULT_MODEL, DEFAULT_SPACE, _read_json
from dreamhouse.structure.profiles import profile
from dreamhouse.structure.steel_checks import (
    HSSGeometry,
    SteelCheckError,
    beam_column_interaction_ratio,
    hss_compression_strength,
    hss_flexural_strength,
    hss_local_slenderness,
    second_order_screen,
    trial_gusset_connection,
)
from dreamhouse.structure.systems_checks import (
    base_plate_screen,
    braced_bay_screen,
    diaphragm_screen,
    erection_lift_screen,
    fire_capacity_screen,
    fire_retention_factors,
    pad_foundation_screen,
)
from dreamhouse.structure.vertical_continuity import (
    VerticalContinuityError,
    evaluate_vertical_continuity,
)


class TestHSSMemberChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = _read_json(DEFAULT_MODEL)
        cls.steel = materials_from_json(cls.cfg)["S355"]

    def test_square_hss_has_equal_principal_axis_ratios(self):
        section = HSSGeometry.from_name("HSS100x100x6")
        section_profile = profile(section.name)
        i_strong, i_weak, z_strong, z_weak = section.principal_properties(section_profile)
        self.assertAlmostEqual(i_strong, i_weak)
        self.assertAlmostEqual(z_strong, z_weak)

    def test_invalid_hss_designation_fails_closed(self):
        with self.assertRaises(SteelCheckError):
            HSSGeometry.from_name("IPE300")

    def test_catalogue_hss_local_elements_are_screened(self):
        result = hss_local_slenderness(profile("HSS100x100x6"), self.steel)
        self.assertEqual(result.compression_class, "nonslender")
        self.assertEqual(result.flexural_class, "compact")
        self.assertLess(result.compression_ratio, 1.0)
        self.assertEqual(result.effective_area_m2, profile("HSS100x100x6").area_m2)

    def test_out_of_plane_unbraced_length_can_govern(self):
        section_profile = profile("HSS200x150x8")
        long_unbraced = hss_compression_strength(
            section_profile,
            self.steel,
            length_in_plane_m=2.0,
            length_out_of_plane_m=6.0,
        )
        short_unbraced = hss_compression_strength(
            section_profile,
            self.steel,
            length_in_plane_m=2.0,
            length_out_of_plane_m=1.5,
        )
        self.assertEqual(long_unbraced.governing_axis, "out_of_plane")
        self.assertLess(long_unbraced.phi_pn_n, short_unbraced.phi_pn_n)

    def test_compact_hss_flexure_has_positive_capacity(self):
        result = hss_flexural_strength(profile("HSS120x120x6"), self.steel)
        self.assertTrue(result.resolved)
        self.assertEqual(result.section_class, "compact")
        self.assertGreater(result.phi_mn_nm, 0.0)

    def test_h1_interaction_branches(self):
        low_axial = beam_column_interaction_ratio(10.0, 100.0, 50.0, 100.0)
        high_axial = beam_column_interaction_ratio(30.0, 100.0, 50.0, 100.0)
        self.assertAlmostEqual(low_axial, 0.55)
        self.assertAlmostEqual(high_axial, 0.3 + 8.0 / 9.0 * 0.5)

    def test_reduced_euler_second_order_magnifier(self):
        e_pa, inertia, length = 200.0e9, 1.0e-5, 3.0
        pe = math.pi**2 * 0.8 * e_pa * inertia / length**2
        result = second_order_screen(pe / 2.0, e_pa, inertia, length)
        self.assertTrue(result.stable)
        self.assertAlmostEqual(result.compression_to_euler_ratio, 0.5)
        self.assertAlmostEqual(result.moment_magnifier, 2.0)


class TestConnectionScreen(unittest.TestCase):
    def test_trial_components_can_pass_without_resolving_hss_joint(self):
        result = trial_gusset_connection(
            200.0,
            bolt_count=6,
            bolt_diameter_mm=20.0,
            hole_diameter_mm=22.0,
            bolt_fu_mpa=800.0,
            plate_thickness_mm=12.0,
            plate_width_mm=240.0,
            plate_fy_mpa=355.0,
            plate_fu_mpa=490.0,
            end_distance_mm=45.0,
            pitch_mm=70.0,
            weld_size_mm=8.0,
            weld_length_each_side_mm=220.0,
            electrode_fu_mpa=490.0,
        )
        self.assertTrue(result.trial_components_pass)
        self.assertFalse(result.hss_local_limit_states_resolved)
        self.assertFalse(result.overall_design_resolved)
        self.assertAlmostEqual(
            result.governing_trial_capacity_kn,
            min(
                result.bolt_shear_capacity_kn,
                result.plate_bearing_capacity_kn,
                result.plate_gross_yield_capacity_kn,
                result.plate_net_rupture_capacity_kn,
                result.plate_block_shear_capacity_kn,
                result.weld_capacity_kn,
            ),
        )


class TestSystemChecks(unittest.TestCase):
    def test_base_plate_compression_can_pass_while_anchors_remain_open(self):
        result = base_plate_screen(
            100.0,
            0.0,
            plate_width_mm=300.0,
            plate_length_mm=300.0,
            plate_thickness_mm=20.0,
            column_width_mm=200.0,
            column_depth_mm=190.0,
            plate_fy_mpa=355.0,
            concrete_fc_mpa=28.0,
        )
        self.assertTrue(result.compression_components_pass)
        self.assertFalse(result.anchor_tension_resolved)
        self.assertFalse(result.overall_base_plate_resolved)
        self.assertLess(result.required_plate_thickness_mm, 20.0)

    def test_braced_bay_resolves_demand_but_not_the_load_path(self):
        result = braced_bay_screen(
            160.0,
            parallel_braced_lines=2,
            active_bays_per_line=2,
            bay_width_m=6.0,
            bay_height_m=7.5,
            brace_area_m2=4.8e-4,
            brace_fy_pa=235.0e6,
        )
        expected = 40.0 / math.cos(math.atan2(7.5, 6.0))
        self.assertAlmostEqual(result.tension_brace_demand_kn, expected)
        self.assertTrue(result.trial_strength_pass)
        self.assertFalse(result.overall_lateral_path_resolved)

    def test_fire_retention_interpolates_and_does_not_claim_rating(self):
        ky, ke = fire_retention_factors(550.0)
        self.assertAlmostEqual(ky, 0.625)
        self.assertAlmostEqual(ke, 0.455)
        result = fire_capacity_screen(0.65, 550.0)
        self.assertGreater(result.conservative_strength_utilization, 1.0)
        self.assertFalse(result.trial_temperature_pass)
        self.assertFalse(result.overall_fire_design_resolved)

    def test_diaphragm_reports_demand_and_blocks_without_manufacturer(self):
        result = diaphragm_screen(180.0, 36.0, 18.0)
        self.assertAlmostEqual(result.required_unit_shear_kn_m, 10.0)
        self.assertAlmostEqual(result.required_chord_force_kn, 45.0)
        self.assertIsNone(result.strength_ratio)
        self.assertFalse(result.overall_diaphragm_resolved)

    def test_erection_lift_reports_transport_and_sling_demands(self):
        result = erection_lift_screen(
            18.0,
            1000.0,
            dynamic_factor=1.3,
            lift_point_count=2,
            sling_angle_deg_from_horizontal=60.0,
            maximum_transport_piece_length_m=12.0,
        )
        self.assertEqual(result.minimum_transport_piece_count, 2)
        self.assertTrue(result.shop_or_field_splice_required)
        self.assertAlmostEqual(result.required_hook_load_kn, 12.748645, places=6)
        self.assertAlmostEqual(
            result.sling_tension_each_kn,
            result.reaction_per_lift_point_kn / math.sin(math.radians(60.0)),
        )
        self.assertFalse(result.overall_release_from_crane_ready)

    def test_pad_foundation_concentric_bearing_and_uplift(self):
        common = {
            "width_m": 2.0,
            "length_m": 2.0,
            "thickness_m": 0.5,
            "embedment_m": 0.8,
            "allowable_bearing_kpa": 150.0,
            "base_friction_coefficient": 0.35,
        }
        gravity = pad_foundation_screen(100.0, 10.0, 0.0, **common)
        self.assertTrue(gravity.full_contact)
        self.assertAlmostEqual(gravity.net_vertical_kn, 169.6)
        self.assertAlmostEqual(gravity.maximum_bearing_kpa, 42.4)
        self.assertTrue(gravity.bearing_pass)
        self.assertTrue(gravity.sliding_pass)
        self.assertFalse(gravity.overall_foundation_resolved)

        uplift = pad_foundation_screen(-100.0, 0.0, 0.0, **common)
        self.assertFalse(uplift.uplift_pass)
        self.assertIsNone(uplift.maximum_bearing_kpa)


class TestE1Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = _read_json(DEFAULT_MODEL)
        cls.roof_space = _read_json(DEFAULT_SPACE)
        cls.e1_space = _read_json(DEFAULT_E1_SPACE)

    def test_reference_screen_is_deterministic_and_strict_json(self):
        first = run_screening(self.cfg, self.roof_space, self.e1_space)
        second = run_screening(self.cfg, self.roof_space, self.e1_space)
        self.assertEqual(first, second)
        json.dumps(first, allow_nan=False, sort_keys=True)
        self.assertEqual(first["overall_status"], "research_screening_complete_design_blocked")
        self.assertFalse(first["selection_or_construction_authority"])

    def test_local_bending_changes_the_reference_member_screen(self):
        result = run_screening(self.cfg, self.roof_space, self.e1_space)
        reference = result["reference_truss"]
        checks = result["checks"]
        self.assertEqual(reference["selected_screening_profiles"]["chord"], "HSS120x120x6")
        self.assertGreater(checks["chord_local_bending"]["maximum_local_moment_knm"], 0.0)
        self.assertGreater(
            checks["local_and_biaxial_member_stability"]["maximum_interaction_ratio"],
            checks["local_and_biaxial_member_stability"]["maximum_axial_ratio"],
        )
        self.assertFalse(checks["diaphragm"]["result"]["overall_diaphragm_resolved"])
        self.assertFalse(checks["foundation"]["design_resolved"])


class TestVerticalContinuity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = _read_json(DEFAULT_MODEL)
        cls.pb = _read_json(DEFAULT_PB)
        cls.p2 = _read_json(DEFAULT_P2)
        cls.e1_space = _read_json(DEFAULT_E1_SPACE)

    def test_only_four_stair_enclosure_corners_are_geometry_compatible(self):
        result = evaluate_vertical_continuity(
            self.cfg,
            self.pb,
            self.p2,
            self.e1_space["vertical_continuity"],
        )
        self.assertEqual(
            result["compatible_column_ids"],
            ["GW-STAIR-S", "GW-STAIR-N", "STAIR-REAR-S", "STAIR-REAR-N"],
        )
        self.assertEqual(result["existing_great_wall_columns_reused"], 2)
        self.assertEqual(result["new_rear_columns_required"], 2)
        self.assertTrue(result["geometry_screen_pass"])
        self.assertFalse(result["stair_stringers_in_primary_lateral_system"])
        self.assertFalse(result["complete_orthogonal_lateral_system_resolved"])

    def test_rejected_great_wall_lines_keep_specific_conflicts(self):
        result = evaluate_vertical_continuity(
            self.cfg,
            self.pb,
            self.p2,
            self.e1_space["vertical_continuity"],
        )
        candidates = {item["id"]: item for item in result["candidates"]}
        self.assertEqual(candidates["GW-SOUTH"]["window_conflicts"], ["W-M-LAT-A"])
        self.assertEqual(candidates["GW-Y2.4"]["interior_nonstair_spaces"], ["M-D"])
        self.assertEqual(candidates["GW-Y13.4"]["interior_nonstair_spaces"], ["G-C"])
        self.assertEqual(candidates["GW-NORTH"]["window_conflicts"], ["W-G"])

    def test_stair_alignment_change_fails_closed(self):
        shifted_p2 = copy.deepcopy(self.p2)
        stair = next(space for space in shifted_p2["spaces"] if space["id"] == "ESC")
        stair["y"] += 0.10
        with self.assertRaisesRegex(VerticalContinuityError, "not aligned"):
            evaluate_vertical_continuity(
                self.cfg,
                self.pb,
                shifted_p2,
                self.e1_space["vertical_continuity"],
            )


if __name__ == "__main__":
    unittest.main()

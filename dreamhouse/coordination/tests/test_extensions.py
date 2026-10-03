"""Current source extension calculations and explicit evidence gates."""

from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from dreamhouse.coordination.extensions import evaluate_extensions
from dreamhouse.coordination.model import resolve_project, study_template


class ExtensionCalculationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = resolve_project()
        cls.result = evaluate_extensions(cls.snapshot)

    def finding(self, rule_id, entity_ids=None, result=None):
        evaluation = result or self.result
        for item in evaluation["findings"]:
            if item["rule_id"] == rule_id and (
                entity_ids is None or item["entity_ids"] == sorted(entity_ids)
            ):
                return item
        self.fail(f"No finding for {rule_id} and entity IDs {entity_ids}")

    def resolve_study(self, changes, scenario_id="EXTENSION-TEST"):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "study.json"
            document = study_template(self.snapshot, scenario_id)
            document["changes"] = changes
            path.write_text(json.dumps(document), encoding="utf-8")
            return resolve_project(path)

    def test_wall_takeoffs_use_current_opening_unions_and_keep_mass_unknown(self):
        walls = self.result["extensions"]["wall_schedule"]
        exterior = walls["exterior"]
        self.assertTrue(exterior["quantity_valid"])
        self.assertAlmostEqual(exterior["gross_plan_line_m"], 48.0)
        self.assertAlmostEqual(exterior["opening_union_m"], 21.8)
        self.assertAlmostEqual(exterior["plan_line_without_aperture_span_m"], 26.2)
        self.assertIsNone(exterior["wall_area_m2"])
        self.assertIsNone(exterior["wall_mass_kg"])
        self.assertIn("Wall remains above and below openings", exterior["interpretation"])
        self.assertAlmostEqual(exterior["nominal_schedule_thickness_m"], 0.23)
        self.assertAlmostEqual(exterior["source_layer_nominal_sum_mm"], 229.0)
        self.assertAlmostEqual(exterior["source_note_layer_sum_mm"], 297.0)
        self.assertTrue(exterior["source_thickness_basis_conflict"])
        self.assertEqual(exterior["conflict_ids"], ["CF-014"])

        by_edge = {item["edge"]: item for item in exterior["edge_measurements"]}
        self.assertEqual(
            {edge: round(item["opening_union_m"], 2) for edge, item in by_edge.items()},
            {"south": 7.2, "north": 7.2, "east": 7.4},
        )

        hall = walls["hall_edge"]
        self.assertAlmostEqual(hall["retained_length_m"], 10.55)
        self.assertAlmostEqual(hall["open_frontage_length_m"], 7.45)
        self.assertIsNone(hall["wall_mass_kg"])

        dry = walls["same_suite_dry_boundary_candidates"]
        self.assertAlmostEqual(dry["gross_candidate_line_m"], 17.19)
        self.assertAlmostEqual(dry["opening_union_m"], 8.4)
        self.assertAlmostEqual(dry["remaining_candidate_line_m"], 8.79)
        self.assertEqual(dry["registered_wall_instances"], 0)
        self.assertTrue(
            all(not row["registered_wall_instance"] for row in dry["candidate_boundaries"])
        )
        full_opening = next(
            row for row in dry["candidate_boundaries"] if row["space_ids"] == ["M-D", "M-L"]
        )
        self.assertAlmostEqual(full_opening["remaining_plan_line_m"], 0.0)
        self.assertIsNone(full_opening["rule_compatible_family_candidate"])

    def test_exterior_takeoff_reacts_to_changed_opening_width(self):
        base_window = self.snapshot["entities"]["W-H1"]
        changed = self.resolve_study(
            {
                "W-H1": {
                    "expected": {"width_m": base_window["parameters"]["width_m"]},
                    "set": {"width_m": 3.8},
                }
            },
            "EXTENSION-WINDOW-WIDTH",
        )
        result = evaluate_extensions(changed)
        base = self.result["extensions"]["wall_schedule"]["exterior"]
        new = result["extensions"]["wall_schedule"]["exterior"]
        self.assertNotEqual(changed["model_hash"], self.snapshot["model_hash"])
        self.assertAlmostEqual(new["opening_union_m"] - base["opening_union_m"], 0.2)
        self.assertAlmostEqual(
            new["plan_line_without_aperture_span_m"] - base["plan_line_without_aperture_span_m"],
            -0.2,
        )

    def test_opening_interval_union_flags_overlap_without_double_counting_or_net_quantity(self):
        base_window = self.snapshot["entities"]["W-M-LAT-A"]
        changed = self.resolve_study(
            {
                "W-M-LAT-A": {
                    "expected": {"start_m": base_window["parameters"]["start_m"]},
                    "set": {"start_m": 25.0},
                }
            },
            "EXTENSION-WINDOW-OVERLAP",
        )
        result = evaluate_extensions(changed)
        exterior = result["extensions"]["wall_schedule"]["exterior"]
        south = next(item for item in exterior["edge_measurements"] if item["edge"] == "south")
        self.assertAlmostEqual(south["opening_overlap_m"], 0.4)
        self.assertAlmostEqual(south["opening_union_m"], 6.8)
        self.assertAlmostEqual(exterior["opening_union_m"], 21.4)
        self.assertFalse(exterior["quantity_valid"])
        self.assertIsNone(exterior["plan_line_without_aperture_span_m"])
        finding = self.finding("WALL-EXTERIOR-LINE-SCHEDULE", result=result)
        self.assertEqual((finding["status"], finding["coverage"]), ("FAIL", "evaluated"))

    def test_opening_overrun_is_clipped_for_diagnostics_and_never_yields_net_line(self):
        base_window = self.snapshot["entities"]["W-M-LAT-A"]
        changed = self.resolve_study(
            {
                "W-M-LAT-A": {
                    "expected": {"start_m": base_window["parameters"]["start_m"]},
                    "set": {"start_m": 35.0},
                }
            },
            "EXTENSION-WINDOW-OVERRUN",
        )
        exterior = evaluate_extensions(changed)["extensions"]["wall_schedule"]["exterior"]
        record = next(
            opening
            for edge in exterior["edge_measurements"]
            for opening in edge["opening_intervals_m"]
            if opening["entity_id"] == "W-M-LAT-A"
        )
        self.assertEqual(record["diagnostic_clipped_interval_m"], [35.0, 36.0])
        self.assertTrue(record["out_of_bounds"])
        self.assertFalse(exterior["quantity_valid"])
        self.assertIsNone(exterior["plan_line_without_aperture_span_m"])

    def test_bool_and_nonfinite_opening_bounds_are_unsupported_not_quantities(self):
        for value in (True, float("inf")):
            with self.subTest(value=value):
                snapshot = deepcopy(self.snapshot)
                snapshot["entities"]["W-H1"]["geometry"]["x0"] = value
                result = evaluate_extensions(snapshot)
                exterior = result["extensions"]["wall_schedule"]["exterior"]
                self.assertFalse(exterior["quantity_valid"])
                self.assertIsNone(exterior["plan_line_without_aperture_span_m"])
                finding = self.finding("WALL-EXTERIOR-LINE-SCHEDULE", result=result)
                self.assertEqual((finding["status"], finding["coverage"]), ("OPEN", "unsupported"))

    def test_missing_normalized_window_does_not_become_assumed_solid_wall(self):
        snapshot = deepcopy(self.snapshot)
        del snapshot["entities"]["W-H1"]
        result = evaluate_extensions(snapshot)
        exterior = result["extensions"]["wall_schedule"]["exterior"]
        finding = self.finding("WALL-EXTERIOR-LINE-SCHEDULE", result=result)
        self.assertFalse(exterior["quantity_valid"])
        self.assertIsNone(exterior["opening_union_m"])
        self.assertIsNone(exterior["plan_line_without_aperture_span_m"])
        self.assertEqual((finding["status"], finding["coverage"]), ("OPEN", "unsupported"))
        self.assertTrue(any("W-H1" in item for item in exterior["required_inputs_missing"]))

        unscheduled = deepcopy(self.snapshot)
        unscheduled["discipline_inputs"]["programme"]["p2"]["windows"] = [
            item
            for item in unscheduled["discipline_inputs"]["programme"]["p2"]["windows"]
            if item["id"] != "W-H1"
        ]
        incomplete = evaluate_extensions(unscheduled)["extensions"]["wall_schedule"]["exterior"]
        self.assertFalse(incomplete["quantity_valid"])
        self.assertIsNone(incomplete["plan_line_without_aperture_span_m"])
        self.assertTrue(
            any(
                "W-H1" in item and "wall schedule" in item
                for item in incomplete["required_inputs_missing"]
            )
        )

    def test_same_suite_door_move_invalidates_only_its_current_boundary_candidate(self):
        door = self.snapshot["entities"]["D-H1-C"]
        changed = self.resolve_study(
            {
                "D-H1-C": {
                    "expected": {"start_m": door["parameters"]["start_m"]},
                    "set": {"start_m": 2.1},
                }
            },
            "EXTENSION-DOOR-BOUNDARY",
        )
        result = evaluate_extensions(changed)
        finding = self.finding(
            "WALL-W01A-DRY-BOUNDARY-REMAINDER", ["D-H1-C", "H1-C", "H1-D"], result
        )
        self.assertEqual(finding["status"], "FAIL")
        self.assertIsNone(finding["evidence"]["remaining_plan_line_m"])
        self.assertIn("extends beyond", finding["evidence"]["issues"][0])

    def test_missing_same_suite_door_withholds_candidate_remainder(self):
        snapshot = deepcopy(self.snapshot)
        del snapshot["entities"]["D-H1-C"]
        result = evaluate_extensions(snapshot)
        finding = self.finding("WALL-W01A-DRY-BOUNDARY-REMAINDER", ["H1-C", "H1-D"], result)
        self.assertEqual((finding["status"], finding["coverage"]), ("OPEN", "unsupported"))
        self.assertIsNone(finding["evidence"]["remaining_plan_line_m"])

    def test_stair_door_change_invalidates_access_relationship(self):
        door = self.snapshot["entities"]["D-STAIR"]
        changed = self.resolve_study(
            {
                "D-STAIR": {
                    "expected": {"start_m": door["parameters"]["start_m"]},
                    "set": {"start_m": 8.8},
                }
            },
            "EXTENSION-STAIR-DOOR",
        )
        result = evaluate_extensions(changed)
        finding = self.finding("SC01-CROSS-LEVEL-DATUMS", result=result)
        self.assertEqual(finding["status"], "FAIL")
        self.assertFalse(
            finding["evidence"]["p2_access_opening"]["opening_matches_p2_access_reservation"]
        )

    def test_stair_relationship_keeps_arithmetic_separate_from_discharge_and_capacity(self):
        stair = self.result["extensions"]["stair_relationships"]
        cross_level = stair["cross_level"]
        self.assertAlmostEqual(cross_level["levels_m"]["PB"], 0.0)
        self.assertAlmostEqual(cross_level["levels_m"]["intermediate_landing"], 1.9)
        self.assertAlmostEqual(cross_level["levels_m"]["P2"], 3.8)
        self.assertEqual(cross_level["flight_risers"], [11, 11])
        self.assertAlmostEqual(cross_level["riser_height_mm"], 172.7272727)
        self.assertEqual(cross_level["flight_plan_run_m"], [2.7, 2.7])
        self.assertTrue(cross_level["flight_run_geometry_matches_treads"])
        self.assertTrue(cross_level["landing_plan_bounds_m"]["joins_both_flight_ends"])
        self.assertTrue(cross_level["p2_access_opening"]["opening_matches_p2_access_reservation"])
        self.assertEqual(self.finding("SC01-CROSS-LEVEL-DATUMS")["status"], "PASS")

        discharge = stair["rear_discharge"]
        self.assertAlmostEqual(discharge["level_difference_m"], 1.9)
        self.assertEqual(discharge["rear_door_geometry_shape"], "unresolved")
        self.assertFalse(discharge["discharge_resolved"])
        self.assertEqual(self.finding("SC01-REAR-DISCHARGE-RELATIONSHIP")["status"], "OPEN")
        structural = stair["structural_interfaces"]
        self.assertFalse(structural["member_sections_selected"])
        self.assertEqual(structural["engineering_status"], "not evaluated")

    def test_invalid_stair_counts_withhold_derived_datums(self):
        snapshot = deepcopy(self.snapshot)
        snapshot["discipline_inputs"]["structure"]["stair"]["stair"]["total_risers"] = True
        result = evaluate_extensions(snapshot)
        cross = result["extensions"]["stair_relationships"]["cross_level"]
        self.assertEqual(cross["calculation_state"], "unsupported")
        self.assertIsNone(cross["levels_m"])
        finding = self.finding("SC01-CROSS-LEVEL-DATUMS", result=result)
        self.assertEqual(finding["coverage"], "unsupported")

    def test_phase_totals_and_temporary_reservations_remain_distinct(self):
        phase = self.result["extensions"]["phase_reservations"]
        self.assertAlmostEqual(phase["gross_tagged_area_m2_by_phase"]["1"], 165.0)
        self.assertAlmostEqual(phase["gross_tagged_area_m2_by_phase"]["2"], 105.0)
        self.assertAlmostEqual(phase["total_tagged_plan_area_m2"], 270.0)
        self.assertTrue(phase["tagged_rectangles_cover_envelope_without_overlap"])
        closure = phase["temporary_phase_closure"]
        self.assertTrue(closure["geometry_matches_reservation"])
        self.assertTrue(closure["required_during_phase_1"])
        self.assertEqual(closure["physical_installation_state"], "unknown")
        guard = phase["family_frontage_guard_reservation"]
        self.assertAlmostEqual(guard["phase_1_length_m"], 6.0)
        self.assertAlmostEqual(guard["phase_2_length_m"], 7.45)
        self.assertEqual(guard["physical_installation_state"], "unknown")

    def test_workbench_interfaces_are_measured_and_service_routes_are_not_invented(self):
        services = self.result["extensions"]["service_interfaces"]
        operating = services["operating_reservations"]
        benches = {item["source_asset_id"]: item for item in operating["bench_reservations"]}
        self.assertAlmostEqual(benches["PB-BENCH-CAR"]["operating_strip_area_m2"], 10.8)
        self.assertAlmostEqual(benches["PB-BENCH-RC"]["operating_strip_area_m2"], 10.8)
        self.assertTrue(benches["PB-BENCH-CAR"]["bench_strip_adjacency_matches_source"])
        self.assertTrue(benches["PB-BENCH-RC"]["bench_strip_adjacency_matches_source"])
        self.assertTrue(all(item["installed_state"] == "unknown" for item in benches.values()))
        for item in operating["support_equipment_clearances"]:
            self.assertAlmostEqual(item["plan_gap_to_bench_m"], 1.27)
            self.assertAlmostEqual(item["source_stated_minimum_m"], 1.2)
            self.assertTrue(item["meets_source_stated_minimum"])

        routes = services["routes"]
        self.assertIsNone(routes["route_geometry"])
        self.assertIsNone(routes["service_point_coordinates"])
        self.assertEqual(routes["route_status"], "not supplied by captured source")
        self.assertEqual(self.finding("PB-SERVICE-ROUTE-COVERAGE")["status"], "OPEN")

    def test_clearance_change_fails_the_sourced_plan_relationship(self):
        snapshot = deepcopy(self.snapshot)
        snapshot["discipline_inputs"]["equipment"]["pb"]["rc_support_equipment"]["lipo_zone"][
            "y"
        ] = 14.2
        result = evaluate_extensions(snapshot)
        finding = self.finding("PB-SERVICE-OPERATING-RESERVATIONS", result=result)
        lipo = next(
            item
            for item in finding["evidence"]["support_equipment_clearances"]
            if item["source_asset_id"] == "lipo_zone"
        )
        self.assertAlmostEqual(lipo["plan_gap_to_bench_m"], 1.07)
        self.assertFalse(lipo["meets_source_stated_minimum"])
        self.assertEqual(finding["status"], "FAIL")

    def test_maintenance_assets_keep_reservation_and_lifecycle_states_separate(self):
        evidence = self.result["extensions"]["maintenance"]
        assets = {item["source_asset_id"]: item for item in evidence["assets"]}
        self.assertIn("RL-CAR", assets)
        self.assertIn("RL-RC", assets)
        self.assertIn("PB-BENCH-CAR", assets)
        self.assertEqual(assets["RL-CAR"]["installed_state"], "unknown")
        self.assertEqual(assets["RL-CAR"]["maintenance_intervals"], None)
        self.assertTrue(assets["RL-CAR"]["source_open_maintenance_items"])
        self.assertEqual(evidence["recorded_lifecycle_events"], [])

    def test_missing_sources_have_explicit_unsupported_coverage_and_minimal_input_is_safe(self):
        result = evaluate_extensions({})
        self.assertTrue(result["findings"])
        self.assertTrue(
            all(item["coverage"] in {"unsupported", "not_run"} for item in result["findings"])
        )
        self.assertIn(
            "WALL-EXTERIOR-LINE-SCHEDULE", {item["rule_id"] for item in result["findings"]}
        )

        snapshot = deepcopy(self.snapshot)
        snapshot["discipline_inputs"]["programme"].pop("p2")
        missing = evaluate_extensions(snapshot)
        exterior = missing["extensions"]["wall_schedule"]["exterior"]
        self.assertEqual(exterior["calculation_state"], "unsupported")
        self.assertIsNone(exterior["plan_line_without_aperture_span_m"])

    def test_evaluator_does_not_reload_repository_sources(self):
        with patch(
            "dreamhouse.coordination.model.read_json", side_effect=AssertionError("reloaded source")
        ):
            result = evaluate_extensions(self.snapshot)
        self.assertTrue(result["findings"])

    def test_every_finding_is_registered_and_only_references_normalized_entities(self):
        registry = {item["rule_id"] for item in self.result["rule_registry"]}
        normalized = set(self.snapshot["entities"])
        for finding in self.result["findings"]:
            self.assertIn(finding["rule_id"], registry)
            self.assertTrue(set(finding["entity_ids"]).issubset(normalized))
            self.assertTrue(finding["model_hash"])
            self.assertTrue(finding["input_hash"])


if __name__ == "__main__":
    unittest.main()

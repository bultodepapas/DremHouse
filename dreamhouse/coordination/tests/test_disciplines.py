from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from dreamhouse.coordination.disciplines import evaluate_disciplines
from dreamhouse.coordination.model import resolve_project, study_template
from dreamhouse.structure.vertical_continuity import (
    VerticalContinuityError,
    evaluate_current_support_line_plan,
)


class TestCurrentDisciplineAdapters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = resolve_project()
        cls.result = evaluate_disciplines(cls.snapshot)
        cls.findings = {
            (item["rule_id"], tuple(item["entity_ids"])): item for item in cls.result["findings"]
        }

    def test_programme_uses_current_d065_basis_instead_of_old_closet_target(self):
        bath = self.findings[("PROGRAM-PRIMARY-BATH-17", ("M-B", "M-B-A"))]
        closet = self.findings[("PROGRAM-PRIMARY-CLOSET-15", ("M-C",))]
        total = self.findings[("PROGRAM-PRIMARY-TOTAL-75", ("M-B", "M-B-A", "M-C", "M-D", "M-L"))]

        self.assertEqual(bath["status"], "PASS")
        self.assertEqual(bath["evidence"]["measured_area_m2"], 17.6)
        self.assertEqual(closet["status"], "OPEN")
        self.assertEqual(closet["coverage"], "inapplicable")
        self.assertEqual(closet["evidence"]["legacy_check"]["status"], "FAIL")
        self.assertEqual(closet["evidence"]["current_criterion_area_m2"], 13.44)
        self.assertTrue(closet["evidence"]["current_basis_matches_resolved_area"])
        self.assertEqual(total["status"], "OPEN")
        self.assertFalse(total["evidence"]["gross_net_basis_resolved"])
        self.assertFalse(
            any(
                item["rule_id"] == "PROGRAM-PRIMARY-CLOSET-15" and item["status"] == "FAIL"
                for item in self.result["findings"]
            )
        )

    def test_equipment_failures_remain_open_benchmark_evidence(self):
        bed = self.findings[("EQUIP-EQ-M-BED-HOST", ("M-D",))]
        clearance = self.findings[("EQUIP-PRIMARY-BED-CLEARANCE", ("M-D",))]
        lift = self.findings[("EQUIPMENT-LIFT-SELECTION-COVERAGE", ())]
        mass = self.findings[("EQUIPMENT-MASS-COVERAGE", ())]

        self.assertEqual(bed["status"], "OPEN")
        self.assertEqual(bed["coverage"], "evaluated")
        self.assertEqual(bed["evidence"]["benchmark_geometry_status"], "FAIL")
        self.assertEqual(clearance["evidence"]["benchmark_geometry_status"], "FAIL")
        self.assertEqual(lift["evidence"]["selected_lift_product"], None)
        self.assertEqual(lift["evidence"]["actual_installed_mass_kg"], None)
        self.assertEqual(mass["evidence"]["installed_mass_kg_by_equipment"], None)
        self.assertEqual(self.result["disciplines"]["equipment"]["status"], "OPEN")

    def test_workstation_sill_and_span_findings_use_snapshot_geometry(self):
        for window_id in ("GLZ-WS-A", "GLZ-WS-B"):
            finding = self.findings[("WORKSTATION-WINDOW-DATUM", (window_id,))]
            self.assertEqual(finding["status"], "PASS")
            self.assertTrue(finding["evidence"]["sill_matches_worktop"])
            self.assertTrue(finding["evidence"]["width_matches_zone"])
            self.assertTrue(finding["evidence"]["bounds_match_zone"])

    def test_structure_reports_plan_interactions_and_unknown_vertical_clearance(self):
        candidates = [
            item
            for item in self.result["findings"]
            if item["rule_id"] == "STRUCTURE-SUPPORT-LINE-PLAN-INTERACTION"
        ]
        self.assertGreater(len(candidates), 0)
        self.assertTrue(all(item["status"] == "OPEN" for item in candidates))
        self.assertTrue(all(item["coverage"] == "evaluated" for item in candidates))
        self.assertTrue(
            all(item["evidence"]["candidate_vertical_bounds_known"] is False for item in candidates)
        )
        self.assertTrue(
            all(
                match["three_dimensional_conflict"] == "not evaluated"
                for item in candidates
                for match in item["evidence"]["opening_plan_candidates"]
            )
        )
        current = self.findings[("STRUCTURE-CURRENT-SNAPSHOT-COVERAGE", ())]
        self.assertEqual(current["coverage"], "not_run")
        self.assertIsNone(current["evidence"]["structural_result_model_hash"])
        mass = self.findings[("STRUCTURE-MASS-COVERAGE", ())]
        engineering = self.findings[("STRUCTURE-ENGINEERING-COVERAGE", ())]
        self.assertIsNone(mass["evidence"]["element_mass_kg"])
        self.assertEqual(engineering["evidence"]["engineering_status"], "unknown/not evaluated")

    def test_moving_a_window_changes_plan_candidate_and_structural_fingerprint(self):
        entity_id = "W-M-LAT-A"
        base_entity = self.snapshot["entities"][entity_id]
        study = study_template(self.snapshot, "MOVE-P2-WINDOW-STUDY")
        study["changes"] = {
            entity_id: {
                "expected": {"start_m": base_entity["parameters"]["start_m"]},
                "set": {"start_m": 31.5},
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            project_path = Path(directory) / "study.json"
            project_path.write_text(json.dumps(study), encoding="utf-8")
            changed = resolve_project(project_path)
            result = evaluate_disciplines(changed)

        self.assertNotEqual(self.snapshot["model_hash"], changed["model_hash"])
        self.assertEqual(
            self.snapshot["entities"][entity_id]["parameters"]["width_m"],
            changed["entities"][entity_id]["parameters"]["width_m"],
        )
        baseline_candidate = next(
            item
            for item in self.result["findings"]
            if item["rule_id"] == "STRUCTURE-SUPPORT-LINE-PLAN-INTERACTION"
            and item["evidence"]["candidate_source_ref"].endswith("hidden_column_y_m[0]")
        )
        changed_candidate = next(
            item
            for item in result["findings"]
            if item["rule_id"] == "STRUCTURE-SUPPORT-LINE-PLAN-INTERACTION"
            and item["evidence"]["candidate_source_ref"].endswith("hidden_column_y_m[0]")
        )
        self.assertNotIn(entity_id, baseline_candidate["entity_ids"])
        self.assertIn(entity_id, changed_candidate["entity_ids"])
        self.assertIn(
            entity_id,
            [
                item["opening_id"]
                for item in changed_candidate["evidence"]["opening_plan_candidates"]
            ],
        )
        self.assertEqual(changed_candidate["status"], "OPEN")
        current = next(
            item
            for item in result["findings"]
            if item["rule_id"] == "STRUCTURE-CURRENT-SNAPSHOT-COVERAGE"
        )
        self.assertEqual(current["evidence"]["resolved_model_hash"], changed["model_hash"])
        self.assertIn(entity_id, current["evidence"]["changed_entity_ids"])

    def test_changed_workstation_datum_fails_adopted_relationship_and_stays_structurally_open(self):
        entity_id = "GLZ-WS-A"
        base_entity = self.snapshot["entities"][entity_id]
        study = study_template(self.snapshot, "CHANGE-WORKSTATION-SILL-STUDY")
        study["changes"] = {
            entity_id: {
                "expected": {"sill_m": base_entity["parameters"]["sill_m"]},
                "set": {"sill_m": 0.8},
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            project_path = Path(directory) / "study.json"
            project_path.write_text(json.dumps(study), encoding="utf-8")
            changed = resolve_project(project_path)
            result = evaluate_disciplines(changed)

        finding = next(
            item
            for item in result["findings"]
            if item["rule_id"] == "WORKSTATION-WINDOW-DATUM" and item["entity_ids"] == [entity_id]
        )
        self.assertEqual(finding["status"], "FAIL")
        self.assertFalse(finding["evidence"]["sill_matches_worktop"])
        structural = next(
            item
            for item in result["findings"]
            if item["rule_id"] == "STRUCTURE-CURRENT-SNAPSHOT-COVERAGE"
        )
        self.assertIn(entity_id, structural["evidence"]["changed_entity_ids"])
        self.assertEqual(structural["coverage"], "not_run")

    def test_moving_a_current_door_recomputes_support_line_pair(self):
        base_candidate = next(
            item
            for item in self.result["findings"]
            if item["rule_id"] == "STRUCTURE-SUPPORT-LINE-PLAN-INTERACTION"
            and "GW-STAIR-S" in item["entity_ids"]
        )
        self.assertIn(
            "D-M",
            [item["opening_id"] for item in base_candidate["evidence"]["opening_plan_candidates"]],
        )

        door = self.snapshot["entities"]["D-M"]
        study = study_template(self.snapshot, "MOVE-P2-DOOR-STUDY")
        study["changes"] = {
            "D-M": {
                "expected": {"start_m": door["parameters"]["start_m"]},
                "set": {"start_m": 29.5},
            }
        }
        with tempfile.TemporaryDirectory() as directory:
            project_path = Path(directory) / "study.json"
            project_path.write_text(json.dumps(study), encoding="utf-8")
            result = evaluate_disciplines(resolve_project(project_path))
        changed_candidate = next(
            item
            for item in result["findings"]
            if item["rule_id"] == "STRUCTURE-SUPPORT-LINE-PLAN-INTERACTION"
            and "GW-STAIR-S" in item["entity_ids"]
        )
        self.assertNotIn(
            "D-M",
            [
                item["opening_id"]
                for item in changed_candidate["evidence"]["opening_plan_candidates"]
            ],
        )
        self.assertEqual(changed_candidate["status"], "OPEN")

    def test_public_support_line_audit_rejects_invalid_numbers_and_keeps_unknown_geometry_open(
        self,
    ):
        spaces = []
        openings = [{"id": "UNLOCATED-DOOR", "geometry": {"shape": "unresolved"}}]
        candidate = {"source_ref": "test#line[0]", "x_m": 1.0, "y_m": 2.0}
        result = evaluate_current_support_line_plan(candidate, spaces, openings)
        self.assertEqual(result["unsupported_opening_ids"], ["UNLOCATED-DOOR"])
        self.assertEqual(
            result["vertical_relation"], "unknown: no selected structural member extent"
        )

        for invalid in (True, float("nan"), float("inf")):
            with self.subTest(invalid=invalid), self.assertRaises(VerticalContinuityError):
                evaluate_current_support_line_plan(
                    {"source_ref": "bad", "x_m": invalid, "y_m": 0.0}, spaces, openings
                )

    def test_unsupported_current_room_geometry_is_not_evaluated_as_a_pass(self):
        snapshot = deepcopy(self.snapshot)
        snapshot["entities"]["M-D"]["geometry"]["shape"] = "polygon"
        result = evaluate_disciplines(snapshot)
        programme = [item for item in result["findings"] if item["rule_id"].startswith("PROGRAM-")]
        self.assertEqual(len(programme), 3)
        self.assertTrue(
            all(
                item["status"] == "OPEN" and item["coverage"] == "unsupported" for item in programme
            )
        )
        equipment = next(
            item
            for item in result["findings"]
            if item["rule_id"] == "EQUIPMENT-BENCHMARK-LAYOUT-APPLICABILITY"
        )
        self.assertEqual(equipment["coverage"], "unsupported")

    def test_adapters_are_pure_and_do_not_reload_equipment_files(self):
        snapshot = deepcopy(self.snapshot)
        before = deepcopy(snapshot)
        with (
            patch(
                "dreamhouse.equipment.validators.load_catalog",
                side_effect=AssertionError("file reload"),
            ),
            patch(
                "dreamhouse.equipment.validators.load_layout",
                side_effect=AssertionError("file reload"),
            ),
        ):
            result = evaluate_disciplines(snapshot)
        self.assertEqual(snapshot, before)
        self.assertEqual(result["disciplines"]["equipment"]["status"], "OPEN")
        registry_ids = {item["rule_id"] for item in result["rule_registry"]}
        self.assertEqual({item["rule_id"] for item in result["findings"]} - registry_ids, set())


if __name__ == "__main__":
    unittest.main()

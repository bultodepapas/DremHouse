from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dreamhouse.cost import reconcile_costs
from dreamhouse.envelope import validate_rooflights
from dreamhouse.equipment import validate_equipment
from dreamhouse.model import load_project
from dreamhouse.model.io import ModelError
from dreamhouse.pipeline import run_pipeline
from dreamhouse.quantities import build_quantity_ledger
from dreamhouse.structure.coordination import compare_support_concepts


class TestCanonicalProjectModel(unittest.TestCase):
    def test_active_scenario_is_hash_locked_and_cross_model_consistent(self):
        project = load_project()
        self.assertEqual(project.scenario_id, "D054_HALF_CENTRES")
        self.assertTrue(all(item.status == "PASS" for item in project.checks))
        self.assertEqual(project.geometry["great_wall_x_m"], 31.5)

    def test_bad_source_hash_fails_closed(self):
        source = Path(__file__).parents[2] / "model" / "project_v04.json"
        manifest = json.loads(source.read_text(encoding="utf-8"))
        manifest["sources"]["PB_B05"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad-manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ModelError, "failed closed"):
                load_project(manifest_path=path)


class TestIntegratedGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = load_project()

    def test_d054_half_centres_are_exact_and_grid_crossings_remain_open(self):
        result = validate_rooflights(
            self.project.models["rooflights"],
            canonical_double_height=self.project.geometry["double_height"],
        )
        checks = {item["rule_id"]: item for item in result["checks"]}
        self.assertEqual(checks["ROOF-D054-HALF-CENTRES"]["status"], "PASS")
        self.assertEqual(checks["ROOF-D054-STRUCTURAL-TRIMMERS"]["status"], "OPEN")
        self.assertEqual(result["total_area_m2"], 23.04)
        conflicts = result["structural_grid"]["conflicts"]
        self.assertEqual(conflicts[0]["portal_lines_x_m"], [6.0])
        self.assertEqual(conflicts[1]["portal_lines_x_m"], [18.0])
        self.assertTrue(all(item["purlin_lines_y_m"] == [9.0] for item in conflicts))

    def test_real_equipment_envelopes_report_one_kitchen_mismatch(self):
        result = validate_equipment(
            self.project.models["pb"], self.project.models["p2"]
        )
        checks = {item["rule_id"]: item for item in result["checks"]}
        self.assertEqual(checks["EQUIP-PRIMARY-BED-CLEARANCE"]["status"], "PASS")
        self.assertEqual(checks["EQUIP-EQ-CAR-HOST"]["status"], "PASS")
        self.assertEqual(checks["EQUIP-EQ-FRIDGE-HOST"]["status"], "OPEN")

    def test_quantity_cost_chain_is_exact_but_not_budget_eligible(self):
        ledger = build_quantity_ledger(
            self.project.models["pb"],
            self.project.models["p2"],
            self.project.models["rooflights"],
        )
        totals = ledger["totals_by_assembly"]
        self.assertEqual(totals["PB-TECHNICAL-GLAZING"]["m2"], 41.76)
        self.assertEqual(totals["P2-WINDOWS"]["m2"], 55.02)
        self.assertEqual(totals["ROOFLIGHT-GLAZING"]["m2"], 23.04)
        self.assertEqual(ledger["programme"]["suite_component_areas_m2"]["M"], 66.28)
        costs = reconcile_costs(ledger)
        self.assertIsNone(costs["approved_budget_total_cop"])
        self.assertFalse(any(item["eligible_for_budget"] for item in costs["rows"]))

    def test_support_comparison_does_not_select_a_structure(self):
        result = compare_support_concepts(
            self.project.models["structure"],
            self.project.models["pb"],
            self.project.models["p2"],
            self.project.models["e1_space"],
        )
        by_id = {item["id"]: item for item in result["alternatives"]}
        self.assertEqual(by_id["SUPPORT-A-STAIR-4"]["geometry_status"], "PASS")
        self.assertEqual(by_id["SUPPORT-B-GREAT-WALL-6"]["geometry_status"], "FAIL")
        self.assertFalse(result["selection_or_construction_authority"])


class TestPipelineArtifacts(unittest.TestCase):
    def test_fast_pipeline_is_deterministic_and_self_hashing(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "package"
            first = run_pipeline(output_dir=output, include_structural_screening=False)
            first_manifest = (output / "manifest.json").read_bytes()
            second = run_pipeline(output_dir=output, include_structural_screening=False)
            self.assertEqual(first["input_hash"], second["input_hash"])
            self.assertEqual(first_manifest, (output / "manifest.json").read_bytes())
            manifest = json.loads(first_manifest)
            self.assertFalse(manifest["issue_ready"])
            self.assertTrue((output / "rooflights" / "compliance.json").exists())
            listed = {item["path"] for item in manifest["outputs"]}
            actual = {
                path.relative_to(output).as_posix()
                for path in output.rglob("*")
                if path.is_file() and path != output / "manifest.json"
            }
            self.assertEqual(listed, actual)


if __name__ == "__main__":
    unittest.main()

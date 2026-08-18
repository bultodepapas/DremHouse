from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import build_access_diagram, build_plan, generate, validate_model
from dreamhouse.generate_p2_b18 import DELTA, load_b18_model


class TestP2B18(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b18_model()
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)
        cls.access = build_access_diagram(cls.model)

    def test_rear_spur_is_absorbed_into_wellness(self):
        by_id = {item["id"]: item for item in self.model["spaces"]}
        self.assertNotIn("F2-SPUR", by_id)
        self.assertIn("WELL-D", by_id)
        wellness_area = sum(
            by_id[item]["w"] * by_id[item]["d"]
            for item in self.model["wellness_suite"]["space_ids"]
        )
        self.assertAlmostEqual(wellness_area, 22.62)

    def test_dry_threshold_is_open_to_wellness_and_keeps_route(self):
        by_door = {item["id"]: item for item in self.model["doors"]}
        self.assertEqual(by_door["D-DIST-SPUR"]["connects"], ["FAM-N", "WELL-D"])
        self.assertEqual(by_door["D-WELL"]["connects"], ["WELL-D", "WELL"])
        self.assertEqual(by_door["D-WELL"]["kind"], "opening")
        self.assertEqual(by_door["D-WELL"]["width"], 2.9)
        self.assertEqual(self.model["egress_reserve"]["access_space"], "WELL-D")

    def test_geometry_passes_and_egress_gate_stays_open(self):
        by_rule = {item["rule_id"]: item for item in self.checks}
        self.assertEqual(by_rule["P2-WELLNESS"]["status"], "PASS")
        self.assertEqual(by_rule["P2-WELLNESS-RELAXATION"]["status"], "PASS")
        self.assertEqual(by_rule["P2-CENTRAL-DISTRIBUTOR"]["status"], "PASS")
        self.assertEqual(by_rule["P2-WELLNESS-EGRESS-ROUTE"]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        ET.fromstring(self.plan)
        ET.fromstring(self.access)

    def test_plan_explains_expanded_wellness(self):
        self.assertIn("COOL / RECLINE", self.plan)
        self.assertIn("D-062 · EXPANDED P2 WELLNESS", self.plan)
        self.assertNotIn("F2-SPUR", self.plan)
        self.assertIn("WELL-D", self.access)

    def test_generation_manifest_records_delta_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(
                self.model,
                target,
                source_path=DELTA,
                generator_name="dreamhouse/generate_p2_b18.py",
            )
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-18-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b18_delta.json")
            self.assertEqual(manifest["supersedes"], "0.3-draft-17-P2 / R14")


if __name__ == "__main__":
    unittest.main()

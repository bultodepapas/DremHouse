from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import build_plan, generate, validate_model
from dreamhouse.generate_p2_b23 import DELTA, load_b23_model


class TestP2B23(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b23_model()
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)

    def test_primary_bedroom_has_one_name_and_area(self):
        by_id = {item["id"]: item for item in self.model["spaces"]}
        unified = self.model["primary_bedroom_unified"]
        self.assertEqual({by_id[item]["name"] for item in unified["space_ids"]}, {"Primary bedroom"})
        self.assertAlmostEqual(sum(by_id[item]["w"] * by_id[item]["d"] for item in unified["space_ids"]), 35.24)

    def test_privacy_screen_is_removed_from_model_and_plan(self):
        self.assertNotIn("privacy_screen", self.model["primary_suite_rebalance"])
        self.assertNotIn("PRIVACY SCREEN", self.plan)
        self.assertNotIn("primary-privacy-screen", self.plan)

    def test_plan_has_one_primary_bedroom_label(self):
        self.assertEqual(self.plan.count(">Primary bedroom<"), 1)
        self.assertNotIn("Primary bedroom lounge entry", self.plan)
        self.assertNotIn("Primary bedroom sleep zone", self.plan)

    def test_geometry_and_unified_bedroom_pass(self):
        by_rule = {item["rule_id"]: item for item in self.checks}
        self.assertEqual(by_rule["P2-PRIMARY-PROGRAMME"]["status"], "PASS")
        self.assertEqual(by_rule["P2-PRIMARY-BEDROOM-UNIFIED"]["status"], "PASS")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        ET.fromstring(self.plan)

    def test_generation_manifest_records_delta_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(self.model, target, source_path=DELTA, generator_name="dreamhouse/generate_p2_b23.py")
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-23-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b23_delta.json")
            self.assertEqual(manifest["supersedes"], "0.3-draft-22-P2 / R19")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import build_plan, generate, validate_model
from dreamhouse.generate_p2_b22 import DELTA, load_b22_model


class TestP2B22(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b22_model()
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)

    def test_primary_bathroom_is_one_l_shaped_area(self):
        by_id = {item["id"]: item for item in self.model["spaces"]}
        bathroom = self.model["primary_bathroom_unified"]
        gross = sum(by_id[item]["w"] * by_id[item]["d"] for item in bathroom["space_ids"])
        self.assertAlmostEqual(gross, 17.60)
        self.assertAlmostEqual(bathroom["schematic_net_area_m2"], 15.66)

    def test_intermediate_wall_and_door_are_removed(self):
        by_door = {item["id"]: item for item in self.model["doors"]}
        opening = by_door["D-M-WET"]
        self.assertEqual(opening["kind"], "opening")
        self.assertEqual(opening["at"], 5.0)
        self.assertEqual(opening["width"], 2.4)

    def test_fixture_programme_is_complete_and_not_duplicated(self):
        fixtures = self.model["primary_bathroom_unified"]["fixtures"]
        self.assertEqual({item["type"] for item in fixtures}, {"shower", "tub", "vanity", "wc", "linen"})
        for fixture_type in ("shower", "tub", "vanity", "wc", "linen"):
            self.assertEqual(self.plan.count(f"primary-{fixture_type}"), 1)

    def test_geometry_and_unified_bathroom_pass(self):
        by_rule = {item["rule_id"]: item for item in self.checks}
        self.assertEqual(by_rule["P2-AREA-CLOSURE"]["status"], "PASS")
        self.assertEqual(by_rule["P2-DOOR-GEOMETRY"]["status"], "PASS")
        self.assertEqual(by_rule["P2-PRIMARY-BATHROOM-UNIFIED"]["status"], "PASS")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        ET.fromstring(self.plan)

    def test_plan_records_d066_and_single_room(self):
        self.assertIn("D-066 · UNIFIED PRIMARY BATHROOM", self.plan)
        self.assertIn("17.60 m2 gross unified", self.plan)
        self.assertNotIn("Primary bathroom wet salon", self.plan)
        self.assertNotIn("Primary bathroom service band", self.plan)

    def test_generation_manifest_records_delta_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(self.model, target, source_path=DELTA, generator_name="dreamhouse/generate_p2_b22.py")
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-22-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b22_delta.json")
            self.assertEqual(manifest["supersedes"], "0.3-draft-21-P2 / R18")


if __name__ == "__main__":
    unittest.main()

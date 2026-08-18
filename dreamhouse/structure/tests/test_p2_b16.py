from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import build_access_diagram, build_plan, generate, validate_model
from dreamhouse.generate_p2_b16 import DELTA, load_b16_model


class TestP2B16(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b16_model()
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)
        cls.access = build_access_diagram(cls.model)

    def test_family_centre_is_one_coherent_room(self):
        by_id = {item["id"]: item for item in self.model["spaces"]}
        self.assertNotIn("FAM-A", by_id)
        self.assertNotIn("HALL-C", by_id)
        self.assertEqual((by_id["FAM"]["w"], by_id["FAM"]["d"]), (7.6, 3.6))
        self.assertAlmostEqual(by_id["FAM"]["w"] * by_id["FAM"]["d"], 27.36)
        self.assertIn('data-space-id="FAM"', self.plan)
        self.assertIn("FITTED LIBRARY WALL", self.plan)

    def test_geometry_and_access_fail_closed_checks_pass(self):
        by_rule = {item["rule_id"]: item for item in self.checks}
        self.assertEqual(by_rule["P2-FAMILY-CENTRE"]["status"], "PASS")
        self.assertEqual(by_rule["P2-AREA-CLOSURE"]["status"], "PASS")
        self.assertEqual(by_rule["P2-ACCESS-GRAPH"]["status"], "PASS")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        ET.fromstring(self.plan)
        ET.fromstring(self.access)

    def test_child_one_access_remains_explicitly_unchanged(self):
        door = next(item for item in self.model["doors"] if item["id"] == "D-H1")
        self.assertEqual(door["connects"], ["H1-D", "DECK"])
        self.assertIn("access correction remains a separate", self.model["family_centre"]["access_scope"])

    def test_generation_manifest_records_delta_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(
                self.model,
                target,
                source_path=DELTA,
                generator_name="dreamhouse/generate_p2_b16.py",
            )
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-16-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b16_delta.json")
            self.assertEqual(manifest["supersedes"], "0.3-draft-15-P2 / R12")


if __name__ == "__main__":
    unittest.main()

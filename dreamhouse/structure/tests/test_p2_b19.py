from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import build_hall_edge_detail, build_plan, generate, validate_model
from dreamhouse.generate_p2_b19 import DELTA, load_b19_model


class TestP2B19(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b19_model()
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)
        cls.edge = build_hall_edge_detail(cls.model)

    def test_family_frontage_is_fully_open(self):
        balcony = self.model["family_balcony"]
        self.assertEqual((balcony["from_y"], balcony["to_y"]), (5.0, 12.45))
        self.assertAlmostEqual(balcony["to_y"] - balcony["from_y"], 7.45)
        self.assertEqual(balcony["space_ids"], ["DECK", "FAM", "FAM-N"])
        self.assertEqual(self.model["internal_glazing"], [])

    def test_mini_deck_and_family_are_joined_without_door(self):
        by_door = {item["id"]: item for item in self.model["doors"]}
        self.assertEqual(by_door["D-DECK"]["kind"], "opening")
        self.assertEqual(by_door["D-DECK"]["width"], 2.8)
        self.assertEqual(by_door["D-DECK"]["at"], 21.0)

    def test_bedroom_edges_remain_enclosed_and_guard_is_reserved(self):
        wall = self.model["hall_edge_partition"]
        self.assertEqual(wall["id"], "P2-W04R")
        self.assertEqual(wall["open_family_edge"], {"from_y": 5.0, "to_y": 12.45})
        self.assertGreaterEqual(self.model["family_balcony"]["guard_height_m"], 1.10)
        self.assertTrue(self.model["family_balcony"]["continuous_guard"])

    def test_geometry_passes_and_performance_gate_stays_open(self):
        by_rule = {item["rule_id"]: item for item in self.checks}
        self.assertEqual(by_rule["P2-FAMILY-BALCONY"]["status"], "PASS")
        self.assertEqual(by_rule["P2-W04-HALL-EDGE"]["status"], "PASS")
        self.assertEqual(by_rule["P2-FAMILY-BALCONY-PERFORMANCE"]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        ET.fromstring(self.plan)
        ET.fromstring(self.edge)

    def test_drawings_show_open_balcony_not_acoustic_glazing(self):
        self.assertIn("OPEN FAMILY BALCONY", self.plan)
        self.assertIn("D-063 · OPEN FAMILY BALCONY", self.plan)
        self.assertNotIn("internal-acoustic-glazing", self.plan)
        self.assertIn("7.45 m open frontage", self.edge)

    def test_generation_manifest_records_delta_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(
                self.model,
                target,
                source_path=DELTA,
                generator_name="dreamhouse/generate_p2_b19.py",
            )
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-19-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b19_delta.json")
            self.assertEqual(manifest["supersedes"], "0.3-draft-18-P2 / R15")


if __name__ == "__main__":
    unittest.main()

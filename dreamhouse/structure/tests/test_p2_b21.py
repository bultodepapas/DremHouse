from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import build_plan, generate, validate_model
from dreamhouse.generate_p2_b21 import DELTA, load_b21_model


class TestP2B21(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b21_model()
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)

    def test_primary_suite_area_is_rebalanced_not_enlarged(self):
        by_id = {item["id"]: item for item in self.model["spaces"]}
        primary = self.model["primary_suite_rebalance"]
        bedroom = sum(by_id[item]["w"] * by_id[item]["d"] for item in primary["bedroom_space_ids"])
        dressing = by_id[primary["dressing_space_id"]]["w"] * by_id[primary["dressing_space_id"]]["d"]
        bathroom = sum(by_id[item]["w"] * by_id[item]["d"] for item in primary["bathroom_space_ids"])
        self.assertAlmostEqual(bedroom, 35.24)
        self.assertAlmostEqual(dressing, 13.44)
        self.assertAlmostEqual(bathroom, 17.6)
        self.assertAlmostEqual(bedroom + dressing + bathroom, 66.28)

    def test_dressing_moves_to_child_one_service_side(self):
        by_id = {item["id"]: item for item in self.model["spaces"]}
        self.assertEqual((by_id["M-C"]["x"], by_id["M-C"]["y"]), (28.6, 0.0))
        self.assertEqual((by_id["M-C"]["w"], by_id["M-C"]["d"]), (3.2, 4.2))
        self.assertEqual(self.model["primary_suite_rebalance"]["new_partition_axis_x"], 31.8)

    def test_old_wall_becomes_wide_opening_and_privacy_is_retained(self):
        by_door = {item["id"]: item for item in self.model["doors"]}
        self.assertEqual(by_door["D-M-D"]["connects"], ["M-L", "M-D"])
        self.assertEqual(by_door["D-M-D"]["kind"], "opening")
        self.assertEqual(by_door["D-M-D"]["width"], 4.2)
        self.assertEqual(by_door["D-M-C"]["connects"], ["M-L", "M-C"])
        self.assertIn("privacy_screen", self.model["primary_suite_rebalance"])

    def test_south_window_clears_new_dressing(self):
        by_window = {item["id"]: item for item in self.model["windows"]}
        self.assertEqual(by_window["W-M-LAT-A"]["from"], 32.05)
        self.assertEqual(by_window["W-M-LAT-A"]["room_id"], "M-D")

    def test_geometry_and_primary_programme_pass(self):
        by_rule = {item["rule_id"]: item for item in self.checks}
        self.assertEqual(by_rule["P2-AREA-CLOSURE"]["status"], "PASS")
        self.assertEqual(by_rule["P2-DOOR-GEOMETRY"]["status"], "PASS")
        self.assertEqual(by_rule["P2-WINDOWS"]["status"], "PASS")
        self.assertEqual(by_rule["P2-PRIMARY-PROGRAMME"]["status"], "PASS")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        ET.fromstring(self.plan)

    def test_plan_records_d065_and_new_furniture(self):
        self.assertIn("D-065 · PRIMARY SUITE REBALANCE", self.plan)
        self.assertIn("PRIMARY COMPACT DRESSING", self.plan.upper())
        self.assertIn("PRIVACY SCREEN", self.plan)
        self.assertIn("primary-wardrobe-run", self.plan)

    def test_generation_manifest_records_delta_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(
                self.model,
                target,
                source_path=DELTA,
                generator_name="dreamhouse/generate_p2_b21.py",
            )
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-21-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b21_delta.json")
            self.assertEqual(manifest["supersedes"], "0.3-draft-20-P2 / R17")


if __name__ == "__main__":
    unittest.main()

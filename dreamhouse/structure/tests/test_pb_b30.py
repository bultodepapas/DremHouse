from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b30 import generate, load_b30_model, validate_b30


class TestPBB30(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b30_model()
        cls.checks = validate_b30(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_full_span_kitchen_and_island_routes_pass(self):
        kitchen = self.model["kitchen"]
        self.assertEqual(kitchen["wall_run"]["length"], 10.05)
        self.assertEqual(kitchen["island"]["length"], 7.2)
        self.assertEqual(kitchen["island_seating"]["count"], 8)
        self.assertEqual(self.by_rule["PB-KD-FULL-DOMESTIC-WALL"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-KD-ISLAND-END-ROUTES"]["status"], "PASS")

    def test_dining_moves_opposite_without_entering_axis(self):
        table = self.model["social_layout"]["dining"]["table"]
        self.assertGreater(table["y"], self.model["design_values"]["axis_y1"])
        self.assertEqual(self.by_rule["PB-KD-DINING-OPPOSITE"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-KD-CENTRAL-AXIS-CLEAR"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-KD-DINING-LIVING-SEPARATION"]["status"], "PASS")

    def test_option_status_and_professional_gates_remain_open(self):
        self.assertIn("does not supersede PB b29", self.model["status"])
        for rule_id in (
            "PB-KD-OWNER-SELECTION",
            "PB-KD-APPLIANCE-MEP",
            "PB-KD-DINING-DAYLIGHT",
        ):
            self.assertEqual(self.by_rule[rule_id]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_option_drawings_and_manifest_are_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-S01_PB-KITCHEN-DINING-OPTION.svg"
            ).read_text(encoding="utf-8")
            study = target.joinpath(
                "DH-ARQ-OPT-001-R00_PB-KITCHEN-DINING-STUDY.svg"
            ).read_text(encoding="utf-8")
            self.assertIn("7.20 m FULL-SPAN ISLAND", plan)
            self.assertIn("DINING OPPOSITE KITCHEN", plan)
            self.assertIn("CURRENT DIAGNOSIS + PREFERRED TEST", study)
            self.assertIn("PREFERRED TEST (NOT ADOPTED)", study)

            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-option-30-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b30_delta.json")
            for filename in manifest["outputs"]:
                if filename.endswith(".svg"):
                    ET.fromstring(target.joinpath(filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

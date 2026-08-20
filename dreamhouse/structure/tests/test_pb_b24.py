from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b24 import generate, load_b24_model, validate_b24


class TestPBB24(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b24_model()
        cls.checks = validate_b24(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_workstations_are_a_true_mirrored_pair(self):
        by_side = {item["side"]: item for item in self.model["workstations"]}
        self.assertEqual(set(by_side), {"A", "B"})
        for key in (
            "zone_x0",
            "zone_x1",
            "zone_depth",
            "worktop_x0",
            "worktop_length",
            "worktop_depth",
            "worktop_height",
        ):
            self.assertEqual(by_side["A"][key], by_side["B"][key])
        self.assertEqual(self.by_rule["PB-WS-MIRROR"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-WS-WALL-CONTACT"]["status"], "PASS")

    def test_workstation_windows_match_and_clear_the_worktops(self):
        by_side = {item["side"]: item for item in self.model["workstation_glazing"]}
        self.assertEqual(by_side["A"]["x0"], by_side["B"]["x0"])
        self.assertEqual(by_side["A"]["x1"], by_side["B"]["x1"])
        self.assertEqual(by_side["A"]["sill"], 0.9)
        self.assertEqual(by_side["A"]["height"], 1.65)
        self.assertEqual(self.by_rule["PB-WS-GLAZING-SYMMETRY"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-WS-SILL-CLEARANCE"]["status"], "PASS")

    def test_open_professional_interfaces_are_explicit(self):
        self.assertEqual(
            self.by_rule["PB-WS-A-MAIN-GLAZING-JUNCTION"]["status"], "OPEN"
        )
        self.assertEqual(self.by_rule["PB-CAR-BENCH-LIFT-INTERFACE"]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_generated_sheets_are_valid_svg_and_manifested(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-24-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b24_delta.json")
            for filename in manifest["outputs"]:
                if filename.endswith(".svg"):
                    ET.fromstring(target.joinpath(filename).read_text(encoding="utf-8"))

    def test_plan_and_elevations_expose_d068_intent(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(self.model, target)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-R05_PB-INTEGRATED-WORKSTATIONS.svg"
            ).read_text(encoding="utf-8")
            side_a = target.joinpath(
                "DH-ARQ-ELE-003-R07_SIDE-A-INTEGRATED-WORKSTATION.svg"
            ).read_text(encoding="utf-8")
            side_b = target.joinpath(
                "DH-ARQ-ELE-004-R07_SIDE-B-INTEGRATED-WORKSTATION.svg"
            ).read_text(encoding="utf-8")
            detail = target.joinpath(
                "DH-ARQ-DET-006-R00_PB-INTEGRATED-WORKSTATIONS.svg"
            ).read_text(encoding="utf-8")
            self.assertEqual(plan.count("3 × 3 m CLEAR"), 2)
            self.assertIn("WORKSTATION 1 WINDOW", side_a)
            self.assertIn("WORKSTATION 2 WINDOW", side_b)
            self.assertIn("DEDICATED SECONDARY STEEL", detail)
            self.assertNotIn(">ESCRITORIO<", plan)


if __name__ == "__main__":
    unittest.main()

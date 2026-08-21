from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b35 import generate, load_b35_model, validate_b35


class TestPBB35(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b35_model()
        cls.checks = validate_b35(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_side_a_window_worktop_and_monumental_band_share_one_centre(self):
        workstation = next(item for item in self.model["workstations"] if item["side"] == "A")
        window = next(item for item in self.model["workstation_glazing"] if item["side"] == "A")
        self.assertEqual((window["x0"], window["x1"], window["sill"], window["height"]), (12.15, 19.35, .9, 2.9))
        self.assertEqual((workstation["worktop_x0"], workstation["worktop_length"], workstation["worktop_depth"]), (13.05, 5.4, .9))
        self.assertEqual(self.by_rule["PB35-D078-COMMON-CENTRE"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB35-D078-SYMMETRIC-RESIDUALS"]["status"], "PASS")

    def test_two_equal_seats_are_defined_by_three_cabinets(self):
        workstation = next(item for item in self.model["workstations"] if item["side"] == "A")
        self.assertEqual(workstation["drawer_cabinet_count"], 3)
        self.assertEqual(workstation["drawer_cabinet_offsets"], [0.0, 2.35, 4.7])
        self.assertEqual(workstation["chair_centres_x"], [14.575, 16.925])
        self.assertEqual(self.by_rule["PB35-D078-TWO-SEATS-THREE-CABINETS"]["status"], "PASS")

    def test_side_b_and_all_unaffected_pb_geometry_are_retained(self):
        workstation = next(item for item in self.model["workstations"] if item["side"] == "B")
        window = next(item for item in self.model["workstation_glazing"] if item["side"] == "B")
        self.assertEqual((workstation["worktop_x0"], workstation["worktop_length"], workstation["drawer_cabinet_count"]), (13.0, 3.0, 2))
        self.assertEqual((window["x0"], window["x1"], window["sill"], window["height"]), (13.0, 16.0, .9, 1.65))
        self.assertEqual(self.model["kitchen"]["island"]["length"], 7.2)
        self.assertEqual(self.model["social_layout"]["dining"]["seat_count"], 12)
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_generated_evidence_is_traceable_and_states_exterior_priority(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-R13_PB-SIDE-A-SHARED-WORKSTATION.svg"
            ).read_text(encoding="utf-8")
            elevation = target.joinpath(
                "DH-ARQ-ELE-003-R09_SIDE-A-PERFORMANCE-FIRST-OPENING.svg"
            ).read_text(encoding="utf-8")
            detail = target.joinpath(
                "DH-ARQ-DET-006-R02_SIDE-A-SHARED-WORKSTATION.svg"
            ).read_text(encoding="utf-8")
            self.assertEqual(plan.count(">3D</text>"), 5)
            self.assertEqual(plan.count("SIDE A SHARED WORKSTATION"), 2)
            self.assertNotIn("PROVISIONAL MAIN GLAZING", plan)
            self.assertIn("PERFORMANCE-FIRST OPENING", elevation)
            self.assertIn("not a facade showpiece", elevation)
            self.assertIn("ONE 7.20 × 2.90 m ARCHITECTURAL OPENING", detail)
            self.assertIn("RUGGED CORRUGATED INDUSTRIAL ENVELOPE", detail)
            for content in (plan, elevation, detail):
                ET.fromstring(content)

            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-35-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b35_delta.json")
            self.assertEqual(manifest["base_source"], "dreamhouse/pb_b34_delta.json")


if __name__ == "__main__":
    unittest.main()

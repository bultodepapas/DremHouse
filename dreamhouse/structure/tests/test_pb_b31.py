from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b31 import generate, load_b31_model, validate_b31


class TestPBB31(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b31_model()
        cls.checks = validate_b31(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_researched_table_size_and_twelve_seats_pass(self):
        dining = self.model["social_layout"]["dining"]
        table = dining["table"]
        self.assertEqual((table["length"], table["depth"], table["height"]), (3.2, 1.1, 0.75))
        self.assertEqual(dining["chairs_per_side"], 5)
        self.assertEqual(dining["end_chairs"], 1)
        self.assertEqual(self.by_rule["PB-KD-DINING-12-SEATS"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-KD-DINING-RESEARCHED-SIZE"]["status"], "PASS")

    def test_table_group_and_clearance_are_truly_centred(self):
        self.assertEqual(self.by_rule["PB-KD-DINING-TRUE-CENTRE"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-KD-DINING-CLEARANCE-ENVELOPE"]["status"], "PASS")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_product_selection_remains_open(self):
        self.assertEqual(self.by_rule["PB-KD-DINING-PRODUCT-SELECTION"]["status"], "OPEN")
        self.assertEqual(len(self.model["research_sources"]), 4)

    def test_option_drawings_and_manifest_are_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-S02_PB-CENTRED-12-SEAT-DINING.svg"
            ).read_text(encoding="utf-8")
            study = target.joinpath(
                "DH-ARQ-OPT-002-R00_PB-CENTRED-DINING-STUDY.svg"
            ).read_text(encoding="utf-8")
            self.assertIn("12P · 3.20 × 1.10", plan)
            self.assertIn("1.10 m CHAIR / WALK CLEARANCE ENVELOPE", plan)
            self.assertIn("TRUE CENTRE · X=26.25 / Y=14.41", study)

            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-option-31-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b31_delta.json")
            for filename in manifest["outputs"]:
                if filename.endswith(".svg"):
                    ET.fromstring(target.joinpath(filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

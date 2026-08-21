from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b32 import generate, load_b32_model, validate_b32


class TestPBB32(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b32_model()
        cls.checks = validate_b32(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_complete_car_lift_group_is_centred(self):
        layout = self.model["car_lift_layout"]
        territory = self.model["car_territory"]
        self.assertEqual(layout["centre"], {"x": 5.34, "y": 3.965})
        self.assertEqual(territory["centre"], {"x": 5.34, "y": 3.965})
        self.assertEqual(self.by_rule["PB-CAR-LIFT-LONGITUDINAL-CENTRE"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-CAR-LIFT-INTERNAL-CENTRE"]["status"], "PASS")

    def test_equal_end_residuals_and_constrained_transverse_fit_pass(self):
        layout = self.model["car_lift_layout"]
        self.assertEqual((layout["front_residual"], layout["rear_residual"]), (1.96, 1.96))
        self.assertEqual((layout["bench_clearance"], layout["axis_clearance"]), (.10, .10))
        self.assertEqual(self.by_rule["PB-CAR-LIFT-EQUAL-END-RESIDUALS"]["status"], "PASS")
        self.assertEqual(
            self.by_rule["PB-CAR-LIFT-CONSTRAINED-TRANSVERSE-FIT"]["status"], "PASS"
        )
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_real_equipment_coordination_remains_open(self):
        self.assertEqual(self.by_rule["PB-CAR-LIFT-REAL-EQUIPMENT"]["status"], "OPEN")

    def test_option_drawings_and_manifest_are_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-S03_PB-CENTRED-PROJECT-CAR-LIFT.svg"
            ).read_text(encoding="utf-8")
            study = target.joinpath(
                "DH-ARQ-OPT-003-R00_PB-PROJECT-CAR-CENTRING-STUDY.svg"
            ).read_text(encoding="utf-8")
            self.assertIn("CENTRED PROJECT CAR + LIFT", plan)
            self.assertIn("END RESIDUALS", study)
            self.assertIn("1.96 m front + 1.96 m rear", study)

            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-option-32-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b32_delta.json")
            for filename in manifest["outputs"]:
                if filename.endswith(".svg"):
                    ET.fromstring(target.joinpath(filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

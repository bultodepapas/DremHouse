from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b36 import generate, load_b36_model, validate_b36


class TestPBB36(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b36_model()
        cls.checks = validate_b36(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}
        cls.benches = {item["id"]: item for item in cls.model["built_in_benches"]}

    def test_wall_benches_share_only_the_economical_module_grid(self):
        car = self.benches["PB-BENCH-CAR"]
        rc = self.benches["PB-BENCH-RC"]
        for bench in (car, rc):
            self.assertEqual((bench["length"], bench["depth"]), (9.0, .75))
            self.assertEqual((bench["module_count"], bench["module_width"]), (6, 1.5))
        self.assertEqual(car["module_top_heights"], [.9, .84, .9, .9, .9, .9])
        self.assertEqual(rc["adjustable_module_indices"], [1, 2, 3])
        self.assertEqual(rc["esd_module_indices"], [1, 2, 3])
        self.assertEqual(self.by_rule["PB36-D079-COMMON-MODULE-GRID"]["status"], "PASS")

    def test_central_island_and_rc_operating_clearances_are_exact(self):
        central = self.model["central_rc_bench"]
        self.assertEqual(
            (central["x"], central["y"], central["length"], central["depth"], central["height"]),
            (2.8, 12.7, 4.5, 1.6, .84),
        )
        self.assertEqual(self.model["rc_support_equipment"]["printer_zone"]["y"], 14.0)
        self.assertEqual(self.model["rc_support_equipment"]["lipo_zone"]["y"], 14.0)
        self.assertEqual(self.by_rule["PB36-D079-RC-OPERATING-CLEARANCES"]["status"], "PASS")

    def test_unsafe_or_product_dependent_claims_fail_closed(self):
        for rule_id in (
            "PB36-D079-CAR-LIFT-OPERATING-CONFLICT",
            "PB36-D079-ANTHROPOMETRY-AND-MOCKUP",
            "PB36-D079-WINDOW-SERVICE-INDEPENDENCE",
            "PB36-D079-MEP-ESD-FUME-BATTERY",
            "PB36-D079-COST-CODE-GAP",
        ):
            self.assertEqual(self.by_rule[rule_id]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_generated_plan_detail_and_manifest_are_traceable(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-R14_PB-MODULAR-TECHNICAL-WORKBENCHES.svg"
            ).read_text(encoding="utf-8")
            detail = target.joinpath(
                "DH-ARQ-DET-007-R01_PB-TECHNICAL-WORKBENCH-SYSTEM.svg"
            ).read_text(encoding="utf-8")
            self.assertIn("PROJECT-CAR MODULAR BENCH", plan)
            self.assertIn("RC / ELECTRONICS MODULAR BENCH", plan)
            self.assertIn("1.20 m BENCH OPERATING STRIP", plan)
            self.assertIn("CENTRAL RC ASSEMBLY ISLAND", plan)
            self.assertIn("PROJECT CAR WALL BENCH · SIX DUTY MODULES", detail)
            self.assertIn("RC / ELECTRONICS WALL BENCH", detail)
            self.assertIn("NOT FOR PROCUREMENT, FABRICATION OR CONSTRUCTION", detail)
            for content in (plan, detail):
                ET.fromstring(content)

            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-36-PB")
            self.assertEqual(manifest["decision"], "D-079")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b36_delta.json")
            self.assertEqual(manifest["base_source"], "dreamhouse/pb_b35_delta.json")


if __name__ == "__main__":
    unittest.main()

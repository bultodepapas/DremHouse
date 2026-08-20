from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b29 import generate, load_b29_model, validate_b29


class TestPBB29(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b29_model()
        cls.checks = validate_b29(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_both_benches_start_at_front_inner_corners(self):
        for bench in self.model["built_in_benches"]:
            self.assertAlmostEqual(bench["x0"], 0.18)
            self.assertEqual(bench["start_condition"], "front_inner_corner")
        self.assertEqual(
            self.by_rule["PB-TECH-BENCHES-FRONT-CORNER-START"]["status"],
            "PASS",
        )

    def test_lengths_and_front_door_separation_pass(self):
        self.assertEqual(
            self.by_rule["PB-TECH-BENCHES-LENGTH-RETAINED"]["status"], "PASS"
        )
        self.assertEqual(
            self.by_rule["PB-TECH-BENCHES-FRONT-DOOR-SEPARATION"]["status"],
            "PASS",
        )
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_plan_records_corner_start_revision(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-R10_PB-CORNER-START-WORKBENCHES.svg"
            ).read_text(encoding="utf-8")
            self.assertIn("CORNER-START WORKBENCHES", plan)
            self.assertIn("PLN-001-R10", plan)
            self.assertIn("WALL-INTEGRATED PROJECT-CAR BENCH · 9.00 m", plan)
            self.assertIn("RC / ELECTRONICS INTEGRATED BENCH · 9.00 m", plan)

    def test_manifest_and_svg_outputs_are_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(self.model, target)
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-29-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b29_delta.json")
            for filename in manifest["outputs"]:
                if filename.endswith(".svg"):
                    ET.fromstring(target.joinpath(filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

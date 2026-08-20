from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b28 import generate, load_b28_model, validate_b28


class TestPBB28(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b28_model()
        cls.checks = validate_b28(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_project_car_bench_is_against_side_a_wall(self):
        car_bench = next(
            item for item in self.model["built_in_benches"]
            if item["id"] == "PB-BENCH-CAR"
        )
        self.assertEqual(car_bench["mounting"], "side_a_perimeter")
        self.assertAlmostEqual(car_bench["y0"], 0.18)
        self.assertEqual(self.by_rule["PB-CAR-BENCH-SIDE-A-WALL"]["status"], "PASS")

    def test_bench_window_and_lift_test_geometry_pass(self):
        for rule_id in (
            "PB-TECHNICAL-BENCHES-PERIMETER",
            "PB-CAR-BENCH-BELOW-WINDOW",
            "PB-CAR-BENCH-LIFT-GRAPHIC-SEPARATION",
        ):
            self.assertEqual(self.by_rule[rule_id]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-CAR-BENCH-LIFT-INTERFACE"]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_plan_states_wall_integrated_workbench(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-R09_PB-WALL-INTEGRATED-WORKBENCH.svg"
            ).read_text(encoding="utf-8")
            self.assertIn("WALL-INTEGRATED PROJECT-CAR BENCH · 9.00 m", plan)
            self.assertIn("PLN-001-R09", plan)
            self.assertIn("100-IN TV · SIDE B WALL", plan)

    def test_manifest_and_svg_outputs_are_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(self.model, target)
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-28-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b28_delta.json")
            for filename in manifest["outputs"]:
                if filename.endswith(".svg"):
                    ET.fromstring(target.joinpath(filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

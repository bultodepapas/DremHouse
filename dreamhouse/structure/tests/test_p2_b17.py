from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import build_access_diagram, build_plan, generate, validate_model
from dreamhouse.generate_p2_b17 import DELTA, load_b17_model


class TestP2B17(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b17_model()
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)
        cls.access = build_access_diagram(cls.model)

    def test_long_double_corridor_is_removed(self):
        by_id = {item["id"]: item for item in self.model["spaces"]}
        self.assertNotIn("ARR", by_id)
        self.assertNotIn("F2-HALL", by_id)
        self.assertEqual((by_id["FAM"]["w"], by_id["FAM"]["d"]), (10.5, 3.6))
        self.assertEqual((by_id["F2-SPUR"]["w"], by_id["F2-SPUR"]["d"]), (4.5, 1.45))
        self.assertAlmostEqual(by_id["F2-SPUR"]["w"] * by_id["F2-SPUR"]["d"], 6.525)

    def test_stair_and_suites_connect_to_distributor(self):
        by_door = {item["id"]: item for item in self.model["doors"]}
        self.assertEqual(by_door["D-STAIR"]["connects"], ["ESC", "FAM"])
        self.assertEqual(by_door["D-H2"]["connects"], ["FAM-N", "H2-D"])
        self.assertEqual(by_door["D-G"]["connects"], ["FAM-N", "G-ENTRY"])
        self.assertEqual(by_door["D-WELL"]["connects"], ["F2-SPUR", "WELL"])
        self.assertEqual(self.model["egress_reserve"]["access_space"], "F2-SPUR")

    def test_geometry_passes_and_fire_gate_stays_open(self):
        by_rule = {item["rule_id"]: item for item in self.checks}
        self.assertEqual(by_rule["P2-CENTRAL-DISTRIBUTOR"]["status"], "PASS")
        self.assertEqual(by_rule["P2-AREA-CLOSURE"]["status"], "PASS")
        self.assertEqual(by_rule["P2-ACCESS-GRAPH"]["status"], "PASS")
        self.assertEqual(by_rule["P2-OPEN-STAIR-ARRIVAL-FIRE"]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        ET.fromstring(self.plan)
        ET.fromstring(self.access)

    def test_plan_explains_open_family_distributor(self):
        self.assertIn("FAMILY STUDY EDGE", self.plan)
        self.assertIn("D-061 · P2 FAMILY DISTRIBUTOR", self.plan)
        self.assertIn("temporary-open-plan-boundary", self.plan)

    def test_generation_manifest_records_delta_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(
                self.model,
                target,
                source_path=DELTA,
                generator_name="dreamhouse/generate_p2_b17.py",
            )
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-17-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b17_delta.json")
            self.assertEqual(manifest["supersedes"], "0.3-draft-16-P2 / R13")


if __name__ == "__main__":
    unittest.main()

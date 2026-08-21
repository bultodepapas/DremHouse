from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.architecture.stair_core import (
    derived_stair_values,
    load_stair_core,
    validate_stair_core,
)
from dreamhouse.generate_p2_b09 import build_plan, validate_model
from dreamhouse.generate_p2_b24 import DELTA as P2_DELTA
from dreamhouse.generate_p2_b24 import load_b24_model
from dreamhouse.generate_pb_b33 import generate as generate_pb
from dreamhouse.generate_pb_b33 import load_b33_model, validate_b33

SVG_NAMESPACE = "{http://www.w3.org/2000/svg}"


class TestStairCoreCoordination(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stair = load_stair_core()
        cls.pb = load_b33_model()
        cls.p2 = load_b24_model()

    def test_stair_arithmetic_and_plan_closure(self):
        values = derived_stair_values(self.stair)
        self.assertAlmostEqual(values["riser"], 3.8 / 22.0)
        self.assertAlmostEqual(values["going"], 0.27)
        self.assertAlmostEqual(values["two_risers_plus_going"], 0.61545454545)
        self.assertGreaterEqual(values["two_risers_plus_going"], 0.60)
        self.assertLessEqual(values["two_risers_plus_going"], 0.64)
        self.assertAlmostEqual(values["flight_run"], 2.70)
        self.assertAlmostEqual(values["clear_width_x"], 4.10)
        self.assertAlmostEqual(values["clear_width_y"], 3.20)
        self.assertAlmostEqual(values["slope_degrees"], 32.61, places=2)
        by_rule = {item["rule_id"]: item for item in validate_stair_core(self.stair)}
        self.assertEqual(by_rule["STAIR-TRANSVERSE-CLOSURE"]["status"], "PASS")
        self.assertEqual(by_rule["STAIR-REAR-DISCHARGE-LEVEL"]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in by_rule.values()), 0)

    def test_pb_p2_footprints_doors_and_columns_match_shared_model(self):
        enclosure = self.stair["enclosure"]
        pb_stair = next(item for item in self.pb["core"] if item["id"] == "ESC")
        p2_stair = next(item for item in self.p2["spaces"] if item["id"] == "ESC")
        self.assertEqual(
            (self.pb["great_wall"]["x"], self.pb["envelope"]["length"], pb_stair["y0"], pb_stair["y1"]),
            (enclosure["x0"], enclosure["x1"], enclosure["y0"], enclosure["y1"]),
        )
        self.assertEqual(
            (p2_stair["x"], p2_stair["x"] + p2_stair["w"], p2_stair["y"], p2_stair["y"] + p2_stair["d"]),
            (enclosure["x0"], enclosure["x1"], enclosure["y0"], enclosure["y1"]),
        )
        shared_columns = {
            (item["id"], item["x"], item["y"])
            for item in self.stair["structure"]["column_reservations"]
        }
        self.assertEqual(
            {(item["id"], item["x"], item["y"]) for item in self.pb["structural_reservations"]},
            shared_columns,
        )
        self.assertEqual(
            {(item["id"], item["x"], item["y"]) for item in self.p2["structural_reservations"]},
            shared_columns,
        )
        p2_door = next(item for item in self.p2["doors"] if item["id"] == "D-STAIR")
        self.assertEqual(p2_door["at"], 9.5)

    def test_pb_and_p2_compliance_fail_closed_without_false_discharge_claim(self):
        pb_checks = validate_b33(self.pb)
        p2_checks = validate_model(self.p2)
        self.assertEqual(sum(item["status"] == "FAIL" for item in pb_checks), 0)
        self.assertEqual(sum(item["status"] == "FAIL" for item in p2_checks), 0)
        self.assertIn(
            "STAIR-REAR-DISCHARGE-LEVEL",
            {item["rule_id"] for item in pb_checks if item["status"] == "OPEN"},
        )
        self.assertIn(
            "STAIR-REAR-DISCHARGE-LEVEL",
            {item["rule_id"] for item in p2_checks if item["status"] == "OPEN"},
        )

    def test_plan_symbols_have_opposite_level_readings_and_four_columns(self):
        p2_svg = build_plan(self.p2)
        self.assertIn("DN TO PB", p2_svg)
        self.assertNotIn("UP FROM PB", p2_svg)
        self.assertIn('data-stair-model-revision="SC-01"', p2_svg)
        p2_root = ET.fromstring(p2_svg)

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate_pb(self.pb, target)
            pb_svg = target.joinpath("DH-ARQ-PLN-001-R11_PB-STAIR-CORE.svg").read_text(
                encoding="utf-8"
            )
            pb_root = ET.fromstring(pb_svg)
            self.assertIn("UP TO P2", pb_svg)
            self.assertIn('data-stair-model-revision="SC-01"', pb_svg)

        def count_class(root: ET.Element, class_name: str) -> int:
            return sum(
                class_name in element.attrib.get("class", "").split()
                for element in root.iter()
            )

        self.assertEqual(count_class(pb_root, "d048-column-reservation"), 4)
        self.assertEqual(count_class(p2_root, "d048-column-reservation"), 4)
        self.assertEqual(count_class(pb_root, "stair-tread"), 20)
        self.assertEqual(count_class(p2_root, "stair-tread"), 20)

    def test_p2_delta_hash_and_shared_source_are_traceable(self):
        delta = json.loads(P2_DELTA.read_text(encoding="utf-8"))
        self.assertEqual(delta["stair_core"], "dreamhouse/stair_core.json")
        self.assertEqual(delta["decision"], "D-074")
        self.assertTrue(math.isfinite(derived_stair_values(self.stair)["riser"]))


if __name__ == "__main__":
    unittest.main()

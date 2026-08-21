from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b24 import load_b24_model
from dreamhouse.generate_pb_b34 import generate, load_b34_model, validate_b34


class TestPBB34(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b34_model()
        cls.checks = validate_b34(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_restored_domestic_relationship_is_exact(self):
        dining = self.model["social_layout"]["dining"]
        kitchen = self.model["kitchen"]
        self.assertEqual(dining["centre"], {"x": 26.25, "y": 14.41})
        self.assertEqual(dining["table"]["length"], 3.2)
        self.assertEqual(dining["table"]["depth"], 1.1)
        self.assertEqual(dining["seat_count"], 12)
        self.assertEqual(dining["chairs_per_side"], 5)
        self.assertEqual(dining["end_chairs"], 1)
        self.assertEqual(kitchen["wall_run"]["length"], 10.05)
        self.assertEqual(kitchen["island"]["length"], 7.2)
        self.assertEqual(self.by_rule["PB34-D077-DOMESTIC-GEOMETRY"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB34-DOMESTIC-CORE-SEPARATION"]["status"], "PASS")

    def test_car_lift_and_stair_are_integrated_without_regression(self):
        layout = self.model["car_lift_layout"]
        p2 = load_b24_model()
        self.assertEqual(layout["centre"], {"x": 5.34, "y": 3.965})
        self.assertEqual((layout["front_residual"], layout["rear_residual"]), (1.96, 1.96))
        self.assertEqual(self.by_rule["PB34-STAIR-SHARED-FOOTPRINT"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB34-STAIR-ACCESS-FLIGHT"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB34-STAIR-FOUR-COLUMN-SYNC"]["status"], "PASS")
        self.assertEqual(
            {
                (item["id"], item["x"], item["y"])
                for item in self.model["structural_reservations"]
            },
            {
                (item["id"], item["x"], item["y"])
                for item in p2["structural_reservations"]
            },
        )
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_adoption_closes_only_the_schematic_owner_selection_gate(self):
        self.assertEqual(self.by_rule["PB-KD-OWNER-SELECTION"]["status"], "PASS")
        for rule_id in (
            "PB-KD-APPLIANCE-MEP",
            "PB-KD-DINING-DAYLIGHT",
            "PB-KD-DINING-PRODUCT-SELECTION",
            "PB-CAR-LIFT-REAL-EQUIPMENT",
            "STAIR-HEADROOM",
            "STAIR-REAR-DISCHARGE-LEVEL",
        ):
            self.assertEqual(self.by_rule[rule_id]["status"], "OPEN")

    def test_generated_plan_is_traceable_and_contains_required_symbols(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual((report["passed"], report["failed"]), (73, 0))
            plan_path = target / "DH-ARQ-PLN-001-R12_PB-INTEGRATED-RESTORATION.svg"
            plan = plan_path.read_text(encoding="utf-8")
            root = ET.fromstring(plan)
            self.assertIn("RESTORED DOMESTIC LAYOUT", plan)
            self.assertIn("DINING OPPOSITE KITCHEN", plan)
            self.assertIn("7.20 m FULL-SPAN ISLAND", plan)
            self.assertIn("UP TO P2", plan)
            self.assertIn('data-stair-model-revision="SC-01"', plan)
            self.assertNotIn("PB b29 remains current", plan)

            def count_class(class_name: str) -> int:
                return sum(
                    class_name in element.attrib.get("class", "").split()
                    for element in root.iter()
                )

            self.assertEqual(count_class("d048-column-reservation"), 4)
            self.assertEqual(count_class("stair-tread"), 20)

            manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-34-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b34_delta.json")
            self.assertEqual(manifest["base_source"], "dreamhouse/pb_b32_delta.json")
            self.assertEqual(manifest["shared_stair_source"], "dreamhouse/stair_core.json")


if __name__ == "__main__":
    unittest.main()

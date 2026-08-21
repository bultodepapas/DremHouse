from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import (
    build_acoustic_partition_detail,
    build_exterior_wall_detail,
    build_plan,
    generate,
    net_area,
    validate_model,
)
from dreamhouse.generate_p2_b25 import DELTA, load_b25_model


class TestP2B25(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b25_model()
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)

    def test_wall_schedule_uses_differentiated_realistic_thicknesses(self):
        expected = {
            "P2-W01A": 0.09,
            "P2-W01B": 0.20,
            "P2-W02": 0.15,
            "P2-W02S": 0.20,
            "P2-W03": 0.20,
            "P2-W04R": 0.20,
            "P2-W05": 0.23,
            "P2-W06": 0.09,
        }
        self.assertEqual(
            {key: value["nominal_total_m"] for key, value in self.model["wall_schedule"].items()},
            expected,
        )
        self.assertEqual(self.model["acoustic_partition"]["id"], "P2-W01B")
        self.assertEqual(self.model["internal_partition"]["id"], "P2-W01A")

    def test_new_wall_checks_pass_without_claiming_ratings(self):
        by_rule = {item["rule_id"]: item for item in self.checks}
        for rule_id in ("P2-WALL-SCHEDULE", "P2-W01A-090", "P2-W01B-200", "P2-W05-230"):
            self.assertEqual(by_rule[rule_id]["status"], "PASS")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        self.assertIn("No acoustic, fire, structural or moisture rating is claimed", build_acoustic_partition_detail(self.model))
        self.assertIn("No U-value, fire, acoustic or structural rating is claimed", build_exterior_wall_detail(self.model))

    def test_net_area_uses_actual_scheduled_adjacent_wall_types(self):
        by_id = {item["id"]: item for item in self.model["spaces"]}
        current = net_area(by_id["H1-D"], self.model["envelope"], self.model)
        generic = net_area(by_id["H1-D"], self.model["envelope"])
        self.assertNotAlmostEqual(current, generic)
        self.assertGreater(current, 0.0)

    def test_drawings_and_manifest_are_deterministic(self):
        self.assertEqual(self.plan, build_plan(self.model))
        ET.fromstring(self.plan)
        ET.fromstring(build_acoustic_partition_detail(self.model))
        ET.fromstring(build_exterior_wall_detail(self.model))
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(
                self.model,
                target,
                source_path=DELTA,
                generator_name="dreamhouse/generate_p2_b25.py",
            )
            self.assertEqual(report["failed"], 0)
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-25-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b25_delta.json")


if __name__ == "__main__":
    unittest.main()

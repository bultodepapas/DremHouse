from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b27 import generate, load_b27_model, validate_b27


class TestPBB27(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b27_model()
        cls.checks = validate_b27(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_tv_is_on_side_b_perimeter_wall_without_internal_partition(self):
        media = self.model["social_layout"]["media_wall"]
        self.assertEqual(media["mounting"], "side_b_perimeter")
        self.assertEqual(media["side"], "B")
        self.assertAlmostEqual(media["y"], 17.82)
        self.assertNotIn("x", media)
        self.assertEqual(self.by_rule["PB-TV-SIDE-B-PERIMETER"]["status"], "PASS")

    def test_living_clears_axis_and_workstation_2(self):
        self.assertEqual(self.by_rule["PB-SOCIAL-AXIS-CLEAR"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-SOCIAL-WORKSTATION-CLEAR"]["status"], "PASS")

    def test_tv_geometry_view_and_dining_pass(self):
        self.assertEqual(self.by_rule["PB-TV-100-IN-ENVELOPE"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-TV-VIEWING-DISTANCE"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-DINING-INDEPENDENT"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-SIDE-B-SOLID-HALL-BAY"]["status"], "PASS")

    def test_professional_interfaces_remain_open_without_failures(self):
        for rule_id in (
            "PB-TV-PERIMETER-BACKING",
            "PB-TV-AV-MEP",
            "PB-TV-GLARE-SIDE-B",
        ):
            self.assertEqual(self.by_rule[rule_id]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_drawings_state_the_corrected_wall_relationship(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-R08_PB-SIDE-B-WALL-TV-LIVING.svg"
            ).read_text(encoding="utf-8")
            media = target.joinpath(
                "DH-ARQ-ELE-INT-002-R01_PB-100IN-SIDE-B-WALL.svg"
            ).read_text(encoding="utf-8")
            self.assertIn("100-IN TV · SIDE B WALL", plan)
            self.assertIn("LIVING / 100-IN TV LOUNGE", plan)
            self.assertIn("12-SEAT DINING", plan)
            self.assertNotIn("DINING SIDEBOARD", plan)
            self.assertNotIn("100-IN TV / MEDIA WALL", plan)
            self.assertIn("DIRECTLY ON SIDE B PERIMETER WALL", media)
            self.assertIn("NO INTERNAL MEDIA PARTITION", media)
            self.assertIn("ELE-INT-002-R01", media)

    def test_manifest_and_svg_outputs_are_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(self.model, target)
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-27-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b27_delta.json")
            for filename in manifest["outputs"]:
                if filename.endswith(".svg"):
                    ET.fromstring(target.joinpath(filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

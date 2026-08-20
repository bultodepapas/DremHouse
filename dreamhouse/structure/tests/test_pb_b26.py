from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b26 import generate, load_b26_model, validate_b26


class TestPBB26(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b26_model()
        cls.checks = validate_b26(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_living_furniture_and_media_wall_clear_the_axis(self):
        self.assertEqual(self.by_rule["PB-SOCIAL-AXIS-CLEAR"]["status"], "PASS")
        self.assertEqual(
            self.by_rule["PB-SOCIAL-WORKSTATION-CLEAR"]["status"], "PASS"
        )
        self.assertEqual(self.by_rule["PB-MEDIA-WALL-P2-EDGE"]["status"], "PASS")

    def test_100_inch_tv_and_viewing_distance_are_geometrically_consistent(self):
        media = self.model["social_layout"]["media_wall"]
        self.assertEqual(media["tv_diagonal_inches"], 100.0)
        self.assertAlmostEqual(media["tv_width"], 2.214, places=3)
        self.assertAlmostEqual(media["tv_height"], 1.245, places=3)
        self.assertEqual(self.by_rule["PB-TV-100-IN-ENVELOPE"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-TV-VIEWING-DISTANCE"]["status"], "PASS")

    def test_dining_hinge_and_solid_side_b_bay_pass(self):
        self.assertEqual(self.by_rule["PB-DINING-HINGE"]["status"], "PASS")
        self.assertEqual(
            self.by_rule["PB-SIDE-B-SOLID-HALL-BAY"]["status"], "PASS"
        )

    def test_professional_media_interfaces_remain_explicitly_open(self):
        for rule_id in (
            "PB-TV-MEDIA-WALL-STRUCTURE",
            "PB-TV-AV-MEP",
            "PB-TV-GLARE-PRIMARY-GLAZING",
        ):
            self.assertEqual(self.by_rule[rule_id]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_drawings_replace_legacy_social_symbols(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-R07_PB-LIVING-DINING-MEDIA.svg"
            ).read_text(encoding="utf-8")
            side_b = target.joinpath(
                "DH-ARQ-ELE-004-R09_SIDE-B-SOLID-HALL-BAY.svg"
            ).read_text(encoding="utf-8")
            media = target.joinpath(
                "DH-ARQ-ELE-INT-002-R00_PB-100IN-MEDIA-WALL.svg"
            ).read_text(encoding="utf-8")
            self.assertIn("LIVING / 100-IN TV LOUNGE", plan)
            self.assertIn("100-IN TV / MEDIA WALL", plan)
            self.assertIn("12-SEAT DINING", plan)
            self.assertNotIn("LOUNGE / TRANSITION", plan)
            self.assertNotIn(">CENTRE</text>", plan)
            self.assertNotIn("SITE-DEPENDENT ALTERNATIVE", side_b)
            self.assertIn("100-IN TV EQUIPMENT ENVELOPE", media)
            self.assertIn("ELE-INT-002-R00", media)

    def test_manifest_and_svg_outputs_are_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(self.model, target)
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-26-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b26_delta.json")
            for filename in manifest["outputs"]:
                if filename.endswith(".svg"):
                    ET.fromstring(target.joinpath(filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

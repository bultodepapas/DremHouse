from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_rooflight_b11 import (
    DATA,
    OUT,
    PLAN_NAME,
    SECTION_NAME,
    center,
    generate,
    group_center,
    plan,
    section,
    validate,
)

ROOT = Path(__file__).resolve().parents[3]


class TestRooflightB11(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = json.loads(DATA.read_text(encoding="utf-8"))
        cls.pb = json.loads((ROOT / "dreamhouse" / "pb_b05.json").read_text(encoding="utf-8"))
        cls.checks = validate(cls.model, cls.pb)
        cls.report = {
            "passed": sum(item["status"] == "PASS" for item in cls.checks),
            "open": sum(item["status"] == "OPEN" for item in cls.checks),
            "failed": sum(item["status"] == "FAIL" for item in cls.checks),
        }

    def test_group_is_exactly_centered_over_double_height(self):
        self.assertEqual(center(self.model), (10.5, 9.0))
        self.assertEqual(group_center(self.model), center(self.model))
        self.assertEqual(self.report, {"passed": 7, "open": 3, "failed": 0})

    def test_generator_fails_closed_outside_tolerance(self):
        invalid = copy.deepcopy(self.model)
        invalid["rooflights"][0]["x"] -= 0.21
        invalid["rooflights"][1]["x"] -= 0.21
        with (
            tempfile.TemporaryDirectory() as temporary,
            self.assertRaisesRegex(ValueError, "centre X"),
        ):
            generate(invalid, Path(temporary))

    def test_issued_drawings_are_valid_and_deterministic(self):
        plan_svg = plan(self.model, self.report)
        section_svg = section(self.model)
        ET.fromstring(plan_svg)
        ET.fromstring(section_svg)
        self.assertEqual(OUT.joinpath(PLAN_NAME).read_text(encoding="utf-8"), plan_svg)
        self.assertEqual(OUT.joinpath(SECTION_NAME).read_text(encoding="utf-8"), section_svg)
        self.assertEqual(plan_svg.count('class="central-rooflight"'), 2)
        self.assertEqual(section_svg.count('class="central-rooflight-section"'), 2)


if __name__ == "__main__":
    unittest.main()

"""Rooflight changes reach real sheet geometry and dimensions; old issues stay reproducible."""

import json
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from dreamhouse import generate_rooflight_b11 as renderer
from dreamhouse.coordination.model import ROOT


class RoofDrawingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roof = json.loads((ROOT / "dreamhouse/rooflight_b12.json").read_text())
        cls.pb = json.loads((ROOT / "dreamhouse/pb_b05.json").read_text())

    def test_changed_dimensions_coordinates_and_areas_reach_both_projections(self):
        changed = deepcopy(self.roof)
        light = changed["rooflights"][0]
        light.update(x=6.0, y=7.0, length=4.2, width=2.1, area=8.82)
        with patch.object(Path, "read_text", side_effect=AssertionError("hidden file reload")):
            checks = renderer.validate(changed, self.pb, parameterize=True)
            plan = renderer.plan(changed, {"passed": 0, "failed": 0, "open": 0}, parameterize=True)
            section = renderer.section(changed, parameterize=True)
        self.assertIn("4.20 x 2.10 m", plan)
        rect = next(e for e in ET.fromstring(plan).iter() if e.get("data-entity-id") == light["id"])
        self.assertAlmostEqual(float(rect.get("x")), 95 + 6 * 36)
        self.assertAlmostEqual(float(rect.get("width")), 4.2 * 36)
        self.assertIn("X=6.00–10.20 m", section)
        self.assertIn("Y=7.00–9.10 m", section)
        self.assertIn("8.82 m2", section)
        line = next(
            e for e in ET.fromstring(section).iter() if e.get("data-entity-id") == light["id"]
        )
        self.assertAlmostEqual(float(line.get("x2")) - float(line.get("x1")), 2.1 * 62)
        self.assertEqual(next(c for c in checks if c["rule_id"] == "RL-AREA")["status"], "PASS")
        light["area"] = 11.52
        checks = renderer.validate(changed, self.pb, parameterize=True)
        self.assertEqual(next(c for c in checks if c["rule_id"] == "RL-AREA")["status"], "FAIL")

    def test_original_leaf_defaults_preserve_published_b11_sheets(self):
        original = json.loads(renderer.DATA.read_text())
        checks = renderer.validate(original, self.pb)
        report = {
            key: sum(c["status"] == status for c in checks)
            for key, status in (("passed", "PASS"), ("failed", "FAIL"), ("open", "OPEN"))
        }
        self.assertEqual(
            renderer.plan(original, report), (renderer.OUT / renderer.PLAN_NAME).read_text()
        )
        self.assertEqual(
            renderer.section(original), (renderer.OUT / renderer.SECTION_NAME).read_text()
        )

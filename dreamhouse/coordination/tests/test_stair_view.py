"""Cross-level envelopes respond to source changes while missing discharge stays absent."""

import unittest
from copy import deepcopy
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import resolve_project
from dreamhouse.coordination.rules import evaluate
from dreamhouse.coordination.stair_view import render_stair_section
from dreamhouse.coordination.view_contract import inspect_views


class StairViewTests(unittest.TestCase):
    def test_stair_rise_anchors_and_access_datum_follow_same_snapshot(self):
        baseline = resolve_project()
        changed = deepcopy(baseline)
        changed["entities"]["ST-F1"]["geometry"]["z1"] = 2.0
        changed["entities"]["D-STAIR"]["geometry"]["z0"] = 3.9
        for snapshot, expected in [(baseline, 1.9), (changed, 2.0)]:
            svg = render_stair_section(snapshot, evaluate(snapshot))
            inventory = inspect_views(snapshot, {"stair-sections.svg": svg})
            view = inventory["views"][0]
            rise = next(d for d in view["dimensions"] if d["dimension_id"] == "ST-F1.rise")
            self.assertAlmostEqual(rise["measurement_check"]["measured_m"], expected)
            self.assertEqual(rise["label_check"]["state"], "evaluated")
            self.assertTrue(
                all(a["source_check"]["state"] == "evaluated" for a in view["anchors"].values())
            )
            self.assertEqual(
                {o["entity_id"] for o in view["occurrences"]},
                {"ST-F1", "ST-F2", "ST-L1", "D-STAIR"},
            )
            self.assertIn("EXT-ESC remains unlocated", svg)
            self.assertNotIn('data-entity-id="EXT-ESC"', svg)
        self.assertIn("D-STAIR floor +3.90 m", svg)
        self.assertIn("FAIL · SC01-CROSS-LEVEL-DATUMS", svg)

    def test_missing_geometry_never_creates_stair_or_exit(self):
        snapshot = resolve_project()
        for identifier in ["ST-F1", "ST-F2", "ST-L1"]:
            snapshot["entities"][identifier]["geometry"]["z0"] = None
        svg = render_stair_section(snapshot, evaluate(snapshot))
        self.assertIn("no stair section inferred", svg)
        root = ET.fromstring(svg)
        self.assertFalse(any(e.get("data-entity-id") for e in root.iter()))

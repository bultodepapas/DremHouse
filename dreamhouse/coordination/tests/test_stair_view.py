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

    def test_review_header_roles_counts_and_links_preserve_stair_cues(self):
        snapshot = resolve_project()
        evaluation = evaluate(snapshot)
        root = ET.fromstring(render_stair_section(snapshot, evaluation))
        self.assertEqual(root.get("data-visual-language-version"), "connected-atlas-1")
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}title"))
        self.assertIsNotNone(root.find("{http://www.w3.org/2000/svg}desc"))

        roles = {node.get("data-legend-role") for node in root.iter() if node.get("data-legend-role")}
        self.assertTrue(
            {
                "geometry.structure-envelope",
                "representation.context",
                "access-floor-datum-only",
                "selection.focus",
            }.issubset(roles)
        )
        style = "".join(
            node.text or ""
            for node in root.iter()
            if node.tag == "{http://www.w3.org/2000/svg}style"
        )
        self.assertIn(".entity-occurrence.is-selected .entity-shape", style)
        flight = next(node for node in root.iter() if node.get("data-entity-id") == "ST-F1")
        shape = next(node for node in flight.iter() if node.get("class") == "entity-shape")
        self.assertEqual(shape.get("stroke"), "#1D7480")
        self.assertEqual(shape.get("stroke-width"), "5")
        self.assertNotEqual(shape.get("stroke"), "#2454A6")

        visible_ids = {"ST-F1", "ST-F2", "ST-L1", "D-STAIR"}
        records = [
            finding
            for finding in evaluation["findings"]
            if str(finding.get("status", "")).upper() in {"OPEN", "FAIL"}
        ]
        local = [
            finding
            for finding in records
            if visible_ids.intersection(finding.get("entity_ids", []))
        ]
        self.assertEqual(root.get("data-local-open-count"), str(sum(f["status"] == "OPEN" for f in local)))
        self.assertEqual(root.get("data-local-fail-count"), str(sum(f["status"] == "FAIL" for f in local)))
        self.assertEqual(root.get("data-project-open-count"), str(sum(f["status"] == "OPEN" for f in records)))
        self.assertEqual(root.get("data-project-fail-count"), str(sum(f["status"] == "FAIL" for f in records)))
        links = [
            node
            for node in root.iter()
            if node.tag == "{http://www.w3.org/2000/svg}a"
        ]
        finding_links = [node for node in links if node.get("data-finding-index") is not None]
        self.assertEqual(len(finding_links), len(local))
        self.assertTrue(all(node.get("href", "").startswith("index.html#html-finding-") for node in finding_links))
        self.assertTrue(
            any(node.get("href") == "index.html#project-finding-register" for node in links)
        )

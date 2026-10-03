"""PB wall context dimensions bind native graphics to resolved sources."""

from __future__ import annotations

import math
import unittest
from copy import deepcopy
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import CoordinationError, resolve_project
from dreamhouse.coordination.view_contract import inspect_views
from dreamhouse.coordination.wall_context_annotations import (
    GREAT_WALL,
    PB_MEDIA_WALL,
    annotate_wall_context,
    audit_wall_context,
    render_wall_context,
)

SVG_NS = "http://www.w3.org/2000/svg"


class WallContextAnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = resolve_project()

    def render(self, snapshot, view_id):
        svg = render_wall_context(snapshot, view_id)
        self.assertIsNotNone(svg)
        root = ET.fromstring(svg)
        root.set("data-view-id", view_id)
        return root

    def test_both_views_publish_measured_source_context_dimensions(self):
        expected = {GREAT_WALL: (6, 12), PB_MEDIA_WALL: (5, 10)}
        for view_id, (dimensions, anchors) in expected.items():
            with self.subTest(view_id=view_id):
                root = self.render(self.snapshot, view_id)
                self.assertEqual(audit_wall_context(self.snapshot, root)["state"], "evaluated")
                result = annotate_wall_context(self.snapshot, root)
                self.assertEqual(result["status"], "supported")
                self.assertEqual(result["dimensions"], dimensions)
                self.assertEqual(result["anchors"], anchors)
                inventory = inspect_views(
                    self.snapshot,
                    {f"drawings/{view_id}.svg": ET.tostring(root, encoding="unicode")},
                )
                coverage = inventory["annotation_coverage"]
                self.assertEqual(coverage["source_bound_anchors"], anchors)
                self.assertEqual(coverage["evaluated_dimensions"], dimensions)
                self.assertEqual(coverage["verified_dimension_labels"], dimensions)

    def test_great_wall_height_and_unresolved_core_doors_are_explicit(self):
        root = self.render(self.snapshot, GREAT_WALL)
        audit = audit_wall_context(self.snapshot, root)
        self.assertEqual(audit["unresolved_references"]["height"]["state"], "unavailable")
        self.assertIn(
            "no source field defines", audit["unresolved_references"]["height"]["reason"].lower()
        )
        unresolved = audit["unresolved_references"]["doors"]["entity_ids"]
        self.assertEqual(len(unresolved), 5)
        self.assertIn(
            "Continuous architectural finish across the core zones; door positions remain unresolved under CF-013.",
            "".join(root.itertext()),
        )
        self.assertEqual(audit["unresolved_references"]["doors"]["conflict_id"], "CF-013")
        self.assertEqual(
            [
                node.text
                for node in root.iter(f"{{{SVG_NS}}}text")
                if node.get("data-context-feature") == "great-wall-height-unresolved"
            ],
            ["HEIGHT NOT SOURCE-DEFINED · VERTICAL PROFILE IS SCHEMATIC"],
        )
        door_shapes = [
            node
            for node in root.iter(f"{{{SVG_NS}}}rect")
            if node.get("fill") in {"none", "#806044"}
        ]
        self.assertEqual(door_shapes, [])
        self.assertNotIn("great-wall-height", [feature["id"] for feature in audit["features"]])

    def test_great_wall_renderer_updates_core_spans_from_current_source(self):
        changed = deepcopy(self.snapshot)
        core = changed["discipline_inputs"]["equipment"]["pb"]["core"]
        core[0]["y1"] = 2.6
        core[1]["y0"] = 2.6
        root = self.render(changed, GREAT_WALL)
        self.assertEqual(audit_wall_context(changed, root)["state"], "evaluated")
        boundary = next(
            node
            for node in root.iter(f"{{{SVG_NS}}}line")
            if node.get("stroke") == "#725238"
            and math.isclose(float(node.get("x1")), 120 + 2.6 * 63, abs_tol=1e-6)
        )
        self.assertAlmostEqual(float(boundary.get("x2")), 120 + 2.6 * 63)
        labels = [
            node.text
            for node in root.iter(f"{{{SVG_NS}}}text")
            if math.isclose(float(node.get("y", "nan")), 716, abs_tol=1e-6)
        ]
        self.assertIn("2,60", labels)
        self.assertIn("4,80", labels)

    def test_great_wall_graphic_fails_when_source_bound_core_span_drifts(self):
        root = self.render(self.snapshot, GREAT_WALL)
        changed = deepcopy(self.snapshot)
        core = changed["discipline_inputs"]["equipment"]["pb"]["core"]
        core[0]["y1"] = 2.3
        core[1]["y0"] = 2.3
        with self.assertRaisesRegex(CoordinationError, "projection mismatch"):
            audit_wall_context(changed, root)

    def test_media_wall_snapshot_changes_render_and_native_drift_is_rejected(self):
        changed = deepcopy(self.snapshot)
        media = changed["discipline_inputs"]["equipment"]["pb"]["social_layout"]["media_wall"]
        media["tv_width"] = 2.30
        media["tv_height"] = 1.29
        fresh = self.render(changed, PB_MEDIA_WALL)
        self.assertEqual(audit_wall_context(changed, fresh)["state"], "evaluated")

        stale = self.render(self.snapshot, PB_MEDIA_WALL)
        with self.assertRaisesRegex(CoordinationError, "projection mismatch|label disagrees"):
            audit_wall_context(changed, stale)

    def test_media_wall_uses_source_tv_specification_and_equipment_positions(self):
        changed = deepcopy(self.snapshot)
        media = changed["discipline_inputs"]["equipment"]["pb"]["social_layout"]["media_wall"]
        media["tv_diagonal_inches"] = 85
        media["tv_aspect_ratio"] = "21:9"
        media["tv_center_x"] = 19.0
        media["console"]["x"] = 17.1
        media["console"]["length"] = 3.5
        media["height"] = 4.0

        root = self.render(changed, PB_MEDIA_WALL)
        self.assertEqual(audit_wall_context(changed, root)["state"], "evaluated")
        text_by_feature = {
            node.get("data-context-feature"): "".join(node.itertext()).strip()
            for node in root.iter(f"{{{SVG_NS}}}text")
        }
        self.assertEqual(
            text_by_feature["pb-media-tv-specification"], "85-IN TV EQUIPMENT ENVELOPE"
        )
        self.assertEqual(text_by_feature["pb-media-title"], "PB LIVING / 85-INCH TV ON SIDE B WALL")
        self.assertEqual(
            text_by_feature["pb-media-tv-envelope-dimensions"],
            "2.21 × 1.25 m · 21:9",
        )
        self.assertEqual(
            text_by_feature["pb-media-tv-center-height-label"],
            "TV CENTRE +1.25 m AFF",
        )
        self.assertEqual(
            text_by_feature["pb-media-console-length-label"], "3.50 m ACCESSIBLE AV CONSOLE"
        )
        self.assertEqual(
            text_by_feature["pb-media-mounting-field-width-label"],
            "4.40 m MOUNTING FIELD · DIRECTLY ON SIDE B PERIMETER WALL",
        )
        self.assertEqual(text_by_feature["pb-media-mounting-field-height-label"], "4.00 m")

        tv = next(node for node in root.iter(f"{{{SVG_NS}}}rect") if node.get("fill") == "#172126")
        self.assertAlmostEqual(float(tv.get("x")), 70 + (19.0 - 16.4 - 2.214 / 2) * 150)
        console = next(
            node for node in root.iter(f"{{{SVG_NS}}}rect") if node.get("fill") == "#6f543e"
        )
        self.assertAlmostEqual(float(console.get("x")), 70 + (17.1 - 16.4) * 150)

        annotate_wall_context(changed, root)
        inventory = inspect_views(
            changed,
            {f"drawings/{PB_MEDIA_WALL}.svg": ET.tostring(root, encoding="unicode")},
        )
        coverage = inventory["annotation_coverage"]
        self.assertEqual(coverage["verified_dimension_labels"], coverage["dimensions"])

    def test_media_wall_rejects_corrupt_tv_center_and_height_labels(self):
        for feature, bad_text in (
            ("pb-media-tv-center-height-label", "TV CENTRE +9.99 m AFF"),
            ("pb-media-mounting-field-height-label", "9.99 m"),
        ):
            with self.subTest(feature=feature):
                root = self.render(self.snapshot, PB_MEDIA_WALL)
                annotate_wall_context(self.snapshot, root)
                label = next(
                    node
                    for node in root.iter(f"{{{SVG_NS}}}text")
                    if node.get("data-context-feature") == feature
                )
                label.text = bad_text
                with self.assertRaisesRegex(CoordinationError, "label disagrees"):
                    audit_wall_context(self.snapshot, root)

    def test_media_wall_rejects_inconsistent_distance_and_graphic_edits(self):
        changed = deepcopy(self.snapshot)
        media = changed["discipline_inputs"]["equipment"]["pb"]["social_layout"]["media_wall"]
        media["viewing_distance"] = 5.0
        with self.assertRaisesRegex(CoordinationError, "viewing distance disagrees"):
            render_wall_context(changed, PB_MEDIA_WALL)

        root = self.render(self.snapshot, PB_MEDIA_WALL)
        field = next(
            node for node in root.iter(f"{{{SVG_NS}}}rect") if node.get("fill") == "#c6a37b"
        )
        field.set("width", str(float(field.get("width")) + 1.0))
        with self.assertRaisesRegex(CoordinationError, "projection mismatch"):
            audit_wall_context(self.snapshot, root)

    def test_transformed_feature_ancestry_is_rejected(self):
        root = self.render(self.snapshot, PB_MEDIA_WALL)
        field = next(
            node for node in root.iter(f"{{{SVG_NS}}}rect") if node.get("fill") == "#c6a37b"
        )
        parent = next(node for node in root.iter() if field in list(node))
        parent.set("transform", "translate(1 0)")
        with self.assertRaisesRegex(CoordinationError, "Transformed wall context"):
            audit_wall_context(self.snapshot, root)

    def test_unrecognized_view_is_not_claimed(self):
        self.assertIsNone(render_wall_context(self.snapshot, "architecture-side-a-elevation"))
        self.assertIsNone(audit_wall_context(self.snapshot, ET.Element(f"{{{SVG_NS}}}svg")))


if __name__ == "__main__":
    unittest.main()

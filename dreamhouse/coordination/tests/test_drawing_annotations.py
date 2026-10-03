"""Native dimensions remain bound to source geometry and rendered features."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.coordination.drawing_annotations import (
    NATIVE_VIEW_PROJECTIONS,
    audit_native_geometry,
)
from dreamhouse.coordination.drawings import render_drawings
from dreamhouse.coordination.model import (
    CoordinationError,
    json_text,
    resolve_project,
    study_template,
)
from dreamhouse.coordination.view_contract import inspect_views

SVG_NS = "http://www.w3.org/2000/svg"


class NativeDrawingAnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = resolve_project()

    def resolve_study(self, scenario_id: str, changes: dict) -> dict:
        document = study_template(self.snapshot, scenario_id)
        for entity_id, setters in changes.items():
            parameters = self.snapshot["entities"][entity_id]["parameters"]
            document["changes"][entity_id] = {
                "expected": {field: parameters[field] for field in setters},
                "set": setters,
            }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "study.json"
            path.write_text(json_text(document), encoding="utf-8")
            return resolve_project(path)

    @staticmethod
    def dimension_labels(svg: str) -> dict[str, str]:
        root = ET.fromstring(svg)
        return {
            node.get("data-dimension-id"): "".join(node.itertext()).strip()
            for node in root.iter()
            if node.get("data-dimension-id")
        }

    def test_public_render_and_view_inventory_report_real_annotation_coverage(self):
        rendered = render_drawings(self.snapshot, {})
        svg_files = {
            path: content
            for path, content in rendered["files"].items()
            if path.endswith(".svg")
        }
        inspected = inspect_views(self.snapshot, svg_files)
        coverage = rendered["inventory"]["annotation_migration"]
        rows = rendered["inventory"]["drawings"]
        by_id = {row["id"]: row for row in rows}

        self.assertEqual(set(by_id), {row["id"] for row in self.snapshot["drawing_catalog"]["drawings"]})
        self.assertEqual(set(coverage["supported_sheets"]), set(NATIVE_VIEW_PROJECTIONS))
        self.assertEqual(coverage["supported_sheet_count"], len(NATIVE_VIEW_PROJECTIONS))
        self.assertEqual(coverage["named_dimension_count"], 30)
        self.assertEqual(len(rows), 27)

        for row in rows:
            annotation = row["annotation_coverage"]
            self.assertIn(annotation["status"], {"supported", "unsupported", "not_applicable"})
            if annotation["status"] == "supported":
                self.assertEqual(annotation["geometry_binding"]["state"], "evaluated")
                self.assertGreater(annotation["dimensions"], 0)
                self.assertIsNone(annotation["reason"])
            else:
                self.assertTrue(annotation["reason"])
                self.assertEqual(annotation["dimensions"], 0)

        audited_views = {view["view_id"]: view for view in inspected["views"]}
        for view_id in NATIVE_VIEW_PROJECTIONS:
            view = audited_views[view_id]
            self.assertTrue(view["dimensions"])
            self.assertTrue(view["anchors"])
            labels = self.dimension_labels(svg_files[f"drawings/{view_id}.svg"])
            for dimension in view["dimensions"]:
                self.assertEqual(dimension["measurement_check"]["state"], "evaluated")
                self.assertEqual(dimension["label_check"]["state"], "evaluated")
                self.assertEqual(
                    labels[dimension["dimension_id"]],
                    f'{float(dimension["value"]):.2f} m',
                )

    def test_source_change_updates_the_native_shape_anchor_and_visible_label(self):
        changed = self.resolve_study(
            "FRONT-OPENING-ANNOTATION-STUDY", {"CAR": {"width_m": 4.4}}
        )
        rendered = render_drawings(changed, {})
        svg = rendered["files"]["drawings/architecture-front-elevation.svg"]
        root = ET.fromstring(svg)
        car = next(node for node in root.iter() if node.get("data-entity-id") == "CAR")
        self.assertAlmostEqual(float(car.get("width")), 4.4 * 62)
        self.assertEqual(self.dimension_labels(svg)["CAR.width"], "4.40 m")

        inspected = inspect_views(
            changed,
            {"drawings/architecture-front-elevation.svg": svg},
        )
        view = inspected["views"][0]
        dimension = next(item for item in view["dimensions"] if item["dimension_id"] == "CAR.width")
        self.assertEqual(dimension["measurement_check"]["state"], "evaluated")
        self.assertAlmostEqual(dimension["measurement_check"]["measured_m"], 4.4)
        start, end = [view["anchors"][ref] for ref in dimension["anchor_refs"]]
        self.assertEqual(start["coordinates"]["data-world-y"], "1.2")
        self.assertEqual(end["coordinates"]["data-world-y"], "5.6")
        self.assertEqual(start["source_check"]["state"], "evaluated")
        self.assertEqual(end["source_check"]["state"], "evaluated")

    def test_native_rectangle_must_match_registered_transform_before_annotation(self):
        svg = render_drawings(self.snapshot, {})["files"][
            "drawings/architecture-side-a-elevation.svg"
        ]
        root = ET.fromstring(svg)
        window = next(node for node in root.iter() if node.get("data-entity-id") == "W-H1")
        window.set("x", str(float(window.get("x")) + 1.0))
        with self.assertRaisesRegex(CoordinationError, "Native geometry projection mismatch"):
            audit_native_geometry(self.snapshot, root)
        with self.assertRaisesRegex(CoordinationError, "Native geometry projection mismatch"):
            inspect_views(
                self.snapshot,
                {"drawings/architecture-side-a-elevation.svg": ET.tostring(root, encoding="unicode")},
            )

    def test_transformed_native_feature_is_rejected_before_projection_check(self):
        svg = render_drawings(self.snapshot, {})["files"][
            "drawings/architecture-side-a-elevation.svg"
        ]
        root = ET.fromstring(svg)
        feature = next(node for node in root.iter() if node.get("data-entity-id") == "W-H1")
        parent = next(node for node in root.iter() if feature in list(node))
        parent.set("transform", "translate(1 0)")
        with self.assertRaisesRegex(CoordinationError, "Transformed native geometry"):
            inspect_views(
                self.snapshot,
                {"drawings/architecture-side-a-elevation.svg": ET.tostring(root, encoding="unicode")},
            )


if __name__ == "__main__":
    unittest.main()

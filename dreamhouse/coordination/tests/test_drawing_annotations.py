"""Native dimensions remain bound to source geometry and rendered features."""

from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.coordination.context_annotations import VIEWS as CONTEXT_VIEWS
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
from dreamhouse.coordination.p2_context_annotations import CONTEXT_VIEWS as P2_CONTEXT_VIEWS
from dreamhouse.coordination.view_contract import inspect_views
from dreamhouse.coordination.wall_context_annotations import VIEWS as WALL_CONTEXT_VIEWS

SVG_NS = "http://www.w3.org/2000/svg"
ALL_CONTEXT_VIEWS = CONTEXT_VIEWS | P2_CONTEXT_VIEWS | WALL_CONTEXT_VIEWS


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
        self.assertEqual(set(coverage["supported_sheets"]), set(NATIVE_VIEW_PROJECTIONS) | ALL_CONTEXT_VIEWS)
        self.assertEqual(coverage["supported_sheet_count"], len(NATIVE_VIEW_PROJECTIONS) + len(ALL_CONTEXT_VIEWS))
        self.assertEqual(coverage["named_dimension_count"], 82)
        self.assertEqual(len(rows), 27)

        for row in rows:
            annotation = row["annotation_coverage"]
            self.assertIn(annotation["status"], {"supported", "unsupported", "not_applicable"})
            if annotation["status"] == "supported":
                self.assertEqual(annotation["geometry_binding"]["state"], "evaluated")
                self.assertGreater(annotation["dimensions"] + annotation.get("context_dimensions", 0), 0)
                self.assertIsNone(annotation["reason"])
            else:
                self.assertTrue(annotation["reason"])
                self.assertEqual(annotation["dimensions"], 0)

        audited_views = {view["view_id"]: view for view in inspected["views"]}
        for view_id in NATIVE_VIEW_PROJECTIONS:
            view = audited_views[view_id]
            self.assertTrue(view["dimensions"])
            self.assertTrue(view["anchors"])
            definition = view["definition"]
            projection = NATIVE_VIEW_PROJECTIONS[view_id]
            self.assertEqual(definition["purpose"], projection["view_purpose"])
            self.assertEqual(definition["projection_basis"], projection["projection_basis"])
            self.assertEqual(definition["projected_axes"], projection["projected_axes"])
            self.assertEqual(definition["world_to_view"], projection.get("world_to_view"))
            labels = self.dimension_labels(svg_files[f"drawings/{view_id}.svg"])
            for dimension in view["dimensions"]:
                self.assertEqual(dimension["measurement_check"]["state"], "evaluated")
                self.assertEqual(dimension["label_check"]["state"], "evaluated")
                self.assertEqual(
                    labels[dimension["dimension_id"]],
                    f'{float(dimension["value"]):.2f} m',
                )

    def test_new_native_views_bind_visible_geometry_to_the_current_source(self):
        changed = self.resolve_study("P2-WINDOW-LINE-STUDY", {"W-H1": {"width_m": 3.4}})
        rendered = render_drawings(changed, {})
        plan_svg = rendered["files"]["drawings/architecture-upper-floor.svg"]
        plan_root = ET.fromstring(plan_svg)
        window = next(node for node in plan_root.iter() if node.get("data-entity-id") == "W-H1")
        self.assertAlmostEqual(
            abs(float(window.get("x2")) - float(window.get("x1"))),
            3.4 * 40.0,
        )
        self.assertEqual(self.dimension_labels(plan_svg)["W-H1.width"], "3.40 m")

        detail_svg = rendered["files"]["drawings/architecture-p2-bedroom-windows.svg"]
        detail_root = ET.fromstring(detail_svg)
        window = next(node for node in detail_root.iter() if node.get("data-entity-id") == "W-H1")
        self.assertAlmostEqual(float(window.get("width")), 3.4 * 132.0)
        inspected = inspect_views(
            changed,
            {
                "drawings/architecture-upper-floor.svg": plan_svg,
                "drawings/architecture-p2-bedroom-windows.svg": detail_svg,
            },
        )
        by_id = {item["view_id"]: item for item in inspected["views"]}
        self.assertEqual(by_id["architecture-upper-floor"]["geometry_check"]["state"], "evaluated")
        self.assertEqual(by_id["architecture-p2-bedroom-windows"]["geometry_check"]["state"], "evaluated")

    def test_native_line_occurrences_must_be_present_unique_and_source_projected(self):
        svg = render_drawings(self.snapshot, {})["files"][
            "drawings/architecture-upper-floor.svg"
        ]
        root = ET.fromstring(svg)
        window = next(node for node in root.iter() if node.get("data-entity-id") == "W-H1")
        parent = next(node for node in root.iter() if window in list(node))

        missing_root = deepcopy(root)
        missing_window = next(
            node for node in missing_root.iter() if node.get("data-entity-id") == "W-H1"
        )
        missing_parent = next(node for node in missing_root.iter() if missing_window in list(node))
        missing_parent.remove(missing_window)
        with self.assertRaisesRegex(CoordinationError, "feature set changed|missing"):
            audit_native_geometry(self.snapshot, missing_root)

        duplicate = deepcopy(window)
        duplicate.set("id", "duplicate-native-window")
        parent.append(duplicate)
        with self.assertRaisesRegex(CoordinationError, "occurs more than once"):
            audit_native_geometry(self.snapshot, root)

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

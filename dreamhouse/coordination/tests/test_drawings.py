"""Snapshot-driven rendering propagates current study geometry to drawing views."""

from __future__ import annotations

import builtins
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from dreamhouse.coordination.drawings import render_drawings
from dreamhouse.coordination.model import json_text, resolve_project, study_template

SVG_NS = "http://www.w3.org/2000/svg"


class ConnectedDrawingRendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = resolve_project()

    def resolve_study(self, scenario_id: str, changes: dict) -> dict:
        """Resolve explicit, optimistic changes through the public study API."""
        document = study_template(self.snapshot, scenario_id)
        for entity_id, setters in changes.items():
            parameters = self.snapshot["entities"][entity_id]["parameters"]
            document["changes"][entity_id] = {
                "expected": {field: parameters[field] for field in setters},
                "set": setters,
            }
        with tempfile.TemporaryDirectory() as directory:
            project_path = Path(directory) / "study.json"
            project_path.write_text(json_text(document), encoding="utf-8")
            return resolve_project(project_path)

    @staticmethod
    def svg_texts(svg: str) -> list[str]:
        root = ET.fromstring(svg)
        return ["".join(element.itertext()).strip() for element in root.iter(f"{{{SVG_NS}}}text")]

    def test_catalog_renders_27_consumers_without_io_or_snapshot_mutation(self):
        snapshot_before = deepcopy(self.snapshot)
        expected = {
            f"drawings/{row['id']}.svg" for row in self.snapshot["drawing_catalog"]["drawings"]
        } | {"drawings/index.html"}

        with (
            patch.object(Path, "read_text", side_effect=AssertionError("hidden source reload")),
            patch.object(Path, "read_bytes", side_effect=AssertionError("hidden source reload")),
            patch.object(builtins, "open", side_effect=AssertionError("hidden source reload")),
        ):
            rendered = render_drawings(self.snapshot, {})

        self.assertEqual(self.snapshot, snapshot_before)
        self.assertEqual(set(rendered["files"]), expected)
        self.assertEqual(rendered["inventory"]["drawing_count"], 27)
        self.assertEqual(sum(name.endswith(".svg") for name in rendered["files"]), 27)
        self.assertFalse(rendered["inventory"]["construction_authority"])
        for path, svg in rendered["files"].items():
            if path.endswith(".svg"):
                root = ET.fromstring(svg)
                self.assertTrue(root.get("data-view-id"), path)
                self.assertIsNotNone(root.find(f"{{{SVG_NS}}}title"), path)
                self.assertIn("REVIEW ONLY · NOT DESIGN ADOPTION", "".join(root.itertext()))
        self.assertIn('loading="lazy"', rendered["files"]["drawings/index.html"])
        self.assertIs(
            rendered["structural_screening"]["selection_or_construction_authority"], False
        )

    def test_h2_and_g_detail_rows_keep_their_own_current_dimensions(self):
        cases = (
            ("W-H2", {"width_m": 2.4, "modules": 2}, "2.40 × 2.90 m · 2 modules"),
            ("W-G", {"height_m": 2.6}, "3.60 × 2.60 m · 3 modules"),
        )
        for index, (entity_id, setters, expected_label) in enumerate(cases):
            with self.subTest(entity_id=entity_id):
                changed = self.resolve_study(
                    f"P2-{entity_id}-DRAWING-STUDY-{index}", {entity_id: setters}
                )
                svg = render_drawings(changed, {})["files"][
                    "drawings/architecture-p2-bedroom-windows.svg"
                ]
                texts = self.svg_texts(svg)
                row_index = texts.index(entity_id)
                self.assertEqual(texts[row_index + 1], expected_label)
                h1_index = texts.index("W-H1")
                self.assertEqual(texts[h1_index + 1], "3.60 × 2.90 m · 3 modules")
                self.assertIn("3.60 x 2.90 m · 3 modules", texts)

    def test_workstation_start_and_sill_reach_detail_with_source_gap_range(self):
        changed = self.resolve_study(
            "WORKSTATION-DATUM-DRAWING-STUDY",
            {"GLZ-WS-A": {"start_m": 12.55, "sill_m": 0.8}},
        )
        svg = render_drawings(changed, {})["files"][
            "drawings/architecture-pb-integrated-workstations.svg"
        ]
        texts = self.svg_texts(svg)

        self.assertIn(
            "WINDOW CENTRE X=16.15 m · WORKTOP CENTRE X=15.75 m",
            texts,
        )
        self.assertIn(
            "Current window sill +0.80 m · worktop top +0.75 m · independent structure",
            texts,
        )
        self.assertIn("30–50 mm INDEPENDENT SHADOW / SERVICE GAP", texts)

    def test_rooflight_geometry_updates_native_view_and_structural_screening(self):
        changed = self.resolve_study(
            "ROOFLIGHT-FOOTPRINT-DRAWING-STUDY",
            {
                "RL-CAR": {
                    "x_m": 6.0,
                    "y_m": 6.0,
                    "length_m": 3.0,
                    "width_m": 1.2,
                }
            },
        )
        rendered = render_drawings(changed, {})
        plan = ET.fromstring(rendered["files"]["drawings/architecture-roof-plan.svg"])
        opening = next(
            element for element in plan.iter() if element.get("data-entity-id") == "RL-CAR"
        )
        self.assertAlmostEqual(float(opening.get("x")), 95 + 6.0 * 36)
        self.assertAlmostEqual(float(opening.get("y")), 185 + 6.0 * 36)
        self.assertAlmostEqual(float(opening.get("width")), 3.0 * 36)
        self.assertAlmostEqual(float(opening.get("height")), 1.2 * 36)
        self.assertIn("3.00 x 1.20 m", "".join(plan.itertext()))
        section_text = self.svg_texts(
            rendered["files"]["drawings/architecture-roof-daylight-section.svg"]
        )
        self.assertIn("RL-CAR · X=6.00–9.00 m · Y=6.00–7.20 m · 3.60 m2", section_text)

        roof_screen = rendered["structural_screening"]["checks"]["roof_openings"]
        car_screen = next(
            item for item in roof_screen["conflicts"] if item["rooflight_id"] == "RL-CAR"
        )
        self.assertEqual(car_screen["portal_lines_x_m"], [])
        self.assertEqual(car_screen["purlin_lines_y_m"], [])
        self.assertFalse(car_screen["requires_engineered_trimmers"])
        self.assertEqual(roof_screen["status"], "OPEN")

    def test_front_door_width_height_position_and_sill_reach_the_elevation(self):
        changed = self.resolve_study(
            "FRONT-DOOR-DRAWING-STUDY",
            {"CAR": {"start_m": 2.0, "width_m": 4.4, "height_m": 4.1, "sill_m": 0.25}},
        )
        svg = render_drawings(changed, {})["files"]["drawings/architecture-front-elevation.svg"]
        root = ET.fromstring(svg)
        car = next(element for element in root.iter() if element.get("data-entity-id") == "CAR")

        self.assertAlmostEqual(float(car.get("x")), 264.0)
        self.assertAlmostEqual(float(car.get("width")), 272.8)
        self.assertAlmostEqual(float(car.get("y")), 645 - (0.25 + 4.1) * 62)
        self.assertAlmostEqual(float(car.get("height")), 4.1 * 62)
        self.assertIn("4.40 × 4.10 m · sill +0.25 m", "".join(root.itertext()))

    def test_p2_failure_after_window_move_remains_visible_in_review_sheet(self):
        changed = self.resolve_study("P2-WINDOW-OVERLAP-DRAWING-STUDY", {"W-H1": {"start_m": 31.5}})
        rendered = render_drawings(changed, {})
        svg = rendered["files"]["drawings/architecture-upper-floor.svg"]

        self.assertNotEqual(changed["model_hash"], self.snapshot["model_hash"])
        self.assertIn("FAIL", svg)
        self.assertIn("REVIEW ONLY · NOT DESIGN ADOPTION", svg)
        self.assertFalse(rendered["inventory"]["construction_authority"])


if __name__ == "__main__":
    unittest.main()

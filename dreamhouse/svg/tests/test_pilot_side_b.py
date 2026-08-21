from __future__ import annotations

import json
import unittest
from xml.etree import ElementTree as ET

from dreamhouse.svg import pilot_side_b as pilot
from dreamhouse.svg.sheet import create_document, q


GEOMETRY_ATTRS = {
    "cx",
    "cy",
    "d",
    "height",
    "points",
    "r",
    "rx",
    "ry",
    "width",
    "x",
    "x1",
    "x2",
    "y",
    "y1",
    "y2",
}


def geometry_signature(element: ET.Element) -> tuple:
    attributes = () if element.tag == q("text") else tuple(
        (name, element.attrib[name]) for name in sorted(GEOMETRY_ATTRS & element.attrib.keys())
    )
    return element.tag, attributes, tuple(geometry_signature(child) for child in element)


def visible_text(element: ET.Element) -> str:
    return " ".join(" ".join(element.itertext()).split())


class TestSideBGraphicPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_root = ET.parse(pilot.SOURCE).getroot()
        cls.output_root = pilot.build_svg().getroot()

    def test_source_geometry_is_copied_without_coordinate_changes(self) -> None:
        model = self.output_root.find(f"{q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None
        source_nodes = list(self.source_root)[pilot.SOURCE_CONTENT_START : pilot.SOURCE_CONTENT_END]
        output_nodes = list(model)
        self.assertEqual(len(output_nodes), len(source_nodes))
        self.assertEqual(
            [geometry_signature(node) for node in output_nodes],
            [geometry_signature(node) for node in source_nodes],
        )

    def test_accessibility_status_and_source_metadata_are_explicit(self) -> None:
        root = self.output_root
        self.assertEqual(root.get("role"), "img")
        self.assertEqual(root.get("aria-labelledby"), "gp02-title gp02-desc")
        self.assertEqual(root.get("data-status"), "graphic-pilot-not-current")
        self.assertEqual(root.get("data-construction-authority"), "false")
        metadata = json.loads(root.findtext(q("metadata"), default="{}"))
        self.assertIs(metadata["construction_authority"], False)
        self.assertEqual(metadata["source_sha256"], pilot.sha256(pilot.SOURCE))

    def test_opening_ids_and_source_values_are_retained(self) -> None:
        output_text = visible_text(self.output_root)
        for identifier in ("GLZ-RC", "GLZ-WS-B", "PB-WS-B", "W-H2", "W-G"):
            self.assertIn(identifier, output_text)
        for value in (
            "7.20 × 2.90 m",
            "3.00 × 1.80 m",
            "3.60 × 2.90 m",
            "sill +0.90 m",
            "sill +0.75 m",
            "sill +0.05 m",
            "36.00 m",
        ):
            self.assertIn(value, output_text)

    def test_excluded_dining_study_never_enters_model_geometry(self) -> None:
        model = self.output_root.find(f"{q('g')}[@id='layer-model']")
        status = self.output_root.find(f"{q('g')}[@id='layer-status']")
        self.assertIsNotNone(model)
        self.assertIsNotNone(status)
        assert model is not None and status is not None
        self.assertNotIn("GLZ-DINING-STUDY-B", visible_text(model))
        self.assertIn("NOT ADOPTED", visible_text(status))
        self.assertIn("GLZ-DINING-STUDY-B", visible_text(status))
        self.assertIn("remains solid", visible_text(status))

    def test_each_copied_node_has_a_stable_model_reference(self) -> None:
        model = self.output_root.find(f"{q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None
        self.assertTrue(all(node.get("data-model-id") for node in model))


class TestSharedPilotDocument(unittest.TestCase):
    def test_construction_authority_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "construction_authority"):
            create_document(
                title_id="title",
                desc_id="desc",
                accessible_title="Pilot",
                description="Presentation-only pilot",
                sheet_id="DH-TEST",
                revision="GP00",
                status="not-current",
                metadata={"construction_authority": True},
            )


if __name__ == "__main__":
    unittest.main()

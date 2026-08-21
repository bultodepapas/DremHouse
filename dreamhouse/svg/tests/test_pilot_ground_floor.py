from __future__ import annotations

import json
import unittest
from xml.etree import ElementTree as ET

from dreamhouse.svg import pilot_ground_floor as pilot


SVG_NS = "http://www.w3.org/2000/svg"


def Q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


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
    attributes = () if element.tag == Q("text") else tuple(
        (name, element.attrib[name]) for name in sorted(GEOMETRY_ATTRS & element.attrib.keys())
    )
    return (
        element.tag,
        attributes,
        tuple(geometry_signature(child) for child in element),
    )


def visible_text(element: ET.Element) -> str:
    return " ".join(" ".join(element.itertext()).split())


class TestGroundFloorGraphicPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_root = ET.parse(pilot.SOURCE).getroot()
        cls.output_root = pilot.build_svg().getroot()

    def test_source_geometry_is_copied_without_coordinate_changes(self) -> None:
        model = self.output_root.find(f"{Q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None

        source_nodes = list(self.source_root)[3:247]
        output_nodes = list(model)
        self.assertEqual(len(output_nodes), len(source_nodes))
        self.assertEqual(
            [geometry_signature(node) for node in output_nodes],
            [geometry_signature(node) for node in source_nodes],
        )

    def test_accessibility_status_and_source_metadata_are_explicit(self) -> None:
        root = self.output_root
        self.assertEqual(root.get("role"), "img")
        self.assertEqual(root.get("aria-labelledby"), "gp01-title gp01-desc")
        self.assertEqual(root.get("data-status"), "graphic-pilot-not-current")
        self.assertEqual(root.get("data-construction-authority"), "false")
        metadata = json.loads(root.findtext(Q("metadata"), default="{}"))
        self.assertIs(metadata["construction_authority"], False)
        self.assertEqual(metadata["source_sha256"], pilot.sha256(pilot.SOURCE))

    def test_every_keyed_source_label_is_retained_in_the_sidebar(self) -> None:
        source_text = visible_text(self.source_root)
        sidebar = self.output_root.find(f"{Q('g')}[@id='layer-status']")
        self.assertIsNotNone(sidebar)
        assert sidebar is not None
        sidebar_text = visible_text(sidebar)
        model = self.output_root.find(f"{Q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None
        model_text = visible_text(model)

        for label, code in pilot.KEYED_NOTES.items():
            self.assertIn(label, source_text)
            self.assertIn(label, sidebar_text)
            self.assertIn(code, model_text)

        for label, (code, description, _x, _y) in pilot.RELOCATED_ZONE_NOTES.items():
            self.assertIn(label, source_text)
            self.assertIn(description, sidebar_text)
            self.assertIn(code, model_text)

        for label, (code, description, _new_y) in pilot.CORE_NOTES.items():
            self.assertIn(label, source_text)
            self.assertIn(description, sidebar_text)
            self.assertIn(code, model_text)

    def test_known_low_contrast_label_pairs_are_removed(self) -> None:
        for text in self.output_root.iter(Q("text")):
            self.assertNotIn(text.get("fill", "").lower(), {"#f9f3e8", "#332923"})


if __name__ == "__main__":
    unittest.main()

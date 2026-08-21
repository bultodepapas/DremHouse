from __future__ import annotations

import json
import unittest
from xml.etree import ElementTree as ET

from dreamhouse.svg import pilot_transverse_section as pilot
from dreamhouse.svg.sheet import q


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
    return " ".join(
        " ".join("".join(text.itertext()).split()) for text in element.iter(q("text"))
    )


class TestTransverseSectionGraphicPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_root = ET.parse(pilot.SOURCE).getroot()
        cls.source_group = list(cls.source_root)[1]
        cls.output_root = pilot.build_svg().getroot()

    def test_missing_source_viewbox_is_repaired_only_in_the_pilot_root(self) -> None:
        self.assertIsNone(self.source_root.get("viewBox"))
        self.assertEqual(self.output_root.get("viewBox"), "0 0 1684 1191")
        self.assertEqual(self.output_root.get("preserveAspectRatio"), "xMidYMid meet")

    def test_source_geometry_is_copied_without_coordinate_changes(self) -> None:
        model = self.output_root.find(f"{q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None
        source_nodes = list(self.source_group)[
            pilot.SOURCE_CONTENT_START : pilot.SOURCE_CONTENT_END
        ]
        output_nodes = list(model)
        self.assertEqual(len(output_nodes), 11)
        self.assertEqual(
            [geometry_signature(node) for node in output_nodes],
            [geometry_signature(node) for node in source_nodes],
        )

    def test_accessibility_status_and_source_metadata_are_explicit(self) -> None:
        root = self.output_root
        self.assertEqual(root.get("role"), "img")
        self.assertEqual(root.get("aria-labelledby"), "gp03-title gp03-desc")
        self.assertEqual(root.get("data-status"), "graphic-pilot-not-current")
        self.assertEqual(root.get("data-construction-authority"), "false")
        metadata = json.loads(root.findtext(q("metadata"), default="{}"))
        self.assertIs(metadata["construction_authority"], False)
        self.assertEqual(metadata["source_sha256"], pilot.sha256(pilot.SOURCE))
        self.assertEqual(metadata["decision_ids"], ["D-039", "D-044"])

    def test_source_values_and_provisional_status_are_retained(self) -> None:
        text = visible_text(self.output_root)
        for value in (
            "18.00 m",
            "0.60 m",
            "3.33%",
            "+7.20 m",
            "+7.80 m",
            "+3.80 m",
            "3.05–3.20 m",
            "3.00–3.10 m",
        ):
            self.assertIn(value, text)
        self.assertIn("ACTIVE PROVISIONAL DCV · D-039", text)
        self.assertIn("OPEN · DO NOT FREEZE", text)
        self.assertIn("NOT FOR CONSTRUCTION", text)

    def test_visible_editorial_text_is_english_and_ceiling_is_not_misrepresented(self) -> None:
        text = visible_text(self.output_root)
        for spanish_fragment in (
            "CORTE TRANSVERSAL",
            "Cubierta mono-pendiente",
            "LADO BAJO",
            "LADO ALTO",
            "sentido bajo/alto",
            "NO APTO PARA CONSTRUIR",
        ):
            self.assertNotIn(spanish_fragment, text)
        self.assertIn("horizontal ceiling not shown", text)
        self.assertIn("P2 finished floor · approx. +3.80 m", text)

    def test_each_copied_node_has_a_stable_model_reference(self) -> None:
        model = self.output_root.find(f"{q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None
        self.assertTrue(all(node.get("data-model-id") for node in model))

    def test_level_markers_are_typed_relationships(self) -> None:
        annotations = self.output_root.find(f"{q('g')}[@id='layer-annotations']")
        self.assertIsNotNone(annotations)
        assert annotations is not None
        relationships = {
            group.get("data-relates-to")
            for group in annotations.findall(q("g"))
            if group.get("class") == "level-marker"
        }
        self.assertEqual(relationships, {"PB-REFERENCE-LEVEL", "P2-FLOOR-DATUM"})


if __name__ == "__main__":
    unittest.main()

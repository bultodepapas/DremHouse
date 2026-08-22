from __future__ import annotations

import json
import unittest
from xml.etree import ElementTree as ET

from dreamhouse.svg import pilot_p2_wall_family as pilot
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
        " ".join(" ".join(piece.split()) for piece in text.itertext())
        for text in element.iter(q("text"))
    )


class TestP2WallFamilyGraphicPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_root = ET.parse(pilot.SOURCE).getroot()
        cls.source_children = list(cls.source_root)
        cls.output_root = pilot.build_svg().getroot()

    def test_controlled_build_up_geometry_is_copied_without_coordinate_changes(self) -> None:
        model = self.output_root.find(f"{q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None
        groups = list(model)
        self.assertEqual([group.get("data-model-id") for group in groups], ["P2-W01A", "P2-W01B"])

        for group, source_range in zip(
            groups,
            (pilot.W01A_SOURCE_RANGE, pilot.W01B_SOURCE_RANGE),
            strict=True,
        ):
            source_nodes = [self.source_children[index] for index in source_range]
            self.assertEqual(
                [geometry_signature(node) for node in group],
                [geometry_signature(node) for node in source_nodes],
            )

    def test_accessibility_status_and_source_metadata_are_explicit(self) -> None:
        root = self.output_root
        self.assertEqual(root.get("role"), "img")
        self.assertEqual(root.get("aria-labelledby"), "gp04-title gp04-desc")
        self.assertEqual(root.get("data-status"), "graphic-pilot-not-current")
        self.assertEqual(root.get("data-construction-authority"), "false")
        metadata = json.loads(root.findtext(q("metadata"), default="{}"))
        self.assertIs(metadata["construction_authority"], False)
        self.assertIs(metadata["rating_claimed"], False)
        self.assertEqual(metadata["source_sha256"], pilot.sha256(pilot.SOURCE))
        self.assertEqual(metadata["decision_ids"], ["D-080"])

    def test_all_wall_types_nominal_values_and_duties_are_retained(self) -> None:
        text = visible_text(self.output_root)
        for wall_id, nominal, duty in pilot.SCHEDULE_ROWS:
            self.assertIn(wall_id, text)
            self.assertIn(nominal, text)
            self.assertIn(duty, text)
        self.assertEqual(text.count("P2-W02S"), 1)
        self.assertEqual(text.count("P2-W04R"), 1)
        self.assertEqual(text.count("P2-W05"), 1)
        self.assertEqual(text.count("P2-W06"), 1)

    def test_illustrative_sums_and_layer_order_are_retained(self) -> None:
        text = visible_text(self.output_root)
        for value in (
            "90 mm NOMINAL · 89 mm ILLUSTRATIVE SUM",
            "200 mm NOMINAL · 198 mm ILLUSTRATIVE SUM",
            "12.5 + 64 + 12.5 = 89 mm illustrative sum",
            "12.5 + 12.5 + 64 + 20 clear + 64 + 12.5 + 12.5 = 198 mm illustrative sum",
            "Numbering follows room-side → room-side model order.",
        ):
            self.assertIn(value, text)

    def test_redundant_material_keys_do_not_depend_on_colour(self) -> None:
        text = visible_text(self.output_root).lower()
        for material in (
            "new visible board",
            "reclaimed concealed board",
            "insulated frame",
            "clear decoupling cavity",
        ):
            self.assertIn(material, text)
        pattern_ids = {
            pattern.get("id")
            for pattern in self.output_root.iter(q("pattern"))
        }
        self.assertEqual(
            pattern_ids,
            {
                "gp04-new-board",
                "gp04-reclaimed-board",
                "gp04-insulated-frame",
                "gp04-air-cavity",
            },
        )

    def test_authority_and_performance_limits_remain_explicit(self) -> None:
        text = visible_text(self.output_root)
        for statement in (
            "ACTIVE SCHEMATIC COORDINATION",
            "OPEN · DO NOT FREEZE",
            "No STC/Rw or fire rating claimed.",
            "Thickness alone proves no performance rating.",
            "No product selected · no saving booked · no target change",
            "NOT FOR CONSTRUCTION",
        ):
            self.assertIn(statement, text)

    def test_each_copied_node_has_a_stable_model_reference(self) -> None:
        model = self.output_root.find(f"{q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None
        self.assertTrue(
            all(node.get("data-model-id") for group in model for node in group)
        )

    def test_copied_geometry_retains_non_scaling_strokes(self) -> None:
        model = self.output_root.find(f"{q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None
        geometry_tags = {
            q("line"),
            q("path"),
            q("rect"),
            q("circle"),
            q("polygon"),
            q("polyline"),
        }
        geometry = [element for element in model.iter() if element.tag in geometry_tags]
        self.assertTrue(geometry)
        self.assertTrue(
            all(element.get("vector-effect") == "non-scaling-stroke" for element in geometry)
        )


if __name__ == "__main__":
    unittest.main()

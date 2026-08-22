from __future__ import annotations

import json
import unittest
from xml.etree import ElementTree as ET

from dreamhouse.svg import pilot_e1_synthesis as pilot
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
    attributes = tuple(
        (name, element.attrib[name]) for name in sorted(GEOMETRY_ATTRS & element.attrib.keys())
    )
    return element.tag, attributes, tuple(geometry_signature(child) for child in element)


def visible_text(element: ET.Element) -> str:
    return " ".join(
        " ".join(" ".join(piece.split()) for piece in text.itertext())
        for text in element.iter(q("text"))
    )


class TestE1SynthesisGraphicPilot(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_root = ET.parse(pilot.SOURCE).getroot()
        cls.source_children = list(cls.source_root)
        cls.output_root = pilot.build_svg().getroot()

    def test_all_six_technical_geometry_groups_preserve_source_coordinates(self) -> None:
        model = self.output_root.find(f"{q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None
        output_groups = {group.get("data-source-group"): group for group in model}
        self.assertEqual(set(output_groups), set(pilot.SOURCE_GROUPS))

        for group_id, source_index in pilot.SOURCE_GROUPS.items():
            source_shapes = [
                node
                for node in self.source_children[source_index]
                if node.tag in pilot.SHAPE_TAGS
            ]
            output_shapes = list(output_groups[group_id])
            self.assertEqual(
                [geometry_signature(node) for node in output_shapes],
                [geometry_signature(node) for node in source_shapes],
            )

    def test_accessibility_status_and_source_metadata_are_explicit(self) -> None:
        root = self.output_root
        self.assertEqual(root.get("role"), "img")
        self.assertEqual(root.get("aria-labelledby"), "gp05-title gp05-desc")
        self.assertEqual(root.get("data-status"), "graphic-pilot-not-current")
        self.assertEqual(root.get("data-construction-authority"), "false")
        metadata = json.loads(root.findtext(q("metadata"), default="{}"))
        self.assertIs(metadata["construction_authority"], False)
        self.assertIs(metadata["selection_authority"], False)
        self.assertEqual(metadata["source_sha256"], pilot.sha256(pilot.SOURCE))
        self.assertEqual(
            metadata["input_sha256"],
            "9598c4d5d4c9d5b7398f86e79e6a0e3d5d4de1439a94a6db775c9e7090cd6e33",
        )

    def test_all_evidence_rows_retain_values_and_blocked_design_status(self) -> None:
        text = visible_text(self.output_root)
        for phenomenon, calc, evidence, design in pilot.EVIDENCE_ROWS:
            self.assertIn(phenomenon, text)
            self.assertIn(calc, text)
            self.assertIn(evidence, text)
            self.assertIn(design, text)
        self.assertEqual(text.count("BLOCKED"), 14)

    def test_reference_truss_and_detail_values_are_retained(self) -> None:
        text = visible_text(self.output_root)
        for value in (
            "18.00 m TRANSVERSE SPAN",
            "6 PANELS",
            "VARIABLE DEPTH 0.99→1.80 m",
            "HSS120×120×6",
            "HSS100×100×6",
            "0.653",
            "B1 1.255",
            "Nmax 209.8 kN",
            "Rdown 79.7 kN",
            "1241 kg / truss",
            "6-M20 · plate 12 mm · weld 8 mm",
            "2.0×2.0×0.5 m",
            "HOOK 15.8 kN",
        ):
            self.assertIn(value, text)

    def test_plan_values_and_active_rooflight_provenance_are_explicit(self) -> None:
        text = visible_text(self.output_root)
        for value in (
            "36.00 m",
            "18.00 m",
            "P2 18 × 15 m · +3.80",
            "DIAPHRAGM DEMAND · 8.77 kN/m",
            "EDGE · X=21",
            "HIDDEN FRAME · X=31.5",
            "4.50 m OVERHANG",
            "D-054 RL / q",
        ):
            self.assertIn(value, text)
        self.assertNotIn("D-040", text)

    def test_seven_technical_panels_and_authority_block_are_retained(self) -> None:
        text = visible_text(self.output_root)
        for number in range(1, 8):
            self.assertIn(f"{number:02} ·", text)
        self.assertIn("Research screening complete; design blocked.", text)
        self.assertIn("NOT FOR CONSTRUCTION", text)

    def test_no_visible_text_falls_below_the_pilot_role_floor(self) -> None:
        sizes = [float(text.get("font-size", "0")) for text in self.output_root.iter(q("text"))]
        self.assertTrue(sizes)
        self.assertGreaterEqual(min(sizes), 9.8)

    def test_each_copied_shape_has_stable_model_reference_and_stroke_scaling(self) -> None:
        model = self.output_root.find(f"{q('g')}[@id='layer-model']")
        self.assertIsNotNone(model)
        assert model is not None
        shapes = [shape for group in model for shape in group]
        self.assertTrue(shapes)
        self.assertTrue(all(shape.get("data-model-id") for shape in shapes))
        self.assertTrue(
            all(shape.get("vector-effect") == "non-scaling-stroke" for shape in shapes)
        )


if __name__ == "__main__":
    unittest.main()

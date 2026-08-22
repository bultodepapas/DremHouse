from __future__ import annotations

import unittest
from xml.etree import ElementTree as ET

from dreamhouse.svg.layout import (
    Bounds,
    LayoutRegion,
    estimate_geometry_bounds,
    estimate_text_bounds,
    q,
    register_geometry_regions,
    register_text_regions,
)


class TestSvgLayout(unittest.TestCase):
    def test_bounds_round_trip_and_inset(self) -> None:
        panel = Bounds(10, 20, 100, 60)
        safe = panel.inset(8)

        self.assertEqual(Bounds.parse(safe.serialize()), safe)
        self.assertTrue(panel.contains(safe))
        self.assertEqual(safe, Bounds(18, 28, 84, 44))
        self.assertFalse(safe.contains(Bounds(17, 28, 1, 1)))

    def test_invalid_bounds_and_regions_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Bounds(0, 0, 0, 10)
        with self.assertRaises(ValueError):
            Bounds.parse("0 0 10")
        with self.assertRaises(ValueError):
            LayoutRegion("bad", Bounds(0, 0, 10, 10), Bounds(9, 9, 2, 2))

    def test_estimator_supports_anchors_and_multiline_text(self) -> None:
        middle = ET.Element(
            q("text"),
            {"x": "50", "y": "30", "font-size": "10", "text-anchor": "middle"},
        )
        middle.text = "WIDE"
        middle_box = estimate_text_bounds(middle, letter_spacing=0.5, bold=True)

        multiline = ET.Element(q("text"), {"x": "10", "y": "20", "font-size": "10"})
        first = ET.SubElement(multiline, q("tspan"), {"x": "10", "dy": "0"})
        first.text = "First"
        second = ET.SubElement(multiline, q("tspan"), {"x": "10", "dy": "12"})
        second.text = "Second"
        multiline_box = estimate_text_bounds(multiline)

        self.assertLess(middle_box.x, 50)
        self.assertGreater(middle_box.right, 50)
        self.assertGreater(multiline_box.height, 20)

    def test_geometry_estimator_supports_registered_primitives(self) -> None:
        line = ET.Element(q("line"), {"x1": "10", "y1": "20", "x2": "40", "y2": "20"})
        polygon = ET.Element(q("polygon"), {"points": "50,10 70,20 50,30"})
        rectangle = ET.Element(q("rect"), {"x": "80", "y": "10", "width": "20", "height": "30"})

        self.assertEqual(estimate_geometry_bounds(line, stroke_width=2), Bounds(9, 19, 32, 2))
        self.assertEqual(estimate_geometry_bounds(polygon), Bounds(50, 10, 20, 20))
        self.assertEqual(estimate_geometry_bounds(rectangle), Bounds(80, 10, 20, 30))

        with self.assertRaises(ValueError):
            estimate_geometry_bounds(ET.Element(q("path"), {"d": "M0 0 L10 10"}))

    def test_registration_skips_model_and_types_rotated_text(self) -> None:
        root = ET.Element(q("svg"))
        model = ET.SubElement(root, q("g"), {"id": "layer-model"})
        model_text = ET.SubElement(model, q("text"), {"x": "20", "y": "20"})
        model_text.text = "Inherited"
        rotated = ET.SubElement(
            root,
            q("text"),
            {"x": "30", "y": "30", "font-size": "10", "transform": "rotate(-90 30 30)"},
        )
        rotated.text = "Rotated"

        register_text_regions(
            root,
            (LayoutRegion.with_inset("panel", Bounds(0, 0, 100, 100), 8),),
        )

        self.assertNotIn("data-layout-region", model_text.attrib)
        self.assertEqual(rotated.get("data-layout-region"), "panel")
        self.assertEqual(rotated.get("data-layout-policy"), "rotated-skip")

    def test_geometry_registration_requires_typed_editorial_relationships(self) -> None:
        root = ET.Element(q("svg"))
        leader = ET.SubElement(
            root,
            q("line"),
            {
                "x1": "10",
                "y1": "20",
                "x2": "80",
                "y2": "20",
                "data-layout-geometry": "leader",
                "data-layout-relation": "level-a",
            },
        )
        region = LayoutRegion.with_inset("panel", Bounds(0, 0, 100, 100), 8)

        register_geometry_regions(root, (region,))

        self.assertEqual(leader.get("data-layout-region"), "panel")

        leader.attrib.pop("data-layout-relation")
        with self.assertRaises(ValueError):
            register_geometry_regions(root, (region,))


if __name__ == "__main__":
    unittest.main()

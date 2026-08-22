from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.svg.render_equivalence import (
    _hex_colour,
    _font_requirement_passes,
    _probe_colour,
    build_geometry_probe,
    build_text_line_probe,
    check_layout_clearance,
    compare_probe_boxes,
    decode_probe_boxes,
    discover_browser,
    q,
)


PIL_AVAILABLE = importlib.util.find_spec("PIL") is not None


class TestSvgRenderEquivalence(unittest.TestCase):
    def test_probe_colours_are_unique_and_bounded(self) -> None:
        colours = {_probe_colour(index) for index in range(1, 512)}

        self.assertEqual(len(colours), 511)
        self.assertTrue(all(24 <= channel <= 220 for colour in colours for channel in colour))
        self.assertEqual(_hex_colour(1), "#341818")
        with self.assertRaises(ValueError):
            _probe_colour(512)

    def test_primary_font_requirement_fails_closed(self) -> None:
        self.assertTrue(
            _font_requirement_passes(
                {"requested": "Inter", "resolved_family": "Inter", "resolved_path": "/font"}
            )
        )
        self.assertFalse(
            _font_requirement_passes(
                {
                    "requested": "Inter",
                    "resolved_family": "Liberation Sans",
                    "resolved_path": "/fallback",
                }
            )
        )
        self.assertFalse(_font_requirement_passes(None))

    def test_text_probe_assigns_one_colour_per_explicit_line(self) -> None:
        root = ET.Element(q("svg"), {"width": "100", "height": "80"})
        ET.SubElement(root, q("rect"), {"width": "100", "height": "80"})
        text = ET.SubElement(
            root,
            q("text"),
            {"x": "10", "y": "20", "data-layout-region": "panel"},
        )
        first = ET.SubElement(text, q("tspan"), {"x": "10", "dy": "0"})
        first.text = "First"
        second = ET.SubElement(text, q("tspan"), {"x": "10", "dy": "12"})
        second.text = "Second"

        probe, items = build_text_line_probe(root)

        self.assertEqual([item["text"] for item in items], ["First", "Second"])
        self.assertEqual([item["line_index"] for item in items], [1, 2])
        self.assertEqual(len(list(probe.iter(q("rect")))), 0)
        self.assertIn("#341818", first_style := list(probe.iter(q("tspan")))[0].get("style", ""))
        self.assertIn("important", first_style)

    def test_geometry_probe_keeps_only_registered_editorial_primitives(self) -> None:
        root = ET.Element(q("svg"), {"width": "100", "height": "80"})
        ET.SubElement(root, q("rect"), {"width": "100", "height": "80"})
        registered = ET.SubElement(
            root,
            q("line"),
            {
                "x1": "10",
                "y1": "20",
                "x2": "80",
                "y2": "20",
                "data-layout-geometry": "keepout",
                "data-layout-region": "panel",
            },
        )

        probe, items = build_geometry_probe(root)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["role"], "keepout")
        self.assertEqual(len(list(probe.iter(q("rect")))), 0)
        self.assertIn("#341818", list(probe.iter(q("line")))[0].get("style", ""))
        self.assertIsNotNone(registered)

    @unittest.skipUnless(PIL_AVAILABLE, "Pillow is an optional presentation dependency")
    def test_exact_probe_colours_decode_to_paint_boxes(self) -> None:
        from PIL import Image

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "probe.png"
            image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            for x in range(2, 6):
                for y in range(3, 8):
                    image.putpixel((x, y), (*_probe_colour(1), 255))
            image.putpixel((90, 90), (*_probe_colour(1), 255))
            for x in range(10, 15):
                for y in range(11, 13):
                    image.putpixel((x, y), (*_probe_colour(2), 120))
            image.save(path)

            boxes = decode_probe_boxes(path, 2)

        self.assertEqual(boxes, {1: (2, 3, 5, 7), 2: (10, 11, 14, 12)})

    def test_box_comparison_fails_closed_on_missing_or_excess_delta(self) -> None:
        items = [
            {"index": 1, "text": "One"},
            {"index": 2, "text": "Two"},
            {"index": 3, "text": "Three"},
        ]
        comparison = compare_probe_boxes(
            items,
            {1: (1, 2, 3, 4), 2: (10, 10, 20, 20)},
            {1: (2, 2, 3, 4), 2: (10, 10, 25, 20), 3: (1, 1, 2, 2)},
            tolerance_px=2,
        )

        self.assertFalse(comparison["passed"])
        self.assertEqual(comparison["mismatches"], 2)
        self.assertEqual(comparison["missing_in_browser"], [3])
        self.assertEqual(comparison["maximum_edge_delta_px"], 5)

    def test_measured_layout_clearance_preserves_typed_relationships(self) -> None:
        text_items = [
            {
                "index": 1,
                "parent_index": 1,
                "text": "Badge",
                "layout_region": "panel",
                "layout_relation": "badge-a",
                "layout_policy": "rotated-measured",
            },
            {
                "index": 2,
                "parent_index": 2,
                "text": "Untyped",
                "layout_region": "panel",
                "layout_relation": None,
            },
        ]
        geometry_items = [
            {
                "index": 1,
                "source_id": "badge-outline",
                "role": "marker",
                "layout_region": "panel",
                "layout_relation": "badge-a",
            }
        ]
        result = check_layout_clearance(
            text_items,
            {1: (10, 10, 30, 20), 2: (80, 10, 100, 20)},
            geometry_items,
            {1: (8, 8, 32, 22)},
            scale=2,
        )

        self.assertTrue(result["passed"])
        self.assertEqual(result["rotated_text_elements_measured"], 1)
        self.assertEqual(result["rotated_text_elements_skipped"], 0)
        self.assertEqual(result["typed_text_geometry_pairs"], 1)
        self.assertEqual(result["untyped_text_geometry_pairs"], 0)

    def test_explicit_browser_path_is_resolved_without_installation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            browser = Path(temporary) / "chrome"
            browser.touch()

            self.assertEqual(discover_browser(browser), browser.resolve())


if __name__ == "__main__":
    unittest.main()

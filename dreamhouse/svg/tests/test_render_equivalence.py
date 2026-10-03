from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.svg.render_equivalence import (
    _font_requirement_passes,
    _hex_colour,
    _probe_colour,
    _render_browser,
    _render_resvg,
    audit_file,
    build_geometry_probe,
    build_text_line_probe,
    check_layout_clearance,
    compare_probe_boxes,
    decode_probe_boxes,
    discover_browser,
    q,
)
from dreamhouse.svg.style import compile_svg_styles
from dreamhouse.svg.theme import THEME_COLOURS

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
        self.assertIn("#341818", first_style := next(iter(probe.iter(q("tspan")))).get("style", ""))
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
        self.assertIn("#341818", next(iter(probe.iter(q("line")))).get("style", ""))
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

    def test_original_theme_colours_render_as_literals_in_resvg_and_optional_browser(self) -> None:
        # resvg is required for the project's raster-export parity profile. Browser
        # coverage is added when a local Chromium executable is available.
        import resvg_py  # noqa: F401
        from PIL import Image

        root = ET.Element(
            q("svg"),
            {"width": "240", "height": "110", "viewBox": "0 0 240 110"},
        )
        style = ET.SubElement(root, q("style"), {"id": "colour-parity"})
        style.text = (
            ":root { --info: #1D7480; --ink: #172A32; --selection: #2454A6; }\n"
            ".swatch { fill: var(--info); }\n"
            ".label { fill: var(--ink); font-family: Arial, sans-serif; "
            "font-size: 64px; font-weight: 700; }\n"
            ".is-selected .entity { fill: #FFFDFA; stroke: var(--selection) !important; "
            "stroke-width: 4px !important; }"
        )
        swatch = ET.SubElement(
            root,
            q("rect"),
            {"class": "swatch", "x": "10", "y": "10", "width": "65", "height": "65"},
        )
        label = ET.SubElement(
            root,
            q("text"),
            {"class": "label", "x": "92", "y": "68", "data-text-role": "primary"},
        )
        label.text = "H"
        selected_group = ET.SubElement(root, q("g"), {"class": "is-selected", "id": "picked"})
        selected_shape = ET.SubElement(
            selected_group,
            q("rect"),
            {"class": "entity", "x": "160", "y": "10", "width": "65", "height": "65"},
        )

        compile_svg_styles(root)

        self.assertEqual(swatch.get("class"), "swatch")
        self.assertEqual(label.get("data-text-role"), "primary")
        self.assertEqual(selected_group.get("id"), "picked")
        self.assertEqual(selected_shape.get("x"), "160")
        self.assertNotIn("var(", style.text or "")

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            svg_path = directory / "theme-parity.svg"
            ET.ElementTree(root).write(svg_path, encoding="utf-8", xml_declaration=True)
            resvg_path = directory / "theme-parity-resvg.png"
            _render_resvg(svg_path, resvg_path, width=240, height=110)

            browser: Path | None
            try:
                browser = discover_browser()
            except FileNotFoundError:
                browser = None
            browser_path = directory / "theme-parity-browser.png"
            if browser is not None:
                _render_browser(
                    svg_path,
                    browser_path,
                    browser=browser,
                    width=240,
                    height=110,
                    scale=1,
                )

            images = [resvg_path]
            if browser is not None:
                images.append(browser_path)
            for raster_path in images:
                with Image.open(raster_path) as source:
                    image = source.convert("RGBA")
                with self.subTest(renderer=raster_path.stem):
                    self.assertEqual(image.getpixel((25, 25)), (29, 116, 128, 255))
                    self.assertEqual(image.getpixel((160, 40)), (36, 84, 166, 255))
                    ink = tuple(
                        int(THEME_COLOURS["ink"][index : index + 2], 16)
                        for index in (1, 3, 5)
                    )
                    # Glyph edge pixels vary by renderer; the interior must still
                    # contain the intended original token within a 4-channel tolerance.
                    glyph_pixels = [
                        image.getpixel((x, y)) for x in range(82, 155) for y in range(8, 82)
                    ]
                    self.assertTrue(
                        any(
                            pixel[3] >= 250
                            and max(abs(pixel[channel] - ink[channel]) for channel in range(3)) <= 4
                            for pixel in glyph_pixels
                        ),
                        f"Expected primary glyph fill {THEME_COLOURS['ink']} in {raster_path.name}",
                    )

    def test_audit_marks_compiled_source_as_not_directly_certified(self) -> None:
        try:
            browser = discover_browser()
        except FileNotFoundError:
            self.skipTest("Chromium is optional for local audit-report coverage")

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            svg_path = directory / "variable-source.svg"
            svg_path.write_text(
                "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"40\" height=\"30\">"
                "<style>:root { --sample: #1D7480; } .box { fill: var(--sample); }</style>"
                '<rect class="box" x="4" y="4" width="20" height="20"/></svg>',
                encoding="utf-8",
            )

            result = audit_file(svg_path, directory / "audit", browser=browser)

        full_render = result["full_render"]
        self.assertTrue(full_render["portable_copy_rendered_for_parity"])
        self.assertTrue(full_render["source_had_css_variable_references"])
        self.assertFalse(full_render["original_source_style_portable"])
        self.assertFalse(full_render["original_source_artifact_parity_certified"])
        self.assertEqual(full_render["parity_subject"], "variable-source-portable.svg")


if __name__ == "__main__":
    unittest.main()

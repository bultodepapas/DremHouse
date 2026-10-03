from __future__ import annotations

import unittest
from xml.etree import ElementTree as ET

from dreamhouse.svg.style import compile_svg_styles, has_svg_css_variables
from dreamhouse.svg.theme import THEME_COLOURS

SVG_NS = "http://www.w3.org/2000/svg"


def q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


class TestSvgStyleCompilation(unittest.TestCase):
    def test_compiles_stylesheet_inline_and_paint_variables_preserving_structure(self) -> None:
        root = ET.Element(
            q("svg"),
            {"width": "100", "height": "100", "viewBox": "0 0 100 100"},
        )
        style = ET.SubElement(root, q("style"), {"id": "theme"})
        style.text = (
            ":root { --ink: #172A32; }\n"
            ".entity { fill: var(--paper); stroke: var(--info); }\n"
            ".entity.is-selected { stroke: var(--selection) !important; }"
        )
        group = ET.SubElement(root, q("g"), {"class": "entity is-selected", "id": "e-1"})
        rect = ET.SubElement(
            group,
            q("rect"),
            {
                "x": "10",
                "y": "10",
                "width": "20",
                "height": "20",
                "fill": "var(--panel)",
                "data-role": "space.primary-bedroom",
                "style": "stroke: var(--open);stroke-width: 2px",
            },
        )
        original_geometry = {key: rect.get(key) for key in ("x", "y", "width", "height")}

        compiled = compile_svg_styles(root)
        compile_svg_styles(compiled)

        self.assertIs(compiled, root)
        self.assertIn("stroke: #2454A6 !important", style.text or "")
        self.assertIn("fill: #F4F0E7", style.text or "")
        self.assertEqual(rect.get("fill"), THEME_COLOURS["panel"])
        self.assertEqual(rect.get("style"), "stroke: #8A5A16;stroke-width: 2px")
        self.assertEqual(rect.get("data-role"), "space.primary-bedroom")
        self.assertEqual(group.get("class"), "entity is-selected")
        self.assertEqual(group.get("id"), "e-1")
        self.assertEqual({key: rect.get(key) for key in original_geometry}, original_geometry)

    def test_explicit_mapping_extends_or_overrides_theme_and_requires_literal_colour(self) -> None:
        root = ET.Element(q("svg"), {"width": "10", "height": "10"})
        rect = ET.SubElement(root, q("rect"), {"fill": "var(--owner-accent)"})

        compile_svg_styles(root, variables={"owner-accent": "#123456"})

        self.assertEqual(rect.get("fill"), "#123456")
        with self.assertRaisesRegex(ValueError, "literal six-digit colour"):
            compile_svg_styles(root, variables={"owner-accent": "red"})

    def test_unknown_variable_fails_with_stylesheet_context(self) -> None:
        root = ET.Element(q("svg"))
        style = ET.SubElement(root, q("style"), {"id": "drawing-style"})
        style.text = ".bad { fill: var(--not-in-theme); }"

        with self.assertRaisesRegex(
            ValueError,
            r"Unknown SVG CSS variable --not-in-theme in <style> under drawing-style",
        ):
            compile_svg_styles(root)

    def test_literal_root_declaration_is_used_instead_of_the_theme_default(self) -> None:
        root = ET.Element(q("svg"))
        style = ET.SubElement(root, q("style"))
        style.text = ":root { --ink: #AA2233; } .title { fill: var(--ink); }"

        compile_svg_styles(root)

        self.assertIn("fill: #AA2233", style.text or "")

    def test_scoped_custom_property_override_fails_instead_of_flattening_cascade(self) -> None:
        root = ET.Element(q("svg"))
        style = ET.SubElement(root, q("style"))
        style.text = ".selected { --selection: #FF0000; stroke: var(--selection); }"

        with self.assertRaisesRegex(ValueError, "Scoped SVG CSS custom properties"):
            compile_svg_styles(root)

    def test_non_literal_root_custom_property_fails_closed(self) -> None:
        root = ET.Element(q("svg"))
        style = ET.SubElement(root, q("style"))
        style.text = ":root { --ink: currentColor; } .title { fill: var(--ink); }"

        with self.assertRaisesRegex(ValueError, "literal six-digit colour"):
            compile_svg_styles(root)

    def test_unknown_variables_fail_in_inline_and_presentation_styles(self) -> None:
        for attribute in ("style", "fill"):
            with self.subTest(attribute=attribute):
                root = ET.Element(q("svg"))
                rect = ET.SubElement(
                    root,
                    q("rect"),
                    {
                        attribute: "fill: var(--unknown);"
                        if attribute == "style"
                        else "var(--unknown)"
                    },
                )
                with self.assertRaisesRegex(ValueError, "Unknown SVG CSS variable --unknown"):
                    compile_svg_styles(root)
                self.assertIsNotNone(rect)

    def test_unsupported_variable_locations_and_fallbacks_fail_closed(self) -> None:
        root = ET.Element(q("svg"))
        rect = ET.SubElement(root, q("rect"), {"transform": "translate(var(--ink))"})
        with self.assertRaisesRegex(ValueError, "unsupported SVG attribute 'transform'"):
            compile_svg_styles(root)

        rect.attrib.pop("transform")
        rect.set("fill", "var(--ink, #ffffff)")
        with self.assertRaisesRegex(ValueError, "fallback values are outside"):
            compile_svg_styles(root)

        rect.set("fill", "var (--ink)")
        with self.assertRaisesRegex(ValueError, r"Malformed CSS var\(\) function spacing"):
            compile_svg_styles(root)

    def test_strings_and_comments_do_not_create_false_variable_references(self) -> None:
        root = ET.Element(q("svg"))
        style = ET.SubElement(root, q("style"))
        style.text = '/* var(--missing) */ .x { content: "var(--also-missing)"; fill: var(--ink); }'

        compile_svg_styles(root)

        self.assertIn("/* var(--missing) */", style.text or "")
        self.assertIn('"var(--also-missing)"', style.text or "")
        self.assertIn("fill: #172A32", style.text or "")

    def test_variable_presence_detection_includes_inline_styles_and_ignores_metadata(self) -> None:
        inline = ET.Element(q("svg"))
        ET.SubElement(inline, q("rect"), {"style": "fill: var(--info)"})
        self.assertTrue(has_svg_css_variables(inline))

        metadata = ET.Element(q("svg"))
        ET.SubElement(metadata, q("rect"), {"data-note": "literal var(--info) text"})
        style = ET.SubElement(metadata, q("style"))
        style.text = "/* var(--info) */ .x { fill: #1D7480; }"
        self.assertFalse(has_svg_css_variables(metadata))


if __name__ == "__main__":
    unittest.main()

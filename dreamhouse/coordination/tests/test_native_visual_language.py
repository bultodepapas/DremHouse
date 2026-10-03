"""Native candidate styling remains traceable to source meaning and geometry."""

from __future__ import annotations

import unittest
from xml.etree import ElementTree as ET

from dreamhouse.coordination import drawings
from dreamhouse.coordination.drawings import render_drawings
from dreamhouse.coordination.model import resolve_project
from dreamhouse.coordination.native_visual_language import apply_native_visual_language

SVG_NS = "http://www.w3.org/2000/svg"
_NS = f"{{{SVG_NS}}}"


class NativeVisualLanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = resolve_project()

    def test_p2_wall_key_covers_exactly_the_wall_roles_in_the_plan(self) -> None:
        rendered = render_drawings(self.snapshot, {})
        root = ET.fromstring(rendered["files"]["drawings/architecture-upper-floor.svg"])
        geometry_wall_ids = {
            node.get("data-wall-type")
            for node in root.iter()
            if node.get("data-wall-type") and node.get("data-legend-role") is None
        }
        legend_rows = {
            node.get("data-wall-type"): node
            for node in root.iter()
            if node.get("data-legend-role") == "wall-family"
        }

        self.assertEqual(set(legend_rows), geometry_wall_ids)
        schedule = self.snapshot["discipline_inputs"]["programme"]["p2"]["wall_schedule"]
        for wall_id, row in legend_rows.items():
            self.assertEqual(
                row.get("data-visual-language-version"), "native-connected-candidate-1"
            )
            self.assertEqual(row.get("data-source-wall-name"), schedule[wall_id]["name"])
            thickness = round(schedule[wall_id]["nominal_total_m"] * 1000)
            label = next(
                child for child in row if child.get("data-legend-role") == "wall-family-label"
            )
            self.assertIn(f"{thickness} mm", "".join(label.itertext()))
            line = next(
                child for child in row if child.get("data-legend-role") == "wall-family-sample"
            )
            source_line = next(
                node
                for node in root.iter(_NS + "line")
                if node.get("data-wall-type") == wall_id and node.get("data-legend-role") is None
            )
            self.assertEqual(line.get("stroke"), source_line.get("stroke"))
            self.assertEqual(line.get("stroke-dasharray"), source_line.get("stroke-dasharray"))

        self.assertEqual(root.get("data-reader-pair"), "p2")
        self.assertIn("upper-floor", root.get("data-view-purpose", ""))
        sheet_text = " ".join("".join(node.itertext()).strip() for node in root.iter(_NS + "text"))
        self.assertIn("SOURCE MODEL CHECKS · NOT DESIGN ACCEPTANCE", sheet_text)
        _pb, p2, _rooflights, _structure = drawings._synchronise_native_models(self.snapshot)
        report = drawings.generate_p2_b09._report(p2)
        status_text = f"{report['passed']} PASS · {report['failed']} FAIL · {report['open']} OPEN"
        self.assertIn(status_text, sheet_text)

    def test_wall_legend_does_not_change_native_wall_geometry(self) -> None:
        _pb, p2, _rooflights, _structure = drawings._synchronise_native_models(self.snapshot)
        source_svg = drawings.generate_p2_b09.build_plan(p2, drawings.generate_p2_b09._report(p2))
        source = ET.fromstring(source_svg)
        rendered = render_drawings(self.snapshot, {})
        output = ET.fromstring(rendered["files"]["drawings/architecture-upper-floor.svg"])
        attributes = (
            "x1",
            "y1",
            "x2",
            "y2",
            "stroke",
            "stroke-width",
            "stroke-dasharray",
            "data-wall-type",
        )

        def physical_walls(root: ET.Element) -> list[tuple[str, ...]]:
            return sorted(
                tuple(node.get(key, "") for key in attributes)
                for node in root.iter()
                if node.get("data-wall-type") and node.get("data-legend-role") is None
            )

        self.assertEqual(physical_walls(output), physical_walls(source))

    def test_quiet_pattern_changes_only_repetition_contrast(self) -> None:
        svg = (
            f'<svg xmlns="{SVG_NS}" data-view-id="architecture-side-a-elevation">'
            '<defs><pattern id="metals" width="14" height="14" patternUnits="userSpaceOnUse">'
            '<line x1="3" y1="0" x2="3" y2="14" stroke="#90999b" stroke-width=".7" />'
            "</pattern></defs></svg>"
        )
        root = ET.fromstring(svg)
        before_pattern = next(root.iter(_NS + "pattern"))
        before_line = next(root.iter(_NS + "line"))
        before_pattern_shape = (before_pattern.get("width"), before_pattern.get("height"))
        before_line_geometry = tuple(before_line.get(key) for key in ("x1", "y1", "x2", "y2"))

        apply_native_visual_language(self.snapshot, "architecture-side-a-elevation", root)

        pattern = next(root.iter(_NS + "pattern"))
        line = next(root.iter(_NS + "line"))
        self.assertEqual((pattern.get("width"), pattern.get("height")), before_pattern_shape)
        self.assertEqual(
            tuple(line.get(key) for key in ("x1", "y1", "x2", "y2")),
            before_line_geometry,
        )
        self.assertEqual(line.get("opacity"), "0.36")
        self.assertEqual(pattern.get("data-presentation-role"), "decorative-surface-pattern")

    def test_final_native_outputs_have_purpose_and_portable_literal_paint(self) -> None:
        rendered = render_drawings(self.snapshot, {})
        views = [path for path in rendered["files"] if path.endswith(".svg")]
        self.assertEqual(len(views), 27)
        for path in views:
            with self.subTest(path=path):
                root = ET.fromstring(rendered["files"][path])
                self.assertEqual(
                    root.get("data-visual-language-version"), "native-connected-candidate-1"
                )
                self.assertTrue(root.get("data-view-purpose"))
                self.assertTrue(root.get("data-coordination-companion"))
                self.assertFalse(
                    any(
                        "var(" in node.get(attribute, "")
                        for node in root.iter()
                        for attribute in ("fill", "stroke", "style")
                    )
                )
                authority = next(
                    node for node in root.iter() if node.get("data-text-role") == "authority-status"
                )
                self.assertIn("NOT DESIGN ADOPTION", "".join(authority.itertext()))
                self.assertIn("NOT FOR CONSTRUCTION", "".join(authority.itertext()))
                self.assertIn(
                    root.get("data-visible-purpose", "").upper(), "".join(authority.itertext())
                )


if __name__ == "__main__":
    unittest.main()

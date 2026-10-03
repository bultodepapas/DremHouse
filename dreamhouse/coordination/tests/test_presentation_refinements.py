"""Presentation-only corrections retain the resolved drawing geometry and anchors."""

from __future__ import annotations

import unittest
from xml.etree import ElementTree as ET

from dreamhouse.coordination.drawings import render_drawings
from dreamhouse.coordination.model import resolve_project
from dreamhouse.coordination.presentation_refinements import refine_native_svg

SVG_NS = "http://www.w3.org/2000/svg"


def _svg(view_id: str, body: str) -> str:
    return f'<svg xmlns="{SVG_NS}" data-view-id="{view_id}" viewBox="0 0 1400 962">{body}</svg>'


def _texts(root: ET.Element) -> list[ET.Element]:
    return list(root.iter(f"{{{SVG_NS}}}text"))


def _content(node: ET.Element) -> str:
    return "".join(node.itertext()).strip()


def _geometry(root: ET.Element) -> list[tuple[str, tuple[tuple[str, str], ...]]]:
    coordinate_attrs = {
        "x",
        "y",
        "width",
        "height",
        "x1",
        "y1",
        "x2",
        "y2",
        "cx",
        "cy",
        "r",
        "rx",
        "ry",
        "d",
        "points",
    }
    return [
        (
            node.tag.rsplit("}", 1)[-1],
            tuple(
                sorted(
                    (key, value) for key, value in node.attrib.items() if key in coordinate_attrs
                )
            ),
        )
        for node in root.iter()
        if node.tag.rsplit("}", 1)[-1] in {"rect", "line", "circle", "path", "polygon", "polyline"}
    ]


def _audit_features(root: ET.Element) -> list[tuple[tuple[str, str], ...]]:
    keys = (
        "id",
        "data-entity-id",
        "data-anchor-id",
        "data-anchor-name",
        "data-anchor-entity-id",
        "data-anchor-context-id",
        "data-context-feature",
        "data-dimension-id",
    )
    return [
        tuple((key, node.get(key, "")) for key in keys if key in node.attrib)
        for node in root.iter()
        if any(key in node.attrib for key in keys)
    ]


class NativePresentationRefinementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.snapshot = resolve_project()

    def test_primary_bathroom_room_label_moves_into_clear_compartment(self) -> None:
        svg = _svg(
            "architecture-upper-floor",
            '<rect data-space-id="M-B" x="376" y="657" width="76" height="128" />'
            '<rect class="fixture primary-linen" x="384" y="669" width="54" height="18" />'
            '<rect class="fixture primary-wc" x="386" y="741" width="28" height="34" />'
            '<rect data-entity-id="W-G" x="1036" y="425" width="117" height="94" />'
            '<text x="280" y="693.75" font-size="9"><tspan>Primary bathroom</tspan>'
            "<tspan>15.66 m2 net schematic</tspan><tspan>17.60 m2 gross unified</tspan></text>",
        )
        before = ET.fromstring(svg)
        refined = ET.fromstring(refine_native_svg(self.snapshot, "architecture-upper-floor", svg))

        label = next(node for node in _texts(refined) if node.get("data-presentation-refinement"))
        self.assertEqual(_content(label), "BATH")
        self.assertEqual(label.get("x"), "414")
        self.assertGreater(float(label.get("y")), 687)
        area_note = next(
            node
            for node in _texts(refined)
            if node.get("data-presentation-refinement") == "VR-01-primary-bathroom-areas"
        )
        self.assertEqual(
            _content(area_note),
            "PRIMARY BATHROOM · 15.66 m² NET (SCHEMATIC) · 17.60 m² GROSS (UNIFIED)",
        )
        self.assertLess(float(label.get("y")) + 9, 741)
        self.assertEqual(_geometry(refined), _geometry(before))
        self.assertEqual(_audit_features(refined), _audit_features(before))

    def test_pb_and_detail_island_labels_use_d079_source_dimensions(self) -> None:
        cases = (
            (
                "architecture-ground-floor",
                (
                    '<rect x="280.6" y="254.9" width="121.5" height="43.2" />'
                    '<line x1="321.1" y1="254.9" x2="321.1" y2="298.1" />'
                    '<text x="341.35" y="279.5" text-anchor="middle">'
                    "CENTRAL RC ASSEMBLY ISLAND · 3 × 1.50 m · TOP +0.84</text>"
                ),
                "VR-02-pb-rc-island-label",
            ),
            (
                "architecture-pb-technical-workbenches",
                (
                    '<rect x="75" y="725" width="414" height="147.2" />'
                    '<line x1="75" y1="798.6" x2="489" y2="798.6" />'
                    '<text x="282" y="801.6">4.50 × 1.60 m · 3 × 1.50 m · TWO-SIDED · TOP +0.84</text>'
                ),
                "VR-02-detail-rc-island-label",
            ),
        )
        source = self.snapshot["discipline_inputs"]["equipment"]["pb"]["central_rc_bench"]
        for view_id, body, refinement_id in cases:
            with self.subTest(view_id=view_id):
                svg = _svg(view_id, body)
                before = ET.fromstring(svg)
                refined = ET.fromstring(refine_native_svg(self.snapshot, view_id, svg))
                label = next(
                    node
                    for node in _texts(refined)
                    if node.get("data-presentation-refinement") == refinement_id
                )
                joined = " ".join(_content(child) for child in label)
                self.assertIn(f"{source['length']:.2f} × {source['depth']:.2f} m", joined)
                self.assertIn(
                    f"{source['module_count']} × {source['module_width']:.2f} m modules", joined
                )
                self.assertIn(f"+{source['height']:.2f} m", joined)
                self.assertEqual(_geometry(refined), _geometry(before))
                self.assertEqual(_audit_features(refined), _audit_features(before))
                self.assertEqual(len(_texts(refined)), len(_texts(before)))

    def test_side_b_downpipe_reference_is_distinguished_without_moving_it(self) -> None:
        svg = _svg(
            "architecture-side-b-elevation",
            '<rect id="side-B-W-G" data-entity-id="W-G" x="1036.125" y="425.625" '
            'width="117" height="94.25" />'
            '<line x1="1128.75" y1="406.5" x2="1128.75" y2="645" '
            'stroke="#536166" stroke-width="3" />',
        )
        before = ET.fromstring(svg)
        refined = ET.fromstring(
            refine_native_svg(self.snapshot, "architecture-side-b-elevation", svg)
        )
        line_before = next(before.iter(f"{{{SVG_NS}}}line"))
        line_after = next(refined.iter(f"{{{SVG_NS}}}line"))

        self.assertEqual(
            [line_after.get(key) for key in ("x1", "y1", "x2", "y2")],
            [line_before.get(key) for key in ("x1", "y1", "x2", "y2")],
        )
        self.assertEqual(line_after.get("stroke-dasharray"), "5 4")
        self.assertEqual(line_after.get("stroke"), "#b45d35")
        self.assertIn("POSITION / W-G", " ".join(map(_content, _texts(refined))))
        self.assertIn("INTERFACE OPEN", " ".join(map(_content, _texts(refined))))
        self.assertEqual(_geometry(refined), _geometry(before))
        self.assertEqual(_audit_features(refined), _audit_features(before))

    def test_core_and_great_wall_show_unlocated_access_without_opening_symbols(self) -> None:
        cases = (
            (
                "architecture-ground-floor-core",
                (
                    '<rect data-space-id="PAN" x="300" y="120" width="160" height="70" />'
                    '<text x="381" y="184">Pantry / clean support</text>'
                ),
                "VR-04-core-access-unlocated",
            ),
            (
                "architecture-great-wall-elevation",
                (
                    '<rect x="120" y="408.4" width="1134" height="201.6" />'
                    '<rect x="120" y="780" width="1134" height="65" fill="#fff4df" stroke="#bd5c3c" />'
                    '<text x="140" y="805">DESIGN INTENT</text>'
                    '<text x="140" y="827">Continuous architectural finish across the core zones; door positions remain unresolved under CF-013.</text>'
                    '<text x="140" y="844">Finish and stability require a 1:1 sample and professional specification.</text>'
                    '<text x="140" y="875" data-context-feature="great-wall-height-unresolved">HEIGHT NOT SOURCE-DEFINED · VERTICAL PROFILE IS SCHEMATIC</text>'
                ),
                "VR-04-great-wall-access-unlocated",
            ),
        )
        for view_id, body, refinement_id in cases:
            with self.subTest(view_id=view_id):
                svg = _svg(view_id, body)
                before = ET.fromstring(svg)
                refined = ET.fromstring(refine_native_svg(self.snapshot, view_id, svg))
                note = next(
                    node
                    for node in _texts(refined)
                    if node.get("data-presentation-refinement") == refinement_id
                )
                self.assertIn("CF-013", _content(note))
                self.assertIn("unresolved", _content(note).lower())
                if view_id == "architecture-great-wall-elevation":
                    old_panel = next(
                        node
                        for node in before.iter(f"{{{SVG_NS}}}rect")
                        if node.get("fill") == "#fff4df"
                    )
                    new_panel = next(
                        node
                        for node in refined.iter(f"{{{SVG_NS}}}rect")
                        if node.get("fill") == "#fff4df"
                    )
                    self.assertEqual(
                        [new_panel.get(key) for key in ("x", "y", "width")],
                        [old_panel.get(key) for key in ("x", "y", "width")],
                    )
                    self.assertEqual(new_panel.get("height"), "88")
                    old_geometry = _geometry(before)
                    new_geometry = _geometry(refined)
                    old_panel_signature = (
                        "rect",
                        tuple(
                            sorted(
                                (key, old_panel.get(key)) for key in ("x", "y", "width", "height")
                            )
                        ),
                    )
                    new_panel_signature = (
                        "rect",
                        tuple(
                            sorted(
                                (key, new_panel.get(key)) for key in ("x", "y", "width", "height")
                            )
                        ),
                    )
                    old_geometry.remove(old_panel_signature)
                    new_geometry.remove(new_panel_signature)
                    self.assertEqual(new_geometry, old_geometry)
                    height_note = next(
                        node
                        for node in _texts(refined)
                        if node.get("data-context-feature") == "great-wall-height-unresolved"
                    )
                    self.assertEqual(height_note.get("y"), "860")
                    self.assertEqual(height_note.get("font-size"), "9")
                    self.assertIn("HEIGHT NOT SOURCE-DEFINED", _content(height_note))
                    self.assertIn("door locations, leaves and swings", _content(note))
                    self.assertEqual(note.get("font-size"), "9")
                else:
                    self.assertEqual(_geometry(refined), _geometry(before))
                self.assertEqual(_audit_features(refined), _audit_features(before))
                if view_id == "architecture-great-wall-elevation":
                    header = next(
                        node for node in _texts(refined) if _content(node) == "DESIGN INTENT"
                    )
                    spec = next(node for node in _texts(refined) if "1:1 sample" in _content(node))
                    self.assertEqual(header.get("y"), "798")
                    self.assertEqual(spec.get("y"), "829")

    def test_unaffected_views_are_returned_byte_for_byte(self) -> None:
        svg = '<svg xmlns="http://www.w3.org/2000/svg" data-view-id="architecture-roof-plan" />'
        self.assertEqual(refine_native_svg(self.snapshot, "architecture-roof-plan", svg), svg)

    def test_integrated_native_consumers_render_all_target_refinements(self) -> None:
        rendered = render_drawings(self.snapshot, {})
        expected = {
            "architecture-upper-floor": "VR-01-primary-bathroom-areas",
            "architecture-ground-floor": "VR-02-pb-rc-island-label",
            "architecture-pb-technical-workbenches": "VR-02-detail-rc-island-label",
            "architecture-side-b-elevation": "VR-03-provisional-downpipe-reference",
            "architecture-ground-floor-core": "VR-04-core-access-unlocated",
            "architecture-great-wall-elevation": "VR-04-great-wall-access-unlocated",
        }
        for view_id, refinement_id in expected.items():
            with self.subTest(view_id=view_id):
                svg = rendered["files"][f"drawings/{view_id}.svg"]
                root = ET.fromstring(svg)
                self.assertEqual(root.get("data-view-id"), view_id)
                self.assertTrue(
                    any(
                        node.get("data-presentation-refinement") == refinement_id
                        for node in root.iter()
                    )
                )
                self.assertTrue(_audit_features(root))
        great_wall = ET.fromstring(
            rendered["files"]["drawings/architecture-great-wall-elevation.svg"]
        )
        height_note = next(
            node
            for node in _texts(great_wall)
            if node.get("data-presentation-refinement") == "VR-04-great-wall-height-unresolved"
        )
        access_note = next(
            node
            for node in _texts(great_wall)
            if node.get("data-presentation-refinement") == "VR-04-great-wall-access-unlocated"
        )
        self.assertIn("HEIGHT NOT SOURCE-DEFINED", _content(height_note))
        self.assertIn("no door coordinates", _content(access_note).lower())
        self.assertEqual(height_note.get("font-size"), "9")
        self.assertEqual(access_note.get("font-size"), "9")


if __name__ == "__main__":
    unittest.main()

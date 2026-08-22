from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.svg import (
    pilot_e1_synthesis,
    pilot_ground_floor,
    pilot_p2_wall_family,
    pilot_side_b,
    pilot_transverse_section,
)
from dreamhouse.svg.layout import Bounds, LayoutRegion, register_text_regions
from dreamhouse.svg.lint import exit_code, lint_file, lint_paths, markdown_report
from dreamhouse.svg.sheet import create_document, q


PILOTS = (
    pilot_ground_floor.OUTPUT,
    pilot_side_b.OUTPUT,
    pilot_transverse_section.OUTPUT,
    pilot_p2_wall_family.OUTPUT,
    pilot_e1_synthesis.OUTPUT,
)


def finding_codes(report: dict) -> set[str]:
    return {finding["code"] for finding in report["findings"]}


def valid_document() -> ET.Element:
    root = create_document(
        title_id="test-title",
        desc_id="test-desc",
        accessible_title="Static lint test",
        description="A complete non-construction SVG lint fixture.",
        sheet_id="DH-TEST-001",
        revision="T01",
        status="test-not-current",
        metadata={
            "construction_authority": False,
            "source": "generated test fixture",
        },
    )
    background = ET.SubElement(
        root,
        q("g"),
        {"id": "layer-background", "data-layer": "paper"},
    )
    ET.SubElement(
        background,
        q("rect"),
        {
            "x": "0",
            "y": "0",
            "width": "1684",
            "height": "1191",
            "fill": "#ffffff",
        },
    )
    model = ET.SubElement(
        root,
        q("g"),
        {"id": "layer-model", "data-layer": "model"},
    )
    model_node = ET.SubElement(model, q("g"), {"data-model-id": "TEST-MODEL-001"})
    ET.SubElement(
        model_node,
        q("rect"),
        {
            "x": "100",
            "y": "100",
            "width": "200",
            "height": "100",
            "fill": "none",
            "stroke": "#172A32",
            "stroke-width": "2",
        },
    )
    annotations = ET.SubElement(
        root,
        q("g"),
        {
            "id": "layer-annotations",
            "data-layer": "annotations",
            "data-contrast-bg": "#FFFDFA",
        },
    )
    annotation = ET.SubElement(
        annotations,
        q("text"),
        {
            "x": "100",
            "y": "240",
            "font-size": "10",
            "class": "new-body",
            "data-text-role": "primary",
        },
    )
    annotation.text = "Primary label"
    sheet = ET.SubElement(
        root,
        q("g"),
        {"id": "layer-sheet", "data-layer": "sheet", "data-contrast-bg": "#FFFDFA"},
    )
    sheet_text = ET.SubElement(
        sheet,
        q("text"),
        {"x": "100", "y": "1120", "font-size": "10", "class": "new-body"},
    )
    sheet_text.text = "Presentation only"
    register_text_regions(
        root,
        (LayoutRegion.with_inset("fixture", Bounds(0, 0, 1684, 1191), 8),),
    )
    return root


def write_svg(directory: Path, root: ET.Element, name: str = "fixture.svg") -> Path:
    path = directory / name
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
    return path


class TestStaticSvgLint(unittest.TestCase):
    def test_all_five_pilots_pass_the_required_profile(self) -> None:
        report = lint_paths(list(PILOTS))

        self.assertEqual(report["summary"]["files"], 5)
        self.assertEqual(report["summary"]["failed"], 0)
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertEqual(exit_code(report), 0)
        self.assertTrue(
            all(file["metrics"]["required_text_below_minimum"] == 0 for file in report["files"])
        )
        self.assertTrue(all(file["metrics"]["contrast_failures"] == 0 for file in report["files"]))
        self.assertTrue(
            all(file["metrics"]["presentation_palette_failures"] == 0 for file in report["files"])
        )
        self.assertTrue(
            all(file["metrics"]["minimum_contrast_ratio"] >= 4.5 for file in report["files"])
        )
        self.assertTrue(
            all(file["metrics"]["safe_bound_failures"] == 0 for file in report["files"])
        )
        self.assertTrue(
            all(file["metrics"]["untyped_text_collisions"] == 0 for file in report["files"])
        )

    def test_layout_contract_bounds_and_collisions_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing_root = valid_document()
            missing_text = missing_root.find(f"{q('g')}[@id='layer-annotations']/{q('text')}")
            assert missing_text is not None
            missing_text.attrib.pop("data-layout-region")
            missing_path = write_svg(Path(temporary), missing_root, "missing-layout.svg")

            outside_root = valid_document()
            outside_text = outside_root.find(f"{q('g')}[@id='layer-annotations']/{q('text')}")
            assert outside_text is not None
            outside_text.set("x", "7")
            outside_path = write_svg(Path(temporary), outside_root, "outside-layout.svg")

            collision_root = valid_document()
            collision_texts = list(collision_root.iter(q("text")))
            assert len(collision_texts) == 2
            collision_texts[1].set("x", collision_texts[0].get("x", "100"))
            collision_texts[1].set("y", collision_texts[0].get("y", "240"))
            collision_path = write_svg(Path(temporary), collision_root, "collision-layout.svg")

            missing = lint_file(missing_path)
            outside = lint_file(outside_path)
            collision = lint_file(collision_path)

        self.assertIn("SVG-B001", finding_codes(missing))
        self.assertIn("SVG-B003", finding_codes(outside))
        self.assertIn("SVG-B004", finding_codes(collision))
        self.assertEqual(outside["metrics"]["safe_bound_failures"], 1)
        self.assertEqual(collision["metrics"]["untyped_text_collisions"], 1)

    def test_shared_layout_relation_types_an_intentional_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = valid_document()
            texts = list(root.iter(q("text")))
            assert len(texts) == 2
            texts[1].set("x", texts[0].get("x", "100"))
            texts[1].set("y", texts[0].get("y", "240"))
            for text in texts:
                text.set("data-layout-relation", "fixture-composite-label")
            path = write_svg(Path(temporary), root)

            report = lint_file(path)

        self.assertNotIn("SVG-B004", finding_codes(report))
        self.assertEqual(report["metrics"]["typed_text_collisions"], 1)

    def test_malformed_svg_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "broken.svg"
            path.write_text("<svg><broken></svg>", encoding="utf-8")

            report = lint_file(path)

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(finding_codes(report), {"SVG-X001"})

    def test_duplicate_ids_and_unsafe_content_are_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = valid_document()
            annotations = root.find(f"{q('g')}[@id='layer-annotations']")
            assert annotations is not None
            ET.SubElement(root, q("script")).text = "void 0"
            ET.SubElement(root, q("image"), {"href": "https://example.invalid/a.png"})
            ET.SubElement(annotations, q("g"), {"id": "layer-sheet", "onclick": "void 0"})
            path = write_svg(Path(temporary), root)

            report = lint_file(path)

        self.assertTrue(
            {"SVG-I001", "SVG-S001", "SVG-S002", "SVG-S003"} <= finding_codes(report)
        )
        self.assertEqual(report["status"], "FAIL")

    def test_required_small_text_fails_while_model_microtext_warns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = valid_document()
            annotations = root.find(f"{q('g')}[@id='layer-annotations']")
            model_node = root.find(f"{q('g')}[@id='layer-model']/{q('g')}")
            assert annotations is not None and model_node is not None
            required = annotations.find(q("text"))
            assert required is not None
            required.set("font-size", "9")
            micro = ET.SubElement(
                model_node,
                q("text"),
                {"x": "100", "y": "180", "font-size": "5", "data-text-role": "micro"},
            )
            micro.text = "Inherited note"
            path = write_svg(Path(temporary), root)

            report = lint_file(path)

        self.assertTrue({"SVG-T002", "SVG-T004"} <= finding_codes(report))
        self.assertEqual(report["metrics"]["required_text_below_minimum"], 1)
        self.assertEqual(report["metrics"]["model_microtext_below_minimum"], 1)
        self.assertEqual(report["status"], "FAIL")

    def test_authority_accessibility_layers_and_model_references_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = valid_document()
            title = root.find(q("title"))
            metadata_element = root.find(q("metadata"))
            model_node = root.find(f"{q('g')}[@id='layer-model']/{q('g')}")
            sheet = root.find(f"{q('g')}[@id='layer-sheet']")
            assert title is not None and metadata_element is not None
            assert model_node is not None and sheet is not None
            title.text = ""
            metadata = json.loads(metadata_element.text or "{}")
            metadata["construction_authority"] = True
            metadata["revision"] = "MISMATCH"
            metadata_element.text = json.dumps(metadata)
            root.set("data-construction-authority", "true")
            model_node.attrib.pop("data-model-id")
            root.remove(sheet)
            path = write_svg(Path(temporary), root)

            report = lint_file(path)

        self.assertTrue(
            {"SVG-A004", "SVG-L001", "SVG-L004", "SVG-M005", "SVG-M006", "SVG-M009"}
            <= finding_codes(report)
        )
        self.assertEqual(report["status"], "FAIL")

    def test_nonfinite_numbers_fail_and_precision_can_be_strict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = valid_document()
            model_rect = root.find(f"{q('g')}[@id='layer-model']/{q('g')}/{q('rect')}")
            assert model_rect is not None
            model_rect.set("x", "NaN")
            model_rect.set("width", "200.1234567")
            path = write_svg(Path(temporary), root)

            ordinary = lint_file(path)
            strict = lint_file(path, strict_precision=True)

        self.assertTrue({"SVG-N001", "SVG-N003"} <= finding_codes(ordinary))
        ordinary_precision = next(
            finding for finding in ordinary["findings"] if finding["code"] == "SVG-N003"
        )
        strict_precision = next(
            finding for finding in strict["findings"] if finding["code"] == "SVG-N003"
        )
        self.assertEqual(ordinary_precision["severity"], "warning")
        self.assertEqual(strict_precision["severity"], "error")

    def test_unapproved_presentation_colour_fails_but_model_colour_warns(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = valid_document()
            background_rect = root.find(f"{q('g')}[@id='layer-background']/{q('rect')}")
            model_rect = root.find(f"{q('g')}[@id='layer-model']/{q('g')}/{q('rect')}")
            assert background_rect is not None and model_rect is not None
            background_rect.set("fill", "#123456")
            model_rect.set("stroke", "#654321")
            path = write_svg(Path(temporary), root)

            report = lint_file(path)

        self.assertTrue({"SVG-C001", "SVG-C002"} <= finding_codes(report))
        self.assertEqual(report["metrics"]["presentation_palette_failures"], 1)
        self.assertEqual(report["metrics"]["inherited_off_palette_colours"], 1)
        self.assertEqual(report["status"], "FAIL")

    def test_missing_background_and_low_contrast_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing_root = valid_document()
            missing_annotations = missing_root.find(f"{q('g')}[@id='layer-annotations']")
            assert missing_annotations is not None
            missing_annotations.attrib.pop("data-contrast-bg")
            missing_path = write_svg(Path(temporary), missing_root, "missing.svg")

            low_root = valid_document()
            low_annotations = low_root.find(f"{q('g')}[@id='layer-annotations']")
            assert low_annotations is not None
            low_annotations.set("data-contrast-bg", "#172A32")
            low_path = write_svg(Path(temporary), low_root, "low.svg")

            missing = lint_file(missing_path)
            low = lint_file(low_path)

        self.assertIn("SVG-C003", finding_codes(missing))
        self.assertIn("SVG-C005", finding_codes(low))
        self.assertEqual(missing["metrics"]["untyped_contrast_backgrounds"], 1)
        self.assertEqual(low["metrics"]["contrast_failures"], 1)

    def test_contrast_thresholds_are_configurable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = write_svg(Path(temporary), valid_document())

            ordinary = lint_file(path)
            strict = lint_file(path, normal_contrast=15.0, large_contrast=15.0)

        self.assertNotIn("SVG-C005", finding_codes(ordinary))
        self.assertIn("SVG-C005", finding_codes(strict))

    def test_reports_are_deterministic_and_warnings_can_fail_ci(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = valid_document()
            model_rect = root.find(f"{q('g')}[@id='layer-model']/{q('g')}/{q('rect')}")
            assert model_rect is not None
            model_rect.set("width", "200.1234567")
            path = write_svg(Path(temporary), root)

            first = lint_paths([path])
            second = lint_paths([path])

        self.assertEqual(first, second)
        self.assertEqual(markdown_report(first), markdown_report(second))
        self.assertEqual(exit_code(first), 0)
        self.assertEqual(exit_code(first, warnings_as_errors=True), 1)


if __name__ == "__main__":
    unittest.main()

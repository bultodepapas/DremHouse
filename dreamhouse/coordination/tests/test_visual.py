from __future__ import annotations

import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from PIL import Image

from dreamhouse.coordination.visual import (
    CONTACT_GUTTER,
    CONTACT_HEADER_HEIGHT,
    CONTACT_LABEL_HEIGHT,
    compare_visuals,
    render_visuals,
    visual_configuration,
)

ROOT = Path(__file__).resolve().parents[3]
FONT_DIR = ROOT / "dreamhouse" / "coordination" / "fonts"
FONTS = (
    FONT_DIR / "IBMPlexSans-Regular.ttf",
    FONT_DIR / "IBMPlexSans-Bold.ttf",
)


def sample_svg(title: str, color: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg"
  width="400" height="200" viewBox="0 0 400 200">
  <title>{title}</title>
  <style>text {{ font-family: "IBM Plex Sans", sans-serif; }}</style>
  <rect width="400" height="200" fill="#fbfaf7" />
  <rect x="30" y="35" width="340" height="100" fill="{color}" stroke="#172a32" />
  <text x="38" y="170" font-size="20" fill="#172a32">{title}</text>
</svg>'''


def source_pngs(artifacts: dict[str, bytes]) -> dict[str, bytes]:
    return {name: contents for name, contents in artifacts.items() if name != "contact_sheet.png"}


class VisualExportTests(unittest.TestCase):
    def test_all_svg_inputs_render_to_siblings_and_contact_sheet(self) -> None:
        files = {
            "views/pb.svg": sample_svg("Ground floor review", "#9bc4cb"),
            "views/p2.svg": sample_svg("Upper floor review", "#e9c786"),
            "details/windows.svg": sample_svg("Window detail review", "#c8d6b9"),
        }

        artifacts, manifest = render_visuals(files, font_paths=FONTS, width_px=320)

        self.assertEqual(
            set(artifacts),
            {"views/pb.png", "views/p2.png", "details/windows.png", "contact_sheet.png"},
        )
        self.assertEqual(set(manifest["sources"]), set(files))
        self.assertEqual(
            manifest["contact_sheet"]["included_sources"],
            sorted(files),
        )
        self.assertFalse(manifest["geometry_mutated"])
        self.assertFalse(manifest["construction_authority"])

        for name, svg_text in files.items():
            with Image.open(io.BytesIO(artifacts[name.replace(".svg", ".png")])) as image:
                self.assertEqual(image.size, (320, 160))
                self.assertEqual(
                    image.info["Source-SHA256"],
                    hashlib.sha256(svg_text.encode()).hexdigest(),
                )
                self.assertEqual(
                    image.info["Configuration-Fingerprint"],
                    manifest["configuration"]["fingerprint"],
                )

        with Image.open(io.BytesIO(artifacts["contact_sheet.png"])) as sheet:
            self.assertEqual(sheet.width, 2 * 320 + 3 * 24)
            self.assertEqual(sheet.info["Included-SVG-Count"], "3")
            self.assertGreater(sheet.height, 320)

    def test_contact_sheet_uses_each_row_pair_height_for_mixed_aspect_views(self) -> None:
        def aspect_svg(title: str, height: int, color: str) -> str:
            return f'''<svg xmlns="http://www.w3.org/2000/svg"
  width="320" height="{height}" viewBox="0 0 320 {height}">
  <title>{title}</title>
  <rect width="320" height="{height}" fill="{color}" />
</svg>'''

        artifacts, manifest = render_visuals(
            {
                "a-landscape.svg": aspect_svg("Landscape A", 80, "#e9c786"),
                "b-landscape.svg": aspect_svg("Landscape B", 100, "#9bc4cb"),
                "c-detail.svg": aspect_svg("Tall detail", 300, "#c8d6b9"),
                "d-detail.svg": aspect_svg("Medium detail", 180, "#e2b7ad"),
            },
            font_paths=FONTS,
            width_px=320,
        )

        expected_height = (
            CONTACT_HEADER_HEIGHT
            + CONTACT_LABEL_HEIGHT
            + 100
            + CONTACT_GUTTER
            + CONTACT_LABEL_HEIGHT
            + 300
            + CONTACT_GUTTER
        )
        self.assertEqual(manifest["contact_sheet"]["height_px"], expected_height)
        with Image.open(io.BytesIO(artifacts["contact_sheet.png"])) as sheet:
            self.assertEqual(sheet.height, expected_height)
            self.assertEqual(sheet.width, 320 * 2 + CONTACT_GUTTER * 3)
            second_row_image_bottom = (
                CONTACT_HEADER_HEIGHT
                + CONTACT_LABEL_HEIGHT
                + 100
                + CONTACT_GUTTER
                + CONTACT_LABEL_HEIGHT
                + 300
                - 1
            )
            self.assertEqual(
                sheet.getpixel((CONTACT_GUTTER + 10, second_row_image_bottom)), (200, 214, 185)
            )

    def test_matching_inputs_and_fonts_reproduce_pixels_and_provenance(self) -> None:
        files = {"pb.svg": sample_svg("PB", "#9bc4cb"), "p2.svg": sample_svg("P2", "#e9c786")}

        first_artifacts, first_manifest = render_visuals(files, font_paths=FONTS, width_px=256)
        second_artifacts, second_manifest = render_visuals(files, font_paths=FONTS, width_px=256)

        self.assertEqual(first_artifacts, second_artifacts)
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(
            first_manifest["sources"]["pb.svg"]["source_sha256"],
            hashlib.sha256(files["pb.svg"].encode()).hexdigest(),
        )

    def test_configuration_fingerprint_includes_font_content_and_renderer_versions(self) -> None:
        configuration = visual_configuration(FONTS, width_px=1400)

        self.assertEqual(configuration["width_px"], 1400)
        self.assertEqual(
            configuration["font_policy"],
            "explicit font files only; system fonts disabled",
        )
        self.assertEqual(
            [font["file_name"] for font in configuration["font_files"]],
            [path.name for path in FONTS],
        )
        self.assertTrue(configuration["renderer_version"])
        self.assertTrue(configuration["rasterizer_version"])
        self.assertTrue(configuration["freetype_version"])
        unhashed = dict(configuration)
        fingerprint = unhashed.pop("fingerprint")
        canonical = json.dumps(
            unhashed,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        self.assertEqual(fingerprint, hashlib.sha256(canonical.encode()).hexdigest())

    def test_requested_export_fails_for_missing_declared_font(self) -> None:
        with self.assertRaisesRegex(FileNotFoundError, "Declared visual font does not exist"):
            render_visuals(
                {"pb.svg": sample_svg("PB", "#9bc4cb")},
                font_paths=(FONT_DIR / "missing.ttf",),
            )

    def test_requested_export_fails_for_invalid_declared_font(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            invalid_font = Path(temporary_directory) / "invalid.ttf"
            invalid_font.write_bytes(b"not a font")
            with self.assertRaisesRegex(ValueError, "not a supported font file"):
                visual_configuration((invalid_font,))

    def test_missing_optional_renderer_metadata_fails_closed(self) -> None:
        missing = __import__("importlib").metadata.PackageNotFoundError("Pillow")
        with (
            patch(
                "dreamhouse.coordination.visual.importlib.metadata.version",
                side_effect=missing,
            ),
            self.assertRaisesRegex(RuntimeError, "requires installed package metadata"),
        ):
            visual_configuration(FONTS)

    def test_uncompiled_css_variables_fail_instead_of_silently_rendering_black(self) -> None:
        from dreamhouse.coordination.visual import _parse_svg

        for style in ('<style>.a {fill:var(--ink)}</style><rect class="a"/>',
                      '<rect fill="var(--ink)"/>', '<rect style="fill:var(--ink)"/>'):
            with self.subTest(style=style), self.assertRaisesRegex(ValueError, "Compile SVG CSS"):
                _parse_svg('<svg xmlns="http://www.w3.org/2000/svg">' + style + '</svg>', name="probe.svg")

    def test_external_resources_are_rejected(self) -> None:
        svg = sample_svg("PB", "#9bc4cb").replace(
            "</svg>", '<image href="../hidden-source.png" /></svg>'
        )

        with self.assertRaisesRegex(ValueError, "External SVG resource references are not allowed"):
            render_visuals({"pb.svg": svg}, font_paths=FONTS, width_px=320)

    def test_relative_svg_callout_navigation_is_not_a_render_resource(self) -> None:
        plain = sample_svg("PB", "#9bc4cb")
        linked = plain.replace(
            "</svg>", '<a href="detail.svg#anchor"><text x="10" y="10">A</text></a></svg>'
        )
        images, _ = render_visuals({"pb.svg": linked}, font_paths=FONTS, width_px=320)
        self.assertIn("pb.png", images)
        for fragment in ("project-finding-register", "html-finding-9"):
            exported, _ = render_visuals(
                {"pb.svg": linked.replace("detail.svg#anchor", "index.html#" + fragment)},
                font_paths=FONTS, width_px=320,
            )
            self.assertIn("pb.png", exported)
        for href in ("../detail.svg#anchor", "https://example.com/detail.svg#anchor",
                     "%2e%2e/secret.svg#target", "drawings/%2E%2E/secret.svg#target"):
            with self.subTest(href=href), self.assertRaises(ValueError):
                render_visuals(
                    {"pb.svg": linked.replace("detail.svg#anchor", href)},
                    font_paths=FONTS,
                    width_px=320,
                )

    def test_pixel_comparison_reports_identical_images_and_skips_contact_sheets(self) -> None:
        svg = sample_svg("PB", "#9bc4cb")
        rendered, _manifest = render_visuals({"pb.svg": svg}, font_paths=FONTS, width_px=320)
        configuration = visual_configuration(FONTS, width_px=320)

        differences, report = compare_visuals(
            source_pngs(rendered) | {"contact_sheet.png": rendered["contact_sheet.png"]},
            source_pngs(rendered) | {"contact_sheet.png": rendered["contact_sheet.png"]},
            current_configuration=configuration,
            baseline_configuration=configuration,
        )

        self.assertEqual(differences, {})
        self.assertEqual(report["status"], "compared")
        self.assertEqual(report["counts"]["pixel_identical"], 1)
        self.assertEqual(report["sources"]["pb.png"]["changed_pixels"], 0)
        self.assertFalse(report["automatic_acceptance"])
        self.assertEqual(report["skipped_contact_sheets"]["current"], ["contact_sheet.png"])

    def test_moving_a_same_size_rectangle_produces_exact_difference_evidence(self) -> None:
        baseline_svg = sample_svg("PB", "#9bc4cb")
        current_svg = baseline_svg.replace('x="30" y="35"', 'x="42" y="35"')
        baseline_rect = next(
            element
            for element in ET.fromstring(baseline_svg)
            if element.tag.endswith("rect") and element.get("fill") != "#fbfaf7"
        )
        current_rect = next(
            element
            for element in ET.fromstring(current_svg)
            if element.tag.endswith("rect") and element.get("fill") != "#fbfaf7"
        )
        self.assertNotEqual(baseline_rect.get("x"), current_rect.get("x"))
        self.assertEqual(
            float(baseline_rect.get("width")) * float(baseline_rect.get("height")),
            float(current_rect.get("width")) * float(current_rect.get("height")),
        )
        baseline, _ = render_visuals({"pb.svg": baseline_svg}, font_paths=FONTS, width_px=320)
        current, _ = render_visuals({"pb.svg": current_svg}, font_paths=FONTS, width_px=320)
        configuration = visual_configuration(FONTS, width_px=320)

        differences, report = compare_visuals(
            source_pngs(current),
            source_pngs(baseline),
            current_configuration=configuration,
            baseline_configuration=configuration,
        )

        result = report["sources"]["pb.png"]
        self.assertEqual(result["status"], "pixel_changed")
        self.assertGreater(result["changed_pixels"], 0)
        self.assertIsNotNone(result["changed_pixel_bounds_xyxy"])
        self.assertIn(result["difference_image"], differences)
        self.assertTrue(report["configuration"]["matches"])

    def test_comparison_reports_added_removed_and_dimension_mismatch_without_resizing(self) -> None:
        baseline = render_visuals(
            {
                "plan.svg": sample_svg("PB", "#9bc4cb"),
                "removed.svg": sample_svg("Removed", "#e9c786"),
            },
            font_paths=FONTS,
            width_px=320,
        )[0]
        current_svg = sample_svg("PB", "#9bc4cb").replace(
            'height="200" viewBox="0 0 400 200"',
            'height="250" viewBox="0 0 400 250"',
        )
        current = render_visuals(
            {
                "plan.svg": current_svg,
                "added.svg": sample_svg("Added", "#c8d6b9"),
            },
            font_paths=FONTS,
            width_px=320,
        )[0]
        configuration = visual_configuration(FONTS, width_px=320)

        differences, report = compare_visuals(
            source_pngs(current),
            source_pngs(baseline),
            current_configuration=configuration,
            baseline_configuration=configuration,
        )

        self.assertEqual(report["status"], "partially_compared_dimension_mismatch")
        self.assertEqual(report["sources"]["added.png"]["status"], "added")
        self.assertEqual(report["sources"]["removed.png"]["status"], "removed")
        self.assertEqual(report["sources"]["plan.png"]["status"], "dimension_mismatch")
        self.assertEqual(differences, {})

    def test_comparison_skips_pixels_when_renderer_configuration_differs(self) -> None:
        rendered, _manifest = render_visuals(
            {"pb.svg": sample_svg("PB", "#9bc4cb")}, font_paths=FONTS, width_px=320
        )
        current_configuration = visual_configuration(FONTS, width_px=320)
        baseline_configuration = visual_configuration(FONTS, width_px=321)

        differences, report = compare_visuals(
            source_pngs(rendered),
            source_pngs(rendered),
            current_configuration=current_configuration,
            baseline_configuration=baseline_configuration,
        )

        self.assertEqual(report["status"], "incompatible_configuration")
        self.assertEqual(report["sources"]["pb.png"]["status"], "configuration_mismatch")
        self.assertEqual(report["counts"]["configuration_mismatch"], 1)
        self.assertEqual(differences, {})


if __name__ == "__main__":
    unittest.main()

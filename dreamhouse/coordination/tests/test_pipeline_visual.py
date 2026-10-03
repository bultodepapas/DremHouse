"""End-to-end package identity, verification, and publication tests for PNG mode."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import (
    CoordinationError,
    json_text,
    resolve_project,
    study_template,
)
from dreamhouse.coordination.pipeline import build_candidate, check_candidate


class VisualPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)
        cls.study = cls.root / "study.json"
        cls.study.write_text(json_text(study_template(resolve_project(), "VISUAL_PIPELINE_TEST")))
        cls.plain_out = cls.root / "plain"
        cls.visual_out = cls.root / "visual"
        cls.plain = build_candidate(cls.study, cls.plain_out)
        cls.visual = build_candidate(cls.study, cls.visual_out, visuals=True, visual_width_px=420)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_rendering_mode_is_part_of_package_identity_and_check_auto_detects_it(self):
        plain_manifest = self.plain["manifest"]
        visual_manifest = self.visual["manifest"]
        self.assertEqual(plain_manifest["input_hash"], visual_manifest["input_hash"])
        self.assertNotEqual(plain_manifest["issue_id"], visual_manifest["issue_id"])
        self.assertIsNone(plain_manifest["rendering"])
        self.assertEqual(visual_manifest["rendering"]["width_px"], 420)

        self.assertEqual(
            check_candidate(self.study, self.plain_out)["manifest"]["issue_id"],
            plain_manifest["issue_id"],
        )
        self.assertEqual(
            check_candidate(self.study, self.visual_out)["manifest"]["issue_id"],
            visual_manifest["issue_id"],
        )

    def test_explicit_check_mode_must_match_the_published_package(self):
        with self.assertRaisesRegex(CoordinationError, "rendering mode differs"):
            check_candidate(self.study, self.plain_out, visuals=True)
        with self.assertRaisesRegex(CoordinationError, "rendering mode differs"):
            check_candidate(self.study, self.visual_out, visuals=False)

    def test_tampered_visual_artifact_is_detected(self):
        issue = Path(self.visual["path"])
        visual_name = next(
            name
            for name in self.visual["manifest"]["artifacts"]
            if name.endswith(".png") and name != "contact_sheet.png"
        )
        artifact = issue / visual_name
        original = artifact.read_bytes()
        try:
            artifact.write_bytes(original + b"tampered")
            with self.assertRaisesRegex(CoordinationError, "artifact"):
                check_candidate(self.study, self.visual_out)
        finally:
            artifact.write_bytes(original)

    def test_native_sheet_review_banner_text_is_actually_rasterized(self):
        from PIL import Image

        issue = Path(self.visual["path"])
        for name in ("architecture-p2-bedroom-windows", "structure-vertical-continuity"):
            svg = ET.parse(issue / "drawings" / f"{name}.svg").getroot()
            _, _, width, _ = map(float, svg.get("viewBox").split())
            banner = next(node for node in svg.iter() if node.get("id") == "review-status-banner")
            background = banner.find("{http://www.w3.org/2000/svg}rect")
            with Image.open(issue / "drawings" / f"{name}.png") as preview:
                # At thumbnail scale white glyphs are antialiased into the dark
                # red background. Test visible contrast, not fully white pixels,
                # and derive the crop from the actual banner geometry.
                first_row = int(float(background.get("y")) * preview.width / width) + 1
                pixels = preview.convert("RGB").crop(
                    (1, first_row, preview.width - 1, preview.height - 1)
                )
                self.assertGreater(
                    sum(r > 170 and g > 100 and b > 90 for r, g, b in pixels.getdata()), 10, name
                )

    def test_visual_render_failure_preserves_the_published_pointer(self):
        pointer = self.visual_out / "latest.json"
        previous = pointer.read_bytes()
        with (
            patch(
                "dreamhouse.coordination.visual.render_visuals",
                side_effect=RuntimeError("synthetic visual renderer failure"),
            ),
            self.assertRaisesRegex(RuntimeError, "synthetic visual renderer failure"),
        ):
            build_candidate(self.study, self.visual_out, visuals=True, visual_width_px=420)
        self.assertEqual(pointer.read_bytes(), previous)
        self.assertFalse(list(self.visual_out.glob(".staging-*")))

    def test_changed_renderer_version_makes_visual_package_stale(self):
        from dreamhouse.coordination import visual

        original_version = visual.importlib.metadata.version

        def changed_version(package):
            version = original_version(package)
            return f"{version}.changed" if package == "resvg-py" else version

        with (
            patch(
                "dreamhouse.coordination.visual.importlib.metadata.version",
                side_effect=changed_version,
            ),
            self.assertRaisesRegex(CoordinationError, "visual renderer/font configuration changed"),
        ):
            check_candidate(self.study, self.visual_out)


if __name__ == "__main__":
    unittest.main()

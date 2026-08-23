from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from dreamhouse.svg.audit import build_collection


SVG_TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"
  viewBox="0 0 100 50" data-revision="{revision}" data-status="graphic-pilot-not-current">
  <title>{title}</title>
  <style>text {{ font-family: DejaVu Sans, sans-serif; }}</style>
  <rect width="100" height="50" fill="#FFFFFF"/>
  <text x="10" y="28" font-size="10" fill="#172A32">{label}</text>
</svg>
"""


class TestSvgAuditCollection(unittest.TestCase):
    def _svg(self, directory: Path, name: str, revision: str) -> Path:
        path = directory / name
        path.write_text(
            SVG_TEMPLATE.format(
                revision=revision,
                title=f"Audit fixture {revision}",
                label=revision,
            ),
            encoding="utf-8",
        )
        return path

    def test_collection_builds_sorted_multiscale_and_contact_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            second = self._svg(root, "a.svg", "GP02")
            first = self._svg(root, "b.svg", "GP01")
            output = root / "audit"

            report = build_collection(
                [second, first],
                output,
                prefix="fixtures",
                widths=(120, 200),
                contact_width=120,
                columns=2,
            )

            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["summary"]["files"], 2)
            self.assertEqual(
                [Path(record["path"]).name for record in report["files"]],
                ["b.svg", "a.svg"],
            )
            self.assertTrue((output / "renders" / "b-120.png").is_file())
            self.assertTrue((output / "renders" / "b-200-grayscale.png").is_file())
            with Image.open(output / "fixtures-contact-120.png") as contact:
                self.assertEqual(contact.width, 288)
            with Image.open(output / "fixtures-contact-120-grayscale.png") as grayscale:
                self.assertEqual(grayscale.mode, "L")

    def test_collection_report_is_deterministic_and_hashes_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            svg = self._svg(root, "pilot.svg", "GP01")
            output = root / "audit"

            first = build_collection(
                [svg], output, prefix="fixture", widths=(120,), contact_width=120
            )
            report_path = output / "fixture-metrics.json"
            first_bytes = report_path.read_bytes()
            second = build_collection(
                [svg], output, prefix="fixture", widths=(120,), contact_width=120
            )

            self.assertEqual(first, second)
            self.assertEqual(report_path.read_bytes(), first_bytes)
            loaded = json.loads(first_bytes)
            self.assertRegex(loaded["files"][0]["sha256"], r"^[0-9a-f]{64}$")

    def test_collection_rejects_empty_duplicate_or_invalid_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            svg = self._svg(root, "pilot.svg", "GP01")
            output = root / "audit"

            with self.assertRaises(ValueError):
                build_collection([], output, prefix="empty")
            with self.assertRaises(ValueError):
                build_collection([svg, svg], output, prefix="duplicate")
            with self.assertRaises(ValueError):
                build_collection([root / "missing.svg"], output, prefix="missing")
            with self.assertRaises(ValueError):
                build_collection([svg], output, prefix="width", widths=(0,))
            with self.assertRaises(ValueError):
                build_collection([svg], output, prefix="width", widths=(120, 120))


if __name__ == "__main__":
    unittest.main()

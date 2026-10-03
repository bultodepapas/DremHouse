"""Reader artifacts keep view purpose, authority and source links explicit."""

import unittest

from dreamhouse.coordination.model import CoordinationError
from dreamhouse.coordination.reader import attach_reading_guide, companion_pages
from dreamhouse.coordination.visual_quality import visual_quality_report

SHEET = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 960">
<title>Upper floor</title><desc>Source extents and open evidence.</desc>
<text>NOT FOR CONSTRUCTION</text><rect width="10" height="10" fill="#172A32"/>
</svg>"""


class ReaderTests(unittest.TestCase):
    def test_pair_links_exist_and_partial_inventory_does_not_invent_a_pair(self):
        page = "<html><head></head><body><header></header></body></html>"
        files = {"plan-p2.svg": SHEET, "drawings/architecture-upper-floor.svg": SHEET}
        linked = attach_reading_guide(page, files)
        self.assertIn('href="drawings/architecture-upper-floor.svg"', linked)
        self.assertIn('href="#section-plan-p2"', linked)
        self.assertNotIn('href="#section-plan-pb"', linked)
        self.assertNotIn(
            'href="#section-plan-p2"', attach_reading_guide(page, {"plan-p2.svg": SHEET})
        )
        self.assertIn(":focus-visible", linked)

    def test_print_and_text_guides_keep_all_sheets_and_no_scale_claim(self):
        files = {"plan-p2.svg": SHEET, "drawings/architecture-upper-floor.svg": SHEET}
        pages = companion_pages(files, {"model_hash": "unchanged-model"})
        for name in files:
            self.assertIn(f'href="{name}"', pages["reading-guide.html"])
            self.assertIn(f'src="{name}"', pages["print.html"])
        self.assertIn("Source extents and open evidence.", pages["reading-guide.html"])
        self.assertEqual(pages["print.html"].count('class="plate"'), 2)
        self.assertIn("no numerical print scale", pages["print.html"])
        self.assertIn("unchanged-model", pages["print.html"])

    def test_reader_rejects_external_artifact_paths(self):
        with self.assertRaisesRegex(ValueError, "Unsafe reader"):
            companion_pages({"../bad.svg": SHEET}, {"model_hash": "same"})

    def test_quality_records_honest_scope_without_certifying_contrast(self):
        report = visual_quality_report({"plan-p2.svg": SHEET}, {"model_hash": "same"})
        self.assertEqual(report["summary"]["svg_count"], 1)
        self.assertEqual(report["summary"]["fundamental_errors"], 0)
        self.assertIn("visual_acceptance_separate", report["status"])
        self.assertEqual(
            report["sheets"][0]["review_tasks"][0]["state"], "manual_or_profile_review_required"
        )

    def test_authority_wording_spanning_tspans_is_not_lost(self):
        content = SHEET.replace("NOT FOR CONSTRUCTION", "NOT <tspan>FOR</tspan> CONSTRUCTION")
        report = visual_quality_report({"plan-p2.svg": content}, {"model_hash": "same"})
        self.assertTrue(report["sheets"][0]["authority_wording_present"])
        self.assertIn("requires rendered review", report["sheets"][0]["authority_visibility"])

    def test_missing_or_encoded_navigation_destination_blocks_candidate(self):
        linked = SHEET.replace(
            "</svg>", '<a href="index.html#html-finding-1"><text>Issue</text></a></svg>'
        )
        files = {"plan-p2.svg": linked, "index.html": '<p id="html-finding-1">Issue</p>'}
        self.assertEqual(
            visual_quality_report(files, {"model_hash": "same"})["summary"][
                "navigation_links_checked"
            ],
            1,
        )
        with self.assertRaisesRegex(CoordinationError, "Missing SVG navigation"):
            visual_quality_report({"plan-p2.svg": linked}, {"model_hash": "same"})
        with self.assertRaisesRegex(CoordinationError, "Unsupported SVG navigation"):
            visual_quality_report(
                {"plan-p2.svg": linked.replace("index.html", "%2e%2e/index.html")},
                {"model_hash": "same"},
            )
        with self.assertRaisesRegex(ValueError, "Unsafe reader"):
            companion_pages({"%2e%2e/bad.svg": SHEET}, {"model_hash": "same"})

    def test_style_mismatch_or_lost_authority_blocks_candidate(self):
        for content in (
            SHEET.replace('fill="#172A32"', 'fill="var(--ink)"'),
            SHEET.replace("NOT FOR CONSTRUCTION", "READY"),
            SHEET.replace("<title>Upper floor</title>", ""),
            SHEET.replace("1440 960", "0 960"),
            SHEET.replace("<text>", '<text display="none">'),
            SHEET.replace("<text>", '<text style="opacity:0">'),
        ):
            with self.subTest(content=content), self.assertRaises(CoordinationError):
                visual_quality_report({"plan-p2.svg": content}, {"model_hash": "same"})


if __name__ == "__main__":
    unittest.main()

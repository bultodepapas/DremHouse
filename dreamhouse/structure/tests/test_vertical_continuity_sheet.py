from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.structure.e1_screening import (
    DEFAULT_E1_SPACE,
    DEFAULT_P2,
    DEFAULT_PB,
    run_screening,
)
from dreamhouse.structure.optimize_roof import DEFAULT_MODEL, DEFAULT_SPACE, _read_json
from dreamhouse.structure.vertical_continuity_sheet import (
    SHEET_NAME,
    build_vertical_continuity_sheet,
)

ROOT = Path(__file__).resolve().parents[3]
ISSUED_SHEET = ROOT / "planos" / "estructura" / SHEET_NAME
SVG_NAMESPACE = "{http://www.w3.org/2000/svg}"


class TestVerticalContinuitySheet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configuration = _read_json(DEFAULT_MODEL)
        cls.roof_space = _read_json(DEFAULT_SPACE)
        cls.e1_space = _read_json(DEFAULT_E1_SPACE)
        cls.pb = _read_json(DEFAULT_PB)
        cls.p2 = _read_json(DEFAULT_P2)
        cls.results = run_screening(
            cls.configuration,
            cls.roof_space,
            cls.e1_space,
            cls.pb,
            cls.p2,
        )
        cls.svg = build_vertical_continuity_sheet(
            cls.configuration,
            cls.pb,
            cls.p2,
            cls.results,
        )
        cls.root = ET.fromstring(cls.svg)

    def test_svg_is_deterministic_valid_and_fail_closed(self):
        second = build_vertical_continuity_sheet(
            self.configuration,
            self.pb,
            self.p2,
            self.results,
        )
        self.assertEqual(self.svg, second)
        self.assertEqual(self.root.attrib["viewBox"], "0 0 1684 1191")
        self.assertIn("NOT FOR CONSTRUCTION", self.svg)
        self.assertNotIn("APPROVED", self.svg.upper())
        metadata = self.root.find(f"{SVG_NAMESPACE}metadata")
        self.assertIsNotNone(metadata)
        payload = json.loads(metadata.text or "")
        self.assertEqual(len(payload["compatible_column_ids"]), 4)
        self.assertFalse(payload["selection_or_construction_authority"])

    def test_graphic_counts_match_the_audited_hypothesis(self):
        classes = [
            set(element.attrib.get("class", "").split()) for element in self.root.iter()
        ]

        def count(class_name: str) -> int:
            return sum(class_name in names for names in classes)

        self.assertEqual(count("full-height-core-column"), 4)
        self.assertEqual(count("rejected-column-line"), 4)
        self.assertEqual(count("tower-column"), 4)
        self.assertEqual(count("tower-side-brace"), 8)
        self.assertEqual(count("side-plane-brace"), 4)
        self.assertEqual(count("moment-frame-beam"), 6)
        self.assertEqual(count("drift-slot"), 1)

    def test_generator_rejects_design_authority_or_unresolved_geometry(self):
        unsafe = copy.deepcopy(self.results)
        unsafe["selection_or_construction_authority"] = True
        with self.assertRaisesRegex(ValueError, "fail-closed"):
            build_vertical_continuity_sheet(self.configuration, self.pb, self.p2, unsafe)

        failed_geometry = copy.deepcopy(self.results)
        failed_geometry["checks"]["vertical_continuity_and_stair_core"][
            "geometry_screen_pass"
        ] = False
        with self.assertRaisesRegex(ValueError, "has not passed"):
            build_vertical_continuity_sheet(
                self.configuration,
                self.pb,
                self.p2,
                failed_geometry,
            )

    def test_issued_sheet_matches_the_generator(self):
        self.assertTrue(ISSUED_SHEET.is_file())
        self.assertEqual(ISSUED_SHEET.read_text(encoding="utf-8"), self.svg)


if __name__ == "__main__":
    unittest.main()

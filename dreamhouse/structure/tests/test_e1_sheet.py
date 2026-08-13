from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.structure.e1_screening import DEFAULT_E1_SPACE, run_screening
from dreamhouse.structure.e1_sheet import SHEET_NAME, build_e1_sheet
from dreamhouse.structure.optimize_roof import DEFAULT_MODEL, DEFAULT_SPACE, _read_json

ROOT = Path(__file__).resolve().parents[3]
ROOFLIGHTS = ROOT / "dreamhouse" / "rooflight_b12.json"
ISSUED_SHEET = ROOT / "planos" / "estructura" / SHEET_NAME
SVG_NAMESPACE = "{http://www.w3.org/2000/svg}"


class TestE1IntegratedSheet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.configuration = _read_json(DEFAULT_MODEL)
        cls.roof_space = _read_json(DEFAULT_SPACE)
        cls.e1_space = _read_json(DEFAULT_E1_SPACE)
        cls.rooflights = _read_json(ROOFLIGHTS)
        cls.results = run_screening(cls.configuration, cls.roof_space, cls.e1_space)
        cls.svg = build_e1_sheet(
            cls.configuration,
            cls.roof_space,
            cls.e1_space,
            cls.rooflights,
            cls.results,
        )
        cls.root = ET.fromstring(cls.svg)

    def test_svg_is_deterministic_valid_and_fail_closed(self):
        second = build_e1_sheet(
            self.configuration,
            self.roof_space,
            self.e1_space,
            self.rooflights,
            self.results,
        )
        self.assertEqual(self.svg, second)
        self.assertEqual(self.root.attrib["viewBox"], "0 0 1684 1191")
        self.assertNotRegex(self.svg.lower(), r"(?:^|[\s=\"',])(?:nan|inf|infinity)(?:[\s\"',/]|$)")
        self.assertIn("NOT FOR CONSTRUCTION", self.svg)

        metadata = self.root.find(f"{SVG_NAMESPACE}metadata")
        self.assertIsNotNone(metadata)
        payload = json.loads(metadata.text or "")
        self.assertFalse(payload["selection_or_construction_authority"])
        self.assertEqual(payload["input_sha256"], self.results["input_sha256"])

    def test_graphic_counts_follow_active_geometry_and_truss_grammar(self):
        classes = [
            set(element.attrib.get("class", "").split()) for element in self.root.iter()
        ]

        def count(class_name: str) -> int:
            return sum(class_name in names for names in classes)

        self.assertEqual(count("roof-truss-line"), 7)
        self.assertEqual(count("rooflight-opening"), 2)
        self.assertEqual(count("p2-longitudinal-beam"), 6)
        self.assertEqual(count("hidden-steel-column"), 6)
        self.assertEqual(count("trial-braced-bay"), 4)
        self.assertEqual(count("truss-member"), 25)
        self.assertEqual(count("truss-node"), 14)
        self.assertEqual(count("top-restraint"), 13)
        self.assertEqual(count("bottom-restraint"), 4)
        self.assertEqual(count("full-height-core-column"), 4)
        self.assertEqual(count("stair-core-study-zone"), 1)

    def test_calculated_evidence_is_embedded_without_claiming_design(self):
        member = self.results["checks"]["local_and_biaxial_member_stability"]
        diaphragm = self.results["checks"]["diaphragm"]["result"]
        erection = self.results["checks"]["erection"]["result"]
        self.assertIn(f"interaction {member['maximum_interaction_ratio']:.3f}", self.svg)
        self.assertIn(f"{diaphragm['required_unit_shear_kn_m']:.2f} kN/m", self.svg)
        self.assertIn(f"HOOK {erection['required_hook_load_kn']:.1f} kN", self.svg)
        self.assertGreaterEqual(self.svg.count("BLOCKED"), 12)
        self.assertNotIn("APPROVED", self.svg.upper())

    def test_generator_rejects_any_release_authority(self):
        unsafe = copy.deepcopy(self.results)
        unsafe["selection_or_construction_authority"] = True
        with self.assertRaisesRegex(ValueError, "fail-closed"):
            build_e1_sheet(
                self.configuration,
                self.roof_space,
                self.e1_space,
                self.rooflights,
                unsafe,
            )

    def test_issued_sheet_matches_the_calculation_linked_generator(self):
        self.assertTrue(ISSUED_SHEET.is_file())
        issued = ISSUED_SHEET.read_text(encoding="utf-8")
        self.assertEqual(issued, self.svg)
        ET.fromstring(issued)


if __name__ == "__main__":
    unittest.main()

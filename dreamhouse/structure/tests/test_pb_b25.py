from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b25 import generate, load_b25_model, validate_b25


class TestPBB25(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b25_model()
        cls.checks = validate_b25(cls.model)
        cls.by_rule = {item["rule_id"]: item for item in cls.checks}

    def test_worktops_fill_the_bay_without_excessive_depth(self):
        for workstation in self.model["workstations"]:
            self.assertEqual(workstation["worktop_length"], 3.0)
            self.assertEqual(workstation["worktop_depth"], 0.9)
        self.assertEqual(self.by_rule["PB-WS-FULL-BAY-WORKTOP"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-WS-CONTROLLED-DEPTH"]["status"], "PASS")

    def test_large_drawer_cabinets_are_mirrored_and_keep_knee_space(self):
        for workstation in self.model["workstations"]:
            self.assertEqual(workstation["drawer_cabinet_count"], 2)
            self.assertEqual(workstation["drawer_cabinet_width"], 0.7)
            self.assertEqual(workstation["drawer_levels"], 3)
            self.assertEqual(workstation["central_knee_clear_width"], 1.6)
        self.assertEqual(self.by_rule["PB-WS-CABINETRY-MIRROR"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-WS-KNEE-CLEARANCE"]["status"], "PASS")

    def test_b24_symmetry_and_open_professional_gates_are_retained(self):
        self.assertEqual(self.by_rule["PB-WS-MIRROR"]["status"], "PASS")
        self.assertEqual(self.by_rule["PB-WS-GLAZING-SYMMETRY"]["status"], "PASS")
        self.assertEqual(
            self.by_rule["PB-WS-A-MAIN-GLAZING-JUNCTION"]["status"], "OPEN"
        )
        self.assertEqual(self.by_rule["PB-CAR-BENCH-LIFT-INTERFACE"]["status"], "OPEN")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_drawings_show_full_width_worktops_and_drawer_banks(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            plan = target.joinpath(
                "DH-ARQ-PLN-001-R06_PB-ENLARGED-INTEGRATED-WORKSTATIONS.svg"
            ).read_text(encoding="utf-8")
            detail = target.joinpath(
                "DH-ARQ-DET-006-R01_ENLARGED-WORKSTATION-CABINET-FAMILY.svg"
            ).read_text(encoding="utf-8")
            self.assertEqual(plan.count(">3D</text>"), 4)
            self.assertIn("D-069 enlarges the workstation/cabinet assembly only.", plan)
            self.assertIn("PB ENLARGED WORKSTATION + CABINET FAMILY", detail)
            self.assertIn("DET-006-R01", detail)
            self.assertIn("3.00 m TEST LENGTH", detail)
            self.assertIn("0.90 m TEST DEPTH", detail)
            self.assertIn("two large suspended steel three-drawer cabinets", detail)

    def test_manifest_and_svg_outputs_are_valid(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(self.model, target)
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-25-PB")
            self.assertEqual(manifest["source"], "dreamhouse/pb_b25_delta.json")
            for filename in manifest["outputs"]:
                if filename.endswith(".svg"):
                    ET.fromstring(target.joinpath(filename).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

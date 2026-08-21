from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b37 import generate, load_b37_model, validate_b37


class TestPBB37(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b37_model()
        cls.checks = validate_b37(cls.model)

    def test_desk_windows_align_and_technical_sills_do_not_move(self):
        workstations = {item["side"]: item for item in self.model["workstations"]}
        openings = {item["side"]: item for item in self.model["workstation_glazing"]}
        for side in ("A", "B"):
            self.assertEqual(openings[side]["sill"], .75)
            self.assertEqual(openings[side]["sill"], workstations[side]["worktop_height"])
        self.assertEqual(openings["A"]["sill"] + openings["A"]["height"], 3.80)
        self.assertEqual(openings["B"]["sill"] + openings["B"]["height"], 2.55)
        self.assertTrue(all(item["sill"] == .90 for item in self.model["technical_glazing"]))

    def test_dining_window_remains_an_excluded_study(self):
        study = self.model["optional_opening_studies"][0]
        self.assertEqual(study["id"], "GLZ-DINING-STUDY-B")
        self.assertTrue(study["status"].startswith("study only"))

    def test_generated_elevations_schedule_and_totals_are_coherent(self):
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            for filename in (
                "DH-ARQ-ELE-002-R07_REAR-WINDOW-DAYLIGHT.svg",
                "DH-ARQ-ELE-003-R10_SIDE-A-WINDOW-DAYLIGHT.svg",
                "DH-ARQ-ELE-004-R10_SIDE-B-WINDOW-DAYLIGHT.svg",
                "DH-ARQ-DET-006-R03_PB-DESK-WINDOW-INTERFACE.svg",
                "DH-ARQ-SCH-001-R00_D083-WINDOW-SCHEDULE.svg",
            ):
                ET.parse(target / filename)
            schedule = json.loads((target / "opening_schedule.json").read_text(encoding="utf-8"))
            self.assertEqual(schedule["area_totals_m2"]["vertical_glazing"], 123.84)
            self.assertEqual(schedule["area_totals_m2"]["rooflight"], 23.04)
            self.assertEqual(len(schedule["study_items_excluded_from_totals"]), 1)


if __name__ == "__main__":
    unittest.main()

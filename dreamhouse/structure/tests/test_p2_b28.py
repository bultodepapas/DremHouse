from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b28 import generate, load_b28_model, validate_b28


class TestP2B28(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b28_model()
        cls.checks = validate_b28(cls.model)
        cls.windows = {item["id"]: item for item in cls.model["windows"]}

    def test_bedroom_family_uses_repeated_modules_and_one_vertical_datum(self):
        for window_id in ("W-H1", "W-H2", "W-G", "W-M-LAT-A"):
            item = self.windows[window_id]
            self.assertAlmostEqual(item["to"] - item["from"], 3.60)
            self.assertEqual(item["modules"], 3)
        rear = self.windows["W-M-REAR"]
        self.assertAlmostEqual(rear["to"] - rear["from"], 2.40)
        self.assertEqual(rear["modules"], 2)
        self.assertTrue(
            all(
                item["sill"] == .05 and item["height"] == 2.90
                for key, item in self.windows.items()
                if key in {"W-H1", "W-H2", "W-G", "W-M-LAT-A", "W-M-REAR"}
            )
        )

    def test_non_bedroom_openings_remain_unchanged(self):
        self.assertEqual((self.windows["W-WELL"]["sill"], self.windows["W-WELL"]["height"]), (1.4, 1.2))
        self.assertEqual((self.windows["W-EGRESS-P2"]["sill"], self.windows["W-EGRESS-P2"]["height"]), (.9, 1.2))

    def test_generated_issue_is_valid_and_traceable(self):
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            detail = target / "DH-ARQ-DET-008-R00_P2-BEDROOM-WINDOW-FAMILY.svg"
            ET.parse(detail)
            manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["decision"], "D-083")
            self.assertEqual(manifest["revision"], "0.3-draft-28-P2")
            self.assertIn(detail.name, manifest["outputs"])


if __name__ == "__main__":
    unittest.main()

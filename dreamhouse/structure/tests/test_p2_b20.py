from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import build_access_diagram, build_plan, generate, validate_model
from dreamhouse.generate_p2_b20 import DELTA, load_b20_model


class TestP2B20(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b20_model()
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)
        cls.access = build_access_diagram(cls.model)

    def test_phase_boundary_is_hidden_only_on_main_plan(self):
        self.assertTrue(self.model["hide_phase_boundary_on_plan"])
        self.assertNotIn("ONE ISOLATABLE F1 / F2 BOUNDARY", self.plan)
        self.assertNotIn('class="phase-boundary"', self.plan)
        self.assertNotIn("temporary-open-plan-boundary", self.plan)
        self.assertNotIn("F1 / F2 boundary", self.plan)
        self.assertIn("PHASING LOGIC", self.access)
        self.assertIn('stroke="#76558f" stroke-width="3" stroke-dasharray="9 6"', self.access)

    def test_phase_control_remains_active_in_model(self):
        by_rule = {item["rule_id"]: item for item in self.checks}
        self.assertEqual(self.model["phase_boundary_y"], 11.0)
        self.assertEqual(by_rule["P2-PHASING"]["status"], "PASS")
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)

    def test_plan_records_graphic_revision(self):
        self.assertIn("D-064 · CLEAN P2 PLAN GRAPHICS", self.plan)
        self.assertIn("R17", self.plan)
        ET.fromstring(self.plan)
        ET.fromstring(self.access)

    def test_generation_manifest_records_delta_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(
                self.model,
                target,
                source_path=DELTA,
                generator_name="dreamhouse/generate_p2_b20.py",
            )
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-20-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b20_delta.json")
            self.assertEqual(manifest["supersedes"], "0.3-draft-19-P2 / R16")


if __name__ == "__main__":
    unittest.main()

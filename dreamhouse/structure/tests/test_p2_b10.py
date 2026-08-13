from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import (
    build_access_diagram,
    build_owner_priorities_detail,
    build_plan,
    generate,
    load_model,
    output_names,
    validate_model,
)

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "dreamhouse" / "p2_b10.json"
OUT = ROOT / "planos" / "conceptual_v0.3_b10_p2"


class TestP2B10(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_model(DATA)
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)
        cls.access = build_access_diagram(cls.model)
        cls.detail = build_owner_priorities_detail(cls.model)

    def test_owner_priorities_close_without_geometry_failure(self):
        self.assertEqual(sum(item["status"] == "PASS" for item in self.checks), 20)
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        self.assertEqual(sum(item["status"] == "OPEN" for item in self.checks), 3)
        by_rule = {item["rule_id"]: item for item in self.checks}
        for rule_id in (
            "P2-PRIMARY-PROGRAMME",
            "PB-LAUNDRY-RESERVE",
            "P2-RETRACTABLE-STAIR-RESERVE",
            "P2-EDGE-TRUSS-BRIEF",
        ):
            self.assertEqual(by_rule[rule_id]["status"], "PASS")

    def test_sheets_are_valid_deterministic_and_show_new_interfaces(self):
        self.assertEqual(self.plan, build_plan(self.model))
        self.assertEqual(self.access, build_access_diagram(self.model))
        self.assertEqual(self.detail, build_owner_priorities_detail(self.model))
        for sheet in (self.plan, self.access, self.detail):
            ET.fromstring(sheet)
        self.assertIn("retractable-stair-reserve", self.plan)
        self.assertIn("reserved-second-route", self.access)
        self.assertIn("pb-laundry-reserve", self.detail)
        self.assertIn("large-exposed-truss-web", self.detail)

    def test_generation_manifest_and_issued_files_match(self):
        plan_name, access_name, detail_name = output_names(self.model)
        self.assertIsNotNone(detail_name)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(
                self.model,
                target,
                source_path=DATA,
                generator_name="dreamhouse/generate_p2_b10.py",
            )
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source"], "dreamhouse/p2_b10.json")
            self.assertEqual(target.joinpath(plan_name).read_text(encoding="utf-8"), self.plan)
            self.assertEqual(target.joinpath(access_name).read_text(encoding="utf-8"), self.access)
            self.assertEqual(target.joinpath(detail_name).read_text(encoding="utf-8"), self.detail)
        self.assertEqual(OUT.joinpath(plan_name).read_text(encoding="utf-8"), self.plan)


if __name__ == "__main__":
    unittest.main()

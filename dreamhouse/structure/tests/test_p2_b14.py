from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import (
    acoustic_detail_name,
    build_access_diagram,
    build_acoustic_partition_detail,
    build_hall_edge_detail,
    build_owner_priorities_detail,
    build_plan,
    generate,
    hall_edge_detail_name,
    load_model,
    output_names,
    validate_model,
)

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "dreamhouse" / "p2_b14.json"
OUT = ROOT / "planos" / "conceptual_v0.3_b14_p2"


class TestP2B14(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_model(DATA)
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)
        cls.access = build_access_diagram(cls.model)
        cls.owner_detail = build_owner_priorities_detail(cls.model)
        cls.wall_detail = build_acoustic_partition_detail(cls.model)
        cls.edge_detail = build_hall_edge_detail(cls.model)

    def test_d058_continuous_hall_edge_passes(self):
        self.assertEqual(sum(item["status"] == "PASS" for item in self.checks), 22)
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        self.assertEqual(sum(item["status"] == "OPEN" for item in self.checks), 3)
        by_rule = {item["rule_id"]: item for item in self.checks}
        self.assertEqual(by_rule["P2-W04-HALL-EDGE"]["status"], "PASS")
        self.assertEqual(by_rule["P2-W01-250"]["status"], "PASS")
        self.assertEqual(self.model["envelope"]["hall_edge_wall"], 0.25)

    def test_plan_cuts_only_the_scheduled_glazing_from_p2_w04(self):
        self.assertEqual(self.plan, build_plan(self.model))
        self.assertIn('data-wall-type="P2-W04"', self.plan)
        self.assertIn('class="hall-edge-acoustic-opening"', self.plan)
        self.assertIn('data-opening-id="GLZ-DECK"', self.plan)
        self.assertIn("P2-W04 / DOUBLE-HEIGHT HALL", self.plan)

    def test_sheets_are_valid_and_expose_limits_of_authority(self):
        self.assertEqual(self.edge_detail, build_hall_edge_detail(self.model))
        for sheet in (
            self.plan,
            self.access,
            self.owner_detail,
            self.wall_detail,
            self.edge_detail,
        ):
            ET.fromstring(sheet)
        self.assertIn("18.00 m CONTINUOUS ENCLOSURE", self.edge_detail)
        self.assertIn("only GLZ-DECK interrupts", self.edge_detail)
        self.assertIn("no STC/Rw", self.edge_detail)
        self.assertIn("NOT FOR", self.edge_detail)

    def test_generation_manifest_and_issued_files_match(self):
        plan_name, access_name, owner_name = output_names(self.model)
        wall_name = acoustic_detail_name(self.model)
        edge_name = hall_edge_detail_name(self.model)
        self.assertIsNotNone(owner_name)
        self.assertIsNotNone(wall_name)
        self.assertIsNotNone(edge_name)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(
                self.model,
                target,
                source_path=DATA,
                generator_name="dreamhouse/generate_p2_b14.py",
            )
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source"], "dreamhouse/p2_b14.json")
            self.assertEqual(target.joinpath(plan_name).read_text(encoding="utf-8"), self.plan)
            self.assertEqual(target.joinpath(access_name).read_text(encoding="utf-8"), self.access)
            self.assertEqual(target.joinpath(owner_name).read_text(encoding="utf-8"), self.owner_detail)
            self.assertEqual(target.joinpath(wall_name).read_text(encoding="utf-8"), self.wall_detail)
            self.assertEqual(target.joinpath(edge_name).read_text(encoding="utf-8"), self.edge_detail)
        self.assertEqual(OUT.joinpath(plan_name).read_text(encoding="utf-8"), self.plan)


if __name__ == "__main__":
    unittest.main()

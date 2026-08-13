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
    build_exterior_wall_detail,
    build_hall_edge_detail,
    build_owner_priorities_detail,
    build_plan,
    exterior_wall_detail_name,
    generate,
    hall_edge_detail_name,
    load_model,
    output_names,
    validate_model,
)

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "dreamhouse" / "p2_b15.json"
OUT = ROOT / "planos" / "conceptual_v0.3_b15_p2"


class TestP2B15(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_model(DATA)
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)
        cls.access = build_access_diagram(cls.model)
        cls.owner_detail = build_owner_priorities_detail(cls.model)
        cls.partition_detail = build_acoustic_partition_detail(cls.model)
        cls.hall_detail = build_hall_edge_detail(cls.model)
        cls.exterior_detail = build_exterior_wall_detail(cls.model)

    def test_d059_double_frame_exterior_wall_passes(self):
        self.assertEqual(sum(item["status"] == "PASS" for item in self.checks), 23)
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        self.assertEqual(sum(item["status"] == "OPEN" for item in self.checks), 4)
        by_rule = {item["rule_id"]: item for item in self.checks}
        self.assertEqual(by_rule["P2-W05-300"]["status"], "PASS")
        self.assertEqual(by_rule["P2-W04-HALL-EDGE"]["status"], "PASS")
        self.assertEqual(by_rule["P2-CIRCULATION"]["status"], "PASS")
        self.assertEqual(self.model["envelope"]["exterior_wall"], 0.30)

    def test_plan_draws_three_exterior_edges_and_cuts_scheduled_openings(self):
        self.assertEqual(self.plan, build_plan(self.model))
        self.assertEqual(self.plan.count('data-wall-type="P2-W05"'), 3)
        self.assertEqual(self.plan.count('class="p2-w05-window-opening"'), 6)
        self.assertIn("LATERAL A / P2-W05", self.plan)
        self.assertIn("LATERAL B / P2-W05", self.plan)
        self.assertIn("REAR FACADE / P2-W05", self.plan)

    def test_exterior_detail_is_valid_and_keeps_industrial_finish_outside(self):
        self.assertEqual(self.exterior_detail, build_exterior_wall_detail(self.model))
        for sheet in (
            self.plan,
            self.access,
            self.owner_detail,
            self.partition_detail,
            self.hall_detail,
            self.exterior_detail,
        ):
            ET.fromstring(sheet)
        self.assertIn("CORRUGATED RAINSCREEN · OUTSIDE ONLY", self.exterior_detail)
        self.assertIn("NO VISIBLE SHEET / FRAME / STEEL / SERVICES", self.exterior_detail)
        self.assertIn("no U-value, STC/Rw or fire rating", self.exterior_detail)
        self.assertIn("NOT FOR", self.exterior_detail)

    def test_generation_manifest_and_issued_files_match(self):
        plan_name, access_name, owner_name = output_names(self.model)
        partition_name = acoustic_detail_name(self.model)
        hall_name = hall_edge_detail_name(self.model)
        exterior_name = exterior_wall_detail_name(self.model)
        self.assertIsNotNone(owner_name)
        self.assertIsNotNone(partition_name)
        self.assertIsNotNone(hall_name)
        self.assertIsNotNone(exterior_name)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            generate(
                self.model,
                target,
                source_path=DATA,
                generator_name="dreamhouse/generate_p2_b15.py",
            )
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source"], "dreamhouse/p2_b15.json")
            self.assertEqual(target.joinpath(plan_name).read_text(encoding="utf-8"), self.plan)
            self.assertEqual(target.joinpath(access_name).read_text(encoding="utf-8"), self.access)
            self.assertEqual(target.joinpath(owner_name).read_text(encoding="utf-8"), self.owner_detail)
            self.assertEqual(
                target.joinpath(partition_name).read_text(encoding="utf-8"),
                self.partition_detail,
            )
            self.assertEqual(target.joinpath(hall_name).read_text(encoding="utf-8"), self.hall_detail)
            self.assertEqual(
                target.joinpath(exterior_name).read_text(encoding="utf-8"),
                self.exterior_detail,
            )
        self.assertEqual(OUT.joinpath(plan_name).read_text(encoding="utf-8"), self.plan)


if __name__ == "__main__":
    unittest.main()

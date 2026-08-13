from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import (
    ACCESS_NAME,
    OUT,
    PLAN_NAME,
    P2ModelError,
    build_access_diagram,
    build_plan,
    generate,
    load_model,
    net_area,
    validate_model,
)


class TestP2B09(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_model()
        cls.checks = validate_model(cls.model)
        cls.plan = build_plan(cls.model)
        cls.access = build_access_diagram(cls.model)
        cls.root = ET.fromstring(cls.plan)

    def test_model_closes_and_reports_only_declared_open_gates(self):
        self.assertEqual(sum(item["status"] == "PASS" for item in self.checks), 16)
        self.assertEqual(sum(item["status"] == "FAIL" for item in self.checks), 0)
        self.assertEqual(sum(item["status"] == "OPEN" for item in self.checks), 4)
        gross = sum(space["w"] * space["d"] for space in self.model["spaces"])
        self.assertAlmostEqual(gross, 270.0)

    def test_child_bedrooms_retain_d042_equivalence(self):
        spaces = {space["id"]: space for space in self.model["spaces"]}
        envelope = self.model["envelope"]
        delta = abs(net_area(spaces["H1-D"], envelope) - net_area(spaces["H2-D"], envelope))
        self.assertAlmostEqual(delta, 0.24, places=2)
        self.assertLessEqual(delta, 1.0)

    def test_plan_is_deterministic_valid_and_graphically_complete(self):
        self.assertEqual(self.plan, build_plan(self.model))
        self.assertEqual(self.access, build_access_diagram(self.model))
        self.assertEqual(self.root.attrib["viewBox"], "0 0 1684 1191")
        self.assertIn("NOT FOR", self.plan)
        self.assertNotIn("equality exact", self.plan.lower())

        elements = list(self.root.iter())

        def count(class_name: str) -> int:
            return sum(class_name in item.attrib.get("class", "").split() for item in elements)

        self.assertEqual(count("door-opening"), 23)
        self.assertEqual(count("d048-column-reservation"), 4)
        self.assertEqual(count("exterior-window"), 6)
        self.assertEqual(count("stair-tread"), 21)

    def test_generator_fails_closed_when_a_door_leaves_its_shared_wall(self):
        invalid = copy.deepcopy(self.model)
        invalid["doors"][0]["at"] = 0.0
        with self.assertRaisesRegex(P2ModelError, "P2-DOOR-GEOMETRY"):
            build_plan(invalid)

    def test_generator_fails_closed_when_access_graph_is_broken(self):
        invalid = copy.deepcopy(self.model)
        invalid["doors"] = [door for door in invalid["doors"] if door["id"] != "D-WELL"]
        with self.assertRaisesRegex(P2ModelError, "P2-ACCESS-GRAPH"):
            build_plan(invalid)

    def test_generation_manifest_and_issued_drawings_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(self.model, target)
            self.assertEqual(report["failed"], 0)
            self.assertEqual(target.joinpath(PLAN_NAME).read_text(encoding="utf-8"), self.plan)
            self.assertEqual(target.joinpath(ACCESS_NAME).read_text(encoding="utf-8"), self.access)
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["source"], "dreamhouse/p2_b09.json")

        self.assertEqual(OUT.joinpath(PLAN_NAME).read_text(encoding="utf-8"), self.plan)
        self.assertEqual(OUT.joinpath(ACCESS_NAME).read_text(encoding="utf-8"), self.access)


if __name__ == "__main__":
    unittest.main()

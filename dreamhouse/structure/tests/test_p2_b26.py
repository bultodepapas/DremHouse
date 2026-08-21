from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import build_plan, generate, validate_model
from dreamhouse.generate_p2_b25 import load_b25_model
from dreamhouse.generate_p2_b26 import DELTA, load_b26_model


def elements_with_class(svg: str, css_class: str) -> list[ET.Element]:
    root = ET.fromstring(svg)
    return [
        element
        for element in root.iter()
        if css_class in element.attrib.get("class", "").split()
    ]


class TestP2B26(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b26_model()
        cls.plan = build_plan(cls.model)

    def test_exterior_corner_strokes_overlap_cleanly(self):
        exterior = elements_with_class(self.plan, "exterior-wall")
        interior_reading = elements_with_class(
            self.plan, "p2-w05-refined-interior-reading"
        )
        self.assertEqual(len(exterior), 3)
        self.assertEqual(len(interior_reading), 3)
        self.assertTrue(
            all(element.attrib["stroke-linecap"] == "square" for element in exterior)
        )
        self.assertTrue(
            all(
                element.attrib["stroke-linecap"] == "square"
                for element in interior_reading
            )
        )

    def test_graphic_correction_does_not_change_wall_geometry_or_thickness(self):
        predecessor = build_plan(load_b25_model())
        old_edges = elements_with_class(predecessor, "exterior-wall")
        new_edges = elements_with_class(self.plan, "exterior-wall")
        geometry_attributes = ("x1", "y1", "x2", "y2", "stroke-width", "data-wall-type")
        self.assertEqual(
            [[edge.attrib[key] for key in geometry_attributes] for edge in old_edges],
            [[edge.attrib[key] for key in geometry_attributes] for edge in new_edges],
        )
        self.assertTrue(
            all(element.attrib["stroke-linecap"] == "butt" for element in old_edges)
        )
        self.assertEqual(
            self.model["wall_schedule"], load_b25_model()["wall_schedule"]
        )

    def test_drawings_and_manifest_are_deterministic(self):
        self.assertEqual(sum(item["status"] == "FAIL" for item in validate_model(self.model)), 0)
        self.assertEqual(self.plan, build_plan(self.model))
        ET.fromstring(self.plan)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(
                self.model,
                target,
                source_path=DELTA,
                generator_name="dreamhouse/generate_p2_b26.py",
            )
            self.assertEqual(report["failed"], 0)
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-26-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b26_delta.json")


if __name__ == "__main__":
    unittest.main()

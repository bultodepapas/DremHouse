from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET

from dreamhouse.generate_p2_b09 import (
    build_access_diagram,
    build_owner_priorities_detail,
    build_plan,
    generate,
    validate_model,
)
from dreamhouse.generate_p2_b26 import load_b26_model
from dreamhouse.generate_p2_b27 import DELTA, load_b27_model
from dreamhouse.generate_pb_b36 import load_b36_model


def elements_with_class(svg: str, css_class: str) -> list[ET.Element]:
    root = ET.fromstring(svg)
    return [
        element
        for element in root.iter()
        if css_class in element.attrib.get("class", "").split()
    ]


class TestP2B27(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = load_b27_model()
        cls.plan = build_plan(cls.model)
        cls.access = build_access_diagram(cls.model)
        cls.detail = build_owner_priorities_detail(cls.model)

    def test_replaces_inclined_stair_with_rescue_window_and_vertical_ladder(self):
        reserve = self.model["egress_reserve"]
        self.assertEqual(reserve["system"], "vertical_foldout_escape_ladder")
        self.assertEqual(reserve["deployment_direction"], "perpendicular_to_wall")
        self.assertNotIn("retracted_clearance_above_grade_m", reserve)
        self.assertEqual(len(elements_with_class(self.plan, "rescue-window")), 1)
        self.assertEqual(len(elements_with_class(self.plan, "foldout-ladder-closed-profile")), 1)
        self.assertEqual(len(elements_with_class(self.plan, "egress-door")), 0)
        self.assertEqual(len(elements_with_class(self.detail, "deployed-stair")), 0)
        self.assertEqual(len(elements_with_class(self.detail, "foldout-ladder-fixed-rail")), 2)
        self.assertEqual(len(elements_with_class(self.detail, "foldout-ladder-mobile-rail")), 1)
        self.assertEqual(len(elements_with_class(self.detail, "foldout-ladder-rung")), 13)

    def test_detail_uses_one_real_proportional_scale(self):
        scale = (610.0 - 390.0) / self.model["egress_reserve"]["served_level_m"]
        window = elements_with_class(self.detail, "operable-rescue-window")[0]
        self.assertTrue(math.isclose(float(window.attrib["width"]), 1.0 * scale))
        self.assertTrue(math.isclose(float(window.attrib["height"]), 1.2 * scale))

        rungs = elements_with_class(self.detail, "foldout-ladder-rung")
        for rung in rungs:
            self.assertTrue(
                math.isclose(
                    float(rung.attrib["x2"]) - float(rung.attrib["x1"]),
                    self.model["egress_reserve"]["rung_width_m"] * scale,
                )
            )
        pitches = [
            float(second.attrib["y1"]) - float(first.attrib["y1"])
            for first, second in zip(rungs, rungs[1:])
        ]
        self.assertTrue(
            all(
                math.isclose(
                    pitch,
                    self.model["egress_reserve"]["rung_spacing_m"] * scale,
                )
                for pitch in pitches
            )
        )
        self.assertTrue(
            math.isclose(
                610.0 - float(rungs[-1].attrib["y1"]),
                self.model["egress_reserve"]["bottom_rung_above_grade_m"] * scale,
            )
        )

    def test_window_ladder_transfer_and_pb_openings_are_screened(self):
        reserve = self.model["egress_reserve"]
        window = next(
            item for item in self.model["windows"] if item["id"] == reserve["rescue_opening_id"]
        )
        self.assertEqual(window["room_id"], reserve["access_space"])
        self.assertTrue(window["escape_rescue"])
        self.assertTrue(
            math.isclose(
                window["from"] - reserve["ladder_axis_y"],
                reserve["jamb_offset_m"],
                abs_tol=1e-9,
            )
        )
        pb = load_b36_model()
        nearest = next(
            item
            for item in pb["exterior_doors"]
            if item["id"] == reserve["pb_opening_screen"]["nearest_opening_id"]
        )
        self.assertTrue(
            math.isclose(
                nearest["y"] + nearest["width"],
                reserve["pb_opening_screen"]["nearest_opening_to_y"],
                abs_tol=1e-9,
            )
        )
        self.assertTrue(
            math.isclose(
                reserve["pb_opening_screen"]["clear_zone_from_y"]
                - (nearest["y"] + nearest["width"]),
                reserve["pb_opening_screen"]["minimum_clearance_m"],
                abs_tol=1e-9,
            )
        )

    def test_d082_preserves_wall_geometry_and_is_explicitly_supplementary(self):
        predecessor = load_b26_model()
        self.assertEqual(self.model["wall_schedule"], predecessor["wall_schedule"])
        self.assertEqual(self.model["spaces"], predecessor["spaces"])
        self.assertEqual(self.model["doors"], predecessor["doors"])
        self.assertEqual(
            self.model["egress_reserve"]["code_role"],
            "supplementary_escape_rescue_device",
        )
        self.assertIn("not credited", self.model["egress_reserve"]["status"])
        self.assertEqual(len(elements_with_class(self.access, "supplementary-rescue-route")), 1)

    def test_drawings_and_manifest_are_deterministic(self):
        self.assertEqual(
            sum(item["status"] == "FAIL" for item in validate_model(self.model)),
            0,
        )
        self.assertEqual(self.plan, build_plan(self.model))
        for svg in (self.plan, self.access, self.detail):
            ET.fromstring(svg)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            report = generate(
                self.model,
                target,
                source_path=DELTA,
                generator_name="dreamhouse/generate_p2_b27.py",
            )
            self.assertEqual(report["failed"], 0)
            manifest = json.loads(target.joinpath("manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["revision"], "0.3-draft-27-P2")
            self.assertEqual(manifest["source"], "dreamhouse/p2_b27_delta.json")


if __name__ == "__main__":
    unittest.main()

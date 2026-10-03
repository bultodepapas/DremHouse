import hashlib
import json
from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b05 import front_elevation_sheet, plan_sheet

ROOT = Path(__file__).resolve().parents[3]


def _source_pb() -> dict:
    return json.loads((ROOT / "dreamhouse/pb_b05.json").read_text(encoding="utf-8"))


class ConnectedFrontDrawingTests(TestCase):
    def test_legacy_default_rendering_remains_byte_identical(self) -> None:
        model = _source_pb()
        self.assertEqual(
            hashlib.sha256(front_elevation_sheet(model).encode()).hexdigest(),
            "e10437b1ccc45e4f4284f7af26971d20ece8abda69e9637554bc16661ff26158",
        )
        self.assertEqual(
            hashlib.sha256(plan_sheet(model).encode()).hexdigest(),
            "be0572bf67267a2156e5b80bee846e877519254b922f616874fec6a9363210d9",
        )

    def test_connected_front_tracks_door_position_size_and_sill_in_geometry_and_dims(self) -> None:
        model = deepcopy(_source_pb())
        car = next(item for item in model["front_openings"] if item["id"] == "CAR")
        car.update({"y0": 2.0, "width": 4.4, "height": 4.1, "sill": 0.25})

        rendered = front_elevation_sheet(model, parameterize=True)
        root = ET.fromstring(rendered)
        car_frame = next(
            element
            for element in root.iter()
            if element.tag.endswith("rect") and element.get("fill") == "#39484e"
        )
        self.assertAlmostEqual(float(car_frame.get("x")), 264.0)
        self.assertAlmostEqual(float(car_frame.get("y")), 375.3)
        self.assertAlmostEqual(float(car_frame.get("width")), 272.8)
        self.assertAlmostEqual(float(car_frame.get("height")), 254.2)

        visible_text = "".join(root.itertext())
        self.assertIn("4.40 × 4.10 m · sill +0.25 m", visible_text)
        self.assertIn("2,00", visible_text)
        self.assertIn("4,40", visible_text)
        self.assertIn("1,80", visible_text)
        self.assertIn("Opening positions, widths, sills and heads", visible_text)
        self.assertNotIn("Dos portones industriales iguales", visible_text)

    def test_connected_plan_labels_actual_technical_opening_width(self) -> None:
        model = deepcopy(_source_pb())
        technical = next(item for item in model["technical_glazing"] if item["id"] == "GLZ-CAR")
        technical["x1"] = 9.1

        self.assertIn("VENTANAL CAR PROJECT · 7,60 m", plan_sheet(model, parameterize=True))
        self.assertIn("VENTANAL CAR PROJECT · 7,20 m", plan_sheet(model))


if __name__ == "__main__":
    import unittest

    unittest.main()

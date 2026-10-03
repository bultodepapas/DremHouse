import hashlib
from copy import deepcopy
from unittest import TestCase
from xml.etree import ElementTree as ET

from dreamhouse.generate_pb_b36 import (
    load_b36_model,
    technical_workbench_detail_sheet,
)


class ConnectedTechnicalBenchDrawingTests(TestCase):
    def test_legacy_default_detail_remains_byte_identical(self) -> None:
        model = load_b36_model()
        svg = technical_workbench_detail_sheet(model)
        self.assertEqual(
            hashlib.sha256(svg.encode()).hexdigest(),
            "f84960a3e5ea6f5f0aa396715dfbede34d31c63ee8c8a1558ac3ef2c3e5b4d0b",
        )

    def test_connected_detail_reports_each_current_technical_window_separately(self) -> None:
        model = deepcopy(load_b36_model())
        windows = {item["id"]: item for item in model["technical_glazing"]}
        windows["GLZ-CAR"].update(
            {"x0": 1.2, "x1": 8.9, "sill": 0.62, "height": 2.75, "modules": 5}
        )
        windows["GLZ-RC"].update(
            {"x0": 1.25, "x1": 8.45, "sill": 0.96, "height": 2.6, "modules": 4}
        )

        svg = technical_workbench_detail_sheet(model, parameterize=True)
        root = ET.fromstring(svg)
        text = "".join(root.itertext())

        self.assertIn("GLZ-CAR · 7.70 × 2.75 m · sill +0.62 m · head +3.37 m · 5 modules", text)
        self.assertIn("GLZ-RC · 7.20 × 2.60 m · sill +0.96 m · head +3.56 m · 4 modules", text)
        self.assertIn("SCHEMATIC INTERFACE · NOT TO SCALE", text)
        self.assertNotIn("+0.90 general", text)
        self.assertNotIn("TOP / SILL ALIGN VISUALLY", text)

        car = next(element for element in root.iter() if element.get("data-entity-id") == "GLZ-CAR")
        rc = next(element for element in root.iter() if element.get("data-entity-id") == "GLZ-RC")
        self.assertAlmostEqual(float(car.get("x")), 75 + (1.2 - 0.18) * 50)
        self.assertAlmostEqual(float(car.get("y")), 315 - (0.62 + 2.75) * 50)
        self.assertAlmostEqual(float(car.get("width")), 7.7 * 50)
        self.assertAlmostEqual(float(car.get("height")), 2.75 * 50)
        self.assertAlmostEqual(float(rc.get("x")), 75 + (1.25 - 0.18) * 50)
        self.assertAlmostEqual(float(rc.get("y")), 600 - (0.96 + 2.6) * 50)
        self.assertAlmostEqual(float(rc.get("width")), 7.2 * 50)
        self.assertAlmostEqual(float(rc.get("height")), 2.6 * 50)

        def opening_mullions(frame: ET.Element) -> list[float]:
            x0 = float(frame.get("x"))
            y0 = float(frame.get("y"))
            x1 = x0 + float(frame.get("width"))
            y1 = y0 + float(frame.get("height"))
            return sorted(
                float(line.get("x1"))
                for line in root.findall(".//{http://www.w3.org/2000/svg}line")
                if float(line.get("x1")) == float(line.get("x2"))
                and abs(float(line.get("y1")) - y0) < 1e-9
                and abs(float(line.get("y2")) - y1) < 1e-9
                and x0 < float(line.get("x1")) < x1
            )

        car_dividers = opening_mullions(car)
        rc_dividers = opening_mullions(rc)
        self.assertEqual(len(car_dividers), 4)
        self.assertEqual(len(rc_dividers), 3)
        for actual, expected in zip(car_dividers, (203.0, 280.0, 357.0, 434.0), strict=True):
            self.assertAlmostEqual(actual, expected)
        for actual, expected in zip(rc_dividers, (218.5, 308.5, 398.5), strict=True):
            self.assertAlmostEqual(actual, expected)

        self.assertIn(
            "HISTORICAL D-079 1.10 m overlap; not a current check.",
            text,
        )
        self.assertIn("EQUIPMENT-LIFT-SELECTION-COVERAGE", text)
        self.assertIn("PB-SERVICE-OPERATING-RESERVATIONS", text)
        self.assertNotIn("overlaps the test envelope by 1.10 m", text)
        gate_text = [
            element.text or "" for element in root.iter("{http://www.w3.org/2000/svg}text")
        ]
        self.assertTrue(any(line.startswith("1  HISTORICAL D-079") for line in gate_text))
        self.assertTrue(any(line.strip().startswith("Recalculate/review") for line in gate_text))

    def test_missing_window_datum_is_explicit_and_does_not_fall_back_to_090(self) -> None:
        model = deepcopy(load_b36_model())
        model["technical_glazing"] = [
            item for item in model["technical_glazing"] if item["id"] == "GLZ-CAR"
        ]

        text = "".join(
            ET.fromstring(technical_workbench_detail_sheet(model, parameterize=True)).itertext()
        )

        self.assertIn("GLZ-CAR ·", text)
        self.assertIn("GLZ-RC · OPEN · current source datum unavailable", text)
        self.assertIn("R WINDOW · OPEN · CURRENT SOURCE DATUM UNAVAILABLE", text)
        missing_datum_svg = ET.fromstring(
            technical_workbench_detail_sheet(model, parameterize=True)
        )
        self.assertFalse(
            any(element.get("data-entity-id") == "GLZ-RC" for element in missing_datum_svg.iter())
        )
        self.assertNotIn("+0.90 general", text)


if __name__ == "__main__":
    import unittest

    unittest.main()

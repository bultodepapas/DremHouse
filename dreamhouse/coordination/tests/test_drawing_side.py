"""Side-elevation occurrences and labels follow each window independently."""

import unittest
from copy import deepcopy
from xml.etree import ElementTree as ET

from dreamhouse import generate_pb_b05 as renderer
from dreamhouse.generate_pb_b24 import translate_visible_text
from dreamhouse.generate_pb_b37 import OUT, load_b37_model


class SideDrawingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pb = load_b37_model()

    def test_bedroom_height_sill_width_modules_update_real_geometry_and_labels(self):
        pb = deepcopy(self.pb)
        window = next(w for w in pb["bedroom_glazing"] if w["p2_id"] == "W-H2")
        window.update({"from": 22.0, "to": 26.8, "height": 2.2, "sill": 0.6, "modules": 4})
        output = renderer.side_elevation_sheet(pb, "B", parameterize=True)
        root = ET.fromstring(output)
        node = next(e for e in root.iter() if e.get("data-entity-id") == "W-H2")
        self.assertAlmostEqual(float(node.get("width")), 4.8 * 32.5)
        self.assertAlmostEqual(float(node.get("height")), 2.2 * 32.5)
        self.assertAlmostEqual(float(node.get("y")), 645 - (3.8 + 0.6 + 2.2) * 32.5)
        self.assertIn("4.80 x 2.20 m · sill 0.60", output)
        # H2 has four modules; Guest retains three. Two plus three divisions.
        self.assertEqual(sum(e.get("class") == "bedroom-module" for e in root.iter()), 5)
        self.assertNotIn("PISO A TECHO", output)

    def test_original_side_elevations_remain_byte_identical(self):
        for side in ("A", "B"):
            name = f"DH-ARQ-ELE-00{3 if side == 'A' else 4}-R10_SIDE-{side}-WINDOW-DAYLIGHT.svg"
            self.assertEqual(
                translate_visible_text(renderer.side_elevation_sheet(self.pb, side)),
                (OUT / name).read_text(),
            )

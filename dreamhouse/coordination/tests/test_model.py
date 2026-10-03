"""Current-source parity and controlled repository authoring contracts."""

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from dreamhouse.coordination.model import (
    CoordinationError,
    current_drawing_inventory,
    editable_fields,
    json_text,
    model_digest,
    read_json,
    resolve_project,
    study_template,
)


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = resolve_project()

    def write_study(self, path, changes):
        document = study_template(self.baseline, "TEST_ONLY")
        document["changes"] = changes
        path.write_text(json_text(document))
        return document

    def test_current_geometry_and_single_identity(self):
        s = self.baseline
        self.assertEqual(s["model_hash"], s["base_model_hash"])
        self.assertEqual(s["geometry"]["hall"], {"length_m": 36.0, "width_m": 18.0})
        w = s["entities"]["W-H1"]
        self.assertEqual(w["aliases"], ["GLZ-H1"])
        self.assertNotIn("GLZ-H1", s["entities"])
        self.assertAlmostEqual(w["geometry"]["z0"], 3.85)
        self.assertAlmostEqual(w["geometry"]["z1"], 6.75)
        self.assertEqual(len(current_drawing_inventory()["drawings"]), 27)

    def test_unknowns_survive_resolution(self):
        s = self.baseline["entities"]
        self.assertIsNone(s["GW-STAIR-S"]["geometry"]["z1"])
        self.assertEqual(s["GW-STAIR-S"]["kind"], "reservation")
        self.assertIsNone(s["D-H1"]["parameters"]["height_m"])
        self.assertEqual(s["PB-DOOR-ESC"]["geometry"]["shape"], "unresolved")
        self.assertEqual(s["EXT-ESC"]["geometry"]["shape"], "unresolved")
        self.assertEqual(s["GLZ-DINING-STUDY-B"]["status"], "study")

    def test_unmodelled_door_panel_counts_are_not_advertised_or_accepted(self):
        self.assertNotIn("modules", editable_fields(self.baseline["entities"]["PED"]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "study.json"
            self.write_study(path, {"PED": {"expected": {"modules": None}, "set": {"modules": 2}}})
            with self.assertRaisesRegex(CoordinationError, "unsupported authoring field"):
                resolve_project(path)

    def test_publication_provenance_is_captured_with_current_inputs(self):
        snapshot = self.baseline
        entries = snapshot["drawing_catalog"]["drawings"]
        evidence = snapshot["drawing_source_evidence"]
        self.assertEqual({e["id"] for e in entries}, set(evidence))
        for entry in entries:
            record = evidence[entry["id"]]
            self.assertEqual(record["source"], entry["source"])
            self.assertEqual(record["source_revision"], entry["source_revision"])
            self.assertEqual(
                record["source_sha256"], snapshot["build_dependencies"][record["source"]]
            )
        context = snapshot["discipline_inputs"]["structure"]
        self.assertIn("roof_space", context)
        self.assertIn("e1_space", context)

    def test_discipline_context_is_pinned_and_independent_of_archived_baseline(self):
        snapshot = deepcopy(self.baseline)
        context = snapshot["discipline_inputs"]
        pb = context["equipment"]["pb"]
        self.assertEqual(pb["workstations"][0]["window_id"], "GLZ-WS-A")
        original = snapshot["baseline"]["discipline_inputs"]["equipment"]["pb"]
        pb["workstations"][0]["worktop_height"] = 0.80
        self.assertEqual(original["workstations"][0]["worktop_height"], 0.75)
        self.assertNotEqual(
            model_digest(snapshot["geometry"], snapshot["entities"], context),
            snapshot["base_model_hash"],
        )

    def test_study_updates_geometry_without_mutating_baseline(self):
        previous = deepcopy(self.baseline)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "study.json"
            self.write_study(
                path,
                {
                    "W-H1": {
                        "expected": {"start_m": 21.8, "width_m": 3.6 - 1e-15},
                        "set": {"start_m": 22.0, "width_m": 3.0},
                    }
                },
            )
            # Expected values are exact resolved values, not rounded display labels.
            document = read_json(path)
            document["changes"]["W-H1"]["expected"]["width_m"] = self.baseline["entities"]["W-H1"][
                "parameters"
            ]["width_m"]
            path.write_text(json_text(document))
            s = resolve_project(path)
            self.assertEqual(
                (s["entities"]["W-H1"]["geometry"]["x0"], s["entities"]["W-H1"]["geometry"]["x1"]),
                (22.0, 25.0),
            )
            self.assertNotEqual(s["model_hash"], self.baseline["model_hash"])
            self.assertEqual(previous, self.baseline)

    def test_stale_baseline_expected_values_unknown_fields_and_aliases_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "study.json"
            valid = self.write_study(
                path, {"W-H1": {"expected": {"start_m": 21.8}, "set": {"start_m": 22}}}
            )
            invalid_documents = []
            d = deepcopy(valid)
            d["base_model_hash"] = "stale"
            invalid_documents.append(d)
            d = deepcopy(valid)
            d["changes"]["W-H1"]["expected"]["start_m"] = 20
            invalid_documents.append(d)
            d = deepcopy(valid)
            d["changes"]["GLZ-H1"] = d["changes"].pop("W-H1")
            invalid_documents.append(d)
            d = deepcopy(valid)
            d["changes"]["W-H1"]["set"]["start_m"] = True
            invalid_documents.append(d)
            d = deepcopy(valid)
            d["changes"]["W-H1"] = {"expected": {"swing": None}, "set": {"swing": 1}}
            invalid_documents.append(d)
            d = deepcopy(valid)
            d["schema_version"] = True
            invalid_documents.append(d)
            for d in invalid_documents:
                with self.subTest(document=d):
                    path.write_text(json_text(d))
                    with self.assertRaises(CoordinationError):
                        resolve_project(path)

    def test_duplicate_keys_and_nonfinite_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.json"
            for data in (
                '{"x": 1, "x": 2}',
                '{"nested": {"x": NaN}}',
                '{"x": 1e999}',
                '{"x": Infinity}',
            ):
                path.write_text(data)
                with self.subTest(data=data), self.assertRaises(CoordinationError):
                    read_json(path)

    def test_model_fingerprint_is_independent_of_study_path(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = [Path(directory) / name for name in ("a.json", "b.json")]
            self.write_study(a, {"W-H1": {"expected": {"start_m": 21.8}, "set": {"start_m": 22}}})
            b.write_text(a.read_text())
            sa, sb = resolve_project(a), resolve_project(b)
            self.assertEqual(sa["model_hash"], sb["model_hash"])
            self.assertNotEqual(sa["input_hash"], sb["input_hash"])


if __name__ == "__main__":
    unittest.main()

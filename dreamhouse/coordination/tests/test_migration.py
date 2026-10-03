"""Safety checks for reviewable study rebasing and exclusive output creation."""

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from dreamhouse.coordination.migration import prepare_migration, write_migration
from dreamhouse.coordination.model import (
    CoordinationError,
    digest,
    resolve_project,
    study_template,
)


class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = resolve_project()

    def old_study(self, changes):
        document = study_template(self.baseline, "OWNER_SCENARIO_12")
        document["base_model_hash"] = "0" * 64
        document["changes"] = changes
        return document

    def test_stale_fingerprint_rebases_when_all_expected_values_still_match(self):
        original = self.old_study(
            {"W-H1": {"expected": {"width_m": 3.6}, "set": {"width_m": 3.0}}}
        )
        untouched = deepcopy(original)

        plan = prepare_migration(original, self.baseline)

        self.assertEqual(original, untouched)
        self.assertEqual(plan["study"]["scenario_id"], original["scenario_id"])
        self.assertEqual(plan["study"]["changes"], original["changes"])
        self.assertEqual(plan["study"]["base_model_hash"], self.baseline["base_model_hash"])
        self.assertTrue(plan["report"]["ready_to_apply"])
        self.assertEqual(plan["report"]["source_base_model_hash"], "0" * 64)
        self.assertEqual(plan["report"]["source_document_fingerprint"], digest(original))
        self.assertEqual(
            plan["report"]["current_base_model_hash"], self.baseline["base_model_hash"]
        )
        self.assertEqual(
            plan["report"]["current_snapshot_input_hash"], self.baseline["input_hash"]
        )
        self.assertEqual(plan["report"]["context_equivalence"], "not_asserted")
        field = plan["report"]["changes"]["W-H1"]["fields"]["width_m"]
        self.assertEqual(field["expected"], 3.6)
        self.assertAlmostEqual(field["current"], 3.6)
        self.assertEqual(field["requested"], 3.0)
        self.assertTrue(field["precondition_matches"])

    def test_changed_expected_value_returns_conflict_report_without_candidate(self):
        original = self.old_study(
            {"W-H1": {"expected": {"start_m": 20.0}, "set": {"start_m": 22.0}}}
        )
        untouched = deepcopy(original)

        plan = prepare_migration(original, self.baseline)

        self.assertEqual(original, untouched)
        self.assertIsNone(plan["study"])
        self.assertFalse(plan["report"]["ready_to_apply"])
        self.assertEqual(
            plan["report"]["conflicts"],
            [
                {
                    "entity_id": "W-H1",
                    "field": "start_m",
                    "expected": 20.0,
                    "current": 21.8,
                    "requested": 22.0,
                }
            ],
        )

    def test_schema_extra_fields_and_nonfinite_values_are_rejected(self):
        valid = self.old_study(
            {"W-H1": {"expected": {"start_m": 21.8}, "set": {"start_m": 22.0}}}
        )
        invalid_documents = []

        extra = deepcopy(valid)
        extra["force"] = True
        invalid_documents.append(extra)
        wrong_version = deepcopy(valid)
        wrong_version["schema_version"] = True
        invalid_documents.append(wrong_version)
        wrong_base = deepcopy(valid)
        wrong_base["base"] = "OTHER"
        invalid_documents.append(wrong_base)
        missing_fingerprint = deepcopy(valid)
        del missing_fingerprint["base_model_hash"]
        invalid_documents.append(missing_fingerprint)
        nan_setter = deepcopy(valid)
        nan_setter["changes"]["W-H1"]["set"]["start_m"] = float("nan")
        invalid_documents.append(nan_setter)
        nan_expected = deepcopy(valid)
        nan_expected["changes"]["W-H1"]["expected"]["start_m"] = float("nan")
        invalid_documents.append(nan_expected)

        for document in invalid_documents:
            with self.subTest(document=document), self.assertRaises(CoordinationError):
                prepare_migration(document, self.baseline)

    def test_unsupported_operation_and_entity_fields_are_rejected(self):
        invalid_changes = (
            {"W-H1": {"expected": {"swing": None}, "set": {"swing": 1}}},
            {"GLZ-H1": {"expected": {"start_m": 21.8}, "set": {"start_m": 22.0}}},
            {"PB-DOOR-ESC": {"expected": {"width_m": 0.8}, "set": {"width_m": 0.9}}},
        )
        for changes in invalid_changes:
            with self.subTest(changes=changes), self.assertRaises(CoordinationError):
                prepare_migration(self.old_study(changes), self.baseline)

    def test_existing_destination_is_never_overwritten(self):
        document = self.old_study(
            {"W-H1": {"expected": {"start_m": 21.8}, "set": {"start_m": 22.0}}}
        )
        plan = prepare_migration(document, self.baseline)
        with tempfile.TemporaryDirectory() as directory:
            study_path = Path(directory) / "rebased.json"
            report_path = Path(directory) / "rebased.migration.json"
            study_path.write_text("keep existing study", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                write_migration(plan, study_path, report_path)

            self.assertEqual(study_path.read_text(encoding="utf-8"), "keep existing study")
            self.assertFalse(report_path.exists())

    def test_report_failure_cleans_up_study_created_by_same_write(self):
        document = self.old_study(
            {"W-H1": {"expected": {"start_m": 21.8}, "set": {"start_m": 22.0}}}
        )
        plan = prepare_migration(document, self.baseline)
        with tempfile.TemporaryDirectory() as directory:
            study_path = Path(directory) / "rebased.json"
            report_path = Path(directory) / "rebased.migration.json"
            report_path.write_text("keep existing report", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                write_migration(plan, study_path, report_path)

            self.assertFalse(study_path.exists())
            self.assertEqual(report_path.read_text(encoding="utf-8"), "keep existing report")

    def test_dangling_symlink_study_or_report_destination_is_rejected(self):
        document = self.old_study(
            {"W-H1": {"expected": {"start_m": 21.8}, "set": {"start_m": 22.0}}}
        )
        plan = prepare_migration(document, self.baseline)
        for symlink_leaf in ("study", "report"):
            with self.subTest(symlink_leaf=symlink_leaf), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                study_path = root / "rebased.json"
                report_path = root / "rebased.migration.json"
                link_path = study_path if symlink_leaf == "study" else report_path
                link_path.symlink_to(root / "missing-target.json")

                with self.assertRaisesRegex(CoordinationError, "must not be a symlink"):
                    write_migration(plan, study_path, report_path)

                self.assertTrue(link_path.is_symlink())
                self.assertFalse((root / "missing-target.json").exists())
                if symlink_leaf == "report":
                    self.assertFalse(study_path.exists())

    def test_conflict_writes_report_only_and_never_creates_study(self):
        document = self.old_study(
            {"W-H1": {"expected": {"start_m": 20.0}, "set": {"start_m": 22.0}}}
        )
        plan = prepare_migration(document, self.baseline)
        with tempfile.TemporaryDirectory() as directory:
            study_path = Path(directory) / "rebased.json"

            outputs = write_migration(plan, study_path)

            self.assertFalse(study_path.exists())
            report_path = Path(outputs["report"])
            self.assertEqual(report_path, study_path.with_suffix(".migration.json"))
            self.assertIn('"ready_to_apply": false', report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

"""Exercise study migration through the same CLI used by the owner."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from dreamhouse.coordination.model import json_text, resolve_project, study_template
from dreamhouse.coordination.pipeline import main


class MigrationCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.original = self.root / "old-study.json"
        self.destination = self.root / "nested/current-study.json"
        self.snapshot = resolve_project()
        self.document = study_template(self.snapshot, "MIGRATION_CLI_TEST")
        self.document["base_model_hash"] = "a" * 64
        self.document["changes"] = {
            "W-H1": {
                "expected": {"width_m": self.snapshot["entities"]["W-H1"]["parameters"]["width_m"]},
                "set": {"width_m": 3.0},
            }
        }

    def run_migration(self):
        self.original.write_text(json_text(self.document))
        with redirect_stdout(io.StringIO()):
            return main(["--project", str(self.original), "--migrate-study", str(self.destination)])

    def test_stale_study_is_rebased_to_a_new_resolvable_candidate(self):
        self.assertEqual(self.run_migration(), 0)
        self.assertEqual(json.loads(self.original.read_text()), self.document)
        result = resolve_project(self.destination)
        self.assertEqual(result["entities"]["W-H1"]["parameters"]["width_m"], 3)
        self.assertIn("CF-014", result["open_conflicts"])
        report = json.loads(self.destination.with_suffix(".migration.json").read_text())
        self.assertEqual(report["context_equivalence"], "not_asserted")
        self.assertEqual(report["source_base_model_hash"], "a" * 64)
        before = self.destination.read_bytes()
        self.assertEqual(self.run_migration(), 1)
        self.assertEqual(self.destination.read_bytes(), before)

    def test_conflict_produces_report_without_creating_a_study(self):
        self.document["changes"]["W-H1"]["expected"]["width_m"] = 8
        self.assertEqual(self.run_migration(), 2)
        self.assertFalse(self.destination.exists())
        report = json.loads(self.destination.with_suffix(".migration.json").read_text())
        self.assertAlmostEqual(report["conflicts"][0]["current"], 3.6)
        self.assertEqual(json.loads(self.original.read_text()), self.document)

    def test_cli_rejects_flags_that_would_silently_be_ignored(self):
        for argv in (["--watch", "--require-no-fail"], ["--migration-report", "unused.json"]):
            with (
                self.subTest(argv=argv),
                redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as caught,
            ):
                main(argv)
            self.assertEqual(caught.exception.code, 2)

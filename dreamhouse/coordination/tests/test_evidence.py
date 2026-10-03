"""Review evidence becomes stale on source/dependency changes, not display-label changes."""

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from dreamhouse.coordination.evidence import (
    assess_evidence,
    dependency_fingerprint,
    validate_records,
)
from dreamhouse.coordination.model import (
    ROOT,
    CoordinationError,
    file_hash,
    json_text,
    read_json,
    resolve_project,
    study_template,
)
from dreamhouse.coordination.pipeline import build_candidate, check_candidate


class EvidenceTests(unittest.TestCase):
    def test_real_source_and_geometry_changes_invalidate_retained_evidence(self):
        baseline = resolve_project()
        (ROOT / ".build").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            source = root / "fixture-review.txt"
            source.write_text("Synthetic review fixture only")
            source_path = source.relative_to(ROOT).as_posix()
            record = {
                "id": "FIXTURE-EVIDENCE",
                "entity_ids": ["W-H1"],
                "context_paths": [],
                "purpose": "coordination",
                "milestone": "schematic-review",
                "responsible_role": "fixture reviewer",
                "recorded_status": "reviewed",
                "reviewed_fingerprint": dependency_fingerprint(baseline, ["W-H1"], [])[
                    "fingerprint"
                ],
                "source": {"path": source_path, "sha256": file_hash(source)},
            }
            document = study_template(baseline, "EVIDENCE_FIXTURE")
            document["evidence_records"] = [record]
            project = root / "study.json"
            project.write_text(json_text(document))
            snapshot = resolve_project(project)
            report = assess_evidence(snapshot)
            self.assertFalse(report["records"][0]["review_required"])
            self.assertFalse(report["engineering_approval"])
            self.assertIn(source_path, snapshot["build_dependencies"])
            renamed = deepcopy(snapshot)
            renamed["entities"]["W-H1"]["label"] = "New display label"
            self.assertFalse(assess_evidence(renamed)["records"][0]["review_required"])
            relabelled_level = deepcopy(snapshot)
            relabelled_level["entities"]["W-H1"]["level"] = "PB"
            self.assertTrue(assess_evidence(relabelled_level)["records"][0]["review_required"])
            invalid = deepcopy(record)
            invalid["recorded_status"] = []
            with self.assertRaises(CoordinationError):
                validate_records([invalid])
            changed = deepcopy(snapshot)
            changed["entities"]["W-H1"]["geometry"]["x1"] += 0.1
            self.assertEqual(assess_evidence(changed)["records"][0]["dependency_state"], "changed")
            changed["entities"].pop("W-H1")
            self.assertEqual(
                assess_evidence(changed)["records"][0]["dependency_state"], "unavailable"
            )
            source.write_text("Changed fixture review")
            new = resolve_project(project)
            self.assertNotEqual(snapshot["input_hash"], new["input_hash"])
            self.assertEqual(assess_evidence(new)["records"][0]["source_state"], "changed")
            source.unlink()
            self.assertEqual(
                assess_evidence(resolve_project(project))["records"][0]["source_state"], "missing"
            )
            self.assertEqual(
                document["evidence_records"][0]["reviewed_fingerprint"],
                record["reviewed_fingerprint"],
            )

    def test_invalid_records_fail_without_inventing_approval(self):
        for value in [{}, [{}]]:
            with self.assertRaises(CoordinationError):
                validate_records(value)
        self.assertEqual(assess_evidence({"evidence_records": []})["records"], [])

    def test_package_refreshes_presentation_and_retained_source_independently(self):
        base = resolve_project()
        (ROOT / ".build").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".build") as directory:
            root = Path(directory)
            source = root / "review.txt"
            source.write_text("Fixture only")
            document = study_template(base, "RETAINED_REVIEW_AND_CUT_FIXTURE")
            document["evidence_records"] = [
                {
                    "id": "FIXTURE",
                    "entity_ids": ["GLZ-WS-A"],
                    "context_paths": [],
                    "purpose": "coordination",
                    "milestone": "source-review",
                    "responsible_role": "fixture",
                    "recorded_status": "reviewed",
                    "reviewed_fingerprint": dependency_fingerprint(base, ["GLZ-WS-A"], [])[
                        "fingerprint"
                    ],
                    "source": {
                        "path": source.relative_to(ROOT).as_posix(),
                        "sha256": file_hash(source),
                    },
                }
            ]
            project, out = root / "study.json", root / "package"
            project.write_text(json_text(document))
            first = Path(build_candidate(project, out)["path"])
            document["view_settings"] = {"plan-pb": {"cut_plane_m": 1.5}}
            project.write_text(json_text(document))
            with self.assertRaisesRegex(CoordinationError, "stale"):
                check_candidate(project, out)
            second = Path(build_candidate(project, out)["path"])
            self.assertNotEqual(first, second)
            self.assertEqual(
                read_json(first / "quantities.json"), read_json(second / "quantities.json")
            )
            self.assertEqual(
                read_json(first / "model.json")["model_hash"],
                read_json(second / "model.json")["model_hash"],
            )
            self.assertFalse(read_json(second / "evidence.json")["records"][0]["review_required"])
            impact = read_json(second / "dependencies.json")["change_impact"]
            self.assertIn("view_settings", impact["changed_review_inputs"])
            self.assertIn("view:plan-pb", impact["affected_consumer_ids"])
            self.assertNotIn("cost", impact["affected_consumer_ids"])
            issues = read_json(second / "viewpoints.json")["issues"]
            cuts = [
                o["view_definition_ref"]["definition"]["cut_plane"]
                for issue in issues
                for o in issue["viewpoints"]
                if o["view_id"] == "plan-pb"
            ]
            self.assertTrue(cuts)
            self.assertTrue(all(c["value_m"] == 1.5 for c in cuts))
            source.write_text("Revised fixture evidence")
            with self.assertRaisesRegex(CoordinationError, "stale"):
                check_candidate(project, out)
            third = Path(build_candidate(project, out)["path"])
            self.assertEqual(
                read_json(third / "evidence.json")["records"][0]["source_state"], "changed"
            )
            check_candidate(project, out)

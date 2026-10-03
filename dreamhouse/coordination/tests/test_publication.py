"""Immutable release publication, verification, selection, and recovery contracts."""

from __future__ import annotations

import hashlib
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from dreamhouse.coordination import publication
from dreamhouse.coordination.model import CoordinationError, json_text


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.candidate_root = self.root / "candidate"
        self.release_root = self.root / "published"
        self.check_project = self.root / "study.json"
        self.check_project.write_text("{}", encoding="utf-8")

    def make_candidate(
        self, scenario: str, *, status="OPEN", rendering=None, changes_requested=None
    ):
        source_input_hash = _sha256(scenario.encode())
        source_model_hash = _sha256((scenario + "-model").encode())
        issue_id = _sha256((scenario + "-issue").encode())
        issue = self.candidate_root / "issues" / issue_id
        issue.mkdir(parents=True)
        changes_requested = changes_requested or {}
        model = {
            "scenario_id": scenario,
            "project_path": str(self.check_project),
            "input_hash": source_input_hash,
            "model_hash": source_model_hash,
            "base_model_hash": source_model_hash,
            "changes_requested": changes_requested,
            "build_dependencies": {"fixture/source.json": _sha256(b"source")},
        }
        changes = {
            "baseline_scenario_id": "ARCHIVED_CURRENT_BASELINE",
            "added": [],
            "removed": [],
            "modified": [],
            "context_changes": [],
        }
        outputs = {
            "index.html": f"<!doctype html><title>{scenario}</title>\n",
            "model.json": json_text(model),
            "changes.json": json_text(changes),
            "plan-pb.svg": '<svg xmlns="http://www.w3.org/2000/svg"/>',
            "review.md": f"# {scenario}\n",
        }
        artifacts = {}
        for name, content in outputs.items():
            data = content.encode("utf-8")
            (issue / name).write_bytes(data)
            artifacts[name] = _sha256(data)
        manifest = {
            "schema_version": 2,
            "build_status": "complete",
            "purpose": "coordination review",
            "scenario_id": scenario,
            "issue_id": issue_id,
            "input_hash": source_input_hash,
            "model_hash": source_model_hash,
            "rendering": rendering,
            "hash_policy": "fixture-policy",
            "engineering_approval": False,
            "construction_authority": False,
            "published_aliases_promoted": False,
            "check_status": status,
            "artifacts": artifacts,
        }
        manifest_bytes = json_text(manifest).encode("utf-8")
        (issue / "manifest.json").write_bytes(manifest_bytes)
        return issue, manifest, manifest_bytes

    def publish_fixture(self, scenario="BASELINE", **kwargs):
        verified_candidate = self.make_candidate(scenario, **kwargs)
        with patch(
            "dreamhouse.coordination.publication._check_candidate",
            return_value=verified_candidate,
        ):
            result = publication.publish_candidate(
                self.check_project, self.candidate_root, self.release_root
            )
        return result, verified_candidate

    def test_publish_creates_self_contained_release_and_single_pointer_bootstrap(self):
        result, (_issue, candidate_manifest, _manifest_bytes) = self.publish_fixture()

        verified = publication.verify_release(result["release_id"], self.release_root)
        self.assertEqual(verified["release"], result["release"])
        self.assertEqual(
            set(verified["release"]["artifacts"]),
            set(candidate_manifest["artifacts"]),
        )
        self.assertEqual(
            verified["release"]["source_dependency_hashes"],
            {"fixture/source.json": _sha256(b"source")},
        )
        self.assertFalse(verified["release"]["engineering_approval"])
        self.assertFalse(verified["release"]["construction_authority"])
        self.assertIn("current.json", Path(result["bootstrap_path"]).read_text())
        self.assertEqual(
            publication.read_current_release(self.release_root)["release_id"],
            result["release_id"],
        )

    def test_fail_findings_and_unadopted_changes_cannot_be_released(self):
        failing = self.make_candidate("FAILURE", status="FAIL")
        with (
            patch("dreamhouse.coordination.publication._check_candidate", return_value=failing),
            self.assertRaisesRegex(CoordinationError, "FAIL findings"),
        ):
            publication.publish_candidate(
                self.check_project, self.candidate_root, self.release_root
            )

        changed = self.make_candidate("UNADOPTED", changes_requested={"W-H1": {"width_m": 3.0}})
        with (
            patch("dreamhouse.coordination.publication._check_candidate", return_value=changed),
            self.assertRaisesRegex(CoordinationError, "requested model changes"),
        ):
            publication.publish_candidate(
                self.check_project, self.candidate_root, self.release_root
            )
        self.assertFalse((self.release_root / publication.POINTER_FILE).exists())

    def test_stale_candidate_is_rejected_before_publication_mutates_the_pointer(self):
        with (
            patch(
                "dreamhouse.coordination.publication._check_candidate",
                side_effect=CoordinationError("Review is stale: source changed"),
            ),
            self.assertRaisesRegex(CoordinationError, "stale"),
        ):
            publication.publish_candidate(
                self.check_project, self.candidate_root, self.release_root
            )
        self.assertFalse((self.release_root / publication.POINTER_FILE).exists())
        self.assertFalse((self.release_root / publication.RELEASES_DIRECTORY).exists())

    def test_modified_release_artifact_is_detected(self):
        result, _ = self.publish_fixture()
        artifact = Path(result["path"]) / "plan-pb.svg"
        original = artifact.read_bytes()
        try:
            artifact.write_bytes(original + b"<!-- tampered -->")
            with self.assertRaisesRegex(CoordinationError, "Changed or missing release artifact"):
                publication.verify_release(result["release_id"], self.release_root)
        finally:
            artifact.write_bytes(original)

    def test_rollback_rejects_release_metadata_that_changes_authority_or_limitations(self):
        result, _ = self.publish_fixture("METADATA")
        pointer_path = self.release_root / publication.POINTER_FILE
        previous_pointer = pointer_path.read_bytes()
        manifest_path = Path(result["path"]) / publication.RELEASE_MANIFEST
        original = manifest_path.read_bytes()
        for key, value, message in (
            ("published_aliases_promoted", True, "promote drawing aliases"),
            ("limitations", [], "metadata differs from verified candidate provenance"),
        ):
            with self.subTest(key=key):
                altered = publication.read_json(manifest_path)
                altered[key] = value
                manifest_path.write_text(json_text(altered), encoding="utf-8")
                with self.assertRaisesRegex(CoordinationError, message):
                    publication.rollback_release(result["release_id"], self.release_root)
                self.assertEqual(pointer_path.read_bytes(), previous_pointer)
                manifest_path.write_bytes(original)

    def test_symlinked_artifact_is_rejected(self):
        result, _ = self.publish_fixture()
        release_path = Path(result["path"])
        artifact = release_path / "plan-pb.svg"
        artifact.unlink()
        artifact.symlink_to(release_path / "review.md")
        with self.assertRaisesRegex(CoordinationError, "Symlink"):
            publication.verify_release(result["release_id"], self.release_root)

    def test_failure_while_switching_pointer_keeps_previous_release_selected(self):
        first, _ = self.publish_fixture("FIRST")
        pointer_path = self.release_root / publication.POINTER_FILE
        previous_pointer = pointer_path.read_bytes()
        second_candidate = self.make_candidate("SECOND")
        with (
            patch(
                "dreamhouse.coordination.publication._check_candidate",
                return_value=second_candidate,
            ),
            patch(
                "dreamhouse.coordination.publication._write_current_pointer",
                side_effect=OSError("synthetic pointer failure"),
            ),
            self.assertRaisesRegex(OSError, "pointer failure"),
        ):
            publication.publish_candidate(
                self.check_project, self.candidate_root, self.release_root
            )
        self.assertEqual(pointer_path.read_bytes(), previous_pointer)
        self.assertEqual(
            publication.read_current_release(self.release_root)["release_id"],
            first["release_id"],
        )

    def test_rollback_recovers_complete_old_release_and_marks_freshness_unknown(self):
        first, _ = self.publish_fixture("FIRST")
        second, _ = self.publish_fixture("SECOND")
        self.assertNotEqual(first["release_id"], second["release_id"])

        restored = publication.rollback_release(first["release_id"], self.release_root)
        current = publication.read_current_release(self.release_root)
        self.assertEqual(current["release_id"], first["release_id"])
        self.assertEqual(current["pointer"]["selection_reason"], "rollback")
        self.assertEqual(current["source_freshness"], "not_revalidated")
        self.assertTrue(Path(restored["index_path"]).is_file())
        self.assertEqual(
            publication.verify_release(first["release_id"], self.release_root)["release"],
            first["release"],
        )

    def test_rollback_can_recover_a_corrupted_current_pointer(self):
        first, _ = self.publish_fixture("RECOVER")
        pointer = self.release_root / publication.POINTER_FILE
        for invalid_pointer in ("{broken pointer", "[]", "null", "17"):
            with self.subTest(invalid_pointer=invalid_pointer):
                pointer.write_text(invalid_pointer, encoding="utf-8")
                with self.assertRaises(CoordinationError):
                    publication.read_current_release(self.release_root)
                restored = publication.rollback_release(first["release_id"], self.release_root)
                self.assertEqual(restored["pointer"]["source_freshness"], "not_revalidated")
                self.assertEqual(
                    publication.read_current_release(self.release_root)["release_id"],
                    first["release_id"],
                )

    def test_read_current_can_revalidate_sources_without_rewriting_rollback_provenance(self):
        restored, _candidate = self.publish_fixture("BASELINE")
        publication.rollback_release(restored["release_id"], self.release_root)
        model = publication.read_current_release(self.release_root)["release"]
        current = {
            "input_hash": model["source_input_hash"],
            "model_hash": model["source_model_hash"],
            "base_model_hash": model["source_model_hash"],
            "changes_requested": {},
            "build_dependencies": model["source_dependency_hashes"],
        }
        with patch("dreamhouse.coordination.publication.resolve_project", return_value=current):
            result = publication.read_current_release(
                self.release_root, require_fresh=True, project_path=self.check_project
            )
        self.assertEqual(result["freshness_check"]["status"], "verified_now")
        self.assertEqual(result["source_freshness"], "not_revalidated")

    def test_stale_renderer_configuration_prevents_verified_current_read(self):
        rendering = {
            "width_px": 320,
            "fingerprint": "recorded-renderer-fingerprint",
        }
        result, _ = self.publish_fixture("VISUAL", rendering=rendering)
        release = result["release"]
        current = {
            "input_hash": release["source_input_hash"],
            "model_hash": release["source_model_hash"],
            "base_model_hash": release["source_model_hash"],
            "changes_requested": {},
            "build_dependencies": release["source_dependency_hashes"],
        }
        with (
            patch("dreamhouse.coordination.publication.resolve_project", return_value=current),
            patch(
                "dreamhouse.coordination.publication._visual_configuration",
                return_value={"width_px": 320, "fingerprint": "changed"},
            ),
            self.assertRaisesRegex(CoordinationError, "renderer/font configuration is stale"),
        ):
            publication.read_current_release(
                self.release_root, require_fresh=True, project_path=self.check_project
            )

    def test_publication_lock_serializes_writers(self):
        first_has_lock = threading.Event()
        release_first = threading.Event()
        second_started = threading.Event()
        second_has_lock = threading.Event()

        def first_writer():
            with publication._publication_lock(self.release_root):
                first_has_lock.set()
                release_first.wait(timeout=3)

        def second_writer():
            second_started.set()
            with publication._publication_lock(self.release_root):
                second_has_lock.set()

        first = threading.Thread(target=first_writer)
        second = threading.Thread(target=second_writer)
        first.start()
        self.assertTrue(first_has_lock.wait(timeout=2))
        second.start()
        try:
            self.assertTrue(second_started.wait(timeout=2))
            self.assertFalse(second_has_lock.wait(timeout=0.15))
        finally:
            release_first.set()
            first.join(timeout=3)
            second.join(timeout=3)
        self.assertTrue(second_has_lock.is_set())
        self.assertFalse(first.is_alive())
        self.assertFalse(second.is_alive())


if __name__ == "__main__":
    unittest.main()

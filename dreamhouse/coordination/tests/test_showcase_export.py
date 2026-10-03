"""A connected site exports the selected complete release and rejects changed artifacts."""

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dreamhouse.coordination.model import ROOT


class ShowcaseExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "showcase_export_test", ROOT / ".github/scripts/build_showcase.py"
        )
        cls.showcase = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.showcase)

    def setUp(self):
        (ROOT / ".build").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / ".build")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        package = self.root / "source-package"
        package.mkdir()
        (package / "index.html").write_text("review")
        bootstrap = self.root / "bootstrap.html"
        bootstrap.write_text("stable reader")
        self.release = {
            "release_id": "a" * 64,
            "path": str(package),
            "bootstrap_path": str(bootstrap),
            "pointer": {
                "release_id": "a" * 64,
                "review_index": "releases/" + "a" * 64 + "/index.html",
            },
            "release": {"artifacts": {"index.html": hashlib.sha256(b"review").hexdigest()}},
        }

    def test_export_selects_the_same_immutable_release_and_exposes_reader(self):
        with patch(
            "dreamhouse.coordination.publication.read_current_release", return_value=self.release
        ) as verify:
            self.showcase.build_site(
                {"gallery": []}, self.root / "site", coordination_out=self.root / "candidate"
            )
            self.showcase.build_site(
                {"gallery": []}, self.root / "site", coordination_out=self.root / "candidate"
            )
        self.assertEqual(verify.call_count, 4)
        site = self.root / "site"
        self.assertIn('href="coordination/index.html"', (site / "index.html").read_text())
        self.assertEqual(
            (
                site / "coordination/releases" / self.release["release_id"] / "index.html"
            ).read_text(),
            "review",
        )

    def test_direct_script_loads_the_local_verifier_outside_the_repo(self):
        result = subprocess.run(
            [
                sys.executable, "-I", str(ROOT / ".github/scripts/build_showcase.py"),
                "--site-dir", str(self.root / "site"),
                "--coordination-out", str(self.root / "missing-candidate"),
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No valid current release pointer exists", result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)
        self.assertFalse((self.root / "site").exists())

    def test_changed_export_artifact_prevents_completed_site(self):
        (Path(self.release["path"]) / "index.html").write_text("changed after verification")
        with (
            patch(
                "dreamhouse.coordination.publication.read_current_release",
                return_value=self.release,
            ),
            self.assertRaisesRegex(RuntimeError, "changed during site export"),
        ):
            self.showcase.build_site(
                {"gallery": []}, self.root / "site", coordination_out=self.root / "candidate"
            )
        self.assertFalse((self.root / "site/index.html").exists())

    def test_output_cannot_replace_inputs_or_overlap_coordination_archive(self):
        for destination, out in (
            (ROOT / "dreamhouse", None),
            (self.root / "candidate/site", self.root / "candidate"),
        ):
            with self.subTest(destination=destination), self.assertRaises(RuntimeError):
                self.showcase.build_site({"gallery": []}, destination, coordination_out=out)

    def test_site_output_protects_build_and_default_coordination_roots_without_flag(self):
        for destination in (ROOT / ".build", ROOT / ".build/coordination"):
            with (
                self.subTest(destination=destination),
                self.assertRaisesRegex(
                    RuntimeError, "must not contain or replace .build/coordination"
                ),
            ):
                self.showcase.build_site({"gallery": []}, destination)

    def test_site_output_preserves_custom_candidate_or_release_package_roots(self):
        candidate_root = self.root / "custom-candidate"
        (candidate_root / "issues").mkdir(parents=True)
        candidate_pointer = candidate_root / "latest.json"
        candidate_pointer.write_text("{}", encoding="utf-8")

        release_root = self.root / "custom-release-root"
        (release_root / "releases").mkdir(parents=True)
        release_pointer = release_root / "current.json"
        release_pointer.write_text("{}", encoding="utf-8")

        for destination, pointer in (
            (candidate_root, candidate_pointer),
            (release_root, release_pointer),
        ):
            with (
                self.subTest(destination=destination),
                self.assertRaisesRegex(RuntimeError, "coordination package"),
            ):
                self.showcase.build_site({"gallery": []}, destination)
            self.assertTrue(pointer.is_file())

    def test_site_output_cannot_remove_a_parent_containing_custom_candidate(self):
        output_parent = self.root / "container"
        candidate_root = output_parent / "nested-candidate"
        (candidate_root / "issues").mkdir(parents=True)
        pointer = candidate_root / "latest.json"
        pointer.write_text("{}", encoding="utf-8")

        with self.assertRaisesRegex(RuntimeError, "contains a coordination package"):
            self.showcase.build_site({"gallery": []}, output_parent)
        self.assertTrue(pointer.is_file())

    def test_site_output_rejects_a_symlink_to_a_coordination_root(self):
        candidate_root = self.root / "candidate-root"
        (candidate_root / "issues").mkdir(parents=True)
        pointer = candidate_root / "latest.json"
        pointer.write_text("{}", encoding="utf-8")
        alias = self.root / "candidate-alias"
        alias.symlink_to(candidate_root, target_is_directory=True)

        with self.assertRaisesRegex(RuntimeError, "cannot be a symlink"):
            self.showcase.build_site({"gallery": []}, alias)
        self.assertTrue(pointer.is_file())

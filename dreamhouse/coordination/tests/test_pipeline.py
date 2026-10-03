"""Real source-to-review propagation, stale artifact detection and publication safety."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import (
    ROOT,
    CoordinationError,
    dependency_hashes,
    json_text,
    read_json,
    resolve_project,
    study_template,
)
from dreamhouse.coordination.pipeline import build_candidate, check_candidate


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.out = self.root / "review"
        self.study = self.root / "study.json"
        self.base = resolve_project()
        self.document = study_template(self.base, "REGRESSION_STUDY_ONLY")
        self.study.write_text(json_text(self.document))

    def build(self):
        return Path(build_candidate(self.study, self.out)["path"])

    def test_build_and_check_refuse_source_directories_before_writing(self):
        for path in (ROOT, ROOT / "docs", ROOT / "dreamhouse", ROOT / "planos"):
            for operation in (build_candidate, check_candidate):
                with (
                    self.subTest(path=path, operation=operation.__name__),
                    self.assertRaisesRegex(CoordinationError, "isolated"),
                ):
                    operation(self.study, path)

    def test_current_baseline_is_complete_reproducible_and_unknowns_are_open(self):
        first = self.build()
        result = check_candidate(self.study, self.out)
        self.assertEqual(str(first), result["path"])
        self.assertEqual(self.build(), first)
        self.assertFalse(result["manifest"]["construction_authority"])
        self.assertFalse(result["manifest"]["published_aliases_promoted"])
        ledger = read_json(first / "quantities.json")
        totals = ledger["totals_by_assembly"]
        self.assertAlmostEqual(
            sum(
                totals[k]["m2"]
                for k in ("PB-TECHNICAL-GLAZING", "PB-WORKSTATION-GLAZING", "P2-WINDOWS")
            ),
            123.84,
        )
        self.assertEqual(totals["ROOFLIGHT-GLAZING"]["m2"], 23.04)
        self.assertIsNone(read_json(first / "cost.json")["approved_budget_total_cop"])
        self.assertEqual(len(list(first.glob("*.svg"))), 8)
        self.assertTrue((first / "window-sections.svg").is_file())
        self.assertTrue((first / "disciplines.json").is_file())
        self.assertTrue((first / "dependencies.json").is_file())
        self.assertGreater(
            read_json(first / "view_inventory.json")["annotation_coverage"]["anchors"], 0
        )

    def test_source_width_propagates_to_plan_elevation_detail_and_quantity(self):
        first = self.build()
        old_width = self.base["entities"]["W-H1"]["parameters"]["width_m"]
        self.document["changes"] = {
            "W-H1": {"expected": {"width_m": old_width}, "set": {"width_m": 3.0}}
        }
        self.study.write_text(json_text(self.document))
        with self.assertRaisesRegex(CoordinationError, "stale"):
            check_candidate(self.study, self.out)
        second = self.build()
        self.assertNotEqual(first, second)
        for filename in ("plan-p2.svg", "elevation-side-a.svg", "window-details.svg"):
            before, after = ET.parse(first / filename), ET.parse(second / filename)
            b = [ET.tostring(e) for e in before.iter() if e.get("data-entity-id") == "W-H1"]
            a = [ET.tostring(e) for e in after.iter() if e.get("data-entity-id") == "W-H1"]
            self.assertTrue(a, filename)
            self.assertNotEqual(a, b, filename)
        ledger = read_json(second / "quantities.json")
        self.assertAlmostEqual(ledger["totals_by_assembly"]["P2-WINDOWS"]["m2"], 52.98)
        changes = read_json(second / "changes.json")
        self.assertEqual([c["entity_id"] for c in changes["modified"]], ["W-H1"])
        self.assertTrue(
            any(
                f["rule_id"] == "OPENING-MODULE-CONSISTENCY"
                and f["status"] == "FAIL"
                and f["entity_ids"] == ["W-H1"]
                for f in read_json(second / "findings.json")
            )
        )

    def test_manual_svg_edit_is_detected(self):
        issue = self.build()
        with (issue / "plan-p2.svg").open("a") as stream:
            stream.write("<!-- manual change -->")
        with self.assertRaisesRegex(CoordinationError, "artifact"):
            check_candidate(self.study, self.out)

    def test_sill_change_reaches_section_anchors_and_workstation_warning(self):
        first = self.build()
        self.document["changes"] = {
            "GLZ-WS-A": {"expected": {"sill_m": 0.75}, "set": {"sill_m": 0.85}}
        }
        self.study.write_text(json_text(self.document))
        second = self.build()
        self.assertNotEqual(
            (first / "window-sections.svg").read_bytes(),
            (second / "window-sections.svg").read_bytes(),
        )
        changes = read_json(second / "anchor_lifecycle.json")["items"]
        self.assertTrue(
            any(
                c["view_id"] == "window-sections"
                and c["anchor_id"].startswith("GLZ-WS-A.")
                and c["state"] == "changed"
                for c in changes
            )
        )
        self.assertTrue(
            any(
                f["rule_id"] == "WORKSTATION-WINDOW-DATUM"
                and f["status"] == "FAIL"
                and f["entity_ids"] == ["GLZ-WS-A"]
                for f in read_json(second / "findings.json")
            )
        )

    def test_missing_named_view_cannot_publish_even_if_view_count_matches(self):
        from dreamhouse.coordination.render import render_views

        self.build()
        previous = (self.out / "latest.json").read_bytes()

        def omit(snapshot, result):
            files = render_views(snapshot, result)
            files["unrelated.svg"] = files.pop("window-sections.svg")
            return files

        with (
            patch("dreamhouse.coordination.pipeline.render_views", side_effect=omit),
            self.assertRaisesRegex(CoordinationError, "required review views"),
        ):
            self.build()
        self.assertEqual((self.out / "latest.json").read_bytes(), previous)

    def test_generation_failure_leaves_previous_pointer_and_artifacts(self):
        issue = self.build()
        previous = (self.out / "latest.json").read_bytes()
        with (
            patch(
                "dreamhouse.coordination.pipeline.render_views",
                side_effect=RuntimeError("synthetic renderer failure"),
            ),
            self.assertRaisesRegex(RuntimeError, "synthetic"),
        ):
            self.build()
        self.assertEqual((self.out / "latest.json").read_bytes(), previous)
        self.assertTrue((issue / "index.html").is_file())
        self.assertFalse(list(self.out.glob(".staging-*")))

    def test_changed_code_dependency_invalidates_even_unchanged_geometry(self):
        self.build()
        hashes = dependency_hashes(self.study)
        hashes["dreamhouse/coordination/render.py"] = "synthetic-new-generator-hash"
        with (
            patch("dreamhouse.coordination.model.dependency_hashes", return_value=hashes),
            self.assertRaisesRegex(CoordinationError, "stale"),
        ):
            check_candidate(self.study, self.out)

    def test_changed_inputs_during_build_do_not_replace_previous_review(self):
        self.build()
        previous = (self.out / "latest.json").read_bytes()
        with (
            patch(
                "dreamhouse.coordination.pipeline.dependency_hashes",
                return_value={"changed": "input"},
            ),
            self.assertRaisesRegex(CoordinationError, "changed during"),
        ):
            self.build()
        self.assertEqual(previous, (self.out / "latest.json").read_bytes())
        self.assertFalse(list(self.out.glob(".staging-*")))

    def test_late_pointer_failure_preserves_previous_complete_issue(self):
        first = self.build()
        previous = (self.out / "latest.json").read_bytes()
        self.document["scenario_id"] = "SECOND_REVIEW_ONLY"
        self.study.write_text(json_text(self.document))
        with (
            patch(
                "dreamhouse.coordination.pipeline._write_pointer",
                side_effect=OSError("synthetic pointer failure"),
            ),
            self.assertRaisesRegex(OSError, "pointer failure"),
        ):
            self.build()
        self.assertEqual((self.out / "latest.json").read_bytes(), previous)
        self.assertTrue((first / "manifest.json").is_file())
        self.assertFalse(list(self.out.glob(".staging-*")))


if __name__ == "__main__":
    unittest.main()

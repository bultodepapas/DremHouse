"""References must survive sheet renames and reject dangling annotations."""

import unittest
from copy import deepcopy

from dreamhouse.coordination.model import CoordinationError
from dreamhouse.coordination.view_contract import compare_anchors, inspect_views


class ViewContractTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            "scenario_id": "SYNTHETIC",
            "input_hash": "test",
            "entities": {"W": {}, "UNLOCATED": {}},
        }
        self.detail = """<svg data-view-id="detail">
          <g id="detail-W" data-entity-id="W"/>
          <circle id="a" data-entity-id="W" data-anchor-id="W.sill" data-world-z="1"/>
          <circle id="b" data-entity-id="W" data-anchor-id="W.head" data-world-z="3"/>
          <g id="dim" data-dimension-id="height" data-anchor-refs="W.sill W.head"
             data-anchor-targets="a b" data-dimension-direction="vertical" data-datum="PB"
             data-dimension-value="2"/>
        </svg>"""
        self.plan = """<svg data-view-id="plan">
          <g id="plan-W" data-entity-id="W"/>
          <g id="callout" data-callout-id="section" data-callout-refs="W.sill"
             data-callout-target-view-id="detail" data-callout-targets="a"/>
          <a data-callout-link="section" href="detail.svg#a"/>
        </svg>"""
        self.files = {"detail.svg": self.detail, "plan.svg": self.plan}

    def test_inventory_separates_occurrences_and_annotation_coverage(self):
        audit = inspect_views(self.snapshot, self.files)
        self.assertEqual(audit["represented_entity_count"], 1)
        self.assertEqual(audit["entities_without_svg_occurrences"], ["UNLOCATED"])
        self.assertEqual(len(audit["by_entity"]["W"]), 2)
        self.assertEqual(audit["annotation_coverage"]["dimensions"], 1)
        self.assertEqual(audit["annotation_coverage"]["views_without_named_dimensions"], ["plan"])

    def test_renaming_sheet_preserves_cross_view_target(self):
        files = {
            "renamed-detail.svg": self.detail,
            "plan.svg": self.plan.replace("detail.svg#a", "renamed-detail.svg#a"),
        }
        result = inspect_views(self.snapshot, files)
        self.assertEqual(result["annotation_coverage"]["callouts"], 1)

    def test_semantic_refs_do_not_hide_wrong_clickable_destinations(self):
        for destination in ("detail.svg#b", "missing.svg#a", "https://example.com/detail.svg#a"):
            with self.subTest(destination=destination):
                files = dict(
                    self.files, **{"plan.svg": self.plan.replace("detail.svg#a", destination)}
                )
                with self.assertRaisesRegex(CoordinationError, "callout navigation"):
                    inspect_views(self.snapshot, files)

    def test_nested_drawings_resolve_navigation_relative_to_their_own_file(self):
        files = {"drawings/detail.svg": self.detail, "drawings/plan.svg": self.plan}
        self.assertEqual(inspect_views(self.snapshot, files)["annotation_coverage"]["callouts"], 1)
        files["drawings/plan.svg"] = self.plan.replace("detail.svg#a", "../detail.svg#a")
        with self.assertRaisesRegex(CoordinationError, "callout navigation"):
            inspect_views(self.snapshot, files)

    def test_orphan_navigation_and_duplicate_callout_ids_are_rejected(self):
        for text in (
            self.plan.replace('data-callout-link="section"', 'data-callout-link="missing"'),
            self.plan.replace(
                "</svg>", '<g data-callout-id="section" data-callout-refs="W.sill"/></svg>'
            ),
        ):
            with self.subTest(text=text), self.assertRaises(CoordinationError):
                inspect_views(self.snapshot, dict(self.files, **{"plan.svg": text}))

    def test_deleted_anchor_rejects_existing_dimension(self):
        self.files["detail.svg"] = self.detail.replace('data-anchor-id="W.head"', "")
        with self.assertRaisesRegex(CoordinationError, "dimension anchor"):
            inspect_views(self.snapshot, self.files)

    def test_missing_cross_view_anchor_rejects_callout(self):
        self.files["plan.svg"] = self.plan.replace("W.sill", "W.missing")
        with self.assertRaisesRegex(CoordinationError, "callout anchor"):
            inspect_views(self.snapshot, self.files)

    def test_wrong_dom_target_rejects_dimension(self):
        self.files["detail.svg"] = self.detail.replace(
            'data-anchor-targets="a b"', 'data-anchor-targets="a dim"'
        )
        with self.assertRaisesRegex(CoordinationError, "dimension anchor"):
            inspect_views(self.snapshot, self.files)

    def test_wrong_callout_dom_target_is_rejected(self):
        self.files["plan.svg"] = self.plan.replace(
            'data-callout-targets="a"', 'data-callout-targets="b"'
        )
        with self.assertRaisesRegex(CoordinationError, "callout DOM target"):
            inspect_views(self.snapshot, self.files)

    def test_correct_refs_do_not_hide_a_wrong_dimension_value(self):
        self.files["detail.svg"] = self.detail.replace(
            'data-dimension-value="2"', 'data-dimension-value="3"'
        )
        with self.assertRaisesRegex(CoordinationError, "disagrees with anchors"):
            inspect_views(self.snapshot, self.files)

    def test_duplicate_semantic_anchor_and_view_rejected(self):
        for files in (
            {"detail.svg": self.detail.replace("W.head", "W.sill")},
            {"detail.svg": self.detail, "copy.svg": self.detail},
        ):
            with self.subTest(files=files), self.assertRaises(CoordinationError):
                inspect_views(self.snapshot, files)

    def test_anchor_lifecycle_tracks_changed_and_removed_without_resolving(self):
        before = inspect_views(self.snapshot, self.files)
        after = deepcopy(before)
        detail = next(v for v in after["views"] if v["view_id"] == "detail")
        detail["anchors"]["W.sill"]["coordinates"]["data-world-z"] = "1.2"
        del detail["anchors"]["W.head"]
        states = {
            item["anchor_id"]: item["state"] for item in compare_anchors(after, before)["items"]
        }
        self.assertEqual(states, {"W.sill": "changed", "W.head": "removed"})


if __name__ == "__main__":
    unittest.main()

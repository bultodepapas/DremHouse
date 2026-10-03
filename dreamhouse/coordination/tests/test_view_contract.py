"""References must survive sheet renames and reject dangling annotations."""

import json
import unittest
from copy import deepcopy
from xml.etree import ElementTree as ET

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

    def source_bound_detail(self):
        self.snapshot["entities"]["W"] = {"geometry": {"z0": 1.0, "z1": 3.0}}
        root = ET.fromstring(self.detail)
        for node, field in (
            (root.find("circle[@id='a']"), "z0"),
            (root.find("circle[@id='b']"), "z1"),
        ):
            node.set(
                "data-anchor-bindings", json.dumps({"z": ["entities", "W", "geometry", field]})
            )
        return root

    def test_equal_length_but_displaced_anchors_do_not_pass_source_binding(self):
        root = self.source_bound_detail()
        result = inspect_views(self.snapshot, {"detail.svg": ET.tostring(root, encoding="unicode")})
        self.assertEqual(result["annotation_coverage"]["source_bound_anchors"], 2)
        root.find("circle[@id='a']").set("data-world-z", "2")
        root.find("circle[@id='b']").set("data-world-z", "4")
        with self.assertRaisesRegex(CoordinationError, "disagrees with source"):
            inspect_views(self.snapshot, {"detail.svg": ET.tostring(root, encoding="unicode")})

    def test_bindings_reject_missing_cross_owner_and_partial_source_paths(self):
        for bindings in (
            {},
            {"z": ["entities", "W", "geometry", "missing"]},
            {"z": ["entities", "UNLOCATED", "geometry", "z0"]},
            [],
        ):
            with self.subTest(bindings=bindings):
                root = self.source_bound_detail()
                root.find("circle[@id='a']").set("data-anchor-bindings", json.dumps(bindings))
                with self.assertRaises(CoordinationError):
                    inspect_views(
                        self.snapshot, {"detail.svg": ET.tostring(root, encoding="unicode")}
                    )

    def test_unreferenced_nonfinite_anchor_is_rejected(self):
        files = {
            "plan.svg": '<svg data-view-id="plan"><circle id="a" data-anchor-id="W.unused" data-world-x="NaN"/></svg>'
        }
        with self.assertRaisesRegex(CoordinationError, "Nonfinite"):
            inspect_views(self.snapshot, files)

    def test_visible_dimension_text_is_verified_independently_of_metadata(self):
        root = ET.fromstring(self.detail)
        label = root.find("g[@id='dim']")
        label.tag = "text"
        label.set("data-dimension-label-format", "fixed-2-m")
        label.text = "2.00 m"
        ET.SubElement(label, "title").text = "Accessible description is not painted text"
        self.assertEqual(
            inspect_views(self.snapshot, {"detail.svg": ET.tostring(root, encoding="unicode")})[
                "annotation_coverage"
            ]["verified_dimension_labels"],
            1,
        )
        label.text = "3.00 m"
        with self.assertRaisesRegex(CoordinationError, "Visible dimension label"):
            inspect_views(self.snapshot, {"detail.svg": ET.tostring(root, encoding="unicode")})

    def test_opening_area_is_measured_from_two_independent_spans(self):
        svg = """<svg data-view-id="area">
          <circle id="a" data-anchor-id="W.left" data-world-x="1"/>
          <circle id="b" data-anchor-id="W.right" data-world-x="4"/>
          <circle id="c" data-anchor-id="W.sill" data-world-z="1"/>
          <circle id="d" data-anchor-id="W.head" data-world-z="3"/>
          <text id="area" data-dimension-id="area" data-dimension-value="6"
            data-dimension-unit="m2" data-dimension-formula="width_m * height_m"
            data-anchor-refs="W.left W.right W.sill W.head" data-anchor-targets="a b c d"
            data-dimension-label-format="fixed-2-m2">6.00 m2</text></svg>"""
        result = inspect_views(self.snapshot, {"area.svg": svg})
        measurement = result["views"][0]["dimensions"][0]["measurement_check"]
        self.assertEqual(measurement["measured_m2"], 6)
        for broken in (
            svg.replace('data-world-x="4"', 'data-world-x="5"'),
            svg.replace("data-world-z=", "data-world-x="),
        ):
            with self.subTest(broken=broken), self.assertRaises(CoordinationError):
                inspect_views(self.snapshot, {"area.svg": broken})


if __name__ == "__main__":
    unittest.main()

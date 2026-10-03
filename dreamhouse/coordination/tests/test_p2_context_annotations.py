"""P2 wall-detail context contracts remain tied to their visible schematic profiles."""

from __future__ import annotations

import unittest
from copy import deepcopy
from xml.etree import ElementTree as ET

from dreamhouse import generate_p2_b09
from dreamhouse.coordination.drawings import _synchronise_native_models
from dreamhouse.coordination.model import CoordinationError, resolve_project
from dreamhouse.coordination.p2_context_annotations import (
    annotate_p2_context_view,
    audit_p2_context_geometry,
)
from dreamhouse.coordination.view_contract import inspect_views

SVG_NS = "http://www.w3.org/2000/svg"


class P2ContextAnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = resolve_project()
        _, cls.p2, _, _ = _synchronise_native_models(cls.snapshot)

    def render_root(self, view_id: str) -> ET.Element:
        renderers = {
            "architecture-p2-acoustic-partition": generate_p2_b09.build_acoustic_partition_detail,
            "architecture-p2-hall-edge": generate_p2_b09.build_hall_edge_detail,
            "architecture-p2-exterior-wall": generate_p2_b09.build_integrated_exterior_wall_detail,
        }
        root = ET.fromstring(renderers[view_id](deepcopy(self.p2)))
        root.set("data-view-id", view_id)
        return root

    def test_acoustic_profile_binds_the_visible_illustrative_stack(self):
        root = self.render_root("architecture-p2-acoustic-partition")
        original = ET.tostring(root, encoding="unicode")
        audit = audit_p2_context_geometry(self.snapshot, root)
        self.assertEqual(ET.tostring(root, encoding="unicode"), original)
        self.assertEqual(audit["state"], "evaluated")
        self.assertEqual(audit["feature_count"], 17)
        self.assertEqual(audit["source_values"]["nominal_thickness_mm"], 200.0)
        self.assertEqual(audit["source_values"]["illustrative_layer_sum_mm"], 198.0)
        coverage = annotate_p2_context_view(self.snapshot, root)
        self.assertEqual(coverage["status"], "supported")
        self.assertEqual(coverage["context_dimensions"], 1)
        self.assertEqual(root.get("data-projected-axes"), "x")
        self.assertIsNone(root.get("data-world-to-view"))
        self.assertEqual(
            len([node for node in root.iter() if node.get("data-p2-context-feature")]),
            17,
        )

        layer = next(
            node
            for node in root.iter(f"{{{SVG_NS}}}rect")
            if node.get("data-p2-context-feature") == "acoustic_partition-layer-01"
        )
        layer.set("width", str(float(layer.get("width")) + 1))
        with self.assertRaisesRegex(CoordinationError, "projection mismatch"):
            audit_p2_context_geometry(self.snapshot, root)

    def test_open_hall_edge_frontage_has_snapshot_bound_length_anchors(self):
        root = self.render_root("architecture-p2-hall-edge")
        coverage = annotate_p2_context_view(self.snapshot, root)
        self.assertEqual(coverage["dimensions"], 1)
        self.assertEqual(coverage["anchors"], 2)
        self.assertEqual(coverage["geometry_binding"]["source_values"]["open_frontage_length_m"], 7.45)
        svg = ET.tostring(root, encoding="unicode")
        inspected = inspect_views(
            self.snapshot,
            {"drawings/architecture-p2-hall-edge.svg": svg},
        )
        view = inspected["views"][0]
        dimension = next(item for item in view["dimensions"] if item["dimension_id"] == "P2-W04R.open-frontage")
        self.assertEqual(dimension["measurement_check"]["state"], "evaluated")
        self.assertEqual(dimension["label_check"]["state"], "evaluated")
        for ref in dimension["anchor_refs"]:
            self.assertEqual(view["anchors"][ref]["source_check"]["state"], "evaluated")

        changed = deepcopy(self.snapshot)
        changed["discipline_inputs"]["programme"]["p2"]["family_balcony"]["to_y"] += 0.1
        with self.assertRaisesRegex(CoordinationError, "projection mismatch|label changed|source projection"):
            annotate_p2_context_view(changed, root)
        summary = next(
            node
            for node in root.iter(f"{{{SVG_NS}}}text")
            if "HALL EDGE ·" in "".join(node.itertext())
        )
        self.assertIn("7.55 m OPEN", "".join(summary.itertext()))

    def test_exterior_profile_reports_source_values_and_nullable_inherited_note(self):
        root = self.render_root("architecture-p2-exterior-wall")
        audit = audit_p2_context_geometry(self.snapshot, root)
        values = audit["source_values"]
        self.assertEqual(values["nominal_thickness_mm"], 230.0)
        self.assertEqual(values["illustrative_layer_sum_mm"], 229.0)
        self.assertEqual(values["inherited_layer_note_mm"], 297.0)
        self.assertIn("297 mm", values["inherited_layer_note"])
        self.assertEqual(values["open_conflict"], "CF-014")
        coverage = annotate_p2_context_view(self.snapshot, root)
        self.assertEqual(coverage["context_dimensions"], 1)
        dimension = next(node for node in root.iter() if node.get("data-p2-context-dimension-id"))
        self.assertEqual(dimension.get("data-p2-context-dimension-unit"), "mm")
        self.assertEqual(dimension.get("data-p2-context-dimension-value"), "229")
        self.assertEqual(dimension.get("data-p2-context-nominal-mm"), "230")
        self.assertEqual(dimension.get("data-p2-context-stale-note-mm"), "297")
        self.assertIn("297 mm", dimension.get("data-p2-context-inherited-note"))

        changed = deepcopy(self.snapshot)
        changed["discipline_inputs"]["programme"]["p2"]["exterior_wall_assembly"][
            "outside_to_inside_layers"
        ][0]["nominal_mm"] += 1
        with self.assertRaisesRegex(CoordinationError, "projection mismatch"):
            audit_p2_context_geometry(changed, root)

    def test_changed_source_refreshes_visible_wall_values_and_preserves_conflict(self):
        changed = deepcopy(self.snapshot)
        changed["discipline_inputs"]["programme"]["p2"]["exterior_wall_assembly"][
            "nominal_total_m"
        ] = 0.231
        changed["discipline_inputs"]["programme"]["p2"]["exterior_wall_assembly"][
            "layer_sum_note"
        ] = "Inherited note withdrawn pending a coordinated replacement."
        root = self.render_root("architecture-p2-exterior-wall")
        coverage = annotate_p2_context_view(changed, root)
        values = coverage["geometry_binding"]["source_values"]
        self.assertEqual(values["nominal_thickness_mm"], 231.0)
        self.assertEqual(values["wall_schedule_nominal_mm"], 230.0)
        self.assertFalse(values["nominal_values_match"])
        self.assertIsNone(values["inherited_layer_note_mm"])
        self.assertEqual(
            values["inherited_layer_note"],
            "Inherited note withdrawn pending a coordinated replacement.",
        )
        summary = next(
            node
            for node in root.iter(f"{{{SVG_NS}}}text")
            if node.get("data-p2-context-dimension-id")
        )
        self.assertEqual(
            "".join(summary.itertext()).strip(),
            "231 mm NOMINAL · 229 mm ILLUSTRATIVE SUM",
        )
        self.assertEqual(summary.get("data-p2-context-nominal-mm"), "231")
        self.assertIsNone(summary.get("data-p2-context-stale-note-mm"))
        self.assertEqual(
            summary.get("data-p2-context-inherited-note"),
            "Inherited note withdrawn pending a coordinated replacement.",
        )

        acoustic = deepcopy(self.snapshot)
        acoustic["discipline_inputs"]["programme"]["p2"]["wall_schedule"]["P2-W02"][
            "nominal_total_m"
        ] = 0.151
        acoustic_root = self.render_root("architecture-p2-acoustic-partition")
        acoustic_coverage = annotate_p2_context_view(acoustic, acoustic_root)
        row = next(
            node
            for node in acoustic_root.iter(f"{{{SVG_NS}}}text")
            if node.get("data-p2-context-feature") == "wall-schedule-P2-W02-nominal"
        )
        self.assertEqual("".join(row.itertext()).strip(), "151 mm")
        self.assertEqual(
            acoustic_coverage["geometry_binding"]["feature_count"],
            17,
        )


if __name__ == "__main__":
    unittest.main()

"""Known section datums can be audited without declaring a roof solid."""

import unittest
from copy import deepcopy
from xml.etree import ElementTree as ET

from dreamhouse.coordination.context_annotations import annotate_context_view
from dreamhouse.coordination.drawings import _roof_longitudinal, _roof_transverse
from dreamhouse.coordination.model import CoordinationError, resolve_project
from dreamhouse.coordination.view_contract import inspect_views


class ContextAnnotationTests(unittest.TestCase):
    def render(self, snapshot, name):
        root = ET.fromstring(
            (_roof_longitudinal if "longitudinal" in name else _roof_transverse)(
                snapshot["discipline_inputs"]["equipment"]["pb"],
                snapshot["discipline_inputs"]["programme"]["p2"],
                snapshot["discipline_inputs"]["structure"]["stair"],
            )
        )
        root.set("data-view-id", name)
        return root

    def test_source_eaves_and_floor_datums_have_checked_graphics_and_annotations(self):
        baseline = resolve_project()
        for name in [
            "architecture-roof-longitudinal-section",
            "architecture-roof-transverse-section",
        ]:
            changed = deepcopy(baseline)
            changed["discipline_inputs"]["equipment"]["pb"]["roof"]["high_eave"] = 8.0
            for snapshot in [baseline, changed]:
                root = self.render(snapshot, name)
                coverage = annotate_context_view(snapshot, root)
                self.assertEqual(coverage["dimensions"], 4)
                inventory = inspect_views(
                    snapshot, {name + ".svg": ET.tostring(root, encoding="unicode")}
                )
                self.assertEqual(inventory["annotation_coverage"]["source_bound_anchors"], 8)
                self.assertEqual(inventory["annotation_coverage"]["evaluated_dimensions"], 4)
                self.assertEqual(inventory["views"][0]["geometry_check"]["state"], "evaluated")
            line = next(n for n in root.iter() if n.get("data-context-feature") == "roof-ordinate")
            line.set("y2", str(float(line.get("y2")) + 1))
            with self.assertRaisesRegex(CoordinationError, "projection mismatch"):
                inspect_views(changed, {name + ".svg": ET.tostring(root, encoding="unicode")})

    def test_missing_feature_and_transformed_context_are_rejected(self):
        snapshot = resolve_project()
        name = "architecture-roof-transverse-section"
        root = self.render(snapshot, name)
        line = next(n for n in root.iter() if n.get("data-context-feature") == "p2-datum")
        line.attrib.pop("data-context-feature")
        with self.assertRaisesRegex(CoordinationError, "Missing section"):
            annotate_context_view(snapshot, root)
        root = self.render(snapshot, name)
        root.set("transform", "translate(1 0)")
        with self.assertRaisesRegex(CoordinationError, "Transformed"):
            annotate_context_view(snapshot, root)

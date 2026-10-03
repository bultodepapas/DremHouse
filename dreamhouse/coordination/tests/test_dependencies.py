"""A move must affect review evidence even when nominal area is unchanged."""

import unittest
from copy import deepcopy

from dreamhouse.coordination.dependencies import dependency_report, validate_consumers
from dreamhouse.coordination.model import CoordinationError, resolve_project
from dreamhouse.coordination.rules import evaluate


class DependencyTests(unittest.TestCase):
    def test_extension_dependency_orders_after_its_inputs_and_rejects_bad_graphs(self):
        consumers = [
            {"id": "measurement", "depends_on": []},
            {"id": "fixture-view", "depends_on": ["measurement"]},
        ]
        self.assertEqual(validate_consumers(consumers), ["measurement", "fixture-view"])
        for broken in (
            consumers + [{"id": "measurement", "depends_on": []}],
            [{"id": "fixture-view", "depends_on": ["missing"]}],
            [{"id": "measurement", "depends_on": ["fixture-view"]}, consumers[1]],
        ):
            with self.subTest(graph=broken), self.assertRaises(CoordinationError):
                validate_consumers(broken)

    def test_move_only_recomputes_and_invalidates_linked_review_evidence(self):
        baseline = resolve_project()
        moved = deepcopy(baseline)
        entity = moved["entities"]["W-H1"]
        for key in ("x0", "x1"):
            entity["geometry"][key] += 0.1
        entity["parameters"]["start_m"] += 0.1
        # Explicit fixtures avoid coupling impact accounting to SVG serialization.
        inventory = {
            "views": [
                {"view_id": "side-a", "file": "side-a.svg", "occurrences": [{"entity_id": "W-H1"}]}
            ]
        }
        result = evaluate(moved, baseline)
        before = evaluate(baseline)
        self.assertEqual(
            result["quantity_ledger"]["totals_by_assembly"],
            before["quantity_ledger"]["totals_by_assembly"],
        )
        report = dependency_report(moved, result, inventory)
        impact = report["change_impact"]
        self.assertEqual(impact["changed_entity_ids"], ["W-H1"])
        self.assertIn("view:side-a", impact["affected_consumer_ids"])
        self.assertIn("cost", impact["recomputed_consumer_ids"])
        self.assertTrue(
            all(
                e["review_required_for_changed_scenario"] and not e["approved_evidence_attached"]
                for e in report["professional_evidence"]
            )
        )

    def test_unchanged_baseline_retains_outstanding_gates_without_invented_approval(self):
        baseline = resolve_project()
        report = dependency_report(baseline, evaluate(baseline, baseline), {"views": []})
        self.assertEqual(report["change_impact"]["changed_entity_ids"], [])
        self.assertTrue(
            all(
                e["status"] == "outstanding" and not e["approved_evidence_attached"]
                for e in report["professional_evidence"]
            )
        )

    def test_context_only_change_identifies_affected_consumers_and_review_obligation(self):
        baseline = resolve_project()
        changed = deepcopy(baseline)
        changed["discipline_inputs"]["equipment"]["pb"]["workstations"][0]["worktop_height"] = 0.8
        result = evaluate(changed, baseline)
        report = dependency_report(changed, result, {"views": []})
        self.assertEqual(report["change_impact"]["changed_entity_ids"], [])
        self.assertEqual(
            report["change_impact"]["changed_context_paths"], ["discipline_inputs.equipment"]
        )
        self.assertIn("evaluation", report["change_impact"]["affected_consumer_ids"])
        self.assertTrue(
            all(e["review_required_for_changed_scenario"] for e in report["professional_evidence"])
        )


if __name__ == "__main__":
    unittest.main()

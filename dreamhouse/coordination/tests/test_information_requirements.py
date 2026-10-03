"""Purpose-specific information coverage stays source-bound and status-separated."""

import unittest
from copy import deepcopy

from dreamhouse.coordination.information_requirements import information_requirements
from dreamhouse.coordination.model import resolve_project
from dreamhouse.coordination.rules import evaluate


class InformationRequirementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshot = resolve_project()
        cls.evaluation = evaluate(cls.snapshot)
        cls.report = information_requirements(cls.snapshot, cls.evaluation)

    def record(self, entity_id, purpose):
        return next(
            row
            for row in self.report["records"]
            if row["entity_id"] == entity_id and row["purpose"] == purpose
        )

    @staticmethod
    def requirements(record):
        return {item["id"]: item for item in record["requirements"]}

    def test_coordination_and_procurement_have_distinct_milestone_requirements(self):
        coordination = self.record("W-H1", "coordination")
        procurement = self.record("W-H1", "procurement")

        self.assertEqual(coordination["milestone"], "schematic coordination")
        self.assertEqual(coordination["status"], "complete")
        self.assertEqual(
            self.requirements(coordination)["source-reference"]["source_refs"],
            ["dreamhouse/window_daylight_d083.json#upper_floor_bedroom_windows[id=W-H1]"],
        )
        self.assertEqual(procurement["milestone"], "product selection and procurement")
        self.assertEqual(procurement["status"], "incomplete")
        requirements = self.requirements(procurement)
        self.assertEqual(requirements["selected-product"]["status"], "missing")
        self.assertIsNone(requirements["selected-product"]["observed"])
        self.assertEqual(requirements["procurement-professional-review"]["status"], "missing")
        quantity = requirements["procurement-quantity-basis"]
        self.assertEqual(quantity["status"], "incomplete")
        self.assertIn("not procurement quantity", quantity["observed"]["measurement_status"])
        self.assertIn("selected-product", procurement["missing_information"])

    def test_installation_and_maintenance_show_absent_evidence_explicitly(self):
        installation = self.record("W-H1", "installation")
        self.assertEqual(installation["milestone"], "installation and commissioning")
        self.assertEqual(installation["status"], "incomplete")
        install_requirements = self.requirements(installation)
        self.assertEqual(
            install_requirements["installation-product-reference"]["status"], "missing"
        )
        self.assertEqual(
            install_requirements["installation-inspection-record"]["status"], "missing"
        )

        maintenance = self.record("RL-CAR", "maintenance")
        maintenance_requirements = self.requirements(maintenance)
        self.assertEqual(maintenance["milestone"], "handover and operations")
        self.assertEqual(maintenance["status"], "incomplete")
        self.assertEqual(
            maintenance_requirements["maintainable-asset-registration"]["status"], "met"
        )
        self.assertEqual(maintenance_requirements["lifecycle-records"]["status"], "missing")
        access = maintenance_requirements["maintenance-plan-and-access"]
        self.assertEqual(access["status"], "missing")
        self.assertIn("evaluation.extensions.maintenance.assets[id=RL-CAR]", access["source_refs"])
        self.assertTrue(access["observed"]["source_open_items"])

    def test_unmapped_source_asset_remains_visible_without_invented_entity_geometry(self):
        bench = next(
            row
            for row in self.report["records"]
            if row["purpose"] == "maintenance" and row["source_asset_id"] == "PB-BENCH-CAR"
        )
        self.assertIsNone(bench["entity_id"])
        self.assertEqual(bench["applicability"], "applicable")
        self.assertEqual(bench["status"], "incomplete")
        self.assertEqual(bench["kind"], "source asset reservation")

    def test_evidence_fingerprint_ignores_display_label_but_tracks_source_geometry(self):
        base = self.record("W-H1", "coordination")["evidence_fingerprint"]
        relabeled = deepcopy(self.snapshot)
        relabeled["entities"]["W-H1"]["label"] = "Owner display wording changed"
        relabeled_report = information_requirements(relabeled, self.evaluation)
        relabeled_record = next(
            row
            for row in relabeled_report["records"]
            if row["entity_id"] == "W-H1" and row["purpose"] == "coordination"
        )
        self.assertEqual(relabeled_record["evidence_fingerprint"], base)

        moved = deepcopy(self.snapshot)
        moved["entities"]["W-H1"]["geometry"]["x0"] += 0.1
        moved_report = information_requirements(moved, self.evaluation)
        moved_record = next(
            row
            for row in moved_report["records"]
            if row["entity_id"] == "W-H1" and row["purpose"] == "coordination"
        )
        self.assertNotEqual(moved_record["evidence_fingerprint"], base)

    def test_summary_keeps_purpose_counts_separate_without_a_housewide_percent(self):
        self.assertEqual(
            set(self.report["summary_by_purpose"]),
            {"coordination", "procurement", "installation", "maintenance"},
        )
        self.assertGreater(self.report["summary_by_purpose"]["coordination"]["complete"], 0)
        self.assertGreater(self.report["summary_by_purpose"]["procurement"]["incomplete"], 0)
        self.assertNotIn("completion_percent", self.report)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from dreamhouse.cost import reconcile_costs
from dreamhouse.generate_p2_b28 import load_b28_model
from dreamhouse.generate_pb_b37 import load_b37_model
from dreamhouse.model import load_project
from dreamhouse.quantities import build_quantity_ledger

DREAMHOUSE_DIR = Path(__file__).resolve().parents[2]


class TestQuantityLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.current_pb = load_b37_model()
        cls.current_p2 = load_b28_model()
        cls.current_rooflights = json.loads(
            (DREAMHOUSE_DIR / "rooflight_b12.json").read_text(encoding="utf-8")
        )

    def test_current_workstation_glazing_has_its_own_assembly(self) -> None:
        ledger = build_quantity_ledger(self.current_pb, self.current_p2, self.current_rooflights)

        workstation_records = {
            item["id"]: item
            for item in ledger["records"]
            if item["id"] in {"Q-GLZ-WS-A-AREA", "Q-GLZ-WS-B-AREA"}
        }
        self.assertEqual(set(workstation_records), {"Q-GLZ-WS-A-AREA", "Q-GLZ-WS-B-AREA"})
        self.assertEqual(
            {identifier: record["quantity"] for identifier, record in workstation_records.items()},
            {"Q-GLZ-WS-A-AREA": 21.96, "Q-GLZ-WS-B-AREA": 5.4},
        )
        self.assertTrue(
            all(
                record["assembly_id"] == "PB-WORKSTATION-GLAZING"
                and record["source_model"] == "PB.workstation_glazing"
                for record in workstation_records.values()
            )
        )
        self.assertEqual(ledger["totals_by_assembly"]["PB-WORKSTATION-GLAZING"]["m2"], 27.36)

    def test_rooflights_keep_glazing_and_curb_classifications(self) -> None:
        ledger = build_quantity_ledger(self.current_pb, self.current_p2, self.current_rooflights)
        records = {item["id"]: item for item in ledger["records"]}

        for rooflight_id in ("RL-CAR", "RL-RC"):
            with self.subTest(rooflight_id=rooflight_id):
                area = records[f"Q-{rooflight_id}-AREA"]
                curb = records[f"Q-{rooflight_id}-CURB"]
                self.assertEqual(area["assembly_id"], "ROOFLIGHT-GLAZING")
                self.assertEqual(area["quantity"], 11.52)
                self.assertEqual(curb["assembly_id"], "ROOFLIGHT-CURB")
                self.assertEqual(curb["quantity"], 14.4)

        self.assertEqual(ledger["totals_by_assembly"]["ROOFLIGHT-GLAZING"]["m2"], 23.04)
        self.assertEqual(ledger["totals_by_assembly"]["ROOFLIGHT-CURB"]["m"], 28.8)

    def test_optional_dining_study_is_excluded_and_cost_total_stays_unapproved(self) -> None:
        ledger = build_quantity_ledger(self.current_pb, self.current_p2, self.current_rooflights)
        record_ids = {item["id"] for item in ledger["records"]}

        self.assertEqual(
            self.current_pb["optional_opening_studies"][0]["id"],
            "GLZ-DINING-STUDY-B",
        )
        self.assertNotIn("Q-GLZ-DINING-STUDY-B-AREA", record_ids)
        active_vertical_area = sum(
            ledger["totals_by_assembly"][assembly]["m2"]
            for assembly in (
                "PB-TECHNICAL-GLAZING",
                "PB-WORKSTATION-GLAZING",
                "P2-WINDOWS",
            )
        )
        self.assertEqual(active_vertical_area, 123.84)
        self.assertIsNone(reconcile_costs(ledger)["approved_budget_total_cop"])

    def test_historical_d059_assembly_totals_are_unchanged(self) -> None:
        project = load_project("D059_P2_REFINED_ENVELOPE")
        ledger = build_quantity_ledger(
            project.models["pb"],
            project.models["p2"],
            project.models["rooflights"],
        )
        totals = ledger["totals_by_assembly"]

        self.assertEqual(totals["PB-TECHNICAL-GLAZING"]["m2"], 41.76)
        self.assertEqual(totals["P2-WINDOWS"]["m2"], 55.02)
        self.assertEqual(totals["ROOFLIGHT-GLAZING"]["m2"], 23.04)
        self.assertEqual(totals["ROOFLIGHT-CURB"]["m"], 28.8)
        self.assertNotIn("PB-WORKSTATION-GLAZING", totals)
        self.assertIsNone(reconcile_costs(ledger)["approved_budget_total_cop"])

    def test_unknown_source_or_kind_fails_with_item_diagnostic(self) -> None:
        unsupported_items = (
            {
                "id": "GLZ-NEW-FAMILY",
                "source": "PB.unclassified_glazing",
                "kind": "vertical_glazing",
            },
            {
                "id": "GLZ-NEW-KIND",
                "source": "PB.technical_glazing",
                "kind": "operable_panel",
            },
        )

        for item in unsupported_items:
            with (
                self.subTest(item=item),
                patch(
                    "dreamhouse.quantities.ledger.build_opening_schedule",
                    return_value={"items": [item]},
                ),
            ):
                with self.assertRaises(ValueError) as raised:
                    build_quantity_ledger({}, {}, {})

                message = str(raised.exception)
                self.assertIn(item["id"], message)
                self.assertIn(item["source"], message)
                self.assertIn(item["kind"], message)


if __name__ == "__main__":
    unittest.main()

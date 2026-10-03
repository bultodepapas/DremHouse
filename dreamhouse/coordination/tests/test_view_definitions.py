"""Changing a drawing cut changes membership without changing physical evidence."""

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from dreamhouse.coordination.migration import prepare_migration
from dreamhouse.coordination.model import (
    CoordinationError,
    json_text,
    resolve_project,
    study_template,
)
from dreamhouse.coordination.render import render_views
from dreamhouse.coordination.rules import evaluate
from dreamhouse.coordination.view_contract import inspect_views
from dreamhouse.coordination.view_definitions import classify_membership, validate_view_settings


class ViewDefinitionTests(unittest.TestCase):
    def test_cut_plane_and_depth_change_membership_but_not_geometry_or_quantities(self):
        base = resolve_project()
        document = study_template(base, "CUT_INTENT_ONLY")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "study.json"
            records = []
            for cut, depth in [(0.5, [0, 4]), (1.5, [0, 4]), (4.5, [4, 5])]:
                document["view_settings"] = {
                    "plan-pb": {"cut_plane_m": cut, "depth_range_m": depth}
                }
                path.write_text(json_text(document))
                snapshot = resolve_project(path)
                evaluated = evaluate(snapshot)
                inventory = inspect_views(snapshot, render_views(snapshot, evaluated))
                plan = next(v for v in inventory["views"] if v["view_id"] == "plan-pb")
                opening = next(o for o in plan["occurrences"] if o["entity_id"] == "GLZ-WS-A")
                self.assertEqual(snapshot["model_hash"], base["model_hash"])
                self.assertEqual(snapshot["entities"], base["entities"])
                self.assertEqual(plan["definition"]["cut_plane"]["value_m"], cut)
                self.assertIsNotNone(plan["definition"]["world_to_view"])
                records.append((snapshot, evaluated, opening))
            self.assertEqual(
                [r[2]["section_membership"] for r in records],
                ["projected-above", "cut-envelope", "outside-depth"],
            )
            self.assertEqual(records[0][1]["quantity_ledger"], records[1][1]["quantity_ledger"])
            self.assertNotEqual(records[0][0]["input_hash"], records[1][0]["input_hash"])
            migrated = prepare_migration(document, base)["study"]
            self.assertEqual(migrated["view_settings"], document["view_settings"])

    def test_unknown_height_and_boundary_contact_are_explicit(self):
        self.assertEqual(
            classify_membership({"z0": None, "z1": 3}, {"cut_plane_m": 1}), "unknown-height"
        )
        self.assertEqual(
            classify_membership({"z0": 1, "z1": 1}, {"cut_plane_m": 1}), "on-plane-envelope"
        )
        self.assertEqual(
            classify_membership({"z0": 0, "z1": 1}, {"cut_plane_m": 2}), "projected-below"
        )

    def test_invalid_settings_are_rejected_before_consumption(self):
        for value in [
            None,
            {"unknown": {}},
            {"plan-pb": {"cut_plane_m": True}},
            {"plan-p2": {"cut_plane_m": float("nan")}},
            {"plan-pb": {"depth_range_m": [0, 2]}},
            {"plan-pb": {"cut_plane_m": 1, "depth_range_m": [2, 0]}},
            {"plan-pb": {"cut_plane_m": 1, "depth_range_m": [2, 3]}},
        ]:
            with self.subTest(value=value), self.assertRaises(CoordinationError):
                validate_view_settings(value)
        value = {"plan-pb": {"cut_plane_m": 1, "depth_range_m": [0, 2]}}
        result = validate_view_settings(value)
        before = deepcopy(value)
        result["plan-pb"]["depth_range_m"][0] = -1
        self.assertEqual(value, before)

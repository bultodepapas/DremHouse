"""A source adapter can enroll a family through the real complete-package path."""

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from dreamhouse.coordination import model
from dreamhouse.coordination.model import DEFAULT_PROJECT, CoordinationError, read_json
from dreamhouse.coordination.pipeline import build_candidate


class FamilyExtensionTests(unittest.TestCase):
    def test_fixture_family_reaches_rules_views_and_capabilities_without_another_master(self):
        original = model._baseline

        def extended_source():
            geometry, entities, context = original()
            fixture = deepcopy(entities["GW-STAIR-S"])
            fixture.update(
                id="FIXTURE-SUPPORT", label="Fixture source reservation", family="fixture.support"
            )
            fixture["source"] = {"path": "injected regression source adapter", "key": "support"}
            fixture["geometry"].update(x0=22, x1=22.2, y0=0, y1=0.2)
            entities[fixture["id"]] = fixture
            return geometry, entities, context

        with (
            tempfile.TemporaryDirectory() as directory,
            patch("dreamhouse.coordination.model._baseline", side_effect=extended_source),
        ):
            issue = Path(build_candidate(DEFAULT_PROJECT, Path(directory) / "review")["path"])
            snapshot = read_json(issue / "model.json")
            capabilities = read_json(issue / "capabilities.json")
            inventory = read_json(issue / "view_inventory.json")
            findings = read_json(issue / "findings.json")
            family = next(f for f in capabilities["families"] if f["family"] == "fixture.support")
            self.assertEqual(family["entities"][0]["id"], "FIXTURE-SUPPORT")
            self.assertTrue(inventory["by_entity"]["FIXTURE-SUPPORT"])
            self.assertTrue(any("FIXTURE-SUPPORT" in f["entity_ids"] for f in findings))
            self.assertEqual(snapshot["entities"]["FIXTURE-SUPPORT"]["source"]["key"], "support")
            # The added plan reservation cannot become a priced wall or invented 3D member.
            self.assertIsNone(snapshot["entities"]["FIXTURE-SUPPORT"]["geometry"]["z1"])
            self.assertEqual(family["entities"][0]["editable_fields"], [])

    def test_wrong_relationship_kind_host_cycle_and_deleted_reference_fail_resolution(self):
        original = model._baseline
        mutations = [
            lambda e: e["W-H1"]["relationships"].update(host_id="H1-D"),
            lambda e: e["W-H1"]["relationships"].update(space_ids=["HOST-P2-A"]),
            lambda e: e["HOST-P2-A"]["relationships"].update(host_id="HOST-P2-A"),
            lambda e: e["W-H1"].update(kind="invented"),
            lambda e: e.pop("HOST-P2-A"),
        ]
        for mutate in mutations:

            def changed(mutate=mutate):
                geometry, entities, context = original()
                mutate(entities)
                return geometry, entities, context

            with (
                self.subTest(mutation=mutate),
                patch("dreamhouse.coordination.model._baseline", side_effect=changed),
                self.assertRaises(CoordinationError),
            ):
                model.resolve_project()

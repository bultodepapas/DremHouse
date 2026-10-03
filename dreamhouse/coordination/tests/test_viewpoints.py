"""Saved issue records keep findings anchored to their original view evidence."""

from __future__ import annotations

import unittest

from dreamhouse.coordination.viewpoints import build_viewpoints


def _fixture():
    snapshot = {
        "scenario_id": "SCENARIO-A",
        "input_hash": "input-a",
        "model_hash": "model-a",
        "entities": {
            "WALL-01": {"id": "WALL-01", "label": "North wall", "geometry": {"x0": 1}},
            "DOOR-01": {"id": "DOOR-01", "label": "Rear door"},
        },
    }
    finding = {
        "finding_id": "CLEARANCE:DOOR-01:WALL-01",
        "rule_id": "CLEARANCE",
        "status": "OPEN",
        "coverage": "evaluated",
        "severity": "warning",
        "message": "Review the rear door clearance.",
        "entity_ids": ["WALL-01", "DOOR-01"],
        "scenario_id": "SCENARIO-A",
        "input_hash": "input-a",
        "model_hash": "model-a",
        "evidence": {"measured": False},
    }
    evaluation = {"findings": [finding]}
    definition = {
        "purpose": "plan",
        "basis": "PB",
        "view_box": [0, 0, 20, 20],
        "projected_axes": ["X", "Y"],
        "cut_plane": {"state": "known", "z_m": 1.2},
        "depth_range": {"state": "known", "near_m": 0, "far_m": 2},
        "transform": {"scale": 100},
        "unknowns": [],
    }
    inventory = {
        "schema_version": 4,
        "scenario_id": "SCENARIO-A",
        "input_hash": "input-a",
        "views": [
            {
                "view_id": "plan-pb",
                "file": "plan-pb.svg",
                "definition": definition,
                "occurrences": [
                    {"entity_id": "WALL-01", "occurrence_id": "wall-occ-1"},
                    {"entity_id": "DOOR-01", "occurrence_id": "door-occ-1"},
                ],
            },
            {
                "view_id": "elevation-rear",
                "file": "elevation-rear.svg",
                "definition": {**definition, "purpose": "elevation", "basis": "REAR"},
                "occurrences": [
                    {"entity_id": "DOOR-01", "occurrence_id": "door-occ-rear"}
                ],
            },
        ],
        "by_entity": {
            "WALL-01": [
                {
                    "view": "plan-pb.svg",
                    "view_id": "plan-pb",
                    "occurrence_id": "wall-occ-1",
                }
            ],
            "DOOR-01": [
                {
                    "view": "plan-pb.svg",
                    "view_id": "plan-pb",
                    "occurrence_id": "door-occ-1",
                },
                {
                    "view": "elevation-rear.svg",
                    "view_id": "elevation-rear",
                    "occurrence_id": "door-occ-rear",
                },
            ],
        },
    }
    return snapshot, evaluation, inventory


class ViewpointTests(unittest.TestCase):
    def test_records_round_trip_stable_finding_views_occurrences_and_definition(self):
        snapshot, evaluation, inventory = _fixture()
        first = build_viewpoints(snapshot, evaluation, inventory)
        second = build_viewpoints(snapshot, evaluation, inventory)

        self.assertEqual(first, second)
        self.assertEqual(first["snapshot_ref"], {
            "scenario_id": "SCENARIO-A",
            "input_hash": "input-a",
            "model_hash": "model-a",
        })
        issue = first["issues"][0]
        self.assertEqual(issue["finding_id"], "CLEARANCE:DOOR-01:WALL-01")
        self.assertEqual(issue["finding_ref"]["state"], "available")
        self.assertEqual(
            [(item["view_id"], item["view_file"]) for item in issue["viewpoints"]],
            [("elevation-rear", "elevation-rear.svg"), ("plan-pb", "plan-pb.svg")],
        )
        rear = issue["viewpoints"][0]
        self.assertEqual(
            rear["selected_occurrences"],
            [{"entity_id": "DOOR-01", "occurrence_id": "door-occ-rear"}],
        )
        self.assertEqual(
            rear["view_definition_ref"]["definition"]["purpose"], "elevation"
        )
        self.assertNotIn("geometry", rear["view_definition_ref"]["definition"])
        self.assertEqual(issue["unavailable_references"], [])

    def test_missing_entities_views_and_occurrences_are_explicit_and_unlinked(self):
        snapshot, evaluation, inventory = _fixture()
        finding = evaluation["findings"][0]
        finding["entity_ids"] = ["MISSING-ENTITY", "WALL-01"]
        inventory["by_entity"]["WALL-01"][0]["occurrence_id"] = "deleted-occurrence"
        inventory["by_entity"]["MISSING-ENTITY"] = [
            {
                "view": "missing.svg",
                "view_id": "missing-view",
                "occurrence_id": "missing-occurrence",
            }
        ]

        issue = build_viewpoints(snapshot, evaluation, inventory)["issues"][0]

        self.assertEqual(issue["viewpoints"], [])
        missing = next(item for item in issue["entity_refs"] if item["entity_id"] == "MISSING-ENTITY")
        self.assertEqual(missing["state"], "unavailable")
        self.assertEqual(missing["destinations"][0]["state"], "unavailable")
        self.assertIn("absent from the snapshot", missing["destinations"][0]["reason"])
        wall = next(item for item in issue["entity_refs"] if item["entity_id"] == "WALL-01")
        self.assertIn("occurrence ID is absent", wall["destinations"][0]["reason"])
        self.assertEqual(len(issue["unavailable_references"]), 3)

    def test_package_and_finding_scenario_mismatches_block_all_destinations(self):
        snapshot, evaluation, inventory = _fixture()
        inventory["scenario_id"] = "SCENARIO-OLD"
        issue = build_viewpoints(snapshot, evaluation, inventory)["issues"][0]
        self.assertEqual(issue["viewpoints"], [])
        self.assertEqual(issue["finding_ref"]["state"], "unavailable")
        self.assertTrue(any("view inventory scenario_id" in reason for reason in issue["finding_ref"]["reasons"]))

        snapshot, evaluation, inventory = _fixture()
        evaluation["findings"][0]["scenario_id"] = "SCENARIO-OLD"
        issue = build_viewpoints(snapshot, evaluation, inventory)["issues"][0]
        self.assertEqual(issue["viewpoints"], [])
        self.assertEqual(issue["finding_ref"]["state"], "unavailable")
        self.assertTrue(any("finding scenario_id" in reason for reason in issue["finding_ref"]["reasons"]))

    def test_missing_view_definition_does_not_create_a_restorable_viewpoint(self):
        snapshot, evaluation, inventory = _fixture()
        del inventory["views"][0]["definition"]

        issue = build_viewpoints(snapshot, evaluation, inventory)["issues"][0]

        self.assertFalse(any(item["view_id"] == "plan-pb" for item in issue["viewpoints"]))
        destinations = [
            destination
            for entity in issue["entity_refs"]
            for destination in entity["destinations"]
            if destination["view_id"] == "plan-pb"
        ]
        self.assertTrue(destinations)
        self.assertTrue(all(item["state"] == "unavailable" for item in destinations))
        self.assertTrue(all("definition" in item["reason"] for item in destinations))


if __name__ == "__main__":
    unittest.main()

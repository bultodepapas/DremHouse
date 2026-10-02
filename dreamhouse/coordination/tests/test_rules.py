from __future__ import annotations

import copy
import unittest

from dreamhouse.coordination.rules import evaluate


def _snapshot(entities: dict[str, dict]) -> dict:
    return {
        "schema_version": "coordination-snapshot-v1",
        "scenario_id": "RULE-TEST",
        "input_hash": "input-test-hash",
        "model_hash": "model-test-hash",
        "geometry": {"hall": {"length_m": 10.0, "width_m": 6.0}, "p2": {"level_m": 3.0}},
        "entities": entities,
    }


def _wall(
    *, x0: float = 0.0, x1: float = 10.0, z0: float | None = 0.0, z1: float | None = 3.0
) -> dict:
    return {
        "id": "WALL-A",
        "kind": "wall",
        "level": "PB",
        "status": "active",
        "source": {"path": "fixture.json", "key": "wall"},
        "geometry": {
            "shape": "line",
            "x0": x0,
            "x1": x1,
            "y0": 0.0,
            "y1": 0.0,
            "z0": z0,
            "z1": z1,
        },
    }


def _opening(
    identifier: str,
    *,
    start: float,
    width: float = 2.0,
    sill: float = 0.75,
    height: float | None = 1.5,
    host_id: str = "WALL-A",
    family: str = "PB.workstation_glazing",
) -> dict:
    level = 0.0
    return {
        "id": identifier,
        "kind": "opening",
        "label": identifier,
        "level": "PB",
        "status": "active",
        "family": family,
        "aliases": [],
        "source": {"path": "fixture.json", "key": identifier},
        "geometry": {
            "shape": "opening",
            "x0": start,
            "x1": start + width,
            "y0": 0.0,
            "y1": 0.0,
            "z0": level + sill if height is not None else None,
            "z1": level + sill + height if height is not None else None,
        },
        "parameters": {
            "facade": "A",
            "start_m": start,
            "width_m": width,
            "height_m": height,
            "sill_m": sill,
            "level_m": level,
        },
        "relationships": {"host_id": host_id, "space_ids": []},
    }


def _by_rule(result: dict, rule_id: str) -> list[dict]:
    return [item for item in result["findings"] if item["rule_id"] == rule_id]


class TestRuleEvaluation(unittest.TestCase):
    def test_opening_fits_facade_reference_line_and_outside_extent_fails(self) -> None:
        inside = _opening("GLZ-A", start=1.0)
        outside = _opening("GLZ-B", start=9.0)
        result = evaluate(_snapshot({"WALL-A": _wall(), "GLZ-A": inside, "GLZ-B": outside}))
        findings = {
            tuple(item["entity_ids"]): item for item in _by_rule(result, "OPENING-IN-HOST-EXTENT")
        }

        self.assertEqual(findings[("GLZ-A", "WALL-A")]["status"], "PASS")
        self.assertEqual(findings[("GLZ-B", "WALL-A")]["status"], "FAIL")
        self.assertTrue(findings[("GLZ-A", "WALL-A")]["evidence"]["horizontal_contained"])
        self.assertFalse(findings[("GLZ-B", "WALL-A")]["evidence"]["horizontal_contained"])

    def test_reference_line_xy_overrun_fails_even_when_host_height_is_unknown(self) -> None:
        host = _wall(z0=None, z1=None)
        outside = _opening("GLZ-OUT", start=9.0, width=2.0)
        inside = _opening("GLZ-IN", start=1.0, width=2.0)
        result = evaluate(_snapshot({"WALL-A": host, "GLZ-OUT": outside, "GLZ-IN": inside}))
        findings = {
            tuple(item["entity_ids"]): item for item in _by_rule(result, "OPENING-IN-HOST-EXTENT")
        }

        self.assertEqual(findings[("GLZ-OUT", "WALL-A")]["status"], "FAIL")
        self.assertEqual(findings[("GLZ-IN", "WALL-A")]["status"], "OPEN")
        self.assertEqual(findings[("GLZ-IN", "WALL-A")]["coverage"], "unsupported")
        self.assertTrue(findings[("GLZ-IN", "WALL-A")]["evidence"]["horizontal_contained"])

    def test_room_linked_window_stays_within_declared_space_and_on_its_boundary(self) -> None:
        window = _opening("W-H1", start=2.5, width=2.0, family="P2.windows")
        window["level"] = "P2"
        window["relationships"]["space_ids"] = ["SPACE-A"]
        space = {
            "id": "SPACE-A",
            "kind": "space",
            "level": "P2",
            "status": "active",
            "geometry": {"shape": "rect", "x0": 2.0, "x1": 5.0, "y0": 0.0, "y1": 4.0},
        }
        baseline = _snapshot({"WALL-A": _wall(), "W-H1": window, "SPACE-A": space})
        baseline_finding = _by_rule(evaluate(baseline), "OPENING-IN-SPACE-BOUNDARY")[0]
        self.assertEqual(baseline_finding["status"], "PASS")

        current = copy.deepcopy(baseline)
        current["entities"]["W-H1"]["parameters"]["start_m"] = 5.5
        current["entities"]["W-H1"]["geometry"]["x0"] = 5.5
        current["entities"]["W-H1"]["geometry"]["x1"] = 7.5
        result = evaluate(current, baseline=baseline)
        findings = {
            item["rule_id"]: item
            for item in result["findings"]
            if item["rule_id"] in {"OPENING-IN-HOST-EXTENT", "OPENING-IN-SPACE-BOUNDARY"}
        }

        self.assertEqual(findings["OPENING-IN-HOST-EXTENT"]["status"], "PASS")
        self.assertEqual(findings["OPENING-IN-SPACE-BOUNDARY"]["status"], "FAIL")
        lifecycle = next(
            item
            for item in result["finding_lifecycle"]["items"]
            if item["rule_id"] == "OPENING-IN-SPACE-BOUNDARY"
        )
        self.assertEqual(lifecycle["state"], "new")
        self.assertEqual(lifecycle["before_status"], "PASS")

    def test_room_linked_window_with_missing_space_geometry_remains_open(self) -> None:
        window = _opening("W-H1", start=2.5, width=2.0, family="P2.windows")
        window["relationships"]["space_ids"] = ["SPACE-A"]
        space = {
            "id": "SPACE-A",
            "kind": "space",
            "status": "active",
            "geometry": {"shape": "rect", "x0": 2.0, "x1": None, "y0": 0.0, "y1": 4.0},
        }
        finding = _by_rule(
            evaluate(_snapshot({"WALL-A": _wall(), "W-H1": window, "SPACE-A": space})),
            "OPENING-IN-SPACE-BOUNDARY",
        )[0]

        self.assertEqual(finding["status"], "OPEN")
        self.assertEqual(finding["coverage"], "unsupported")

    def test_rooflight_hall_extent_checks_studies_and_unknown_hall_bounds(self) -> None:
        rooflight = {
            "id": "RL-STUDY",
            "kind": "opening",
            "level": "PROJECT",
            "status": "study",
            "family": "ROOFLIGHTS.rooflights",
            "source": {"path": "fixture.json", "key": "RL-STUDY"},
            "geometry": {"shape": "rect", "x0": 2.0, "x1": 4.0, "y0": 1.0, "y1": 3.0},
            "parameters": {"length_m": 2.0, "width_m": 2.0},
            "relationships": {"host_id": None, "space_ids": []},
        }
        baseline = _snapshot({"RL-STUDY": rooflight})
        self.assertEqual(
            _by_rule(evaluate(baseline), "ROOFLIGHT-IN-HALL-EXTENT")[0]["status"], "PASS"
        )

        outside = copy.deepcopy(baseline)
        outside["entities"]["RL-STUDY"]["geometry"].update(x0=100.0, x1=102.0)
        outside_result = evaluate(outside, baseline=baseline)
        outside_finding = _by_rule(outside_result, "ROOFLIGHT-IN-HALL-EXTENT")[0]
        self.assertEqual(outside_finding["status"], "FAIL")
        self.assertEqual(outside_finding["coverage"], "evaluated")
        self.assertEqual(outside_result["finding_lifecycle"]["items"][0]["state"], "new")

        unknown_hall = _snapshot({"RL-STUDY": rooflight})
        unknown_hall["geometry"].pop("hall")
        unresolved = _by_rule(evaluate(unknown_hall), "ROOFLIGHT-IN-HALL-EXTENT")[0]
        self.assertEqual(unresolved["status"], "OPEN")
        self.assertEqual(unresolved["coverage"], "unsupported")

    def test_normalized_p2_door_with_opening_semantics_keeps_cf009_gate(self) -> None:
        door = {
            "id": "DOOR-P2-A",
            "kind": "door",
            "level": "P2",
            "status": "active",
            "family": "P2.doors",
            "parameters": {"door_kind": "opening"},
        }
        gate = _by_rule(evaluate(_snapshot({"DOOR-P2-A": door})), "PROFESSIONAL-DESIGN-GATE")[0]

        self.assertEqual(gate["status"], "OPEN")
        self.assertIn("CF-009", gate["evidence"]["governance_refs"])

    def test_enrolled_unresolved_geometry_is_reported_as_unsupported(self) -> None:
        entity = {
            "id": "ENTITY-UNRESOLVED",
            "kind": "equipment",
            "status": "context",
            "source": {"path": "fixture.json", "key": "equipment.unknown"},
            "geometry": {"shape": "unresolved"},
            "parameters": {"reason": "The source identifies the element but gives no plan bounds."},
        }
        finding = _by_rule(
            evaluate(_snapshot({"ENTITY-UNRESOLVED": entity})), "ENTITY-GEOMETRY-CAPABILITY"
        )[0]

        self.assertEqual(finding["status"], "OPEN")
        self.assertEqual(finding["coverage"], "unsupported")
        self.assertEqual(finding["evidence"]["reason"], entity["parameters"]["reason"])
        self.assertEqual(finding["evidence"]["source_model"], "fixture.json#equipment.unknown")

    def test_same_host_overlap_detects_interference_but_allows_touch_and_height_separation(
        self,
    ) -> None:
        entities = {
            "WALL-A": _wall(),
            "O-1": _opening("O-1", start=1.0, width=2.0, sill=0.75, height=1.5),
            "O-2": _opening("O-2", start=2.5, width=2.0, sill=1.0, height=1.0),
            "O-3": _opening("O-3", start=4.5, width=2.0, sill=0.75, height=1.5),
            "O-4": _opening("O-4", start=1.0, width=2.0, sill=2.25, height=0.5),
        }
        result = evaluate(_snapshot(entities))
        pair_status = {
            tuple(item["entity_ids"]): item["status"]
            for item in _by_rule(result, "SAME-HOST-OVERLAP")
        }

        self.assertEqual(pair_status[("O-1", "O-2")], "FAIL")
        self.assertEqual(pair_status[("O-2", "O-3")], "PASS")
        self.assertEqual(pair_status[("O-1", "O-4")], "PASS")

    def test_column_opening_rule_uses_plan_and_height_and_keeps_unknown_height_open(self) -> None:
        opening = _opening("GLZ-A", start=1.0, width=2.0)
        column = {
            "id": "COL-A",
            "kind": "column",
            "level": "PB",
            "status": "active",
            "geometry": {
                "shape": "box",
                "x0": 2.0,
                "x1": 2.5,
                "y0": -0.2,
                "y1": 0.2,
                "z0": 0.0,
                "z1": 3.0,
            },
        }
        result = evaluate(_snapshot({"COL-A": column, "GLZ-A": opening}))
        finding = _by_rule(result, "COLUMN-OPENING-INTERFERENCE")[0]
        self.assertEqual(finding["status"], "FAIL")
        self.assertEqual(finding["evidence"]["intersection_xyz_m"], [0.5, 0.0, 1.5])

        unknown_column = copy.deepcopy(column)
        unknown_column["geometry"]["z1"] = None
        unresolved = evaluate(_snapshot({"COL-A": unknown_column, "GLZ-A": opening}))
        finding = _by_rule(unresolved, "COLUMN-OPENING-INTERFERENCE")[0]
        self.assertEqual(finding["status"], "OPEN")
        self.assertEqual(finding["coverage"], "unsupported")

        unknown_shape = copy.deepcopy(column)
        unknown_shape["geometry"]["shape"] = "rect"
        unresolved_shape = evaluate(_snapshot({"COL-A": unknown_shape, "GLZ-A": opening}))
        finding = _by_rule(unresolved_shape, "COLUMN-OPENING-INTERFERENCE")[0]
        self.assertEqual(finding["status"], "OPEN")

    def test_touching_or_separated_heights_do_not_count_as_column_interference(self) -> None:
        opening = _opening("GLZ-A", start=1.0, width=2.0, sill=1.0, height=1.0)
        column = {
            "id": "COL-A",
            "kind": "column",
            "status": "active",
            "geometry": {
                "shape": "box",
                "x0": 1.5,
                "x1": 2.0,
                "y0": -0.2,
                "y1": 0.2,
                "z0": 0.0,
                "z1": 1.0,
            },
        }
        result = evaluate(_snapshot({"COL-A": column, "GLZ-A": opening}))

        self.assertEqual(_by_rule(result, "COLUMN-OPENING-INTERFERENCE")[0]["status"], "PASS")

    def test_quantities_use_declared_dimensions_exclude_studies_and_keep_missing_door_height_open(
        self,
    ) -> None:
        workstation = _opening("GLZ-WS-A", start=1.0, width=7.2, height=3.05)
        rooflight = {
            "id": "RL-CAR",
            "kind": "opening",
            "level": "PROJECT",
            "status": "active",
            "family": "ROOFLIGHTS.rooflights",
            "source": {"path": "fixture.json", "key": "RL-CAR"},
            "geometry": {"shape": "opening", "x0": 0, "x1": 4.8, "y0": 0, "y1": 2.4},
            "parameters": {"facade": "ROOF", "length_m": 4.8, "width_m": 2.4, "height_m": None},
            "relationships": {"host_id": "ROOF-A", "space_ids": []},
        }
        study = _opening("GLZ-DINING-STUDY-B", start=1.0, width=4.8, height=1.8)
        study["status"] = "study"
        door = {
            "id": "DOOR-REAR",
            "kind": "door",
            "level": "PB",
            "status": "active",
            "family": "PB.exterior_doors",
            "parameters": {"width_m": 0.9, "height_m": None, "sill_m": 0.0, "level_m": 0.0},
            "relationships": {"host_id": "WALL-A", "space_ids": []},
        }
        roof = {
            "id": "ROOF-A",
            "kind": "wall",
            "status": "active",
            "geometry": {
                "shape": "box",
                "x0": 0,
                "x1": 10,
                "y0": 0,
                "y1": 6,
                "z0": 5,
                "z1": 6,
            },
        }
        snapshot = _snapshot(
            {
                "WALL-A": _wall(),
                "ROOF-A": roof,
                "GLZ-WS-A": workstation,
                "RL-CAR": rooflight,
                "GLZ-DINING-STUDY-B": study,
                "DOOR-REAR": door,
            }
        )
        result = evaluate(snapshot)
        by_id = {item["id"]: item for item in result["opening_schedule"]["items"]}
        ledger = result["quantity_ledger"]

        self.assertEqual(by_id["GLZ-WS-A"]["area_m2"], 21.96)
        self.assertIsNone(by_id["GLZ-WS-A"]["net_glass_area_m2"])
        self.assertEqual(by_id["RL-CAR"]["area_m2"], 11.52)
        self.assertIsNone(by_id["DOOR-REAR"]["area_m2"])
        self.assertEqual(
            result["opening_schedule"]["study_items_excluded_from_totals"][0]["id"],
            "GLZ-DINING-STUDY-B",
        )
        self.assertNotIn("GLZ-DINING-STUDY-B", {item["id"] for item in ledger["records"]})
        self.assertEqual(ledger["totals_by_assembly"]["PB-WORKSTATION-GLAZING"]["m2"], 21.96)
        self.assertEqual(ledger["totals_by_assembly"]["ROOFLIGHT-GLAZING"]["m2"], 11.52)
        self.assertEqual(ledger["totals_by_assembly"]["ROOFLIGHT-CURB"]["m"], 14.4)
        self.assertIsNone(ledger["approved_budget_total_cop"])
        self.assertTrue(ledger["coverage"]["not_a_full_takeoff"])
        self.assertIn(
            "gross-floor-area and programme-area metrics from the legacy ledger",
            ledger["coverage"]["excluded"],
        )
        missing_height = next(
            item
            for item in _by_rule(result, "OPENING-DIMENSION-AREA")
            if item["entity_ids"] == ["DOOR-REAR"]
        )
        self.assertEqual(missing_height["status"], "OPEN")

    def test_quantity_provenance_cites_working_source_and_preserves_baseline_source(self) -> None:
        opening = _opening("GLZ-WS-CHANGED", start=1.0, width=2.0, height=1.5)
        opening["source"] = {"path": "source/pb.json", "key": "workstation_glazing"}
        opening["working_source"] = {
            "path": "coordination_scenarios/active.json",
            "key": "changes.GLZ-WS-CHANGED.set",
        }
        result = evaluate(_snapshot({"GLZ-WS-CHANGED": opening}))
        schedule_item = result["opening_schedule"]["items"][0]
        quantity_record = next(
            item
            for item in result["quantity_ledger"]["records"]
            if item["id"] == "Q-GLZ-WS-CHANGED-AREA"
        )

        self.assertEqual(
            schedule_item["source_model"],
            "coordination_scenarios/active.json#changes.GLZ-WS-CHANGED.set",
        )
        self.assertEqual(
            schedule_item["baseline_source_model"], "source/pb.json#workstation_glazing"
        )
        self.assertEqual(quantity_record["source_model"], schedule_item["source_model"])
        self.assertEqual(
            quantity_record["baseline_source_model"], schedule_item["baseline_source_model"]
        )

    def test_declared_module_width_mismatch_remains_visible_in_a_study(self) -> None:
        baseline_entity = _opening("W-H1", start=1.0, width=2.4, height=2.9)
        baseline_entity["status"] = "study"
        baseline_entity["parameters"].update(modules=2, module_width_m=1.2)
        baseline = _snapshot({"W-H1": baseline_entity})

        current = copy.deepcopy(baseline)
        current["entities"]["W-H1"]["parameters"]["width_m"] = 2.5
        current["entities"]["W-H1"]["geometry"]["x1"] = 3.5
        result = evaluate(current, baseline=baseline)
        module_finding = next(
            item
            for item in _by_rule(result, "OPENING-MODULE-CONSISTENCY")
            if item["entity_ids"] == ["W-H1"]
        )

        self.assertEqual(module_finding["status"], "FAIL")
        self.assertEqual(module_finding["evidence"]["computed_width_m"], 2.4)
        self.assertEqual(module_finding["evidence"]["difference_m"], 0.1)
        self.assertEqual(
            result["finding_lifecycle"]["items"][0]["state"],
            "new",
        )

    def test_plan_only_reservations_are_visible_as_unsupported_coverage(self) -> None:
        reservations = {
            f"RES-{index}": {
                "id": f"RES-{index}",
                "kind": "reservation",
                "level": "PROJECT",
                "status": "context",
                "family": "SC01.column_reservations",
                "geometry": {
                    "shape": "rect",
                    "x0": float(index),
                    "x1": float(index) + 0.3,
                    "y0": 1.0,
                    "y1": 1.3,
                    "z0": None,
                    "z1": None,
                },
                "parameters": {"capability": "plan reservation only"},
                "relationships": {"host_id": None, "space_ids": []},
            }
            for index in range(4)
        }
        result = evaluate(_snapshot(reservations))
        reservation_findings = _by_rule(result, "RESERVATION-EXTENT-COVERAGE")
        coverage = next(
            item
            for item in result["coverage"]["rules"]
            if item["rule_id"] == "RESERVATION-EXTENT-COVERAGE"
        )

        self.assertEqual(len(reservation_findings), 4)
        self.assertTrue(all(item["status"] == "OPEN" for item in reservation_findings))
        self.assertEqual(coverage["counts"]["unsupported"], 4)
        self.assertEqual(len(coverage["entity_ids_by_coverage"]["unsupported"]), 4)

    def test_reservation_opening_plan_overlap_is_visible_without_claiming_a_3d_clash(self) -> None:
        reservation = {
            "id": "RES-A",
            "kind": "reservation",
            "status": "context",
            "geometry": {
                "shape": "rect",
                "x0": 2.0,
                "x1": 2.3,
                "y0": 2.0,
                "y1": 2.3,
                "z0": None,
                "z1": None,
            },
        }
        crossing_door = {
            "id": "DOOR-A",
            "kind": "door",
            "status": "active",
            "family": "PB.interior_doors",
            "geometry": {"shape": "opening", "x0": 2.15, "x1": 2.15, "y0": 2.1, "y1": 2.5},
            "parameters": {"width_m": 0.8, "height_m": None},
            "relationships": {"host_id": None, "space_ids": []},
        }
        touching_door = {
            **crossing_door,
            "id": "DOOR-TOUCH",
            "geometry": {"shape": "opening", "x0": 2.3, "x1": 2.3, "y0": 2.1, "y1": 2.5},
        }
        result = evaluate(
            _snapshot(
                {
                    "RES-A": reservation,
                    "DOOR-A": crossing_door,
                    "DOOR-TOUCH": touching_door,
                }
            )
        )
        findings = _by_rule(result, "RESERVATION-OPENING-PLAN")

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["entity_ids"], ["DOOR-A", "RES-A"])
        self.assertEqual(findings[0]["status"], "OPEN")
        self.assertEqual(findings[0]["coverage"], "evaluated")
        self.assertEqual(findings[0]["evidence"]["three_dimensional_clash"], "not evaluated")
        self.assertFalse(findings[0]["evidence"]["reservation_is_structural_member"])
        self.assertEqual(findings[0]["evidence"]["opening_plane_axes_inside_reservation"], ["x"])

    def test_move_creates_new_overlap_finding_and_reports_parameter_delta(self) -> None:
        baseline = _snapshot(
            {
                "WALL-A": _wall(),
                "O-1": _opening("O-1", start=1.0),
                "O-2": _opening("O-2", start=4.0),
            }
        )
        current = copy.deepcopy(baseline)
        current["scenario_id"] = "RULE-TEST-MOVED"
        current["input_hash"] = "current-input-hash"
        current["entities"]["O-2"]["parameters"]["start_m"] = 2.5
        current["entities"]["O-2"]["geometry"]["x0"] = 2.5
        current["entities"]["O-2"]["geometry"]["x1"] = 4.5

        result = evaluate(current, baseline=baseline)
        finding_id = "SAME-HOST-OVERLAP:O-1:O-2"
        lifecycle = next(
            item
            for item in result["finding_lifecycle"]["items"]
            if item["finding_id"] == finding_id
        )

        self.assertEqual(lifecycle["state"], "new")
        self.assertEqual(lifecycle["before_status"], "PASS")
        self.assertEqual(lifecycle["after_status"], "FAIL")
        delta = result["changes"]["modified"]
        self.assertEqual(delta[0]["entity_id"], "O-2")
        changed_paths = {item["path"] for item in delta[0]["deltas"]}
        self.assertIn("parameters.start_m", changed_paths)
        self.assertIn("geometry.x0", changed_paths)

    def test_lifecycle_preserves_findings_for_removed_or_inapplicable_pairs(self) -> None:
        baseline = _snapshot(
            {
                "WALL-A": _wall(),
                "WALL-B": {**_wall(x0=0.0, x1=10.0), "id": "WALL-B"},
                "O-1": _opening("O-1", start=1.0),
                "O-2": _opening("O-2", start=2.5),
            }
        )
        current = copy.deepcopy(baseline)
        current["entities"]["O-2"]["relationships"]["host_id"] = "WALL-B"
        result = evaluate(current, baseline=baseline)
        inapplicable = next(
            item
            for item in result["finding_lifecycle"]["items"]
            if item["finding_id"] == "SAME-HOST-OVERLAP:O-1:O-2"
        )

        self.assertEqual(inapplicable["state"], "inapplicable")
        self.assertEqual(inapplicable["before_status"], "FAIL")
        self.assertIsNone(inapplicable["after_status"])
        self.assertIsNotNone(inapplicable["before_evidence"])

        removed = copy.deepcopy(baseline)
        del removed["entities"]["O-2"]
        removed_result = evaluate(removed, baseline=baseline)
        removed_finding = next(
            item
            for item in removed_result["finding_lifecycle"]["items"]
            if item["finding_id"] == "SAME-HOST-OVERLAP:O-1:O-2"
        )
        self.assertEqual(removed_finding["state"], "removed")
        self.assertIsNotNone(removed_finding["before_evidence"])

    def test_finding_identity_hashes_and_rule_coverage_are_stable(self) -> None:
        snapshot = _snapshot({"WALL-A": _wall(), "GLZ-A": _opening("GLZ-A", start=1.0)})
        first = evaluate(snapshot)
        second = evaluate(snapshot)
        finding = next(
            item for item in first["findings"] if item["rule_id"] == "OPENING-DIMENSION-AREA"
        )
        coverage = next(
            item
            for item in first["coverage"]["rules"]
            if item["rule_id"] == "COLUMN-OPENING-INTERFERENCE"
        )

        self.assertEqual(first["findings"], second["findings"])
        self.assertEqual(finding["scenario_id"], "RULE-TEST")
        self.assertEqual(finding["input_hash"], "input-test-hash")
        self.assertEqual(finding["model_hash"], "model-test-hash")
        self.assertEqual(coverage["counts"]["inapplicable"], 1)
        self.assertEqual(
            set(coverage["counts"]), {"evaluated", "unsupported", "inapplicable", "not_run"}
        )


if __name__ == "__main__":
    unittest.main()

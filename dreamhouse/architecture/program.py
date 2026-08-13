"""Room-performance checks that keep targets distinct from frozen requirements."""

from __future__ import annotations

from typing import Any

from dreamhouse.model.schema import check, open_check


def evaluate_room_program(p2: dict[str, Any]) -> dict[str, Any]:
    spaces = p2["spaces"]
    suite_areas: dict[str, float] = {}
    for space in spaces:
        suite = space.get("suite")
        if suite:
            suite_areas[suite] = suite_areas.get(suite, 0.0) + float(space["w"]) * float(
                space["d"]
            )
    suite_areas = {key: round(value, 2) for key, value in sorted(suite_areas.items())}
    primary_bath = sum(
        float(item["w"]) * float(item["d"])
        for item in spaces
        if item.get("suite") == "M" and item["kind"] == "bath"
    )
    primary_closet = sum(
        float(item["w"]) * float(item["d"])
        for item in spaces
        if item.get("suite") == "M" and item["kind"] == "closet"
    )
    checks = [
        check(
            "PROGRAM-PRIMARY-BATH-17",
            primary_bath >= 17.0,
            f"Primary bath components total {primary_bath:.2f} m2 against the 17 m2 study target",
            entity_ids=tuple(
                item["id"]
                for item in spaces
                if item.get("suite") == "M" and item["kind"] == "bath"
            ),
        ),
        check(
            "PROGRAM-PRIMARY-CLOSET-15",
            primary_closet >= 15.0,
            f"Primary dressing totals {primary_closet:.2f} m2 against the 15 m2 study target",
            entity_ids=tuple(
                item["id"]
                for item in spaces
                if item.get("suite") == "M" and item["kind"] == "closet"
            ),
        ),
    ]
    if suite_areas.get("M", 0.0) < 75.0:
        checks.append(
            open_check(
                "PROGRAM-PRIMARY-TOTAL-75",
                f"Tagged primary-suite components total {suite_areas.get('M', 0.0):.2f} m2; reconcile the 75 m2 owner target and gross/net basis",
                entity_ids=tuple(
                    item["id"] for item in spaces if item.get("suite") == "M"
                ),
            )
        )
    rank = {"PASS": 0, "OPEN": 1, "FAIL": 2}
    return {
        "revision": "0.4-I01-PROGRAM",
        "status": max((item.status for item in checks), key=rank.get),
        "suite_component_areas_m2": suite_areas,
        "measurement_warning": "Component tags are not a boundary survey; shared circulation is excluded.",
        "checks": [item.to_dict() for item in checks],
    }

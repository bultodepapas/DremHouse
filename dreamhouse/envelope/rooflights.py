"""D-054 rooflight geometry and preliminary structural-grid coordination."""

from __future__ import annotations

import math
from typing import Any

from dreamhouse.geometry import Rect, collision_pairs
from dreamhouse.model.schema import CheckResult, check, open_check


def _rect(value: dict[str, Any]) -> Rect:
    return Rect.from_mapping(value, width_key="length", depth_key="width")


def _line_hits(value: float, start: float, end: float, tolerance: float = 1e-9) -> bool:
    return start + tolerance < value < end - tolerance


def analyze_structural_grid(
    model: dict[str, Any],
    *,
    hall_length_m: float = 36.0,
    hall_width_m: float = 18.0,
) -> dict[str, Any]:
    """Identify grid lines crossing openings; this is coordination, not member design."""

    grid = model["structural_grid_hypothesis"]
    bay = float(grid["longitudinal_bay"])
    purlin_spacing = float(grid["purlin_spacing"])
    portal_lines = [round(index * bay, 6) for index in range(round(hall_length_m / bay) + 1)]
    purlin_lines = [
        round(index * purlin_spacing, 6)
        for index in range(round(hall_width_m / purlin_spacing) + 1)
    ]
    conflicts = []
    for value in model["rooflights"]:
        opening = _rect(value)
        portals = [line for line in portal_lines if _line_hits(line, opening.x, opening.x1)]
        purlins = [line for line in purlin_lines if _line_hits(line, opening.y, opening.y1)]
        conflicts.append(
            {
                "rooflight_id": opening.id,
                "portal_lines_x_m": portals,
                "purlin_lines_y_m": purlins,
                "requires_engineered_trimmers": bool(portals or purlins),
            }
        )
    return {
        "status": "OPEN" if any(item["requires_engineered_trimmers"] for item in conflicts) else "PASS",
        "basis": {
            "longitudinal_bay_m": bay,
            "purlin_spacing_m": purlin_spacing,
            "authority": "schematic grid hypothesis only",
        },
        "conflicts": conflicts,
        "note": "A crossing flags a trimmer/design task; it does not prove infeasibility.",
    }


def validate_rooflights(
    model: dict[str, Any],
    *,
    canonical_double_height: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Strongly validate D-054 geometry and expose every unresolved grid crossing."""

    zone_value = canonical_double_height or model["double_height"]
    zone = Rect(
        "DOUBLE-HEIGHT",
        float(zone_value["x0"]),
        float(zone_value["y0"]),
        float(zone_value["x1"]) - float(zone_value["x0"]),
        float(zone_value["y1"]) - float(zone_value["y0"]),
    )
    values = model["rooflights"]
    rectangles = [_rect(value) for value in values]
    checks: list[CheckResult] = [
        check(
            "ROOF-D054-COUNT",
            len(values) == 2,
            "D-054 scenario contains exactly two rooflights",
            entity_ids=tuple(item.id for item in rectangles),
        ),
        check(
            "ROOF-D054-UNIQUE-IDS",
            len({item.id for item in rectangles}) == len(rectangles),
            "Rooflight identifiers are unique",
            entity_ids=tuple(item.id for item in rectangles),
        ),
        check(
            "ROOF-D054-CONTAINMENT",
            all(zone.contains(item) for item in rectangles),
            "Both rooflights are contained in the double-height zone",
            entity_ids=tuple(item.id for item in rectangles) + (zone.id,),
        ),
        check(
            "ROOF-D054-NO-OVERLAP",
            not collision_pairs(rectangles),
            "Rooflight footprints do not overlap",
            entity_ids=tuple(item.id for item in rectangles),
        ),
        check(
            "ROOF-D054-EQUAL-DIMENSIONS",
            len(rectangles) == 2
            and math.isclose(rectangles[0].width, rectangles[1].width, abs_tol=1e-9)
            and math.isclose(rectangles[0].depth, rectangles[1].depth, abs_tol=1e-9),
            "D-054 rooflights have equal plan dimensions",
            entity_ids=tuple(item.id for item in rectangles),
        ),
        check(
            "ROOF-D054-DECLARED-AREAS",
            all(math.isclose(item.area, float(value["area"]), abs_tol=1e-9) for item, value in zip(rectangles, values, strict=True)),
            "Each declared rooflight area equals length times width",
            entity_ids=tuple(item.id for item in rectangles),
        ),
    ]

    if len(rectangles) == 2:
        ordered = sorted(rectangles, key=lambda item: item.x)
        midpoint_x = (zone.x + zone.x1) / 2
        expected_centres = [
            ((zone.x + midpoint_x) / 2, (zone.y + zone.y1) / 2),
            ((midpoint_x + zone.x1) / 2, (zone.y + zone.y1) / 2),
        ]
        tolerance = float(model.get("center_tolerance_m", 0.1))
        centred = all(
            math.isclose(item.x + item.width / 2, expected[0], abs_tol=tolerance)
            and math.isclose(item.y + item.depth / 2, expected[1], abs_tol=tolerance)
            for item, expected in zip(ordered, expected_centres, strict=True)
        )
        separation = ordered[1].x - ordered[0].x1
        minimum = float(model.get("minimum_edge_separation_m", 0.0))
        checks.extend(
            [
                check(
                    "ROOF-D054-HALF-CENTRES",
                    centred,
                    "One rooflight is centred in each longitudinal half",
                    entity_ids=tuple(item.id for item in ordered),
                ),
                check(
                    "ROOF-D054-SEPARATION",
                    separation >= minimum,
                    f"Clear edge separation is {separation:.2f} m against {minimum:.2f} m minimum hypothesis",
                    entity_ids=tuple(item.id for item in ordered),
                ),
            ]
        )

    grid = analyze_structural_grid(
        model,
        hall_length_m=float(model["roof"]["length"]),
        hall_width_m=float(model["roof"]["width"]),
    )
    if grid["status"] == "OPEN":
        crossing_ids = tuple(
            item["rooflight_id"]
            for item in grid["conflicts"]
            if item["requires_engineered_trimmers"]
        )
        checks.append(
            open_check(
                "ROOF-D054-STRUCTURAL-TRIMMERS",
                "Both D-054 openings cross schematic portal/purlin lines; engineered trimmers and diaphragm detailing remain open",
                entity_ids=crossing_ids,
            )
        )

    rank = {"PASS": 0, "OPEN": 1, "FAIL": 2}
    overall = max((item.status for item in checks), key=rank.get)
    return {
        "revision": model["revision"],
        "status": overall,
        "checks": [item.to_dict() for item in checks],
        "structural_grid": grid,
        "total_area_m2": round(sum(item.area for item in rectangles), 3),
        "curb_perimeter_m": round(sum(2 * (item.width + item.depth) for item in rectangles), 3),
    }

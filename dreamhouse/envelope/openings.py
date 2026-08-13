"""One schedule for wall glazing, P2 windows, and rooflights."""

from __future__ import annotations

from typing import Any


def _wall_opening(
    value: dict[str, Any], *, source: str, width_keys: tuple[str, str]
) -> dict[str, Any]:
    start_key, end_key = width_keys
    width = float(value[end_key]) - float(value[start_key])
    height = float(value["height"])
    return {
        "id": value["id"],
        "kind": "vertical_glazing",
        "source": source,
        "location": value.get("edge", value.get("side", value.get("facade"))),
        "width_m": round(width, 3),
        "height_m": round(height, 3),
        "area_m2": round(width * height, 3),
        "perimeter_m": round(2 * (width + height), 3),
    }


def build_opening_schedule(
    pb: dict[str, Any], p2: dict[str, Any], rooflights: dict[str, Any]
) -> dict[str, Any]:
    """Build traceable, non-priced opening quantities from active geometry."""

    items = [
        _wall_opening(value, source="PB.technical_glazing", width_keys=("x0", "x1"))
        for value in pb["technical_glazing"]
    ]
    items.extend(
        _wall_opening(value, source="P2.windows", width_keys=("from", "to"))
        for value in p2["windows"]
    )
    for value in rooflights["rooflights"]:
        length = float(value["length"])
        width = float(value["width"])
        items.append(
            {
                "id": value["id"],
                "kind": "rooflight",
                "source": "ROOFLIGHTS.rooflights",
                "location": value["below"],
                "width_m": round(length, 3),
                "height_m": round(width, 3),
                "area_m2": round(length * width, 3),
                "perimeter_m": round(2 * (length + width), 3),
            }
        )
    totals: dict[str, float] = {}
    for item in items:
        totals[item["kind"]] = round(totals.get(item["kind"], 0.0) + item["area_m2"], 3)
    return {
        "revision": "0.4-I01-OPENINGS",
        "status": "derived quantity schedule; not procurement authority",
        "items": items,
        "area_totals_m2": totals,
    }

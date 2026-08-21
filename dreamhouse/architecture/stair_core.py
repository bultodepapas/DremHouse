"""Shared mathematical model for PB/P2 stair and four-column coordination.

The model is intentionally schematic and fail-closed.  It coordinates plan
geometry and arithmetic; it does not select steel members, resolve fire/egress,
or authorize fabrication or construction.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

DEFAULT_STAIR_CORE = Path(__file__).resolve().parents[1] / "stair_core.json"


class StairCoreError(ValueError):
    """The canonical stair-core input is incomplete or internally inconsistent."""


def load_stair_core(path: Path = DEFAULT_STAIR_CORE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def derived_stair_values(model: dict[str, Any]) -> dict[str, float]:
    enclosure = model["enclosure"]
    levels = model["levels"]
    stair = model["stair"]
    total_rise = float(levels["p2_finished_floor"]) - float(levels["pb_finished_floor"])
    riser = total_rise / int(stair["total_risers"])
    going = float(stair["going"])
    return {
        "enclosure_width_x": float(enclosure["x1"]) - float(enclosure["x0"]),
        "enclosure_width_y": float(enclosure["y1"]) - float(enclosure["y0"]),
        "clear_width_x": (
            float(enclosure["x1"])
            - float(enclosure["x0"])
            - 2.0 * float(enclosure["wall_thickness"])
        ),
        "clear_width_y": (
            float(enclosure["y1"])
            - float(enclosure["y0"])
            - 2.0 * float(enclosure["wall_thickness"])
        ),
        "total_rise": total_rise,
        "riser": riser,
        "going": going,
        "two_risers_plus_going": 2.0 * riser + going,
        "flight_run": going * int(stair["treads_per_flight"][0]),
        "slope_degrees": math.degrees(math.atan2(riser, going)),
        "rear_discharge_level_difference": (
            float(stair["intermediate_landing"]["level"])
            - float(model["open_conflicts"][0]["rear_door_level"])
        ),
    }


def validate_stair_core(model: dict[str, Any]) -> list[dict[str, str]]:
    values = derived_stair_values(model)
    enclosure = model["enclosure"]
    levels = model["levels"]
    stair = model["stair"]
    structure = model["structure"]
    code = model["code_screen"]
    tolerance = 1e-9
    checks: list[dict[str, str]] = []

    def add(rule_id: str, ok: bool, message: str, *, open_gate: bool = False) -> None:
        checks.append(
            {
                "rule_id": rule_id,
                "status": "OPEN" if open_gate else ("PASS" if ok else "FAIL"),
                "message": message,
            }
        )

    add(
        "STAIR-ENCLOSURE",
        math.isclose(values["enclosure_width_x"], 4.5, abs_tol=tolerance)
        and math.isclose(values["enclosure_width_y"], 3.6, abs_tol=tolerance)
        and math.isclose(values["clear_width_x"], 4.1, abs_tol=tolerance)
        and math.isclose(values["clear_width_y"], 3.2, abs_tol=tolerance),
        "PB and P2 share one 4.50 x 3.60 m enclosure with a 4.10 x 3.20 m schematic clear rectangle.",
    )
    add(
        "STAIR-RISERS",
        int(stair["total_risers"]) == sum(int(value) for value in stair["risers_per_flight"])
        and math.isclose(values["riser"], 3.8 / 22.0, abs_tol=tolerance),
        f"22 equal risers give {values['riser'] * 1000.0:.1f} mm per riser over 3.80 m.",
    )
    add(
        "STAIR-GOING-RULE",
        float(code["two_risers_plus_going_min"]) - tolerance
        <= values["two_risers_plus_going"]
        <= float(code["two_risers_plus_going_max"]) + tolerance,
        (
            f"With a {values['going'] * 1000.0:.0f} mm going, 2R+G = "
            f"{values['two_risers_plus_going'] * 1000.0:.1f} mm within the 600-640 mm screen."
        ),
    )
    lower = stair["lower_flight"]
    upper = stair["upper_flight"]
    landing = stair["intermediate_landing"]
    add(
        "STAIR-FLIGHT-RUN",
        math.isclose(float(lower["x1"]) - float(lower["x0"]), values["flight_run"], abs_tol=tolerance)
        and math.isclose(float(upper["x1"]) - float(upper["x0"]), values["flight_run"], abs_tol=tolerance),
        f"Both flights use 10 equal 270 mm goings for a {values['flight_run']:.2f} m run.",
    )
    add(
        "STAIR-WIDTH-LANDING",
        float(stair["flight_width"]) >= float(code["minimum_screened_width"])
        and float(stair["intermediate_landing_depth"]) >= float(stair["flight_width"])
        and math.isclose(
            float(landing["x1"]) - float(landing["x0"]),
            float(stair["intermediate_landing_depth"]),
            abs_tol=tolerance,
        ),
        "Each flight is 1.40 m clear and the intermediate landing is 1.40 m deep.",
    )
    add(
        "STAIR-TRANSVERSE-CLOSURE",
        math.isclose(
            2.0 * float(stair["side_clearance"])
            + 2.0 * float(stair["flight_width"])
            + float(stair["clear_gap_between_flights"]),
            values["clear_width_y"],
            abs_tol=tolerance,
        ),
        "0.10 + 1.40 + 0.20 + 1.40 + 0.10 = 3.20 m clear transverse closure.",
    )
    add(
        "STAIR-LANDING-RISE",
        math.isclose(float(levels["intermediate_landing"]), values["total_rise"] / 2.0, abs_tol=tolerance)
        and float(levels["intermediate_landing"]) <= float(code["maximum_rise_between_landings"]),
        "The intermediate landing is at +1.90 m, below the 3.60 m screened maximum rise between landings.",
    )
    expected_columns = {
        ("GW-STAIR-S", float(enclosure["x0"]), float(enclosure["y0"])),
        ("GW-STAIR-N", float(enclosure["x0"]), float(enclosure["y1"])),
        ("STAIR-REAR-S", float(enclosure["x1"]), float(enclosure["y0"])),
        ("STAIR-REAR-N", float(enclosure["x1"]), float(enclosure["y1"])),
    }
    actual_columns = {
        (item["id"], float(item["x"]), float(item["y"]))
        for item in structure["column_reservations"]
    }
    add(
        "STAIR-FOUR-COLUMNS",
        actual_columns == expected_columns,
        "Four and only four foundation-to-roof column reservations coincide with the enclosure corners.",
    )
    add(
        "STAIR-STRUCTURAL-SEPARATION",
        structure["stair_flights_primary_lateral_role"] is False
        and structure["drift_compatible_stair_connections_required"] is True,
        "The independent enclosure frame carries the structural study; stair flights receive no primary lateral credit.",
    )
    add(
        "STAIR-HEADROOM",
        False,
        "A longitudinal section must verify at least 2.05 m headroom, stringer depth, landing beams and door clearances.",
        open_gate=True,
    )
    add(
        "STAIR-REAR-DISCHARGE-LEVEL",
        False,
        (
            "CF-011: the current rear-door plane meets the +1.90 m intermediate landing, "
            "not PB grade; a sectioned discharge alternative is required."
        ),
        open_gate=True,
    )
    return checks


def assert_stair_core_renderable(model: dict[str, Any]) -> None:
    failures = [item for item in validate_stair_core(model) if item["status"] == "FAIL"]
    if failures:
        detail = "; ".join(f"{item['rule_id']}: {item['message']}" for item in failures)
        raise StairCoreError("Stair-core model failed closed: " + detail)

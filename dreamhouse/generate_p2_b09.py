"""Generate the coordinated upper-floor revision based on the b04 spatial logic.

The model is deliberately fail-closed: rooms must tile the 18 x 15 m envelope,
every door must sit on the shared boundary of the two spaces it connects, and
every space must be reachable from the protected stair.  Passing those checks
does not establish regulatory compliance or construction authority.
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import textwrap
from collections import deque
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from dreamhouse.architecture.stair_core import validate_stair_core

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(__file__).with_name("p2_b09.json")
OUT = ROOT / "planos" / "conceptual_v0.3_b09_p2"

PLAN_NAME = "DH-ARQ-PLN-002-R08_P2-COORDINATED.svg"
ACCESS_NAME = "DH-ARQ-DIA-001-R08_P2-ACCESS-EGRESS.svg"
WIDTH = 1684
HEIGHT = 1191
PLAN_X = 72.0
PLAN_BOTTOM = 953.0
SCALE = 40.0

PAPER = "#f6f3ec"
INK = "#172a33"
MUTED = "#617078"
GRID = "#a9b4b7"
TEAL = "#168aa3"
GREEN = "#2e7252"
AMBER = "#bd7626"
RED = "#a63f31"
PURPLE = "#76558f"

COLORS = {
    "bedroom": "#dce9ec",
    "master": "#ead9ca",
    "bath": "#d7e8e5",
    "closet": "#e9e0d3",
    "circulation": "#f1ece2",
    "service": "#e2e7df",
    "deck": "#e6d5b9",
    "shared": "#e8dcc8",
    "vertical": "#ddd5ce",
    "wellness": "#dec5a4",
}


def output_names(model: dict[str, Any]) -> tuple[str, str, str | None]:
    """Return revision-aware output names while preserving the issued b09 names."""

    drawing_revision = model["drawing_revision"]
    detail = None
    if model.get("relocated_laundry") or model.get("egress_reserve"):
        detail = f"DH-ARQ-DET-002-{drawing_revision}_OWNER-PRIORITIES.svg"
    return (
        f"DH-ARQ-PLN-002-{drawing_revision}_P2-COORDINATED.svg",
        f"DH-ARQ-DIA-001-{drawing_revision}_P2-ACCESS-EGRESS.svg",
        detail,
    )


def acoustic_detail_name(model: dict[str, Any]) -> str | None:
    """Return the D-057 wall-detail filename when the model declares P2-W01."""

    if not model.get("acoustic_partition"):
        return None
    return f"DH-ARQ-DET-003-{model['drawing_revision']}_P2-ACOUSTIC-PARTITION.svg"


def hall_edge_detail_name(model: dict[str, Any]) -> str | None:
    """Return the D-058 hall-edge detail filename when P2-W04 is declared."""

    if not model.get("hall_edge_partition"):
        return None
    return f"DH-ARQ-DET-004-{model['drawing_revision']}_P2-HALL-EDGE.svg"


def exterior_wall_detail_name(model: dict[str, Any]) -> str | None:
    """Return the D-059 exterior-wall detail filename when P2-W05 is declared."""

    if not model.get("exterior_wall_assembly"):
        return None
    return f"DH-ARQ-DET-005-{model['drawing_revision']}_P2-EXTERIOR-WALL.svg"


def sheet_ids(model: dict[str, Any]) -> tuple[str, str, str]:
    drawing_revision = model["drawing_revision"]
    return (
        f"DH-ARQ-PLN-002-{drawing_revision}",
        f"DH-ARQ-DIA-001-{drawing_revision}",
        f"DH-ARQ-DET-002-{drawing_revision}",
    )


class P2ModelError(ValueError):
    """The P2 model cannot be validated or safely rendered."""


def load_model(path: Path = DATA) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def _fmt(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def _sx(x: float, *, origin: float = PLAN_X, scale: float = SCALE) -> float:
    return origin + (x - 21.0) * scale


def _sy(y: float, *, bottom: float = PLAN_BOTTOM, scale: float = SCALE) -> float:
    return bottom - y * scale


def _attrs(**attrs: object) -> str:
    def attribute_name(key: str) -> str:
        return "class" if key == "css_class" else key.replace("_", "-")

    return " ".join(
        f'{attribute_name(key)}="{_esc(value)}"'
        for key, value in attrs.items()
        if value is not None
    )


def _rect(x: float, y: float, w: float, h: float, **attrs: object) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {_attrs(**attrs)}/>'


def _line(x1: float, y1: float, x2: float, y2: float, **attrs: object) -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" {_attrs(**attrs)}/>'


def _text(
    x: float,
    y: float,
    value: object,
    size: float,
    *,
    anchor: str = "start",
    weight: int = 400,
    fill: str = INK,
    css_class: str | None = None,
) -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
        f'font-weight="{weight}" fill="{fill}" class="{_esc(css_class or "")}">'
        f"{_esc(value)}</text>"
    )


def _multiline(
    x: float,
    y: float,
    lines: list[str],
    size: float,
    *,
    leading: float = 1.35,
    anchor: str = "start",
    weight: int = 400,
    fill: str = INK,
) -> str:
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if index == 0 else size * leading}">{_esc(line)}</tspan>'
        for index, line in enumerate(lines)
    )
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
        f'font-weight="{weight}" fill="{fill}">{spans}</text>'
    )


def _space_index(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {space["id"]: space for space in model["spaces"]}


def _wall_thickness(space: dict[str, Any], envelope: dict[str, Any]) -> float:
    if space["kind"] in {"bath", "vertical", "wellness"}:
        return float(envelope["wet_wall"])
    return float(envelope["partition"])


def _boundary_wall_type(
    a: dict[str, Any], b: dict[str, Any], model: dict[str, Any]
) -> tuple[str, float, str, str | None]:
    """Classify a shared P2 boundary for the coordination drawing only."""

    kinds = {a["kind"], b["kind"]}
    wall_schedule = model.get("wall_schedule")
    if wall_schedule:
        if "vertical" in kinds:
            wall_id, color, dash = "P2-W03", PURPLE, "7 4"
        elif "wellness" in kinds:
            wall_id, color, dash = "P2-W02S", GREEN, "6 3"
        elif "bath" in kinds:
            wall_id, color, dash = "P2-W02", AMBER, "5 3"
        else:
            suite_a, suite_b = a.get("suite"), b.get("suite")
            wall_id = "P2-W01A" if suite_a == suite_b else "P2-W01B"
            color, dash = (MUTED, None) if wall_id == "P2-W01A" else (TEAL, None)
        return wall_id, float(wall_schedule[wall_id]["nominal_total_m"]), color, dash
    if "vertical" in kinds:
        return "P2-W03", float(model["envelope"]["wet_wall"]), PURPLE, "7 4"
    if kinds & {"bath", "wellness"}:
        return "P2-W02", float(model["envelope"]["wet_wall"]), AMBER, "5 3"
    return "P2-W01", float(model["envelope"]["partition"]), INK, None


def _wall_side_allowances(
    space: dict[str, Any], model: dict[str, Any]
) -> dict[str, float]:
    """Return conservative wall deductions at each room side for a scheduled wall family."""

    envelope = model["envelope"]
    tolerance = float(model["tolerances"]["geometry_m"])
    ext = float(envelope["exterior_wall"])
    hall_edge = float(envelope.get("hall_edge_wall", ext))
    x0 = float(space["x"])
    x1 = x0 + float(space["w"])
    y0 = float(space["y"])
    y1 = y0 + float(space["d"])
    x_min = float(envelope["x"])
    x_max = x_min + float(envelope["length"])
    y_max = float(envelope["width"])
    family_balcony = model.get("family_balcony")
    hall_is_open = bool(
        family_balcony
        and y0 >= float(family_balcony["from_y"]) - tolerance
        and y1 <= float(family_balcony["to_y"]) + tolerance
    )
    deductions = {
        "x0": 0.0 if hall_is_open else hall_edge if math.isclose(x0, x_min, abs_tol=tolerance) else 0.0,
        "x1": ext if math.isclose(x1, x_max, abs_tol=tolerance) else 0.0,
        "y0": ext if math.isclose(y0, 0.0, abs_tol=tolerance) else 0.0,
        "y1": ext if math.isclose(y1, y_max, abs_tol=tolerance) else 0.0,
    }
    for other in model["spaces"]:
        if other["id"] == space["id"]:
            continue
        shared = _shared_boundary(space, other, tolerance)
        if not shared:
            continue
        orientation, coordinate, _, _ = shared
        _, thickness, _, _ = _boundary_wall_type(space, other, model)
        half = thickness / 2.0
        if orientation == "vertical":
            side = "x0" if math.isclose(coordinate, x0, abs_tol=tolerance) else "x1"
        else:
            side = "y0" if math.isclose(coordinate, y0, abs_tol=tolerance) else "y1"
        deductions[side] = max(deductions[side], half)
    return deductions


def net_dimensions(
    space: dict[str, Any],
    envelope: dict[str, Any],
    model: dict[str, Any] | None = None,
) -> tuple[float, float]:
    """Return schematic clear dimensions using half-partition allocation."""

    if model and model.get("wall_schedule"):
        deductions = _wall_side_allowances(space, model)
        return max(0.0, float(space["w"]) - deductions["x0"] - deductions["x1"]), max(
            0.0, float(space["d"]) - deductions["y0"] - deductions["y1"]
        )
    tolerance = 1e-9
    ext = float(envelope["exterior_wall"])
    hall_edge = float(envelope.get("hall_edge_wall", ext))
    half = _wall_thickness(space, envelope) / 2.0
    x0 = float(space["x"])
    x1 = x0 + float(space["w"])
    y0 = float(space["y"])
    y1 = y0 + float(space["d"])
    x_min = float(envelope["x"])
    x_max = x_min + float(envelope["length"])
    y_max = float(envelope["width"])
    dx0 = hall_edge if math.isclose(x0, x_min, abs_tol=tolerance) else half
    dx1 = ext if math.isclose(x1, x_max, abs_tol=tolerance) else half
    dy0 = ext if math.isclose(y0, 0.0, abs_tol=tolerance) else half
    dy1 = ext if math.isclose(y1, y_max, abs_tol=tolerance) else half
    return max(0.0, float(space["w"]) - dx0 - dx1), max(
        0.0, float(space["d"]) - dy0 - dy1
    )


def net_area(
    space: dict[str, Any],
    envelope: dict[str, Any],
    model: dict[str, Any] | None = None,
) -> float:
    width, depth = net_dimensions(space, envelope, model)
    return width * depth


def _overlap(a: dict[str, Any], b: dict[str, Any], tolerance: float) -> bool:
    dx = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
    dy = min(a["y"] + a["d"], b["y"] + b["d"]) - max(a["y"], b["y"])
    return dx > tolerance and dy > tolerance


def _shared_boundary(
    a: dict[str, Any], b: dict[str, Any], tolerance: float
) -> tuple[str, float, float, float] | None:
    ax0, ax1 = float(a["x"]), float(a["x"] + a["w"])
    ay0, ay1 = float(a["y"]), float(a["y"] + a["d"])
    bx0, bx1 = float(b["x"]), float(b["x"] + b["w"])
    by0, by1 = float(b["y"]), float(b["y"] + b["d"])
    if math.isclose(ax1, bx0, abs_tol=tolerance) or math.isclose(bx1, ax0, abs_tol=tolerance):
        low, high = max(ay0, by0), min(ay1, by1)
        if high - low > tolerance:
            coordinate = ax1 if math.isclose(ax1, bx0, abs_tol=tolerance) else bx1
            return "vertical", coordinate, low, high
    if math.isclose(ay1, by0, abs_tol=tolerance) or math.isclose(by1, ay0, abs_tol=tolerance):
        low, high = max(ax0, bx0), min(ax1, bx1)
        if high - low > tolerance:
            coordinate = ay1 if math.isclose(ay1, by0, abs_tol=tolerance) else by1
            return "horizontal", coordinate, low, high
    return None


def _window_belongs_to_room(
    window: dict[str, Any], room: dict[str, Any], envelope: dict[str, Any], tolerance: float
) -> bool:
    x0, x1 = float(room["x"]), float(room["x"] + room["w"])
    y0, y1 = float(room["y"]), float(room["y"] + room["d"])
    edge = window["edge"]
    start, end = float(window["from"]), float(window["to"])
    if edge == "south":
        return math.isclose(y0, 0.0, abs_tol=tolerance) and start >= x0 - tolerance and end <= x1 + tolerance
    if edge == "north":
        return math.isclose(y1, envelope["width"], abs_tol=tolerance) and start >= x0 - tolerance and end <= x1 + tolerance
    if edge == "east":
        east = float(envelope["x"] + envelope["length"])
        return math.isclose(x1, east, abs_tol=tolerance) and start >= y0 - tolerance and end <= y1 + tolerance
    return False


def validate_model(model: dict[str, Any]) -> list[dict[str, str]]:
    """Validate geometry, access topology, programme controls and declared open gates."""

    spaces = model["spaces"]
    envelope = model["envelope"]
    tolerance = float(model["tolerances"]["geometry_m"])
    by_id = _space_index(model)
    checks: list[tuple[str, bool, str]] = []

    ids = [space["id"] for space in spaces]
    checks.append(("P2-IDS", len(ids) == len(set(ids)), "Space identifiers are unique"))

    finite_positive = all(
        math.isfinite(float(space[key])) and float(space[key]) > 0.0
        for space in spaces
        for key in ("w", "d")
    )
    checks.append(("P2-FINITE", finite_positive, "All room dimensions are finite and positive"))

    x_min = float(envelope["x"])
    x_max = x_min + float(envelope["length"])
    y_max = float(envelope["width"])
    inside = all(
        space["x"] >= x_min - tolerance
        and space["x"] + space["w"] <= x_max + tolerance
        and space["y"] >= -tolerance
        and space["y"] + space["d"] <= y_max + tolerance
        for space in spaces
    )
    checks.append(("P2-ENVELOPE", inside, "All spaces remain inside the 18 x 15 m P2 envelope"))

    overlaps = [
        f"{a['id']}|{b['id']}"
        for index, a in enumerate(spaces)
        for b in spaces[index + 1 :]
        if _overlap(a, b, tolerance)
    ]
    checks.append(
        (
            "P2-NO-OVERLAP",
            not overlaps,
            "No room overlaps" if not overlaps else "Overlaps: " + ", ".join(overlaps),
        )
    )

    gross = sum(float(space["w"] * space["d"]) for space in spaces)
    envelope_area = float(envelope["length"] * envelope["width"])
    checks.append(
        (
            "P2-AREA-CLOSURE",
            math.isclose(gross, envelope_area, abs_tol=tolerance),
            f"Gross room tessellation {gross:.3f} m2 = envelope {envelope_area:.3f} m2",
        )
    )

    n1 = net_area(by_id["H1-D"], envelope, model)
    n2 = net_area(by_id["H2-D"], envelope, model)
    dims1 = net_dimensions(by_id["H1-D"], envelope, model)
    dims2 = net_dimensions(by_id["H2-D"], envelope, model)
    ratio1 = max(dims1) / min(dims1)
    ratio2 = max(dims2) / min(dims2)
    tolerances = model["tolerances"]
    checks.extend(
        [
            (
                "P2-CHILD-EQUAL",
                abs(n1 - n2) <= tolerances["child_area_delta_m2"] + tolerance,
                f"D-042 net bedrooms: H1 {n1:.2f} m2, H2 {n2:.2f} m2, delta {abs(n1 - n2):.2f} m2",
            ),
            (
                "P2-CHILD-PROPORTION",
                ratio1 <= tolerances["child_ratio_max"] + tolerance
                and ratio2 <= tolerances["child_ratio_max"] + tolerance
                and abs(ratio1 - ratio2) <= tolerances["child_ratio_delta"] + tolerance,
                f"Child-bedroom ratios {ratio1:.2f}:1 and {ratio2:.2f}:1",
            ),
        ]
    )

    circulation = [space for space in spaces if space["kind"] == "circulation"]
    narrowest = min(
        (min(net_dimensions(space, envelope, model)), space["id"]) for space in circulation
    )
    checks.append(
        (
            "P2-CIRCULATION",
            narrowest[0] >= tolerances["circulation_min_clear_m"] - tolerance,
            f"Narrowest declared circulation is {narrowest[1]} at {narrowest[0]:.2f} m clear",
        )
    )

    phase_ok = all(
        space["y"] >= model["phase_boundary_y"] - tolerance
        for space in spaces
        if space["phase"] == 2
    ) and all(
        space["y"] + space["d"] <= model["phase_boundary_y"] + tolerance
        for space in spaces
        if space["phase"] == 1
    )
    checks.append(("P2-PHASING", phase_ok, "F1 and F2 meet at one isolatable Y=11.00 m boundary"))

    family_centre = model.get("family_centre")
    if family_centre:
        family = by_id.get(family_centre["space_id"])
        target_width = float(family_centre["gross_width_m"])
        target_depth = float(family_centre["gross_depth_m"])
        family_ok = bool(family) and math.isclose(
            float(family["w"]), target_width, abs_tol=tolerance
        ) and math.isclose(float(family["d"]), target_depth, abs_tol=tolerance)
        checks.append(
            (
                "P2-FAMILY-CENTRE",
                family_ok,
                (
                    f"One coherent family room is coordinated at {target_width:.2f} x "
                    f"{target_depth:.2f} m gross with circulation absorbed at its edges"
                ),
            )
        )

    central_distributor = model.get("central_distributor")
    wellness_suite = model.get("wellness_suite")
    if central_distributor:
        main = by_id.get(central_distributor["main_space_id"])
        extension = by_id.get(central_distributor["extension_space_id"])
        spur = by_id.get(central_distributor["short_spur_id"])
        central_ok = (
            bool(main)
            and bool(extension)
            and bool(spur)
            and "ARR" not in by_id
            and "F2-HALL" not in by_id
            and math.isclose(float(main["w"] * main["d"]), 37.80, abs_tol=tolerance)
            and math.isclose(float(extension["w"] * extension["d"]), 15.225, abs_tol=tolerance)
            and math.isclose(float(spur["w"] * spur["d"]), 6.525, abs_tol=tolerance)
        )
        checks.append(
            (
                "P2-CENTRAL-DISTRIBUTOR",
                central_ok,
                (
                    "The stair opens to a 37.80 m2 family distributor; the 15.00 m lobby "
                    + (
                        "is replaced by a 15.23 m2 open study edge and a 6.53 m2 dry wellness threshold"
                        if model.get("wellness_suite")
                        else "is replaced by a 15.23 m2 open study edge and one 6.53 m2 short spur"
                    )
                ),
            )
        )

    door_errors: list[str] = []
    graph: dict[str, set[str]] = {space_id: set() for space_id in by_id}
    for door in model["doors"]:
        first, second = door["connects"]
        if first not in by_id or second not in by_id:
            door_errors.append(f"{door['id']} references a missing space")
            continue
        boundary = _shared_boundary(by_id[first], by_id[second], tolerance)
        if boundary is None:
            door_errors.append(f"{door['id']} connects non-adjacent spaces")
            continue
        wall, coordinate, low, high = boundary
        declared_coordinate = float(door["x"] if wall == "vertical" else door["y"])
        start = float(door["at"])
        end = start + float(door["width"])
        if door["wall"] != wall or not math.isclose(
            declared_coordinate, coordinate, abs_tol=tolerance
        ):
            door_errors.append(f"{door['id']} is assigned to the wrong wall")
        elif start < low - tolerance or end > high + tolerance:
            door_errors.append(f"{door['id']} falls outside the shared wall")
        else:
            graph[first].add(second)
            graph[second].add(first)
    checks.append(
        (
            "P2-DOOR-GEOMETRY",
            not door_errors,
            f"All {len(model['doors'])} doors/openings lie on the boundaries they connect"
            if not door_errors
            else "Door errors: " + "; ".join(door_errors),
        )
    )

    reached = {"ESC"}
    queue: deque[str] = deque(["ESC"])
    while queue:
        current = queue.popleft()
        for neighbor in graph[current] - reached:
            reached.add(neighbor)
            queue.append(neighbor)
    missing = sorted(set(by_id) - reached)
    checks.append(
        (
            "P2-ACCESS-GRAPH",
            not missing,
            "Every enclosed space is connected to the protected stair"
            if not missing
            else "Spaces without a route to the stair: " + ", ".join(missing),
        )
    )

    window_errors = [
        window["id"]
        for window in model["windows"]
        if window["room_id"] not in by_id
        or not _window_belongs_to_room(
            window, by_id.get(window["room_id"], {}), envelope, tolerance
        )
    ]
    bedroom_windows = {
        window["room_id"]
        for window in model["windows"]
        if window["room_id"] in {"H1-D", "H2-D", "G-D", "M-D"}
    }
    checks.append(
        (
            "P2-WINDOWS",
            not window_errors and bedroom_windows == {"H1-D", "H2-D", "G-D", "M-D"},
            "Every bedroom window lies on its room's exterior wall"
            if not window_errors
            else "Misassigned windows: " + ", ".join(window_errors),
        )
    )

    stair = by_id["ESC"]
    expected_columns = {(31.5, 7.4), (31.5, 11.0), (36.0, 7.4), (36.0, 11.0)}
    columns = {(item["x"], item["y"]) for item in model["structural_reservations"]}
    checks.extend(
        [
            (
                "P2-STAIR-ALIGNMENT",
                stair["x"] == 31.5 and stair["y"] == 7.4 and stair["w"] == 4.5 and stair["d"] == 3.6,
                "Protected stair remains aligned 1:1 with the PB core",
            ),
            (
                "P2-D048-COLUMNS",
                columns == expected_columns,
                "Four D-048 full-height column reservations remain at stair corners",
            ),
        ]
    )

    guest = by_id
    checks.append(
        (
            "P2-GUEST-PROGRAMME",
            16.9 <= guest["G-D"]["w"] * guest["G-D"]["d"] <= 18.0
            and 5.3 <= guest["G-B"]["w"] * guest["G-B"]["d"] <= 5.7
            and 3.5 <= guest["G-C"]["w"] * guest["G-C"]["d"] <= 4.0,
            "Guest bedroom, bathroom and wardrobe remain within coordinated programme bands",
        )
    )
    primary_bathroom_unified = model.get("primary_bathroom_unified")
    if primary_bathroom_unified:
        bathroom_ids = primary_bathroom_unified["space_ids"]
        unified_gross = sum(
            by_id[space_id]["w"] * by_id[space_id]["d"] for space_id in bathroom_ids
        )
        wet_opening = next(
            (door for door in model["doors"] if door["id"] == "D-M-WET"), None
        )
        unified_ok = (
            math.isclose(unified_gross, 17.60, abs_tol=tolerance)
            and math.isclose(
                float(primary_bathroom_unified["schematic_net_area_m2"]),
                15.66,
                abs_tol=tolerance,
            )
            and wet_opening is not None
            and wet_opening["kind"] == "opening"
            and math.isclose(float(wet_opening["width"]), 2.40, abs_tol=tolerance)
            and math.isclose(float(wet_opening["at"]), 5.00, abs_tol=tolerance)
            and len(primary_bathroom_unified["fixtures"]) == 5
        )
        checks.append(
            (
                "P2-PRIMARY-BATHROOM-UNIFIED",
                unified_ok,
                "The 17.60 m2 gross L-shaped primary bathroom is one 15.66 m2 schematic-net room with the full 2.40 m internal boundary open",
            )
        )
    primary_bedroom_unified = model.get("primary_bedroom_unified")
    if primary_bedroom_unified:
        bedroom_ids = primary_bedroom_unified["space_ids"]
        unified_bedroom_gross = sum(
            by_id[space_id]["w"] * by_id[space_id]["d"] for space_id in bedroom_ids
        )
        bedroom_names = {by_id[space_id]["name"] for space_id in bedroom_ids}
        bedroom_ok = (
            math.isclose(unified_bedroom_gross, 35.24, abs_tol=tolerance)
            and bedroom_names == {"Primary bedroom"}
            and primary_bedroom_unified["display_name"] == "Primary bedroom"
            and "privacy_screen" not in model.get("primary_suite_rebalance", {})
        )
        checks.append(
            (
                "P2-PRIMARY-BEDROOM-UNIFIED",
                bedroom_ok,
                "The 35.24 m2 combined primary bedroom reads as one room with one name and no fitted privacy screen",
            )
        )
    wellness_suite = model.get("wellness_suite")
    wellness_ids = wellness_suite["space_ids"] if wellness_suite else ["WELL"]
    wellness_gross = sum(
        by_id[space_id]["w"] * by_id[space_id]["d"] for space_id in wellness_ids
    )
    checks.append(
        (
            "P2-WELLNESS",
            16.0 <= wellness_gross <= 24.0
            and min(net_dimensions(by_id["WELL"], envelope, model)) >= 2.40 - tolerance,
            f"Wellness is {wellness_gross:.2f} m2 gross and fits a 2.40 m sauna",
        )
    )
    if wellness_suite:
        dry = by_id.get(wellness_suite["dry_threshold_space_id"])
        route_clear = float(wellness_suite["route_clear_m"])
        relaxation_ok = (
            bool(dry)
            and wellness_gross >= 22.0 - tolerance
            and min(net_dimensions(dry, envelope, model)) >= route_clear - tolerance
            and wellness_suite.get("wet_dry_separation") is True
        )
        checks.append(
            (
                "P2-WELLNESS-RELAXATION",
                relaxation_ok,
                (
                    f"The {wellness_gross:.2f} m2 L-shaped wellness includes a dry "
                    f"threshold, relaxation zone and {route_clear:.2f} m clear exterior route"
                ),
            )
        )

    laundry = model.get("relocated_laundry")
    if laundry:
        laundry_ok = (
            laundry.get("floor") == "PB"
            and laundry.get("container") == "BOD"
            and 31.7 - tolerance <= float(laundry["x"])
            and float(laundry["x"]) + float(laundry["w"]) <= 35.82 + tolerance
            and 2.4 - tolerance <= float(laundry["y"])
            and float(laundry["y"]) + float(laundry["d"]) <= 7.4 + tolerance
        )
        checks.append(
            (
                "PB-LAUNDRY-RESERVE",
                laundry_ok,
                "Laundry is reserved inside PB storage behind the Great Wall and below the primary wet band",
            )
        )

    egress = model.get("egress_reserve")
    if egress:
        access_space = by_id.get(egress.get("access_space"))
        start = float(egress["from"])
        width = float(egress["width"])
        egress_ok = (
            egress.get("edge") == "east"
            and access_space is not None
            and math.isclose(
                float(access_space["x"] + access_space["w"]), x_max, abs_tol=tolerance
            )
            and start >= float(access_space["y"]) - tolerance
            and start + width <= float(access_space["y"] + access_space["d"]) + tolerance
            and width >= 0.90 - tolerance
            and float(egress["retracted_clearance_above_grade_m"]) > 0.0
            and start >= 11.25 - tolerance
        )
        checks.append(
            (
                "P2-RETRACTABLE-STAIR-RESERVE",
                egress_ok,
                (
                    "Rear-facade retractable stair reserve is reached directly from the "
                    + (
                        "dry wellness threshold and clears the D-048 corner"
                        if model.get("wellness_suite")
                        else "short wellness/egress spur and clears the D-048 corner"
                    )
                    if model.get("central_distributor")
                    else "Rear-facade retractable stair reserve is reached directly from "
                    "the Phase 2 lobby and clears the D-048 corner"
                ),
            )
        )

    edge_intent = model.get("edge_truss_intent")
    if edge_intent:
        edge_ok = (
            math.isclose(float(edge_intent["x"]), 21.0, abs_tol=tolerance)
            and edge_intent.get("view_priority") == "primary"
            and edge_intent.get("expression") == "single large exposed industrial truss"
        )
        checks.append(
            (
                "P2-EDGE-TRUSS-BRIEF",
                edge_ok,
                (
                    "X=21 architectural brief requires one large exposed industrial truss while protecting the open family-balcony view"
                    if model.get("family_balcony")
                    else "X=21 architectural brief requires one large exposed industrial truss while protecting the mini-deck view"
                ),
            )
        )

    wall_schedule = model.get("wall_schedule")
    if wall_schedule:
        expected_thicknesses = {
            "P2-W01A": 0.09,
            "P2-W01B": 0.20,
            "P2-W02": 0.15,
            "P2-W02S": 0.20,
            "P2-W03": 0.20,
            "P2-W04R": 0.20,
            "P2-W05": 0.23,
            "P2-W06": 0.09,
        }
        schedule_ok = set(wall_schedule) == set(expected_thicknesses) and all(
            math.isclose(
                float(wall_schedule[wall_id]["nominal_total_m"]),
                expected,
                abs_tol=tolerance,
            )
            for wall_id, expected in expected_thicknesses.items()
        )
        checks.append(
            (
                "P2-WALL-SCHEDULE",
                schedule_ok,
                "D-080 differentiates wall thickness by duty: 90, 150, 200 and 230 mm coordination families",
            )
        )

    acoustic = model.get("acoustic_partition")
    if acoustic:
        layers = acoustic.get("room_side_to_room_side_layers", [])
        layer_sum_mm = sum(float(layer.get("nominal_mm", 0.0)) for layer in layers)
        reused = [layer for layer in layers if layer.get("material") == "reclaimed gypsum board"]
        new = [layer for layer in layers if layer.get("material") == "new gypsum board"]
        frames = [
            layer
            for layer in layers
            if layer.get("material") == "metal stud frame with glass-wool infill"
        ]
        acoustic_ok = (
            acoustic.get("id") == ("P2-W01B" if wall_schedule else "P2-W01")
            and math.isclose(
                float(acoustic.get("nominal_total_m", 0.0)),
                0.20 if wall_schedule else 0.25,
                abs_tol=tolerance,
            )
            and math.isclose(
                float(envelope["partition"]),
                0.09 if wall_schedule else 0.25,
                abs_tol=tolerance,
            )
            and math.isclose(layer_sum_mm, 198.0 if wall_schedule else 250.8, abs_tol=0.01)
            and len(reused) == 2
            and len(new) == 2
            and len(frames) == 2
            and all(math.isclose(float(frame.get("infill_nominal_mm", 0.0)), 50.0) for frame in frames)
            and len(acoustic.get("exclusions", [])) >= 4
        )
        checks.append(
            (
                "P2-W01B-200" if wall_schedule else "P2-W01-250",
                acoustic_ok,
                (
                    "D-080 P2-W01B is 200 mm nominal: two independent 64 mm insulated frames, a 20 mm clear gap and four outer board layers"
                    if wall_schedule
                    else "D-057 P2-W01 is 250 mm nominal: two independent insulated frames, two concealed reclaimed boards and two new finish boards"
                ),
            )
        )
        if wall_schedule:
            internal = model.get("internal_partition", {})
            internal_layers = internal.get("room_side_to_room_side_layers", [])
            internal_sum_mm = sum(float(layer.get("nominal_mm", 0.0)) for layer in internal_layers)
            internal_ok = (
                internal.get("id") == "P2-W01A"
                and math.isclose(float(internal.get("nominal_total_m", 0.0)), 0.09, abs_tol=tolerance)
                and math.isclose(internal_sum_mm, 89.0, abs_tol=0.01)
                and [layer.get("material") for layer in internal_layers]
                == [
                    "new gypsum board",
                    "metal stud frame with glass-wool infill",
                    "new gypsum board",
                ]
            )
            checks.append(
                (
                    "P2-W01A-090",
                    internal_ok,
                    "D-080 P2-W01A is a 90 mm nominal single-frame wall for low-risk dry boundaries within one suite",
                )
            )

    hall_edge = model.get("hall_edge_partition")
    if hall_edge:
        family_balcony = model.get("family_balcony")
        acoustic_glazing = {
            item["id"]
            for item in model.get("internal_glazing", [])
            if item.get("acoustic")
        }
        scheduled_openings = set(hall_edge.get("acoustic_openings", []))
        glazing_by_id = {item["id"]: item for item in model.get("internal_glazing", [])}
        openings_ok = scheduled_openings == acoustic_glazing and all(
            opening in glazing_by_id
            and glazing_by_id[opening].get("room_id") == "DECK"
            and glazing_by_id[opening].get("edge") == "west"
            and float(glazing_by_id[opening]["from"]) >= float(hall_edge["from_y"]) - tolerance
            and float(glazing_by_id[opening]["to"]) <= float(hall_edge["to_y"]) + tolerance
            for opening in scheduled_openings
        )
        hall_edge_nominal = 0.20 if wall_schedule else 0.25
        hall_edge_reference = "P2-W01B" if wall_schedule else "P2-W01"
        hall_edge_ok = (
            hall_edge.get("id") in {"P2-W04", "P2-W04R"}
            and math.isclose(float(hall_edge.get("axis_x", 0.0)), 21.0, abs_tol=tolerance)
            and math.isclose(float(hall_edge.get("from_y", -1.0)), 0.0, abs_tol=tolerance)
            and math.isclose(float(hall_edge.get("to_y", -1.0)), 18.0, abs_tol=tolerance)
            and math.isclose(float(hall_edge.get("nominal_total_m", 0.0)), hall_edge_nominal, abs_tol=tolerance)
            and math.isclose(float(envelope.get("hall_edge_wall", 0.0)), hall_edge_nominal, abs_tol=tolerance)
            and hall_edge.get("full_height") is True
            and hall_edge.get("opaque_assembly_reference") == hall_edge_reference
            and openings_ok
        )
        checks.append(
            (
                "P2-W04-HALL-EDGE",
                hall_edge_ok,
                (
                    "D-063 retains full-height P2-W04R only at the two bedroom edges and opens the 7.45 m family-balcony frontage"
                    if family_balcony
                    else "D-058 closes the full 18.00 m X=21 hall/workshop edge with 250 mm opaque construction; GLZ-DECK is the only scheduled acoustic opening"
                ),
            )
        )
        if family_balcony:
            open_from = float(family_balcony["from_y"])
            open_to = float(family_balcony["to_y"])
            balcony_ok = (
                math.isclose(float(family_balcony["axis_x"]), 21.0, abs_tol=tolerance)
                and math.isclose(open_from, 5.0, abs_tol=tolerance)
                and math.isclose(open_to, 12.45, abs_tol=tolerance)
                and math.isclose(open_to - open_from, 7.45, abs_tol=tolerance)
                and float(family_balcony["guard_height_m"]) >= 1.10 - tolerance
                and family_balcony.get("continuous_guard") is True
                and not model.get("internal_glazing")
            )
            checks.append(
                (
                    "P2-FAMILY-BALCONY",
                    balcony_ok,
                    "Mini deck, family distributor and study edge share a 7.45 m open hall frontage with a continuous 1.10 m minimum guard",
                )
            )

    exterior_wall = model.get("exterior_wall_assembly")
    if exterior_wall:
        exterior_layers = exterior_wall.get("outside_to_inside_layers", [])
        exterior_materials = [layer.get("material") for layer in exterior_layers]
        exterior_layer_sum_mm = sum(
            float(layer.get("nominal_mm", 0.0)) for layer in exterior_layers
        )
        exterior_frames = [
            layer for layer in exterior_layers if "metal stud frame" in layer.get("material", "")
        ]
        exterior_wall_ok = (
            exterior_wall.get("id") == "P2-W05"
            and set(exterior_wall.get("edges", [])) == {"south", "north", "east"}
            and math.isclose(
                float(exterior_wall.get("nominal_total_m", 0.0)),
                0.23 if wall_schedule else 0.30,
                abs_tol=tolerance,
            )
            and math.isclose(
                float(envelope["exterior_wall"]),
                0.23 if wall_schedule else 0.30,
                abs_tol=tolerance,
            )
            and math.isclose(
                exterior_layer_sum_mm, 229.0 if wall_schedule else 297.0, abs_tol=0.01
            )
            and len(exterior_frames) == (1 if wall_schedule else 2)
            and (
                "insulated corrugated metal facade panel" in exterior_materials
                if wall_schedule
                else "corrugated metal rainscreen" in exterior_materials
            )
            and exterior_materials[-2:] == ["reclaimed gypsum board", "new gypsum board"]
            and all(
                window.get("edge") in exterior_wall.get("edges", [])
                for window in model.get("windows", [])
            )
            and len(exterior_wall.get("coordination_gates", [])) >= 7
        )
        checks.append(
            (
                "P2-W05-230" if wall_schedule else "P2-W05-300",
                exterior_wall_ok,
                (
                    "D-080 P2-W05 integrates a 100 mm insulated corrugated facade panel with a 64 mm independent service lining in 230 mm nominal"
                    if wall_schedule
                    else "D-059 P2-W05 closes the three exterior P2 edges with a 300 mm nominal double-frame envelope, corrugated metal outside only and a smooth concealed-structure interior"
                ),
            )
        )

    results = [
        {"rule_id": rule_id, "status": "PASS" if passed else "FAIL", "message": message}
        for rule_id, passed, message in checks
    ]
    primary_rebalance = model.get("primary_suite_rebalance")
    primary_bath = sum(
        space["w"] * space["d"]
        for space in spaces
        if space.get("suite") == "M" and space["kind"] == "bath"
    )
    primary_closet = sum(
        space["w"] * space["d"]
        for space in spaces
        if space.get("suite") == "M" and space["kind"] == "closet"
    )
    primary_bedroom = sum(
        space["w"] * space["d"]
        for space in spaces
        if space.get("suite") == "M" and space["kind"] == "bedroom"
    )
    primary_ok = (
        primary_bath >= 17.0
        and primary_closet >= 13.0
        and primary_bedroom >= 35.0
        and (
            model.get("primary_bedroom_unified") is not None
            or primary_rebalance.get("privacy_screen") is not None
        )
        if primary_rebalance
        else primary_bath >= 17.0 and primary_closet >= 15.0
    )
    results.extend(
        [
            {
                "rule_id": "P2-PRIMARY-PROGRAMME",
                "status": "PASS" if primary_ok else "OPEN",
                "message": (
                    f"D-065 coordinates a {primary_bedroom:.2f} m2 primary bedroom, "
                    f"{primary_closet:.2f} m2 compact dressing and {primary_bath:.1f} m2 bathroom"
                    if primary_rebalance and primary_ok
                    else f"Primary bathroom {primary_bath:.1f} m2 and dressing room "
                    f"{primary_closet:.1f} m2 meet or exceed the original programme minimums"
                    if primary_ok
                    else f"Primary bathroom {primary_bath:.1f} m2 and dressing room "
                    f"{primary_closet:.1f} m2 remain below the original 17-18 and 15-16 m2 targets"
                ),
            },
            {
                "rule_id": "LIFE-EGRESS-2",
                "status": "OPEN",
                "message": (
                    "A rear retractable stair is reserved, but its acceptance as a second exit awaits D-021 and professional fire review"
                    if egress
                    else "Second independent P2 exit awaits D-021 occupancy and fire review"
                ),
            },
            {
                "rule_id": "P2-EDGE-TRUSS",
                "status": "OPEN",
                "message": (
                    (
                        "The large exposed X=21 truss must preserve the family-balcony opening; guard, members, joints and fire protection remain undesigned"
                        if model.get("family_balcony")
                        else "The large exposed X=21 truss must preserve the mini-deck view; members, joints, fire protection and services remain undesigned"
                    )
                    if edge_intent
                    else "The X=21 edge truss must preserve the mini-deck view, doors, ceiling and services"
                ),
            },
            {
                "rule_id": "P2-SITE-ORIENTATION",
                "status": "OPEN",
                "message": "Solar control, privacy and final glazing await the selected site and orientation",
            },
        ]
    )
    if central_distributor:
        results.append(
            {
                "rule_id": "P2-OPEN-STAIR-ARRIVAL-FIRE",
                "status": "OPEN",
                "message": (
                    "The stair-to-family-room arrival is an architectural objective only; "
                    "fire separation, smoke control and door strategy await professional design"
                ),
            }
        )
    if wellness_suite:
        results.append(
            {
                "rule_id": "P2-WELLNESS-EGRESS-ROUTE",
                "status": "OPEN",
                "message": (
                    "The reserved exterior route crosses the dry wellness threshold; "
                    "professional fire review must accept it or require a separated clear lane"
                ),
            }
        )
    if model.get("family_balcony"):
        results.append(
            {
                "rule_id": "P2-FAMILY-BALCONY-PERFORMANCE",
                "status": "OPEN",
                "message": (
                    "The open family balcony intentionally gives up D-058 acoustic continuity; "
                    "guarding, smoke transfer and hall-to-suite noise require professional design"
                ),
            }
        )
    if exterior_wall:
        results.append(
            {
                "rule_id": "P2-W05-BUILDING-PHYSICS",
                "status": "OPEN",
                "message": "P2-W05 hygrothermal, wind, fire and window interfaces await professional design",
            }
        )
    stair_core = model.get("stair_core")
    if stair_core:
        results.extend(validate_stair_core(stair_core))
        stair_door = next((door for door in model["doors"] if door["id"] == "D-STAIR"), None)
        upper = stair_core["stair"]["upper_flight"]
        access = stair_core["stair"]["p2_access_platform"]
        door_ok = bool(stair_door) and math.isclose(
            float(stair_door["at"]), float(access["door_y0"]), abs_tol=tolerance
        ) and float(stair_door["at"]) >= float(upper["y0"]) - tolerance and (
            float(stair_door["at"]) + float(stair_door["width"])
            <= float(upper["y1"]) + tolerance
        )
        results.append(
            {
                "rule_id": "P2-STAIR-ACCESS-FLIGHT",
                "status": "PASS" if door_ok else "FAIL",
                "message": "The P2 family-distributor door aligns with the upper-flight top platform.",
            }
        )
    return results


def _report(model: dict[str, Any]) -> dict[str, Any]:
    checks = validate_model(model)
    return {
        "revision": model["revision"],
        "passed": sum(item["status"] == "PASS" for item in checks),
        "open": sum(item["status"] == "OPEN" for item in checks),
        "failed": sum(item["status"] == "FAIL" for item in checks),
        "checks": checks,
    }


def _assert_renderable(report: dict[str, Any]) -> None:
    failures = [item for item in report["checks"] if item["status"] == "FAIL"]
    if failures:
        detail = "; ".join(f"{item['rule_id']}: {item['message']}" for item in failures)
        raise P2ModelError("P2 model failed closed: " + detail)


def _svg_start(title: str, description: str, metadata: dict[str, Any]) -> list[str]:
    payload = json.dumps(metadata, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
            'aria-labelledby="sheet-title sheet-description">'
        ),
        f'<title id="sheet-title">{_esc(title)}</title>',
        f'<desc id="sheet-description">{_esc(description)}</desc>',
        f"<metadata>{_esc(payload)}</metadata>",
        """<defs>
          <marker id="route-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#a63f31"/></marker>
          <marker id="up-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#76558f"/></marker>
          <style>
            text { font-family: Arial, Helvetica, sans-serif; }
            line, path, rect, circle, polygon, polyline { vector-effect: non-scaling-stroke; }
          </style>
        </defs>""",
        _rect(0, 0, WIDTH, HEIGHT, fill=PAPER),
    ]


def _header(parts: list[str], model: dict[str, Any], sheet: str, title: str, subtitle: str) -> None:
    parts.extend(
        [
            _rect(0, 0, WIDTH, 112, fill=INK),
            _rect(0, 112, WIDTH, 6, fill=TEAL),
            _text(52, 45, "DREAM HOUSE · BOYACA, COLOMBIA", 9, weight=700, fill="#9fc4cc"),
            _text(52, 80, title, 23, weight=700, fill="#ffffff"),
            _text(1040, 48, sheet, 15, anchor="end", weight=700, fill="#ffffff"),
            _text(1040, 76, subtitle, 8.5, anchor="end", fill="#c9d8dc"),
            _text(1618, 48, model["drawing_revision"], 17, anchor="end", weight=700, fill="#ffffff"),
            _text(1618, 75, model["revision"], 8.5, anchor="end", fill="#c9d8dc"),
        ]
    )


def _room_label(space: dict[str, Any], model: dict[str, Any]) -> str:
    primary_bathroom_unified = model.get("primary_bathroom_unified")
    primary_bedroom_unified = model.get("primary_bedroom_unified")
    if primary_bathroom_unified and space["id"] == "M-B":
        return ""
    if primary_bedroom_unified and space["id"] == "M-D":
        return ""
    x = _sx(space["x"] + space["w"] / 2.0)
    y = _sy(space["y"] + space["d"] / 2.0)
    pixel_width = space["w"] * SCALE
    pixel_height = space["d"] * SCALE
    size = min(9.0, max(5.2, pixel_width / 18.0))
    if pixel_height < 70:
        size = min(size, 6.4)
    label_width = max(8, int(pixel_width / max(1.0, size * 0.58)))
    primary_rebalance = model.get("primary_suite_rebalance")
    name_lines = textwrap.wrap(space["name"].replace(" / ", " "), width=label_width)
    if primary_bathroom_unified and space["id"] == "M-B-A":
        lines = [
            "Primary bathroom",
            f"{float(primary_bathroom_unified['schematic_net_area_m2']):.2f} m2 net schematic",
            f"{float(primary_bathroom_unified['gross_area_m2']):.2f} m2 gross unified",
        ]
    elif primary_bedroom_unified and space["id"] == "M-L":
        lines = [
            str(primary_bedroom_unified["display_name"]),
            f"{float(primary_bedroom_unified['gross_area_m2']):.2f} m2 gross",
        ]
    elif primary_rebalance and space["id"] in {"M-D", "M-L"}:
        lines = name_lines + [f"{float(primary_rebalance['bedroom_gross_area_m2']):.2f} m2 gross combined"]
    else:
        lines = name_lines + [f"{net_area(space, model['envelope'], model):.1f} m2 net"]
    if (
        pixel_height >= 90
        and pixel_width >= 80
        and not (primary_rebalance and space["id"] in {"M-D", "M-L"})
        and not (primary_bathroom_unified and space["id"] in {"M-B", "M-B-A"})
    ):
        lines.append(f"gross {space['w']:.2f} x {space['d']:.2f}")
    total = (len(lines) - 1) * size * 1.25
    return _multiline(
        x,
        y - total / 2.0,
        lines,
        size,
        leading=1.25,
        anchor="middle",
        weight=700,
    )


def _draw_rooms(parts: list[str], model: dict[str, Any]) -> None:
    for space in model["spaces"]:
        x = _sx(space["x"])
        y = _sy(space["y"] + space["d"])
        width = space["w"] * SCALE
        height = space["d"] * SCALE
        parts.append(
            _rect(
                x,
                y,
                width,
                height,
                fill=COLORS[space["kind"]],
                stroke="#4e6066",
                stroke_width=1.2,
                css_class=f"space space-{space['kind']}",
                data_space_id=space["id"],
            )
        )


def _draw_partition_walls(parts: list[str], model: dict[str, Any]) -> None:
    """Draw declared wall thicknesses over the gross-room tessellation."""

    if not model.get("acoustic_partition"):
        return
    spaces = model["spaces"]
    tolerance = float(model["tolerances"]["geometry_m"])
    for index, first in enumerate(spaces):
        for second in spaces[index + 1 :]:
            boundary = _shared_boundary(first, second, tolerance)
            if boundary is None:
                continue
            orientation, coordinate, low, high = boundary
            wall_id, thickness, color, dash = _boundary_wall_type(first, second, model)
            attrs = {
                "stroke": color,
                "stroke_width": thickness * SCALE,
                "stroke_dasharray": dash,
                "stroke_linecap": "butt",
                "css_class": f"partition-wall {wall_id.lower()}",
                "data_wall_type": wall_id,
            }
            if orientation == "vertical":
                parts.append(_line(_sx(coordinate), _sy(low), _sx(coordinate), _sy(high), **attrs))
            else:
                parts.append(_line(_sx(low), _sy(coordinate), _sx(high), _sy(coordinate), **attrs))


def _draw_hall_edge_wall(parts: list[str], model: dict[str, Any]) -> None:
    """Draw the coordinated X=21 enclosure and any controlled open balcony edge."""

    wall = model.get("hall_edge_partition")
    if not wall:
        return
    x = _sx(float(wall["axis_x"]))
    family_balcony = model.get("family_balcony")
    segments = (
        [
            (float(wall["from_y"]), float(family_balcony["from_y"])),
            (float(family_balcony["to_y"]), float(wall["to_y"])),
        ]
        if family_balcony
        else [(float(wall["from_y"]), float(wall["to_y"]))]
    )
    for low, high in segments:
        parts.append(
            _line(
                x,
                _sy(low),
                x,
                _sy(high),
                stroke=INK,
                stroke_width=float(wall["nominal_total_m"]) * SCALE,
                stroke_linecap="butt",
                css_class="hall-edge-wall p2-w04",
                data_wall_type=wall["id"],
            )
        )
    if family_balcony:
        parts.extend(
            [
                _line(
                    x,
                    _sy(float(family_balcony["from_y"])),
                    x,
                    _sy(float(family_balcony["to_y"])),
                    stroke=AMBER,
                    stroke_width=5,
                    stroke_dasharray="12 4",
                    stroke_linecap="butt",
                    css_class="family-balcony-guard",
                ),
                _text(
                    x + 10,
                    (_sy(float(family_balcony["from_y"])) + _sy(float(family_balcony["to_y"]))) / 2,
                    "OPEN FAMILY BALCONY · CONTINUOUS GUARD",
                    6.6,
                    weight=700,
                    fill=AMBER,
                ),
            ]
        )


def _draw_exterior_walls(parts: list[str], model: dict[str, Any]) -> None:
    """Draw the three coordinated P2 exterior edges before cutting openings."""

    wall = model.get("exterior_wall_assembly")
    if not wall:
        return
    width = float(wall["nominal_total_m"]) * SCALE
    common = {
        "stroke": "#36535d",
        "stroke_width": width,
        "stroke_linecap": "butt",
        "css_class": "exterior-wall p2-w05",
        "data_wall_type": wall["id"],
    }
    finish = {
        "stroke": "#dce8e5",
        "stroke_width": 2.4,
        "stroke_linecap": "butt",
        "css_class": (
            "p2-w05-refined-interior-reading"
            if model.get("wall_schedule")
            else "p2-w05-double-frame-reading"
        ),
    }
    edges = [
        (_sx(21.0), _sy(0.0), _sx(36.0), _sy(0.0)),
        (_sx(21.0), _sy(18.0), _sx(36.0), _sy(18.0)),
        (_sx(36.0), _sy(0.0), _sx(36.0), _sy(18.0)),
    ]
    for x1, y1, x2, y2 in edges:
        parts.append(_line(x1, y1, x2, y2, **common))
        parts.append(_line(x1, y1, x2, y2, **finish))


def _draw_room_labels(parts: list[str], model: dict[str, Any]) -> None:
    parts.extend(_room_label(space, model) for space in model["spaces"])


def _draw_bed(parts: list[str], room: dict[str, Any], *, x_ratio: float, y_ratio: float) -> None:
    width, depth = 2.05, 2.00
    x = room["x"] + x_ratio * max(0.0, room["w"] - width)
    y = room["y"] + y_ratio * max(0.0, room["d"] - depth)
    px, py = _sx(x), _sy(y + depth)
    parts.extend(
        [
            _rect(px, py, width * SCALE, depth * SCALE, fill="#f5f0e8", stroke="#708087", stroke_width=1, rx=6, css_class="furniture bed"),
            _rect(px + 5, py + 5, width * SCALE - 10, 15, fill="#ffffff", stroke="#a3acae", stroke_width=0.8, rx=4),
        ]
    )


def _draw_furniture(parts: list[str], model: dict[str, Any]) -> None:
    by_id = _space_index(model)
    _draw_bed(parts, by_id["H1-D"], x_ratio=0.16, y_ratio=0.15)
    _draw_bed(parts, by_id["H2-D"], x_ratio=0.12, y_ratio=0.62)
    _draw_bed(parts, by_id["G-D"], x_ratio=0.48, y_ratio=0.50)
    _draw_bed(parts, by_id["M-D"], x_ratio=0.58, y_ratio=0.18)

    primary_rebalance = model.get("primary_suite_rebalance")
    if primary_rebalance:
        for wardrobe in primary_rebalance["wardrobe_runs"]:
            parts.append(
                _rect(
                    _sx(float(wardrobe["x"])),
                    _sy(float(wardrobe["y"]) + float(wardrobe["d"])),
                    float(wardrobe["w"]) * SCALE,
                    float(wardrobe["d"]) * SCALE,
                    fill="#d7c5aa",
                    stroke="#705f4d",
                    stroke_width=1,
                    rx=2,
                    css_class="furniture primary-wardrobe-run",
                )
            )
        screen = primary_rebalance.get("privacy_screen")
        if screen:
            parts.extend(
                [
                    _rect(
                        _sx(float(screen["x"])),
                        _sy(float(screen["y"]) + float(screen["d"])),
                        float(screen["w"]) * SCALE,
                        float(screen["d"]) * SCALE,
                        fill="#b99d78",
                        stroke="#705f4d",
                        stroke_width=1,
                        rx=2,
                        css_class="furniture primary-privacy-screen",
                    ),
                    _text(
                        _sx(float(screen["x"]) + float(screen["w"]) / 2.0),
                        _sy(float(screen["y"]) + float(screen["d"]) / 2.0) + 2,
                        "PRIVACY SCREEN",
                        5.5,
                        anchor="middle",
                        weight=700,
                    ),
                ]
            )

    family = by_id["FAM"]
    parts.append(
        _rect(
            _sx(family["x"] + 0.35),
            _sy(family["y"] + 1.45),
            2.7 * SCALE,
            0.65 * SCALE,
            fill="#cbb89d",
            stroke="#766a5c",
            stroke_width=1,
            rx=5,
            css_class="furniture sofa",
        )
    )
    family_centre = model.get("family_centre")
    if family_centre:
        library = family_centre["fitted_library"]
        parts.extend(
            [
                _rect(
                    _sx(float(library["x"])),
                    _sy(float(library["y"]) + float(library["d"])),
                    float(library["w"]) * SCALE,
                    float(library["d"]) * SCALE,
                    fill="#b99d78",
                    stroke="#705f4d",
                    stroke_width=1,
                    rx=2,
                    css_class="furniture fitted-library",
                ),
                _text(
                    _sx(float(library["x"]) + float(library["w"]) / 2.0),
                    _sy(float(library["y"]) + float(library["d"]) / 2.0) + 2,
                    "FITTED LIBRARY WALL",
                    6.2,
                    anchor="middle",
                    weight=700,
                    fill="#ffffff",
                ),
            ]
        )
    central_distributor = model.get("central_distributor")
    if central_distributor:
        study = central_distributor["study_counter"]
        parts.extend(
            [
                _rect(
                    _sx(float(study["x"])),
                    _sy(float(study["y"]) + float(study["d"])),
                    float(study["w"]) * SCALE,
                    float(study["d"]) * SCALE,
                    fill="#d7c5aa",
                    stroke="#705f4d",
                    stroke_width=1,
                    rx=2,
                    css_class="furniture family-study-counter",
                ),
                _text(
                    _sx(float(study["x"]) + float(study["w"]) / 2.0),
                    _sy(float(study["y"]) + float(study["d"]) / 2.0) + 2,
                    "FAMILY STUDY EDGE",
                    6.2,
                    anchor="middle",
                    weight=700,
                ),
            ]
        )
    deck = by_id["DECK"]
    for offset in (0.45, 1.55):
        parts.append(
            _rect(
                _sx(deck["x"] + offset),
                _sy(
                    deck["y"] + deck["d"] - 0.30
                    if family_centre
                    else deck["y"] + 2.45
                ),
                0.70 * SCALE,
                0.70 * SCALE,
                fill="#d3b98c",
                stroke="#766a5c",
                stroke_width=1,
                rx=4,
                css_class="furniture chair",
            )
        )

    laundry = by_id.get("LAV")
    if laundry:
        for offset, label in ((0.35, "W"), (1.20, "D")):
            x = _sx(laundry["x"] + offset)
            y = _sy(laundry["y"] + laundry["d"] - 0.25)
            parts.append(_rect(x, y, 0.70 * SCALE, 0.70 * SCALE, fill="#f5f5f1", stroke="#708087", stroke_width=1, rx=3, css_class="furniture appliance"))
            parts.append(_text(x + 14, y + 18, label, 7, anchor="middle", weight=700))

    wellness = by_id["WELL"]
    sauna_x = _sx(wellness["x"] + 0.30)
    sauna_y = _sy(wellness["y"] + wellness["d"] - 0.30)
    parts.extend(
        [
            _rect(sauna_x, sauna_y, 2.40 * SCALE, 2.40 * SCALE, fill="#d7b184", stroke="#766a5c", stroke_width=1.1, rx=4, css_class="furniture sauna"),
            _text(sauna_x + 48, sauna_y + 52, "SAUNA", 7, anchor="middle", weight=700),
            _rect(_sx(33.25), _sy(14.05), 1.15 * SCALE, 1.15 * SCALE, fill="#d7edf0", stroke="#617078", stroke_width=1, rx=3, css_class="fixture shower"),
            _text(_sx(33.825), _sy(13.48), "SH", 6, anchor="middle", weight=700),
        ]
    )
    wellness_suite = model.get("wellness_suite")
    if wellness_suite:
        bench = wellness_suite["relaxation_bench"]
        parts.extend(
            [
                _rect(
                    _sx(float(bench["x"])),
                    _sy(float(bench["y"]) + float(bench["d"])),
                    float(bench["w"]) * SCALE,
                    float(bench["d"]) * SCALE,
                    fill="#cbb89d",
                    stroke="#766a5c",
                    stroke_width=1,
                    rx=5,
                    css_class="furniture wellness-recline-bench",
                ),
                _text(
                    _sx(float(bench["x"]) + float(bench["w"]) / 2.0),
                    _sy(float(bench["y"]) + float(bench["d"]) / 2.0) + 2,
                    "COOL / RECLINE",
                    6.2,
                    anchor="middle",
                    weight=700,
                ),
            ]
        )


def _draw_bath_fixtures(parts: list[str], model: dict[str, Any]) -> None:
    by_id = _space_index(model)
    primary_bathroom_unified = model.get("primary_bathroom_unified")
    room_ids = [
        room_id
        for room_id in ("H1-B", "H2-B", "G-B", "M-B", "M-B-A")
        if room_id in by_id
        and not (primary_bathroom_unified and room_id in {"M-B", "M-B-A"})
    ]
    for room_id in room_ids:
        room = by_id[room_id]
        clear_x = room["x"] + 0.16
        clear_y = room["y"] + 0.16
        shower = 1.25 if room_id in {"M-B", "M-B-A"} else 1.0
        parts.append(
            _rect(
                _sx(clear_x),
                _sy(clear_y + shower),
                shower * SCALE,
                shower * SCALE,
                fill="#d7edf0",
                stroke="#617078",
                stroke_width=0.9,
                rx=3,
                css_class="fixture shower",
            )
        )
        vanity_w = min(1.6 if room_id in {"M-B", "M-B-A"} else 0.95, room["w"] - 0.35)
        parts.append(
            _rect(
                _sx(clear_x),
                _sy(room["y"] + room["d"] - 0.18),
                vanity_w * SCALE,
                0.42 * SCALE,
                fill="#eee2cf",
                stroke="#617078",
                stroke_width=0.9,
                rx=3,
                css_class="fixture vanity",
            )
        )
        wc_x = room["x"] + room["w"] - 0.78
        wc_y = room["y"] + room["d"] - 0.95
        parts.append(
            _rect(
                _sx(wc_x),
                _sy(wc_y + 0.72),
                0.58 * SCALE,
                0.72 * SCALE,
                fill="#fbfaf6",
                stroke="#617078",
                stroke_width=0.9,
                rx=5,
                css_class="fixture wc",
            )
        )

    if primary_bathroom_unified:
        colors = {
            "shower": "#d7edf0",
            "tub": "#f5f5f1",
            "vanity": "#e6d5b9",
            "wc": "#ffffff",
            "linen": "#d7c5aa",
        }
        for fixture in primary_bathroom_unified["fixtures"]:
            parts.extend(
                [
                    _rect(
                        _sx(float(fixture["x"])),
                        _sy(float(fixture["y"]) + float(fixture["d"])),
                        float(fixture["w"]) * SCALE,
                        float(fixture["d"]) * SCALE,
                        fill=colors[fixture["type"]],
                        stroke="#617078",
                        stroke_width=0.9,
                        rx=4,
                        css_class=f"fixture primary-{fixture['type']}",
                    ),
                    _text(
                        _sx(float(fixture["x"]) + float(fixture["w"]) / 2.0),
                        _sy(float(fixture["y"]) + float(fixture["d"]) / 2.0) + 2,
                        fixture["label"],
                        5.8,
                        anchor="middle",
                        weight=700,
                    ),
                ]
            )
        screen = primary_bathroom_unified["wc_privacy_screen"]
        parts.append(
            _line(
                _sx(float(screen["x"])),
                _sy(float(screen["y"])),
                _sx(float(screen["x"])),
                _sy(float(screen["y"]) + float(screen["length"])),
                stroke="#705f4d",
                stroke_width=3,
                css_class="primary-bathroom-wc-screen",
            )
        )


def _draw_stair(parts: list[str], model: dict[str, Any] | None = None) -> None:
    stair_core = model.get("stair_core") if model else None
    if stair_core:
        stair = stair_core["stair"]
        lower = stair["lower_flight"]
        upper = stair["upper_flight"]
        landing = stair["intermediate_landing"]
        parts.append(
            f'<g class="canonical-stair-core" data-stair-model-revision="{_esc(stair_core["revision"])}">'
        )
        parts.extend(
            [
                _rect(
                    _sx(float(lower["x0"])),
                    _sy(float(lower["y1"])),
                    (float(lower["x1"]) - float(lower["x0"])) * SCALE,
                    (float(lower["y1"]) - float(lower["y0"])) * SCALE,
                    fill="#f6f2eb",
                    stroke=PURPLE,
                    stroke_width=1.0,
                    stroke_dasharray="5 3",
                    css_class="stair-flight lower-flight below",
                ),
                _rect(
                    _sx(float(upper["x0"])),
                    _sy(float(upper["y1"])),
                    (float(upper["x1"]) - float(upper["x0"])) * SCALE,
                    (float(upper["y1"]) - float(upper["y0"])) * SCALE,
                    fill="#ebe7e1",
                    stroke=MUTED,
                    stroke_width=1.0,
                    css_class="stair-flight upper-flight",
                ),
                _rect(
                    _sx(float(landing["x0"])),
                    _sy(float(landing["y1"])),
                    (float(landing["x1"]) - float(landing["x0"])) * SCALE,
                    (float(landing["y1"]) - float(landing["y0"])) * SCALE,
                    fill="#e3ddd3",
                    stroke=MUTED,
                    stroke_width=1.0,
                    css_class="stair-landing intermediate-landing",
                ),
            ]
        )
        for flight, css_class in ((lower, "lower-tread"), (upper, "upper-tread")):
            for index in range(1, int(stair["treads_per_flight"][0]) + 1):
                x = float(flight["x0"]) + index * float(stair["going"])
                parts.append(
                    _line(
                        _sx(x), _sy(float(flight["y0"])),
                        _sx(x), _sy(float(flight["y1"])),
                        stroke="#7a868a", stroke_width=0.7,
                        css_class=f"stair-tread {css_class}",
                    )
                )
        upper_mid_y = (float(upper["y0"]) + float(upper["y1"])) / 2.0
        lower_mid_y = (float(lower["y0"]) + float(lower["y1"])) / 2.0
        parts.extend(
            [
                _line(
                    _sx(float(upper["x0"]) + 0.25), _sy(upper_mid_y),
                    _sx(float(upper["x1"]) - 0.20), _sy(upper_mid_y),
                    stroke=PURPLE, stroke_width=1.8, marker_end="url(#up-arrow)",
                    css_class="stair-direction p2-down-direction",
                ),
                _text(_sx(33.05), _sy(upper_mid_y) - 8, "DN TO PB", 6.5, anchor="middle", weight=700, fill=PURPLE),
                _line(
                    _sx(float(lower["x1"]) - 0.25), _sy(lower_mid_y),
                    _sx(float(lower["x0"]) + 0.20), _sy(lower_mid_y),
                    stroke=PURPLE, stroke_width=1.1, stroke_dasharray="4 3",
                    css_class="stair-direction lower-flight-below",
                ),
                _text(_sx(33.05), _sy(lower_mid_y) - 8, "LOWER FLIGHT BELOW", 5.3, anchor="middle", weight=700, fill=MUTED),
                _text(_sx(35.1), _sy(9.2), "LANDING +1.90", 5.2, anchor="middle", weight=700, fill=MUTED),
            ]
        )
        parts.append("</g>")
        return

    x0, x1 = _sx(31.82), _sx(35.68)
    lower_top, lower_bottom = _sy(9.12), _sy(7.72)
    upper_top, upper_bottom = _sy(10.68), _sy(9.28)
    parts.extend(
        [
            _rect(x0, lower_top, x1 - x0, lower_bottom - lower_top, fill="#ebe7e1", stroke=MUTED, stroke_width=1, css_class="stair-flight"),
            _rect(x0, upper_top, x1 - x0, upper_bottom - upper_top, fill="#ebe7e1", stroke=MUTED, stroke_width=1, css_class="stair-flight"),
        ]
    )
    for index in range(11):
        x = x0 + index * (x1 - x0) / 10.0
        parts.append(_line(x, lower_top, x, lower_bottom, stroke="#7a868a", stroke_width=0.7, css_class="stair-tread"))
    for index in range(10):
        x = x0 + index * (x1 - x0) / 9.0
        parts.append(_line(x, upper_top, x, upper_bottom, stroke="#7a868a", stroke_width=0.7, css_class="stair-tread"))
    mid_y = (lower_top + lower_bottom) / 2.0
    parts.extend(
        [
            _line(x0 + 12, mid_y, x1 - 12, mid_y, stroke=PURPLE, stroke_width=1.8, marker_end="url(#up-arrow)"),
            _text((x0 + x1) / 2.0, mid_y - 7, "UP FROM PB", 6.5, anchor="middle", weight=700, fill=PURPLE),
        ]
    )


def _draw_door(parts: list[str], door: dict[str, Any], model: dict[str, Any] | None = None) -> None:
    width_px = float(door["width"]) * SCALE
    opening_stroke = 5.5
    if model and model.get("acoustic_partition"):
        if model.get("wall_schedule"):
            opening_stroke = max(
                float(model["wall_schedule"][wall_id]["nominal_total_m"])
                for wall_id in ("P2-W01A", "P2-W01B", "P2-W02", "P2-W02S", "P2-W03")
            ) * SCALE + 2.0
        else:
            opening_stroke = max(
                float(model["envelope"]["partition"]),
                float(model["envelope"]["wet_wall"]),
            ) * SCALE + 2.0
    common = {"stroke": "#965039", "stroke_width": 1.3, "fill": "none", "css_class": "door"}
    if door["wall"] == "horizontal":
        x0 = _sx(float(door["at"]))
        y = _sy(float(door["y"]))
        x1 = x0 + width_px
        parts.append(_line(x0 - 1, y, x1 + 1, y, stroke=PAPER, stroke_width=opening_stroke, css_class="door-opening"))
        if door["kind"] == "opening":
            parts.append(_line(x0, y, x1, y, stroke=TEAL, stroke_width=2.0, css_class="open-passage"))
            return
        direction = -1.0 if door["swing"] == "north" else 1.0
        open_y = y + direction * width_px
        sweep = 0 if direction < 0 else 1
        parts.append(_line(x0, y, x0, open_y, **common))
        parts.append(
            f'<path d="M {x1} {y} A {width_px} {width_px} 0 0 {sweep} {x0} {open_y}" {_attrs(**common)}/>'
        )
    else:
        x = _sx(float(door["x"]))
        y0 = _sy(float(door["at"]))
        y1 = _sy(float(door["at"] + door["width"]))
        parts.append(_line(x, y0 + 1, x, y1 - 1, stroke=PAPER, stroke_width=opening_stroke, css_class="door-opening"))
        direction = 1.0 if door["swing"] == "east" else -1.0
        open_x = x + direction * width_px
        sweep = 1 if direction > 0 else 0
        parts.append(_line(x, y0, open_x, y0, **common))
        parts.append(
            f'<path d="M {x} {y1} A {width_px} {width_px} 0 0 {sweep} {open_x} {y0}" {_attrs(**common)}/>'
        )


def _draw_windows(parts: list[str], model: dict[str, Any]) -> None:
    exterior_wall = model.get("exterior_wall_assembly")
    opening_width = (
        float(exterior_wall["nominal_total_m"]) * SCALE + 2 if exterior_wall else 0.0
    )
    for window in model["windows"]:
        if window["edge"] in {"south", "north"}:
            y = _sy(0.0 if window["edge"] == "south" else 18.0)
            x0, x1 = _sx(window["from"]), _sx(window["to"])
            if exterior_wall:
                parts.append(
                    _line(
                        x0,
                        y,
                        x1,
                        y,
                        stroke=PAPER,
                        stroke_width=opening_width,
                        stroke_linecap="butt",
                        css_class="p2-w05-window-opening",
                        data_opening_id=window["id"],
                    )
                )
            parts.append(_line(x0, y, x1, y, stroke=TEAL, stroke_width=8, css_class="exterior-window"))
            parts.append(_line(x0, y, x1, y, stroke="#d9f2f5", stroke_width=2, css_class="window-glass"))
        else:
            x = _sx(36.0)
            y0, y1 = _sy(window["from"]), _sy(window["to"])
            if exterior_wall:
                parts.append(
                    _line(
                        x,
                        y0,
                        x,
                        y1,
                        stroke=PAPER,
                        stroke_width=opening_width,
                        stroke_linecap="butt",
                        css_class="p2-w05-window-opening",
                        data_opening_id=window["id"],
                    )
                )
            parts.append(_line(x, y0, x, y1, stroke=TEAL, stroke_width=8, css_class="exterior-window"))
            parts.append(_line(x, y0, x, y1, stroke="#d9f2f5", stroke_width=2, css_class="window-glass"))
    for glazing in model["internal_glazing"]:
        wall = model.get("hall_edge_partition")
        x = _sx(float(wall["axis_x"]) if wall else 21.0)
        y0, y1 = _sy(glazing["from"]), _sy(glazing["to"])
        if wall and glazing["id"] in wall.get("acoustic_openings", []):
            parts.append(
                _line(
                    x,
                    y0,
                    x,
                    y1,
                    stroke=PAPER,
                    stroke_width=float(wall["nominal_total_m"]) * SCALE + 2,
                    stroke_linecap="butt",
                    css_class="hall-edge-acoustic-opening",
                    data_opening_id=glazing["id"],
                )
            )
        parts.append(_line(x, y0, x, y1, stroke=AMBER, stroke_width=7, css_class="internal-acoustic-glazing"))
        parts.append(_line(x, y0, x, y1, stroke="#fff1d9", stroke_width=2, css_class="window-glass"))


def _draw_egress_reserve(parts: list[str], model: dict[str, Any]) -> None:
    reserve = model.get("egress_reserve")
    if not reserve:
        return
    x = _sx(36.0)
    y0 = _sy(float(reserve["from"]) + float(reserve["width"]))
    y1 = _sy(float(reserve["from"]))
    parts.extend(
        [
            _line(
                x,
                y0,
                x,
                y1,
                stroke=PAPER,
                stroke_width=(
                    float(model["exterior_wall_assembly"]["nominal_total_m"]) * SCALE + 2
                    if model.get("exterior_wall_assembly")
                    else 7
                ),
                stroke_linecap=("butt" if model.get("exterior_wall_assembly") else None),
                css_class="egress-door-opening",
            ),
            _line(x, y0, x, y1, stroke=RED, stroke_width=3, css_class="egress-door"),
            _rect(
                x + 8,
                y0 - 4,
                58,
                y1 - y0 + 8,
                fill="none",
                stroke=RED,
                stroke_width=1.6,
                stroke_dasharray="7 4",
                css_class="retractable-stair-reserve",
            ),
            _text(x + 37, (y0 + y1) / 2 - 1, "RETRACTABLE", 5.6, anchor="middle", weight=700, fill=RED),
            _text(x + 37, (y0 + y1) / 2 + 9, "EXT. STAIR", 5.6, anchor="middle", weight=700, fill=RED),
        ]
    )


def _draw_columns(parts: list[str], model: dict[str, Any]) -> None:
    for column in model["structural_reservations"]:
        x, y = _sx(column["x"]), _sy(column["y"])
        parts.append(
            _rect(
                x - 6,
                y - 6,
                12,
                12,
                fill="#ffffff",
                stroke=PURPLE,
                stroke_width=2.2,
                css_class="d048-column-reservation",
                data_column_id=column["id"],
            )
        )


def _draw_plan_dimensions(parts: list[str], model: dict[str, Any]) -> None:
    left, right = _sx(21.0), _sx(36.0)
    top, bottom = _sy(18.0), _sy(0.0)
    dim_y = bottom + 48
    parts.extend(
        [
            _line(left, dim_y, right, dim_y, stroke=MUTED, stroke_width=1),
            _line(left, dim_y - 7, left, dim_y + 7, stroke=MUTED, stroke_width=1),
            _line(right, dim_y - 7, right, dim_y + 7, stroke=MUTED, stroke_width=1),
            _text((left + right) / 2, dim_y - 8, "15.00 m · X=21.00 to 36.00", 8, anchor="middle", weight=700),
            _line(left - 38, top, left - 38, bottom, stroke=MUTED, stroke_width=1),
            _line(left - 45, top, left - 31, top, stroke=MUTED, stroke_width=1),
            _line(left - 45, bottom, left - 31, bottom, stroke=MUTED, stroke_width=1),
            _text(left - 49, (top + bottom) / 2, "18.00 m", 8, anchor="middle", weight=700),
            _text(
                left,
                top - 18,
                "LATERAL B / P2-W05"
                if model.get("exterior_wall_assembly")
                else "LATERAL B / HIGH EAVE STUDY",
                7.5,
                weight=700,
                fill=MUTED,
            ),
            _text(
                left,
                bottom + 22,
                "LATERAL A / P2-W05"
                if model.get("exterior_wall_assembly")
                else "LATERAL A / LOW EAVE STUDY",
                7.5,
                weight=700,
                fill=MUTED,
            ),
            _text(
                left - 2,
                (top + bottom) / 2 - 6,
                "P2-W04 / DOUBLE-HEIGHT HALL"
                if model.get("hall_edge_partition")
                else "P2 EDGE / DOUBLE-HEIGHT VOID",
                7,
                anchor="middle",
                weight=700,
                fill=AMBER,
            ),
            _text(
                right + 12,
                (top + bottom) / 2,
                "REAR FACADE / P2-W05"
                if model.get("exterior_wall_assembly")
                else "REAR FACADE",
                7,
                anchor="middle",
                weight=700,
                fill=MUTED,
            ),
        ]
    )


def _panel_title(
    parts: list[str],
    x: float,
    y: float,
    number: str,
    title: str,
    *,
    width: float = 780,
) -> None:
    parts.extend(
        [
            _text(x, y, number, 9, weight=700, fill=TEAL),
            _text(x + 34, y, title, 12, weight=700),
            _line(x, y + 11, x + width, y + 11, stroke="#c3ccce", stroke_width=1),
        ]
    )


def _right_notes(parts: list[str], model: dict[str, Any], report: dict[str, Any]) -> None:
    x = 785.0
    _panel_title(parts, x, 166, "01", "ARCHITECTURAL POSITION")
    owner_priority_revision = bool(model.get("relocated_laundry"))
    acoustic = model.get("acoustic_partition")
    hall_edge = model.get("hall_edge_partition")
    exterior_wall = model.get("exterior_wall_assembly")
    family_centre = model.get("family_centre")
    central_distributor = model.get("central_distributor")
    wellness_suite = model.get("wellness_suite")
    family_balcony = model.get("family_balcony")
    primary_rebalance = model.get("primary_suite_rebalance")
    primary_bathroom_unified = model.get("primary_bathroom_unified")
    primary_bedroom_unified = model.get("primary_bedroom_unified")
    stair_core = model.get("stair_core")
    position_lines = (
        [
            "Use P2-W01A 90 mm only within the same dry suite.",
            "Use P2-W01B / W04R 200 mm at private and hall separations.",
            "Reserve 150 / 200 mm for wet, sauna and protected-core walls.",
            "Integrate P2-W05 230 mm with the industrial insulated shell.",
            "Keep fire, acoustic, wind and hygrothermal ratings open to design.",
        ]
        if model.get("wall_schedule")
        else
        [
            "Use one shared SC-01 stair geometry in PB and P2.",
            "Coordinate 22 equal risers and two 1.40 m straight flights.",
            "Move the P2 door to the upper-flight top platform.",
            "Keep the same four foundation-to-roof column coordinates.",
            "Retain CF-011 until rear grade discharge is solved in section.",
        ]
        if stair_core
        else (
            [
                (
                    "Read the 35.24 m2 primary bedroom as one room without a privacy screen."
                    if primary_bedroom_unified
                    else "Unify the 17.60 m2 primary bathroom as one open L-shaped room."
                    if primary_bathroom_unified
                    else "Move the compact dressing beside the Child 1 service band."
                    if primary_rebalance
                    else "Open 7.45 m of the family edge as one internal hall balcony."
                    if family_balcony
                    else "Absorb the rear spur into a 22.62 m2 dry/wet wellness suite."
                    if wellness_suite
                    else "Open the stair into one 10.50 x 3.60 m family distributor."
                    if central_distributor
                    else "Consolidate the shared centre as one 7.60 x 3.60 m family room."
                    if family_centre
                    else "Prioritize the primary suite without enlarging P2."
                ),
                "Move laundry into PB storage behind the Great Wall.",
                "Keep the large exposed X=21 truss on the hall side of P2-W04.",
                (
                    "P2-W04R closes bedroom ends; the shared family frontage stays open."
                    if family_balcony
                    else "P2-W01 / W04 close the interior and hall-facing boundaries."
                ),
                "P2-W05 gives all exterior P2 rooms a refined double-frame envelope.",
            ]
            if exterior_wall
            else [
                "Prioritize the primary suite without enlarging P2.",
                "Move laundry into PB storage behind the Great Wall.",
                "Protect the view while allowing one large exposed industrial truss.",
                *(
                    ["Coordinate dry P2 partitions at 250 mm nominal under D-057."]
                    if acoustic
                    else []
                ),
                *(
                    ["Open the family frontage; retain P2-W04R only at bedroom ends."]
                    if family_balcony
                    else ["Close the full X=21 hall/workshop edge under D-058."]
                    if hall_edge
                    else []
                ),
            ]
        )
        if owner_priority_revision
        else [
            "Carry forward the spatial centre of b04/R03.",
            "Retain the verified dimensional corrections of b06/R05.",
            "The previous R05 remains superseded, not erased.",
        ]
    )
    parts.append(
        _multiline(
            x,
            198,
            position_lines,
            9.2,
            leading=1.55,
        )
    )
    parts.append(_rect(x, 268, 780, 66, fill="#e3efe8", stroke="#78a18c", stroke_width=1.1, rx=5))
    parts.append(_text(x + 18, 292, "MODEL RESULT", 7.5, weight=700, fill=GREEN))
    parts.append(
        _text(
            x + 18,
            318,
            f"{report['passed']} PASS · {report['failed']} FAIL · {report['open']} OPEN",
            15,
            weight=700,
            fill=GREEN if report["failed"] == 0 else RED,
        )
    )

    by_id = _space_index(model)
    envelope = model["envelope"]
    _panel_title(parts, x, 376, "02", "WHAT THIS REVISION FIXES")
    child_delta = abs(
        net_area(by_id["H1-D"], envelope, model)
        - net_area(by_id["H2-D"], envelope, model)
    )
    fixes = (
        [
            ("STAIR", "One dogleg model replaces the contradictory PB/P2 stair symbols."),
            ("MATH", "22R @ 172.7 mm + 20G @ 270 mm; 2R+G = 615.5 mm."),
            ("WIDTH", "Flights and intermediate landing are each 1.40 m clear."),
            ("PB / P2", "PB reads UP on ST-F1; P2 reads DN from ST-F2."),
            ("COLUMNS", "Four SC-01/D-048 column IDs retain identical coordinates."),
            ("CF-011", "Rear grade discharge remains open; the landing there is +1.90 m."),
        ]
        if stair_core
        else [
            (
                "PRIMARY",
                (
                    "One 35.24 m2 primary bedroom; duplicate zone labels and privacy screen removed."
                    if primary_bedroom_unified
                    else "Unified bathroom 17.60 m2 gross / 15.66 m2 schematic net; no intermediate door."
                    if primary_bathroom_unified
                    else "Bedroom 35.24 m2 + compact dressing 13.44 m2 + bathroom 17.60 m2."
                    if primary_rebalance
                    else "Bathroom 17.6 m2 + dressing/filter 17.6 m2 meet the brief."
                ),
            ),
            (
                "FAMILY" if family_centre else "LAUNDRY",
                (
                    "One 27.4 m2 family room replaces lounge, gallery and private-hall fragments."
                    if family_centre and not central_distributor
                    else "The residual 6.53 m2 spur becomes the dry wellness threshold."
                    if wellness_suite
                    else "The 15 m double corridor becomes an open study edge + 4.5 m spur."
                    if central_distributor
                    else "Washer, dryer and sink move to PB storage behind the Great Wall."
                ),
            ),
            (
                "BALCONY" if family_balcony else "WELLNESS" if wellness_suite else "EGRESS",
                (
                    "Mini deck + family centre share one 7.45 m open guarded hall edge."
                    if family_balcony
                    else "22.62 m2 combines dry threshold, cooling/recline, sauna and shower."
                    if wellness_suite
                    else "A theft-resistant retractable exterior-stair envelope is reserved."
                ),
            ),
            ("VIEW", "Mini-deck sightline governs the single large X=21 truss."),
            ("STRUCTURE", "Four D-048 column reservations remain at stair corners."),
            *(
                [
                    (
                        "ACOUSTIC" if hall_edge else "P2-W01",
                        (
                            "W01A 90 / W01B-W04R 200 / wet 150-200 / W05 230 mm."
                            if model.get("wall_schedule")
                            else "W01/W04R: 250 mm at enclosed zones; family balcony edge open."
                            if family_balcony
                            else "W01/W04: 250 mm acoustic; W05: 300 mm exterior, smooth inside."
                            if exterior_wall
                            else "P2-W01 + continuous P2-W04: 250 mm opaque wall; only deck glazing interrupts."
                            if hall_edge
                            else "250 mm nominal dry wall: twin insulated frames + reused concealed board."
                        ),
                    )
                ]
                if acoustic
                else []
            ),
        ]
        if owner_priority_revision
        else [
            ("ACCESS", f"{len(model['doors'])} doors/openings are checked against shared walls."),
            ("CENTRE", "Mini deck -> family lounge -> gallery -> protected arrival."),
            ("CHILDREN", f"Net-bedroom difference {child_delta:.2f} m2 under D-042."),
            ("PHASING", "One 1.25 m clear isolatable Phase 2 lobby."),
            ("STRUCTURE", "Four D-048 column reservations retained at stair corners."),
        ]
    )
    for index, (tag, note) in enumerate(fixes):
        y = 410 + index * 44
        parts.append(_rect(x, y - 16, 84, 25, fill="#deedf0", stroke="none", rx=12))
        parts.append(_text(x + 42, y + 1, tag, 6.7, anchor="middle", weight=700, fill=TEAL))
        parts.append(_text(x + 100, y, note, 8.4))

    _panel_title(parts, x, 657, "03", "PROGRAMME SNAPSHOT · GROSS AREAS")
    rows = [
        ("Child suite 1", sum(s["w"] * s["d"] for s in model["spaces"] if s.get("suite") == "H1")),
        ("Child suite 2", sum(s["w"] * s["d"] for s in model["spaces"] if s.get("suite") == "H2")),
        ("Guest suite", sum(s["w"] * s["d"] for s in model["spaces"] if s.get("suite") == "G")),
        ("Primary private rooms", sum(s["w"] * s["d"] for s in model["spaces"] if s.get("suite") == "M")),
        ("Mini deck", by_id["DECK"]["w"] * by_id["DECK"]["d"]),
        (
            "Family room" if family_centre else "Wellness",
            (
                sum(
                    by_id[space_id]["w"] * by_id[space_id]["d"]
                    for space_id in (
                        central_distributor["main_space_id"],
                        central_distributor["extension_space_id"],
                    )
                )
                if central_distributor
                else by_id[family_centre["space_id"]]["w"]
                * by_id[family_centre["space_id"]]["d"]
                if family_centre
                else by_id["WELL"]["w"] * by_id["WELL"]["d"]
            ),
        ),
    ]
    for index, (label, area) in enumerate(rows):
        y = 692 + index * 30
        parts.append(_text(x, y, label, 8.3))
        parts.append(_text(x + 360, y, f"{area:.1f} m2", 8.3, anchor="end", weight=700))
        parts.append(_line(x + 380, y - 4, x + 520, y - 4, stroke="#d0d6d7", stroke_width=1))

    _panel_title(parts, x, 895, "04", "OPEN DESIGN GATES")
    open_items = [item for item in report["checks"] if item["status"] == "OPEN"]
    visible_open_items = open_items[:4]
    for index, item in enumerate(visible_open_items):
        y = 928 + index * 27
        parts.append(_circle_status(x + 7, y - 3, RED))
        parts.append(_text(x + 24, y, item["message"], 7.5))
    if len(open_items) > len(visible_open_items):
        parts.append(
            _text(
                x + 24,
                1041,
                f"+ {len(open_items) - len(visible_open_items)} additional open gates in compliance.json",
                7.5,
                weight=700,
                fill=RED,
            )
        )

    parts.extend(
        [
            _line(1320, 657, 1320, 858, stroke="#c3ccce", stroke_width=1),
            _text(1350, 684, "LEGEND", 9, weight=700),
            _line(1350, 712, 1402, 712, stroke=TEAL, stroke_width=7),
            _text(1415, 715, "exterior glazing", 7.5),
            _line(1350, 740, 1402, 740, stroke=AMBER, stroke_width=7),
            _text(
                1415,
                743,
                "open balcony guard" if family_balcony else "acoustic deck glazing",
                7.5,
            ),
            _rect(1350, 758, 12, 12, fill="#fff", stroke=PURPLE, stroke_width=2),
            _text(1374, 769, "D-048 column reserve", 7.5),
            *(
                []
                if model.get("hide_phase_boundary_on_plan")
                else [
                    _line(1350, 793, 1402, 793, stroke=PURPLE, stroke_width=3, stroke_dasharray="8 5"),
                    _text(1415, 796, "F1 / F2 boundary", 7.5),
                ]
            ),
            *(
                [
                    _line(1350, 820, 1402, 820, stroke=INK, stroke_width=8.3),
                    _text(
                        1415,
                        823,
                        (
                            "W01A 90 · W01B/W04R 200 · W05 230 mm"
                            if model.get("wall_schedule")
                            else "P2-W01/W04R · 250 · W05 · 300 mm"
                            if family_balcony and exterior_wall
                            else "P2-W01/W04 · 250 · W05 · 300 mm"
                            if exterior_wall
                            else "P2-W01 / W04 · 250 mm nominal"
                            if hall_edge
                            else "P2-W01 · 250 mm nominal"
                        ),
                        7.5,
                    ),
                    _text(
                        1350,
                        848,
                        (
                            "Wet / sauna / protected-core reserves: 150 / 200 / 200 mm."
                            if model.get("wall_schedule")
                            else "W04R closes bedrooms; family edge is open and guarded."
                            if family_balcony
                            else "W05: corrugated outside only; smooth concealed interior."
                            if exterior_wall
                            else "W04 is full-height; GLZ-DECK is its only planned opening."
                            if hall_edge
                            else "Wet/hot, exterior, stair and technical walls remain separate."
                        ),
                        6.8,
                        fill=MUTED,
                    ),
                ]
                if acoustic
                else [
                    _text(1350, 830, "All dimensions are schematic coordination values.", 7.2, fill=MUTED),
                    _text(1350, 848, "Wall build-ups and structure remain subject to design.", 7.2, fill=MUTED),
                ]
            ),
        ]
    )


def _circle_status(x: float, y: float, color: str) -> str:
    return f'<circle cx="{x}" cy="{y}" r="5" fill="{color}" opacity="0.85"/>'


def _footer(parts: list[str], model: dict[str, Any], digest: str, sheet_id: str) -> None:
    outcome = (
        "D-080 · DIFFERENTIATED P2 WALL FAMILY · DESIGN COORDINATION"
        if model.get("wall_schedule")
        and sheet_id.startswith(("DH-ARQ-PLN-002", "DH-ARQ-DET-003", "DH-ARQ-DET-004", "DH-ARQ-DET-005"))
        else "D-074 · SHARED PB/P2 STAIR CORE · DESIGN COORDINATION"
        if model.get("stair_core")
        and sheet_id.startswith(("DH-ARQ-PLN-002", "DH-ARQ-DIA-001"))
        else "D-067 · UNIFIED PRIMARY BEDROOM · DESIGN COORDINATION"
        if model.get("primary_bedroom_unified")
        and sheet_id.startswith("DH-ARQ-PLN-002")
        else "D-066 · UNIFIED PRIMARY BATHROOM · DESIGN COORDINATION"
        if model.get("primary_bathroom_unified")
        and sheet_id.startswith("DH-ARQ-PLN-002")
        else "D-065 · PRIMARY SUITE REBALANCE · DESIGN COORDINATION"
        if model.get("primary_suite_rebalance")
        and sheet_id.startswith("DH-ARQ-PLN-002")
        else "D-064 · CLEAN P2 PLAN GRAPHICS · DESIGN COORDINATION"
        if model.get("hide_phase_boundary_on_plan")
        and sheet_id.startswith("DH-ARQ-PLN-002")
        else "D-063 · OPEN FAMILY BALCONY · DESIGN COORDINATION"
        if model.get("family_balcony")
        and sheet_id.startswith(("DH-ARQ-PLN-002", "DH-ARQ-DET-004"))
        else "D-062 · EXPANDED P2 WELLNESS · DESIGN COORDINATION"
        if model.get("wellness_suite") and sheet_id.startswith("DH-ARQ-PLN-002")
        else "D-061 · P2 FAMILY DISTRIBUTOR · DESIGN COORDINATION"
        if model.get("central_distributor") and sheet_id.startswith("DH-ARQ-PLN-002")
        else "D-060 · COHERENT P2 FAMILY CENTRE · DESIGN COORDINATION"
        if model.get("family_centre") and sheet_id.startswith("DH-ARQ-PLN-002")
        else "D-059 · REFINED DOUBLE-FRAME P2 EXTERIOR ENVELOPE · DESIGN COORDINATION"
        if model.get("exterior_wall_assembly")
        else "D-058 · CONTINUOUS X=21 ACOUSTIC ENCLOSURE · DESIGN COORDINATION"
        if model.get("hall_edge_partition")
        else "D-057 · 250 mm P2 DRY ACOUSTIC PARTITION · DESIGN COORDINATION"
        if model.get("acoustic_partition")
        else "PRIMARY SUITE PRIORITY · PB LAUNDRY · RETRACTABLE STAIR RESERVE"
        if model.get("relocated_laundry")
        else "b04 SPATIAL LOGIC · b06 VERIFIED CORRECTIONS · EXPLICIT ACCESS"
    )
    parts.extend(
        [
            _rect(36, 1060, 1612, 106, fill=INK),
            _rect(36, 1060, 1612, 7, fill=TEAL),
            _text(56, 1092, "CONTROLLED OUTCOME", 8, weight=700, fill="#9fc4cc"),
            _text(56, 1120, outcome, 13, weight=700, fill="#ffffff"),
            _text(56, 1145, "Current architectural coordination hypothesis. It does not authorize procurement, fabrication or construction.", 7.8, fill="#d3dfe2"),
            _line(1160, 1067, 1160, 1166, stroke="#536970", stroke_width=1),
            _text(1180, 1092, "SHEET", 8, weight=700, fill="#9fc4cc"),
            _text(1180, 1121, sheet_id, 15, weight=700, fill="#ffffff"),
            _text(1180, 1146, f"{model['drawing_revision']} · {model['date']} · SHA {digest[:14]}...", 7.5, fill="#c9d8dc"),
            _line(1450, 1067, 1450, 1166, stroke="#536970", stroke_width=1),
            _text(1470, 1092, "STATUS", 8, weight=700, fill="#9fc4cc"),
            _text(1470, 1120, "NOT FOR", 14, weight=700, fill="#ffffff"),
            _text(1470, 1141, "CONSTRUCTION", 14, weight=700, fill="#ffffff"),
        ]
    )


def build_plan(model: dict[str, Any], report: dict[str, Any] | None = None) -> str:
    report = _report(model) if report is None else report
    _assert_renderable(report)
    digest = hashlib.sha256(
        json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    plan_sheet_id, _, _ = sheet_ids(model)
    owner_priority_revision = bool(model.get("relocated_laundry"))
    metadata = {
        "drawing": plan_sheet_id,
        "revision": model["revision"],
        "model_sha256": digest,
        "status": model["status"],
        "construction_authority": False,
    }
    parts = _svg_start(
        "Dream House coordinated upper-floor plan",
        (
            (
                "An upper-floor revision assigning economical wall thickness by acoustic, wet, hot-side, protected-core and exterior duty. Not for construction."
                if model.get("wall_schedule")
                else "An upper-floor revision coordinating the same mathematical stair and four column reservations used by PB. Not for construction."
                if model.get("stair_core")
                else "An upper-floor revision reading the combined primary bedroom as one room and removing its fitted privacy screen. Not for construction."
                if model.get("primary_bedroom_unified")
                else "An upper-floor revision unifying the primary bathroom as one L-shaped room without an intermediate wall or door. Not for construction."
                if model.get("primary_bathroom_unified")
                else "An upper-floor revision relocating and compacting the primary dressing beside the Child 1 service band while enlarging the bedroom. Not for construction."
                if model.get("primary_suite_rebalance")
                else "An upper-floor revision joining the mini deck and family centre behind one 7.45 m open guarded balcony edge toward the double-height hall. Not for construction."
                if model.get("family_balcony")
                else "An upper-floor revision absorbing the rear spur into an L-shaped dry/wet wellness suite while preserving a clear reserved exterior route. Not for construction."
                if model.get("wellness_suite")
                else "An upper-floor revision opening the stair into one usable family distributor and replacing the long Phase 2 lobby with a short spur. Not for construction."
                if model.get("central_distributor")
                else "An upper-floor revision consolidating the family centre as one coherent shared room while retaining the coordinated suites and interfaces. Not for construction."
                if model.get("family_centre")
                else "An upper-floor revision prioritizing the primary suite, relocating laundry to PB and reserving a retractable exterior stair. Not for construction."
            )
            if owner_priority_revision
            else "A b04-led upper-floor revision with explicit access, b06 dimensional corrections and D-048 stair-column reservations. Not for construction."
        ),
        metadata,
    )
    _header(
        parts,
        model,
        plan_sheet_id,
        "COORDINATED UPPER FLOOR · SCHEMATIC DESIGN",
        (
            "D-080 realistic wall family · 90 / 150 / 200 / 230 mm"
            if model.get("wall_schedule")
            else "D-074 shared PB/P2 stair + four continuous column reserves"
            if model.get("stair_core")
            else "D-067 one primary bedroom + D-066 unified bathroom"
            if model.get("primary_bedroom_unified")
            else "D-066 unified primary bathroom + D-065 suite rebalance"
            if model.get("primary_bathroom_unified")
            else "D-065 compact dressing + enlarged primary bedroom"
            if model.get("primary_suite_rebalance")
            else "D-064 clean plan graphics · phasing retained in dedicated diagram"
            if model.get("hide_phase_boundary_on_plan")
            else "D-063 open family balcony + retained bedroom-edge P2-W04R"
            if model.get("family_balcony")
            else "D-062 expanded wellness + D-057/D-058/D-059 wall controls"
            if model.get("wellness_suite")
            else "D-061 family distributor + D-057/D-058/D-059 wall controls"
            if model.get("central_distributor")
            else "D-060 coherent family centre + D-057/D-058/D-059 wall controls"
            if model.get("family_centre")
            else "D-059 refined exterior envelope + D-058 hall edge + D-057 partitions"
            if model.get("exterior_wall_assembly")
            else "D-058 continuous hall-edge enclosure + D-057 wall control"
            if model.get("hall_edge_partition")
            else "D-057 wall control + primary-suite priority + active interfaces"
            if model.get("acoustic_partition")
            else "primary-suite priority + PB laundry + exterior-stair reserve"
            if owner_priority_revision
            else "b04 spatial logic + b06 controls + D-048 coordination"
        ),
    )
    parts.append(_text(72, 165, "P2 PLAN · 18.00 x 15.00 m · +3.80 m STUDY LEVEL", 12, weight=700))
    parts.append(_text(72, 188, "FRONT / DOUBLE HEIGHT", 7.5, weight=700, fill=AMBER))
    parts.append(_text(672, 188, "REAR CORE", 7.5, anchor="end", weight=700, fill=MUTED))
    _draw_rooms(parts, model)
    _draw_furniture(parts, model)
    _draw_bath_fixtures(parts, model)
    _draw_stair(parts, model)
    _draw_partition_walls(parts, model)
    _draw_exterior_walls(parts, model)
    _draw_hall_edge_wall(parts, model)
    _draw_room_labels(parts, model)
    _draw_windows(parts, model)
    _draw_egress_reserve(parts, model)
    phase_y = _sy(model["phase_boundary_y"])
    if not model.get("hide_phase_boundary_on_plan"):
        parts.append(_line(_sx(21), phase_y, _sx(36), phase_y, stroke=PURPLE, stroke_width=3, stroke_dasharray="9 6", css_class="phase-boundary"))
        parts.append(_text((_sx(21) + _sx(36)) / 2, phase_y - 8, "ONE ISOLATABLE F1 / F2 BOUNDARY", 7.4, anchor="middle", weight=700, fill=PURPLE))
    for door in model["doors"]:
        _draw_door(parts, door, model)
    if model.get("central_distributor") and not model.get("hide_phase_boundary_on_plan"):
        parts.append(
            _line(
                _sx(21),
                phase_y,
                _sx(31.5),
                phase_y,
                stroke=PURPLE,
                stroke_width=3,
                stroke_dasharray="9 6",
                css_class="phase-boundary temporary-open-plan-boundary",
            )
        )
    _draw_columns(parts, model)
    _draw_plan_dimensions(parts, model)
    _right_notes(parts, model, report)
    _footer(parts, model, digest, plan_sheet_id)
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    if any(token in output.lower() for token in ("nan", "infinity", 'inf"')):
        raise P2ModelError("Generated plan contains a non-finite SVG value")
    return output


def _plan_point(space: dict[str, Any], *, origin: float, bottom: float, scale: float) -> tuple[float, float]:
    return (
        _sx(space["x"] + space["w"] / 2.0, origin=origin, scale=scale),
        _sy(space["y"] + space["d"] / 2.0, bottom=bottom, scale=scale),
    )


def build_access_diagram(model: dict[str, Any], report: dict[str, Any] | None = None) -> str:
    report = _report(model) if report is None else report
    _assert_renderable(report)
    digest = hashlib.sha256(
        json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    _, access_sheet_id, _ = sheet_ids(model)
    metadata = {
        "drawing": access_sheet_id,
        "revision": model["revision"],
        "model_sha256": digest,
        "status": model["status"],
        "life_safety_design_resolved": False,
    }
    parts = _svg_start(
        "Dream House upper-floor access and egress diagram",
        "Verified room-access graph and indicative single-stair travel paths. The second independent exit remains open.",
        metadata,
    )
    _header(
        parts,
        model,
        access_sheet_id,
        "UPPER-FLOOR ACCESS + EGRESS LOGIC",
        "topology verified · life-safety design remains open",
    )
    origin, bottom, scale = 95.0, 910.0, 36.0
    by_id = _space_index(model)
    for space in model["spaces"]:
        x = _sx(space["x"], origin=origin, scale=scale)
        y = _sy(space["y"] + space["d"], bottom=bottom, scale=scale)
        parts.append(
            _rect(
                x,
                y,
                space["w"] * scale,
                space["d"] * scale,
                fill="#e2ede8" if space["phase"] == 1 else "#ebe1ee",
                stroke="#637278",
                stroke_width=1.0,
                css_class="access-space",
            )
        )
        cx, cy = _plan_point(space, origin=origin, bottom=bottom, scale=scale)
        parts.append(_text(cx, cy + 2, space["id"], 6.5, anchor="middle", weight=700))

    central_distributor = model.get("central_distributor")
    wellness_suite = model.get("wellness_suite")
    centre_path = ["FAM"] if "HALL-C" not in by_id else ["HALL-C"]
    route_ids = (
        {
            "H1-D": ["H1-D", "DECK", "FAM", "ESC"],
            "M-D": (
                ["M-D", "M-L", "FAM", "ESC"]
                if model.get("primary_suite_rebalance")
                else ["M-D", "M-C", "FAM", "ESC"]
            ),
            "H2-D": ["H2-D", "FAM-N", "FAM", "ESC"],
            "G-D": ["G-D", "G-ENTRY", "FAM-N", "FAM", "ESC"],
            "WELL": [
                "WELL",
                "WELL-D" if wellness_suite else "F2-SPUR",
                "FAM-N",
                "FAM",
                "ESC",
            ],
        }
        if central_distributor
        else {
        "H1-D": (
            ["H1-D", "FAM", "HALL-A", "HALL-C", "ARR", "ESC"]
            if "HALL-A" in by_id
            else ["H1-D", "DECK", "FAM", "ARR", "ESC"]
            if "HALL-C" not in by_id
            else ["H1-D", "DECK", "FAM", "HALL-C", "ARR", "ESC"]
        ),
        "M-D": (
            ["M-D", "M-PASS", "ARR", "ESC"]
            if "M-PASS" in by_id
            else ["M-D", "M-C", "ARR", "ESC"]
        ),
        "H2-D": ["H2-D", "F2-HALL", *centre_path, "ARR", "ESC"],
        "G-D": ["G-D", "G-ENTRY", "F2-HALL", *centre_path, "ARR", "ESC"],
        "WELL": ["WELL", "F2-HALL", *centre_path, "ARR", "ESC"],
        }
    )
    for index, path_ids in enumerate(route_ids.values()):
        points = [_plan_point(by_id[space_id], origin=origin, bottom=bottom, scale=scale) for space_id in path_ids]
        point_text = " ".join(f"{x:.1f},{y + index * 1.3:.1f}" for x, y in points)
        parts.append(
            f'<polyline points="{point_text}" fill="none" stroke="{RED}" stroke-width="{2.6 if index == 0 else 1.7}" opacity="{0.92 if index == 0 else 0.62}" marker-end="url(#route-arrow)" class="egress-route"/>'
        )

    egress = model.get("egress_reserve")
    if egress:
        lobby = _plan_point(by_id[egress["access_space"]], origin=origin, bottom=bottom, scale=scale)
        exterior = (
            _sx(36.0, origin=origin, scale=scale) + 76,
            _sy(float(egress["from"]) + float(egress["width"]) / 2, bottom=bottom, scale=scale),
        )
        parts.extend(
            [
                f'<polyline points="{lobby[0]:.1f},{lobby[1]:.1f} {exterior[0]:.1f},{exterior[1]:.1f}" fill="none" stroke="{TEAL}" stroke-width="3" stroke-dasharray="7 4" marker-end="url(#route-arrow)" class="reserved-second-route"/>',
                _rect(
                    exterior[0] - 56,
                    exterior[1] - 20,
                    70,
                    40,
                    fill="none",
                    stroke=TEAL,
                    stroke_width=1.8,
                    stroke_dasharray="6 4",
                    css_class="retractable-stair-reserve",
                ),
                _text(exterior[0] - 21, exterior[1] - 27, "RESERVED SECOND ROUTE", 6.8, anchor="middle", weight=700, fill=TEAL),
            ]
        )

    phase_y = _sy(model["phase_boundary_y"], bottom=bottom, scale=scale)
    parts.append(_line(origin, phase_y, origin + 15 * scale, phase_y, stroke=PURPLE, stroke_width=3, stroke_dasharray="9 6"))
    _panel_title(parts, 760, 176, "01", "VERIFIED ACCESS TOPOLOGY")
    parts.append(
        _multiline(
            760,
            213,
            (
                [
                    "Every enclosed room reaches ESC through a declared door/opening.",
                    (
                        "The dry wellness threshold reaches the reserved rear stair."
                        if wellness_suite
                        else "The short wellness/egress spur reaches the reserved rear stair."
                        if central_distributor
                        else "The Phase 2 lobby also reaches a reserved rear retractable stair."
                    ),
                    "That exterior device is a geometric reserve, not an approved exit.",
                    (
                        "The main stair opens to the family distributor; fire approval is open."
                        if central_distributor
                        else "The main stair still arrives in a shared protected lobby."
                    ),
                ]
                if egress
                else [
                    "Every enclosed room reaches ESC through a declared door/opening.",
                    "Suite filters prevent bathroom doors from becoming suite entrances.",
                    "The stair arrives in a shared protected lobby, not inside the primary suite.",
                    "The mini deck remains acoustically enclosed from the double-height hall.",
                ]
            ),
            9.2,
            leading=1.65,
        )
    )
    _panel_title(parts, 760, 355, "02", "PHASING LOGIC")
    parts.append(
        _multiline(
            760,
            392,
            [
                "F1: primary suite, Child 1, shared centre, laundry and protected stair.",
                "F2: Child 2, guest suite and wellness behind one controlled boundary.",
                "The temporary enclosure must coordinate fire, dust, noise and services.",
            ],
            9.2,
            leading=1.65,
        )
    )
    parts.append(_rect(760, 510, 790, 132, fill="#f5ded8", stroke="#bf7468", stroke_width=1.2, rx=6))
    parts.append(_text(782, 542, "LIFE-SAFETY HOLD POINT", 9, weight=700, fill=RED))
    parts.append(
        _multiline(
            782,
            572,
            [
                (
                    "A retractable exterior stair reserve is shown, but is not yet an accepted exit."
                    if egress
                    else "The arrows converge on the only stair currently represented."
                ),
                "This diagram does not validate travel distance, occupant load, fire rating,",
                "deployment under fire/power loss, accessibility or the required number of exits.",
                "D-021 and the professional fire review remain mandatory before freezing P2.",
            ],
            8.7,
            leading=1.45,
            fill="#6f3028",
        )
    )
    _panel_title(parts, 760, 710, "03", "STRUCTURAL INTERFACE")
    parts.append(
        _multiline(
            760,
            747,
            [
                "D-048 retains four foundation-to-roof column reservations around ESC.",
                "Stair flights are not counted as the primary lateral system.",
                "Landing drift joints, enclosure fire rating and clear widths remain open.",
            ],
            9.2,
            leading=1.65,
        )
    )
    parts.append(_text(95, 960, f"ACCESS GRAPH: {report['passed']} PASS · {report['failed']} FAIL · {report['open']} OPEN", 9, weight=700, fill=GREEN))
    _footer(parts, model, digest, access_sheet_id)
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def build_owner_priorities_detail(model: dict[str, Any]) -> str:
    """Draw the PB laundry, retractable-stair and exposed-truss coordination brief."""

    laundry = model.get("relocated_laundry")
    egress = model.get("egress_reserve")
    edge = model.get("edge_truss_intent")
    hall_edge = model.get("hall_edge_partition")
    family_balcony = model.get("family_balcony")
    if not (laundry and egress and edge):
        raise P2ModelError("Owner-priorities detail requires laundry, egress and edge-truss data")
    report = _report(model)
    _assert_renderable(report)
    digest = hashlib.sha256(
        json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    _, _, detail_sheet_id = sheet_ids(model)
    metadata = {
        "drawing": detail_sheet_id,
        "revision": model["revision"],
        "model_sha256": digest,
        "status": model["status"],
        "construction_authority": False,
        "life_safety_design_resolved": False,
    }
    parts = _svg_start(
        "Dream House owner-priority coordination details",
        "PB laundry relocation, retractable exterior stair reserve and large exposed edge-truss architectural brief.",
        metadata,
    )
    _header(
        parts,
        model,
        detail_sheet_id,
        "OWNER PRIORITIES · ARCHITECTURAL INTERFACES",
        (
            "PB laundry + retractable stair + open family balcony at exposed truss"
            if family_balcony
            else "PB laundry + retractable stair + exposed truss outside continuous P2-W04"
            if hall_edge
            else "PB laundry + retractable stair + large exposed X=21 truss"
        ),
    )

    _panel_title(parts, 70, 166, "01", "PB LAUNDRY BEHIND THE GREAT WALL")
    core_x, core_y, scale = 105.0, 215.0, 52.0
    core_width = 4.5 * scale
    core_height = 7.4 * scale
    parts.extend(
        [
            _rect(core_x, core_y, core_width, core_height, fill="#eef0eb", stroke=INK, stroke_width=2),
            _rect(core_x, core_y, 0.20 * scale, core_height, fill="#b88c64", stroke="#6f4e34", stroke_width=1.2),
            _rect(core_x + 0.20 * scale, core_y, 4.30 * scale, 2.4 * scale, fill="#e5dcc7", stroke=MUTED, stroke_width=1),
            _rect(core_x + 0.20 * scale, core_y + 2.4 * scale, 4.30 * scale, 5.0 * scale, fill="#dce2dc", stroke=MUTED, stroke_width=1),
            _text(core_x + core_width / 2, core_y + 1.2 * scale, "PANTRY / CLEAN SUPPORT", 8, anchor="middle", weight=700),
            _text(core_x + core_width / 2, core_y + 3.0 * scale, "STORAGE + CONCEALED LAUNDRY", 8, anchor="middle", weight=700),
        ]
    )
    lx = core_x + (float(laundry["x"]) - 31.5) * scale
    ly = core_y + float(laundry["y"]) * scale
    lw = float(laundry["w"]) * scale
    ld = float(laundry["d"]) * scale
    parts.extend(
        [
            _rect(lx, ly, lw, ld, fill="#c7ddd8", stroke=TEAL, stroke_width=2, css_class="pb-laundry-reserve"),
            _text(lx + lw / 2, ly + 15, "W + D + SINK + TALL STORE", 7, anchor="middle", weight=700, fill="#1e6673"),
            _line(lx + lw / 2, ly + ld, lx + lw / 2, ly + ld + 56, stroke=TEAL, stroke_width=1.6, stroke_dasharray="6 4"),
            _text(lx + lw / 2, ly + ld + 72, "STACK BELOW PRIMARY WET BAND", 7.2, anchor="middle", weight=700, fill=TEAL),
            _text(core_x - 18, core_y + core_height / 2, "GREAT WALL", 8, anchor="middle", weight=700, fill="#6f4e34"),
        ]
    )
    parts.append(
        _multiline(
            375,
            238,
            [
                "Preferred location: inside the existing PB storage room.",
                "The open hall remains free of a new enclosed box.",
                "Laundry noise and visual clutter stay behind the flush Great Wall door.",
                "The reserve aligns below the enlarged primary bathroom/service band.",
                "Drainage, trap primer, ventilation, waterproofing and appliance access remain MEP tasks.",
            ],
            8.8,
            leading=1.55,
        )
    )

    _panel_title(parts, 830, 166, "02", "REAR RETRACTABLE EXTERIOR STAIR RESERVE")
    facade_x, ground_y, landing_y = 1020.0, 610.0, 365.0
    parts.extend(
        [
            _line(870, ground_y, 1510, ground_y, stroke=INK, stroke_width=2),
            _line(facade_x, 220, facade_x, ground_y, stroke=INK, stroke_width=6),
            _rect(facade_x - 8, landing_y - 56, 16, 56, fill="#f5ded8", stroke=RED, stroke_width=2, css_class="egress-door"),
            _line(facade_x, landing_y, 1130, landing_y, stroke=RED, stroke_width=5),
            _text(1075, landing_y - 12, "P2 LANDING", 7.5, anchor="middle", weight=700, fill=RED),
            _line(1130, landing_y, 1210, 465, stroke=RED, stroke_width=7, css_class="retracted-stair"),
            _line(1210, 465, 1125, 520, stroke=RED, stroke_width=7, css_class="retracted-stair"),
            _text(1218, 493, "RETRACTED", 8, weight=700, fill=RED),
            _text(1218, 508, "LOWER END ABOVE GRADE", 7, weight=700, fill=RED),
            _line(1130, landing_y, 1450, ground_y, stroke=TEAL, stroke_width=3, stroke_dasharray="10 6", css_class="deployed-stair"),
            _line(1100, landing_y + 6, 1420, ground_y + 6, stroke=TEAL, stroke_width=3, stroke_dasharray="10 6", css_class="deployed-stair"),
            _text(1380, 555, "DEPLOYED STUDY POSITION", 8, anchor="middle", weight=700, fill=TEAL),
        ]
    )
    for index in range(9):
        x = 1140 + index * 34
        y = landing_y + 14 + index * 25.5
        parts.append(_line(x, y, x + 24, y + 2, stroke=TEAL, stroke_width=1.2, stroke_dasharray="5 3"))
    parts.append(
        _multiline(
            845,
            655,
            [
                "Security intent: the lower flight does not touch grade while stored.",
                (
                    "Access is directly from the dry wellness threshold."
                    if model.get("wellness_suite")
                    else "Access is directly from the short common wellness/egress spur."
                    if model.get("central_distributor")
                    else "Access is directly from the common Phase 2 lobby, not through a bedroom."
                ),
                "Required study: counterbalanced/manual fail-safe deployment without a key from inside.",
                "Do not count as a compliant second exit until fire, egress, accessibility and rescue review.",
            ],
            8.4,
            leading=1.45,
        )
    )

    _panel_title(
        parts,
        70,
        790,
        "03",
        (
            "X=21 EDGE · EXPOSED TRUSS + OPEN FAMILY BALCONY"
            if family_balcony
            else "X=21 EDGE · EXPOSED TRUSS + CONTINUOUS P2-W04"
            if hall_edge
            else "X=21 EDGE · ONE LARGE INDUSTRIAL TRUSS"
        ),
    )
    tx0, tx1, top_y, bottom_y = 105.0, 740.0, 845.0, 965.0
    if hall_edge and not family_balcony:
        parts.extend(
            [
                _rect(
                    tx0,
                    top_y,
                    tx1 - tx0,
                    bottom_y - top_y,
                    fill="#d8e7df",
                    stroke=TEAL,
                    stroke_width=2,
                    css_class="p2-w04-behind-truss",
                ),
                _text(
                    (tx0 + tx1) / 2,
                    top_y + 22,
                    "P2-W04 CONTINUES BEHIND / PRIVATE SIDE",
                    7.2,
                    anchor="middle",
                    weight=700,
                    fill=TEAL,
                ),
            ]
        )
    parts.extend(
        [
            _line(tx0, top_y, tx1, top_y, stroke=INK, stroke_width=9),
            _line(tx0, bottom_y, tx1, bottom_y, stroke=INK, stroke_width=9),
        ]
    )
    if family_balcony:
        parts.extend(
            [
                _line(tx0, bottom_y - 8, tx1, bottom_y - 8, stroke=AMBER, stroke_width=4, stroke_dasharray="12 5"),
                _text((tx0 + tx1) / 2, top_y + 22, "OPEN FAMILY BALCONY · CONTINUOUS GUARD", 7.2, anchor="middle", weight=700, fill=AMBER),
            ]
        )
    panels = 6
    panel = (tx1 - tx0) / panels
    for index in range(panels):
        xa, xb = tx0 + index * panel, tx0 + (index + 1) * panel
        parts.append(
            _line(
                xa,
                bottom_y if index % 2 == 0 else top_y,
                xb,
                top_y if index % 2 == 0 else bottom_y,
                stroke="#4d626a",
                stroke_width=6,
                css_class="large-exposed-truss-web",
            )
        )
    parts.extend(
        [
            _rect(tx0 + 135, bottom_y + 18, 360, 48, fill="#e6d5b9", stroke=AMBER, stroke_width=1.5),
            _text(tx0 + 315, bottom_y + 47, "MINI-DECK VIEW CONE KEPT CLEAR", 8.5, anchor="middle", weight=700, fill=AMBER),
            _text(805, 846, "ARCHITECTURAL BRIEF", 9, weight=700, fill=TEAL),
            _multiline(
                805,
                875,
                [
                    "A visible truss is acceptable—and desirable—when it reads as one large,",
                    "deep, load-bearing industrial object. Small decorative trusses are rejected.",
                    "The open family-balcony view remains primary; member topology, depth, joints, fire"
                    if family_balcony
                    else "The mini-deck view remains primary; member topology, depth, joints, fire",
                    "protection, vibration and services still require structural coordination.",
                    *(
                        ["D-063: coordinate the 7.45 m guard, edge beam and smoke/noise transfer."]
                        if family_balcony
                        else ["D-058: keep it hall-side; do not puncture or rigidly bridge P2-W04."]
                        if hall_edge
                        else []
                    ),
                ],
                9.1,
                leading=1.45,
            ),
        ]
    )

    _footer(parts, model, digest, detail_sheet_id)
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def build_differentiated_wall_family_detail(model: dict[str, Any]) -> str:
    """Draw the D-080 economical P2 wall family and its limits of authority."""

    report = _report(model)
    _assert_renderable(report)
    digest = hashlib.sha256(
        json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    schedule = model["wall_schedule"]
    sheet_id = f"DH-ARQ-DET-003-{model['drawing_revision']}"
    metadata = {
        "drawing": sheet_id,
        "revision": model["revision"],
        "model_sha256": digest,
        "status": model["status"],
        "wall_types": list(schedule),
        "construction_authority": False,
        "acoustic_rating_claimed": False,
        "fire_rating_claimed": False,
    }
    parts = _svg_start(
        "Dream House D-080 differentiated P2 wall family",
        "Economical wall thicknesses assigned by duty, with enhanced separation only where privacy, wet use, heat, protected circulation or weather exposure requires it. Not for construction.",
        metadata,
    )
    _header(
        parts,
        model,
        sheet_id,
        "P2 WALL FAMILY · REALISTIC THICKNESS BY DUTY",
        "D-080 · 90 / 150 / 200 / 230 mm coordination values · performance gates open",
    )

    layer_colors = {
        "new gypsum board": "#f7f5ef",
        "reclaimed gypsum board": "#d7d2c8",
        "metal stud frame with glass-wool infill": "#d8e7df",
        "clear air cavity": "#ffffff",
    }

    def draw_build_up(
        assembly: dict[str, Any], y: float, title: str, note: str, scale: float
    ) -> None:
        x0, height = 120.0, 126.0
        cursor = x0
        parts.append(_text(70, y - 55, title, 10.5, weight=700, fill=TEAL))
        parts.append(_text(70, y - 35, note, 7.2, fill=MUTED))
        for index, layer in enumerate(assembly["room_side_to_room_side_layers"], start=1):
            width = float(layer["nominal_mm"]) * scale
            material = layer["material"]
            parts.append(
                _rect(
                    cursor,
                    y,
                    width,
                    height,
                    fill=layer_colors[material],
                    stroke=INK,
                    stroke_width=1.0,
                    css_class=f"wall-layer {material.replace(' ', '-').lower()}",
                )
            )
            if material == "metal stud frame with glass-wool infill":
                for offset in range(10, max(11, int(width)), 18):
                    parts.append(
                        _line(
                            cursor + offset,
                            y + 7,
                            cursor + min(offset + 12, width - 3),
                            y + height - 7,
                            stroke=GREEN,
                            stroke_width=0.9,
                            opacity=0.65,
                        )
                    )
            parts.append(
                _text(cursor + width / 2, y + height + 20, str(index), 6.6, anchor="middle", weight=700)
            )
            cursor += width
        nominal = int(round(float(assembly["nominal_total_m"]) * 1000.0))
        layer_sum = sum(float(layer["nominal_mm"]) for layer in assembly["room_side_to_room_side_layers"])
        parts.extend(
            [
                _line(x0, y - 2, cursor, y - 2, stroke=TEAL, stroke_width=1.6),
                _line(x0, y - 9, x0, y + 5, stroke=TEAL, stroke_width=1.6),
                _line(cursor, y - 9, cursor, y + 5, stroke=TEAL, stroke_width=1.6),
                _text(
                    (x0 + cursor) / 2,
                    y - 10,
                    f"{nominal} mm NOMINAL · {layer_sum:g} mm ILLUSTRATIVE SUM",
                    7.8,
                    anchor="middle",
                    weight=700,
                    fill=TEAL,
                ),
            ]
        )

    _panel_title(parts, 70, 165, "01", "TWO DRY-WALL DUTIES · SPEND MASS ONLY AT SEPARATIONS", width=830)
    draw_build_up(
        model["internal_partition"],
        260,
        "P2-W01A · 90 mm · SAME-SUITE DRY WALL",
        "1 new board / 64 mm insulated frame / 1 new board · no rating claimed",
        3.0,
    )
    draw_build_up(
        model["acoustic_partition"],
        555,
        "P2-W01B · 200 mm · SUITE / COMMON SEPARATION",
        "2 outer boards / 64 frame / 20 clear / 64 frame / 2 outer boards · independent frames",
        3.0,
    )
    parts.append(
        _multiline(
            120,
            735,
            [
                "Layer keys: 1…n follow room-side to room-side order in the controlled model.",
                "Recovered gypsum is concealed only in W01B; visible faces remain new board.",
            ],
            7.4,
            leading=1.55,
            fill=MUTED,
        )
    )

    _panel_title(parts, 960, 165, "02", "COORDINATION SCHEDULE", width=620)
    headers = ("TYPE", "NOM.", "USE / LIMIT")
    for x, label in zip((980, 1115, 1210), headers, strict=True):
        parts.append(_text(x, 208, label, 7.2, weight=700, fill=MUTED))
    rows = [
        ("P2-W01A", "90", "dry wall inside one suite"),
        ("P2-W01B", "200", "suite-to-suite / suite-to-common"),
        ("P2-W02", "150", "wet / service wall; shafts thicken locally"),
        ("P2-W02S", "200", "sauna / hot-side reserve; separate detail"),
        ("P2-W03", "200", "stair / protected-core reserve only"),
        ("P2-W04R", "200", "retained bedroom ends at hall edge"),
        ("P2-W05", "230", "insulated shell + independent inner lining"),
        ("P2-W06", "90", "reversible phase closure; upgrade if required"),
    ]
    for index, (wall_id, thickness, use) in enumerate(rows):
        y = 245 + index * 50
        parts.append(_rect(970, y - 24, 590, 39, fill="#eef2f0" if index % 2 == 0 else "#faf9f5"))
        parts.extend(
            [
                _text(980, y, wall_id, 7.8, weight=700, fill=TEAL),
                _text(1115, y, thickness + " mm", 7.5, weight=700),
                _text(1210, y, use, 7.2),
            ]
        )

    _panel_title(parts, 960, 680, "03", "PROFESSIONAL HOLD POINTS", width=620)
    parts.append(
        _multiline(
            980,
            720,
            [
                "Do not infer STC/Rw or fire resistance from thickness.",
                "Select tested local systems after fire and acoustic briefs.",
                "Engineer head tracks, anchors, bracing and steel interfaces.",
                "Coordinate plumbing stacks before freezing W02 locally.",
                "Mock up seals, outlets and reclaimed concealed board.",
            ],
            8.0,
            leading=1.58,
            fill=RED,
        )
    )

    _panel_title(parts, 70, 865, "04", "ECONOMY / AUTHORITY")
    parts.append(
        _multiline(
            70,
            905,
            [
                "The 90 mm wall is restricted to low-risk same-suite boundaries; privacy boundaries keep twin independent frames.",
                "Nominal thickness is a schematic design-control value, not a product order or construction dimension.",
                "Wet, hot-side, protected-core and exterior types remain subject to professional assembly selection.",
            ],
            8.7,
            leading=1.52,
        )
    )
    parts.append(_rect(1120, 880, 440, 104, fill="#f5ded8", stroke="#bf7468", stroke_width=1.2, rx=6))
    parts.append(_text(1142, 912, "NOT FOR CONSTRUCTION", 9, weight=700, fill=RED))
    parts.append(_text(1142, 943, "No acoustic, fire, structural or moisture rating is claimed.", 7.4, fill="#6f3028"))
    parts.append(_text(1142, 966, "D-080 replaces the former universal 250 mm dry-wall rule.", 7.4, fill="#6f3028"))

    _footer(parts, model, digest, sheet_id)
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def build_acoustic_partition_detail(model: dict[str, Any]) -> str:
    """Draw the D-057 P2-W01 coordination build-up and its limits of authority."""

    if model.get("wall_schedule"):
        return build_differentiated_wall_family_detail(model)

    acoustic = model.get("acoustic_partition")
    if not acoustic:
        raise P2ModelError("Acoustic-partition detail requires acoustic_partition data")
    report = _report(model)
    _assert_renderable(report)
    digest = hashlib.sha256(
        json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    sheet_id = f"DH-ARQ-DET-003-{model['drawing_revision']}"
    metadata = {
        "drawing": sheet_id,
        "revision": model["revision"],
        "model_sha256": digest,
        "status": model["status"],
        "wall_type": acoustic["id"],
        "nominal_total_mm": 250,
        "construction_authority": False,
        "acoustic_rating_claimed": False,
        "fire_rating_claimed": False,
    }
    parts = _svg_start(
        "Dream House P2-W01 nominal 250 mm acoustic partition",
        "D-057 design-control detail with twin insulated frames, concealed reclaimed gypsum board and new finish board. Not for construction.",
        metadata,
    )
    _header(
        parts,
        model,
        sheet_id,
        "P2-W01 · 250 mm NOMINAL ACOUSTIC PARTITION",
        (
            "D-057 build-up · also used in opaque P2-W04 portions under D-058"
            if model.get("hall_edge_partition")
            else "D-057 design control · dry interior P2 walls only"
        ),
    )

    _panel_title(parts, 70, 165, "01", "ROOM-TO-ROOM BUILD-UP · NO CENTRE BOARD")
    x0, y0, height, mm_scale = 150.0, 260.0, 250.0, 3.0
    layer_colors = {
        "new gypsum board": "#f7f5ef",
        "reclaimed gypsum board": "#d7d2c8",
        "metal stud frame with glass-wool infill": "#d8e7df",
        "clear air cavity": "#ffffff",
    }
    cursor = x0
    layer_centres: list[tuple[float, dict[str, Any]]] = []
    for layer in acoustic["room_side_to_room_side_layers"]:
        width = float(layer["nominal_mm"]) * mm_scale
        material = layer["material"]
        parts.append(
            _rect(
                cursor,
                y0,
                width,
                height,
                fill=layer_colors[material],
                stroke=INK,
                stroke_width=1.2,
                css_class=f"wall-layer {material.replace(' ', '-').lower()}",
            )
        )
        if material == "metal stud frame with glass-wool infill":
            for offset in range(12, int(width), 20):
                parts.append(
                    _line(
                        cursor + offset,
                        y0 + 8,
                        cursor + min(offset + 14, width - 4),
                        y0 + height - 8,
                        stroke=GREEN,
                        stroke_width=1.1,
                        opacity=0.65,
                        css_class="glass-wool-infill",
                    )
                )
        layer_centres.append((cursor + width / 2.0, layer))
        cursor += width

    parts.extend(
        [
            _line(x0, 224, cursor, 224, stroke=TEAL, stroke_width=1.8),
            _line(x0, 215, x0, 233, stroke=TEAL, stroke_width=1.8),
            _line(cursor, 215, cursor, 233, stroke=TEAL, stroke_width=1.8),
            _text(
                (x0 + cursor) / 2,
                210,
                "250 mm NOMINAL · 250.8 mm ILLUSTRATIVE LAYER SUM",
                10,
                anchor="middle",
                weight=700,
                fill=TEAL,
            ),
            _text(x0 - 30, y0 + height / 2, "ROOM A", 9, anchor="end", weight=700),
            _text(cursor + 30, y0 + height / 2, "ROOM B", 9, weight=700),
        ]
    )

    label_rows = [560, 600, 640, 680, 720, 760, 800]
    for row, (centre, layer) in zip(label_rows, layer_centres, strict=True):
        material = layer["material"]
        label = {
            "new gypsum board": "12.7 NEW FINISH BOARD",
            "reclaimed gypsum board": "12.7 RECLAIMED BOARD · CONCEALED",
            "metal stud frame with glass-wool infill": "60 FRAME + 50 GLASS WOOL",
            "clear air cavity": "80 CLEAR DECOUPLING CAVITY",
        }[material]
        parts.extend(
            [
                _line(centre, y0 + height, centre, row - 14, stroke=MUTED, stroke_width=0.9),
                _text(centre, row, label, 7.0, anchor="middle", weight=700),
            ]
        )

    _panel_title(parts, 1010, 165, "02", "WHY THIS IS THE ECONOMICAL BASE", width=638)
    economy_lines = [
        "Two independent frames provide the primary decoupling.",
        "Glass wool fills each frame; the central cavity stays clear.",
        "Reclaimed board adds concealed mass where appearance is irrelevant.",
        "New outer boards provide the durable visible finish.",
        "No third gypsum leaf is placed in the centre cavity.",
    ]
    if model.get("hall_edge_partition"):
        economy_lines.append("P2-W04 uses this build-up only in its opaque portions.")
    parts.append(
        _multiline(
            1010,
            205,
            economy_lines,
            8.7,
            leading=1.58,
        )
    )

    _panel_title(parts, 1010, 405, "03", "RECLAIMED-BOARD ACCEPTANCE", width=638)
    parts.append(
        _multiline(
            1010,
            445,
            [
                "Concealed layer only; never the visible finish.",
                "Accept only dry, clean, sound sheets without mould or delamination.",
                "Confirm fastener holding on a site sample before installation.",
                "Stagger joints from the finish layer and seal the perimeter.",
                "Reject damaged edges that prevent continuous sealed joints.",
            ],
            8.4,
            leading=1.55,
        )
    )

    _panel_title(parts, 1010, 620, "04", "EXCLUDED FROM P2-W01", width=638)
    parts.append(
        _multiline(
            1010,
            660,
            [
                "Exterior / facade walls.",
                "Sauna hot-side and wet-area build-ups.",
                "Protected-stair and fire-rated enclosures.",
                "Shafts, equipment and structural / bracing walls.",
            ],
            8.6,
            leading=1.6,
            fill=RED,
        )
    )

    _panel_title(parts, 70, 875, "05", "COORDINATION HOLD POINTS BEFORE CONSTRUCTION")
    parts.append(
        _multiline(
            70,
            915,
            [
                "Select locally available studs and boards while maintaining 250 mm nominal overall thickness.",
                "Verify head movement, anchorage, fire requirement, acoustic doors, seals, outlets and penetrations.",
                "Build one full-height mock-up; inspect reused board, wool fit, perimeter seals and absence of rigid bridges.",
                "No STC/Rw, field DnT,w or fire rating is claimed by this schematic detail.",
            ],
            9.0,
            leading=1.55,
        )
    )
    parts.append(
        _rect(1030, 880, 520, 116, fill="#f5ded8", stroke="#bf7468", stroke_width=1.2, rx=6)
    )
    parts.append(_text(1052, 912, "AUTHORITY", 8, weight=700, fill=RED))
    parts.append(
        _multiline(
            1052,
            942,
            [
                "Frozen as a DESIGN CONTROL VALUE for P2 coordination.",
                "Not a tested assembly and not for procurement or construction.",
            ],
            8.6,
            leading=1.55,
            fill="#6f3028",
        )
    )

    _footer(parts, model, digest, sheet_id)
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def build_family_balcony_detail(model: dict[str, Any]) -> str:
    """Draw the D-063 open family-balcony edge and retained bedroom enclosure."""

    wall = model["hall_edge_partition"]
    balcony = model["family_balcony"]
    report = _report(model)
    _assert_renderable(report)
    digest = hashlib.sha256(
        json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    sheet_id = f"DH-ARQ-DET-004-{model['drawing_revision']}"
    metadata = {
        "drawing": sheet_id,
        "revision": model["revision"],
        "model_sha256": digest,
        "status": model["status"],
        "wall_type": wall["id"],
        "open_balcony_length_m": float(balcony["to_y"]) - float(balcony["from_y"]),
        "construction_authority": False,
        "acoustic_continuity_claimed": False,
        "fire_rating_claimed": False,
    }
    parts = _svg_start(
        "Dream House open family balcony at the P2 hall edge",
        "D-063 coordination detail for a 7.45 m open guarded family frontage with bedroom enclosure retained at both ends. Not for construction.",
        metadata,
    )
    _header(
        parts,
        model,
        sheet_id,
        "P2-W04R · OPEN FAMILY BALCONY / RETAINED SUITE EDGE",
        "D-063 · 7.45 m open frontage · continuous guard · bedrooms remain enclosed",
    )

    _panel_title(parts, 70, 165, "01", "UNFOLDED X=21 EDGE · P2 SIDE")
    run_x, run_y, run_w, run_h = 110.0, 255.0, 720.0, 255.0
    y_scale = run_w / 18.0
    open_from = float(balcony["from_y"])
    open_to = float(balcony["to_y"])
    for low, high, label in (
        (0.0, open_from, "CHILD 1 · ENCLOSED"),
        (open_to, 18.0, "CHILD 2 · ENCLOSED"),
    ):
        x = run_x + low * y_scale
        width = (high - low) * y_scale
        parts.extend(
            [
                _rect(x, run_y, width, run_h, fill=COLORS["bedroom"], stroke=INK, stroke_width=7, css_class="p2-w04r-suite-edge"),
                _text(x + width / 2, run_y + 126, label, 8, anchor="middle", weight=700),
                _text(
                    x + width / 2,
                    run_y + 150,
                    (
                        "P2-W04R · 200 mm FULL HEIGHT"
                        if model.get("wall_schedule")
                        else "P2-W04R FULL HEIGHT"
                    ),
                    6.8,
                    anchor="middle",
                    fill=TEAL,
                ),
            ]
        )
    bx = run_x + open_from * y_scale
    bw = (open_to - open_from) * y_scale
    parts.extend(
        [
            _rect(bx, run_y, bw, run_h, fill="#f6ead8", stroke=AMBER, stroke_width=3, stroke_dasharray="12 5", css_class="open-family-balcony"),
            _line(bx, run_y + run_h - 18, bx + bw, run_y + run_h - 18, stroke=AMBER, stroke_width=6, css_class="family-balcony-guard"),
            _text(bx + bw / 2, run_y + 104, "OPEN FAMILY BALCONY", 10, anchor="middle", weight=700, fill=AMBER),
            _text(bx + bw / 2, run_y + 132, "MINI DECK + FAMILY DISTRIBUTOR + STUDY EDGE", 6.8, anchor="middle", weight=700),
            _text(bx + bw / 2, run_y + 160, "1.10 m MIN GUARD · HEIGHT / LOADS TBD", 6.8, anchor="middle", weight=700, fill=AMBER),
            _line(run_x, 220, run_x + run_w, 220, stroke=TEAL, stroke_width=1.8),
            _line(run_x, 211, run_x, 229, stroke=TEAL, stroke_width=1.8),
            _line(run_x + run_w, 211, run_x + run_w, 229, stroke=TEAL, stroke_width=1.8),
            _text(run_x + run_w / 2, 205, "18.00 m HALL EDGE · 7.45 m OPEN / 10.55 m ENCLOSED", 9.5, anchor="middle", weight=700, fill=TEAL),
            _text(run_x, 555, "Y=0.00 · LOW EAVE", 7.2, weight=700, fill=MUTED),
            _text(run_x + run_w, 555, "Y=18.00 · HIGH EAVE", 7.2, anchor="end", weight=700, fill=MUTED),
            _text(run_x + run_w / 2, 592, "NO ACOUSTIC GLAZING AT THE OPEN FAMILY FRONTAGE", 8.5, anchor="middle", weight=700, fill=RED),
        ]
    )

    _panel_title(parts, 930, 165, "02", "SCHEMATIC SECTION AT OPEN EDGE", width=650)
    parts.extend(
        [
            _rect(980, 490, 560, 22, fill="#c8c1b7", stroke=INK, stroke_width=1.2),
            _text(1515, 538, "P2 FLOOR / EDGE BEAM", 7.4, anchor="end", weight=700),
            _line(1115, 490, 1115, 365, stroke=AMBER, stroke_width=8, css_class="family-balcony-guard"),
            _line(1088, 365, 1142, 365, stroke=AMBER, stroke_width=5),
            _text(1150, 375, "CONTINUOUS GUARD", 8, weight=700, fill=AMBER),
            _text(1150, 398, "≥1.10 m · NON-CLIMBABLE", 7.2, weight=700),
            _line(1115, 270, 995, 405, stroke="#4d626a", stroke_width=8, stroke_linecap="round"),
            _line(995, 405, 1115, 455, stroke="#4d626a", stroke_width=8, stroke_linecap="round"),
            _text(980, 380, "EXPOSED X=21", 7.2, anchor="end", weight=700),
            _text(980, 403, "TRUSS / EDGE", 8.4, anchor="end", weight=700),
            _text(1035, 540, "DOUBLE-HEIGHT HALL / WORKSHOPS", 7.2, anchor="middle", weight=700, fill=AMBER),
            _text(1390, 540, "FAMILY BALCONY", 7.2, anchor="middle", weight=700, fill=TEAL),
            _text(1260, 585, "Coordinate guard anchors, edge beam, vibration and truss clearance", 7.4, anchor="middle"),
            _text(1260, 606, "without assuming the architectural line is a structural design.", 7.4, anchor="middle"),
        ]
    )

    _panel_title(parts, 70, 690, "03", "ARCHITECTURAL CONTROL")
    parts.append(
        _multiline(
            70,
            730,
            [
                "Open the complete Y=5.00–12.45 family frontage; do not leave residual wall piers.",
                "Join the former mini deck to the family distributor with a full 2.80 m opening.",
                (
                    "Keep both bedroom end zones enclosed with P2-W04R / W01B 200 mm and controlled doors."
                    if model.get("wall_schedule")
                    else "Keep both bedroom end zones fully enclosed with acoustically controlled doors."
                ),
                "Use one visually quiet, continuous and non-climbable guard along the void.",
            ],
            8.8,
            leading=1.55,
        )
    )

    _panel_title(parts, 930, 690, "04", "OPEN PROFESSIONAL GATES", width=650)
    parts.append(
        _multiline(
            930,
            730,
            [
                "Guard height, loads, openings, anchors and impact resistance.",
                "Edge beam, floor vibration, exposed-truss topology and fire protection.",
                "Smoke movement and required separation from the workshop/hall volume.",
                "Hall noise transfer to the family centre and through suite entrance doors.",
                "Lighting, glare, falling-object control and cleaning access over the void.",
            ],
            8.5,
            leading=1.52,
            fill=RED,
        )
    )
    parts.append(_rect(930, 910, 650, 94, fill="#f5ded8", stroke="#bf7468", stroke_width=1.2, rx=6))
    parts.extend(
        [
            _text(952, 940, "AUTHORITY", 8, weight=700, fill=RED),
            _text(952, 969, "Owner-approved spatial intent; guard, structure, fire and acoustic performance remain undesigned.", 8.0, weight=700, fill="#6f3028"),
        ]
    )
    _footer(parts, model, digest, sheet_id)
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def build_hall_edge_detail(model: dict[str, Any]) -> str:
    """Draw the D-058 continuous X=21 hall/workshop-edge enclosure concept."""

    if model.get("family_balcony"):
        return build_family_balcony_detail(model)

    wall = model.get("hall_edge_partition")
    if not wall:
        raise P2ModelError("Hall-edge detail requires hall_edge_partition data")
    report = _report(model)
    _assert_renderable(report)
    digest = hashlib.sha256(
        json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    sheet_id = f"DH-ARQ-DET-004-{model['drawing_revision']}"
    metadata = {
        "drawing": sheet_id,
        "revision": model["revision"],
        "model_sha256": digest,
        "status": model["status"],
        "wall_type": wall["id"],
        "axis_x": wall["axis_x"],
        "continuous_length_m": float(wall["to_y"]) - float(wall["from_y"]),
        "construction_authority": False,
        "acoustic_rating_claimed": False,
        "fire_rating_claimed": False,
    }
    parts = _svg_start(
        "Dream House continuous P2 hall-edge acoustic enclosure",
        "D-058 coordination detail for the full X=21 edge toward the double-height hall and workshops. Not for construction.",
        metadata,
    )
    _header(
        parts,
        model,
        sheet_id,
        "P2-W04 · CONTINUOUS HALL / WORKSHOP EDGE",
        "D-058 · 18.00 m full-height enclosure · only GLZ-DECK interrupts",
    )

    _panel_title(parts, 70, 165, "01", "UNFOLDED X=21 EDGE · P2 SIDE")
    run_x, run_y, run_w, run_h = 110.0, 255.0, 720.0, 255.0
    y_scale = run_w / 18.0
    family_centre = model.get("family_centre")
    central_distributor = model.get("central_distributor")
    deck = _space_index(model)["DECK"]
    family = _space_index(model)["FAM"]
    segments = [
        (0.0, 5.0, "CHILD 1 BEDROOM", COLORS["bedroom"]),
        (5.0, deck["y"] + deck["d"], "MINI DECK", COLORS["deck"]),
        (
            family["y"] if family_centre else 8.5,
            12.45 if central_distributor else 11.0,
            "FAMILY DISTRIBUTOR" if central_distributor else "FAMILY ROOM" if family_centre else "FAMILY LOUNGE",
            COLORS["shared"],
        ),
        *([] if central_distributor else [(11.0, 12.45, "F2 LOBBY", COLORS["circulation"])]),
        (12.45, 18.0, "CHILD 2 BEDROOM", COLORS["bedroom"]),
    ]
    for low, high, label, color in segments:
        x = run_x + low * y_scale
        width = (high - low) * y_scale
        parts.extend(
            [
                _rect(x, run_y, width, run_h, fill=color, stroke="#90a0a5", stroke_width=0.8),
                _text(x + width / 2.0, run_y + run_h + 26, label, 7.0, anchor="middle", weight=700),
            ]
        )

    parts.append(
        _rect(
            run_x,
            run_y,
            run_w,
            run_h,
            fill="none",
            stroke=INK,
            stroke_width=9,
            css_class="hall-edge-wall p2-w04",
            data_wall_type=wall["id"],
        )
    )
    glazing = next(
        item for item in model["internal_glazing"] if item["id"] in wall["acoustic_openings"]
    )
    gx = run_x + float(glazing["from"]) * y_scale
    gw = (float(glazing["to"]) - float(glazing["from"])) * y_scale
    parts.extend(
        [
            _rect(
                gx,
                run_y - 5,
                gw,
                run_h + 10,
                fill="#f7e6ca",
                stroke=AMBER,
                stroke_width=7,
                css_class="hall-edge-acoustic-opening",
                data_opening_id=glazing["id"],
            ),
            _line(gx + gw / 2.0, run_y, gx + gw / 2.0, run_y + run_h, stroke="#fff7e8", stroke_width=2),
            _text(gx + gw / 2.0, run_y + 118, "GLZ-DECK", 9, anchor="middle", weight=700, fill=AMBER),
            _text(gx + gw / 2.0, run_y + 142, "ACOUSTIC GLAZING", 6.8, anchor="middle", weight=700, fill=AMBER),
            _text(gx + gw / 2.0, run_y + 165, "ELEVATION TBD", 6.8, anchor="middle", fill=MUTED),
            _line(run_x, 220, run_x + run_w, 220, stroke=TEAL, stroke_width=1.8),
            _line(run_x, 211, run_x, 229, stroke=TEAL, stroke_width=1.8),
            _line(run_x + run_w, 211, run_x + run_w, 229, stroke=TEAL, stroke_width=1.8),
            _text(run_x + run_w / 2.0, 205, "18.00 m CONTINUOUS ENCLOSURE · Y=0.00 TO 18.00", 9.5, anchor="middle", weight=700, fill=TEAL),
            _text(run_x, 555, "Y=0.00 · LOW EAVE", 7.2, weight=700, fill=MUTED),
            _text(run_x + run_w, 555, "Y=18.00 · HIGH EAVE", 7.2, anchor="end", weight=700, fill=MUTED),
            _text(run_x + run_w / 2.0, 590, "OPAQUE PORTIONS: P2-W01 BUILD-UP · 250 mm NOMINAL", 8.5, anchor="middle", weight=700),
            _text(run_x + run_w / 2.0, 614, "FLOOR → COORDINATED ROOF SOFFIT / HEAD · NO OPEN GALLERY", 8.0, anchor="middle", weight=700, fill=GREEN),
        ]
    )

    _panel_title(parts, 930, 165, "02", "SCHEMATIC SECTION AT X=21", width=650)
    parts.extend(
        [
            _rect(980, 490, 560, 22, fill="#c8c1b7", stroke=INK, stroke_width=1.2),
            _text(1515, 538, "P2 FLOOR EDGE", 7.4, anchor="end", weight=700),
            _rect(1100, 255, 32, 235, fill="#d8e7df", stroke=INK, stroke_width=2.0, css_class="p2-w04-section"),
            _line(1116, 255, 1395, 205, stroke=INK, stroke_width=8, stroke_linecap="round"),
            _text(1395, 188, "ROOF / SOFFIT · FINAL SLOPE + DEFLECTION TBD", 7.2, anchor="end", weight=700),
            _line(1116, 270, 995, 405, stroke=AMBER, stroke_width=8, stroke_linecap="round"),
            _line(995, 405, 1116, 455, stroke=AMBER, stroke_width=8, stroke_linecap="round"),
            _line(995, 405, 1116, 375, stroke=AMBER, stroke_width=5, stroke_linecap="round"),
            _text(980, 380, "HALL-SIDE EXPOSED", 7.2, anchor="end", weight=700, fill=AMBER),
            _text(980, 403, "D-052 TRUSS", 8.4, anchor="end", weight=700, fill=AMBER),
            _text(1148, 340, "P2-W04", 9, weight=700, fill=TEAL),
            _text(1148, 365, "FULL HEIGHT", 7.2, weight=700),
            _text(1148, 388, "CONTINUOUS + SEALED", 7.2, weight=700),
            _text(1035, 540, "DOUBLE-HEIGHT HALL / WORKSHOPS", 7.2, anchor="middle", weight=700, fill=AMBER),
            _text(1390, 540, "PRIVATE P2", 7.2, anchor="middle", weight=700, fill=TEAL),
            _text(1260, 585, "Truss expression remains; its supports and connections may not puncture", 7.4, anchor="middle"),
            _text(1260, 606, "or rigidly bridge the acoustic enclosure without an engineered detail.", 7.4, anchor="middle"),
        ]
    )

    _panel_title(parts, 70, 690, "03", "NON-NEGOTIABLE CONTINUITY")
    parts.append(
        _multiline(
            70,
            730,
            [
                "Close the complete X=21 run; no open mezzanine or gallery condition remains.",
                "Seal floor track, lateral returns, head, glazing perimeter and every service penetration.",
                "Keep the twin frames decoupled; do not use truss members, blocking or services as rigid bridges.",
                "At GLZ-DECK, coordinate acoustic seals, edge protection and guard resistance as one system.",
            ],
            8.8,
            leading=1.55,
        )
    )

    _panel_title(parts, 930, 690, "04", "OPEN PROFESSIONAL GATES", width=650)
    parts.append(
        _multiline(
            930,
            730,
            [
                "Structural truss topology, supports, movement and connection strategy.",
                "Roof/head deflection track and full-height fire-stopping detail.",
                "Required fire/smoke separation and tested acoustic performance.",
                "GLZ-DECK glass build-up, frame, guarding, height and installation.",
                "Full-height mock-up and field verification before repetition.",
            ],
            8.5,
            leading=1.52,
            fill=RED,
        )
    )
    parts.append(
        _rect(930, 910, 650, 94, fill="#f5ded8", stroke="#bf7468", stroke_width=1.2, rx=6)
    )
    parts.extend(
        [
            _text(952, 940, "AUTHORITY", 8, weight=700, fill=RED),
            _text(952, 969, "Frozen enclosure intent; no STC/Rw, fire rating or construction assembly is claimed.", 8.2, weight=700, fill="#6f3028"),
        ]
    )

    _footer(parts, model, digest, sheet_id)
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def build_integrated_exterior_wall_detail(model: dict[str, Any]) -> str:
    """Draw the D-080 insulated-shell-plus-lining P2-W05 concept."""

    wall = model["exterior_wall_assembly"]
    report = _report(model)
    _assert_renderable(report)
    digest = hashlib.sha256(
        json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    sheet_id = f"DH-ARQ-DET-005-{model['drawing_revision']}"
    metadata = {
        "drawing": sheet_id,
        "revision": model["revision"],
        "model_sha256": digest,
        "status": model["status"],
        "wall_type": wall["id"],
        "nominal_total_mm": 230,
        "construction_authority": False,
        "thermal_performance_claimed": False,
        "acoustic_rating_claimed": False,
        "fire_rating_claimed": False,
    }
    parts = _svg_start(
        "Dream House P2-W05 integrated 230 mm exterior wall",
        "D-080 concept integrating the industrial insulated facade panel with an independent residential service lining, avoiding a redundant second exterior frame. Not for construction.",
        metadata,
    )
    _header(
        parts,
        model,
        sheet_id,
        "P2-W05 · INTEGRATED INDUSTRIAL SHELL + PRIVATE LINING",
        "D-080 · 230 mm nominal · 100 mm test-value panel, final core 80–120 mm open",
    )

    _panel_title(parts, 70, 165, "01", "OUTSIDE-TO-INSIDE BUILD-UP · 230 mm NOMINAL", width=880)
    x0, y0, height, scale = 115.0, 290.0, 300.0, 2.8
    layer_colors = {
        "insulated corrugated metal facade panel": "#78919a",
        "clear service and decoupling cavity": "#ffffff",
        "metal stud frame with glass-wool infill": "#d8e7df",
        "reclaimed gypsum board": "#d7d2c8",
        "new gypsum board": "#f7f5ef",
    }
    labels = {
        "insulated corrugated metal facade panel": "100 INSULATED CORRUGATED FACADE PANEL · TEST VALUE",
        "clear service and decoupling cavity": "40 CLEAR DRAINABLE / SERVICE / DECOUPLING ZONE",
        "metal stud frame with glass-wool infill": "64 INDEPENDENT SERVICE FRAME + 50 GLASS WOOL",
        "reclaimed gypsum board": "12.5 RECLAIMED BOARD · CONCEALED ONLY",
        "new gypsum board": "12.5 NEW SMOOTH FINISH BOARD",
    }
    cursor = x0
    centres: list[tuple[float, dict[str, Any]]] = []
    for layer in wall["outside_to_inside_layers"]:
        width = float(layer["nominal_mm"]) * scale
        material = layer["material"]
        parts.append(
            _rect(
                cursor,
                y0,
                width,
                height,
                fill=layer_colors[material],
                stroke=INK,
                stroke_width=1.1,
                css_class=f"exterior-wall-layer {material.replace(' ', '-').lower()}",
            )
        )
        if material == "metal stud frame with glass-wool infill":
            for offset in range(10, max(11, int(width)), 19):
                parts.append(
                    _line(
                        cursor + offset,
                        y0 + 8,
                        cursor + min(offset + 13, width - 3),
                        y0 + height - 8,
                        stroke=GREEN,
                        stroke_width=1.0,
                        opacity=0.65,
                    )
                )
        centres.append((cursor + width / 2, layer))
        cursor += width
    parts.extend(
        [
            _line(x0, 246, cursor, 246, stroke=TEAL, stroke_width=1.8),
            _line(x0, 237, x0, 255, stroke=TEAL, stroke_width=1.8),
            _line(cursor, 237, cursor, 255, stroke=TEAL, stroke_width=1.8),
            _text((x0 + cursor) / 2, 230, "230 mm NOMINAL · 229 mm ILLUSTRATIVE SUM", 9.2, anchor="middle", weight=700, fill=TEAL),
            _text(x0 - 20, y0 + height / 2, "OUTSIDE", 8.0, anchor="end", weight=700),
            _text(cursor + 20, y0 + height / 2, "P2 INSIDE", 8.0, weight=700),
        ]
    )
    for index, (_, layer) in enumerate(centres):
        y = 650 + index * 48
        parts.append(_rect(105, y - 15, 16, 16, fill=layer_colors[layer["material"]], stroke=INK, stroke_width=0.8))
        parts.append(_text(137, y, labels[layer["material"]], 7.5, weight=700))

    _panel_title(parts, 1010, 165, "02", "WHY IT IS MORE EFFICIENT", width=570)
    parts.append(
        _multiline(
            1030,
            210,
            [
                "The insulated metal panel is the weather shell.",
                "One independent inner frame carries services and finish.",
                "No redundant outer stud wall is added behind the panel.",
                "Corrugated industrial character remains outside only.",
                "Local column boxes may project beyond 230 mm.",
            ],
            8.3,
            leading=1.58,
        )
    )

    _panel_title(parts, 1010, 430, "03", "DO NOT FREEZE THE 100 mm CORE YET", width=570)
    parts.append(
        _multiline(
            1030,
            475,
            [
                "Choose the 80–120 mm panel after Boyaca climate analysis.",
                "Coordinate condensation, vapour and continuous air control.",
                "Select PIR or mineral-wool core from the fire strategy.",
                "Verify wind spans, fasteners and primary-steel interfaces.",
                "Detail windows, base, eaves, corners and cavity drainage.",
            ],
            8.1,
            leading=1.58,
            fill=RED,
        )
    )

    _panel_title(parts, 1010, 705, "04", "PERIMETER / AUTHORITY", width=570)
    parts.append(
        _multiline(
            1030,
            750,
            [
                "Apply to south, north and rear/east P2 edges.",
                "P2-W04R remains the separate hall-edge wall.",
                "No U-value, fire, acoustic or structural rating is claimed.",
                "Not for product order, fabrication or construction.",
            ],
            8.2,
            leading=1.62,
        )
    )
    parts.append(_rect(1030, 905, 520, 84, fill="#f5ded8", stroke="#bf7468", stroke_width=1.2, rx=6))
    parts.append(_text(1052, 937, "D-080 REPLACES THE FORMER 300 mm DOUBLE-FRAME BASIS", 8.0, weight=700, fill=RED))
    parts.append(_text(1052, 966, "Envelope experience retained; illustrative construction rationalized.", 7.4, fill="#6f3028"))

    _footer(parts, model, digest, sheet_id)
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def build_exterior_wall_detail(model: dict[str, Any]) -> str:
    """Draw the D-059 P2-W05 exterior double-frame envelope concept."""

    if model.get("wall_schedule"):
        return build_integrated_exterior_wall_detail(model)

    wall = model.get("exterior_wall_assembly")
    if not wall:
        raise P2ModelError("Exterior-wall detail requires exterior_wall_assembly data")
    report = _report(model)
    _assert_renderable(report)
    digest = hashlib.sha256(
        json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    sheet_id = f"DH-ARQ-DET-005-{model['drawing_revision']}"
    metadata = {
        "drawing": sheet_id,
        "revision": model["revision"],
        "model_sha256": digest,
        "status": model["status"],
        "wall_type": wall["id"],
        "nominal_total_mm": 300,
        "construction_authority": False,
        "thermal_performance_claimed": False,
        "acoustic_rating_claimed": False,
        "fire_rating_claimed": False,
    }
    parts = _svg_start(
        "Dream House P2-W05 refined double-frame exterior wall",
        "D-059 exterior-envelope concept with corrugated metal outside and a smooth concealed-structure P2 interior. Not for construction.",
        metadata,
    )
    _header(
        parts,
        model,
        sheet_id,
        "P2-W05 · REFINED DOUBLE-FRAME EXTERIOR WALL",
        "D-059 · three exterior P2 edges only · corrugated outside / smooth inside",
    )

    _panel_title(parts, 70, 165, "01", "OUTSIDE-TO-INSIDE BUILD-UP · 300 mm NOMINAL")
    x0, y0, height, mm_scale = 105.0, 265.0, 280.0, 2.0
    layer_colors = {
        "corrugated metal rainscreen": "#66818a",
        "ventilated drainage cavity": "#f7f5ef",
        "weather-resistive barrier and exterior sheathing": "#b9c6c8",
        "outer metal stud frame with glass-wool infill": "#c9ddd5",
        "clear decoupling and service cavity": "#ffffff",
        "inner metal stud frame with glass-wool infill": "#d8e7df",
        "reclaimed gypsum board": "#d7d2c8",
        "new gypsum board": "#f7f5ef",
    }
    short_labels = {
        "corrugated metal rainscreen": "CORRUGATED RAINSCREEN · OUTSIDE ONLY",
        "ventilated drainage cavity": "20 DRAINED / VENTILATED CAVITY",
        "weather-resistive barrier and exterior sheathing": "11 SHEATHING + WATER / AIR LAYER",
        "outer metal stud frame with glass-wool infill": "90 OUTER FRAME + GLASS WOOL",
        "clear decoupling and service cavity": "50 CLEAR SERVICE / DECOUPLING CAVITY",
        "inner metal stud frame with glass-wool infill": "100 INNER FRAME + GLASS WOOL",
        "reclaimed gypsum board": "12.7 RECLAIMED BOARD · CONCEALED",
        "new gypsum board": "12.7 NEW SMOOTH FINISH BOARD",
    }
    cursor = x0
    layer_centres: list[tuple[float, dict[str, Any]]] = []
    for layer in wall["outside_to_inside_layers"]:
        layer_width = float(layer["nominal_mm"]) * mm_scale
        material = layer["material"]
        parts.append(
            _rect(
                cursor,
                y0,
                layer_width,
                height,
                fill=layer_colors[material],
                stroke=INK,
                stroke_width=1.1,
                css_class=f"exterior-wall-layer {material.replace(' ', '-').lower()}",
            )
        )
        if "glass-wool" in material:
            for offset in range(12, int(layer_width), 22):
                parts.append(
                    _line(
                        cursor + offset,
                        y0 + 8,
                        cursor + min(offset + 15, layer_width - 4),
                        y0 + height - 8,
                        stroke=GREEN,
                        stroke_width=1.0,
                        opacity=0.65,
                    )
                )
        layer_centres.append((cursor + layer_width / 2.0, layer))
        cursor += layer_width

    parts.extend(
        [
            _line(x0, 225, cursor, 225, stroke=TEAL, stroke_width=1.8),
            _line(x0, 216, x0, 234, stroke=TEAL, stroke_width=1.8),
            _line(cursor, 216, cursor, 234, stroke=TEAL, stroke_width=1.8),
            _text(
                (x0 + cursor) / 2.0,
                210,
                "300 mm NOMINAL · 297 mm ILLUSTRATIVE LAYER SUM",
                9.5,
                anchor="middle",
                weight=700,
                fill=TEAL,
            ),
            _text(x0 - 18, y0 + height / 2.0, "OUTSIDE", 8.5, anchor="end", weight=700),
            _text(cursor + 18, y0 + height / 2.0, "P2 INSIDE", 8.5, weight=700),
        ]
    )
    for index, (_, layer) in enumerate(layer_centres):
        row = 245 + index * 43
        parts.extend(
            [
                _text(772, row, str(index + 1), 7.0, anchor="end", weight=700, fill=TEAL),
                _rect(
                    784,
                    row - 11,
                    13,
                    13,
                    fill=layer_colors[layer["material"]],
                    stroke=INK,
                    stroke_width=0.7,
                ),
                _text(810, row, short_labels[layer["material"]], 7.3, weight=700),
            ]
        )

    _panel_title(parts, 70, 660, "02", "P2 PERIMETER APPLICATION", width=430)
    px, py, pw, ph = 110.0, 720.0, 300.0, 220.0
    parts.extend(
        [
            _rect(px, py, pw, ph, fill="#eef1ed", stroke="#90a0a5", stroke_width=1.0),
            _line(px, py, px + pw, py, stroke="#36535d", stroke_width=11),
            _line(px, py + ph, px + pw, py + ph, stroke="#36535d", stroke_width=11),
            _line(px + pw, py, px + pw, py + ph, stroke="#36535d", stroke_width=11),
            _line(px, py, px, py + ph, stroke=INK, stroke_width=9),
            _text(px + pw / 2.0, py - 20, "NORTH · P2-W05", 7.4, anchor="middle", weight=700),
            _text(px + pw / 2.0, py + ph + 26, "SOUTH · P2-W05", 7.4, anchor="middle", weight=700),
            _text(px + pw + 18, py + ph / 2.0, "REAR / EAST · P2-W05", 7.0, weight=700),
            _text(px - 18, py + ph / 2.0, "HALL · P2-W04", 7.0, anchor="end", weight=700),
            _text(px + pw / 2.0, py + ph / 2.0, "PRIVATE P2", 11, anchor="middle", weight=700, fill=TEAL),
        ]
    )

    _panel_title(parts, 540, 660, "03", "EXPRESSION RULE", width=480)
    parts.extend(
        [
            _rect(570, 720, 190, 150, fill="#d9e0e1", stroke=INK, stroke_width=1.2),
            _rect(800, 720, 190, 150, fill="#fbfaf6", stroke=INK, stroke_width=1.2),
            *[
                _line(580 + offset, 728, 580 + offset, 862, stroke="#78919a", stroke_width=3)
                for offset in range(0, 180, 16)
            ],
            _text(665, 895, "OUTSIDE", 8, anchor="middle", weight=700, fill=MUTED),
            _text(665, 918, "economical corrugated rainscreen", 7.0, anchor="middle"),
            _text(895, 895, "P2 INSIDE", 8, anchor="middle", weight=700, fill=TEAL),
            _text(895, 918, "smooth, quiet, domestic finish", 7.0, anchor="middle"),
            _text(895, 946, "NO VISIBLE SHEET / FRAME / STEEL / SERVICES", 6.8, anchor="middle", weight=700, fill=GREEN),
        ]
    )

    _panel_title(parts, 1080, 660, "04", "OPEN PROFESSIONAL GATES", width=500)
    parts.append(
        _multiline(
            1080,
            705,
            [
                "Climate-specific condensation and vapour-control analysis.",
                "Wind resistance, studs, sheathing, anchors and primary-steel interfaces.",
                "Window heads, sills, reveals, drainage and continuous air seals.",
                "Roof/eave, slab edge, corners, flashings and thermal bridges.",
                "Fire, cavity barriers, combustibility and full-height mock-up.",
            ],
            8.2,
            leading=1.55,
            fill=RED,
        )
    )
    parts.append(
        _rect(1080, 895, 500, 96, fill="#f5ded8", stroke="#bf7468", stroke_width=1.2, rx=6)
    )
    parts.extend(
        [
            _text(1102, 925, "AUTHORITY", 8, weight=700, fill=RED),
            _text(1102, 954, "Envelope principle frozen; no U-value, STC/Rw or fire rating is claimed.", 7.6, weight=700, fill="#6f3028"),
            _text(1102, 975, "Not for product order, fabrication or construction.", 7.6, fill="#6f3028"),
        ]
    )

    _footer(parts, model, digest, sheet_id)
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def generate(
    model: dict[str, Any] | None = None,
    out_dir: Path = OUT,
    *,
    source_path: Path = DATA,
    generator_name: str = "dreamhouse/generate_p2_b09.py",
) -> dict[str, Any]:
    model = load_model() if model is None else model
    report = _report(model)
    _assert_renderable(report)
    plan_name, access_name, detail_name = output_names(model)
    outputs = {
        plan_name: build_plan(model, report),
        access_name: build_access_diagram(model, report),
    }
    if detail_name:
        outputs[detail_name] = build_owner_priorities_detail(model)
    partition_detail = acoustic_detail_name(model)
    if partition_detail:
        outputs[partition_detail] = build_acoustic_partition_detail(model)
    hall_detail = hall_edge_detail_name(model)
    if hall_detail:
        outputs[hall_detail] = build_hall_edge_detail(model)
    exterior_detail = exterior_wall_detail_name(model)
    if exterior_detail:
        outputs[exterior_detail] = build_exterior_wall_detail(model)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        out_dir.joinpath(name).write_text(content, encoding="utf-8")
    out_dir.joinpath("compliance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "revision": model["revision"],
        "status": model["status"],
        "source": f"dreamhouse/{source_path.name}",
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "generator": generator_name,
        "supersedes": model["supersedes"],
        "outputs": [*outputs, "compliance.json", "manifest.json"],
    }
    if model.get("stair_core") and model.get("stair_core_source"):
        shared_source = ROOT / model["stair_core_source"]
        manifest["shared_stair_source"] = model["stair_core_source"]
        manifest["shared_stair_sha256"] = hashlib.sha256(shared_source.read_bytes()).hexdigest()
    out_dir.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    report = generate()
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

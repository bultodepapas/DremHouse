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
    if "vertical" in kinds:
        return "P2-W03", float(model["envelope"]["wet_wall"]), PURPLE, "7 4"
    if kinds & {"bath", "wellness"}:
        return "P2-W02", float(model["envelope"]["wet_wall"]), AMBER, "5 3"
    return "P2-W01", float(model["envelope"]["partition"]), INK, None


def net_dimensions(space: dict[str, Any], envelope: dict[str, Any]) -> tuple[float, float]:
    """Return schematic clear dimensions using half-partition allocation."""

    tolerance = 1e-9
    ext = float(envelope["exterior_wall"])
    half = _wall_thickness(space, envelope) / 2.0
    x0 = float(space["x"])
    x1 = x0 + float(space["w"])
    y0 = float(space["y"])
    y1 = y0 + float(space["d"])
    x_min = float(envelope["x"])
    x_max = x_min + float(envelope["length"])
    y_max = float(envelope["width"])
    dx0 = ext if math.isclose(x0, x_min, abs_tol=tolerance) else half
    dx1 = ext if math.isclose(x1, x_max, abs_tol=tolerance) else half
    dy0 = ext if math.isclose(y0, 0.0, abs_tol=tolerance) else half
    dy1 = ext if math.isclose(y1, y_max, abs_tol=tolerance) else half
    return max(0.0, float(space["w"]) - dx0 - dx1), max(
        0.0, float(space["d"]) - dy0 - dy1
    )


def net_area(space: dict[str, Any], envelope: dict[str, Any]) -> float:
    width, depth = net_dimensions(space, envelope)
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

    n1 = net_area(by_id["H1-D"], envelope)
    n2 = net_area(by_id["H2-D"], envelope)
    dims1 = net_dimensions(by_id["H1-D"], envelope)
    dims2 = net_dimensions(by_id["H2-D"], envelope)
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
        (min(net_dimensions(space, envelope)), space["id"]) for space in circulation
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
    wellness_gross = by_id["WELL"]["w"] * by_id["WELL"]["d"]
    checks.append(
        (
            "P2-WELLNESS",
            16.0 <= wellness_gross <= 22.0
            and min(net_dimensions(by_id["WELL"], envelope)) >= 2.40 - tolerance,
            f"Wellness is {wellness_gross:.1f} m2 gross and fits a 2.40 m sauna",
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
                "Rear-facade retractable stair reserve is reached directly from the Phase 2 lobby and clears the D-048 corner",
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
                "X=21 architectural brief requires one large exposed industrial truss while protecting the mini-deck view",
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
            acoustic.get("id") == "P2-W01"
            and math.isclose(float(acoustic.get("nominal_total_m", 0.0)), 0.25, abs_tol=tolerance)
            and math.isclose(float(envelope["partition"]), 0.25, abs_tol=tolerance)
            and math.isclose(layer_sum_mm, 250.8, abs_tol=0.01)
            and len(reused) == 2
            and len(new) == 2
            and len(frames) == 2
            and all(math.isclose(float(frame.get("infill_nominal_mm", 0.0)), 50.0) for frame in frames)
            and len(acoustic.get("exclusions", [])) >= 4
        )
        checks.append(
            (
                "P2-W01-250",
                acoustic_ok,
                "D-057 P2-W01 is 250 mm nominal: two independent insulated frames, two concealed reclaimed boards and two new finish boards",
            )
        )

    results = [
        {"rule_id": rule_id, "status": "PASS" if passed else "FAIL", "message": message}
        for rule_id, passed, message in checks
    ]
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
    primary_ok = primary_bath >= 17.0 and primary_closet >= 15.0
    results.extend(
        [
            {
                "rule_id": "P2-PRIMARY-PROGRAMME",
                "status": "PASS" if primary_ok else "OPEN",
                "message": (
                    f"Primary bathroom {primary_bath:.1f} m2 and dressing room "
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
                    "The large exposed X=21 truss must preserve the mini-deck view; members, joints, fire protection and services remain undesigned"
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
    x = _sx(space["x"] + space["w"] / 2.0)
    y = _sy(space["y"] + space["d"] / 2.0)
    pixel_width = space["w"] * SCALE
    pixel_height = space["d"] * SCALE
    size = min(9.0, max(5.2, pixel_width / 18.0))
    if pixel_height < 70:
        size = min(size, 6.4)
    label_width = max(8, int(pixel_width / max(1.0, size * 0.58)))
    name_lines = textwrap.wrap(space["name"].replace(" / ", " "), width=label_width)
    lines = name_lines + [f"{net_area(space, model['envelope']):.1f} m2 net"]
    if pixel_height >= 90 and pixel_width >= 80:
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
    deck = by_id["DECK"]
    for offset in (0.45, 1.55):
        parts.append(
            _rect(
                _sx(deck["x"] + offset),
                _sy(deck["y"] + 2.45),
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


def _draw_bath_fixtures(parts: list[str], model: dict[str, Any]) -> None:
    by_id = _space_index(model)
    room_ids = [room_id for room_id in ("H1-B", "H2-B", "G-B", "M-B", "M-B-A") if room_id in by_id]
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


def _draw_stair(parts: list[str]) -> None:
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
    for window in model["windows"]:
        if window["edge"] in {"south", "north"}:
            y = _sy(0.0 if window["edge"] == "south" else 18.0)
            x0, x1 = _sx(window["from"]), _sx(window["to"])
            parts.append(_line(x0, y, x1, y, stroke=TEAL, stroke_width=8, css_class="exterior-window"))
            parts.append(_line(x0, y, x1, y, stroke="#d9f2f5", stroke_width=2, css_class="window-glass"))
        else:
            x = _sx(36.0)
            y0, y1 = _sy(window["from"]), _sy(window["to"])
            parts.append(_line(x, y0, x, y1, stroke=TEAL, stroke_width=8, css_class="exterior-window"))
            parts.append(_line(x, y0, x, y1, stroke="#d9f2f5", stroke_width=2, css_class="window-glass"))
    for glazing in model["internal_glazing"]:
        x = _sx(21.0)
        y0, y1 = _sy(glazing["from"]), _sy(glazing["to"])
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
            _line(x, y0, x, y1, stroke=PAPER, stroke_width=7, css_class="egress-door-opening"),
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
            _text(left, top - 18, "LATERAL B / HIGH EAVE STUDY", 7.5, weight=700, fill=MUTED),
            _text(left, bottom + 22, "LATERAL A / LOW EAVE STUDY", 7.5, weight=700, fill=MUTED),
            _text(left - 2, (top + bottom) / 2 - 6, "P2 EDGE / DOUBLE-HEIGHT VOID", 7, anchor="middle", weight=700, fill=AMBER),
            _text(right + 12, (top + bottom) / 2, "REAR FACADE", 7, anchor="middle", weight=700, fill=MUTED),
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
    position_lines = (
        [
            "Prioritize the primary suite without enlarging P2.",
            "Move laundry into PB storage behind the Great Wall.",
            "Protect the view while allowing one large exposed industrial truss.",
            *(["Coordinate dry P2 partitions at 250 mm nominal under D-057."] if acoustic else []),
        ]
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
    child_delta = abs(net_area(by_id["H1-D"], envelope) - net_area(by_id["H2-D"], envelope))
    fixes = (
        [
            ("PRIMARY", "Bathroom 17.6 m2 + dressing/filter 17.6 m2 meet the brief."),
            ("LAUNDRY", "Washer, dryer and sink move to PB storage behind the Great Wall."),
            ("EGRESS", "A theft-resistant retractable exterior-stair envelope is reserved."),
            ("VIEW", "Mini-deck sightline governs the single large X=21 truss."),
            ("STRUCTURE", "Four D-048 column reservations remain at stair corners."),
            *(
                [
                    (
                        "P2-W01",
                        "250 mm nominal dry wall: twin insulated frames + reused concealed board.",
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
        ("Wellness", by_id["WELL"]["w"] * by_id["WELL"]["d"]),
    ]
    for index, (label, area) in enumerate(rows):
        y = 692 + index * 30
        parts.append(_text(x, y, label, 8.3))
        parts.append(_text(x + 360, y, f"{area:.1f} m2", 8.3, anchor="end", weight=700))
        parts.append(_line(x + 380, y - 4, x + 520, y - 4, stroke="#d0d6d7", stroke_width=1))

    _panel_title(parts, x, 895, "04", "OPEN DESIGN GATES")
    open_items = [item for item in report["checks"] if item["status"] == "OPEN"]
    for index, item in enumerate(open_items):
        y = 928 + index * 27
        parts.append(_circle_status(x + 7, y - 3, RED))
        parts.append(_text(x + 24, y, item["message"], 7.5))

    parts.extend(
        [
            _line(1320, 657, 1320, 858, stroke="#c3ccce", stroke_width=1),
            _text(1350, 684, "LEGEND", 9, weight=700),
            _line(1350, 712, 1402, 712, stroke=TEAL, stroke_width=7),
            _text(1415, 715, "exterior glazing", 7.5),
            _line(1350, 740, 1402, 740, stroke=AMBER, stroke_width=7),
            _text(1415, 743, "acoustic deck glazing", 7.5),
            _rect(1350, 758, 12, 12, fill="#fff", stroke=PURPLE, stroke_width=2),
            _text(1374, 769, "D-048 column reserve", 7.5),
            _line(1350, 793, 1402, 793, stroke=PURPLE, stroke_width=3, stroke_dasharray="8 5"),
            _text(1415, 796, "F1 / F2 boundary", 7.5),
            *(
                [
                    _line(1350, 820, 1402, 820, stroke=INK, stroke_width=8.3),
                    _text(1415, 823, "P2-W01 · 250 mm nominal", 7.5),
                    _text(
                        1350,
                        848,
                        "Wet/hot, exterior, stair and technical walls remain separate.",
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
        "D-057 · 250 mm P2 DRY ACOUSTIC PARTITION · DESIGN COORDINATION"
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
            "An upper-floor revision prioritizing the primary suite, relocating laundry to PB and reserving a retractable exterior stair. Not for construction."
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
            "D-057 wall control + primary-suite priority + active interfaces"
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
    _draw_stair(parts)
    _draw_partition_walls(parts, model)
    _draw_room_labels(parts, model)
    _draw_windows(parts, model)
    _draw_egress_reserve(parts, model)
    phase_y = _sy(model["phase_boundary_y"])
    parts.append(_line(_sx(21), phase_y, _sx(36), phase_y, stroke=PURPLE, stroke_width=3, stroke_dasharray="9 6", css_class="phase-boundary"))
    parts.append(_text((_sx(21) + _sx(36)) / 2, phase_y - 8, "ONE ISOLATABLE F1 / F2 BOUNDARY", 7.4, anchor="middle", weight=700, fill=PURPLE))
    for door in model["doors"]:
        _draw_door(parts, door, model)
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

    route_ids = {
        "H1-D": (
            ["H1-D", "FAM", "HALL-A", "HALL-C", "ARR", "ESC"]
            if "HALL-A" in by_id
            else ["H1-D", "DECK", "FAM", "HALL-C", "ARR", "ESC"]
        ),
        "M-D": (
            ["M-D", "M-PASS", "ARR", "ESC"]
            if "M-PASS" in by_id
            else ["M-D", "M-C", "ARR", "ESC"]
        ),
        "H2-D": ["H2-D", "F2-HALL", "HALL-C", "ARR", "ESC"],
        "G-D": ["G-D", "G-ENTRY", "F2-HALL", "HALL-C", "ARR", "ESC"],
        "WELL": ["WELL", "F2-HALL", "HALL-C", "ARR", "ESC"],
    }
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
                    "The Phase 2 lobby also reaches a reserved rear retractable stair.",
                    "That exterior device is a geometric reserve, not an approved exit.",
                    "The main stair still arrives in a shared protected lobby.",
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
        "PB laundry + retractable stair + large exposed X=21 truss",
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
                "Access is directly from the common Phase 2 lobby, not through a bedroom.",
                "Required study: counterbalanced/manual fail-safe deployment without a key from inside.",
                "Do not count as a compliant second exit until fire, egress, accessibility and rescue review.",
            ],
            8.4,
            leading=1.45,
        )
    )

    _panel_title(parts, 70, 790, "03", "X=21 EDGE · ONE LARGE INDUSTRIAL TRUSS")
    tx0, tx1, top_y, bottom_y = 105.0, 740.0, 845.0, 965.0
    parts.extend(
        [
            _line(tx0, top_y, tx1, top_y, stroke=INK, stroke_width=9),
            _line(tx0, bottom_y, tx1, bottom_y, stroke=INK, stroke_width=9),
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
                    "The mini-deck view remains primary; member topology, depth, joints, fire",
                    "protection, vibration and services still require structural coordination.",
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


def build_acoustic_partition_detail(model: dict[str, Any]) -> str:
    """Draw the D-057 P2-W01 coordination build-up and its limits of authority."""

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
        "D-057 design control · dry interior P2 walls only",
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
    parts.append(
        _multiline(
            1010,
            205,
            [
                "Two independent frames provide the primary decoupling.",
                "Glass wool fills each frame; the central cavity stays clear.",
                "Reclaimed board adds concealed mass where appearance is irrelevant.",
                "New outer boards provide the durable visible finish.",
                "No third gypsum leaf is placed in the centre cavity.",
            ],
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
    out_dir.joinpath("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    report = generate()
    print(json.dumps({key: report[key] for key in ("passed", "open", "failed")}))


if __name__ == "__main__":
    main()

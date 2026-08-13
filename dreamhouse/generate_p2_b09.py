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
            "All 23 doors/openings lie on the boundaries they connect"
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

    results = [
        {"rule_id": rule_id, "status": "PASS" if passed else "FAIL", "message": message}
        for rule_id, passed, message in checks
    ]
    primary_bath = by_id["M-B"]["w"] * by_id["M-B"]["d"]
    primary_closet = by_id["M-C"]["w"] * by_id["M-C"]["d"]
    results.extend(
        [
            {
                "rule_id": "P2-PRIMARY-PROGRAMME",
                "status": "OPEN",
                "message": (
                    f"Primary bathroom {primary_bath:.1f} m2 and dressing room "
                    f"{primary_closet:.1f} m2 remain below the original 17-18 and 15-16 m2 targets"
                ),
            },
            {
                "rule_id": "LIFE-EGRESS-2",
                "status": "OPEN",
                "message": "Second independent P2 exit awaits D-021 occupancy and fire review",
            },
            {
                "rule_id": "P2-EDGE-TRUSS",
                "status": "OPEN",
                "message": "The X=21 edge truss must preserve the mini-deck view, doors, ceiling and services",
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

    laundry = by_id["LAV"]
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
    for room_id in ("H1-B", "H2-B", "G-B", "M-B"):
        room = by_id[room_id]
        clear_x = room["x"] + 0.16
        clear_y = room["y"] + 0.16
        shower = 1.0 if room_id != "M-B" else 1.25
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
        vanity_w = min(1.6 if room_id == "M-B" else 0.95, room["w"] - 0.35)
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


def _draw_door(parts: list[str], door: dict[str, Any]) -> None:
    width_px = float(door["width"]) * SCALE
    common = {"stroke": "#965039", "stroke_width": 1.3, "fill": "none", "css_class": "door"}
    if door["wall"] == "horizontal":
        x0 = _sx(float(door["at"]))
        y = _sy(float(door["y"]))
        x1 = x0 + width_px
        parts.append(_line(x0 - 1, y, x1 + 1, y, stroke=PAPER, stroke_width=5.5, css_class="door-opening"))
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
        parts.append(_line(x, y0 + 1, x, y1 - 1, stroke=PAPER, stroke_width=5.5, css_class="door-opening"))
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


def _panel_title(parts: list[str], x: float, y: float, number: str, title: str) -> None:
    parts.extend(
        [
            _text(x, y, number, 9, weight=700, fill=TEAL),
            _text(x + 34, y, title, 12, weight=700),
            _line(x, y + 11, x + 780, y + 11, stroke="#c3ccce", stroke_width=1),
        ]
    )


def _right_notes(parts: list[str], model: dict[str, Any], report: dict[str, Any]) -> None:
    x = 785.0
    _panel_title(parts, x, 166, "01", "ARCHITECTURAL POSITION")
    parts.append(
        _multiline(
            x,
            198,
            [
                "Carry forward the spatial centre of b04/R03.",
                "Retain the verified dimensional corrections of b06/R05.",
                "The previous R05 remains superseded, not erased.",
            ],
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
    fixes = [
        ("ACCESS", "23 doors/openings are located and checked against shared walls."),
        ("CENTRE", "Mini deck -> family lounge -> gallery -> protected arrival."),
        ("CHILDREN", f"Net-bedroom difference {child_delta:.2f} m2 under D-042."),
        ("PHASING", "One 1.25 m clear isolatable Phase 2 lobby."),
        ("STRUCTURE", "Four D-048 column reservations retained at stair corners."),
    ]
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
            _text(1350, 830, "All dimensions are schematic coordination values.", 7.2, fill=MUTED),
            _text(1350, 848, "Wall build-ups and structure remain subject to design.", 7.2, fill=MUTED),
        ]
    )


def _circle_status(x: float, y: float, color: str) -> str:
    return f'<circle cx="{x}" cy="{y}" r="5" fill="{color}" opacity="0.85"/>'


def _footer(parts: list[str], model: dict[str, Any], digest: str, sheet_id: str) -> None:
    parts.extend(
        [
            _rect(36, 1060, 1612, 106, fill=INK),
            _rect(36, 1060, 1612, 7, fill=TEAL),
            _text(56, 1092, "CONTROLLED OUTCOME", 8, weight=700, fill="#9fc4cc"),
            _text(56, 1120, "b04 SPATIAL LOGIC · b06 VERIFIED CORRECTIONS · EXPLICIT ACCESS", 13, weight=700, fill="#ffffff"),
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
    metadata = {
        "drawing": "DH-ARQ-PLN-002-R08",
        "revision": model["revision"],
        "model_sha256": digest,
        "status": model["status"],
        "construction_authority": False,
    }
    parts = _svg_start(
        "Dream House coordinated upper-floor plan",
        "A b04-led upper-floor revision with explicit access, b06 dimensional corrections and D-048 stair-column reservations. Not for construction.",
        metadata,
    )
    _header(
        parts,
        model,
        "DH-ARQ-PLN-002-R08",
        "COORDINATED UPPER FLOOR · SCHEMATIC DESIGN",
        "b04 spatial logic + b06 controls + D-048 coordination",
    )
    parts.append(_text(72, 165, "P2 PLAN · 18.00 x 15.00 m · +3.80 m STUDY LEVEL", 12, weight=700))
    parts.append(_text(72, 188, "FRONT / DOUBLE HEIGHT", 7.5, weight=700, fill=AMBER))
    parts.append(_text(672, 188, "REAR CORE", 7.5, anchor="end", weight=700, fill=MUTED))
    _draw_rooms(parts, model)
    _draw_furniture(parts, model)
    _draw_bath_fixtures(parts, model)
    _draw_stair(parts)
    _draw_room_labels(parts, model)
    _draw_windows(parts, model)
    phase_y = _sy(model["phase_boundary_y"])
    parts.append(_line(_sx(21), phase_y, _sx(36), phase_y, stroke=PURPLE, stroke_width=3, stroke_dasharray="9 6", css_class="phase-boundary"))
    parts.append(_text((_sx(21) + _sx(36)) / 2, phase_y - 8, "ONE ISOLATABLE F1 / F2 BOUNDARY", 7.4, anchor="middle", weight=700, fill=PURPLE))
    for door in model["doors"]:
        _draw_door(parts, door)
    _draw_columns(parts, model)
    _draw_plan_dimensions(parts, model)
    _right_notes(parts, model, report)
    _footer(parts, model, digest, "DH-ARQ-PLN-002-R08")
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
    metadata = {
        "drawing": "DH-ARQ-DIA-001-R08",
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
        "DH-ARQ-DIA-001-R08",
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
        "H1-D": ["H1-D", "FAM", "HALL-A", "HALL-C", "ARR", "ESC"],
        "M-D": ["M-D", "M-PASS", "ARR", "ESC"],
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

    phase_y = _sy(model["phase_boundary_y"], bottom=bottom, scale=scale)
    parts.append(_line(origin, phase_y, origin + 15 * scale, phase_y, stroke=PURPLE, stroke_width=3, stroke_dasharray="9 6"))
    _panel_title(parts, 760, 176, "01", "VERIFIED ACCESS TOPOLOGY")
    parts.append(
        _multiline(
            760,
            213,
            [
                "Every enclosed room reaches ESC through a declared door/opening.",
                "Suite filters prevent bathroom doors from becoming suite entrances.",
                "The stair arrives in a shared protected lobby, not inside the primary suite.",
                "The mini deck remains acoustically enclosed from the double-height hall.",
            ],
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
                "The arrows converge on the only stair currently represented.",
                "This diagram does not validate travel distance, occupant load, fire rating,",
                "smoke control, accessibility or the required number of exits.",
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
    _footer(parts, model, digest, "DH-ARQ-DIA-001-R08")
    parts.append("</svg>\n")
    output = "".join(parts)
    ET.fromstring(output)
    return output


def generate(model: dict[str, Any] | None = None, out_dir: Path = OUT) -> dict[str, Any]:
    model = load_model() if model is None else model
    report = _report(model)
    _assert_renderable(report)
    outputs = {
        PLAN_NAME: build_plan(model, report),
        ACCESS_NAME: build_access_diagram(model, report),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        out_dir.joinpath(name).write_text(content, encoding="utf-8")
    out_dir.joinpath("compliance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    manifest = {
        "revision": model["revision"],
        "status": model["status"],
        "source": "dreamhouse/p2_b09.json",
        "source_sha256": hashlib.sha256(DATA.read_bytes()).hexdigest(),
        "generator": "dreamhouse/generate_p2_b09.py",
        "supersedes": model["supersedes"],
        "outputs": [PLAN_NAME, ACCESS_NAME, "compliance.json", "manifest.json"],
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

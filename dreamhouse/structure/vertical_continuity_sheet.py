"""Generate the D-048 vertical-continuity and stair-enclosure study sheet."""

from __future__ import annotations

import html
import json
from itertools import pairwise
from typing import Any

from . import e1_sheet as svg

SHEET_NAME = "DH-EST-E1-002_CONTINUIDAD-VERTICAL-ESCALERA.svg"
SHEET_ID = "DH-EST-E1-002"
SHEET_REVISION = "R00"


def _draw_header(parts: list[str], results: dict[str, Any]) -> None:
    continuity = results["checks"]["vertical_continuity_and_stair_core"]
    parts.extend(
        [
            svg._rect(0, 0, svg.WIDTH, 98, fill=svg.INK),
            svg._rect(0, 98, svg.WIDTH, 6, fill=svg.PURPLE),
            svg._text(
                40,
                42,
                "VERTICAL CONTINUITY + STAIR-ENCLOSURE FRAME",
                24,
                weight=700,
                fill="#ffffff",
            ),
            svg._text(
                40,
                70,
                (
                    f"D-048 geometry screen · {continuity['existing_great_wall_columns_reused']} "
                    "existing Great Wall lines + "
                    f"{continuity['new_rear_columns_required']} new rear lines"
                ),
                11,
                fill="#d8d0e5",
            ),
            svg._rect(1307, 24, 337, 47, rx=6, fill=svg.RED),
            svg._text(
                1475.5,
                45,
                "GEOMETRY HYPOTHESIS",
                12,
                anchor="middle",
                weight=700,
                fill="#ffffff",
            ),
            svg._text(
                1475.5,
                62,
                "NOT FOR CONSTRUCTION",
                10,
                anchor="middle",
                weight=700,
                fill="#ffffff",
            ),
        ]
    )


def _draw_plan_audit(
    parts: list[str],
    pb: dict[str, Any],
    p2: dict[str, Any],
    results: dict[str, Any],
) -> None:
    svg._panel(parts, 40, 120, 950, 535, "01  P2 PLAN AUDIT · COLUMN LINES AND CONFLICTS")
    continuity = results["checks"]["vertical_continuity_and_stair_core"]
    compatible_ids = set(continuity["compatible_column_ids"])
    x_min = float(p2["envelope"]["x"])
    length = float(p2["envelope"]["length"])
    width = float(p2["envelope"]["width"])
    x0, plan_bottom, scale = 78.0, 620.0, 25.0

    def sx(value: float) -> float:
        return x0 + (value - x_min) * scale

    def sy(value: float) -> float:
        return plan_bottom - value * scale

    parts.append('<g id="p2-column-audit">')
    for space in p2["spaces"]:
        is_stair = space["id"] == "ESC"
        parts.append(
            svg._rect(
                sx(float(space["x"])),
                sy(float(space["y"]) + float(space["d"])),
                float(space["w"]) * scale,
                float(space["d"]) * scale,
                fill=svg.PURPLE if is_stair else svg.BLUE,
                opacity=0.15 if is_stair else 0.06,
                stroke=svg.PURPLE if is_stair else svg.GRID,
                stroke_width=2 if is_stair else 0.8,
                class_="p2-space",
            )
        )
        if float(space["w"]) >= 2.4 and float(space["d"]) >= 1.4:
            parts.append(
                svg._text(
                    sx(float(space["x"]) + float(space["w"]) / 2),
                    sy(float(space["y"]) + float(space["d"]) / 2) + 3,
                    space["id"],
                    6.5,
                    anchor="middle",
                    weight=700,
                    fill=svg.PURPLE if is_stair else svg.MUTED,
                )
            )

    for window in p2.get("windows", []):
        start = float(window["from"])
        end = float(window["to"])
        edge = window["edge"]
        if edge == "south":
            coords = (sx(start), sy(0), sx(end), sy(0))
        elif edge == "north":
            coords = (sx(start), sy(width), sx(end), sy(width))
        elif edge == "east":
            coords = (sx(x_min + length), sy(start), sx(x_min + length), sy(end))
        else:
            continue
        parts.append(
            svg._line(
                *coords,
                stroke="#65a9b8",
                stroke_width=7,
                opacity=0.72,
                class_="p2-window",
            )
        )

    # PB openings are projected onto the two enclosure faces to prevent a false
    # assumption that the four-column box can simply receive full X-bracing.
    stair_room = next(room for room in pb["core"] if room["id"] == "ESC")
    front_start = float(stair_room["door_y"]) - 0.10
    front_end = front_start + float(stair_room["door_width"])
    parts.append(
        svg._line(
            sx(float(p2["envelope"]["x"]) + length - 4.5),
            sy(front_start),
            sx(float(p2["envelope"]["x"]) + length - 4.5),
            sy(front_end),
            stroke=svg.AMBER,
            stroke_width=8,
            class_="stair-opening",
        )
    )
    rear_door = next(door for door in pb["exterior_doors"] if door["id"] == "EXT-ESC")
    rear_start = float(rear_door["y"]) - float(rear_door["width"]) / 2
    rear_end = rear_start + float(rear_door["width"])
    parts.append(
        svg._line(
            sx(x_min + length),
            sy(rear_start),
            sx(x_min + length),
            sy(rear_end),
            stroke=svg.AMBER,
            stroke_width=8,
            class_="stair-opening",
        )
    )

    parts.append(
        svg._rect(
            sx(x_min),
            sy(width),
            length * scale,
            width * scale,
            fill="none",
            stroke=svg.INK,
            stroke_width=2.5,
        )
    )
    for candidate in continuity["candidates"]:
        x = sx(float(candidate["x_m"]))
        y = sy(float(candidate["y_m"]))
        if candidate["id"] in compatible_ids:
            parts.append(
                svg._rect(
                    x - 7,
                    y - 7,
                    14,
                    14,
                    rx=2,
                    fill=svg.PURPLE,
                    stroke="#ffffff",
                    stroke_width=1.5,
                    class_="full-height-core-column",
                )
            )
        else:
            parts.append(
                svg._circle(
                    x,
                    y,
                    7,
                    fill="#ffffff",
                    stroke=svg.RED,
                    stroke_width=2,
                    class_="rejected-column-line",
                )
            )
            parts.append(svg._line(x - 4, y - 4, x + 4, y + 4, stroke=svg.RED, stroke_width=1.5))
            parts.append(svg._line(x - 4, y + 4, x + 4, y - 4, stroke=svg.RED, stroke_width=1.5))

    parts.append(svg._text(sx(33.75), sy(9.2), "ESC 4.50 × 3.60 m", 7, anchor="middle", weight=700, fill=svg.PURPLE))
    parts.append(svg._text(sx(31.5) - 12, sy(9.2), "GREAT WALL X=31.50", 6.5, anchor="middle", fill=svg.MUTED, rotate=-90))
    parts.append(svg._text(sx(36) + 13, sy(9.2), "REAR X=36.00", 6.5, anchor="middle", fill=svg.MUTED, rotate=-90))
    parts.append("</g>")

    matrix_x = 493.0
    parts.append(svg._text(matrix_x, 187, "DETERMINISTIC CANDIDATE MATRIX", 9, weight=700))
    parts.append(svg._text(matrix_x, 205, "■ compatible  × rejected", 7.5, fill=svg.MUTED))
    row_y = 224.0
    for index, candidate in enumerate(continuity["candidates"]):
        y = row_y + index * 43
        compatible = candidate["id"] in compatible_ids
        color = svg.PURPLE if compatible else svg.RED
        finding = "clear stair corner"
        if candidate["rejection_reasons"]:
            finding = candidate["rejection_reasons"][-1].replace("_", " ").replace(":", ": ")
        parts.append(svg._rect(matrix_x, y - 14, 438, 33, rx=4, fill=color, opacity=0.06))
        parts.append(svg._text(matrix_x + 10, y, "■" if compatible else "×", 10, weight=700, fill=color))
        parts.append(svg._text(matrix_x + 28, y, candidate["id"], 7.7, weight=700))
        parts.append(
            svg._text(
                matrix_x + 150,
                y,
                f"({candidate['x_m']:.1f}, {candidate['y_m']:.1f})",
                7.2,
                fill=svg.MUTED,
            )
        )
        parts.append(svg._text(matrix_x + 235, y, finding, 6.9, fill=color))
        source = "reuse" if candidate["existing_to_p2"] else "new"
        parts.append(svg._text(matrix_x + 415, y, source.upper(), 6.5, anchor="end", weight=700, fill=color))

    parts.append(
        svg._multiline(
            matrix_x,
            592,
            [
                "Geometry pass = four enclosure corners only.",
                "It does not size columns, joints, bases or foundations.",
            ],
            7.2,
            leading=1.45,
            weight=700,
            fill=svg.RED,
        )
    )


def _draw_tower(parts: list[str]) -> None:
    svg._panel(parts, 1010, 120, 634, 535, "02  FOUR-COLUMN ENCLOSURE · STRUCTURAL STUDY")
    base = [(1090, 566), (1314, 566), (1150, 616), (1374, 616)]
    p2 = [(x, y - 150) for x, y in base]
    roof = [(x, y - 304) for x, y in base]

    def frame(points: list[tuple[float, float]], color: str, width: float = 2.0) -> None:
        for a, b in ((0, 1), (1, 3), (3, 2), (2, 0)):
            parts.append(svg._line(*points[a], *points[b], stroke=color, stroke_width=width))

    parts.append(svg._polygon([base[0], base[1], base[3], base[2]], fill=svg.PURPLE, opacity=0.05))
    frame(base, svg.MUTED)
    frame(p2, svg.PURPLE, 3)
    frame(roof, svg.PURPLE, 3)
    for index in range(4):
        parts.append(
            svg._line(
                *base[index],
                *roof[index],
                stroke=svg.PURPLE,
                stroke_width=6,
                class_="tower-column",
            )
        )
        parts.append(svg._rect(base[index][0] - 8, base[index][1] - 3, 16, 7, fill=svg.INK))

    # Two longitudinal side planes can study bracing; braces are deliberately
    # diagrammatic and are not selected member layouts.
    for left, right in ((0, 1), (2, 3)):
        for lower, upper in ((base, p2), (p2, roof)):
            parts.append(
                svg._line(
                    *lower[left],
                    *upper[right],
                    stroke=svg.TEAL,
                    stroke_width=2.2,
                    class_="tower-side-brace",
                )
            )
            parts.append(
                svg._line(
                    *lower[right],
                    *upper[left],
                    stroke=svg.TEAL,
                    stroke_width=2.2,
                    class_="tower-side-brace",
                )
            )

    # Stair flights are intentionally gray and detached from the lateral-system color.
    stair_points = [(1125, 552), (1286, 492), (1176, 450), (1335, 385), (1228, 340)]
    for start, end in pairwise(stair_points):
        parts.append(svg._line(*start, *end, stroke="#8b969b", stroke_width=7))
    parts.append(svg._text(1235, 488, "STAIR FLIGHTS", 7, anchor="middle", weight=700, fill=svg.MUTED, rotate=-18))
    parts.append(svg._text(1235, 503, "NOT PRIMARY LATERAL MEMBERS", 6.5, anchor="middle", fill=svg.RED, rotate=-18))

    parts.append(svg._text(1068, 570, "+0.00", 7, anchor="end", weight=700, fill=svg.MUTED))
    parts.append(svg._text(1068, 420, "+3.80 P2", 7, anchor="end", weight=700, fill=svg.PURPLE))
    parts.append(svg._text(1068, 266, "ROOF COLLECTOR", 7, anchor="end", weight=700, fill=svg.PURPLE))
    parts.append(svg._badge(1045, 180, "GEOMETRY PASS", svg.GREEN, width=112))
    parts.append(svg._badge(1168, 180, "SYSTEM BLOCKED", svg.RED, width=114))
    parts.append(svg._badge(1293, 180, "2 REUSE + 2 NEW", svg.PURPLE, width=126))
    parts.append(
        svg._multiline(
            1046,
            634,
            [
                "Candidate frame: continuous foundation → P2 → roof lines.",
                "Roof and P2 connections are collector studies, not gravity props.",
            ],
            7.2,
            leading=1.4,
            weight=700,
            fill=svg.MUTED,
        )
    )


def _draw_lateral_planes(parts: list[str]) -> None:
    svg._panel(parts, 40, 675, 950, 365, "03  ORTHOGONAL PLANES · OPENINGS CONTROL THE SYSTEM")
    parts.append(svg._text(70, 736, "SIDE PLANES Y=7.40 / 11.00 · RESIST X", 8.5, weight=700, fill=svg.TEAL))
    left_x, right_x, base_y, roof_y, p2_y = 84.0, 456.0, 980.0, 766.0, 872.0
    for x in (left_x, right_x):
        parts.append(svg._line(x, base_y, x, roof_y, stroke=svg.PURPLE, stroke_width=6))
    for y in (base_y, p2_y, roof_y):
        parts.append(svg._line(left_x, y, right_x, y, stroke=svg.PURPLE, stroke_width=3))
    for bottom, top in ((base_y, p2_y), (p2_y, roof_y)):
        parts.append(svg._line(left_x, bottom, right_x, top, stroke=svg.TEAL, stroke_width=2.4, class_="side-plane-brace"))
        parts.append(svg._line(right_x, bottom, left_x, top, stroke=svg.TEAL, stroke_width=2.4, class_="side-plane-brace"))
    parts.append(svg._text(270, 1003, "4.50 m", 7, anchor="middle", weight=700))
    parts.append(svg._badge(172, 792, "BRACING POSSIBLE", svg.GREEN, width=152))
    parts.append(
        svg._multiline(
            70,
            1022,
            ["Brace topology, reversal, landing clearance", "and fire encasement remain unresolved."],
            6.8,
            leading=1.35,
            fill=svg.RED,
        )
    )

    parts.append(svg._line(500, 724, 500, 1012, stroke=svg.GRID))
    parts.append(svg._text(530, 736, "FRONT / REAR PLANES · RESIST Y", 8.5, weight=700, fill=svg.PURPLE))
    for origin, label in ((548.0, "FRONT PORTAL"), (770.0, "REAR DISCHARGE")):
        lx, rx = origin, origin + 170
        for x in (lx, rx):
            parts.append(svg._line(x, base_y, x, roof_y, stroke=svg.PURPLE, stroke_width=6))
        for y in (base_y, p2_y, roof_y):
            parts.append(svg._line(lx, y, rx, y, stroke=svg.PURPLE, stroke_width=5, class_="moment-frame-beam"))
        parts.append(svg._rect(lx + 48, base_y - 86, 74, 86, fill=svg.PAPER, stroke=svg.AMBER, stroke_width=2))
        parts.append(svg._text((lx + rx) / 2, base_y - 41, "DOOR", 7, anchor="middle", weight=700, fill=svg.AMBER))
        parts.append(svg._text((lx + rx) / 2, 1003, label, 6.8, anchor="middle", weight=700))
    parts.append(svg._badge(638, 792, "NO FULL X-BRACE", svg.RED, width=150))
    parts.append(
        svg._multiline(
            530,
            1022,
            ["Study moment or segmented frames;", "preserve protected portal and discharge."],
            6.8,
            leading=1.35,
            fill=svg.RED,
        )
    )


def _draw_stair_interface(parts: list[str]) -> None:
    svg._panel(parts, 1010, 675, 634, 365, "04  STAIR INTERFACE + LOAD-PATH CONDITIONS")
    column_x = 1108.0
    landing_y = 858.0
    parts.append(svg._line(column_x, 770, column_x, 974, stroke=svg.PURPLE, stroke_width=10))
    parts.append(svg._line(1038, landing_y, 1100, landing_y, stroke="#8b969b", stroke_width=9))
    parts.append(svg._rect(1094, landing_y - 9, 25, 18, rx=7, fill="#ffffff", stroke=svg.AMBER, stroke_width=2, class_="drift-slot"))
    parts.append(svg._line(1084, landing_y - 24, 1129, landing_y - 24, stroke=svg.AMBER, stroke_width=1.8, marker_end="url(#arrow-amber)"))
    parts.append(svg._line(1129, landing_y + 24, 1084, landing_y + 24, stroke=svg.AMBER, stroke_width=1.8, marker_end="url(#arrow-amber)"))
    parts.append(svg._text(1079, 822, "RELATIVE DRIFT", 6.8, anchor="middle", weight=700, fill=svg.AMBER))
    parts.append(svg._text(1079, 901, "SLOTTED / DUCTILE", 6.8, anchor="middle", weight=700, fill=svg.AMBER))
    parts.append(svg._text(1079, 916, "DETAIL TO DESIGN", 6.8, anchor="middle", fill=svg.RED))

    parts.append(svg._line(1170, 731, 1170, 1008, stroke=svg.GRID))
    parts.append(svg._text(1192, 740, "REQUIRED BEFORE STRUCTURAL CREDIT", 8.5, weight=700))
    conditions = [
        ("01", "3D lateral + torsion model"),
        ("02", "P2 / roof diaphragm collectors"),
        ("03", "member, joint and base design"),
        ("04", "foundation uplift / overturning"),
        ("05", "landing restraint + drift detail"),
        ("06", "fire enclosure + egress clearance"),
        ("07", "erection / temporary stability"),
    ]
    for index, (number, label) in enumerate(conditions):
        y = 778 + index * 32
        parts.append(svg._circle(1205, y - 4, 10, fill=svg.RED, opacity=0.12, stroke=svg.RED))
        parts.append(svg._text(1205, y - 1, number, 6, anchor="middle", weight=700, fill=svg.RED))
        parts.append(svg._text(1225, y, label, 7.6, weight=700 if index < 2 else 400))
        parts.append(svg._text(1595, y, "BLOCKED", 6.5, anchor="end", weight=700, fill=svg.RED))


def _draw_footer(parts: list[str], results: dict[str, Any]) -> None:
    project = results["project"]
    digest = results["input_sha256"]
    parts.extend(
        [
            svg._rect(40, 1058, 1604, 108, fill=svg.INK),
            svg._rect(40, 1058, 1604, 7, fill=svg.RED),
            svg._text(60, 1091, "D-048 CONTROLLED INTERPRETATION", 8, weight=700, fill="#bfb3d5"),
            svg._text(
                60,
                1115,
                "FOUR LINES FIT · THE STRUCTURAL SYSTEM IS NOT YET DESIGNED",
                13,
                weight=700,
                fill="#ffffff",
            ),
            svg._multiline(
                60,
                1137,
                [
                    "Continue two stair-jamb Great Wall columns and study two new rear columns from foundation to roof.",
                    "Do not count stair flights as bracing or the roof as gravity-supported here without explicit analysis and detailing.",
                ],
                7.5,
                leading=1.45,
                fill="#d8d0e5",
            ),
            svg._line(1120, 1066, 1120, 1166, stroke="#536970"),
            svg._text(1140, 1091, "SHEET", 8, weight=700, fill="#a9c4c8"),
            svg._text(1140, 1117, SHEET_ID, 16, weight=700, fill="#ffffff"),
            svg._text(
                1140,
                1140,
                f"{SHEET_REVISION} · {project['date']} · E1 {project['revision']}",
                8,
                fill="#cfe0e2",
            ),
            svg._text(1140, 1156, f"INPUT SHA-256 {digest[:16]}…", 7, fill="#a9c4c8"),
            svg._line(1450, 1066, 1450, 1166, stroke="#536970"),
            svg._text(1470, 1091, "STATUS", 8, weight=700, fill="#a9c4c8"),
            svg._text(1470, 1117, "NOT FOR", 14, weight=700, fill="#ffffff"),
            svg._text(1470, 1137, "CONSTRUCTION", 14, weight=700, fill="#ffffff"),
            svg._text(1470, 1156, "professional review required", 7, fill="#f2c7bf"),
        ]
    )


def build_vertical_continuity_sheet(
    configuration: dict[str, Any],
    pb: dict[str, Any],
    p2: dict[str, Any],
    results: dict[str, Any],
) -> str:
    """Return a deterministic, fail-closed D-048 SVG study sheet."""

    del configuration  # Geometry used by this sheet is already audited in results.
    if results.get("selection_or_construction_authority") is not False:
        raise ValueError("The continuity sheet may only render a fail-closed screening result")
    continuity = results.get("checks", {}).get("vertical_continuity_and_stair_core", {})
    if continuity.get("geometry_screen_pass") is not True:
        raise ValueError("The four-corner continuity geometry has not passed its audit")
    if continuity.get("overall_design_resolved") is not False:
        raise ValueError("Unexpected resolved design status: the sheet fails closed")

    metadata = json.dumps(
        {
            "sheet": SHEET_ID,
            "revision": SHEET_REVISION,
            "input_sha256": results["input_sha256"],
            "compatible_column_ids": continuity["compatible_column_ids"],
            "selection_or_construction_authority": False,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg.WIDTH}" '
            f'height="{svg.HEIGHT}" viewBox="0 0 {svg.WIDTH} {svg.HEIGHT}" '
            'role="img" aria-labelledby="sheet-title sheet-description">'
        ),
        '<title id="sheet-title">Dream House vertical continuity and stair frame study</title>',
        (
            '<desc id="sheet-description">Four compatible foundation-to-roof column lines '
            'around the stair enclosure, rejected Great Wall lines, lateral planes, and '
            'drift-compatible stair interface. Not for construction.</desc>'
        ),
        f"<metadata>{html.escape(metadata)}</metadata>",
        """<defs>
          <marker id="arrow-amber" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#bd7626"/></marker>
          <style>
            text { font-family: Arial, Helvetica, sans-serif; }
            line, path, polygon, rect, circle { vector-effect: non-scaling-stroke; }
          </style>
        </defs>""",
        svg._rect(0, 0, svg.WIDTH, svg.HEIGHT, fill=svg.PAPER),
    ]
    _draw_header(parts, results)
    _draw_plan_audit(parts, pb, p2, results)
    _draw_tower(parts)
    _draw_lateral_planes(parts)
    _draw_stair_interface(parts)
    _draw_footer(parts, results)
    parts.append("</svg>\n")
    output = "".join(parts)
    lower = output.lower()
    if any(token in lower for token in ("nan", "infinity", 'inf"')):
        raise ValueError("The generated SVG contains a non-finite value")
    return output

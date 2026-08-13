"""Generate the integrated E1 structural evidence sheet as native SVG.

The sheet is a visual index of calculations and unresolved gates.  It is not a
construction drawing: the M60 roof truss remains the neutral specimen defined
by D-047, while the P2 Great Wall load path is the schematic intent of D-043
and the continuous-overhang hypothesis of D-045.
"""

from __future__ import annotations

import html
import json
from typing import Any

from dreamhouse.structure.truss_grammar import generate_roof_truss

WIDTH = 1684
HEIGHT = 1191
SHEET_NAME = "DH-EST-E1-001_SINTESIS-ESTRUCTURAL.svg"
SHEET_ID = "DH-EST-E1-001"
SHEET_REVISION = "R01"

INK = "#172a32"
MUTED = "#627078"
PAPER = "#f4f0e7"
PANEL = "#fffdfa"
GRID = "#cbd1cf"
TEAL = "#1d7480"
BLUE = "#3d7186"
AMBER = "#bd7626"
RED = "#a33f31"
GREEN = "#2f7859"
BROWN = "#74543c"
PURPLE = "#66538a"


def _attrs(**attributes: object) -> str:
    parts: list[str] = []
    for key, value in attributes.items():
        if value is None:
            continue
        name = key.removesuffix("_")
        name = name.replace("_", "-")
        parts.append(f'{name}="{html.escape(str(value), quote=True)}"')
    return " ".join(parts)


def _rect(x: float, y: float, width: float, height: float, **attributes: object) -> str:
    return f"<rect {_attrs(x=x, y=y, width=width, height=height, **attributes)}/>"


def _line(x1: float, y1: float, x2: float, y2: float, **attributes: object) -> str:
    return f"<line {_attrs(x1=x1, y1=y1, x2=x2, y2=y2, **attributes)}/>"


def _circle(cx: float, cy: float, radius: float, **attributes: object) -> str:
    return f"<circle {_attrs(cx=cx, cy=cy, r=radius, **attributes)}/>"


def _polygon(points: list[tuple[float, float]], **attributes: object) -> str:
    encoded = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f"<polygon {_attrs(points=encoded, **attributes)}/>"


def _path(data: str, **attributes: object) -> str:
    return f"<path {_attrs(d=data, **attributes)}/>"


def _text(
    x: float,
    y: float,
    value: object,
    size: float = 10,
    *,
    anchor: str = "start",
    weight: int = 400,
    fill: str = INK,
    rotate: float | None = None,
    **attributes: object,
) -> str:
    transform = f"rotate({rotate} {x} {y})" if rotate is not None else None
    element_attributes = _attrs(
        x=x,
        y=y,
        font_size=size,
        text_anchor=anchor,
        font_weight=weight,
        fill=fill,
        transform=transform,
        **attributes,
    )
    return f"<text {element_attributes}>{html.escape(str(value))}</text>"


def _multiline(
    x: float,
    y: float,
    lines: list[str],
    size: float = 9,
    *,
    leading: float = 1.35,
    weight: int = 400,
    fill: str = INK,
    anchor: str = "start",
    **attributes: object,
) -> str:
    spans = []
    for index, value in enumerate(lines):
        dy = 0 if index == 0 else size * leading
        spans.append(f'<tspan x="{x}" dy="{dy}">{html.escape(str(value))}</tspan>')
    element_attributes = _attrs(
        x=x,
        y=y,
        font_size=size,
        text_anchor=anchor,
        font_weight=weight,
        fill=fill,
        **attributes,
    )
    return f"<text {element_attributes}>{''.join(spans)}</text>"


def _panel(parts: list[str], x: float, y: float, width: float, height: float, title: str) -> None:
    parts.append(
        _rect(
            x,
            y,
            width,
            height,
            rx=8,
            fill=PANEL,
            stroke="#b8c1c0",
            stroke_width=1.2,
        )
    )
    parts.append(_text(x + 18, y + 28, title, 14, weight=700))
    parts.append(_line(x + 18, y + 40, x + width - 18, y + 40, stroke=GRID))


def _badge(
    x: float,
    y: float,
    label: str,
    color: str,
    *,
    width: float = 74,
) -> str:
    return "".join(
        [
            _rect(x, y, width, 20, rx=10, fill=color, opacity=0.12, stroke=color),
            _text(x + width / 2, y + 14, label, 7.5, anchor="middle", weight=700, fill=color),
        ]
    )


def _great_wall(configuration: dict[str, Any]) -> dict[str, Any]:
    return next(
        option
        for option in configuration["geometry"]["p2_floor_options"]
        if option["id"] == "GRAN-MURO"
    )


def _draw_header(parts: list[str], results: dict[str, Any]) -> None:
    specimen = results["reference_truss"]["candidate"]
    parts.extend(
        [
            _rect(0, 0, WIDTH, 98, fill=INK),
            _rect(0, 98, WIDTH, 6, fill=TEAL),
            _text(40, 42, "INTEGRATED STRUCTURAL E1 SCREENING", 25, weight=700, fill="#ffffff"),
            _text(
                40,
                70,
                (
                    f"{specimen['modulation_id']} {specimen['topology'].replace('_', ' ')} "
                    "neutral roof specimen + P2 gravity path + D-048 stair-core study"
                ),
                11,
                fill="#cfe0e2",
            ),
            _rect(1307, 24, 337, 47, rx=6, fill=RED),
            _text(1475.5, 45, "RESEARCH EVIDENCE", 12, anchor="middle", weight=700, fill="#ffffff"),
            _text(
                1475.5, 62, "NOT FOR CONSTRUCTION", 10, anchor="middle", weight=700, fill="#ffffff"
            ),
        ]
    )


def _draw_plan(
    parts: list[str],
    configuration: dict[str, Any],
    rooflights: dict[str, Any],
    results: dict[str, Any],
) -> None:
    _panel(parts, 40, 120, 1000, 480, "01  INTEGRATED ROOF / P2 LOAD-PATH PLAN")
    x0, y0, scale = 100.0, 174.0, 22.0
    length = float(configuration["geometry"]["nave_length_m"])
    width = float(configuration["geometry"]["nave_width_m"])

    def sx(value: float) -> float:
        return x0 + value * scale

    def sy(value: float) -> float:
        return y0 + (width - value) * scale

    wall = _great_wall(configuration)
    p2_start = float(configuration["geometry"]["p2_start_x_m"])
    wall_x = float(configuration["geometry"]["great_wall_x_m"])
    frame_x = [float(value) for value in range(0, 37, 6)]

    parts.append('<g id="integrated-plan">')
    parts.append(
        _rect(
            sx(p2_start),
            sy(width),
            (length - p2_start) * scale,
            width * scale,
            fill=BLUE,
            opacity=0.08,
        )
    )
    for y_value in [index * 1.5 for index in range(13)]:
        parts.append(
            _line(
                sx(0),
                sy(y_value),
                sx(length),
                sy(y_value),
                stroke=GRID,
                stroke_width=0.75,
            )
        )
    for x_value in frame_x:
        parts.append(
            _line(
                sx(x_value),
                sy(0),
                sx(x_value),
                sy(width),
                stroke=INK,
                stroke_width=3,
                class_="roof-truss-line",
            )
        )
        parts.append(_circle(sx(x_value), sy(0), 4, fill=INK))
        parts.append(_circle(sx(x_value), sy(width), 4, fill=INK))

    for item in rooflights["rooflights"]:
        parts.append(
            _rect(
                sx(float(item["x"])),
                sy(float(item["y"]) + float(item["width"])),
                float(item["length"]) * scale,
                float(item["width"]) * scale,
                rx=3,
                fill="#69a9b5",
                opacity=0.66,
                stroke=TEAL,
                stroke_width=2,
                class_="rooflight-opening",
            )
        )
        parts.append(
            _text(
                sx(float(item["x"]) + float(item["length"]) / 2),
                sy(float(item["y"]) + float(item["width"]) / 2),
                item["id"],
                7,
                anchor="middle",
                weight=700,
                fill="#ffffff",
                rotate=-90,
            )
        )

    # D-043/D-045 P2 path: six continuous beams from X=21 to X=36, supported at
    # the edge truss and the concealed Great Wall frame, then cantilevering 4.5 m.
    for beam_y in wall["beam_y_m"]:
        parts.append(
            _line(
                sx(p2_start),
                sy(float(beam_y)),
                sx(length),
                sy(float(beam_y)),
                stroke=BLUE,
                stroke_width=2.4,
                stroke_dasharray="7 4",
                class_="p2-longitudinal-beam",
            )
        )
    parts.append(
        _line(
            sx(p2_start),
            sy(0),
            sx(p2_start),
            sy(width),
            stroke=BLUE,
            stroke_width=5,
            class_="p2-edge-truss",
        )
    )
    parts.append(
        _line(
            sx(wall_x),
            sy(0),
            sx(wall_x),
            sy(width),
            stroke=BROWN,
            stroke_width=8,
            class_="hybrid-wall-line",
        )
    )
    for column_y in wall["hidden_column_y_m"]:
        parts.append(
            _circle(
                sx(wall_x),
                sy(float(column_y)),
                5.5,
                fill=TEAL,
                stroke="#ffffff",
                stroke_width=1.3,
                class_="hidden-steel-column",
            )
        )

    continuity = results["checks"]["vertical_continuity_and_stair_core"]
    compatible_ids = set(continuity["compatible_column_ids"])
    for candidate in continuity["candidates"]:
        if candidate["id"] not in compatible_ids:
            continue
        parts.append(
            _rect(
                sx(float(candidate["x_m"])) - 7,
                sy(float(candidate["y_m"])) - 7,
                14,
                14,
                rx=2,
                fill=PURPLE,
                stroke="#ffffff",
                stroke_width=1.5,
                class_="full-height-core-column",
            )
        )
    stair = continuity["stair_enclosure"]
    parts.append(
        _rect(
            sx(float(stair["x0_m"])),
            sy(float(stair["y1_m"])),
            float(stair["width_x_m"]) * scale,
            float(stair["width_y_m"]) * scale,
            fill=PURPLE,
            opacity=0.08,
            stroke=PURPLE,
            stroke_width=2,
            stroke_dasharray="5 3",
            class_="stair-core-study-zone",
        )
    )
    parts.append(
        _text(
            sx(33.75),
            sy(9.2),
            "D-048 · 4 FULL-HEIGHT LINES",
            6.8,
            anchor="middle",
            weight=700,
            fill=PURPLE,
            rotate=-90,
        )
    )

    # Four trial active bays from the E1 force-distribution hypothesis.  Their
    # position is deliberately hatched because it has not been coordinated.
    for start_x in (0.0, 30.0):
        for edge_y, offset in ((width, -13), (0.0, 0)):
            bay_top = sy(edge_y) + offset
            parts.append(
                _rect(
                    sx(start_x),
                    bay_top,
                    6 * scale,
                    13,
                    fill="url(#amber-hatch)",
                    stroke=AMBER,
                    stroke_width=1.5,
                    class_="trial-braced-bay",
                )
            )
            parts.append(_line(sx(start_x), bay_top, sx(start_x + 6), bay_top + 13, stroke=AMBER))
            parts.append(_line(sx(start_x), bay_top + 13, sx(start_x + 6), bay_top, stroke=AMBER))

    plan_mid_y = sy(9)
    parts.append(
        _line(
            sx(18),
            plan_mid_y - 8,
            sx(6.6),
            plan_mid_y - 8,
            stroke=TEAL,
            stroke_width=2,
            marker_end="url(#arrow-teal)",
        )
    )
    parts.append(
        _line(
            sx(18),
            plan_mid_y + 8,
            sx(29.4),
            plan_mid_y + 8,
            stroke=TEAL,
            stroke_width=2,
            marker_end="url(#arrow-teal)",
        )
    )
    parts.append(
        _text(
            sx(18),
            plan_mid_y - 16,
            f"DIAPHRAGM DEMAND {results['checks']['diaphragm']['result']['required_unit_shear_kn_m']:.2f} kN/m",
            8,
            anchor="middle",
            weight=700,
            fill=TEAL,
        )
    )

    parts.append(
        _rect(
            sx(0),
            sy(width),
            length * scale,
            width * scale,
            fill="none",
            stroke=INK,
            stroke_width=2.5,
        )
    )
    for index, x_value in enumerate(frame_x):
        parts.append(_circle(sx(x_value), y0 - 16, 9, fill=PANEL, stroke=MUTED))
        parts.append(
            _text(sx(x_value), y0 - 12.5, chr(65 + index), 7.5, anchor="middle", weight=700)
        )
    parts.append(
        _text(
            sx(18),
            sy(width) - 17,
            "7 M60 ROOF-TRUSS LINES · NEUTRAL E1 SPECIMEN",
            8,
            anchor="middle",
            weight=700,
        )
    )
    parts.append(
        _text(
            sx(28.5), sy(17.45), "P2 18 × 15 m · +3.80", 8, anchor="middle", weight=700, fill=BLUE
        )
    )
    parts.append(
        _text(sx(p2_start) + 7, sy(8.9), "EDGE TRUSS X=21", 7, weight=700, fill=BLUE, rotate=-90)
    )
    parts.append(
        _text(
            sx(wall_x) + 11,
            sy(9),
            "D-043 HIDDEN FRAME X=31.5",
            7,
            anchor="middle",
            weight=700,
            fill=BROWN,
            rotate=-90,
        )
    )
    parts.append(
        _text(sx(34), sy(1.2), "4.50 m OVERHANG", 7, anchor="middle", weight=700, fill=BLUE)
    )

    dimension_y = sy(0) + 24
    parts.append(_line(sx(0), dimension_y, sx(length), dimension_y, stroke=MUTED))
    for x_value in frame_x:
        parts.append(
            _line(sx(x_value), dimension_y - 5, sx(x_value), dimension_y + 5, stroke=MUTED)
        )
    for start_x in range(0, 36, 6):
        parts.append(
            _text(sx(start_x + 3), dimension_y - 6, "6.00", 7, anchor="middle", fill=MUTED)
        )
    parts.append(_text(sx(18), dimension_y + 17, "36.00 m", 9, anchor="middle", weight=700))
    parts.append(_text(x0 - 20, sy(9), "18.00 m", 8, anchor="middle", weight=700, rotate=-90))
    parts.append("</g>")

    # Compact legend in the free area between the plan and the panel edge.
    legend_x = 910
    legend_y = 205
    legend = [
        (INK, "M60 neutral roof specimen"),
        (BLUE, "D-043/D-045 P2 gravity path"),
        (TEAL, "D-040 rooflight / diaphragm demand"),
        (PURPLE, "D-048 four-column stair-core study"),
        (AMBER, "trial lateral bays — uncoordinated"),
        (RED, "open design gate"),
    ]
    parts.append(_text(legend_x, legend_y - 18, "GRAPHIC STATUS", 9, weight=700))
    for index, (color, label) in enumerate(legend):
        cy = legend_y + index * 31
        parts.append(_line(legend_x, cy, legend_x + 25, cy, stroke=color, stroke_width=5))
        parts.append(_multiline(legend_x + 34, cy - 4, [label], 7.4, fill=MUTED))
    parts.append(
        _multiline(
            legend_x,
            424,
            [
                "TRIAL BAY LOCATIONS",
                "are diagrammatic.",
                "Openings, collectors,",
                "reversal and joints",
                "remain unresolved.",
            ],
            7.5,
            leading=1.45,
            weight=700,
            fill=RED,
        )
    )


def _draw_gate_matrix(parts: list[str], results: dict[str, Any]) -> None:
    _panel(parts, 1060, 120, 584, 480, "02  E1 EVIDENCE GATE — CALCULATION ≠ DESIGN")
    checks = results["checks"]
    member = checks["local_and_biaxial_member_stability"]
    chord = checks["chord_local_bending"]
    second = checks["member_second_order"]
    joint = checks["trial_connection"]["result"]
    lateral = checks["lateral_system"]["trial_braced_bay_result"]
    diaphragm = checks["diaphragm"]["result"]
    erection = checks["erection"]["result"]
    foundation = checks["foundation"]
    gravity = foundation["gravity_reaction_case"]
    plate = foundation["base_plate_result"]
    fire = checks["fire"]["temperature_sensitivity"]

    rows = [
        ("HSS LOCAL / BIAXIAL", "PASS*", f"interaction {member['maximum_interaction_ratio']:.3f}"),
        (
            "CHORD LOCAL BENDING",
            "PASS*",
            f"{chord['maximum_local_moment_knm']:.2f} kN·m / {chord['maximum_local_bending_ratio']:.3f}",
        ),
        ("MEMBER SECOND ORDER", "PASS*", f"B1 {second['maximum_moment_magnifier']:.3f}"),
        ("GENERIC JOINT PARTS", "PASS*", f"ratio {joint['trial_ratio']:.3f}; HSS wall open"),
        (
            "TRIAL LATERAL BAYS",
            "PASS*",
            f"{lateral['tension_brace_demand_kn']:.1f} kN / {lateral['strength_ratio']:.3f}",
        ),
        (
            "ROOF DIAPHRAGM",
            "DEMAND",
            f"{diaphragm['required_unit_shear_kn_m']:.2f} kN/m; deck open",
        ),
        (
            "FIRE SENSITIVITY",
            "FAIL@550",
            f"ratios {fire[0]['conservative_strength_utilization']:.2f} / {fire[1]['conservative_strength_utilization']:.2f} / {fire[2]['conservative_strength_utilization']:.2f}",
        ),
        (
            "ERECTION / TRANSPORT",
            "DEMAND",
            f"hook {erection['required_hook_load_kn']:.1f} kN; ≥{erection['minimum_transport_piece_count']} pieces",
        ),
        (
            "BASE + TRIAL FOOTING",
            "PASS*",
            f"qmax {gravity['maximum_bearing_kpa']:.1f} kPa; plate {plate['plate_bending_ratio']:.3f}",
        ),
    ]
    parts.append('<g id="evidence-gates">')
    y_start = 178
    parts.append(_text(1080, y_start, "PHENOMENON", 7.5, weight=700, fill=MUTED))
    parts.append(_text(1327, y_start, "CALC", 7.5, weight=700, fill=MUTED))
    parts.append(_text(1420, y_start, "EVIDENCE", 7.5, weight=700, fill=MUTED))
    parts.append(_text(1575, y_start, "DESIGN", 7.5, weight=700, fill=MUTED))
    for index, (phenomenon, status, evidence) in enumerate(rows):
        y = 189 + index * 42
        if index % 2:
            parts.append(_rect(1072, y - 5, 560, 37, rx=3, fill="#f2f3ef"))
        parts.append(_text(1080, y + 16, phenomenon, 8, weight=700))
        calc_color = RED if status.startswith("FAIL") else (GREEN if status == "PASS*" else TEAL)
        parts.append(_badge(1300, y + 3, status, calc_color, width=78))
        parts.append(_text(1392, y + 16, evidence, 7.5, fill=MUTED))
        parts.append(_badge(1561, y + 3, "BLOCKED", RED, width=66))
    parts.append("</g>")
    parts.append(
        _multiline(
            1080,
            581,
            ["PASS* = narrow component screen only. Every system-level design gate remains open."],
            7.5,
            weight=700,
            fill=RED,
        )
    )


def _depth_at(candidate: dict[str, Any], x_value: float) -> float:
    centre = float(candidate["centre_depth_m"])
    if candidate["depth_shape"] == "CONSTANT":
        return centre
    span = 18.0
    shape = 1.0 - abs(2.0 * x_value / span - 1.0)
    end_depth = centre * float(candidate["end_depth_fraction"])
    return end_depth + (centre - end_depth) * shape


def _draw_reference_truss(
    parts: list[str],
    configuration: dict[str, Any],
    results: dict[str, Any],
) -> None:
    _panel(parts, 40, 620, 1000, 420, "03  REFERENCE ROOF TRUSS + EXPLICIT RESTRAINT ASSUMPTIONS")
    reference = results["reference_truss"]
    candidate = reference["candidate"]
    geometry = configuration["geometry"]
    layout = generate_roof_truss(
        topology=candidate["topology"],
        depth_shape=candidate["depth_shape"],
        span_m=float(geometry["nave_width_m"]),
        eave_low_m=float(geometry["eave_low_m"]),
        eave_high_m=float(geometry["eave_high_m"]),
        panel_count=int(candidate["panel_count"]),
        centre_depth_m=float(candidate["centre_depth_m"]),
        end_depth_fraction=float(candidate["end_depth_fraction"]),
    )
    x_left, x_scale = 98.0, 48.0

    def tx(value: float) -> float:
        return x_left + value * x_scale

    def ty(value: float) -> float:
        return 865.0 - (value - 5.5) * 75.0

    parts.append('<g id="reference-truss">')
    # Columns and support conditions sit behind the axial specimen.
    for node_id in layout.support_nodes:
        node_x, node_z = layout.nodes[node_id]
        parts.append(_line(tx(node_x), ty(node_z), tx(node_x), 886, stroke=INK, stroke_width=7))
        parts.append(
            _polygon(
                [(tx(node_x) - 11, 886), (tx(node_x) + 11, 886), (tx(node_x), 871)],
                fill=PAPER,
                stroke=INK,
            )
        )

    for member in layout.members:
        start = layout.nodes[member.i]
        end = layout.nodes[member.j]
        parts.append(
            _line(
                tx(start[0]),
                ty(start[1]),
                tx(end[0]),
                ty(end[1]),
                stroke=INK if member.group == "chord" else TEAL,
                stroke_width=4 if member.group == "chord" else 2.2,
                class_=f"truss-member {member.group} {member.role}",
            )
        )
    for node_x, node_z in layout.nodes:
        parts.append(
            _circle(
                tx(node_x),
                ty(node_z),
                3.1,
                fill=PANEL,
                stroke=INK,
                stroke_width=1.2,
                class_="truss-node",
            )
        )
    for node_id in layout.top_nodes:
        node_x, node_z = layout.nodes[node_id]
        parts.append(
            _line(
                tx(node_x),
                ty(node_z) - 27,
                tx(node_x),
                ty(node_z) - 7,
                stroke=RED,
                stroke_width=1.3,
                marker_end="url(#arrow-red)",
            )
        )

    # Restraints do not arise automatically from the axial model: show the
    # physical top/bottom chord bracing assumptions explicitly.
    for step in range(13):
        x_value = step * 1.5
        roof_z = (
            float(geometry["eave_low_m"])
            + (float(geometry["eave_high_m"]) - float(geometry["eave_low_m"])) * x_value / 18.0
        )
        parts.append(
            _rect(tx(x_value) - 2.5, ty(roof_z) - 2.5, 5, 5, fill=GREEN, class_="top-restraint")
        )
    for x_value in (0.0, 6.0, 12.0, 18.0):
        roof_z = (
            float(geometry["eave_low_m"])
            + (float(geometry["eave_high_m"]) - float(geometry["eave_low_m"])) * x_value / 18.0
        )
        bottom_z = roof_z - _depth_at(candidate, x_value)
        cy = ty(bottom_z)
        parts.append(
            _polygon(
                [
                    (tx(x_value), cy - 5),
                    (tx(x_value) + 5, cy),
                    (tx(x_value), cy + 5),
                    (tx(x_value) - 5, cy),
                ],
                fill=AMBER,
                class_="bottom-restraint",
            )
        )

    splice_x = tx(9.0)
    parts.append(_line(splice_x, 674, splice_x, 888, stroke=RED, stroke_dasharray="5 5"))
    parts.append(_text(splice_x + 7, 680, "ILLUSTRATIVE TRANSPORT SPLIT", 7, weight=700, fill=RED))
    parts.append(_text(98, 680, "TOP RESTRAINT @ 1.50 m", 7, weight=700, fill=GREEN))
    parts.append(_text(98, 695, "BOTTOM RESTRAINT @ 6.00 m", 7, weight=700, fill=AMBER))
    parts.append(_text(958, 680, "LOADS AT PANEL POINTS", 7, anchor="end", weight=700, fill=RED))
    parts.append(
        _text(
            530,
            899,
            "18.00 m TRANSVERSE SPAN · 6 PANELS · VARIABLE DEPTH 0.99→1.80 m",
            8,
            anchor="middle",
            weight=700,
        )
    )
    parts.append("</g>")

    global_screen = reference["global_and_member_screen"]
    envelope = reference["force_and_reaction_envelope"]
    profiles = reference["selected_screening_profiles"]
    metric_boxes = [
        ("TRIAL SECTIONS", f"{profiles['chord']} / {profiles['web']}", "chord / web; not selected"),
        (
            "GOVERNING INTERACTION",
            f"{global_screen['max_strength_ratio']:.3f}",
            f"local M {global_screen['max_chord_local_moment_knm']:.2f} kN·m",
        ),
        (
            "SECOND ORDER",
            f"B1 {global_screen['max_second_order_magnifier']:.3f}",
            f"reduced-Euler ratio {global_screen['max_second_order_euler_ratio']:.3f}",
        ),
        (
            "ENVELOPE",
            f"Nmax {envelope['maximum_member_force_kn']:.1f} kN",
            f"Rdown {envelope['maximum_support_downward_reaction_kn']:.1f} kN",
        ),
        (
            "SPECIMEN",
            f"{reference['truss_mass_kg']:.0f} kg / truss",
            f"deflection {global_screen['max_deflection_m'] * 1000:.1f} mm",
        ),
    ]
    for index, (label, value, note) in enumerate(metric_boxes):
        x = 58 + index * 193
        parts.append(_rect(x, 914, 181, 61, rx=5, fill="#eef3f1", stroke="#c4ceca"))
        parts.append(_text(x + 10, 931, label, 6.8, weight=700, fill=MUTED))
        parts.append(_text(x + 10, 952, value, 11, weight=700))
        parts.append(_text(x + 10, 968, note, 6.8, fill=MUTED))

    # Two linked load paths: gravity to foundations and in-plane actions to
    # diaphragm/collectors/braces.  All system blocks remain explicitly open.
    path_y = 1005
    boxes = [
        (58, 145, "ROOF + OPENINGS", TEAL),
        (225, 130, "PURLINS", INK),
        (380, 145, "M60 TRUSSES", INK),
        (548, 120, "COLUMNS", INK),
        (696, 145, "BASE / FOOTING", RED),
        (862, 130, "GROUND", RED),
    ]
    for x, box_width, label, color in boxes:
        parts.append(
            _rect(x, path_y - 17, box_width, 29, rx=4, fill=color, opacity=0.1, stroke=color)
        )
        parts.append(
            _text(x + box_width / 2, path_y + 2, label, 7, anchor="middle", weight=700, fill=color)
        )
    for index in range(len(boxes) - 1):
        current_x = boxes[index][0] + boxes[index][1]
        next_x = boxes[index + 1][0]
        parts.append(
            _line(
                current_x + 3,
                path_y - 2,
                next_x - 5,
                path_y - 2,
                stroke=MUTED,
                marker_end="url(#arrow-gray)",
            )
        )
    parts.append(
        _text(
            58,
            1030,
            "GRAVITY PATH SHOWN · LATERAL PATH, COLLECTORS, CONNECTIONS AND FOUNDATIONS ARE NOT RELEASED",
            7.5,
            weight=700,
            fill=RED,
        )
    )


def _draw_connection_detail(parts: list[str], results: dict[str, Any]) -> None:
    _panel(parts, 1060, 620, 282, 202, "04  GENERIC JOINT PARTS")
    connection = results["checks"]["trial_connection"]
    trial = connection["result"]
    config = connection["configuration"]
    parts.append('<g id="connection-detail">')
    parts.append(_rect(1080, 689, 152, 40, fill="#e8eceb", stroke=INK, stroke_width=2))
    parts.append(_text(1156, 714, "HSS CHORD", 8, anchor="middle", weight=700))
    parts.append(
        _polygon(
            [(1140, 729), (1255, 729), (1314, 788), (1250, 788)],
            fill="#d9e5e4",
            stroke=TEAL,
            stroke_width=2,
        )
    )
    for index in range(int(config["bolt_count"])):
        parts.append(_circle(1180 + index * 17, 747, 3.8, fill=PANEL, stroke=INK))
    parts.append(_line(1254, 778, 1317, 715, stroke=INK, stroke_width=12))
    parts.append(
        _rect(
            1076, 684, 160, 50, fill="url(#red-hatch)", opacity=0.28, class_="unresolved-hss-wall"
        )
    )
    parts.append(
        _text(
            1080,
            677,
            f"6-M20 · plate {config['plate_thickness_mm']:.0f} mm · weld {config['weld_size_mm']:.0f} mm",
            7.5,
            weight=700,
        )
    )
    parts.append(
        _text(
            1080,
            799,
            f"component ratio {trial['trial_ratio']:.3f} · demand {trial['demand_kn']:.1f} kN",
            7.5,
            weight=700,
            fill=GREEN,
        )
    )
    parts.append(
        _text(1080, 813, "HSS wall / weld access / eccentricity BLOCKED", 7.2, weight=700, fill=RED)
    )
    parts.append("</g>")


def _draw_foundation_detail(parts: list[str], results: dict[str, Any]) -> None:
    _panel(parts, 1352, 620, 292, 202, "05  TRIAL BASE / FOOTING")
    foundation = results["checks"]["foundation"]
    plate = foundation["base_plate_result"]
    gravity = foundation["gravity_reaction_case"]
    config = foundation["configuration"]
    parts.append('<g id="foundation-detail">')
    parts.append(_rect(1470, 670, 54, 58, fill="#d9e0df", stroke=INK, stroke_width=2))
    parts.append(_rect(1445, 725, 104, 9, fill=TEAL, stroke=INK))
    parts.append(_rect(1402, 749, 190, 48, fill="#d9d2c0", stroke=BROWN, stroke_width=2))
    parts.append(_line(1455, 732, 1445, 767, stroke=RED, stroke_width=1.5, stroke_dasharray="4 3"))
    parts.append(_line(1539, 732, 1549, 767, stroke=RED, stroke_width=1.5, stroke_dasharray="4 3"))
    parts.append(_text(1497, 666, "≈ HEA200", 7, anchor="middle", weight=700))
    parts.append(_text(1497, 745, "300×300×20", 7, anchor="middle", weight=700, fill=TEAL))
    parts.append(
        _text(
            1497,
            777,
            f"{config['width_m']:.1f}×{config['length_m']:.1f}×{config['thickness_m']:.1f} m",
            7,
            anchor="middle",
            weight=700,
            fill=BROWN,
        )
    )
    parts.append(
        _text(
            1372,
            797,
            f"qmax {gravity['maximum_bearing_kpa']:.1f} kPa · plate ratio {plate['plate_bending_ratio']:.3f}",
            7.2,
            weight=700,
            fill=GREEN,
        )
    )
    parts.append(
        _text(
            1372, 813, "anchors / shear / moment / geotech / RC BLOCKED", 7.1, weight=700, fill=RED
        )
    )
    parts.append("</g>")


def _draw_erection_detail(parts: list[str], results: dict[str, Any]) -> None:
    _panel(parts, 1060, 838, 282, 202, "06  ERECTION ENVELOPE")
    erection = results["checks"]["erection"]["result"]
    parts.append('<g id="erection-detail">')
    parts.append(
        _path(
            "M1084 965 L1202 914 L1320 965 M1084 965 L1202 984 L1320 965",
            fill="none",
            stroke=INK,
            stroke_width=2,
        )
    )
    parts.append(_circle(1202, 895, 5, fill=RED))
    parts.append(_line(1202, 900, 1145, 944, stroke=AMBER, stroke_width=2))
    parts.append(_line(1202, 900, 1259, 944, stroke=AMBER, stroke_width=2))
    parts.append(_line(1202, 906, 1202, 991, stroke=RED, stroke_dasharray="5 4"))
    parts.append(
        _text(
            1202,
            888,
            f"HOOK {erection['required_hook_load_kn']:.1f} kN",
            7.5,
            anchor="middle",
            weight=700,
            fill=RED,
        )
    )
    parts.append(
        _text(
            1140,
            939,
            f"{erection['sling_tension_each_kn']:.1f} kN",
            7,
            anchor="middle",
            weight=700,
            fill=AMBER,
        )
    )
    parts.append(
        _text(
            1264,
            939,
            f"{erection['sling_tension_each_kn']:.1f} kN",
            7,
            anchor="middle",
            weight=700,
            fill=AMBER,
        )
    )
    parts.append(
        _text(
            1078,
            1008,
            f"18 m requires ≥{erection['minimum_transport_piece_count']} pieces at 12 m transport limit",
            7.2,
            weight=700,
        )
    )
    parts.append(
        _text(
            1078,
            1025,
            "crane chart / lugs / splice / weather / temporary bracing BLOCKED",
            7,
            weight=700,
            fill=RED,
        )
    )
    parts.append("</g>")


def _draw_fire_detail(parts: list[str], results: dict[str, Any]) -> None:
    _panel(parts, 1352, 838, 292, 202, "07  FIRE SENSITIVITY — NOT A RATING")
    fire = results["checks"]["fire"]["temperature_sensitivity"]
    parts.append('<g id="fire-detail">')
    for index, item in enumerate(fire):
        y = 895 + index * 35
        ratio = float(item["conservative_strength_utilization"])
        bar_width = min(ratio / 3.0, 1.0) * 150
        color = GREEN if item["trial_temperature_pass"] else RED
        parts.append(_text(1373, y + 13, f"{item['temperature_c']:.0f}°C", 8, weight=700))
        parts.append(_rect(1424, y, 150, 18, rx=3, fill="#e3e6e2"))
        parts.append(_rect(1424, y, bar_width, 18, rx=3, fill=color, opacity=0.75))
        parts.append(_text(1582, y + 13, f"{ratio:.2f}", 8, weight=700, fill=color))
        parts.append(
            _line(1474, y - 2, 1474, y + 20, stroke=INK, stroke_width=0.8, stroke_dasharray="2 2")
        )
    parts.append(
        _text(
            1373,
            1009,
            "period / scenario / section factor / tested protection BLOCKED",
            7,
            weight=700,
            fill=RED,
        )
    )
    parts.append(
        _text(1373, 1025, "400°C pass is sensitivity only; 550°C and 700°C fail", 7, weight=700)
    )
    parts.append("</g>")


def _draw_footer(parts: list[str], results: dict[str, Any]) -> None:
    project = results["project"]
    digest = results["input_sha256"]
    parts.extend(
        [
            _rect(40, 1058, 1604, 108, fill=INK),
            _rect(40, 1058, 1604, 7, fill=RED),
            _text(60, 1091, "AUTHORITY", 8, weight=700, fill="#a9c4c8"),
            _text(
                60,
                1115,
                "RESEARCH SCREENING COMPLETE · DESIGN BLOCKED",
                13,
                weight=700,
                fill="#ffffff",
            ),
            _multiline(
                60,
                1137,
                [
                    "No structural-system selection, PE-1 quantity, procurement, fabrication or construction authority.",
                    "D-043 fixes P2 gravity intent; D-047 governs the specimen; D-048 adds a fail-closed stair-core study.",
                ],
                7.5,
                leading=1.45,
                fill="#cfe0e2",
            ),
            _line(1120, 1066, 1120, 1166, stroke="#536970"),
            _text(1140, 1091, "SHEET", 8, weight=700, fill="#a9c4c8"),
            _text(1140, 1117, SHEET_ID, 16, weight=700, fill="#ffffff"),
            _text(
                1140,
                1140,
                f"{SHEET_REVISION} · {project['date']} · {project['revision']}",
                8,
                fill="#cfe0e2",
            ),
            _text(1140, 1156, f"INPUT SHA-256 {digest[:16]}…", 7, fill="#a9c4c8"),
            _line(1450, 1066, 1450, 1166, stroke="#536970"),
            _text(1470, 1091, "STATUS", 8, weight=700, fill="#a9c4c8"),
            _text(1470, 1117, "NOT FOR", 14, weight=700, fill="#ffffff"),
            _text(1470, 1137, "CONSTRUCTION", 14, weight=700, fill="#ffffff"),
            _text(1470, 1156, "professional review required", 7, fill="#f2c7bf"),
        ]
    )


def build_e1_sheet(
    configuration: dict[str, Any],
    roof_space: dict[str, Any],
    e1_space: dict[str, Any],
    rooflights: dict[str, Any],
    results: dict[str, Any],
) -> str:
    """Return one deterministic, calculation-linked E1 SVG sheet."""

    if results.get("selection_or_construction_authority") is not False:
        raise ValueError("The E1 sheet may only render a fail-closed screening result")
    if results.get("overall_status") != "research_screening_complete_design_blocked":
        raise ValueError("Unexpected E1 status: the drawing generator fails closed")
    if e1_space["reference_truss"]["modulation_id"] != "M60":
        raise ValueError("D-047 requires the neutral M60 specimen for this sheet revision")
    if roof_space["analysis"]["top_chord_out_of_plane_unbraced_m"] <= 0:
        raise ValueError("Top-chord restraint spacing must be positive")
    if len(rooflights.get("rooflights", [])) != 2:
        raise ValueError("D-040 requires exactly two active rooflight hypotheses")

    metadata = json.dumps(
        {
            "sheet": SHEET_ID,
            "revision": SHEET_REVISION,
            "input_sha256": results["input_sha256"],
            "selection_or_construction_authority": False,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="sheet-title sheet-description">',
        '<title id="sheet-title">Dream House integrated E1 structural screening sheet</title>',
        '<desc id="sheet-description">Calculation-linked structural evidence with an integrated plan, reference roof truss, design gates, connection, foundation, erection and fire sensitivity. Not for construction.</desc>',
        f"<metadata>{html.escape(metadata)}</metadata>",
        """<defs>
          <marker id="arrow-teal" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#1d7480"/></marker>
          <marker id="arrow-red" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#a33f31"/></marker>
          <marker id="arrow-gray" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#627078"/></marker>
          <pattern id="amber-hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="8" stroke="#bd7626" stroke-width="3" opacity="0.42"/></pattern>
          <pattern id="red-hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="7" stroke="#a33f31" stroke-width="2"/></pattern>
          <style>
            text { font-family: Arial, Helvetica, sans-serif; }
            line, path, polygon, rect, circle { vector-effect: non-scaling-stroke; }
          </style>
        </defs>""",
        _rect(0, 0, WIDTH, HEIGHT, fill=PAPER),
    ]
    _draw_header(parts, results)
    _draw_plan(parts, configuration, rooflights, results)
    _draw_gate_matrix(parts, results)
    _draw_reference_truss(parts, configuration, results)
    _draw_connection_detail(parts, results)
    _draw_foundation_detail(parts, results)
    _draw_erection_detail(parts, results)
    _draw_fire_detail(parts, results)
    _draw_footer(parts, results)
    parts.append("</svg>\n")
    output = "".join(parts)
    lower = output.lower()
    if any(token in lower for token in ("nan", "infinity", 'inf"')):
        raise ValueError("The generated SVG contains a non-finite value")
    return output

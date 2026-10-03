"""Source-bound context for the PB Great Wall and media-wall sheets.

Historical leaf generators remain unchanged. This module renders them from the
resolved snapshot, audits their graphics against captured source paths, and adds
context dimensions without creating wall, TV, console, or door entities.
"""

from __future__ import annotations

import copy
import json
import math
import re
from collections.abc import Mapping
from typing import Any
from xml.etree import ElementTree as ET

from dreamhouse import generate_pb_b05, generate_pb_b24, generate_pb_b27
from dreamhouse.coordination.model import CoordinationError

SVG_NS = "http://www.w3.org/2000/svg"
GREAT_WALL = "architecture-great-wall-elevation"
PB_MEDIA_WALL = "architecture-pb-media-wall"
VIEWS = {GREAT_WALL, PB_MEDIA_WALL}
PB = ["discipline_inputs", "equipment", "pb"]
MEDIA = PB + ["social_layout", "media_wall"]
CONSOLE = MEDIA + ["console"]
PB_LEVEL = ["discipline_inputs", "structure", "stair", "levels", "pb_finished_floor"]
EPSILON = 1e-6


def _q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


def _fmt(value: float) -> str:
    return format(value, ".12g") if value else "0"


def _token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-.") or "item"


def _display_number(value: float) -> str:
    return str(int(value)) if value.is_integer() else format(value, ".12g")


def _number(value: object, label: str, *, positive: bool = False) -> float:
    if type(value) not in {int, float} or not math.isfinite(value):
        raise CoordinationError(f"Invalid wall context number at {label}")
    result = float(value)
    if positive and result <= 0:
        raise CoordinationError(f"Wall context value must be positive at {label}")
    return result


def _source(snapshot: Mapping[str, Any], path: list[str | int], *, positive: bool = False) -> float:
    value: Any = snapshot
    try:
        for part in path:
            value = value[part]
    except (KeyError, IndexError, TypeError) as error:
        raise CoordinationError(f"Missing wall context source: {path}") from error
    return _number(value, ".".join(str(part) for part in path), positive=positive)


def _close(actual: object, expected: float, label: str) -> None:
    try:
        observed = float(actual)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError) as error:
        raise CoordinationError(f"Invalid wall context SVG coordinate: {label}") from error
    if not math.isfinite(observed) or not math.isclose(
        observed, expected, rel_tol=0.0, abs_tol=EPSILON
    ):
        raise CoordinationError(
            f"Wall context projection mismatch for {label}: {observed:g} != {expected:g}"
        )


def _text(node: ET.Element) -> str:
    return "".join(node.itertext()).strip()


def _unique(nodes: list[ET.Element], label: str) -> ET.Element:
    if len(nodes) != 1:
        raise CoordinationError(f"Expected one {label} in wall context SVG, found {len(nodes)}")
    return nodes[0]


def _snapshot_pb(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Copy the captured PB model and apply only canonical envelope/door state."""
    try:
        pb = copy.deepcopy(snapshot["discipline_inputs"]["equipment"]["pb"])
        hall = snapshot["geometry"]["hall"]
        pb["envelope"]["length"] = _number(
            hall["length_m"], "geometry.hall.length_m", positive=True
        )
        pb["envelope"]["width"] = _number(hall["width_m"], "geometry.hall.width_m", positive=True)
        entities = snapshot["entities"]
    except (KeyError, TypeError) as error:
        raise CoordinationError(f"PB wall context source is incomplete: {error}") from error

    # CF-013 keeps inherited PB core-door positions unresolved. Never pass their
    # old b36 coordinates to the historical Great Wall renderer.
    for room in pb.get("core", []):
        entity = entities.get(f"PB-DOOR-{room['id']}")
        if entity is None or entity.get("geometry", {}).get("shape") == "unresolved":
            room["door_y"] = None
    return pb


def _great_wall_contract(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    width = _source(snapshot, ["geometry", "hall", "width_m"], positive=True)
    try:
        rooms = snapshot["discipline_inputs"]["equipment"]["pb"]["core"]
        wall = snapshot["discipline_inputs"]["equipment"]["pb"]["great_wall"]
    except (KeyError, TypeError) as error:
        raise CoordinationError(f"Great Wall source context is incomplete: {error}") from error
    if not isinstance(rooms, list) or not rooms:
        raise CoordinationError("Great Wall source core must contain rooms")
    spans = []
    for index, room in enumerate(rooms):
        if not isinstance(room, Mapping) or not isinstance(room.get("id"), str):
            raise CoordinationError(f"Invalid Great Wall core room at index {index}")
        start = _number(room.get("y0"), f"pb.core[{index}].y0")
        end = _number(room.get("y1"), f"pb.core[{index}].y1")
        if start < 0 or end <= start or end > width + EPSILON:
            raise CoordinationError(f"Invalid Great Wall room span: {room['id']}")
        if spans and not math.isclose(start, spans[-1]["end"], rel_tol=0, abs_tol=EPSILON):
            raise CoordinationError("Great Wall room spans must be contiguous")
        spans.append(
            {"id": room["id"], "name": room.get("name"), "start": start, "end": end, "index": index}
        )
    if not math.isclose(spans[0]["start"], 0.0, rel_tol=0, abs_tol=EPSILON):
        raise CoordinationError("Great Wall core must begin at Y=0")
    if not math.isclose(spans[-1]["end"], width, rel_tol=0, abs_tol=EPSILON):
        raise CoordinationError("Great Wall core and hall width disagree")
    return {
        "width": width,
        "spans": spans,
        "plane_x": _number(wall.get("x"), "pb.great_wall.x"),
        "thickness": _number(wall.get("thickness"), "pb.great_wall.thickness", positive=True),
        "width_path": ["geometry", "hall", "width_m"],
        "plane_x_path": PB + ["great_wall", "x"],
        "thickness_path": PB + ["great_wall", "thickness"],
    }


def _media_wall_contract(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    try:
        media = snapshot["discipline_inputs"]["equipment"]["pb"]["social_layout"]["media_wall"]
        pb = snapshot["discipline_inputs"]["equipment"]["pb"]
    except (KeyError, TypeError) as error:
        raise CoordinationError(f"PB media-wall source context is incomplete: {error}") from error
    values: dict[str, Any] = {
        "x0": _number(media.get("x0"), "media_wall.x0"),
        "x1": _number(media.get("x1"), "media_wall.x1"),
        "y": _number(media.get("y"), "media_wall.y"),
        "height": _number(media.get("height"), "media_wall.height", positive=True),
        "tv_width": _number(media.get("tv_width"), "media_wall.tv_width", positive=True),
        "tv_height": _number(media.get("tv_height"), "media_wall.tv_height", positive=True),
        "tv_center_height": _number(media.get("tv_center_height"), "media_wall.tv_center_height"),
        "tv_center_x": _number(media.get("tv_center_x"), "media_wall.tv_center_x"),
        "viewing_point_y": _number(media.get("viewing_point_y"), "media_wall.viewing_point_y"),
        "viewing_distance": _number(
            media.get("viewing_distance"), "media_wall.viewing_distance", positive=True
        ),
        "tv_diagonal_inches": _number(
            media.get("tv_diagonal_inches"), "media_wall.tv_diagonal_inches", positive=True
        ),
        "side": media.get("side"),
        "mounting": media.get("mounting"),
        "aspect_ratio": media.get("tv_aspect_ratio"),
        "level": _source(snapshot, PB_LEVEL),
        "paths": {},
    }
    console = media.get("console")
    if not isinstance(console, Mapping):
        raise CoordinationError("PB media-wall console source is incomplete")
    values.update(
        {
            "console_x": _number(console.get("x"), "media_wall.console.x"),
            "console_length": _number(
                console.get("length"), "media_wall.console.length", positive=True
            ),
            "console_height": _number(
                console.get("height"), "media_wall.console.height", positive=True
            ),
        }
    )
    if (
        values["x1"] <= values["x0"]
        or values["side"] != "B"
        or values["mounting"] != "side_b_perimeter"
    ):
        raise CoordinationError("PB media-wall source is outside the Side B renderer contract")
    if not isinstance(values["aspect_ratio"], str) or not re.fullmatch(
        r"\d+(?:\.\d+)?:\d+(?:\.\d+)?", values["aspect_ratio"]
    ):
        raise CoordinationError("PB TV aspect ratio must be a source-declared ratio")
    if not math.isclose(
        values["viewing_distance"],
        values["y"] - values["viewing_point_y"],
        rel_tol=0,
        abs_tol=EPSILON,
    ):
        raise CoordinationError("PB media-wall viewing distance disagrees with its Y datums")
    if not (
        values["x0"] - EPSILON <= values["tv_center_x"] - values["tv_width"] / 2
        and values["tv_center_x"] + values["tv_width"] / 2 <= values["x1"] + EPSILON
    ):
        raise CoordinationError("PB TV envelope is outside its mounting field")
    if not (
        values["x0"]
        <= values["console_x"]
        < values["console_x"] + values["console_length"]
        <= values["x1"] + EPSILON
    ):
        raise CoordinationError("PB media-wall console is outside its mounting field")

    values["paths"] = {
        key: MEDIA + [source]
        for key, source in {
            "x0": "x0",
            "x1": "x1",
            "y": "y",
            "height": "height",
            "tv_width": "tv_width",
            "tv_height": "tv_height",
            "tv_center_height": "tv_center_height",
            "tv_center_x": "tv_center_x",
            "viewing_point_y": "viewing_point_y",
            "viewing_distance": "viewing_distance",
            "tv_diagonal_inches": "tv_diagonal_inches",
            "aspect_ratio": "tv_aspect_ratio",
        }.items()
    }
    values["paths"].update(
        {
            "console_x": CONSOLE + ["x"],
            "console_length": CONSOLE + ["length"],
            "console_height": CONSOLE + ["height"],
            "level": PB_LEVEL,
        }
    )
    # The wall's Side B location is out of plane in the elevation panel.
    side_b_y = _number(pb["envelope"]["width"], "pb.envelope.width") - _number(
        pb["envelope"]["exterior_wall"], "pb.envelope.exterior_wall", positive=True
    )
    if not math.isclose(values["y"], side_b_y, rel_tol=0, abs_tol=EPSILON):
        raise CoordinationError("PB media-wall Y datum disagrees with the Side B perimeter")
    return values


def _parameterize_great_wall(root: ET.Element, contract: Mapping[str, Any]) -> None:
    """Replace the leaf renderer's plan-span literals with source spans.

    The vertical silhouette stays a non-dimensional schematic profile because
    no Great Wall height is present in the snapshot.
    """
    left, base, scale = 120.0, 610.0, 63.0
    width = float(contract["width"])
    spans = contract["spans"]
    end_points = [spans[0]["start"], *[span["end"] for span in spans]]
    faces = [node for node in root.iter(_q("rect")) if node.get("fill") == "#c7a47e"]
    slats = [node for node in root.iter(_q("rect")) if node.get("fill") == "url(#slats)"]
    if len(faces) != 1 or len(slats) != 1:
        raise CoordinationError("Great Wall elevation face features changed")
    for face in (faces[0], slats[0]):
        face.set("x", _fmt(left))
        face.set("width", _fmt(width * scale))
        face.set("data-context-height-status", "schematic-unresolved")

    boundaries = [
        node
        for node in root.iter(_q("line"))
        if node.get("stroke") == "#725238"
        and node.get("stroke-width") == ".7"
        and node.get("opacity") == ".45"
    ]
    if len(boundaries) != len(end_points):
        raise CoordinationError("Great Wall room-boundary feature count changed")
    for node, position in zip(boundaries, end_points, strict=True):
        x = left + position * scale
        node.set("x1", _fmt(x))
        node.set("x2", _fmt(x))

    dim_y = base + 115.0
    dimension_lines = [
        node
        for node in root.iter(_q("line"))
        if node.get("stroke") == "#536166"
        and math.isclose(float(node.get("y1", "nan")), dim_y, rel_tol=0, abs_tol=EPSILON)
        and math.isclose(float(node.get("y2", "nan")), dim_y, rel_tol=0, abs_tol=EPSILON)
    ]
    if len(dimension_lines) != 1:
        raise CoordinationError("Great Wall total-span dimension line changed")
    dimension_lines[0].set("x1", _fmt(left))
    dimension_lines[0].set("x2", _fmt(left + width * scale))
    ticks = [
        node
        for node in root.iter(_q("line"))
        if node.get("stroke") == "#536166"
        and math.isclose(float(node.get("y1", "nan")), dim_y - 7, rel_tol=0, abs_tol=EPSILON)
        and math.isclose(float(node.get("y2", "nan")), dim_y + 7, rel_tol=0, abs_tol=EPSILON)
    ]
    if len(ticks) != len(end_points):
        raise CoordinationError("Great Wall span-tick feature count changed")
    for node, position in zip(ticks, end_points, strict=True):
        x = left + position * scale
        node.set("x1", _fmt(x))
        node.set("x2", _fmt(x))

    labels = [
        node
        for node in root.iter(_q("text"))
        if math.isclose(float(node.get("y", "nan")), dim_y - 9, rel_tol=0, abs_tol=EPSILON)
        and re.fullmatch(r"\d+[,.]\d+", _text(node))
    ]
    if len(labels) != len(spans):
        raise CoordinationError("Great Wall segment-dimension label count changed")
    for label, span in zip(labels, spans, strict=True):
        label.set("x", _fmt(left + (span["start"] + span["end"]) * scale / 2))
        label.text = f"{span['end'] - span['start']:.2f}".replace(".", ",")

    total_label = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if math.isclose(float(node.get("y", "nan")), dim_y + 26, rel_tol=0, abs_tol=EPSILON)
        ],
        "Great Wall total-span label",
    )
    total_label.set("x", _fmt(left + width * scale / 2))
    total_label.text = f"{width:.2f} m".replace(".", ",")

    for node in root.iter(_q("text")):
        if _text(node).startswith(("El wall debe", "El muro debe")):
            node.text = "Continuous architectural finish across the core zones; door positions remain unresolved under CF-013."

    # Make the missing vertical authority explicit on the drawing. This note
    # disclaims the retained silhouette without assigning it a world height.
    note = ET.SubElement(
        root,
        _q("text"),
        {
            "x": "140",
            "y": "875",
            "font-size": "8",
            "font-weight": "700",
            "fill": "#8e3825",
            "data-context-feature": "great-wall-height-unresolved",
        },
    )
    note.text = "HEIGHT NOT SOURCE-DEFINED · VERTICAL PROFILE IS SCHEMATIC"


def _parameterize_media_wall(root: ET.Element, contract: Mapping[str, Any]) -> None:
    """Bind the legacy elevation panel to declared TV and console coordinates."""
    wall_x, floor_y, scale = 70.0, 730.0, 150.0
    x0, x1 = float(contract["x0"]), float(contract["x1"])
    field_width = x1 - x0
    header = _unique(
        [node for node in root.iter(_q("text")) if _text(node).startswith("PB LIVING /")],
        "media-wall header",
    )
    header.text = f"PB LIVING / {_display_number(float(contract['tv_diagonal_inches']))}-INCH TV ON SIDE B WALL"
    header.set("data-context-feature", "pb-media-title")
    tv_width = float(contract["tv_width"])
    tv_height = float(contract["tv_height"])
    tv_center_x = float(contract["tv_center_x"])
    tv_center_height = float(contract["tv_center_height"])

    tv = _unique(
        [node for node in root.iter(_q("rect")) if node.get("fill") == "#172126"],
        "TV equipment envelope",
    )
    old_tv_x = float(tv.get("x", "nan"))
    new_tv_x = wall_x + (tv_center_x - x0 - tv_width / 2) * scale
    delta_tv_x = new_tv_x - old_tv_x
    for node in (tv, *[item for item in root.iter(_q("rect")) if item.get("fill") == "#324e57"]):
        node.set("x", _fmt(float(node.get("x", "nan")) + delta_tv_x))

    tv_labels = [
        node
        for node in root.iter(_q("text"))
        if _text(node)
        in {"100-IN TV EQUIPMENT ENVELOPE", f"{tv_width:.2f} × {tv_height:.2f} m · 16:9"}
    ]
    if len(tv_labels) != 2:
        raise CoordinationError("PB TV equipment label features changed")
    tv_labels.sort(key=lambda node: float(node.get("y", "nan")))
    tv_labels[
        0
    ].text = f"{_display_number(float(contract['tv_diagonal_inches']))}-IN TV EQUIPMENT ENVELOPE"
    tv_labels[0].set("data-context-feature", "pb-media-tv-specification")
    tv_labels[1].text = f"{tv_width:.2f} × {tv_height:.2f} m · {contract['aspect_ratio']}"
    tv_labels[1].set("data-context-feature", "pb-media-tv-envelope-dimensions")
    for label in tv_labels:
        label.set("x", _fmt(new_tv_x + tv_width * scale / 2))

    tv_center_y = floor_y - tv_center_height * scale
    leader = _unique(
        [
            node
            for node in root.iter(_q("line"))
            if node.get("stroke") == "#9b4c32"
            and math.isclose(float(node.get("y1", "nan")), tv_center_y, abs_tol=EPSILON)
            and math.isclose(float(node.get("y2", "nan")), tv_center_y, abs_tol=EPSILON)
        ],
        "TV center-height leader",
    )
    leader.set("x1", _fmt(new_tv_x + tv_width * scale + 8))
    tv_center_label = _unique(
        [node for node in root.iter(_q("text")) if "TV CENTRE" in _text(node)],
        "TV center-height label",
    )
    tv_center_label.text = f"TV CENTRE +{tv_center_height:.2f} m AFF"
    tv_center_label.set("data-context-feature", "pb-media-tv-center-height-label")

    console = _unique(
        [node for node in root.iter(_q("rect")) if node.get("fill") == "#6f543e"],
        "AV console envelope",
    )
    old_console_x = float(console.get("x", "nan"))
    new_console_x = wall_x + (float(contract["console_x"]) - x0) * scale
    delta_console_x = new_console_x - old_console_x
    console.set("x", _fmt(new_console_x))
    console_width = float(contract["console_length"]) * scale
    console_divisions = [
        node
        for node in root.iter(_q("line"))
        if node.get("stroke") == "#b99876"
        and math.isclose(
            float(node.get("y1", "nan")), float(console.get("y", "nan")), abs_tol=EPSILON
        )
        and math.isclose(float(node.get("y2", "nan")), floor_y, abs_tol=EPSILON)
    ]
    if len(console_divisions) != 3:
        raise CoordinationError("PB AV console division features changed")
    for index, node in enumerate(console_divisions, start=1):
        x = new_console_x + console_width * index / 4
        node.set("x1", _fmt(x))
        node.set("x2", _fmt(x))
    console_label = _unique(
        [node for node in root.iter(_q("text")) if "ACCESSIBLE AV CONSOLE" in _text(node)],
        "AV console dimension label",
    )
    console_label.text = f"{float(contract['console_length']):.2f} m ACCESSIBLE AV CONSOLE"
    console_label.set("x", _fmt(float(console_label.get("x", "nan")) + delta_console_x))

    field_label = _unique(
        [node for node in root.iter(_q("text")) if "MOUNTING FIELD" in _text(node)],
        "mounting-field label",
    )
    field_label.text = f"{field_width:.2f} m MOUNTING FIELD · DIRECTLY ON SIDE B PERIMETER WALL"
    field_label.set("data-context-feature", "pb-media-mounting-field-width-label")
    view_label = _unique(
        [node for node in root.iter(_q("text")) if _text(node).endswith("m VIEW")],
        "viewing-distance label",
    )
    view_label.set("data-context-feature", "pb-media-viewing-distance-label")
    console_label.set("data-context-feature", "pb-media-console-length-label")
    for node in tv_labels:
        node.set("x", _fmt(new_tv_x + tv_width * scale / 2))


def render_wall_context(snapshot: Mapping[str, Any], view_id: str) -> str | None:
    """Render a supported PB wall sheet from snapshot data; unknown IDs return None."""
    if view_id not in VIEWS:
        return None
    pb = _snapshot_pb(snapshot)
    if view_id == GREAT_WALL:
        contract = _great_wall_contract(snapshot)
        svg = generate_pb_b05.wall_elevation_sheet(pb)
        root = ET.fromstring(svg)
        _parameterize_great_wall(root, contract)
        svg = ET.tostring(root, encoding="unicode")
    else:
        contract = _media_wall_contract(snapshot)
        svg = generate_pb_b27.perimeter_media_sheet(pb)
        svg = generate_pb_b24.translate_visible_text(svg)
        root = ET.fromstring(svg)
        _parameterize_media_wall(root, contract)
        height_label = ET.SubElement(
            root,
            _q("text"),
            {
                "x": _fmt(70.0 + ((float(contract["x1"]) - float(contract["x0"])) + 0.08) * 150.0),
                "y": _fmt(730.0 - float(contract["height"]) * 150.0 / 2),
                "font-size": "9",
                "fill": "#176172",
                "data-context-feature": "pb-media-mounting-field-height-label",
            },
        )
        height_label.text = f"{float(contract['height']):.2f} m"
        svg = ET.tostring(root, encoding="unicode")
        return svg
    return generate_pb_b24.translate_visible_text(svg)


def _assert_source_rect(node: ET.Element, expected: Mapping[str, float], label: str) -> None:
    for key, value in expected.items():
        _close(node.get(key), value, f"{label}/{key}")


def _assert_untransformed_ancestry(
    root: ET.Element, features: list[ET.Element], view_id: str
) -> None:
    parents = {child: parent for parent in root.iter() for child in parent}
    for feature in features:
        ancestor = feature
        while ancestor is not None:
            if ancestor.get("transform") or "transform" in ancestor.get("style", "").lower():
                raise CoordinationError(
                    f"Transformed wall context geometry is unsupported: {view_id}"
                )
            ancestor = parents.get(ancestor)


def _source_unresolved(snapshot: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    height_path = PB + ["great_wall", "height"]
    try:
        height = snapshot
        for part in height_path:
            height = height[part]
    except (KeyError, TypeError):
        height = None
    if height is not None:
        _number(height, "pb.great_wall.height", positive=True)
        height_unknown = None
    else:
        height_unknown = {
            "state": "unavailable",
            "expected_path": ".".join(height_path),
            "reason": "No source field defines Great Wall elevation height; the historical 3.20 m profile is schematic and unmeasured.",
        }
    unresolved_doors = [
        f"PB-DOOR-{room['id']}"
        for room in contract["spans"]
        if snapshot.get("entities", {})
        .get(f"PB-DOOR-{room['id']}", {})
        .get("geometry", {})
        .get("shape")
        == "unresolved"
    ]
    return {
        "height": height_unknown,
        "doors": {
            "state": "unresolved" if unresolved_doors else "resolved",
            "entity_ids": unresolved_doors,
            "conflict_id": "CF-013" if unresolved_doors else None,
        },
    }


def _audit_great_wall(snapshot: Mapping[str, Any], root: ET.Element) -> dict[str, Any]:
    contract = _great_wall_contract(snapshot)
    left, base, scale = 120.0, 610.0, 63.0
    width = float(contract["width"])
    face = _unique(
        [node for node in root.iter(_q("rect")) if node.get("fill") == "#c7a47e"],
        "Great Wall finish field",
    )
    _assert_source_rect(face, {"x": left, "width": width * scale}, "great-wall/finish-field")
    hatch = _unique(
        [node for node in root.iter(_q("rect")) if node.get("fill") == "url(#slats)"],
        "Great Wall slat field",
    )
    _assert_source_rect(hatch, {"x": left, "width": width * scale}, "great-wall/slats")

    boundaries = [contract["spans"][0]["start"], *[span["end"] for span in contract["spans"]]]
    lines = [
        node
        for node in root.iter(_q("line"))
        if node.get("stroke") == "#725238"
        and node.get("stroke-width") == ".7"
        and node.get("opacity") == ".45"
    ]
    if len(lines) != len(boundaries):
        raise CoordinationError("Great Wall room-boundary feature set changed")
    for index, (line, boundary) in enumerate(zip(lines, boundaries, strict=True)):
        x = left + boundary * scale
        _close(line.get("x1"), x, f"great-wall/boundary-{index}/x1")
        _close(line.get("x2"), x, f"great-wall/boundary-{index}/x2")

    dim_y = base + 115.0
    dimension_line = _unique(
        [
            node
            for node in root.iter(_q("line"))
            if node.get("stroke") == "#536166"
            and math.isclose(float(node.get("y1", "nan")), dim_y, abs_tol=EPSILON)
            and math.isclose(float(node.get("y2", "nan")), dim_y, abs_tol=EPSILON)
        ],
        "Great Wall span dimension line",
    )
    _close(dimension_line.get("x1"), left, "great-wall/span-line/start")
    _close(dimension_line.get("x2"), left + width * scale, "great-wall/span-line/end")
    ticks = [
        node
        for node in root.iter(_q("line"))
        if node.get("stroke") == "#536166"
        and math.isclose(float(node.get("y1", "nan")), dim_y - 7, abs_tol=EPSILON)
        and math.isclose(float(node.get("y2", "nan")), dim_y + 7, abs_tol=EPSILON)
    ]
    if len(ticks) != len(boundaries):
        raise CoordinationError("Great Wall span-tick feature set changed")
    for index, (tick, boundary) in enumerate(zip(ticks, boundaries, strict=True)):
        _close(tick.get("x1"), left + boundary * scale, f"great-wall/tick-{index}")

    labels = [
        node
        for node in root.iter(_q("text"))
        if math.isclose(float(node.get("y", "nan")), dim_y - 9, abs_tol=EPSILON)
        and re.fullmatch(r"\d+[,.]\d+", _text(node))
    ]
    if len(labels) != len(contract["spans"]):
        raise CoordinationError("Great Wall segment dimension labels changed")
    features = []
    for label, span in zip(labels, contract["spans"], strict=True):
        length = span["end"] - span["start"]
        if _text(label) != f"{length:.2f}".replace(".", ","):
            raise CoordinationError(f"Great Wall segment label disagrees with source: {span['id']}")
        _close(
            label.get("x"),
            left + (span["start"] + span["end"]) * scale / 2,
            f"great-wall/{span['id']}/label",
        )
        features.append(
            {
                "id": f"segment-{span['id']}",
                "world_y": [span["start"], span["end"]],
                "source_paths": [
                    PB + ["core", span["index"], "y0"],
                    PB + ["core", span["index"], "y1"],
                ],
            }
        )
    total_label = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if math.isclose(float(node.get("y", "nan")), dim_y + 26, abs_tol=EPSILON)
        ],
        "Great Wall total-span label",
    )
    if _text(total_label) != f"{width:.2f} m".replace(".", ","):
        raise CoordinationError("Great Wall total span label disagrees with source")
    _close(total_label.get("x"), left + width * scale / 2, "great-wall/total-label")
    height_note = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if _text(node) == "HEIGHT NOT SOURCE-DEFINED · VERTICAL PROFILE IS SCHEMATIC"
        ],
        "Great Wall unresolved-height note",
    )
    _assert_untransformed_ancestry(
        root,
        [face, hatch, *lines, dimension_line, *ticks, *labels, total_label, height_note],
        GREAT_WALL,
    )

    unresolved = _source_unresolved(snapshot, contract)
    unresolved_ids = unresolved["doors"]["entity_ids"]
    door_shapes = [
        node
        for node in root.iter(_q("rect"))
        if node.get("fill") in {"none", "#806044"}
        and float(node.get("x", "-1")) >= left - EPSILON
        and float(node.get("x", "-1")) <= left + width * scale + EPSILON
        and float(node.get("y", "0")) > base - 3 * scale
    ]
    if unresolved_ids and door_shapes:
        raise CoordinationError("Great Wall renders a door at an unresolved CF-013 anchor")
    return {
        "state": "evaluated",
        "view_id": GREAT_WALL,
        "projection_id": "great-wall-source-context-v1",
        "feature_count": len(features) + 1,
        "features": [
            {
                "id": "great-wall-finish-field",
                "world_y": [0.0, width],
                "source_paths": [contract["width_path"]],
            },
            *features,
        ],
        "out_of_plane_context": {
            "plane_x_m": {"value": contract["plane_x"], "source_path": contract["plane_x_path"]},
            "thickness_m": {
                "value": contract["thickness"],
                "source_path": contract["thickness_path"],
            },
        },
        "unresolved_references": unresolved,
        "numerical_tolerance_px": EPSILON,
        "construction_tolerance": False,
        "scope": "Great Wall Y span and core-room divisions only; no wall height, door opening, wall solid, frame or finish performance is represented.",
    }


def _audit_media_wall(snapshot: Mapping[str, Any], root: ET.Element) -> dict[str, Any]:
    contract = _media_wall_contract(snapshot)
    header = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if node.get("data-context-feature") == "pb-media-title"
        ],
        "media-wall source header",
    )
    if (
        _text(header)
        != f"PB LIVING / {_display_number(float(contract['tv_diagonal_inches']))}-INCH TV ON SIDE B WALL"
    ):
        raise CoordinationError("PB media-wall title disagrees with TV source")
    wall_x, floor_y, scale = 70.0, 730.0, 150.0
    x0, x1 = float(contract["x0"]), float(contract["x1"])
    width = x1 - x0
    height = float(contract["height"])
    wall_y = floor_y - height * scale
    wall = _unique(
        [node for node in root.iter(_q("rect")) if node.get("fill") == "#c6a37b"],
        "media-wall field",
    )
    _assert_source_rect(
        wall,
        {"x": wall_x, "y": wall_y, "width": width * scale, "height": height * scale},
        "media-wall/elevation-field",
    )

    tv_width, tv_height = float(contract["tv_width"]), float(contract["tv_height"])
    tv_left = wall_x + (float(contract["tv_center_x"]) - x0 - tv_width / 2) * scale
    tv_center_y = floor_y - float(contract["tv_center_height"]) * scale
    tv_top = tv_center_y - tv_height * scale / 2
    tv = _unique(
        [node for node in root.iter(_q("rect")) if node.get("fill") == "#172126"],
        "TV equipment envelope",
    )
    _assert_source_rect(
        tv,
        {"x": tv_left, "y": tv_top, "width": tv_width * scale, "height": tv_height * scale},
        "media-wall/tv",
    )
    console_x = wall_x + (float(contract["console_x"]) - x0) * scale
    console_width = float(contract["console_length"]) * scale
    console_height = float(contract["console_height"]) * scale
    console_y = floor_y - console_height
    console = _unique(
        [node for node in root.iter(_q("rect")) if node.get("fill") == "#6f543e"],
        "AV console envelope",
    )
    _assert_source_rect(
        console,
        {"x": console_x, "y": console_y, "width": console_width, "height": console_height},
        "media-wall/console",
    )

    px = lambda value: 800.0 + (value - 13.0) * 58.0
    py = lambda value: 430.0 - (value - 11.0) * 38.0
    plan_y = py(float(contract["y"]))
    plan_wall = _unique(
        [node for node in root.iter(_q("line")) if node.get("stroke") == "#4b3b31"],
        "media-wall plan line",
    )
    _assert_source_rect(
        plan_wall, {"x1": px(x0), "y1": plan_y, "x2": px(x1), "y2": plan_y}, "media-wall/plan-field"
    )
    plan_tv = _unique(
        [node for node in root.iter(_q("line")) if node.get("stroke") == "#111719"],
        "TV plan envelope",
    )
    _assert_source_rect(
        plan_tv,
        {
            "x1": px(float(contract["tv_center_x"]) - tv_width / 2),
            "y1": plan_y + 5,
            "x2": px(float(contract["tv_center_x"]) + tv_width / 2),
            "y2": plan_y + 5,
        },
        "media-wall/plan-tv",
    )
    view_line = _unique(
        [node for node in root.iter(_q("line")) if node.get("stroke") == "#a46d20"],
        "viewing-distance line",
    )
    view_x = px(float(contract["tv_center_x"]))
    view_y = py(float(contract["viewing_point_y"]))
    _assert_source_rect(
        view_line,
        {"x1": view_x, "x2": view_x, "y1": view_y, "y2": plan_y},
        "media-wall/viewing-distance",
    )

    tv_specification = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if node.get("data-context-feature") == "pb-media-tv-specification"
        ],
        "TV specification label",
    )
    expected_tv_specification = (
        f"{_display_number(float(contract['tv_diagonal_inches']))}-IN TV EQUIPMENT ENVELOPE"
    )
    if _text(tv_specification) != expected_tv_specification:
        raise CoordinationError("PB TV diagonal label disagrees with source specification")
    tv_label = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if node.get("data-context-feature") == "pb-media-tv-envelope-dimensions"
        ],
        "TV dimension label",
    )
    expected_tv_label = f"{tv_width:.2f} × {tv_height:.2f} m · {contract['aspect_ratio']}"
    if _text(tv_label) != expected_tv_label:
        raise CoordinationError("PB TV size/aspect label disagrees with source envelope")
    tv_center_label = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if node.get("data-context-feature") == "pb-media-tv-center-height-label"
        ],
        "TV center-height label",
    )
    if _text(tv_center_label) != f"TV CENTRE +{float(contract['tv_center_height']):.2f} m AFF":
        raise CoordinationError("PB TV center-height label disagrees with source datum")
    console_label = _unique(
        [node for node in root.iter(_q("text")) if "ACCESSIBLE AV CONSOLE" in _text(node)],
        "console dimension label",
    )
    if _text(console_label) != f"{float(contract['console_length']):.2f} m ACCESSIBLE AV CONSOLE":
        raise CoordinationError("PB console label disagrees with source length")
    field_label = _unique(
        [node for node in root.iter(_q("text")) if "MOUNTING FIELD" in _text(node)],
        "mounting-field label",
    )
    if not _text(field_label).startswith(f"{width:.2f} m MOUNTING FIELD"):
        raise CoordinationError("PB mounting-field label disagrees with source span")
    view_label = _unique(
        [node for node in root.iter(_q("text")) if _text(node).endswith("m VIEW")],
        "viewing-distance label",
    )
    if not _text(view_label).startswith(f"{float(contract['viewing_distance']):.2f} m VIEW"):
        raise CoordinationError("PB viewing-distance label disagrees with source datums")
    height_label = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if node.get("data-context-feature") == "pb-media-mounting-field-height-label"
        ],
        "mounting-field-height label",
    )
    if _text(height_label) != f"{height:.2f} m":
        raise CoordinationError("PB mounting-field-height label disagrees with source height")

    source_measurements = {
        "width": contract["paths"]["tv_width"],
        "height": contract["paths"]["tv_height"],
    }
    if tv.get("data-context-measurement-bindings"):
        try:
            observed = json.loads(tv.get("data-context-measurement-bindings", ""))
        except ValueError as error:
            raise CoordinationError("Invalid PB TV dimension source paths") from error
        if observed != source_measurements:
            raise CoordinationError("PB TV dimension source paths changed")
    _assert_untransformed_ancestry(
        root,
        [
            wall,
            tv,
            console,
            plan_wall,
            plan_tv,
            view_line,
            tv_specification,
            tv_label,
            tv_center_label,
            console_label,
            field_label,
            height_label,
        ],
        PB_MEDIA_WALL,
    )
    return {
        "state": "evaluated",
        "view_id": PB_MEDIA_WALL,
        "projection_id": "pb-media-wall-context-v1",
        "feature_count": 4,
        "features": [
            {
                "id": "mounting-field",
                "x": [x0, x1],
                "height_m": height,
                "y": float(contract["y"]),
                "source_paths": [
                    contract["paths"]["x0"],
                    contract["paths"]["x1"],
                    contract["paths"]["height"],
                    contract["paths"]["y"],
                ],
            },
            {
                "id": "tv-envelope",
                "x_center": float(contract["tv_center_x"]),
                "center_height_aff_m": float(contract["tv_center_height"]),
                "width_m": tv_width,
                "height_m": tv_height,
                "diagonal_inches": float(contract["tv_diagonal_inches"]),
                "aspect_ratio": contract["aspect_ratio"],
                "source_paths": [
                    contract["paths"]["tv_center_x"],
                    contract["paths"]["tv_center_height"],
                    contract["paths"]["tv_diagonal_inches"],
                    contract["paths"]["aspect_ratio"],
                    *source_measurements.values(),
                ],
            },
            {
                "id": "console-envelope",
                "x": [
                    float(contract["console_x"]),
                    float(contract["console_x"]) + float(contract["console_length"]),
                ],
                "height_m": float(contract["console_height"]),
                "source_paths": [
                    contract["paths"]["console_x"],
                    contract["paths"]["console_length"],
                    contract["paths"]["console_height"],
                ],
            },
            {
                "id": "viewing-distance",
                "y": [float(contract["viewing_point_y"]), float(contract["y"])],
                "distance_m": float(contract["viewing_distance"]),
                "source_paths": [
                    contract["paths"]["viewing_point_y"],
                    contract["paths"]["y"],
                    contract["paths"]["viewing_distance"],
                ],
            },
        ],
        "panel_projections": {
            "elevation": {
                "axes": ["x", "z"],
                "scale": [scale, -scale],
                "offset": [wall_x - x0 * scale, floor_y],
            },
            "plan": {"axes": ["x", "y"], "scale": [58.0, -38.0], "offset": [46.0, 848.0]},
        },
        "unresolved_references": [
            "TV and console are owner equipment envelopes; selected products, mount, backing capacity, services and replacement access remain open."
        ],
        "numerical_tolerance_px": EPSILON,
        "construction_tolerance": False,
        "scope": "PB Side B mounting-field, TV/console coordination envelopes and viewing relation from captured discipline inputs; no selected-product or capacity claim.",
    }


def audit_wall_context(snapshot: Mapping[str, Any], root: ET.Element) -> dict[str, Any] | None:
    """Audit a supported sheet; mismatched source graphics fail instead of relabeling."""
    view_id = root.get("data-view-id")
    if view_id == GREAT_WALL:
        return _audit_great_wall(snapshot, root)
    if view_id == PB_MEDIA_WALL:
        return _audit_media_wall(snapshot, root)
    return None


def _anchor(
    group: ET.Element,
    view_id: str,
    name: str,
    point: tuple[float, float],
    coordinates: Mapping[str, float],
    bindings: Mapping[str, Any],
) -> tuple[str, str]:
    semantic_id = f"{view_id}.{name}"
    dom_id = f"{_token(view_id)}-context-anchor-{_token(name)}"
    attributes = {
        "id": dom_id,
        "cx": _fmt(point[0]),
        "cy": _fmt(point[1]),
        "r": "0",
        "fill": "none",
        "data-anchor-id": semantic_id,
        "data-anchor-context-id": "PROJECT.PB",
        "data-anchor-status": "resolved",
        "data-anchor-bindings": json.dumps(bindings, sort_keys=True, separators=(",", ":")),
    }
    attributes.update({f"data-world-{axis}": _fmt(value) for axis, value in coordinates.items()})
    ET.SubElement(group, _q("circle"), attributes)
    return semantic_id, dom_id


def _spec(
    name: str,
    point: tuple[float, float],
    axis: str,
    value: float,
    binding: Any,
) -> tuple[str, tuple[float, float], Mapping[str, float], Mapping[str, Any]]:
    return name, point, {axis: value}, {axis: binding}


def _dimension(
    group: ET.Element,
    view_id: str,
    name: str,
    label: ET.Element,
    value: float,
    start: tuple[str, tuple[float, float], Mapping[str, float], Mapping[str, Any]],
    end: tuple[str, tuple[float, float], Mapping[str, float], Mapping[str, Any]],
    source: str,
    *,
    direction: str = "parallel",
    label_format: str,
) -> dict[str, Any]:
    refs = []
    targets = []
    for suffix, item in (("start", start), ("end", end)):
        ref, target = _anchor(group, view_id, f"{name}.{suffix}", item[1], item[2], item[3])
        refs.append(ref)
        targets.append(target)
    label.set("id", f"{_token(view_id)}-dimension-label-{_token(name)}")
    label.set("data-dimension-id", f"{view_id}.{name}")
    label.set("data-anchor-refs", " ".join(refs))
    label.set("data-anchor-targets", " ".join(targets))
    label.set("data-dimension-status", "resolved")
    label.set("data-dimension-direction", direction)
    label.set("data-dimension-value", _fmt(value))
    label.set("data-dimension-unit", "m")
    label.set("data-dimension-source", source)
    label.set("data-dimension-label-format", label_format)
    return {"dimension_id": name, "value_m": value, "source": source}


def _annotate_great_wall(
    snapshot: Mapping[str, Any], root: ET.Element, group: ET.Element
) -> list[dict[str, Any]]:
    contract = _great_wall_contract(snapshot)
    view_id = GREAT_WALL
    left, base, scale = 120.0, 610.0, 63.0
    dim_y = base + 115.0
    labels = [
        node
        for node in root.iter(_q("text"))
        if math.isclose(float(node.get("y", "nan")), dim_y - 9, abs_tol=EPSILON)
        and re.fullmatch(r"\d+[,.]\d+", _text(node))
    ]
    dimensions = []
    for label, span in zip(labels, contract["spans"], strict=True):
        index = int(span["index"])
        start_path, end_path = PB + ["core", index, "y0"], PB + ["core", index, "y1"]
        start = _spec(
            f"segment-{span['id']}.start",
            (left + span["start"] * scale, dim_y),
            "y",
            span["start"],
            start_path,
        )
        end = _spec(
            f"segment-{span['id']}.end",
            (left + span["end"] * scale, dim_y),
            "y",
            span["end"],
            end_path,
        )
        dimensions.append(
            _dimension(
                group,
                view_id,
                f"segment-{span['id']}",
                label,
                span["end"] - span["start"],
                start,
                end,
                f"discipline_inputs.equipment.pb.core[{index}].y0 → .y1",
                label_format="fixed-2-comma",
            )
        )
    total = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if math.isclose(float(node.get("y", "nan")), dim_y + 26, abs_tol=EPSILON)
        ],
        "Great Wall total span label",
    )
    first = contract["spans"][0]
    start = _spec(
        "total-span.start", (left, dim_y), "y", first["start"], PB + ["core", first["index"], "y0"]
    )
    end = _spec(
        "total-span.end",
        (left + contract["width"] * scale, dim_y),
        "y",
        contract["width"],
        ["geometry", "hall", "width_m"],
    )
    dimensions.append(
        _dimension(
            group,
            view_id,
            "total-span",
            total,
            contract["width"],
            start,
            end,
            "geometry.hall.width_m",
            label_format="fixed-2-comma-m",
        )
    )

    unresolved = _source_unresolved(snapshot, contract)
    root.set(
        "data-context-wall-plane",
        json.dumps(
            {
                "x_m": {"value": contract["plane_x"], "source": contract["plane_x_path"]},
                "thickness_m": {
                    "value": contract["thickness"],
                    "source": contract["thickness_path"],
                },
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    root.set(
        "data-context-unresolved", json.dumps(unresolved, sort_keys=True, separators=(",", ":"))
    )
    return dimensions


def _annotate_media_wall(
    snapshot: Mapping[str, Any], root: ET.Element, group: ET.Element
) -> list[dict[str, Any]]:
    contract = _media_wall_contract(snapshot)
    view_id = PB_MEDIA_WALL
    ex, ey, scale = 70.0, 730.0, 150.0
    px = lambda x: 800.0 + (x - 13.0) * 58.0
    py = lambda y: 430.0 - (y - 11.0) * 38.0
    x0, x1 = float(contract["x0"]), float(contract["x1"])
    wall_y, width = float(contract["y"]), x1 - x0
    level = float(contract["level"])
    paths = contract["paths"]
    dimensions = []

    field_label = _unique(
        [node for node in root.iter(_q("text")) if "MOUNTING FIELD" in _text(node)],
        "mounting-field label",
    )
    dimensions.append(
        _dimension(
            group,
            view_id,
            "mounting-field-width",
            field_label,
            width,
            _spec("field.start", (ex, ey + 28), "x", x0, paths["x0"]),
            _spec("field.end", (ex + width * scale, ey + 28), "x", x1, paths["x1"]),
            "discipline_inputs.equipment.pb.social_layout.media_wall.x0 → .x1",
            label_format="numeric-prefix-fixed-2-m",
        )
    )

    console_label = _unique(
        [node for node in root.iter(_q("text")) if "ACCESSIBLE AV CONSOLE" in _text(node)],
        "console label",
    )
    cx, cl = float(contract["console_x"]), float(contract["console_length"])
    dimensions.append(
        _dimension(
            group,
            view_id,
            "console-length",
            console_label,
            cl,
            _spec("console.start", (ex + (cx - x0) * scale, ey + 35), "x", cx, paths["console_x"]),
            _spec(
                "console.end",
                (ex + (cx + cl - x0) * scale, ey + 35),
                "x",
                cx + cl,
                {"sum": [paths["console_x"], paths["console_length"]]},
            ),
            "discipline_inputs.equipment.pb.social_layout.media_wall.console.x + .length",
            label_format="numeric-prefix-fixed-2-m",
        )
    )

    view_label = _unique(
        [node for node in root.iter(_q("text")) if _text(node).endswith("m VIEW")],
        "viewing-distance label",
    )
    view_start, view_end = float(contract["viewing_point_y"]), wall_y
    view_x = px(float(contract["tv_center_x"]))
    dimensions.append(
        _dimension(
            group,
            view_id,
            "viewing-distance",
            view_label,
            float(contract["viewing_distance"]),
            _spec(
                "viewing.start", (view_x, py(view_start)), "y", view_start, paths["viewing_point_y"]
            ),
            _spec("viewing.end", (view_x, py(view_end)), "y", view_end, paths["y"]),
            "discipline_inputs.equipment.pb.social_layout.media_wall.viewing_point_y → .y",
            label_format="numeric-prefix-fixed-2-m",
        )
    )

    tv_label = _unique(
        [node for node in root.iter(_q("text")) if "TV CENTRE" in _text(node)],
        "TV center-height label",
    )
    tv_center_height = float(contract["tv_center_height"])
    center_screen_x = ex + (float(contract["tv_center_x"]) - x0) * scale
    dimensions.append(
        _dimension(
            group,
            view_id,
            "tv-center-height",
            tv_label,
            tv_center_height,
            _spec("tv-center.start", (center_screen_x, ey), "z", level, PB_LEVEL),
            _spec(
                "tv-center.end",
                (center_screen_x, ey - tv_center_height * scale),
                "z",
                level + tv_center_height,
                {"sum": [PB_LEVEL, paths["tv_center_height"]]},
            ),
            "PB finished-floor datum + media_wall.tv_center_height",
            direction="vertical level comparison",
            label_format="tv-centre-fixed-2-m",
        )
    )

    wall_height = float(contract["height"])
    height_label = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if node.get("data-context-feature") == "pb-media-mounting-field-height-label"
        ],
        "mounting-field-height label",
    )
    dimensions.append(
        _dimension(
            group,
            view_id,
            "mounting-field-height",
            height_label,
            wall_height,
            _spec("wall-height.start", (ex + width * scale, ey), "z", level, PB_LEVEL),
            _spec(
                "wall-height.end",
                (ex + width * scale, ey - wall_height * scale),
                "z",
                level + wall_height,
                {"sum": [PB_LEVEL, paths["height"]]},
            ),
            "PB finished-floor datum + media_wall.height",
            direction="vertical level comparison",
            label_format="fixed-2-m",
        )
    )

    tv = _unique(
        [node for node in root.iter(_q("rect")) if node.get("fill") == "#172126"], "TV envelope"
    )
    tv.set(
        "data-context-measurement-bindings",
        json.dumps(
            {"width": paths["tv_width"], "height": paths["tv_height"]},
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    return dimensions


def annotate_wall_context(snapshot: Mapping[str, Any], root: ET.Element) -> dict[str, Any] | None:
    """Audit then attach source-bound dimensions for either supported PB wall view."""
    view_id = root.get("data-view-id")
    if view_id not in VIEWS:
        return None
    group_id = f"{view_id}-source-context-annotations"
    if any(node.get("id") == group_id for node in root.iter()):
        raise CoordinationError(f"Wall context annotations already exist for {view_id}")
    audit = audit_wall_context(snapshot, root)
    assert audit is not None
    group = ET.Element(
        _q("g"),
        {
            "id": group_id,
            "data-annotation-scope": "source-bound-wall-context-dimensions",
            "data-geometry-projection-id": audit["projection_id"],
            "font-family": "IBM Plex Sans",
        },
    )
    dimensions = (
        _annotate_great_wall(snapshot, root, group)
        if view_id == GREAT_WALL
        else _annotate_media_wall(snapshot, root, group)
    )
    root.set(
        "data-view-purpose",
        "source-bound Great Wall plan span and core zones"
        if view_id == GREAT_WALL
        else "source-bound PB Side B media-wall equipment coordination",
    )
    root.set("data-projection-basis", audit["scope"])
    root.set("data-projected-axes", "y z" if view_id == GREAT_WALL else "x y z")
    root.set("data-context-projection-id", audit["projection_id"])
    if view_id == PB_MEDIA_WALL:
        root.set(
            "data-context-unresolved",
            json.dumps(audit["unresolved_references"], separators=(",", ":")),
        )
    root.append(group)
    checked = audit_wall_context(snapshot, root)
    return {
        "status": "supported",
        "reason": None,
        "geometry_binding": checked,
        "anchors": len(dimensions) * 2,
        "dimensions": len(dimensions),
        "supported_scope": audit["scope"],
        "unresolved_references": audit["unresolved_references"],
    }


__all__ = ["VIEWS", "annotate_wall_context", "audit_wall_context", "render_wall_context"]

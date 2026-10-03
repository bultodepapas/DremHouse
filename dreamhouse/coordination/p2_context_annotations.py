"""Source-context audits for schematic P2 wall details without wall-solid claims."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from typing import Any
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import CoordinationError

SVG_NS = "http://www.w3.org/2000/svg"
P2 = ["discipline_inputs", "programme", "p2"]
CONTEXT_VIEWS = {
    "architecture-p2-acoustic-partition",
    "architecture-p2-hall-edge",
    "architecture-p2-exterior-wall",
}


def _q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


def _path(path: list[str | int]) -> str:
    return ".".join(str(part) for part in path)


def _value(snapshot: Mapping[str, Any], path: list[str | int]) -> float:
    current: Any = snapshot
    try:
        for part in path:
            current = current[part]
    except (KeyError, IndexError, TypeError) as error:
        raise CoordinationError(f"Missing P2 context source {_path(path)}") from error
    if type(current) not in {int, float} or not math.isfinite(float(current)):
        raise CoordinationError(f"Invalid numeric P2 context source {_path(path)}")
    return float(current)


def _mapping(snapshot: Mapping[str, Any], path: list[str | int]) -> Mapping[str, Any]:
    current: Any = snapshot
    try:
        for part in path:
            current = current[part]
    except (KeyError, IndexError, TypeError) as error:
        raise CoordinationError(f"Missing P2 context source {_path(path)}") from error
    if not isinstance(current, Mapping):
        raise CoordinationError(f"Invalid P2 context source {_path(path)}")
    return current


def _number(element: ET.Element, attribute: str, label: str) -> float:
    raw = element.get(attribute)
    try:
        value = float(raw) if raw is not None else math.nan
    except (TypeError, ValueError, OverflowError) as error:
        raise CoordinationError(f"Invalid P2 context SVG coordinate {label}.{attribute}") from error
    if not math.isfinite(value):
        raise CoordinationError(f"Invalid P2 context SVG coordinate {label}.{attribute}")
    return value


def _close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-6):
        raise CoordinationError(
            f"P2 context projection mismatch {label}: rendered {actual:.9g}, source projects to {expected:.9g}"
        )


def _visible_text(element: ET.Element) -> str:
    return "".join(element.itertext()).strip()


def _elements(root: ET.Element, tag: str, *, class_name: str | None = None) -> list[ET.Element]:
    found = []
    for element in root.iter(_q(tag)):
        if class_name is None or class_name in element.get("class", "").split():
            found.append(element)
    return found


def _check_untransformed(root: ET.Element, element: ET.Element, label: str) -> None:
    parents = {child: parent for parent in root.iter() for child in parent}
    node: ET.Element | None = element
    while node is not None:
        if node.get("transform") or re.search(
            r"(?:^|;)\s*transform\s*:", node.get("style", ""), re.IGNORECASE
        ):
            raise CoordinationError(f"Transformed P2 context geometry is unsupported: {label}")
        node = parents.get(node)


def _tag(element: ET.Element, view: str, name: str, source_paths: list[list[str | int]]) -> None:
    stable = re.sub(r"[^A-Za-z0-9_.-]+", "-", f"{view}-{name}").strip("-.")
    current = element.get("data-p2-context-feature")
    if current not in {None, name}:
        raise CoordinationError(f"P2 context feature identity changed in {view}/{name}")
    existing_id = element.get("id")
    wanted_id = f"{stable}-source-context"
    if existing_id not in {None, wanted_id} and element.get("data-p2-context-feature") == name:
        raise CoordinationError(f"P2 context feature occurrence ID changed in {view}/{name}")
    element.set("id", existing_id or wanted_id)
    element.set("data-p2-context-feature", name)
    element.set("data-p2-context-source-paths", json.dumps(source_paths, separators=(",", ":")))


def _tag_context_features(root: ET.Element, view: str, audit: Mapping[str, Any]) -> None:
    for feature in audit["features"]:
        name = str(feature["feature_id"])
        source_paths = feature.get("source_paths", [])
        if source_paths and isinstance(source_paths[0], str):
            normalized_paths = [path.split(".") for path in source_paths]
        else:
            normalized_paths = source_paths
        matches = []
        if "svg_rect" in feature:
            target = feature["svg_rect"]
            for element in _elements(root, "rect"):
                if feature.get("svg_class") and feature["svg_class"] not in element.get("class", "").split():
                    continue
                try:
                    if all(
                        math.isclose(
                            _number(element, attribute, name),
                            float(target[attribute]),
                            rel_tol=0.0,
                            abs_tol=1e-6,
                        )
                        for attribute in ("x", "y", "width", "height")
                    ):
                        matches.append(element)
                except CoordinationError:
                    continue
        elif "svg_line" in feature:
            target = feature["svg_line"]
            for element in _elements(root, "line"):
                try:
                    values = [_number(element, key, name) for key in ("x1", "y1", "x2", "y2")]
                except CoordinationError:
                    continue
                if all(math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-6) for actual, expected in zip(values, target, strict=True)):
                    matches.append(element)
        elif "visible_text" in feature:
            matches = []
            position = feature.get("svg_text_position")
            for element in _elements(root, "text"):
                if _visible_text(element) != feature["visible_text"]:
                    continue
                if position is not None and not all(
                    math.isclose(
                        _number(element, attribute, name),
                        float(expected),
                        rel_tol=0.0,
                        abs_tol=1e-6,
                    )
                    for attribute, expected in zip(("x", "y"), position, strict=True)
                ):
                    continue
                matches.append(element)
        if len(matches) != 1:
            raise CoordinationError(f"P2 context occurrence changed in {view}/{name}: {len(matches)} matches")
        _tag(matches[0], view, name, normalized_paths)
        if name.endswith("layer-sum-label"):
            source_values = audit["source_values"]
            matches[0].set("data-p2-context-dimension-id", str(feature["feature_id"]).replace("-label", ""))
            matches[0].set(
                "data-p2-context-dimension-value",
                f"{source_values['illustrative_layer_sum_mm']:g}",
            )
            matches[0].set("data-p2-context-dimension-unit", "mm")
            matches[0].set(
                "data-p2-context-nominal-mm", f"{source_values['nominal_thickness_mm']:g}"
            )
            if source_values.get("inherited_layer_note_mm") is not None:
                matches[0].set(
                    "data-p2-context-stale-note-mm", f"{source_values['inherited_layer_note_mm']:g}"
                )
            if "inherited_layer_note" in source_values:
                matches[0].set(
                    "data-p2-context-inherited-note", str(source_values["inherited_layer_note"])
                )


def _same_rect(
    element: ET.Element,
    *,
    x: float,
    y: float | None = None,
    width: float,
    height: float,
    label: str,
) -> None:
    for attribute, expected in (("x", x), ("y", y), ("width", width), ("height", height)):
        _close(_number(element, attribute, label), expected, f"{label}.{attribute}")


def _source_layers(snapshot: Mapping[str, Any], assembly_key: str, layers_key: str) -> tuple[list, list]:
    assembly_path = P2 + [assembly_key]
    assembly = _mapping(snapshot, assembly_path)
    layers = assembly.get(layers_key)
    if not isinstance(layers, list) or not layers:
        raise CoordinationError(f"Missing P2 context layer list {_path(assembly_path + [layers_key])}")
    paths = [assembly_path + [layers_key, index, "nominal_mm"] for index in range(len(layers))]
    thicknesses = [_value(snapshot, path) for path in paths]
    if any(value <= 0 for value in thicknesses):
        raise CoordinationError(f"Nonpositive P2 layer thickness in {_path(assembly_path + [layers_key])}")
    return layers, paths


def _fmt(value: float) -> str:
    return f"{value:.12g}"


def _text_at(
    root: ET.Element,
    *,
    x: float | None = None,
    x_max: float | None = None,
    y: float,
    startswith: str | None = None,
    label: str,
) -> ET.Element:
    matches = []
    for element in _elements(root, "text"):
        try:
            if y is not None and not math.isclose(
                _number(element, "y", label), y, rel_tol=0.0, abs_tol=1e-6
            ):
                continue
            if x is not None and not math.isclose(
                _number(element, "x", label), x, rel_tol=0.0, abs_tol=1e-6
            ):
                continue
            if x_max is not None and _number(element, "x", label) >= x_max:
                continue
        except CoordinationError:
            continue
        if startswith is not None and not _visible_text(element).startswith(startswith):
            continue
        matches.append(element)
    if len(matches) != 1:
        raise CoordinationError(f"P2 context source label is missing or ambiguous: {label}")
    return matches[0]


def _set_label(element: ET.Element, text: str, label: str) -> None:
    if list(element):
        raise CoordinationError(f"Unsupported nested P2 context label: {label}")
    element.text = text


def _legend_text(layer: Mapping[str, Any]) -> str:
    material = str(layer.get("material", ""))
    value = _value(layer, ["nominal_mm"])
    descriptions = {
        "insulated corrugated metal facade panel": "INSULATED CORRUGATED FACADE PANEL · TEST VALUE",
        "clear service and decoupling cavity": "CLEAR DRAINABLE / SERVICE / DECOUPLING ZONE",
        "metal stud frame with glass-wool infill": "INDEPENDENT SERVICE FRAME",
        "reclaimed gypsum board": "RECLAIMED BOARD · CONCEALED ONLY",
        "new gypsum board": "NEW SMOOTH FINISH BOARD",
    }
    if material not in descriptions:
        raise CoordinationError(f"Unsupported exterior P2 context material {material!r}")
    description = descriptions[material]
    if material == "metal stud frame with glass-wool infill":
        infill = _value(layer, ["infill_nominal_mm"])
        description += f" + {_fmt(infill)} GLASS WOOL"
    return f"{_fmt(value)} {description}"


def prepare_p2_context_view(snapshot: dict, root: ET.Element) -> dict | None:
    """Refresh hard-coded renderer labels from snapshot values before projection audit."""
    view = str(root.get("data-view-id"))
    if view not in CONTEXT_VIEWS:
        return None
    if view == "architecture-p2-acoustic-partition":
        assembly_path = P2 + ["acoustic_partition"]
        assembly = _mapping(snapshot, assembly_path)
        layers, _ = _source_layers(snapshot, "acoustic_partition", "room_side_to_room_side_layers")
        nominal_mm = _value(snapshot, assembly_path + ["nominal_total_m"]) * 1000.0
        layer_sum_mm = sum(_value(snapshot, assembly_path + ["room_side_to_room_side_layers", index, "nominal_mm"]) for index in range(len(layers)))
        _set_label(
            _text_at(root, x_max=900.0, y=545.0, label=view + "/layer-sum-label"),
            f"{_fmt(nominal_mm)} mm NOMINAL · {_fmt(layer_sum_mm)} mm ILLUSTRATIVE SUM",
            view + "/layer-sum-label",
        )
        title = _text_at(root, x=70.0, y=500.0, startswith="P2-W01B · ", label=view + "/assembly-title")
        _set_label(
            title,
            f"P2-W01B · {_fmt(nominal_mm)} mm · SUITE / COMMON SEPARATION",
            view + "/assembly-title",
        )
        _mapping(snapshot, P2 + ["wall_schedule"])
        row_ids = ("P2-W01A", "P2-W01B", "P2-W02", "P2-W02S", "P2-W03", "P2-W04R", "P2-W05", "P2-W06")
        for index, wall_id in enumerate(row_ids):
            y = 245.0 + index * 50.0
            wall_label = _text_at(root, x=980.0, y=y, label=f"{view}/{wall_id}/schedule-id")
            if _visible_text(wall_label) != wall_id:
                raise CoordinationError(f"P2 wall schedule row changed: {wall_id}")
            row = _mapping(snapshot, P2 + ["wall_schedule", wall_id])
            row_mm = _value(snapshot, P2 + ["wall_schedule", wall_id, "nominal_total_m"]) * 1000.0
            _set_label(
                _text_at(root, x=1115.0, y=y, label=f"{view}/{wall_id}/schedule-value"),
                f"{_fmt(row_mm)} mm",
                f"{view}/{wall_id}/schedule-value",
            )
            if not row.get("name"):
                raise CoordinationError(f"Missing P2 wall schedule identity for {wall_id}")
        return {"state": "prepared", "view_id": view}
    if view == "architecture-p2-hall-edge":
        wall_path = P2 + ["hall_edge_partition"]
        balcony_path = P2 + ["family_balcony"]
        wall_from = _value(snapshot, wall_path + ["from_y"])
        wall_to = _value(snapshot, wall_path + ["to_y"])
        open_from = _value(snapshot, balcony_path + ["from_y"])
        open_to = _value(snapshot, balcony_path + ["to_y"])
        full = wall_to - wall_from
        open_length = open_to - open_from
        label = (
            f"{full:.2f} m HALL EDGE · {open_length:.2f} m OPEN / "
            f"{full - open_length:.2f} m ENCLOSED"
        )
        _set_label(
            _text_at(root, x=470.0, y=205.0, label=view + "/overall-summary"),
            label,
            view + "/overall-summary",
        )
        return {"state": "prepared", "view_id": view}
    assembly_path = P2 + ["exterior_wall_assembly"]
    assembly = _mapping(snapshot, assembly_path)
    layers, _ = _source_layers(snapshot, "exterior_wall_assembly", "outside_to_inside_layers")
    nominal_mm = _value(snapshot, assembly_path + ["nominal_total_m"]) * 1000.0
    layer_sum_mm = sum(
        _value(snapshot, assembly_path + ["outside_to_inside_layers", index, "nominal_mm"])
        for index in range(len(layers))
    )
    _set_label(
        _text_at(root, y=230.0, label=view + "/layer-sum-label"),
        f"{_fmt(nominal_mm)} mm NOMINAL · {_fmt(layer_sum_mm)} mm ILLUSTRATIVE SUM",
        view + "/layer-sum-label",
    )
    title = _text_at(
        root,
        y=165.0,
        startswith="OUTSIDE-TO-INSIDE BUILD-UP · ",
        label=view + "/assembly-title",
    )
    _set_label(
        title,
        f"OUTSIDE-TO-INSIDE BUILD-UP · {_fmt(nominal_mm)} mm NOMINAL",
        view + "/assembly-title",
    )
    subtitle = _text_at(
        root, x=1040.0, y=76.0, startswith="D-080 · ", label=view + "/header-subtitle"
    )
    subtitle_text = _visible_text(subtitle)
    subtitle_text = re.sub(r"\d+(?:\.\d+)? mm nominal", f"{_fmt(nominal_mm)} mm nominal", subtitle_text, count=1)
    _set_label(subtitle, subtitle_text, view + "/header-subtitle")
    for index, layer in enumerate(layers):
        y = 650.0 + index * 48.0
        _set_label(
            _text_at(root, x=137.0, y=y, label=f"{view}/layer-{index + 1}/legend"),
            _legend_text(layer),
            f"{view}/layer-{index + 1}/legend",
        )
    return {"state": "prepared", "view_id": view, "source_layer_note": assembly.get("layer_sum_note")}


def _layer_profile(
    snapshot: Mapping[str, Any],
    root: ET.Element,
    *,
    assembly_key: str,
    layers_key: str,
    top: float,
    height: float,
    scale_px_per_mm: float,
    origin_x: float,
    view: str,
    svg_class: str = "wall-layer",
) -> dict[str, Any]:
    layers, paths = _source_layers(snapshot, assembly_key, layers_key)
    candidates = [
        element
        for element in _elements(root, "rect", class_name=svg_class)
        if math.isclose(_number(element, "y", "wall-layer"), top, rel_tol=0.0, abs_tol=1e-6)
        and math.isclose(
            _number(element, "height", "wall-layer"), height, rel_tol=0.0, abs_tol=1e-6
        )
    ]
    if len(candidates) != len(layers):
        raise CoordinationError(
            f"P2 context layer count changed in {view}: source={len(layers)}, rendered={len(candidates)}"
        )
    candidates.sort(key=lambda element: _number(element, "x", "wall-layer"))
    cursor = origin_x
    features = []
    for index, (element, layer, source_path) in enumerate(
        zip(candidates, layers, paths, strict=True), start=1
    ):
        thickness_mm = _value(snapshot, source_path)
        material = str(layer.get("material", ""))
        if not material:
            raise CoordinationError(f"Missing source material at {_path(source_path[:-1])}")
        material_class = material.replace(" ", "-").lower()
        if material_class not in element.get("class", "").split():
            raise CoordinationError(f"P2 context material identity changed in {view}/layer-{index}")
        _check_untransformed(root, element, f"{view}/layer-{index}")
        _same_rect(
            element,
            x=cursor,
            y=top,
            width=thickness_mm * scale_px_per_mm,
            height=height,
            label=f"{view}/layer-{index}",
        )
        feature_name = f"{assembly_key}-layer-{index:02d}"
        features.append(
            {
                "feature_id": feature_name,
                "source_path": _path(source_path),
                "source_paths": [source_path],
                "material": material,
                "nominal_mm": thickness_mm,
                "svg_rect": {
                    "x": cursor,
                    "y": top,
                    "width": thickness_mm * scale_px_per_mm,
                    "height": height,
                },
            }
        )
        cursor += thickness_mm * scale_px_per_mm
    return {"features": features, "end_x": cursor, "layers": layers, "paths": paths}


def _audit_acoustic(snapshot: Mapping[str, Any], root: ET.Element) -> dict[str, Any]:
    view = "architecture-p2-acoustic-partition"
    contract = _layer_profile(
        snapshot,
        root,
        assembly_key="acoustic_partition",
        layers_key="room_side_to_room_side_layers",
        top=555.0,
        height=126.0,
        scale_px_per_mm=3.0,
        origin_x=120.0,
        view=view,
    )
    assembly_path = P2 + ["acoustic_partition"]
    nominal_path = assembly_path + ["nominal_total_m"]
    schedule_path = P2 + ["wall_schedule", "P2-W01B", "nominal_total_m"]
    nominal_mm = _value(snapshot, nominal_path) * 1000.0
    schedule_nominal_mm = _value(snapshot, schedule_path) * 1000.0
    layer_sum_mm = sum(feature["nominal_mm"] for feature in contract["features"])
    expected_label = f"{_fmt(nominal_mm)} mm NOMINAL · {_fmt(layer_sum_mm)} mm ILLUSTRATIVE SUM"
    labels = [element for element in _elements(root, "text") if _visible_text(element) == expected_label]
    if len(labels) != 1:
        raise CoordinationError(f"P2-W01B source layer label changed in {view}")
    bracket = [
        element
        for element in _elements(root, "line")
        if math.isclose(_number(element, "x1", view), 120.0, abs_tol=1e-6)
        and math.isclose(_number(element, "x2", view), contract["end_x"], abs_tol=1e-6)
        and math.isclose(_number(element, "y1", view), 553.0, abs_tol=1e-6)
        and math.isclose(_number(element, "y2", view), 553.0, abs_tol=1e-6)
    ]
    if len(bracket) != 1:
        raise CoordinationError(f"P2-W01B layer-sum line changed in {view}")
    _check_untransformed(root, bracket[0], view + "/layer-sum")
    source_paths = [*contract["paths"], nominal_path, schedule_path]
    schedule = _mapping(snapshot, P2 + ["wall_schedule"])
    row_ids = ("P2-W01A", "P2-W01B", "P2-W02", "P2-W02S", "P2-W03", "P2-W04R", "P2-W05", "P2-W06")
    schedule_rows = []
    for index, wall_id in enumerate(row_ids):
        value_path = P2 + ["wall_schedule", wall_id, "nominal_total_m"]
        value_mm = _value(snapshot, value_path) * 1000.0
        label_text = f"{_fmt(value_mm)} mm"
        text_position = [1115.0, 245.0 + index * 50.0]
        value_labels = [
            element
            for element in _elements(root, "text")
            if _visible_text(element) == label_text
            and math.isclose(_number(element, "x", view), text_position[0], abs_tol=1e-6)
            and math.isclose(_number(element, "y", view), text_position[1], abs_tol=1e-6)
        ]
        if wall_id not in schedule or len(value_labels) != 1:
            raise CoordinationError(f"P2 wall schedule value changed in {view}/{wall_id}")
        schedule_rows.append(
            {
                "feature_id": f"wall-schedule-{wall_id}-nominal",
                "source_paths": [_path(value_path)],
                "visible_text": label_text,
                "svg_text_position": text_position,
            }
        )
    return {
        "state": "evaluated",
        "projection_id": "p2-w01b-schematic-layer-profile-v1",
        "feature_count": len(contract["features"]) + 2 + len(schedule_rows),
        "features": contract["features"]
        + [
            {
                "feature_id": "acoustic_partition-layer-sum",
                "source_paths": [_path(path) for path in contract["paths"]],
                "svg_line": [120.0, 553.0, contract["end_x"], 553.0],
            },
            {
                "feature_id": "acoustic_partition-layer-sum-label",
                "source_paths": [_path(path) for path in source_paths],
                "visible_text": expected_label,
            },
        ]
        + schedule_rows,
        "source_values": {
            "nominal_thickness_mm": nominal_mm,
            "wall_schedule_nominal_mm": schedule_nominal_mm,
            "nominal_values_match": math.isclose(
                nominal_mm, schedule_nominal_mm, rel_tol=0.0, abs_tol=1e-6
            ),
            "illustrative_layer_sum_mm": layer_sum_mm,
            "wall_schedule_authority": _mapping(snapshot, P2 + ["wall_schedule", "P2-W01B"])[
                "authority"
            ],
        },
        "scope": (
            f"Source-bound schematic layer widths: {nominal_mm:g} mm assembly nominal, "
            f"{schedule_nominal_mm:g} mm wall-schedule nominal, and {layer_sum_mm:g} mm illustrative sum; "
            "drawn panel height is not wall height, and no acoustic/fire rating or selected assembly is claimed."
        ),
    }


def _audit_hall_edge(snapshot: Mapping[str, Any], root: ET.Element) -> dict[str, Any]:
    view = "architecture-p2-hall-edge"
    wall_path = P2 + ["hall_edge_partition"]
    balcony_path = P2 + ["family_balcony"]
    _mapping(snapshot, wall_path)
    _mapping(snapshot, balcony_path)
    wall_from = _value(snapshot, wall_path + ["from_y"])
    wall_to = _value(snapshot, wall_path + ["to_y"])
    open_from = _value(snapshot, balcony_path + ["from_y"])
    open_to = _value(snapshot, balcony_path + ["to_y"])
    axis_x = _value(snapshot, wall_path + ["axis_x"])
    if not wall_from < open_from < open_to < wall_to:
        raise CoordinationError("Invalid P2 W04R/open-balcony source extents")
    if not math.isclose(axis_x, _value(snapshot, balcony_path + ["axis_x"]), abs_tol=1e-9):
        raise CoordinationError("P2 W04R and family-balcony axes disagree")
    run_x, run_y, run_width, run_height = 110.0, 255.0, 720.0, 255.0
    scale = run_width / 18.0
    ranges = [
        ("retained-suite-south", wall_from, open_from, "p2-w04r-suite-edge"),
        ("open-family-frontage", open_from, open_to, "open-family-balcony"),
        ("retained-suite-north", open_to, wall_to, "p2-w04r-suite-edge"),
    ]
    features = []
    for name, start, end, class_name in ranges:
        expected_x = run_x + start * scale
        expected_width = (end - start) * scale
        matches = []
        for element in _elements(root, "rect", class_name=class_name):
            if math.isclose(_number(element, "y", name), run_y, rel_tol=0.0, abs_tol=1e-6) and math.isclose(
                _number(element, "height", name), run_height, rel_tol=0.0, abs_tol=1e-6
            ) and math.isclose(_number(element, "x", name), expected_x, rel_tol=0.0, abs_tol=1e-6) and math.isclose(
                _number(element, "width", name), expected_width, rel_tol=0.0, abs_tol=1e-6
            ):
                matches.append(element)
        if len(matches) != 1:
            raise CoordinationError(f"P2 hall-edge source projection is missing or ambiguous: {view}/{name}")
        _check_untransformed(root, matches[0], view + "/" + name)
        start_path = balcony_path + ["from_y"] if name == "open-family-frontage" else wall_path + ["from_y"] if name == "retained-suite-south" else balcony_path + ["to_y"]
        end_path = balcony_path + ["to_y"] if name == "open-family-frontage" else balcony_path + ["from_y"] if name == "retained-suite-south" else wall_path + ["to_y"]
        features.append(
            {
                "feature_id": name,
                "source_paths": [_path(start_path), _path(end_path)],
                "source_y": [start, end],
                "svg_class": class_name,
                "svg_rect": {
                    "x": expected_x,
                    "y": run_y,
                    "width": expected_width,
                    "height": run_height,
                },
            }
        )
    open_left = run_x + open_from * scale
    open_right = run_x + open_to * scale
    guard_matches = [
        element
        for element in _elements(root, "line", class_name="family-balcony-guard")
        if math.isclose(_number(element, "x1", "family-balcony-guard"), open_left, abs_tol=1e-6)
        and math.isclose(_number(element, "x2", "family-balcony-guard"), open_right, abs_tol=1e-6)
        and math.isclose(_number(element, "y1", "family-balcony-guard"), run_y + run_height - 18, abs_tol=1e-6)
        and math.isclose(_number(element, "y2", "family-balcony-guard"), run_y + run_height - 18, abs_tol=1e-6)
    ]
    if len(guard_matches) != 1:
        raise CoordinationError(f"P2 open-family guard edge source projection changed in {view}")
    guard_paths = [balcony_path + ["from_y"], balcony_path + ["to_y"]]
    features.append(
        {
            "feature_id": "open-frontage-guard-line",
            "source_paths": [_path(path) for path in guard_paths],
            "svg_line": [open_left, run_y + run_height - 18, open_right, run_y + run_height - 18],
        }
    )
    overall = [
        element
        for element in _elements(root, "line")
        if math.isclose(_number(element, "x1", view), run_x, abs_tol=1e-6)
        and math.isclose(_number(element, "x2", view), run_x + run_width, abs_tol=1e-6)
        and math.isclose(_number(element, "y1", view), 220.0, abs_tol=1e-6)
        and math.isclose(_number(element, "y2", view), 220.0, abs_tol=1e-6)
    ]
    if len(overall) != 1:
        raise CoordinationError(f"P2 hall-edge overall source dimension line changed in {view}")
    features.append(
        {
            "feature_id": "hall-edge-overall-dimension-line",
            "source_paths": [_path(wall_path + ["from_y"]), _path(wall_path + ["to_y"])],
            "svg_line": [run_x, 220.0, run_x + run_width, 220.0],
        }
    )
    expected_summary = (
        f"{wall_to - wall_from:.2f} m HALL EDGE · {open_to - open_from:.2f} m OPEN / "
        f"{(wall_to - wall_from) - (open_to - open_from):.2f} m ENCLOSED"
    )
    summaries = [element for element in _elements(root, "text") if _visible_text(element) == expected_summary]
    if len(summaries) != 1:
        raise CoordinationError(f"P2 hall-edge source dimension label changed in {view}")
    features.append(
        {
            "feature_id": "hall-edge-source-dimension-summary",
            "source_paths": [
                _path(wall_path + ["from_y"]),
                _path(wall_path + ["to_y"]),
                _path(balcony_path + ["from_y"]),
                _path(balcony_path + ["to_y"]),
            ],
            "visible_text": expected_summary,
        }
    )
    return {
        "state": "evaluated",
        "projection_id": "p2-w04r-family-edge-v1",
        "feature_count": len(features),
        "features": features,
        "source_values": {
            "wall_axis_x_m": axis_x,
            "wall_range_y_m": [wall_from, wall_to],
            "open_frontage_y_m": [open_from, open_to],
            "open_frontage_length_m": float(_fmt(open_to - open_from)),
            "retained_enclosure_length_m": float(_fmt(wall_to - wall_from - (open_to - open_from))),
            "guard_height_m": _value(snapshot, balcony_path + ["guard_height_m"]),
        },
        "scope": (
            f"Source-bound unfolded Y extents ({wall_to - wall_from:g} m wall edge, "
            f"{open_to - open_from:g} m open frontage) and guard-line plan span; vertical bands, "
            "guard height graphic, edge beam, truss and wall assembly remain schematic or unresolved."
        ),
    }


def _audit_exterior(snapshot: Mapping[str, Any], root: ET.Element) -> dict[str, Any]:
    view = "architecture-p2-exterior-wall"
    contract = _layer_profile(
        snapshot,
        root,
        assembly_key="exterior_wall_assembly",
        layers_key="outside_to_inside_layers",
        top=290.0,
        height=300.0,
        scale_px_per_mm=2.8,
        origin_x=115.0,
        view=view,
        svg_class="exterior-wall-layer",
    )
    assembly_path = P2 + ["exterior_wall_assembly"]
    nominal_path = assembly_path + ["nominal_total_m"]
    schedule_path = P2 + ["wall_schedule", "P2-W05", "nominal_total_m"]
    nominal_mm = _value(snapshot, nominal_path) * 1000.0
    schedule_mm = _value(snapshot, schedule_path) * 1000.0
    layer_sum_mm = sum(feature["nominal_mm"] for feature in contract["features"])
    stale_note = str(_mapping(snapshot, assembly_path).get("layer_sum_note", ""))
    stale_match = re.search(r"(\d+(?:\.\d+)?)\s*mm", stale_note)
    stale_note_mm = float(stale_match.group(1)) if stale_match is not None else None
    expected_label = f"{_fmt(nominal_mm)} mm NOMINAL · {_fmt(layer_sum_mm)} mm ILLUSTRATIVE SUM"
    labels = [element for element in _elements(root, "text") if _visible_text(element) == expected_label]
    if len(labels) != 1:
        raise CoordinationError(f"P2-W05 source layer label changed in {view}")
    bracket = [
        element
        for element in _elements(root, "line")
        if math.isclose(_number(element, "x1", view), 115.0, abs_tol=1e-6)
        and math.isclose(_number(element, "x2", view), contract["end_x"], abs_tol=1e-6)
        and math.isclose(_number(element, "y1", view), 246.0, abs_tol=1e-6)
        and math.isclose(_number(element, "y2", view), 246.0, abs_tol=1e-6)
    ]
    if len(bracket) != 1:
        raise CoordinationError(f"P2-W05 illustrative layer-sum line changed in {view}")
    source_paths = [
        *contract["paths"],
        nominal_path,
        schedule_path,
        assembly_path + ["layer_sum_note"],
    ]
    legend_features = []
    layers = contract["layers"]
    for index, layer in enumerate(layers):
        label_text = _legend_text(layer)
        text_position = [137.0, 650.0 + index * 48.0]
        matching_labels = [
            element
            for element in _elements(root, "text")
            if _visible_text(element) == label_text
            and math.isclose(_number(element, "x", view), text_position[0], abs_tol=1e-6)
            and math.isclose(_number(element, "y", view), text_position[1], abs_tol=1e-6)
        ]
        if len(matching_labels) != 1:
            raise CoordinationError(f"P2-W05 source layer legend changed in {view}/layer-{index + 1}")
        source_paths_for_label = [contract["paths"][index]]
        if "infill_nominal_mm" in layer:
            source_paths_for_label.append(
                P2 + ["exterior_wall_assembly", "outside_to_inside_layers", index, "infill_nominal_mm"]
            )
        legend_features.append(
            {
                "feature_id": f"exterior-wall-assembly-layer-{index + 1:02d}-legend",
                "source_paths": source_paths_for_label,
                "visible_text": label_text,
                "svg_text_position": text_position,
            }
        )
    return {
        "state": "evaluated",
        "projection_id": "p2-w05-schematic-layer-profile-v1",
        "feature_count": len(contract["features"]) + 2 + len(legend_features),
        "features": contract["features"]
        + [
            {
                "feature_id": "exterior_wall_assembly-layer-sum",
                "source_paths": [_path(path) for path in contract["paths"]],
                "svg_line": [115.0, 246.0, contract["end_x"], 246.0],
            },
            {
                "feature_id": "exterior_wall_assembly-layer-sum-label",
                "source_paths": [_path(path) for path in source_paths],
                "visible_text": expected_label,
            },
        ]
        + legend_features,
        "source_values": {
            "nominal_thickness_mm": nominal_mm,
            "wall_schedule_nominal_mm": schedule_mm,
            "nominal_values_match": math.isclose(
                nominal_mm, schedule_mm, rel_tol=0.0, abs_tol=1e-6
            ),
            "illustrative_layer_sum_mm": layer_sum_mm,
            "inherited_layer_note_mm": stale_note_mm,
            "inherited_layer_note": stale_note,
            "open_conflict": "CF-014",
        },
        "scope": (
            f"Source-bound schematic layer widths only: {nominal_mm:g} mm assembly nominal, "
            f"{schedule_mm:g} mm wall-schedule nominal, {layer_sum_mm:g} mm illustrative sum, "
            f"and inherited note {stale_note!r} remain unreconciled under CF-014. "
            "No product, wall solid or performance is selected."
        ),
    }


_AUDITORS = {
    "architecture-p2-acoustic-partition": _audit_acoustic,
    "architecture-p2-hall-edge": _audit_hall_edge,
    "architecture-p2-exterior-wall": _audit_exterior,
}


def audit_p2_context_geometry(snapshot: dict, root: ET.Element) -> dict | None:
    """Audit visible P2 detail features against named snapshot context sources."""
    view = root.get("data-view-id")
    auditor = _AUDITORS.get(str(view))
    if auditor is None:
        return None
    return auditor(snapshot, root)


def _append_hall_opening_dimension(snapshot: Mapping[str, Any], root: ET.Element) -> None:
    from_path = P2 + ["family_balcony", "from_y"]
    to_path = P2 + ["family_balcony", "to_y"]
    start = _value(snapshot, from_path)
    end = _value(snapshot, to_path)
    scale, origin = 40.0, 110.0
    x1, x2 = origin + scale * start, origin + scale * end
    y_dim, y_label = 239.0, 236.0
    group = ET.SubElement(root, _q("g"), {"id": "p2-hall-edge-open-frontage-dimension"})
    ET.SubElement(
        group,
        _q("line"),
        {"x1": str(x1), "y1": str(y_dim), "x2": str(x2), "y2": str(y_dim), "stroke": "#126c83", "stroke-width": "1.1"},
    )
    for x in (x1, x2):
        ET.SubElement(
            group,
            _q("line"),
            {"x1": str(x), "y1": str(y_dim - 3.5), "x2": str(x), "y2": str(y_dim + 3.5), "stroke": "#126c83", "stroke-width": "1.1"},
        )
        ET.SubElement(
            group,
            _q("line"),
            {"x1": str(x), "y1": str(y_dim), "x2": str(x), "y2": "255", "stroke": "#6e8d94", "stroke-width": ".7"},
        )
    references = []
    targets = []
    for suffix, value, source_path, x in (("start", start, from_path, x1), ("end", end, to_path, x2)):
        reference = f"P2-W04R.open-frontage.{suffix}"
        target = f"p2-hall-edge-open-frontage-{suffix}-anchor"
        references.append(reference)
        targets.append(target)
        ET.SubElement(
            group,
            _q("circle"),
            {
                "id": target,
                "cx": str(x),
                "cy": str(y_dim),
                "r": "2.2",
                "fill": "#fffdf8",
                "stroke": "#126c83",
                "stroke-width": "1.0",
                "data-anchor-id": reference,
                "data-anchor-context-id": "PROJECT.P2",
                "data-anchor-status": "resolved",
                "data-anchor-source": "P2 family-balcony source interval",
                "data-anchor-bindings": json.dumps({"y": source_path}, separators=(",", ":")),
                "data-world-y": f"{value:g}",
            },
        )
    text = ET.SubElement(
        group,
        _q("text"),
        {
            "id": "p2-hall-edge-open-frontage-dimension-label",
            "x": str((x1 + x2) / 2),
            "y": str(y_label),
            "text-anchor": "middle",
            "font-family": "IBM Plex Sans",
            "font-size": "8.5",
            "font-weight": "700",
            "fill": "#124c5c",
            "stroke": "#fffdf8",
            "stroke-width": "2.4",
            "paint-order": "stroke",
            "data-dimension-id": "P2-W04R.open-frontage",
            "data-anchor-refs": " ".join(references),
            "data-anchor-targets": " ".join(targets),
            "data-dimension-status": "resolved",
            "data-dimension-datum": "P2 project Y coordinates",
            "data-dimension-direction": "parallel",
            "data-dimension-value": f"{end - start:g}",
            "data-dimension-unit": "m",
            "data-dimension-source": f"{_path(from_path)} → {_path(to_path)}",
            "data-dimension-label-format": "fixed-2-m",
        },
    )
    text.text = f"{end - start:.2f} m"


def annotate_p2_context_view(snapshot: dict, root: ET.Element) -> dict | None:
    """Declare and tag source-context features; never add or resize wall geometry."""
    prepared = prepare_p2_context_view(snapshot, root)
    if prepared is None:
        return None
    audit = audit_p2_context_geometry(snapshot, root)
    if audit is None:
        return None
    view = str(root.get("data-view-id"))
    root.set("data-view-purpose", "source-bound schematic P2 wall-detail review")
    root.set("data-projection-basis", audit["scope"])
    root.set("data-projected-axes", "y" if view == "architecture-p2-hall-edge" else "x")
    root.attrib.pop("data-world-to-view", None)
    _tag_context_features(root, view, audit)
    if view == "architecture-p2-hall-edge":
        existing = next(
            (
                element
                for element in root.iter()
                if element.get("data-dimension-id") == "P2-W04R.open-frontage"
            ),
            None,
        )
        if existing is None:
            _append_hall_opening_dimension(snapshot, root)
        return {
            "status": "supported",
            "reason": None,
            "geometry_binding": audit,
            "anchors": 2,
            "dimensions": 1,
            "supported_scope": audit["scope"],
        }
    dimension = next(
        (
            element
            for element in root.iter(_q("text"))
            if element.get("data-p2-context-dimension-id")
        ),
        None,
    )
    if dimension is not None:
        dimension.set(
            "data-p2-context-dimension-id",
            "P2-W01B.illustrative-layer-sum"
            if view == "architecture-p2-acoustic-partition"
            else "P2-W05.illustrative-layer-sum",
        )
    return {
        "status": "supported",
        "reason": None,
        "geometry_binding": audit,
        "anchors": 0,
        "dimensions": 0,
        "context_dimensions": 1,
        "supported_scope": audit["scope"],
    }

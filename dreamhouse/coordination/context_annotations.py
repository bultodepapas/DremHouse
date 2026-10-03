"""Audit known section datums without inventing roof solids or physical wall entities."""

from __future__ import annotations

import json
import math
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import CoordinationError

VIEWS = {"architecture-roof-longitudinal-section", "architecture-roof-transverse-section"}
NS = "http://www.w3.org/2000/svg"
LEVEL = ["discipline_inputs", "structure", "stair", "levels"]
ROOF = ["discipline_inputs", "equipment", "pb", "roof"]


def _value(snapshot, path):
    value = snapshot
    try:
        for part in path:
            value = value[part]
    except (KeyError, TypeError, IndexError) as exc:
        raise CoordinationError(f"Missing section context source: {path}") from exc
    if type(value) not in {float, int} or not math.isfinite(value):
        raise CoordinationError(f"Invalid numeric section context: {path}")
    return value


def _contract(snapshot, view_id):
    pb = _value(snapshot, LEVEL + ["pb_finished_floor"])
    if pb != 0:
        raise CoordinationError("Native roof datum projection requires the declared PB zero origin")
    p2 = _value(snapshot, LEVEL + ["p2_finished_floor"])
    low = _value(snapshot, ROOF + ["low_eave"])
    high = _value(snapshot, ROOF + ["high_eave"])
    if low > high:
        raise CoordinationError("Reversed roof eave sources")
    if view_id.endswith("longitudinal-section"):
        length = _value(snapshot, ["geometry", "hall", "length_m"])
        start = _value(snapshot, ["geometry", "p2", "x_m"])
        end = start + _value(snapshot, ["geometry", "p2", "length_m"])
        roof = (low + high) / 2
        if length <= 0 or not 0 <= start < end <= length:
            raise CoordinationError("Invalid section plan extents")
        return {
            "axes": ["x", "z"],
            "scale": 22.0,
            "offset": [110.0, 360.0],
            "lines": {
                "ground-datum": [0, pb, length, pb],
                "roof-ordinate": [0, roof, length, roof],
                "p2-datum": [start, p2, end, p2],
            },
            "dimensions": [
                (
                    "hall-span",
                    "x",
                    0,
                    length,
                    {"datum": "project-origin"},
                    ["geometry", "hall", "length_m"],
                    [110, 392],
                    [110 + 22 * length, 392],
                ),
                (
                    "p2-span",
                    "x",
                    start,
                    end,
                    ["geometry", "p2", "x_m"],
                    {"sum": [["geometry", "p2", "x_m"], ["geometry", "p2", "length_m"]]},
                    [110 + 22 * start, 360 - 22 * p2 + 24],
                    [110 + 22 * end, 360 - 22 * p2 + 24],
                ),
                (
                    "p2-level",
                    "z",
                    pb,
                    p2,
                    LEVEL + ["pb_finished_floor"],
                    LEVEL + ["p2_finished_floor"],
                    [950, 360],
                    [950, 360 - 22 * p2],
                ),
                (
                    "roof-ordinate",
                    "z",
                    pb,
                    roof,
                    LEVEL + ["pb_finished_floor"],
                    {"mean": [ROOF + ["low_eave"], ROOF + ["high_eave"]]},
                    [1000, 360],
                    [1000, 360 - 22 * roof],
                ),
            ],
        }
    width = _value(snapshot, ["geometry", "hall", "width_m"])
    side = snapshot["discipline_inputs"]["equipment"]["pb"]["roof"]["low_side"]
    if side not in {"A", "B"} or width <= 0:
        raise CoordinationError("Unknown roof side or invalid width")
    a, b = (low, high) if side == "A" else (high, low)
    return {
        "axes": ["y", "z"],
        "scale": 42.0,
        "offset": [170.0, 575.0],
        "lines": {
            "ground-datum": [0, pb, width, pb],
            "roof-ordinate": [0, a, width, b],
            "p2-datum": [0, p2, width, p2],
        },
        "dimensions": [
            (
                "hall-span",
                "y",
                0,
                width,
                {"datum": "project-origin"},
                ["geometry", "hall", "width_m"],
                [170, 633],
                [170 + 42 * width, 633],
            ),
            (
                "side-a-eave",
                "z",
                pb,
                a,
                LEVEL + ["pb_finished_floor"],
                ROOF + ["low_eave" if side == "A" else "high_eave"],
                [130, 575],
                [130, 575 - 42 * a],
            ),
            (
                "side-b-eave",
                "z",
                pb,
                b,
                LEVEL + ["pb_finished_floor"],
                ROOF + ["high_eave" if side == "A" else "low_eave"],
                [970, 575],
                [970, 575 - 42 * b],
            ),
            (
                "p2-level",
                "z",
                pb,
                p2,
                LEVEL + ["pb_finished_floor"],
                LEVEL + ["p2_finished_floor"],
                [1015, 575],
                [1015, 575 - 42 * p2],
            ),
        ],
    }


def audit_context_geometry(snapshot: dict, root: ET.Element) -> dict | None:
    view = root.get("data-view-id")
    if view not in VIEWS:
        return None
    contract = _contract(snapshot, view)
    features = {}
    parents = {child: parent for parent in root.iter() for child in parent}
    for node in root.iter():
        name = node.get("data-context-feature")
        if name is None:
            continue
        if (
            name in features
            or name not in contract["lines"]
            or node.tag.rsplit("}", 1)[-1] != "line"
        ):
            raise CoordinationError(f"Invalid section context feature: {name}")
        ancestor = node
        while ancestor is not None:
            if ancestor.get("transform") or "transform" in ancestor.get("style", "").lower():
                raise CoordinationError("Transformed section context geometry is unsupported")
            ancestor = parents.get(ancestor)
        expected = []
        s = contract["scale"]
        ox, oy = contract["offset"]
        line = contract["lines"][name]
        for index in (0, 2):
            expected.extend([ox + s * line[index], oy - s * line[index + 1]])
        for key, value in zip(("x1", "y1", "x2", "y2"), expected, strict=True):
            try:
                observed = float(node.get(key, ""))
            except (ValueError, TypeError) as exc:
                raise CoordinationError("Invalid section line coordinate") from exc
            if not math.isfinite(observed) or not math.isclose(
                observed, value, rel_tol=0, abs_tol=1e-6
            ):
                raise CoordinationError(f"Section context projection mismatch: {view}/{name}/{key}")
        features[name] = {"svg_line": expected, "world_line": line}
    if set(features) != set(contract["lines"]):
        raise CoordinationError("Missing section context features")
    return {
        "state": "evaluated",
        "projection_id": view + "-context-v1",
        "feature_count": len(features),
        "features": features,
        "scope": "Source roof ordinates and floor datums only; roof/floor solids and clear heights are not represented.",
    }


def annotate_context_view(snapshot: dict, root: ET.Element) -> dict | None:
    audit = audit_context_geometry(snapshot, root)
    if audit is None:
        return None
    view = root.get("data-view-id")
    contract = _contract(snapshot, view)
    root.set("data-view-purpose", "source roof/floor datum coordination")
    root.set("data-projection-basis", audit["scope"])
    root.set("data-projected-axes", " ".join(contract["axes"]))
    root.set(
        "data-world-to-view",
        json.dumps(
            {
                "axes": contract["axes"],
                "scale": [contract["scale"], -contract["scale"]],
                "offset": contract["offset"],
            }
        ),
    )
    group = ET.SubElement(
        root, f"{{{NS}}}g", {"id": view + "-context-dimensions", "font-family": "IBM Plex Sans"}
    )
    for name, axis, a, b, source_a, source_b, point_a, point_b in contract["dimensions"]:
        refs = []
        targets = []
        for suffix, value, source, point in [
            ("start", a, source_a, point_a),
            ("end", b, source_b, point_b),
        ]:
            ref = f"{view}.{name}.{suffix}"
            target = ref + "-anchor"
            refs.append(ref)
            targets.append(target)
            ET.SubElement(
                group,
                f"{{{NS}}}circle",
                {
                    "id": target,
                    "cx": str(point[0]),
                    "cy": str(point[1]),
                    "r": "2",
                    "fill": "#176172",
                    "data-anchor-id": ref,
                    "data-anchor-context-id": "PROJECT.PB",
                    "data-anchor-status": "resolved",
                    f"data-world-{axis}": str(value),
                    "data-anchor-bindings": json.dumps({axis: source}),
                },
            )
        ET.SubElement(
            group,
            f"{{{NS}}}line",
            {
                "x1": str(point_a[0]),
                "y1": str(point_a[1]),
                "x2": str(point_b[0]),
                "y2": str(point_b[1]),
                "stroke": "#176172",
            },
        )
        text = ET.SubElement(
            group,
            f"{{{NS}}}text",
            {
                "x": str((point_a[0] + point_b[0]) / 2 + (-8 if axis == "z" else 0)),
                "y": str((point_a[1] + point_b[1]) / 2 - 6),
                "text-anchor": "end" if axis == "z" else "middle",
                "font-size": "11",
                "fill": "#176172",
                "stroke": "#fbfaf7",
                "stroke-width": "3",
                "paint-order": "stroke",
                "data-dimension-id": view + "." + name,
                "data-dimension-value": str(abs(b - a)),
                "data-dimension-unit": "m",
                "data-dimension-status": "resolved",
                "data-dimension-label-format": "fixed-2-m",
                "data-anchor-refs": " ".join(refs),
                "data-anchor-targets": " ".join(targets),
            },
        )
        text.text = f"{abs(b - a):.2f} m"
    return {
        "status": "supported",
        "reason": None,
        "scope": audit["scope"],
        "geometry_binding": audit,
        "anchors": 8,
        "dimensions": 4,
    }

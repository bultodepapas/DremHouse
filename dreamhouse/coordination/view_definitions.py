"""Presentation intent and source-extent membership, independent of physical quantities."""

from __future__ import annotations

import json
import math
from copy import deepcopy
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import CoordinationError


def _finite(value: object) -> bool:
    try:
        return type(value) in {int, float} and math.isfinite(value)
    except OverflowError:
        return False


def validate_view_settings(value: object) -> dict:
    """Accept explicit project-elevation cuts for the two review plans only."""
    if not isinstance(value, dict) or set(value) - {"plan-pb", "plan-p2"}:
        raise CoordinationError("view_settings must name supported plan-pb/plan-p2 views")
    for view, settings in value.items():
        if not isinstance(settings, dict) or set(settings) - {"cut_plane_m", "depth_range_m"}:
            raise CoordinationError(f"Invalid presentation fields for {view}")
        if "cut_plane_m" not in settings:
            raise CoordinationError(f"{view} requires an explicit cut_plane_m")
        values = [settings["cut_plane_m"]]
        depth = settings.get("depth_range_m")
        if depth is not None:
            if not isinstance(depth, list) or len(depth) != 2:
                raise CoordinationError("depth_range_m must contain two project elevations")
            values.extend(depth)
        if any(not _finite(n) for n in values):
            raise CoordinationError("View elevations must be finite numeric metres")
        if depth is not None and not depth[0] <= settings["cut_plane_m"] <= depth[1]:
            raise CoordinationError("View depth must be ordered and contain the cut plane")
    return deepcopy(value)


def classify_membership(geometry: dict, settings: dict) -> str:
    """Classify envelopes only; missing solids cannot become a physical section claim."""
    z0, z1 = geometry.get("z0"), geometry.get("z1")
    if any(not _finite(n) for n in (z0, z1)):
        return "unknown-height"
    if z0 > z1:
        raise CoordinationError("Reversed vertical extent in view membership")
    cut = settings.get("cut_plane_m")
    if cut is None:
        return "projected-envelope"
    depth = settings.get("depth_range_m")
    if depth is not None and (z1 < depth[0] or z0 > depth[1]):
        return "outside-depth"
    if z0 == z1 == cut:
        return "on-plane-envelope"
    if z0 <= cut <= z1:
        return "cut-envelope"
    return "projected-above" if z0 > cut else "projected-below"


def apply_plan_intent(root: ET.Element, snapshot: dict) -> None:
    """Decorate actual existing occurrences without changing or inferring geometry."""
    view_id = root.get("data-view-id", "")
    settings = snapshot.get("view_settings", {}).get(view_id, {})
    root.set("data-view-purpose", "schematic coordination plan")
    root.set("data-projection-basis", "orthographic XY projection of source envelopes")
    root.set("data-projected-axes", "x y")
    if settings:
        root.set("data-cut-plane-axis", "Z")
        root.set("data-cut-plane-value-m", repr(settings["cut_plane_m"]))
        if settings.get("depth_range_m") is not None:
            root.set("data-depth-range-m", json.dumps(settings["depth_range_m"]))
    for node in root.iter():
        identifier = node.get("data-entity-id")
        if identifier not in snapshot.get("entities", {}):
            continue
        membership = classify_membership(snapshot["entities"][identifier]["geometry"], settings)
        node.set("data-section-membership", membership)
        node.set("data-representation-role", membership)
        title = next((e for e in node if e.tag.endswith("}title")), None)
        if title is not None:
            title.text = (
                title.text or ""
            ) + f" · View membership: {membership}; source envelope only."
        if membership in {"projected-above", "outside-depth"}:
            node.set("opacity", "0.35" if membership == "outside-depth" else "0.65")
            node.set("stroke-dasharray", "5 4")


def inspect_definition(root: ET.Element) -> dict:
    """Persist actual declared view settings, including unsupported/unknown context."""
    cut = root.get("data-cut-plane-value-m")
    depth = root.get("data-depth-range-m")
    transform = root.get("data-world-to-view")
    try:
        cut_value = None if cut is None else float(cut)
        depth_value = None if depth is None else json.loads(depth)
        matrix = None if transform is None else json.loads(transform)
    except (ValueError, TypeError, OverflowError) as exc:
        raise CoordinationError("Invalid view definition numeric declaration") from exc
    if cut_value is not None and (
        not _finite(cut_value) or root.get("data-cut-plane-axis", "").lower() not in {"x", "y", "z"}
    ):
        raise CoordinationError("Invalid declared cut plane")
    if depth_value is not None and (
        not isinstance(depth_value, list)
        or len(depth_value) != 2
        or any(not _finite(v) for v in depth_value)
        or depth_value[0] > depth_value[1]
        or cut_value is None
        or not depth_value[0] <= cut_value <= depth_value[1]
    ):
        raise CoordinationError("Invalid declared depth range")
    if matrix is not None:
        if not isinstance(matrix, dict) or set(matrix) != {"axes", "scale", "offset"}:
            raise CoordinationError("Invalid declared projection transform")
        if any(
            not isinstance(matrix.get(k), list) or len(matrix[k]) != 2
            for k in ("axes", "scale", "offset")
        ) or any(not _finite(v) for k in ("scale", "offset") for v in matrix[k]):
            raise CoordinationError("Invalid projection transform coordinates")
        if (
            any(not isinstance(axis, str) for axis in matrix["axes"])
            or len(set(matrix["axes"])) != 2
            or not set(matrix["axes"]) <= {"x", "y", "z"}
            or any(v == 0 for v in matrix["scale"])
        ):
            raise CoordinationError("Invalid projection axes or scale")
    return {
        "view_id": root.get("data-view-id"),
        "purpose": root.get("data-view-purpose", "schematic coordination review"),
        "projection_basis": root.get(
            "data-projection-basis", "native sheet; metric coverage separately audited"
        ),
        "sheet_view_box": root.get("viewBox"),
        "projected_axes": root.get("data-projected-axes", "").split(),
        "cut_plane": None
        if cut is None
        else {
            "axis": root.get("data-cut-plane-axis"),
            "value_m": cut_value,
            "datum": "project elevation/coordinates",
        },
        "depth_range_m": depth_value,
        "world_to_view": matrix,
        "scale_authority": "SVG display units per metre where a transform is declared; no printed-sheet scale certification",
        "unknowns": [
            key
            for key, value in [
                ("cut_plane", cut),
                ("depth_range", depth),
                ("single_metric_transform", transform),
            ]
            if value is None
        ],
    }

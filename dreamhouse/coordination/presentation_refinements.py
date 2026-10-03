"""Small presentation-only corrections for inherited native SVG sheets.

These refinements clarify source meaning without editing geometry, model entities,
semantic anchors, or historical drawing generators.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import CoordinationError

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def _q(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"


def _text(node: ET.Element) -> str:
    return "".join(node.itertext()).strip()


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CoordinationError(f"Presentation refinement source {label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise CoordinationError(f"Presentation refinement source {label} must be finite")
    return result


def _svg_number(value: str | None, label: str) -> float:
    try:
        result = float(value)  # SVG numeric attributes are serialized as strings.
    except (TypeError, ValueError, OverflowError) as error:
        raise CoordinationError(
            f"Invalid SVG coordinate for presentation refinement {label}"
        ) from error
    if not math.isfinite(result):
        raise CoordinationError(f"Non-finite SVG coordinate for presentation refinement {label}")
    return result


def _unique(nodes: list[ET.Element], label: str) -> ET.Element:
    if len(nodes) != 1:
        raise CoordinationError(
            f"Expected one {label} for native presentation refinement, found {len(nodes)}"
        )
    return nodes[0]


def _set_multiline(
    node: ET.Element,
    *,
    x: float,
    y: float,
    lines: tuple[str, ...],
    font_size: float,
    line_step: float,
    anchor: str = "middle",
    fill: str = "#172a33",
    weight: str = "700",
    refinement_id: str,
    source_path: str,
) -> None:
    """Reflow one existing text label in place, retaining the original text node."""
    if any(child.tag != _q("tspan") for child in node):
        raise CoordinationError(f"Cannot reflow non-tspan native label for {refinement_id}")
    node.text = None
    node.attrib.update(
        {
            "x": f"{x:.3f}".rstrip("0").rstrip("."),
            "y": f"{y:.3f}".rstrip("0").rstrip("."),
            "font-size": f"{font_size:g}",
            "text-anchor": anchor,
            "font-weight": weight,
            "fill": fill,
            "data-presentation-refinement": refinement_id,
            "data-refinement-source": source_path,
        }
    )
    for child in list(node):
        node.remove(child)
    for index, value in enumerate(lines):
        span = ET.SubElement(
            node,
            _q("tspan"),
            {
                "x": f"{x:.3f}".rstrip("0").rstrip("."),
                "dy": "0" if index == 0 else f"{line_step:g}",
                "font-family": "IBM Plex Sans",
            },
        )
        span.text = value


def _set_note(
    root: ET.Element,
    *,
    x: float,
    y: float,
    lines: tuple[str, ...],
    font_size: float,
    line_step: float,
    refinement_id: str,
    fill: str = "#8e3825",
    weight: str = "700",
) -> None:
    group = ET.SubElement(
        root,
        _q("g"),
        {
            "class": "presentation-note",
            "data-presentation-refinement": refinement_id,
            "aria-label": "Coordination note; no geometry implied",
        },
    )
    node = ET.SubElement(
        group,
        _q("text"),
        {
            "x": f"{x:g}",
            "y": f"{y:g}",
            "font-size": f"{font_size:g}",
            "font-family": "IBM Plex Sans",
            "font-weight": weight,
            "fill": fill,
            "data-presentation-refinement": refinement_id,
        },
    )
    for index, value in enumerate(lines):
        span = ET.SubElement(
            node,
            _q("tspan"),
            {"x": f"{x:g}", "dy": "0" if index == 0 else f"{line_step:g}"},
        )
        span.text = value


def _primary_bathroom(snapshot: Mapping[str, Any], root: ET.Element) -> None:
    try:
        source = snapshot["discipline_inputs"]["programme"]["p2"]["primary_bathroom_unified"]
    except (KeyError, TypeError) as error:
        raise CoordinationError("Missing unified primary-bathroom presentation source") from error

    label = _unique(
        [node for node in root.iter(_q("text")) if _text(node).startswith("Primary bathroom")],
        "native primary-bathroom label",
    )
    right_compartment = _unique(
        [node for node in root.iter(_q("rect")) if node.get("data-space-id") == "M-B"],
        "primary bathroom WC compartment",
    )
    linen = _unique(
        [
            node
            for node in root.iter(_q("rect"))
            if "primary-linen" in node.get("class", "").split()
        ],
        "primary bathroom linen fixture",
    )
    wc = _unique(
        [node for node in root.iter(_q("rect")) if "primary-wc" in node.get("class", "").split()],
        "primary bathroom WC fixture",
    )

    room_x = _svg_number(right_compartment.get("x"), "M-B.x")
    room_width = _svg_number(right_compartment.get("width"), "M-B.width")
    linen_bottom = _svg_number(linen.get("y"), "primary-linen.y") + _svg_number(
        linen.get("height"), "primary-linen.height"
    )
    wc_top = _svg_number(wc.get("y"), "primary-wc.y")
    if room_width <= 0 or wc_top - linen_bottom < 28:
        raise CoordinationError("No clear room for primary-bathroom labels in native SVG")

    try:
        gross = _number(source["gross_area_m2"], "primary_bathroom_unified.gross_area_m2")
        net = _number(
            source["schematic_net_area_m2"],
            "primary_bathroom_unified.schematic_net_area_m2",
        )
    except (KeyError, TypeError) as error:
        raise CoordinationError("Incomplete primary-bathroom area source") from error

    start_y = linen_bottom + 10
    _set_multiline(
        label,
        x=room_x + room_width / 2,
        y=start_y,
        lines=("BATH",),
        font_size=9.0,
        line_step=11.0,
        refinement_id="VR-01-primary-bathroom-label",
        source_path="discipline_inputs.programme.p2.primary_bathroom_unified",
    )
    area_label = f"PRIMARY BATHROOM · {net:.2f} m² NET (SCHEMATIC) · {gross:.2f} m² GROSS (UNIFIED)"
    _set_note(
        root,
        x=803,
        y=353,
        lines=(area_label,),
        font_size=10.0,
        line_step=12.0,
        refinement_id="VR-01-primary-bathroom-areas",
        fill="#31474f",
        weight="600",
    )


def _central_island_source(snapshot: Mapping[str, Any]) -> dict[str, float]:
    try:
        source = snapshot["discipline_inputs"]["equipment"]["pb"]["central_rc_bench"]
        return {
            "length": _number(source["length"], "central_rc_bench.length"),
            "depth": _number(source["depth"], "central_rc_bench.depth"),
            "height": _number(source["height"], "central_rc_bench.height"),
            "modules": _number(source["module_count"], "central_rc_bench.module_count"),
            "module_width": _number(source["module_width"], "central_rc_bench.module_width"),
        }
    except (KeyError, TypeError) as error:
        raise CoordinationError("Missing source dimensions for the central RC island") from error


def _central_island(snapshot: Mapping[str, Any], root: ET.Element, view_id: str) -> None:
    source = _central_island_source(snapshot)
    dimensions = f"{source['length']:.2f} × {source['depth']:.2f} m"
    modules = f"{source['modules']:.0f} × {source['module_width']:.2f} m modules"
    if view_id == "architecture-ground-floor":
        label = _unique(
            [
                node
                for node in root.iter(_q("text"))
                if _text(node).startswith("CENTRAL RC ASSEMBLY ISLAND")
            ],
            "ground-floor central RC island label",
        )
        # Place the source-derived dimensions in the clear strip beside the island,
        # below the separate LiPo study envelope. This keeps module seams legible.
        _set_multiline(
            label,
            x=412,
            y=277,
            lines=(
                f"CENTRAL RC ISLAND · {dimensions}",
                f"{modules} · top +{source['height']:.2f} m",
            ),
            font_size=8.5,
            line_step=11.0,
            anchor="start",
            refinement_id="VR-02-pb-rc-island-label",
            source_path="discipline_inputs.equipment.pb.central_rc_bench",
        )
        return

    label = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if "TWO-SIDED" in _text(node) and "TOP" in _text(node)
        ],
        "technical-detail central RC island label",
    )
    # The old single line crossed the centre seam. Reflow the source dimensions
    # inside the middle module, above that seam, without changing its boundaries.
    _set_multiline(
        label,
        x=282,
        y=750,
        lines=(
            dimensions,
            modules,
            f"two-sided top +{source['height']:.2f} m",
        ),
        font_size=8.0,
        line_step=10.0,
        refinement_id="VR-02-detail-rc-island-label",
        source_path="discipline_inputs.equipment.pb.central_rc_bench",
    )


def _downpipe_reference(root: ET.Element) -> None:
    window = _unique(
        [node for node in root.iter(_q("rect")) if node.get("data-entity-id") == "W-G"],
        "guest-bedroom window W-G",
    )
    left = _svg_number(window.get("x"), "W-G.x")
    right = left + _svg_number(window.get("width"), "W-G.width")
    top = _svg_number(window.get("y"), "W-G.y")
    bottom = top + _svg_number(window.get("height"), "W-G.height")
    lines = []
    for node in root.iter(_q("line")):
        x1 = _svg_number(node.get("x1"), "side-B vertical reference.x1")
        x2 = _svg_number(node.get("x2"), "side-B vertical reference.x2")
        y1 = _svg_number(node.get("y1"), "side-B vertical reference.y1")
        y2 = _svg_number(node.get("y2"), "side-B vertical reference.y2")
        stroke_width = node.get("stroke-width")
        if (
            node.get("stroke") == "#536166"
            and stroke_width == "3"
            and math.isclose(x1, x2, abs_tol=0.01)
            and left < x1 < right
            and y1 < bottom
            and y2 > top
        ):
            lines.append(node)
    if not lines:
        return
    reference = _unique(lines, "vertical line crossing guest-bedroom window")
    original = dict(reference.attrib)
    classes = original.get("class", "").split()
    if "presentation-downpipe-reference" not in classes:
        classes.append("presentation-downpipe-reference")
    reference.attrib.update(
        {
            "class": " ".join(classes),
            "stroke": "#b45d35",
            "stroke-width": "2",
            "stroke-dasharray": "5 4",
            "data-presentation-refinement": "VR-03-provisional-downpipe-reference",
        }
    )
    # The existing side elevation generator identifies this family as provisional
    # downpipes and explicitly says its positions are not final. Keep that uncertainty
    # visible beside W-G; the callout denotes a reference, not a collision finding.
    callout_x = min(right + 8, 1160)
    callout_y = max(bottom + 26, 548)
    _set_note(
        root,
        x=callout_x,
        y=callout_y,
        lines=("DOWNPIPE REFERENCE", "POSITION / W-G", "INTERFACE OPEN"),
        font_size=8.0,
        line_step=10.0,
        refinement_id="VR-03-provisional-downpipe-reference",
    )


def _core_access_note(snapshot: Mapping[str, Any], root: ET.Element) -> None:
    if not _has_unlocated_core_access(snapshot):
        return
    _set_note(
        root,
        x=622,
        y=650,
        lines=(
            "CF-013 · Access to core rooms is required; individual door locations remain unresolved.",
            "No door leaf, swing or opening coordinates are implied by this view.",
        ),
        font_size=7.0,
        line_step=12.0,
        refinement_id="VR-04-core-access-unlocated",
    )


def _has_unlocated_core_access(snapshot: Mapping[str, Any]) -> bool:
    entities = snapshot.get("entities", {})
    if not isinstance(entities, Mapping):
        return False
    return any(
        entity_id.startswith("PB-DOOR-")
        and isinstance(entity, Mapping)
        and entity.get("geometry", {}).get("shape") == "unresolved"
        for entity_id, entity in entities.items()
    )


def _great_wall_access_note(snapshot: Mapping[str, Any], root: ET.Element) -> None:
    # Reflow the existing presentation panel. Its height extension is confined to
    # the cream note box; the wall, dimensions, and unresolved door anchors stay put.
    panel = _unique(
        [
            node
            for node in root.iter(_q("rect"))
            if node.get("fill") == "#fff4df" and node.get("stroke") == "#bd5c3c"
        ],
        "Great Wall coordination note panel",
    )
    original_panel = {
        key: _svg_number(panel.get(key), f"Great Wall note panel.{key}")
        for key in ("x", "y", "width", "height")
    }
    if original_panel["height"] < 60:
        raise CoordinationError("Great Wall coordination note panel is too short to reflow")
    panel.set("height", "88")
    panel.set("data-presentation-refinement", "VR-04-great-wall-note-panel")

    header = _unique(
        [node for node in root.iter(_q("text")) if _text(node) in {"DESIGN INTENT", "INTENCIÓN"}],
        "Great Wall design-intent heading",
    )
    header.text = "DESIGN INTENT"
    header.set("y", "798")
    header.set("font-size", "11")
    header.set("data-presentation-refinement", "VR-04-great-wall-note-panel")

    access_intent = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if _text(node).startswith("Continuous architectural finish across the core zones")
        ],
        "Great Wall access-intent note",
    )
    access_intent.set("x", "140")
    access_intent.set("y", "814")
    access_intent.set("font-size", "9")

    specification = _unique(
        [node for node in root.iter(_q("text")) if "1:1" in _text(node)],
        "Great Wall specification note",
    )
    specification.set("x", "140")
    specification.set("y", "829")
    specification.set("font-size", "8.5")
    specification.text = (
        "Finish, fire performance, acoustic absorption, service access, hardware, and stability "
        "require a 1:1 sample and professional specification."
    )

    if _has_unlocated_core_access(snapshot):
        _set_note(
            root,
            x=140,
            y=844,
            lines=(
                "CF-013 · Core-room access is required; door locations, leaves and swings remain unresolved. No door coordinates are shown.",
            ),
            font_size=9.0,
            line_step=11.0,
            refinement_id="VR-04-great-wall-access-unlocated",
            fill="#8e3825",
        )

    height_note = _unique(
        [
            node
            for node in root.iter(_q("text"))
            if node.get("data-context-feature") == "great-wall-height-unresolved"
        ],
        "Great Wall unresolved-height note",
    )
    height_note.set("x", "140")
    height_note.set("y", "860")
    height_note.set("font-size", "9")
    height_note.set("data-presentation-refinement", "VR-04-great-wall-height-unresolved")

    # The revised baselines must fit the adjusted panel with space before the footer.
    panel_bottom = original_panel["y"] + 88
    if _svg_number(height_note.get("y"), "Great Wall height note.y") + 4 > panel_bottom:
        raise CoordinationError("Great Wall unresolved-height note exceeds its note panel")


def refine_native_svg(snapshot: Mapping[str, Any], view_id: str, svg: str) -> str:
    """Apply source-bounded presentation corrections to selected native SVG views."""
    refinements = {
        "architecture-upper-floor": lambda root: _primary_bathroom(snapshot, root),
        "architecture-ground-floor": lambda root: _central_island(snapshot, root, view_id),
        "architecture-pb-technical-workbenches": lambda root: _central_island(
            snapshot, root, view_id
        ),
        "architecture-side-b-elevation": _downpipe_reference,
        "architecture-ground-floor-core": lambda root: _core_access_note(snapshot, root),
        "architecture-great-wall-elevation": lambda root: _great_wall_access_note(snapshot, root),
    }
    refine = refinements.get(view_id)
    if refine is None:
        return svg
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as error:
        raise CoordinationError(f"Invalid SVG for presentation refinement {view_id}") from error
    if root.get("data-view-id") not in (None, view_id):
        raise CoordinationError(
            f"SVG view id {root.get('data-view-id')!r} does not match {view_id!r}"
        )
    refine(root)
    return ET.tostring(root, encoding="unicode")

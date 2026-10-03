"""Role-aware, presentation-only improvements for connected native drawings.

The native generators remain the geometry and annotation authority.  This module
adds reader metadata, makes a small set of explicitly decorative surface patterns
quieter, and replaces the P2 plan's incomplete generic wall key with an exact key
for the wall duties actually represented in that view.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import CoordinationError

SVG_NS = "http://www.w3.org/2000/svg"
VISUAL_LANGUAGE_VERSION = "native-connected-candidate-1"
_NS = f"{{{SVG_NS}}}"

# Only these repeated surface cues are reduced in visual weight.  Pattern tile
# dimensions and child geometry are retained: the output does not suggest a new
# corrugation, board, slat, or panel module.
_DECORATIVE_PATTERN_IDS = {
    "doorpanel": 0.34,
    "metal": 0.36,
    "metals": 0.36,
    "slats": 0.34,
    "slats-struct": 0.34,
    "wood": 0.34,
    "wood2": 0.34,
}

_WALL_LABELS = {
    "P2-W01A": "same-suite dry",
    "P2-W01B": "suite / common separation",
    "P2-W02": "wet / service",
    "P2-W02S": "sauna / hot-side",
    "P2-W03": "stair / protected core",
    "P2-W04R": "retained bedroom edge",
    "P2-W05": "insulated shell + lining",
    "P2-W06": "future-phase closure",
}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(node: ET.Element) -> str:
    return "".join(node.itertext()).strip()


def _svg_float(value: str | None, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise CoordinationError(f"Invalid native legend coordinate for {label}") from error
    if not math.isfinite(number):
        raise CoordinationError(f"Non-finite native legend coordinate for {label}")
    return number


def _view_metadata(view_id: str) -> tuple[str, str | None, str]:
    """Return a declared reading purpose, paired coordination view, and legend scope."""
    if view_id.startswith("structure-"):
        purpose = "Structural study and screening"
        companion = "structure-coordination-plan"
        legend_scope = "source-specific; discipline meanings remain local"
    elif view_id in {
        "architecture-upper-floor",
        "architecture-access-egress",
        "architecture-owner-priorities",
    } or view_id.startswith("architecture-p2-"):
        purpose_by_view = {
            "architecture-upper-floor": "Architecture · upper-floor plan",
            "architecture-access-egress": "Architecture · access and egress study",
            "architecture-owner-priorities": "Architecture · owner-priorities study",
        }
        purpose = purpose_by_view.get(view_id, "Architecture · P2 detail / coordination study")
        companion = "plan-p2"
        legend_scope = (
            "P2 wall duties represented in this view are keyed"
            if view_id == "architecture-upper-floor"
            else "source-specific; access, phase, and design gates remain distinct"
        )
    elif "schedule" in view_id:
        purpose = "Architecture · opening schedule"
        companion = "plan-pb"
        legend_scope = "source-specific; row and status keys remain local"
    elif "elevation" in view_id:
        purpose = "Architecture · elevation"
        companion = "plan-p2" if "p2" in view_id else "plan-pb"
        legend_scope = "source-specific; material and study cues remain local"
    elif view_id.startswith("architecture-roof"):
        purpose = "Architecture · roof datum study"
        companion = "plan-pb"
        legend_scope = "source-specific; rooflight and datum cues remain local"
    elif "section" in view_id or "detail" in view_id or view_id.startswith("architecture-p"):
        purpose = "Architecture · detail / coordination study"
        companion = "plan-p2" if "p2" in view_id else "plan-pb"
        legend_scope = "source-specific; detail authority remains with its source"
    elif view_id in {"architecture-ground-floor", "architecture-ground-floor-core"}:
        purpose = "Architecture · ground-floor plan"
        companion = "plan-pb"
        legend_scope = "source-specific; local key coverage is not normalized"
    else:
        purpose = "Architecture · coordinated drawing"
        companion = "plan-p2" if "p2" in view_id else "plan-pb"
        legend_scope = "source-specific; local key coverage is not normalized"
    return purpose, companion, legend_scope


def _mark_role(node: ET.Element, role: str) -> None:
    node.set("data-text-role", role)


def _annotate_existing_hierarchy(
    root: ET.Element, view_id: str, purpose: str, companion: str | None
) -> None:
    """Expose existing title, reference, and authority hierarchy to readers/tools."""
    titles = list(root.iter(_NS + "title"))
    for title in titles:
        title.set("data-text-role", "document-title")

    descriptions = list(root.iter(_NS + "desc"))
    for description in descriptions:
        description.set("data-text-role", "document-description")

    # Native sheets use several source-specific title blocks.  Mark the largest
    # existing top-band label as the visible sheet title without changing its
    # text, size, coordinates, or paint.
    candidates: list[tuple[float, float, ET.Element]] = []
    for node in root.iter(_NS + "text"):
        if not _text(node):
            continue
        try:
            y = _svg_float(node.get("y", "0"), "title.y")
            size = _svg_float(node.get("font-size", "0"), "title.font-size")
        except CoordinationError:
            continue
        if y <= 120 and size > 0:
            candidates.append((size, -y, node))
    if candidates:
        max(candidates, key=lambda item: (item[0], item[1]))[2].set("data-text-role", "sheet-title")

    for node in root.iter():
        if node.get("data-related-view"):
            node.set("data-reference-role", "cross-view")
        if node.get("data-view-references"):
            node.set("data-panel-role", "view-references")
        if node.get("id") == "review-status-banner":
            node.set("data-panel-role", "authority-status")
            for label in node.iter(_NS + "text"):
                value = _text(label)
                if value.startswith("REVIEW ONLY"):
                    label.text = f"{value} · {purpose.upper()}"
                    _mark_role(label, "authority-status")
                elif value.startswith("OPEN GATES"):
                    _mark_role(label, "open-gate-summary")

    # The exact catalogue label remains in <title>; this short name lets a paired
    # reader expose a stable architecture/coordination relationship.
    if companion:
        root.set("data-reader-pair", companion.removeprefix("plan-"))
    root.set("data-visible-purpose", purpose)


def _quiet_decorative_patterns(root: ET.Element) -> None:
    for pattern in root.iter(_NS + "pattern"):
        pattern_id = pattern.get("id", "")
        opacity = _DECORATIVE_PATTERN_IDS.get(pattern_id)
        if opacity is None:
            continue
        pattern.set("data-presentation-role", "decorative-surface-pattern")
        pattern.set("data-pattern-treatment", "reduced-contrast; source spacing retained")
        for child in pattern:
            if _local_name(child.tag) not in {"line", "path", "polyline"}:
                continue
            child.set("opacity", f"{opacity:g}")


def _parent_index(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in list(parent)}


def _represented_p2_walls(
    root: ET.Element, schedule: Mapping[str, object]
) -> list[tuple[str, str, str | None, str]]:
    occurrences: dict[str, list[ET.Element]] = defaultdict(list)
    for node in root.iter():
        wall_id = node.get("data-wall-type")
        if wall_id:
            occurrences[wall_id].append(node)
    if not occurrences:
        raise CoordinationError("The P2 wall legend has no source-tagged wall instances")

    rows: list[tuple[str, str, str | None, str]] = []
    for wall_id in sorted(occurrences):
        if wall_id not in _WALL_LABELS:
            raise CoordinationError(f"No native P2 wall legend meaning is registered for {wall_id}")
        source = schedule.get(wall_id)
        if not isinstance(source, Mapping):
            raise CoordinationError(f"Missing P2 wall schedule source for {wall_id}")
        thickness = source.get("nominal_total_m")
        try:
            thickness_mm = round(float(thickness) * 1000)
        except (TypeError, ValueError, OverflowError) as error:
            raise CoordinationError(f"Invalid nominal P2 wall thickness for {wall_id}") from error
        if not math.isfinite(float(thickness)) or thickness_mm <= 0:
            raise CoordinationError(f"Invalid nominal P2 wall thickness for {wall_id}")
        source_name = source.get("name")
        if not isinstance(source_name, str) or not source_name.strip():
            raise CoordinationError(f"Missing source meaning for P2 wall type {wall_id}")

        instances = occurrences[wall_id]
        representative = instances[0]
        stroke = representative.get("stroke")
        if not stroke:
            raise CoordinationError(f"P2 wall type {wall_id} has no explicit portable stroke")
        dash = representative.get("stroke-dasharray")
        # Instances of one semantic wall duty must keep one visual key.
        if any(
            item.get("stroke") != stroke or item.get("stroke-dasharray") != dash
            for item in instances
        ):
            raise CoordinationError(f"P2 wall type {wall_id} has inconsistent native styling")
        rows.append((wall_id, stroke, dash, f"{thickness_mm} mm · {_WALL_LABELS[wall_id]}"))
    return rows


def _p2_wall_legend(root: ET.Element, snapshot: Mapping[str, object]) -> None:
    discipline_inputs = snapshot.get("discipline_inputs")
    programme = (
        discipline_inputs.get("programme") if isinstance(discipline_inputs, Mapping) else None
    )
    p2 = programme.get("p2") if isinstance(programme, Mapping) else None
    schedule = p2.get("wall_schedule") if isinstance(p2, Mapping) else None
    if not isinstance(schedule, Mapping):
        raise CoordinationError("Missing D-080 P2 wall schedule for native legend")

    title_nodes = [node for node in root.iter(_NS + "text") if _text(node) == "LEGEND"]
    if len(title_nodes) != 1:
        raise CoordinationError(f"Expected one native P2 legend heading, found {len(title_nodes)}")
    title = title_nodes[0]
    heading_x = _svg_float(title.get("x"), "P2 legend heading.x")
    heading_y = _svg_float(title.get("y"), "P2 legend heading.y")
    parents = _parent_index(root)

    # Read the non-wall symbol keys from the generator itself.  Their semantic
    # labels and paint are reused exactly; the incomplete old wall summary is
    # replaced by source-derived wall-duty rows below.
    text_by_key = {
        _text(node): node
        for node in root.iter(_NS + "text")
        if node is not title
        and node.get("x") is not None
        and _svg_float(node.get("x"), "P2 legend item.x") >= heading_x
        and heading_y < _svg_float(node.get("y"), "P2 legend item.y") < heading_y + 190
    }
    legend_markers = [
        node
        for node in root.iter()
        if _local_name(node.tag) in {"line", "rect"}
        and node.get("x1", node.get("x", ""))
        and _svg_float(node.get("x1", node.get("x")), "P2 legend marker.x") == heading_x
        and heading_y + 10
        <= _svg_float(node.get("y1", node.get("y")), "P2 legend marker.y")
        < heading_y + 190
    ]

    expected_base = {
        "exterior glazing": "exterior-glazing",
        "open balcony guard": "open-guard",
        "acoustic deck glazing": "deck-glazing",
        "D-048 column reserve": "column-reserve",
        "F1 / F2 boundary": "phase-boundary",
    }
    base_rows: list[tuple[ET.Element, ET.Element, str]] = []
    obsolete_text: list[ET.Element] = []
    for value, label in text_by_key.items():
        if value in expected_base:
            label_y = _svg_float(label.get("y"), "P2 legend label.y")
            candidates = [
                marker
                for marker in legend_markers
                if abs(
                    (
                        _svg_float(marker.get("y"), "P2 legend marker.y")
                        + _svg_float(marker.get("height", "0"), "P2 legend marker.height")
                        if _local_name(marker.tag) == "rect"
                        else _svg_float(marker.get("y1"), "P2 legend marker.y")
                    )
                    - label_y
                )
                <= 8
            ]
            marker_kind = "rect" if label.attrib.get("x") == "1374" else "line"
            marker = next(
                (node for node in candidates if _local_name(node.tag) == marker_kind),
                None,
            )
            if marker is None:
                raise CoordinationError(f"Missing native P2 legend symbol for {value}")
            base_rows.append((marker, label, expected_base[value]))
        elif value.startswith(
            ("W01A", "P2-W01", "Wet / sauna /", "All dimensions", "Wall build-ups")
        ):
            obsolete_text.append(label)
        else:
            # A new visible legend item must be classified before the composed
            # key can be certified as complete.
            raise CoordinationError(f"Unclassified native P2 legend entry: {value}")

    walls = _represented_p2_walls(root, schedule)
    base_rows.sort(key=lambda item: _svg_float(item[1].get("y"), "P2 base legend order"))
    for marker, label, _role in base_rows:
        marker_parent = parents.get(marker)
        label_parent = parents.get(label)
        if marker_parent is None or label_parent is None:
            raise CoordinationError("Native P2 legend items must have a parent group")
        marker_parent.remove(marker)
        label_parent.remove(label)
    for label in obsolete_text:
        parent = parents.get(label)
        if parent is not None:
            parent.remove(label)
    for marker in legend_markers:
        if marker not in [row[0] for row in base_rows]:
            parent = parents.get(marker)
            if parent is not None:
                parent.remove(marker)

    legend = ET.SubElement(
        root,
        _NS + "g",
        {
            "class": "native-local-legend",
            "data-legend-role": "p2-plan-local-key",
            "data-legend-source": "discipline_inputs.programme.p2.wall_schedule",
            "data-legend-coverage": "all source-tagged wall duties represented in this view",
            "aria-label": "Upper-floor plan legend; wall types are coordination duties, not performance ratings",
        },
    )
    x_marker = heading_x
    x_label = heading_x + 38
    title.set("font-size", "11")
    baseline = heading_y + 24
    row_count = len(base_rows) + len(walls)
    row_step = min(16.5, (heading_y + 194 - baseline - 2) / max(row_count, 1))
    for index, (marker, label, role) in enumerate(base_rows):
        y = baseline + index * row_step
        marker.set("data-legend-role", role)
        marker.set("data-visual-language-version", VISUAL_LANGUAGE_VERSION)
        if _local_name(marker.tag) == "line":
            marker.attrib.update(
                {"x1": f"{x_marker:g}", "x2": f"{x_marker + 28:g}", "y1": f"{y:g}", "y2": f"{y:g}"}
            )
        else:
            marker.attrib.update({"x": f"{x_marker:g}", "y": f"{y - 4:g}"})
        label.set("x", f"{x_label:g}")
        label.set("y", f"{y + 3:g}")
        label.set("font-size", "7.8")
        label.set("data-legend-role", role)
        label.set("data-visual-language-version", VISUAL_LANGUAGE_VERSION)
        legend.append(marker)
        legend.append(label)

    first_wall_y = baseline + len(base_rows) * row_step
    for index, (wall_id, stroke, dash, label_text) in enumerate(walls):
        y = first_wall_y + index * row_step
        duty = schedule[wall_id]
        full_name = str(duty["name"])
        item = ET.SubElement(
            legend,
            _NS + "g",
            {
                "data-legend-role": "wall-family",
                "data-wall-type": wall_id,
                "data-source-wall-name": full_name,
                "data-source-wall-instance-count": str(
                    sum(1 for node in root.iter() if node.get("data-wall-type") == wall_id)
                ),
                "data-visual-language-version": VISUAL_LANGUAGE_VERSION,
                "aria-label": f"{wall_id}, {label_text}, {full_name}; schematic coordination value",
            },
        )
        line_attrs = {
            "x1": f"{x_marker:g}",
            "y1": f"{y:g}",
            "x2": f"{x_marker + 28:g}",
            "y2": f"{y:g}",
            "stroke": stroke,
            "stroke-width": "4.5",
            "stroke-linecap": "butt",
            "data-legend-role": "wall-family-sample",
            "data-wall-type": wall_id,
            "data-visual-language-version": VISUAL_LANGUAGE_VERSION,
        }
        if dash:
            line_attrs["stroke-dasharray"] = dash
        ET.SubElement(item, _NS + "line", line_attrs)
        text = ET.SubElement(
            item,
            _NS + "text",
            {
                "x": f"{x_label:g}",
                "y": f"{y + 3:g}",
                "font-size": "10",
                "font-family": "IBM Plex Sans",
                "fill": "#172a33",
                "data-legend-role": "wall-family-label",
                "data-wall-type": wall_id,
                "data-visual-language-version": VISUAL_LANGUAGE_VERSION,
            },
        )
        text.text = f"{wall_id} · {label_text}"

    note = ET.SubElement(
        legend,
        _NS + "text",
        {
            "x": f"{x_marker:g}",
            "y": f"{first_wall_y + len(walls) * row_step + 2:g}",
            "font-size": "6.5",
            "font-family": "IBM Plex Sans",
            "fill": "#617078",
            "data-legend-role": "wall-family-limit",
            "data-visual-language-version": VISUAL_LANGUAGE_VERSION,
        },
    )
    note.text = "Colour / dash identifies duty; it does not rate performance."
    title.set("data-legend-role", "legend-heading")
    title.set("data-visual-language-version", VISUAL_LANGUAGE_VERSION)


def _qualify_p2_model_result(root: ET.Element) -> None:
    labels = [node for node in root.iter(_NS + "text") if _text(node) == "MODEL RESULT"]
    if len(labels) != 1:
        raise CoordinationError(f"Expected one P2 source-model result label, found {len(labels)}")
    labels[0].text = "SOURCE MODEL CHECKS · NOT DESIGN ACCEPTANCE"
    labels[0].set("data-text-role", "model-scope")
    labels[0].set("data-visual-language-version", VISUAL_LANGUAGE_VERSION)


def apply_native_visual_language(
    snapshot: Mapping[str, object], view_id: str, root: ET.Element
) -> None:
    """Apply candidate presentation roles to a connected native SVG root in place."""
    if _local_name(root.tag) != "svg":
        raise CoordinationError(f"Expected an SVG root for native visual language: {view_id}")
    if root.get("data-view-id") not in (None, view_id):
        raise CoordinationError(
            f"SVG view id {root.get('data-view-id')!r} does not match {view_id!r}"
        )
    purpose, companion, legend_scope = _view_metadata(view_id)
    root.set("data-visual-language-version", VISUAL_LANGUAGE_VERSION)
    root.set("data-visual-language-status", "candidate; review only")
    # Projection purpose belongs to the geometry contract. Presentation wording
    # has its own data-visible-purpose attribute and must not replace that contract.
    if not root.get("data-view-purpose"):
        root.set("data-view-purpose", purpose)
    root.set("data-coordination-companion", companion or "")
    root.set("data-legend-coverage", legend_scope)
    root.set("data-authority", "schematic; not for construction")
    _annotate_existing_hierarchy(root, view_id, purpose, companion)
    _quiet_decorative_patterns(root)
    if view_id == "architecture-upper-floor":
        _qualify_p2_model_result(root)
        _p2_wall_legend(root, snapshot)

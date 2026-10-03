"""Audit generated view identities, dimension anchors and cross-view callouts.

The inventory records declared coverage, not engineering adequacy. A broken reference
prevents publication instead of leaving a dimension or callout attached to old geometry.
"""

from __future__ import annotations

import json
import math
import posixpath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

from dreamhouse.coordination.drawing_annotations import audit_native_geometry
from dreamhouse.coordination.model import CoordinationError


def inspect_views(snapshot: dict, files: dict[str, str]) -> dict:
    by_entity = {key: [] for key in sorted(snapshot["entities"])}
    context_ids = {"PROJECT.PB", "PROJECT.P2"}
    pb_context = snapshot.get("discipline_inputs", {}).get("equipment", {}).get("pb", {})
    context_ids.update(w["id"] for w in pb_context.get("workstations", []))
    views = {}
    for name, value in sorted(files.items()):
        if not name.endswith(".svg"):
            continue
        root = ET.fromstring(value)
        view_id = root.get("data-view-id")
        if not view_id or view_id in views:
            raise CoordinationError(f"Missing or duplicate view identity in {name}")
        dom_ids = [e.attrib["id"] for e in root.iter() if "id" in e.attrib]
        if len(dom_ids) != len(set(dom_ids)):
            raise CoordinationError(f"Duplicate SVG occurrence/DOM ID in {name}")
        view = {
            "view_id": view_id,
            "file": name,
            "geometry_check": audit_native_geometry(snapshot, root),
            "occurrences": [],
            "anchors": {},
            "dimensions": [],
            "callouts": [],
            "callout_links": [],
        }
        seen_dimensions = set()
        for element in root.iter():
            entity_id = element.get("data-entity-id")
            if entity_id is not None and entity_id not in by_entity:
                raise CoordinationError(f"Unknown SVG entity {entity_id} in {name}")
            anchor_id = element.get("data-anchor-id")
            if anchor_id:
                owner = element.get("data-anchor-entity-id", entity_id)
                if owner is not None and owner not in by_entity:
                    raise CoordinationError(f"Unknown anchor entity {owner} in {name}")
                context = element.get("data-anchor-context-id")
                if context is not None and context not in context_ids:
                    raise CoordinationError(f"Unknown anchor context {context} in {name}")
                if anchor_id in view["anchors"] or not element.get("id"):
                    raise CoordinationError(
                        f"Duplicate or unaddressable anchor {anchor_id} in {name}"
                    )
                view["anchors"][anchor_id] = {
                    "target_id": element.get("id"),
                    "entity_id": owner,
                    "context_id": context,
                    "status": element.get("data-anchor-status", "known"),
                    "coordinates": {
                        k: v for k, v in element.attrib.items() if k.startswith("data-world-")
                    },
                }
                anchor = view["anchors"][anchor_id]
                for coordinate in anchor["coordinates"].values():
                    _finite_number(coordinate, f"anchor {anchor_id}")
                anchor["source_check"] = _check_anchor_source(snapshot, element, anchor)
            elif entity_id is not None:
                if not element.get("id"):
                    raise CoordinationError(f"Unaddressable occurrence {entity_id} in {name}")
                occurrence = {"entity_id": entity_id, "occurrence_id": element.get("id")}
                view["occurrences"].append(occurrence)
                by_entity[entity_id].append(
                    {"view": name, "view_id": view_id, "occurrence_id": element.get("id")}
                )
            if element.get("data-dimension-id"):
                identifier = element.get("data-dimension-id")
                if identifier in seen_dimensions:
                    raise CoordinationError(f"Duplicate dimension {identifier} in {name}")
                seen_dimensions.add(identifier)
                view["dimensions"].append(
                    {
                        "dimension_id": identifier,
                        "anchor_refs": element.get("data-anchor-refs", "").split(),
                        "anchor_targets": element.get("data-anchor-targets", "").split(),
                        "status": element.get("data-dimension-status", "known"),
                        "datum": element.get("data-datum"),
                        "direction": element.get("data-dimension-direction"),
                        "value": element.get("data-dimension-value"),
                        "unit": element.get("data-dimension-unit", "m"),
                        "source": element.get("data-dimension-source"),
                        "formula": element.get("data-dimension-formula"),
                        "label_check": _check_dimension_label(element),
                    }
                )
            if element.get("data-callout-refs") is not None:
                view["callouts"].append(
                    {
                        "callout_id": element.get("data-callout-id", element.get("id")),
                        "target_view_id": element.get("data-callout-target-view-id"),
                        "anchor_refs": element.get("data-callout-refs", "").split(),
                        "anchor_targets": element.get("data-callout-targets", "").split(),
                    }
                )
            if element.get("data-callout-link") is not None:
                view["callout_links"].append(
                    {
                        "callout_id": element.get("data-callout-link"),
                        "href": element.get("href"),
                    }
                )
        views[view_id] = view
    for view in views.values():
        for dimension in view["dimensions"]:
            refs, targets = dimension["anchor_refs"], dimension["anchor_targets"]
            if not refs or len(refs) != len(targets):
                raise CoordinationError(f"Unbound dimension {dimension['dimension_id']}")
            for ref, target in zip(refs, targets, strict=True):
                anchor = view["anchors"].get(ref)
                if anchor is None or anchor["target_id"] != target:
                    raise CoordinationError(f"Missing dimension anchor {ref} in {view['view_id']}")
                if anchor["status"] == "unresolved" and dimension["status"] in {
                    "known",
                    "resolved",
                    "evaluated",
                }:
                    raise CoordinationError(f"Dimension claims an unresolved anchor: {ref}")
            dimension["measurement_check"] = _check_measurement(dimension, view["anchors"])
        callouts_by_id = {}
        for callout in view["callouts"]:
            if callout["callout_id"] in callouts_by_id:
                raise CoordinationError(f"Duplicate callout in {view['view_id']}")
            callouts_by_id[callout["callout_id"]] = callout
            target = views.get(callout["target_view_id"])
            if not callout["callout_id"] or not callout["anchor_refs"] or target is None:
                raise CoordinationError(f"Unbound callout in {view['view_id']}")
            if any(ref not in target["anchors"] for ref in callout["anchor_refs"]):
                raise CoordinationError(f"Missing callout anchor in {view['view_id']}")
            if len(callout["anchor_refs"]) != len(callout["anchor_targets"]):
                raise CoordinationError(f"Missing callout DOM targets in {view['view_id']}")
            if any(
                target["anchors"][ref]["target_id"] != node
                for ref, node in zip(callout["anchor_refs"], callout["anchor_targets"], strict=True)
            ):
                raise CoordinationError(f"Incorrect callout DOM target in {view['view_id']}")
        for link in view["callout_links"]:
            callout = callouts_by_id.get(link["callout_id"])
            if callout is None:
                raise CoordinationError(f"Orphan callout navigation in {view['view_id']}")
            target = views[callout["target_view_id"]]
            address = urlsplit(link["href"] or "")
            linked_file = (
                posixpath.normpath(
                    posixpath.join(posixpath.dirname(view["file"]), unquote(address.path))
                )
                if address.path
                else view["file"]
            )
            if (
                address.scheme
                or address.netloc
                or address.query
                or linked_file != target["file"]
                or unquote(address.fragment) not in callout["anchor_targets"]
            ):
                raise CoordinationError(f"Incorrect callout navigation in {view['view_id']}")
    missing = [key for key, occurrences in by_entity.items() if not occurrences]
    return {
        "schema_version": 3,
        "scenario_id": snapshot["scenario_id"],
        "input_hash": snapshot["input_hash"],
        "entity_count": len(by_entity),
        "represented_entity_count": len(by_entity) - len(missing),
        "entities_without_svg_occurrences": missing,
        "views": list(views.values()),
        "by_entity": by_entity,
        "annotation_coverage": {
            "anchors": sum(len(v["anchors"]) for v in views.values()),
            "dimensions": sum(len(v["dimensions"]) for v in views.values()),
            "callouts": sum(len(v["callouts"]) for v in views.values()),
            "unresolved_anchors": sum(
                a["status"] == "unresolved" for v in views.values() for a in v["anchors"].values()
            ),
            "source_bound_anchors": sum(
                a["source_check"]["state"] == "evaluated"
                for v in views.values()
                for a in v["anchors"].values()
            ),
            "evaluated_dimensions": sum(
                d["measurement_check"]["state"] == "evaluated"
                for v in views.values()
                for d in v["dimensions"]
            ),
            "verified_dimension_labels": sum(
                d["label_check"]["state"] == "evaluated"
                for v in views.values()
                for d in v["dimensions"]
            ),
            "views_without_named_dimensions": [
                v["view_id"] for v in views.values() if not v["dimensions"]
            ],
        },
        "limitation": "Named annotation coverage is reported separately from occurrence presence; neither proves engineering or full drawing coverage.",
    }


def _finite_number(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise CoordinationError(f"Invalid numeric {label}")
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise CoordinationError(f"Invalid numeric {label}: {value!r}") from exc
    if not math.isfinite(number):
        raise CoordinationError(f"Nonfinite {label}")
    return number


def _check_anchor_source(snapshot: dict, element: ET.Element, anchor: dict) -> dict:
    """Check explicit snapshot paths independently of the coordinates printed in SVG."""
    raw = element.get("data-anchor-bindings")
    if raw is None:
        return {"state": "unresolved" if anchor["status"] == "unresolved" else "unbound"}

    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise CoordinationError(f"Duplicate anchor binding: {key}")
            result[key] = value
        return result

    try:
        bindings = json.loads(raw, object_pairs_hook=unique_pairs)
    except (ValueError, TypeError) as exc:
        raise CoordinationError("Invalid anchor source bindings") from exc
    axes = {key.removeprefix("data-world-") for key in anchor["coordinates"]}
    if not isinstance(bindings, dict) or not axes or set(bindings) != axes:
        raise CoordinationError("Anchor bindings must cover exactly its world coordinates")
    if not axes <= {"x", "y", "z"} or anchor["status"] == "unresolved":
        raise CoordinationError("Cannot source-bind an unresolved or unknown-axis anchor")

    def resolve_path(path):
        if (
            not isinstance(path, list)
            or not path
            or any(type(key) not in {str, int} for key in path)
            or path[0] not in {"entities", "geometry", "discipline_inputs"}
        ):
            raise CoordinationError("Invalid anchor source path")
        if anchor["entity_id"] is not None and path[:2] != ["entities", anchor["entity_id"]]:
            raise CoordinationError("Anchor source path disagrees with its entity owner")
        source = snapshot
        try:
            for key in path:
                if isinstance(source, list) and (type(key) is not int or key < 0):
                    raise KeyError(key)
                source = source[key]
        except (KeyError, IndexError, TypeError) as exc:
            raise CoordinationError(f"Missing anchor source path: {path}") from exc
        if type(source) not in {int, float}:
            raise CoordinationError("Anchor source must be a numeric model value")
        return _finite_number(source, "anchor source")

    for axis, binding in bindings.items():
        if isinstance(binding, dict):
            if (
                set(binding) != {"mean"}
                or not isinstance(binding["mean"], list)
                or len(binding["mean"]) != 2
            ):
                raise CoordinationError("Unknown anchor source expression")
            expected = sum(resolve_path(path) for path in binding["mean"]) / 2
        else:
            expected = resolve_path(binding)
        observed = _finite_number(anchor["coordinates"][f"data-world-{axis}"], "anchor coordinate")
        if not math.isclose(expected, observed, rel_tol=0, abs_tol=1e-6):
            raise CoordinationError(
                f"Anchor disagrees with source: {element.get('data-anchor-id')}"
            )
    return {"state": "evaluated", "bindings": bindings, "numerical_tolerance_m": 1e-6}


def _check_dimension_label(element: ET.Element) -> dict:
    label_format = element.get("data-dimension-label-format")
    if label_format is None:
        return {"state": "unbound", "reason": "No visible numeric label contract declared"}
    if label_format not in {"fixed-2-m", "fixed-2-m2"}:
        raise CoordinationError(f"Unknown dimension label format: {label_format}")
    if element.tag.rsplit("}", 1)[-1] != "text":
        raise CoordinationError("A dimension label contract must address SVG text")
    unit = "m2" if label_format == "fixed-2-m2" else "m"
    if element.get("data-dimension-unit", "m") != unit:
        raise CoordinationError("Dimension label unit disagrees with its measurement")
    value = _finite_number(element.get("data-dimension-value"), "dimension label")

    # SVG title/description children are accessible metadata, not painted labels.
    def painted_text(node):
        pieces = [node.text or ""]
        for child in node:
            if child.tag.rsplit("}", 1)[-1] not in {"title", "desc", "metadata"}:
                pieces.append(painted_text(child))
            pieces.append(child.tail or "")
        return "".join(pieces)

    expected = f"{value:.2f} {unit}"
    if painted_text(element).strip() != expected:
        raise CoordinationError(
            f"Visible dimension label disagrees with value: {element.get('data-dimension-id')}"
        )
    return {"state": "evaluated", "format": label_format, "expected_text": expected}


def _check_measurement(dimension: dict, anchors: dict) -> dict:
    refs = dimension["anchor_refs"]
    value = (
        _finite_number(dimension["value"], f"dimension {dimension['dimension_id']}")
        if dimension["value"] is not None
        else None
    )
    if (
        len(refs) == 4
        and value is not None
        and dimension["unit"] == "m2"
        and dimension.get("formula") == "width_m * height_m"
    ):
        spans = []
        vectors = []
        for pair in (refs[:2], refs[2:]):
            left, right = [anchors[ref]["coordinates"] for ref in pair]
            axes = sorted(left.keys() & right.keys())
            if not axes:
                return {
                    "state": "unsupported",
                    "reason": "Area anchors lack shared coordinate axes",
                }
            spans.append(
                math.dist(
                    [_finite_number(left[k], "area anchor") for k in axes],
                    [_finite_number(right[k], "area anchor") for k in axes],
                )
            )
            vectors.append({k: float(right[k]) - float(left[k]) for k in axes})
        if (
            abs(vectors[0].get("data-world-z", 0)) > 1e-6
            or abs(vectors[1].get("data-world-z", 0)) < 1e-9
            or any(abs(vectors[1].get(k, 0)) > 1e-6 for k in ("data-world-x", "data-world-y"))
            or spans[0] <= 0
        ):
            raise CoordinationError(
                "Opening area requires horizontal width and vertical height anchors"
            )
        measured = spans[0] * spans[1]
        if not math.isclose(value, measured, rel_tol=0, abs_tol=1e-6):
            raise CoordinationError(f"Area disagrees with anchors: {dimension['dimension_id']}")
        return {
            "state": "evaluated",
            "measured_m2": measured,
            "span_lengths_m": spans,
            "numerical_tolerance_m2": 1e-6,
            "construction_tolerance": False,
        }
    if len(refs) != 2 or dimension["value"] is None or dimension["unit"] != "m":
        return {"state": "unsupported", "reason": "No two-anchor linear measurement declared"}
    left, right = [anchors[ref]["coordinates"] for ref in refs]
    axes = sorted(left.keys() & right.keys())
    if dimension["direction"] == "vertical level comparison":
        axes = ["data-world-z"] if "data-world-z" in axes else []
    if not axes:
        return {"state": "unsupported", "reason": "No shared world-coordinate axes"}
    values = [
        float(dimension["value"]),
        *[float(left[k]) for k in axes],
        *[float(right[k]) for k in axes],
    ]
    if not all(math.isfinite(value) for value in values):
        raise CoordinationError(f"Nonfinite dimension: {dimension['dimension_id']}")
    measured = (
        float(right[axes[0]]) - float(left[axes[0]])
        if dimension["direction"] == "vertical level comparison"
        else math.dist([float(left[k]) for k in axes], [float(right[k]) for k in axes])
    )
    if not math.isclose(values[0], measured, rel_tol=0, abs_tol=1e-6):
        raise CoordinationError(f"Dimension disagrees with anchors: {dimension['dimension_id']}")
    return {
        "state": "evaluated",
        "measured_m": measured,
        "numerical_tolerance_m": 1e-6,
        "axes": axes,
        "construction_tolerance": False,
    }


def compare_anchors(current: dict, baseline: dict) -> dict:
    def indexed(inventory):
        return {
            (v["view_id"], key): value
            for v in inventory["views"]
            for key, value in v["anchors"].items()
        }

    before, after = indexed(baseline), indexed(current)
    items = []
    for view_id, anchor_id in sorted(before.keys() | after.keys()):
        key = (view_id, anchor_id)
        state = (
            "added"
            if key not in before
            else "removed"
            if key not in after
            else "unchanged"
            if before[key] == after[key]
            else "changed"
        )
        items.append(
            {
                "view_id": view_id,
                "anchor_id": anchor_id,
                "state": state,
                "before": before.get(key),
                "after": after.get(key),
            }
        )
    return {
        "baseline_scenario_id": baseline["scenario_id"],
        "items": items,
        "limitation": "Removed anchors are not resolved dimensions. Any remaining broken dimension/callout reference blocks candidate publication.",
    }

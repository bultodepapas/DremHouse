"""Audit generated view identities, dimension anchors and cross-view callouts.

The inventory records declared coverage, not engineering adequacy. A broken reference
prevents publication instead of leaving a dimension or callout attached to old geometry.
"""

from __future__ import annotations

import math
import posixpath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

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
        "schema_version": 2,
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
            "views_without_named_dimensions": [
                v["view_id"] for v in views.values() if not v["dimensions"]
            ],
        },
        "limitation": "Named annotation coverage is reported separately from occurrence presence; neither proves engineering or full drawing coverage.",
    }


def _check_measurement(dimension: dict, anchors: dict) -> dict:
    refs = dimension["anchor_refs"]
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

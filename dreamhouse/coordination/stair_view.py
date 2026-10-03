"""SC-01 source-envelope section; no inferred stair solid or discharge geometry."""

from __future__ import annotations

import json
import math
from xml.etree import ElementTree as ET

NS = "http://www.w3.org/2000/svg"
VIEW = "stair-sections"


def render_stair_section(snapshot: dict, evaluation: dict) -> str:
    def node(parent, tag, **attrs):
        return ET.SubElement(
            parent, f"{{{NS}}}{tag}", {k.replace("_", "-"): str(v) for k, v in attrs.items()}
        )

    def text(parent, x, y, value, size=14, **attrs):
        element = node(parent, "text", x=x, y=y, font_size=size, fill="#18313b", **attrs)
        element.text = str(value)
        return element

    def known(value):
        return type(value) in {int, float} and math.isfinite(value)

    root = ET.Element(
        f"{{{NS}}}svg",
        {
            "id": f"{VIEW}-root",
            "viewBox": "0 0 1400 960",
            "width": "1400",
            "height": "960",
            "role": "img",
            "aria-labelledby": f"{VIEW}-title {VIEW}-description",
            "data-view-id": VIEW,
            "data-status": "coordination projection",
            "data-scenario-id": snapshot.get("scenario_id", ""),
            "data-input-hash": snapshot.get("input_hash", ""),
            "data-model-hash": snapshot.get("model_hash", ""),
            "data-view-purpose": "SC-01 cross-level source-envelope coordination",
            "data-projection-basis": "XZ projection of parallel flights; not a cut through both flights",
            "data-projected-axes": "x z",
            "data-construction-authority": "false",
        },
    )
    node(root, "title", id=f"{VIEW}-title").text = "SC-01 cross-level coordination section"
    node(
        root, "desc", id=f"{VIEW}-description"
    ).text = "Source flight and landing envelopes share plan identities. Stair solids, nosings, headroom and rear discharge remain unresolved."
    node(root, "rect", x=0, y=0, width=1400, height=960, fill="#f4f0e7")
    root.set("font-family", "IBM Plex Sans")
    text(root, 55, 52, "SC-01 · CROSS-LEVEL COORDINATION", 26, font_weight="700")
    text(
        root,
        55,
        82,
        "Parallel-flight source envelopes projected in XZ; distinct Y bands remain identified. No headroom or egress approval.",
        13,
    )
    entities = snapshot.get("entities", {})
    identifiers = ["ST-F1", "ST-F2", "ST-L1"]
    usable = {
        k: entities[k]
        for k in identifiers
        if k in entities
        and all(known(entities[k].get("geometry", {}).get(f)) for f in ["x0", "x1", "z0", "z1"])
    }
    if usable:
        x_min = min(e["geometry"]["x0"] for e in usable.values())
        x_max = max(e["geometry"]["x1"] for e in usable.values())
        z_min = min(e["geometry"]["z0"] for e in usable.values())
        z_max = max(e["geometry"]["z1"] for e in usable.values())
        scale = min(650 / max(x_max - x_min, 0.1), 400 / max(z_max - z_min, 0.1))
        ox, oz = 140 - x_min * scale, 590 + z_min * scale
        root.set(
            "data-world-to-view",
            json.dumps({"axes": ["x", "z"], "scale": [scale, -scale], "offset": [ox, oz]}),
        )

        def project(x, z):
            return ox + x * scale, oz - z * scale

        for index, (identifier, entity) in enumerate(usable.items()):
            g = entity["geometry"]
            group = node(
                root,
                "g",
                id=f"{VIEW}-occurrence-{identifier}",
                data_entity_id=identifier,
                data_representation_role="source-rise-envelope",
            )
            node(
                group, "title"
            ).text = f"{identifier}; Y={g.get('y0')}–{g.get('y1')} m; {entity['source']['path']}"
            x0, z0, x1, z1 = g["x0"], g["z0"], g["x1"], g["z1"]
            # The upper flight's source direction is -X. An unsupported direction
            # must remain an envelope rather than being drawn as an invented ascent.
            flight_key = "lower_flight" if identifier == "ST-F1" else "upper_flight"
            source = (
                snapshot.get("discipline_inputs", {})
                .get("structure", {})
                .get("stair", {})
                .get("stair", {})
                .get(flight_key, {})
            )
            direction = source.get("up_direction")
            if identifier == "ST-L1" or direction in {"+X", "-X"}:
                a, b = (
                    (project(x1, z0), project(x0, z1))
                    if direction == "-X" and identifier != "ST-L1"
                    else (project(x0, z0), project(x1, z1))
                )
                node(
                    group,
                    "line",
                    x1=a[0],
                    y1=a[1],
                    x2=b[0],
                    y2=b[1],
                    stroke="#195b69",
                    stroke_width=5,
                )
            else:
                a, b = project(x0, z1), project(x1, z0)
                node(
                    group,
                    "rect",
                    x=a[0],
                    y=a[1],
                    width=b[0] - a[0],
                    height=b[1] - a[1],
                    fill="none",
                    stroke="#a76815",
                    stroke_dasharray="5 4",
                )
            mx, my = project((x0 + x1) / 2, (z0 + z1) / 2)
            text(
                group,
                mx,
                my - 22 if identifier != "ST-F1" else my + 32,
                f"{identifier} · Y {g.get('y0')}–{g.get('y1')} m",
                12,
                stroke="#f4f0e7",
                stroke_width=4,
                paint_order="stroke",
            )
            if identifier in {"ST-F1", "ST-L1"}:
                level_x, level_y = project(x0, z0)
                text(
                    group,
                    level_x + 8,
                    level_y + 24,
                    f"{'PB' if identifier == 'ST-F1' else 'Landing'} +{z0:.2f} m · X={x0:.2f} m",
                    12,
                )
            if z1 > z0:
                refs = []
                targets = []
                for field in ["z0", "z1"]:
                    ref = f"{identifier}.rise.{field}"
                    target = f"{VIEW}-anchor-{identifier}-{field}"
                    node(
                        group,
                        "circle",
                        id=target,
                        cx=90 + index * 32,
                        cy=project(x0, g[field])[1],
                        r=3,
                        fill="#195b69",
                        data_anchor_id=ref,
                        data_anchor_entity_id=identifier,
                        data_anchor_status="resolved",
                        data_world_z=g[field],
                        data_anchor_bindings=json.dumps(
                            {"z": ["entities", identifier, "geometry", field]}
                        ),
                    )
                    refs.append(ref)
                    targets.append(target)
                y0, y1 = project(x0, z0)[1], project(x0, z1)[1]
                node(
                    group,
                    "line",
                    x1=90 + index * 32,
                    y1=y0,
                    x2=90 + index * 32,
                    y2=y1,
                    stroke="#195b69",
                )
                text(
                    group,
                    82 + index * 32,
                    (y0 + y1) / 2,
                    f"{z1 - z0:.2f} m",
                    12,
                    text_anchor="end",
                    data_dimension_id=f"{identifier}.rise",
                    data_dimension_value=z1 - z0,
                    data_dimension_unit="m",
                    data_dimension_status="resolved",
                    data_dimension_direction="vertical",
                    data_dimension_label_format="fixed-2-m",
                    data_anchor_refs=" ".join(refs),
                    data_anchor_targets=" ".join(targets),
                )
        door = entities.get("D-STAIR", {}).get("geometry", {})
        if known(door.get("x0")) and known(door.get("z0")):
            x, y = project(door["x0"], door["z0"])
            group = node(
                root,
                "g",
                id=f"{VIEW}-occurrence-D-STAIR",
                data_entity_id="D-STAIR",
                data_representation_role="access-floor-datum-only",
            )
            node(group, "circle", cx=x, cy=y, r=5, fill="#a76815")
            text(
                group,
                x + 12,
                y - 15,
                f"D-STAIR floor +{door['z0']:.2f} m; opening height unknown",
                12,
            )
    else:
        text(root, 80, 200, "SC-01 source extents unavailable; no stair section inferred.", 18)
    text(root, 850, 165, "SOURCE AND REVIEW GATES", 17, font_weight="700")
    findings = [
        f for f in evaluation.get("findings", []) if f.get("rule_id", "").startswith("SC01-")
    ]
    import textwrap

    y = 200
    for finding in findings:
        text(root, 850, y, f"{finding['status']} · {finding['rule_id']}", 10, font_weight="700")
        y += 22
        for line in textwrap.wrap(finding["message"], width=62):
            text(root, 850, y, line, 11)
            y += 17
        y += 20
    text(root, 70, 710, "REAR DISCHARGE · CF-011 / CF-013", 18, font_weight="700")
    text(
        root,
        70,
        740,
        "EXT-ESC remains unlocated. The source landing datum does not locate or approve an exterior exit.",
        13,
    )
    text(
        root,
        70,
        770,
        "Support reservations are plan hypotheses; member profiles, connections, nosings, headroom and guards need source evidence.",
        13,
    )
    for index, identifier in enumerate(identifiers):
        if identifier not in usable:
            text(root, 70, 800 + index * 18, f"{identifier}: source envelope unavailable", 12)
    text(
        root,
        55,
        915,
        "NOT FOR CONSTRUCTION · Source envelopes and arithmetic are not construction geometry or professional approval.",
        14,
        font_weight="700",
    )
    return ET.tostring(root, encoding="unicode")

"""SC-01 source-envelope section; no inferred stair solid or discharge geometry."""

from __future__ import annotations

import json
import math
import textwrap
from collections.abc import Mapping
from xml.etree import ElementTree as ET

from dreamhouse.svg.style import compile_svg_styles
from dreamhouse.svg.theme import THEME_COLOURS, role_colour

NS = "http://www.w3.org/2000/svg"
VIEW = "stair-sections"
INK = THEME_COLOURS["ink"]
PAPER = THEME_COLOURS["paper"]
PANEL = THEME_COLOURS["panel"]
MUTED = THEME_COLOURS["muted"]
RULE = THEME_COLOURS["sheet-rule"]
INFO = THEME_COLOURS["info"]
OPEN = THEME_COLOURS["open"]
FAIL = THEME_COLOURS["conflict"]
STUDY = THEME_COLOURS["hypothesis"]
SELECTION = role_colour("selection.focus")


def render_stair_section(snapshot: dict, evaluation: dict) -> str:
    def node(parent, tag, **attrs):
        return ET.SubElement(
            parent,
            f"{{{NS}}}{tag}",
            {("class" if k == "class_" else k.replace("_", "-")): str(v) for k, v in attrs.items()},
        )

    def text(parent, x, y, value, size=14, **attrs):
        values = {"x": x, "y": y, "font_size": size, "fill": INK}
        values.update(attrs)
        element = node(parent, "text", **values)
        element.text = str(value)
        return element

    def known(value):
        return type(value) in {int, float} and math.isfinite(value)

    entities = snapshot.get("entities", {})
    entities = entities if isinstance(entities, Mapping) else {}
    identifiers = ["ST-F1", "ST-F2", "ST-L1"]
    usable = {
        key: entities[key]
        for key in identifiers
        if key in entities
        and isinstance(entities[key], Mapping)
        and all(known(entities[key].get("geometry", {}).get(field)) for field in ["x0", "x1", "z0", "z1"])
    }
    door_geometry = entities.get("D-STAIR", {}).get("geometry", {})
    door_usable = bool(usable) and known(door_geometry.get("x0")) and known(door_geometry.get("z0"))
    visible_ids = set(usable)
    if door_usable:
        visible_ids.add("D-STAIR")

    records = evaluation.get("findings", [])
    records = records if isinstance(records, list) else []
    review_records = [
        (index, finding)
        for index, finding in enumerate(records)
        if isinstance(finding, Mapping)
        and str(finding.get("status", "")).upper() in {"OPEN", "FAIL"}
    ]
    local_records = [
        (index, finding)
        for index, finding in review_records
        if visible_ids.intersection(
            str(value)
            for value in finding.get("entity_ids", [])
            if isinstance(finding.get("entity_ids", []), (list, tuple, set))
        )
    ]
    local_open = sum(str(item.get("status", "")).upper() == "OPEN" for _, item in local_records)
    local_fail = sum(str(item.get("status", "")).upper() == "FAIL" for _, item in local_records)
    project_open = sum(str(item.get("status", "")).upper() == "OPEN" for _, item in review_records)
    project_fail = sum(str(item.get("status", "")).upper() == "FAIL" for _, item in review_records)

    message_lines = []
    row_heights = []
    for _index, finding in local_records:
        lines = textwrap.wrap(str(finding.get("message", "")), width=72) or [""]
        message_lines.append(lines[:2])
        row_heights.append(33 + 12 * min(2, len(lines)))
    panel_top = 178
    first_row_y = panel_top + 76
    panel_bottom = first_row_y + sum(row_heights)
    footer_y = max(900, panel_bottom + 84)
    height = footer_y + 60

    root = ET.Element(
        f"{{{NS}}}svg",
        {
            "id": f"{VIEW}-root",
            "viewBox": f"0 0 1400 {height}",
            "width": "1400",
            "height": str(height),
            "preserveAspectRatio": "xMidYMid meet",
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
            "data-visual-language-version": "connected-atlas-1",
            "data-local-open-count": str(local_open),
            "data-local-fail-count": str(local_fail),
            "data-project-open-count": str(project_open),
            "data-project-fail-count": str(project_fail),
        },
    )
    node(root, "title", id=f"{VIEW}-title").text = "SC-01 cross-level coordination section"
    node(
        root, "desc", id=f"{VIEW}-description"
    ).text = "Source flight and landing envelopes share plan identities. Stair solids, nosings, headroom and rear discharge remain unresolved."
    node(root, "style").text = f"""
text {{ font-family: "IBM Plex Sans", "Liberation Sans", Arial, sans-serif; text-rendering: geometricPrecision; }}
.entity-occurrence.is-selected .entity-shape {{ filter: drop-shadow(0 0 3px {SELECTION}); }}
.authority-label {{ fill: {INK}; font-weight: 800; letter-spacing: .4px; }}
.role-legend-label {{ fill: {INK}; }}
.finding-heading {{ font-weight: 700; }}
.finding-register-link {{ fill: {INFO}; font-weight: 700; text-decoration: underline; }}
.small {{ fill: {MUTED}; }}
""".strip()
    node(root, "metadata").text = json.dumps(
        {
            "scenario_id": snapshot.get("scenario_id"),
            "schema_version": snapshot.get("schema_version"),
            "input_hash": snapshot.get("input_hash"),
            "model_hash": snapshot.get("model_hash"),
            "status": "coordination projection",
            "construction_authority": False,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    node(root, "rect", x=0, y=0, width=1400, height=height, fill=PAPER, stroke="none")
    text(root, 55, 25, "DREAM HOUSE · GENERATED REVIEW VIEW", 10, fill=INFO, font_weight="700")
    text(root, 55, 57, "SC-01 · CROSS-LEVEL COORDINATION", 26, font_weight="700")
    text(
        root,
        55,
        81,
        "Parallel-flight source envelopes projected in XZ; distinct Y bands remain identified.",
        12,
        fill=MUTED,
    )
    text(
        root,
        55,
        102,
        f"Scenario {snapshot.get('scenario_id', 'unknown')} · schema {snapshot.get('schema_version', 'unknown')} · model {str(snapshot.get('model_hash', ''))[:18]}",
        9,
        fill=MUTED,
    )
    node(root, "rect", x=1085, y=22, width=315, height=31, rx=3, fill=PANEL, stroke=RULE)
    text(root, 1242.5, 43, "NOT FOR CONSTRUCTION", 13, font_weight="800", text_anchor="middle", class_="authority-label")
    text(root, 1085, 75, f"Input: {str(snapshot.get('input_hash', ''))[:24]}", 9, fill=MUTED)
    node(root, "line", x1=40, y1=116, x2=1400, y2=116, stroke=RULE)

    def legend_line(x, y, role, label, color, *, dash=None, width=2):
        group = node(root, "g", data_legend_role=role, aria_label=label)
        node(
            group,
            "line",
            x1=x,
            y1=y - 4,
            x2=x + 24,
            y2=y - 4,
            stroke=color,
            stroke_width=width,
            stroke_dasharray=dash or "",
        )
        text(group, x + 31, y, label, 9, class_="role-legend-label")

    if usable:
        legend_line(55, 143, "geometry.structure-envelope", "Stair source envelope · solid", INFO)
        if any(
            str(entity.get("status", "")).lower() == "context" for entity in usable.values()
        ):
            legend_line(285, 143, "representation.context", "Context only · source bounds", MUTED, dash="4 3")
        if any(str(entity.get("status", "")).lower() == "study" for entity in usable.values()):
            legend_line(515, 143, "status.study", "Study · dashed outline", STUDY, dash="6 4")
        if door_usable:
            node(root, "circle", cx=755, cy=139, r=4, fill=OPEN, stroke=OPEN)
            text(root, 766, 143, "Access-floor datum only", 9, data_legend_role="access-floor-datum-only")
        legend_line(1010, 143, "selection.focus", "Selection · cobalt halo", SELECTION, width=3)
    else:
        text(root, 55, 143, "No source envelope role is present in this projection.", 9, fill=MUTED)
    node(root, "line", x1=40, y1=158, x2=1400, y2=158, stroke=RULE)

    scale = ox = oz = None
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
            source_meta = entity.get("source", {})
            source_meta = source_meta if isinstance(source_meta, Mapping) else {}
            group = node(
                root,
                "g",
                id=f"{VIEW}-occurrence-{identifier}",
                class_="entity-occurrence",
                data_entity_id=identifier,
                data_kind=entity.get("kind", "stair"),
                data_level=entity.get("level", "unknown"),
                data_status=entity.get("status", "unknown"),
                data_visual_role="geometry.structure-envelope",
                data_representation_role="source-rise-envelope",
                data_source_path=source_meta.get("path", ""),
                data_source_key=source_meta.get("key", ""),
                data_world_x0=g.get("x0"),
                data_world_x1=g.get("x1"),
                data_world_y0=g.get("y0"),
                data_world_y1=g.get("y1"),
                data_world_z0=g.get("z0"),
                data_world_z1=g.get("z1"),
            )
            node(group, "title").text = (
                f"{identifier}; Y={g.get('y0')}–{g.get('y1')} m; "
                f"{source_meta.get('path', 'source path unavailable')} · {source_meta.get('key', 'source key unavailable')}"
            )
            x0, z0, x1, z1 = g["x0"], g["z0"], g["x1"], g["z1"]
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
                    stroke=INFO,
                    stroke_width=5,
                    class_="entity-shape",
                    vector_effect="non-scaling-stroke",
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
                    stroke=OPEN,
                    stroke_dasharray="5 4",
                    class_="entity-shape",
                    data_representation_role="ascent-direction-unresolved",
                )
            mx, my = project((x0 + x1) / 2, (z0 + z1) / 2)
            text(
                group,
                mx,
                my - 22 if identifier != "ST-F1" else my + 32,
                f"{identifier} · Y {g.get('y0')}–{g.get('y1')} m",
                12,
                stroke=PAPER,
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
                        fill=INFO,
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
                    stroke=INFO,
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

    if door_usable:
        x, y = project(door_geometry["x0"], door_geometry["z0"])
        door_source = entities["D-STAIR"].get("source", {})
        door_source = door_source if isinstance(door_source, Mapping) else {}
        group = node(
            root,
            "g",
            id=f"{VIEW}-occurrence-D-STAIR",
            class_="entity-occurrence",
            data_entity_id="D-STAIR",
            data_kind=entities["D-STAIR"].get("kind", "door"),
            data_level=entities["D-STAIR"].get("level", "unknown"),
            data_status=entities["D-STAIR"].get("status", "unknown"),
            data_visual_role="geometry.opening",
            data_representation_role="access-floor-datum-only",
            data_source_path=door_source.get("path", ""),
            data_source_key=door_source.get("key", ""),
        )
        node(group, "title").text = "D-STAIR; floor datum only; opening height unknown"
        node(group, "circle", cx=x, cy=y, r=5, fill=OPEN, stroke=OPEN, class_="entity-shape")
        text(group, x + 12, y - 15, f"D-STAIR floor +{door_geometry['z0']:.2f} m; opening height unknown", 12)
    elif not usable:
        text(root, 80, 220, "SC-01 source extents unavailable; no stair section inferred.", 18)

    # The stair view retains every entity-linked OPEN and FAIL record. Each row
    # links to its complete source text in the project register.
    text(root, 850, panel_top + 18, "STAIR-RELATED EVIDENCE", 17, font_weight="700")
    text(
        root,
        850,
        panel_top + 39,
        f"LOCAL · {local_open} OPEN · {local_fail} FAIL",
        9,
        fill=MUTED,
    )
    project_link = node(
        root,
        "a",
        href="index.html#project-finding-register",
        data_evidence_navigation="project-finding-register",
        aria_label="Open the complete project finding register",
    )
    text(
        project_link,
        850,
        panel_top + 56,
        f"PROJECT TOTAL · {project_open} OPEN · {project_fail} FAIL · register ↗",
        9,
        class_="finding-register-link",
    )
    cursor = first_row_y
    for row_index, ((finding_index, finding), wrapped) in enumerate(
        zip(local_records, message_lines, strict=True)
    ):
        status = str(finding.get("status", "OPEN")).upper()
        color = FAIL if status == "FAIL" else OPEN
        rule_id = str(finding.get("rule_id", "finding"))
        message = str(finding.get("message", ""))
        heading = f"{status} · {rule_id}"
        row = node(
            root,
            "a",
            href=f"index.html#html-finding-{finding_index}",
            id=f"{VIEW}-finding-{finding_index:04d}",
            data_finding_id=rule_id,
            data_finding_index=finding_index,
            aria_label=f"{heading}. {message}",
        )
        node(
            row,
            "rect",
            x=844,
            y=cursor + 2,
            width=500,
            height=row_heights[row_index] - 5,
            rx=2,
            fill=PANEL,
            stroke=RULE,
        )
        node(
            row,
            "rect",
            x=844,
            y=cursor + 2,
            width=4,
            height=row_heights[row_index] - 5,
            rx=2,
            fill=color,
            stroke=color,
        )
        text(row, 857, cursor + 16, heading, 9.5, fill=color, class_="finding-heading")
        for line_index, line in enumerate(wrapped):
            shown = line
            if line_index == 1 and len(textwrap.wrap(message, width=72)) > 2:
                shown = line[:68].rstrip() + "…"
            text(row, 857, cursor + 31 + line_index * 11, shown, 9, fill=MUTED, class_="small")
        node(row, "title").text = f"{heading}. {message}"
        cursor += row_heights[row_index]

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
    node(root, "line", x1=40, y1=footer_y, x2=1400, y2=footer_y, stroke=RULE)
    node(root, "rect", x=40, y=footer_y + 14, width=260, height=27, rx=2, fill=PANEL, stroke=RULE)
    text(root, 170, footer_y + 33, "COORDINATION PROJECTION", 10, class_="authority-label", text_anchor="middle")
    text(root, 320, footer_y + 31, "NOT FOR CONSTRUCTION · Source envelopes and arithmetic are not construction geometry or professional approval.", 10, class_="authority-label")
    compile_svg_styles(root)
    return ET.tostring(root, encoding="unicode")

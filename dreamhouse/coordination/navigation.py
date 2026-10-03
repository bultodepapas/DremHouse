"""Add a human-readable, source-linked index to a coordination review page."""

from __future__ import annotations

import html
from collections import Counter
from pathlib import PurePosixPath
from urllib.parse import quote, urlsplit


def attach_navigation(page: str, snapshot: dict, inventory: dict) -> str:
    """Attach occurrence links and declared annotation coverage to the HTML index.

    Links are emitted only when an inventory reference resolves to an occurrence in
    exactly one inventoried SVG and that SVG has a safe relative path. This keeps the
    panel useful when handed a partial or inconsistent inventory without inventing
    destinations.
    """
    entities = snapshot.get("entities", {})
    entities = entities if isinstance(entities, dict) else {}
    views = inventory.get("views", [])
    views = views if isinstance(views, list) else []
    by_entity = inventory.get("by_entity", {})
    by_entity = by_entity if isinstance(by_entity, dict) else {}

    views_by_id: dict[str, list[dict]] = {}
    for view in views:
        if isinstance(view, dict) and isinstance(view.get("view_id"), str):
            views_by_id.setdefault(view["view_id"], []).append(view)

    occurrences: dict[str, list[tuple[str, str, str]]] = {}
    unresolved_by_entity: Counter = Counter()
    unresolved_references = 0
    for entity_id in sorted(entities):
        references = by_entity.get(entity_id, [])
        if not isinstance(references, list):
            unresolved_references += 1
            unresolved_by_entity[entity_id] += 1
            occurrences[entity_id] = []
            continue
        valid: list[tuple[str, str, str]] = []
        seen: set[tuple[str, str, str]] = set()
        for reference in references:
            target = _resolve_occurrence(entity_id, reference, views_by_id)
            if target is None:
                unresolved_references += 1
                unresolved_by_entity[entity_id] += 1
                continue
            if target in seen:
                unresolved_references += 1
                unresolved_by_entity[entity_id] += 1
                continue
            seen.add(target)
            valid.append(target)
        occurrences[entity_id] = valid

    represented = sum(bool(items) for items in occurrences.values())
    anchors = [anchor for view in views for anchor in _mapping_values(view, "anchors")]
    dimensions = [dimension for view in views for dimension in _mapping_values(view, "dimensions")]
    anchor_states = Counter(_state(anchor.get("source_check")) for anchor in anchors)
    measurement_states = Counter(
        _state(dimension.get("measurement_check")) for dimension in dimensions
    )
    label_states = Counter(_state(dimension.get("label_check")) for dimension in dimensions)

    section = _render_panel(
        entities=entities,
        views=views,
        occurrences=occurrences,
        unresolved_by_entity=unresolved_by_entity,
        represented=represented,
        unresolved_references=unresolved_references,
        anchor_states=anchor_states,
        measurement_states=measurement_states,
        label_states=label_states,
        anchor_count=len(anchors),
        dimension_count=len(dimensions),
        unknown_inventory_entities=sorted(set(by_entity) - set(entities)),
    )
    style = """<style id="source-navigation-style">
#source-navigation { margin: 16px; }
#source-navigation table {
  width: 100%;
  border-collapse: collapse;
}
#source-navigation th, #source-navigation td {
  border: 1px solid #B9C0BD;
  padding: 6px 8px;
  text-align: left;
  vertical-align: top;
}
#source-navigation th { background: #EEF2F0; }
#source-navigation .navigation-entities { list-style: none; padding: 0; }
#source-navigation .navigation-entity { border-top: 1px solid #EEF2F0; padding: 8px 0; }
#source-navigation .navigation-entity button { font: inherit; color: inherit; cursor: pointer; }
#source-navigation .navigation-links { padding-left: 1.5rem; }
@media (max-width: 900px) {
  #source-navigation { overflow-x: auto; }
}
</style>"""
    script = """<script id="source-navigation-filter">
(() => {
  const panel = document.getElementById('source-navigation');
  if (!panel) return;
  const rows = [...panel.querySelectorAll('[data-navigation-entity]')];
  const list = document.getElementById('source-navigation-entities');
  const status = document.getElementById('source-navigation-status');
  document.addEventListener('click', (event) => {
    const button = event.target.closest('[data-select-entity]');
    if (!button) return;
    const entityId = button.dataset.selectEntity;
    let visible = 0;
    rows.forEach((row) => {
      const show = row.dataset.navigationEntity === entityId;
      row.hidden = !show;
      if (show) visible += 1;
    });
    if (list) list.open = true;
    if (status) status.textContent = visible
      ? 'Showing source occurrences for ' + entityId + '.'
      : 'No source occurrence is registered for ' + entityId + '.';
  });
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    rows.forEach((row) => { row.hidden = false; });
    if (status) status.textContent = 'Showing all enrolled entities.';
  });
})();
</script>"""

    if "</body>" in page:
        index = page.rfind("</body>")
        page = page[:index] + section + script + page[index:]
    else:
        page += section + script
    if "</head>" in page:
        index = page.rfind("</head>")
        page = page[:index] + style + page[index:]
    else:
        page = style + page
    return page


def _resolve_occurrence(
    entity_id: str, reference: object, views_by_id: dict[str, list[dict]]
) -> tuple[str, str, str] | None:
    if not isinstance(reference, dict):
        return None
    view_id = reference.get("view_id")
    view_file = reference.get("view")
    occurrence_id = reference.get("occurrence_id")
    if not all(isinstance(value, str) and value for value in (view_id, view_file, occurrence_id)):
        return None
    matching_views = views_by_id.get(view_id, [])
    if len(matching_views) != 1:
        return None
    view = matching_views[0]
    if view.get("file") != view_file or _safe_svg_path(view_file) is None:
        return None
    view_occurrences = view.get("occurrences", [])
    if not isinstance(view_occurrences, list) or not any(
        isinstance(item, dict)
        and item.get("entity_id") == entity_id
        and item.get("occurrence_id") == occurrence_id
        for item in view_occurrences
    ):
        return None
    return view_file, view_id, occurrence_id


def _safe_svg_path(value: str) -> str | None:
    """Return a URL path only for plain, relative SVG artifact paths."""
    if not isinstance(value, str) or not value or any(ord(char) < 32 for char in value):
        return None
    if "\\" in value or "%" in value or "?" in value or "#" in value:
        return None
    address = urlsplit(value)
    if address.scheme or address.netloc or address.path != value or value.startswith("/"):
        return None
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or path.suffix.lower() != ".svg":
        return None
    return quote(value, safe="/")


def _mapping_values(view: object, key: str) -> list[dict]:
    if not isinstance(view, dict):
        return []
    values = view.get(key, [])
    if isinstance(values, dict):
        return [value for value in values.values() if isinstance(value, dict)]
    if isinstance(values, list):
        return [value for value in values if isinstance(value, dict)]
    return []


def _state(check: object) -> str:
    if not isinstance(check, dict):
        return "unassessed"
    state = check.get("state")
    return state if isinstance(state, str) and state else "unassessed"


def _render_panel(
    *,
    entities: dict,
    views: list,
    occurrences: dict[str, list[tuple[str, str, str]]],
    unresolved_by_entity: Counter,
    represented: int,
    unresolved_references: int,
    anchor_states: Counter,
    measurement_states: Counter,
    label_states: Counter,
    anchor_count: int,
    dimension_count: int,
    unknown_inventory_entities: list[str],
) -> str:
    entity_count = len(entities)
    missing = entity_count - represented
    source_summary = _counter_summary(
        anchor_states,
        ("evaluated", "unbound", "unresolved", "unassessed"),
        {
            "evaluated": "source-bound",
            "unbound": "unbound",
            "unresolved": "unresolved",
            "unassessed": "unassessed",
        },
    )
    measurement_summary = _counter_summary(
        measurement_states,
        ("evaluated", "unsupported", "unassessed"),
        {
            "evaluated": "evaluated",
            "unsupported": "unsupported",
            "unassessed": "unassessed",
        },
    )
    label_summary = _counter_summary(
        label_states,
        ("evaluated", "unbound", "unassessed"),
        {"evaluated": "verified", "unbound": "unbound", "unassessed": "unassessed"},
    )

    entity_rows = []
    for entity_id in sorted(entities):
        entity = entities[entity_id]
        entity = entity if isinstance(entity, dict) else {}
        label = entity.get("label") or entity_id
        label_text = f"{label} · {entity_id}" if str(label) != entity_id else str(entity_id)
        targets = occurrences.get(entity_id, [])
        messages = []
        if targets:
            message = f"{len(targets)} linked occurrence{'s' if len(targets) != 1 else ''}."
        elif unresolved_by_entity.get(entity_id):
            message = (
                f"{unresolved_by_entity[entity_id]} listed occurrence reference(s) "
                "could not be resolved."
            )
        else:
            message = "No SVG occurrence is registered in the view inventory."
        if not targets:
            messages.append(f'<p class="navigation-gap">{message}</p>')
        elif unresolved_by_entity.get(entity_id):
            messages.append(
                '<p class="navigation-gap">'
                f"{unresolved_by_entity[entity_id]} additional occurrence reference(s) "
                "could not be resolved.</p>"
            )
        target_links = []
        for path, view_id, occurrence_id in targets:
            safe_path = _safe_svg_path(path)
            if safe_path is None:
                continue
            target_links.append(
                "<li>"
                f"{html.escape(_human_name(view_id))} · "
                f'<a href="{html.escape(safe_path, quote=True)}#{quote(occurrence_id, safe="")}">'
                f"{html.escape(path)} · occurrence {html.escape(occurrence_id)}</a>"
                "</li>"
            )
        if target_links:
            messages.append(f'<ul class="navigation-links">{"".join(target_links)}</ul>')
        entity_rows.append(
            f'<li class="navigation-entity" data-navigation-entity="{html.escape(entity_id, quote=True)}">'
            f'<button type="button" data-select-entity="{html.escape(entity_id, quote=True)}" aria-pressed="false">'
            f"{html.escape(label_text)}</button>{''.join(messages)}</li>"
        )

    sheet_rows = []
    for view in views:
        if not isinstance(view, dict):
            continue
        view_id = str(view.get("view_id", "Unknown sheet"))
        path = view.get("file")
        path = path if isinstance(path, str) else ""
        safe_path = _safe_svg_path(path)
        occurrence_count = len(_mapping_values(view, "occurrences"))
        view_anchors = _mapping_values(view, "anchors")
        view_dimensions = _mapping_values(view, "dimensions")
        per_anchor = Counter(_state(anchor.get("source_check")) for anchor in view_anchors)
        per_measurement = Counter(
            _state(dimension.get("measurement_check")) for dimension in view_dimensions
        )
        per_label = Counter(_state(dimension.get("label_check")) for dimension in view_dimensions)
        anchor_summary = _counter_summary(
            per_anchor,
            ("evaluated", "unbound", "unresolved", "unassessed"),
            {
                "evaluated": "source-bound",
                "unbound": "unbound",
                "unresolved": "unresolved",
                "unassessed": "unassessed",
            },
        )
        measurement_summary = _counter_summary(
            per_measurement,
            ("evaluated", "unsupported", "unassessed"),
            {
                "evaluated": "evaluated",
                "unsupported": "unsupported",
                "unassessed": "unassessed",
            },
        )
        label_summary = _counter_summary(
            per_label,
            ("evaluated", "unbound", "unassessed"),
            {"evaluated": "verified", "unbound": "unbound", "unassessed": "unassessed"},
        )
        gaps = []
        if not view_anchors:
            gaps.append("no named anchors declared")
        elif any(state != "evaluated" for state in per_anchor):
            gaps.append("anchor source checks remain open")
        if not view_dimensions:
            gaps.append("no named dimensions declared")
        else:
            if any(state != "evaluated" for state in per_measurement):
                gaps.append("measurement checks remain unsupported or unassessed")
            if any(state != "evaluated" for state in per_label):
                gaps.append("dimension labels remain unverified")
        if safe_path:
            sheet = (
                f'<a href="{html.escape(safe_path, quote=True)}">'
                f"{html.escape(_human_name(view_id))}</a>"
            )
        else:
            sheet = html.escape(_human_name(view_id)) + " · unsafe or missing SVG path"
            gaps.append("sheet path cannot be linked")
        sheet_rows.append(
            "<tr>"
            f'<th scope="row">{sheet}<br><small>{html.escape(path)}</small></th>'
            f"<td>{occurrence_count}</td>"
            f"<td>{len(view_anchors)}<br><small>{anchor_summary}</small></td>"
            f"<td>{len(view_dimensions)}<br><small>measurements: {measurement_summary}<br>"
            f"labels: {label_summary}</small></td>"
            "<td>"
            f"{html.escape('; '.join(gaps) if gaps else 'No open declared annotation check.')}</td>"
            "</tr>"
        )

    inventory_warning = ""
    if unknown_inventory_entities:
        listed = ", ".join(
            html.escape(str(identifier)) for identifier in unknown_inventory_entities
        )
        inventory_warning = (
            '<p class="navigation-gap">Inventory references unknown snapshot entity IDs: '
            f"{listed}.</p>"
        )
    unresolved_note = (
        f" {unresolved_references} listed occurrence reference(s) could not be resolved and are omitted."
        if unresolved_references
        else ""
    )
    sheets = (
        "".join(sheet_rows)
        if sheet_rows
        else '<tr><td colspan="5">No SVG sheets are present in the view inventory.</td></tr>'
    )
    return (
        '<section id="source-navigation" class="panel" aria-labelledby="source-navigation-title">'
        '<h2 id="source-navigation-title">Source-sheet occurrence navigation</h2>'
        f"<p>{len(views)} SVG sheet(s) indexed. {represented} of {entity_count} snapshot entities have at least one resolved occurrence link; "
        f"{missing} {'entity has' if missing == 1 else 'entities have'} no resolved link.{unresolved_note}</p>"
        f"<p>Declared annotation coverage: {anchor_count} named anchor(s), source checks: {source_summary}; "
        f"{dimension_count} named dimension(s), measurement checks: {measurement_summary}; dimension label checks: {label_summary}. "
        "These checks cover declared SVG annotations only; they do not establish complete drawing coverage or engineering approval.</p>"
        f"{inventory_warning}"
        "<details><summary>Per-sheet anchor, dimension and check coverage</summary>"
        '<div class="navigation-table-wrap"><table><caption>Coverage declared in the SVG view inventory</caption>'
        '<thead><tr><th scope="col">SVG sheet</th><th scope="col">Entity occurrences</th>'
        '<th scope="col">Named anchors / source checks</th><th scope="col">Named dimensions / checks</th>'
        '<th scope="col">Remaining declared gaps</th></tr></thead>'
        f"<tbody>{sheets}</tbody></table></div></details>"
        '<details id="source-navigation-entities"><summary>Find an entity in its source sheets</summary>'
        '<p id="source-navigation-status" aria-live="polite">Showing all enrolled entities. Select an entity in the review index to filter this list.</p>'
        f'<ul class="navigation-entities">{"".join(entity_rows)}</ul>'
        "</details></section>"
    )


def _counter_summary(counter: Counter, states: tuple[str, ...], labels: dict[str, str]) -> str:
    parts = [f"{html.escape(labels[state])} {counter.get(state, 0)}" for state in states]
    other = sorted(set(counter) - set(states))
    parts.extend(f"other state {html.escape(state)} {counter[state]}" for state in other)
    return " · ".join(parts)


def _human_name(view_id: str) -> str:
    return " ".join(part.capitalize() for part in view_id.replace("_", "-").split("-") if part)

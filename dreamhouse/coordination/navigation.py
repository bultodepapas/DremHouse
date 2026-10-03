"""Add a human-readable, source-linked index to a coordination review page."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import PurePosixPath
from urllib.parse import quote, urlencode, urlsplit


def attach_navigation(
    page: str, snapshot: dict, inventory: dict, viewpoints: dict | None = None
) -> str:
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
    page_ids = _PageIds()
    page_ids.feed(page)
    if viewpoints is not None:
        issue_panel = _render_saved_issues(viewpoints, snapshot, page_ids.ids)
        section = section.replace("</section>", issue_panel + "</section>", 1)
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
#source-navigation .saved-issue { border-top: 1px solid #CBD0CC; padding: 10px 0; }
#source-navigation .saved-issue[aria-current="location"] { outline: 2px solid #2454A6; outline-offset: 2px; }
#source-navigation .saved-issue-view[aria-current="location"] { font-weight: 700; }
#source-navigation .saved-issue-selected { outline: 2px solid #2454A6; }
#source-navigation .saved-issue-viewpoints, #source-navigation .saved-issue-gaps ul { padding-left: 1.5rem; }
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
    if viewpoints is not None:
        script += _saved_issue_script()

    page = _add_header_navigation_link(page)

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


class _PageIds(HTMLParser):
    """Collect actual IDs from the generated index before offering an anchor link."""

    def __init__(self):
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        identifier = dict(attrs).get("id")
        if isinstance(identifier, str):
            self.ids.add(identifier)


def _add_header_navigation_link(page: str) -> str:
    if 'data-source-navigation-link="true"' in page:
        return page
    match = re.search(r"<nav\b[^>]*>", page, flags=re.IGNORECASE)
    if match is None:
        return page
    close = re.search(r"</nav\s*>", page[match.end() :], flags=re.IGNORECASE)
    if close is None:
        return page
    end = match.end() + close.start()
    link = (
        '<a data-source-navigation-link="true" href="#source-navigation">'
        "Source navigation</a>"
    )
    return page[:end] + link + page[end:]


def _render_saved_issues(viewpoints: dict, snapshot: dict, page_ids: set[str]) -> str:
    package = viewpoints.get("snapshot_ref", {})
    package = package if isinstance(package, dict) else {}
    expected = {
        "scenario_id": snapshot.get("scenario_id"),
        "input_hash": snapshot.get("input_hash"),
        "model_hash": snapshot.get("model_hash"),
    }
    package_matches = all(
        isinstance(value, str) and value and package.get(key) == value
        for key, value in expected.items()
    )
    issues = viewpoints.get("issues", [])
    issues = issues if isinstance(issues, list) else []
    rows = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        issue_id = issue.get("issue_id")
        finding_id = issue.get("finding_id")
        if not isinstance(issue_id, str) or not isinstance(finding_id, str):
            continue
        summary = issue.get("summary", {})
        summary = summary if isinstance(summary, dict) else {}
        finding_ref = issue.get("finding_ref", {})
        finding_ref = finding_ref if isinstance(finding_ref, dict) else {}
        finding_state = finding_ref.get("state", "unavailable")
        entity_refs = issue.get("entity_refs", [])
        entity_refs = entity_refs if isinstance(entity_refs, list) else []
        entity_ids = [
            item["entity_id"]
            for item in entity_refs
            if isinstance(item, dict)
            and item.get("state") == "available"
            and isinstance(item.get("entity_id"), str)
        ]
        viewpoints_for_issue = issue.get("viewpoints", [])
        viewpoints_for_issue = (
            viewpoints_for_issue if isinstance(viewpoints_for_issue, list) else []
        )
        links = []
        for viewpoint in viewpoints_for_issue:
            if not isinstance(viewpoint, dict) or viewpoint.get("state") != "available":
                continue
            view_id = viewpoint.get("view_id")
            view_file = viewpoint.get("view_file")
            if not isinstance(view_id, str) or not isinstance(view_file, str):
                continue
            definition_ref = viewpoint.get("view_definition_ref", {})
            definition_ref = definition_ref if isinstance(definition_ref, dict) else {}
            if (
                definition_ref.get("view_id") != view_id
                or definition_ref.get("view_file") != view_file
                or not isinstance(definition_ref.get("definition_hash"), str)
                or not isinstance(definition_ref.get("definition"), dict)
            ):
                continue
            selected = viewpoint.get("selected_occurrences", [])
            selected = selected if isinstance(selected, list) else []
            valid_selected = [
                item
                for item in selected
                if isinstance(item, dict)
                and isinstance(item.get("entity_id"), str)
                and isinstance(item.get("occurrence_id"), str)
            ]
            basename = view_file.rsplit("/", 1)[-1]
            section_id = f"section-{basename[:-4]}" if basename.lower().endswith(".svg") else ""
            embedded = section_id in page_ids
            if not package_matches or finding_state != "available":
                continue
            if embedded:
                params = urlencode(
                    {
                        "scenario_id": expected["scenario_id"],
                        "input_hash": expected["input_hash"],
                        "model_hash": expected["model_hash"],
                        "issue_id": issue_id,
                        "finding_id": finding_id,
                        "view_id": view_id,
                    },
                    quote_via=quote,
                )
                href = f"?{params}#{quote(section_id, safe='-_')}"
                view_label = f"Open {view_id} in this review"
                link = (
                    f'<a class="saved-issue-view" data-saved-viewpoint="true" '
                    f'data-view-id="{html.escape(view_id, quote=True)}" '
                    f'data-view-file="{html.escape(view_file, quote=True)}" '
                    f'data-section-id="{html.escape(section_id, quote=True)}" '
                    f'href="{html.escape(href, quote=True)}">{html.escape(view_label)}</a>'
                )
            else:
                safe_file = _safe_svg_path(view_file)
                occurrence_link = None
                if safe_file and valid_selected:
                    first_occurrence = valid_selected[0].get("occurrence_id")
                    occurrence_link = (
                        f'{html.escape(safe_file, quote=True)}#'
                        f'{quote(first_occurrence, safe="")}'
                    )
                if occurrence_link is None:
                    continue
                link = (
                    f'<a class="saved-issue-view" data-saved-viewpoint="true" '
                    f'data-view-id="{html.escape(view_id, quote=True)}" '
                    'data-section-id="" '
                    f'href="{occurrence_link}">Open {html.escape(view_id)} source SVG occurrence</a>'
                )
            count = len(valid_selected)
            links.append(
                '<li>'
                f'{link} <small>· {count} linked occurrence(s) · '
                f'{html.escape(view_file)}</small>'
                "</li>"
            )

        unavailable = issue.get("unavailable_references", [])
        unavailable = unavailable if isinstance(unavailable, list) else []
        reference_gaps = []
        for reference in unavailable:
            if not isinstance(reference, dict):
                continue
            kind = reference.get("kind", "reference")
            identifier = (
                reference.get("entity_id")
                or reference.get("view_id")
                or reference.get("finding_id")
                or reference.get("occurrence_id")
                or "unknown"
            )
            reason = reference.get("reason", "reference is unavailable")
            reference_gaps.append(
                f"<li>{html.escape(str(kind))} {html.escape(str(identifier))}: "
                f"{html.escape(str(reason))}</li>"
            )
        if not package_matches:
            reference_gaps.append(
                "<li>Viewpoint package identity does not match the rendered review.</li>"
            )
        if not links and not reference_gaps:
            reference_gaps.append("<li>No view destination is available for this finding.</li>")

        entity_buttons = " ".join(
            '<button type="button" class="saved-issue-entity" '
            f'data-select-entity="{html.escape(entity_id, quote=True)}">'
            f"{html.escape(entity_id)}</button>"
            for entity_id in entity_ids
        ) or "No linked snapshot entities."
        state_reasons = finding_ref.get("reasons", [])
        state_reasons = state_reasons if isinstance(state_reasons, list) else []
        reason_text = ""
        if finding_state != "available":
            reason_text = " · ".join(str(item) for item in state_reasons) or "finding reference is unavailable"
        reason_markup = (
            f'<p class="navigation-gap">{html.escape(reason_text)}</p>' if reason_text else ""
        )
        gaps_markup = ""
        if reference_gaps:
            gaps_markup = (
                '<details class="saved-issue-gaps">'
                f"<summary>Unavailable references ({len(reference_gaps)})</summary>"
                f'<ul>{"".join(reference_gaps)}</ul></details>'
            )
        rows.append(
            f'<li class="saved-issue" id="saved-issue-{html.escape(issue_id, quote=True)}" '
            f'data-saved-issue="{html.escape(issue_id, quote=True)}" '
            f'data-finding-id="{html.escape(finding_id, quote=True)}" '
            f'data-finding-state="{html.escape(str(finding_state), quote=True)}" '
            f'data-rule-id="{html.escape(str(summary.get("rule_id") or ""), quote=True)}" '
            f'data-finding-status="{html.escape(str(summary.get("status") or ""), quote=True)}" '
            f'data-finding-message="{html.escape(str(summary.get("message") or ""), quote=True)}" '
            f'data-entity-ids="{html.escape(json.dumps(entity_ids, ensure_ascii=False), quote=True)}">'
            f'<strong>{html.escape(str(summary.get("status") or "UNKNOWN"))} · '
            f'{html.escape(str(summary.get("rule_id") or "Finding"))}</strong> '
            f'<small>Finding {html.escape(finding_id)}</small>'
            f'<p>{html.escape(str(summary.get("message") or "No finding message supplied."))}</p>'
            f'<p>Linked elements: {entity_buttons}</p>'
            f"{reason_markup}"
            f'<ul class="saved-issue-viewpoints">{"".join(links)}</ul>'
            f"{gaps_markup}"
            "</li>"
        )
    if not rows:
        rows.append('<li class="navigation-gap">No saved issue viewpoints are available.</li>')
    package_note = "" if package_matches else (
        '<p class="navigation-gap">Saved issue records identify a different scenario or '
        "input package; no viewpoint links are enabled.</p>"
    )
    return (
        '<section id="saved-issues" aria-labelledby="saved-issues-title" '
        f'data-package-scenario="{html.escape(str(expected["scenario_id"] or ""), quote=True)}" '
        f'data-package-input="{html.escape(str(expected["input_hash"] or ""), quote=True)}" '
        f'data-package-model="{html.escape(str(expected["model_hash"] or ""), quote=True)}">'
        '<h2 id="saved-issues-title">Saved issue viewpoints</h2>'
        '<p id="saved-issue-navigation-status" aria-live="polite">'
        f'{len(issues)} finding-linked issue record(s). Each destination retains its '
        "original scenario, input identity and view definition.</p>"
        f"{package_note}<ul class=\"saved-issue-list\">{''.join(rows)}</ul></section>"
    )


def _saved_issue_script() -> str:
    return """<script id="saved-issue-navigation">
(() => {
  const panel = document.getElementById('saved-issues');
  if (!panel) return;
  let savedIssueActive = false;
  let savedSelectedNodes = [];
  let selectedIssue = null;
  let selectedViewLink = null;
  const params = new URLSearchParams(window.location.search);
  const issueId = params.get('issue_id');
  const findingId = params.get('finding_id');
  const viewId = params.get('view_id');
  if (!issueId && !findingId && !viewId) return;
  const status = document.getElementById('saved-issue-navigation-status');
  const expected = {
    scenario_id: panel.dataset.packageScenario,
    input_hash: panel.dataset.packageInput,
    model_hash: panel.dataset.packageModel,
  };
  const supplied = {
    scenario_id: params.get('scenario_id'),
    input_hash: params.get('input_hash'),
    model_hash: params.get('model_hash'),
  };
  if (Object.keys(expected).some((key) => !expected[key] || supplied[key] !== expected[key])) {
    if (status) status.textContent = 'Saved issue belongs to a different scenario or input package. No finding, element, or view was selected.';
    return;
  }
  const issue = [...panel.querySelectorAll('[data-saved-issue]')].find((row) =>
    row.dataset.savedIssue === issueId && row.dataset.findingId === findingId
  );
  if (!issue) {
    if (status) status.textContent = 'Saved finding or issue reference is unavailable in this package.';
    return;
  }
  issue.setAttribute('aria-current', 'location');
  if (issue.dataset.findingState !== 'available') {
    if (status) status.textContent = 'Saved finding ' + findingId + ' is unavailable: ' + issue.textContent.trim();
    return;
  }
  savedIssueActive = true;
  selectedIssue = issue;
  const findingRows = [...document.querySelectorAll('.finding')];
  let linkedIds = [];
  try { linkedIds = JSON.parse(issue.dataset.entityIds || '[]'); } catch (_) { linkedIds = []; }
  const selected = new Set(linkedIds);
  document.querySelectorAll('.is-selected').forEach((node) => node.classList.remove('is-selected'));
  document.querySelectorAll('[data-entity-id], [data-anchor-entity-id], [data-dimension-for]').forEach((node) => {
    const entityId = node.dataset.entityId || node.dataset.anchorEntityId || node.dataset.dimensionFor;
    if (selected.has(entityId)) {
      node.classList.add('is-selected');
      savedSelectedNodes.push(node);
    }
  });
  document.querySelectorAll('[data-select-entity]').forEach((button) => {
    button.setAttribute('aria-pressed', selected.has(button.dataset.selectEntity) ? 'true' : 'false');
  });
  const matchingFindings = findingRows.filter((row) => row.dataset.savedFindingId === findingId);
  findingRows.forEach((row) => {
    row.hidden = matchingFindings.length > 0 && !matchingFindings.includes(row);
    row.classList.toggle('saved-issue-selected', matchingFindings.includes(row));
  });
  const viewpoints = [...issue.querySelectorAll('[data-saved-viewpoint]')];
  const selectedView = viewpoints.find((link) => link.dataset.viewId === viewId);
  if (status) {
    status.textContent = 'Opened saved finding ' + findingId + ' for scenario ' + expected.scenario_id
      + ' with ' + selected.size + ' linked element(s).';
    if (matchingFindings.length === 0) {
      status.textContent += ' The finding row is unavailable in this index.';
    }
  }
  if (viewId && !selectedView) {
    if (status) status.textContent += ' View ' + viewId + ' is unavailable for this saved issue.';
  }
  if (selectedView) {
    selectedViewLink = selectedView;
    selectedView.setAttribute('aria-current', 'location');
    if (!selectedView.dataset.sectionId && status) {
      status.textContent += ' The recorded source SVG exists, but this index has no embedded section for it.';
    }
  }
  document.addEventListener('click', (event) => {
    const entityButton = event.target.closest('[data-select-entity]');
    if (!entityButton || !savedIssueActive) return;
    savedIssueActive = false;
    findingRows.forEach((row) => row.classList.remove('saved-issue-selected'));
    selectedIssue?.removeAttribute('aria-current');
    selectedViewLink?.removeAttribute('aria-current');
  });
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape' || !savedIssueActive) return;
    savedIssueActive = false;
    savedSelectedNodes.forEach((node) => node.classList.remove('is-selected'));
    document.querySelectorAll('[data-select-entity]').forEach((button) => {
      button.setAttribute('aria-pressed', 'false');
    });
    findingRows.forEach((row) => {
      row.hidden = false;
      row.classList.remove('saved-issue-selected');
    });
    selectedIssue?.removeAttribute('aria-current');
    selectedViewLink?.removeAttribute('aria-current');
    const selectionStatus = document.getElementById('selection-status');
    const selectedEvidence = document.getElementById('selected-evidence');
    const findingFilterStatus = document.getElementById('finding-filter-status');
    if (selectionStatus) selectionStatus.textContent = 'No element selected.';
    if (selectedEvidence) selectedEvidence.textContent = 'Element source and status will appear here.';
    if (findingFilterStatus) findingFilterStatus.textContent = 'Showing all ' + findingRows.length + ' findings.';
    if (status) status.textContent = 'Saved issue selection cleared.';
  });
})();
</script>"""


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

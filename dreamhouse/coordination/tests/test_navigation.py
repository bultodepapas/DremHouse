"""The review index links only inventoried SVG occurrences and reports annotation gaps."""

from __future__ import annotations

import unittest
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree as ET

from dreamhouse.coordination.navigation import attach_navigation
from dreamhouse.coordination.view_contract import inspect_views
from dreamhouse.coordination.viewpoints import build_viewpoints

SVG = "http://www.w3.org/2000/svg"


class _Markup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.links = []
        self.buttons = []
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        self.tags.append(tag)
        self.attributes.append(values)
        if tag == "a":
            self.links.append(values)
        if tag == "button":
            self.buttons.append(values)


def _fixture_inventory():
    entity_id = 'ENTITY / "north" &?#'
    entities = {
        entity_id: {"label": '<img src=x onerror="alert(1)">'},
        "SECOND": {"label": "Second element"},
        "UNLOCATED": {"label": "Unrepresented element"},
    }
    snapshot = {
        "scenario_id": "NAVIGATION-TEST",
        "input_hash": "test",
        "entities": entities,
    }
    files = {}
    for index in range(35):
        path = f"drawings/sheet {index:02}.svg"
        root = ET.Element(f"{{{SVG}}}svg", {"data-view-id": f"sheet-{index:02}"})
        occurrence_id = f'occurrence {index:02} / #?&"'
        ET.SubElement(
            root,
            f"{{{SVG}}}g",
            {"id": occurrence_id, "data-entity-id": entity_id},
        )
        if index == 1:
            ET.SubElement(
                root,
                f"{{{SVG}}}g",
                {"id": "second-occurrence", "data-entity-id": "SECOND"},
            )
        if index == 0:
            ET.SubElement(
                root,
                f"{{{SVG}}}circle",
                {
                    "id": "anchor-left",
                    "data-entity-id": entity_id,
                    "data-anchor-id": "left",
                    "data-world-x": "0",
                },
            )
            ET.SubElement(
                root,
                f"{{{SVG}}}circle",
                {
                    "id": "anchor-right",
                    "data-entity-id": entity_id,
                    "data-anchor-id": "right",
                    "data-world-x": "1",
                },
            )
            ET.SubElement(
                root,
                f"{{{SVG}}}text",
                {
                    "id": "dimension",
                    "data-dimension-id": "length",
                    "data-anchor-refs": "left right",
                    "data-anchor-targets": "anchor-left anchor-right",
                    "data-dimension-value": "1",
                    "data-dimension-unit": "m",
                    "data-dimension-label-format": "fixed-2-m",
                },
            ).text = "1.00 m"
        files[path] = ET.tostring(root, encoding="unicode")
    return snapshot, files, entity_id


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, self.files, self.entity_id = _fixture_inventory()
        self.inventory = inspect_views(self.snapshot, self.files)

    def test_real_inspected_35_sheet_inventory_drives_occurrence_links_and_coverage(self):
        self.assertEqual(len(self.inventory["views"]), 35)
        self.assertEqual(self.inventory["represented_entity_count"], 2)
        self.assertEqual(self.inventory["entities_without_svg_occurrences"], ["UNLOCATED"])

        page = attach_navigation(
            "<!doctype html><html><head></head><body></body></html>", self.snapshot, self.inventory
        )
        markup = _Markup()
        markup.feed(page)

        occurrence_links = [link for link in markup.links if "#occurrence" in link.get("href", "")]
        self.assertEqual(len(occurrence_links), 35)
        self.assertIn(
            "drawings/sheet%2000.svg#occurrence%2000%20%2F%20%23%3F%26%22",
            {link["href"] for link in occurrence_links},
        )
        self.assertTrue(
            any(
                link.get("href") == "drawings/sheet%2001.svg#second-occurrence"
                for link in markup.links
            )
        )
        self.assertNotIn("img", markup.tags)
        self.assertIn("No SVG occurrence is registered in the view inventory.", page)
        self.assertIn("35 SVG sheet(s) indexed", page)
        self.assertIn("Named anchors / source checks", page)
        self.assertIn("measurements: evaluated 1", page)
        self.assertIn("labels: verified 1", page)
        self.assertIn("no named anchors declared", page)
        self.assertIn("no named dimensions declared", page)
        self.assertIn("engineering approval", page)

    def test_missing_references_and_unsafe_paths_are_explicit_and_never_linked(self):
        inventory = self.inventory
        first = inventory["views"][0]
        original_path = first["file"]
        first["file"] = "../../outside.svg"
        reference = inventory["by_entity"][self.entity_id][0]
        reference["view"] = "../../outside.svg"

        page = attach_navigation(
            "<html><head></head><body></body></html>", self.snapshot, inventory
        )
        markup = _Markup()
        markup.feed(page)

        self.assertNotIn("../../outside.svg#", page)
        self.assertIn("listed occurrence reference(s) could not be resolved", page)
        self.assertIn("unsafe or missing SVG path", page)
        self.assertNotIn(original_path + "#", page)

    def test_unresolvable_view_reference_is_not_emitted_as_a_fragment(self):
        inventory = self.inventory
        inventory["by_entity"][self.entity_id][0]["view_id"] = "missing-sheet"
        page = attach_navigation(
            "<html><head></head><body></body></html>", self.snapshot, inventory
        )
        self.assertIn("1 listed occurrence reference(s) could not be resolved", page)
        self.assertNotIn("#occurrence%2000", page)

    def test_existing_entity_selection_buttons_filter_the_panel_by_delegated_click(self):
        source_page = '<html><head></head><body><button data-select-entity="SECOND">Second</button></body></html>'
        page = attach_navigation(source_page, self.snapshot, self.inventory)

        self.assertIn("document.addEventListener('click'", page)
        self.assertIn("event.target.closest('[data-select-entity]')", page)
        self.assertIn("row.dataset.navigationEntity === entityId", page)
        self.assertIn('type="button" data-select-entity="SECOND" aria-pressed="false"', page)
        self.assertIn('aria-live="polite"', page)
        self.assertNotIn("<script src=", page)

    def test_saved_issue_link_carries_package_identity_and_selects_real_view(self):
        snapshot = {
            "scenario_id": "ISSUE-SCENARIO",
            "input_hash": "input-hash-1",
            "model_hash": "model-hash-1",
            "entities": {"E-1": {"id": "E-1", "label": "Wall"}},
        }
        evaluation = {
            "findings": [
                {
                    "finding_id": "RULE:E-1",
                    "rule_id": "RULE",
                    "status": "OPEN",
                    "coverage": "evaluated",
                    "severity": "warning",
                    "message": "Review this wall.",
                    "entity_ids": ["E-1"],
                    "scenario_id": "ISSUE-SCENARIO",
                    "input_hash": "input-hash-1",
                    "model_hash": "model-hash-1",
                }
            ]
        }
        inventory = {
            "schema_version": 4,
            "scenario_id": "ISSUE-SCENARIO",
            "input_hash": "input-hash-1",
            "views": [
                {
                    "view_id": "plan-pb",
                    "file": "plan-pb.svg",
                    "definition": {
                        "purpose": "plan",
                        "basis": "PB",
                        "view_box": [0, 0, 10, 10],
                        "projected_axes": ["X", "Y"],
                        "cut_plane": {"state": "known", "z_m": 1.2},
                        "depth_range": {"state": "known", "near_m": 0, "far_m": 1},
                        "transform": {"scale": 20},
                        "unknowns": [],
                    },
                    "occurrences": [{"entity_id": "E-1", "occurrence_id": "occ-1"}],
                }
            ],
            "by_entity": {
                "E-1": [
                    {"view": "plan-pb.svg", "view_id": "plan-pb", "occurrence_id": "occ-1"}
                ]
            },
        }
        saved = build_viewpoints(snapshot, evaluation, inventory)
        page = attach_navigation(
            '<html><head></head><body><header><nav aria-label="Views"></nav></header>'
            '<ul><li class="finding" data-saved-finding-id="OTHER:FINDING">'
            "<strong>PASS · OTHER</strong><p>Another finding.</p></li>"
            '<li class="finding" data-saved-finding-id="RULE:E-1">'
            "<strong>OPEN · RULE</strong><p>Review this wall.</p></li></ul>"
            '<section class="view" id="section-plan-pb"></section></body></html>',
            snapshot,
            inventory,
            viewpoints=saved,
        )
        markup = _Markup()
        markup.feed(page)

        self.assertTrue(
            any(
                link.get("data-source-navigation-link") == "true"
                and link.get("href") == "#source-navigation"
                for link in markup.links
            )
        )
        saved_link = next(link for link in markup.links if link.get("data-saved-viewpoint") == "true")
        self.assertIn("#section-plan-pb", saved_link["href"])
        self.assertIn("scenario_id=ISSUE-SCENARIO", saved_link["href"])
        self.assertIn("input_hash=input-hash-1", saved_link["href"])
        self.assertIn("model_hash=model-hash-1", saved_link["href"])
        self.assertIn("finding_id=RULE%3AE-1", saved_link["href"])
        self.assertEqual(
            parse_qs(urlsplit(saved_link["href"]).query)["finding_id"], ["RULE:E-1"]
        )
        self.assertIn("belongs to a different scenario or input package", page)
        self.assertIn("row.dataset.savedFindingId === findingId", page)
        self.assertNotIn("issueRows[index]", page)

    def test_viewpoint_records_for_another_scenario_are_reported_without_links(self):
        snapshot = {
            "scenario_id": "ISSUE-SCENARIO",
            "input_hash": "input-hash-1",
            "model_hash": "model-hash-1",
            "entities": {"E-1": {"id": "E-1", "label": "Wall"}},
        }
        evaluation = {
            "findings": [
                {
                    "finding_id": "RULE:E-1",
                    "rule_id": "RULE",
                    "status": "OPEN",
                    "coverage": "evaluated",
                    "severity": "warning",
                    "message": "Review this wall.",
                    "entity_ids": ["E-1"],
                    "scenario_id": "ISSUE-SCENARIO",
                    "input_hash": "input-hash-1",
                    "model_hash": "model-hash-1",
                }
            ]
        }
        inventory = {
            "scenario_id": "ISSUE-SCENARIO",
            "input_hash": "input-hash-1",
            "views": [
                {
                    "view_id": "plan-pb",
                    "file": "plan-pb.svg",
                    "definition": {"purpose": "plan"},
                    "occurrences": [{"entity_id": "E-1", "occurrence_id": "occ-1"}],
                }
            ],
            "by_entity": {
                "E-1": [
                    {"view": "plan-pb.svg", "view_id": "plan-pb", "occurrence_id": "occ-1"}
                ]
            },
        }
        saved = build_viewpoints(snapshot, evaluation, inventory)
        rendered_snapshot = {**snapshot, "scenario_id": "OTHER-SCENARIO"}
        page = attach_navigation(
            '<html><head></head><body><nav></nav><section id="section-plan-pb"></section></body></html>',
            rendered_snapshot,
            inventory,
            viewpoints=saved,
        )

        self.assertNotIn('class="saved-issue-view"', page)
        self.assertIn("different scenario or input package", page)
        self.assertIn('data-package-scenario="OTHER-SCENARIO"', page)


if __name__ == "__main__":
    unittest.main()

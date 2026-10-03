"""The review index links only inventoried SVG occurrences and reports annotation gaps."""

from __future__ import annotations

import unittest
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

from dreamhouse.coordination.navigation import attach_navigation
from dreamhouse.coordination.view_contract import inspect_views

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


if __name__ == "__main__":
    unittest.main()

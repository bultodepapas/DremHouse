from __future__ import annotations

import unittest
from copy import deepcopy
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

from dreamhouse.coordination.render import SVG_NS, render_views
from dreamhouse.coordination.view_contract import compare_anchors, inspect_views


def _opening(entity_id: str = "GLZ-A") -> dict:
    return {
        "id": entity_id,
        "kind": "opening",
        "label": "Side A test opening",
        "level": "PB",
        "aliases": [],
        "status": "active",
        "source": {"path": "dreamhouse/test.json", "key": "openings[0]"},
        "geometry": {
            "shape": "opening",
            "x0": 2.0,
            "x1": 3.2,
            "y0": 0.0,
            "y1": 0.15,
            "z0": None,
            "z1": None,
        },
        "parameters": {
            "facade": "A",
            "start_m": 2.0,
            "width_m": 1.2,
            "height_m": 1.0,
            "sill_m": 0.75,
            "level_m": 0.0,
        },
        "relationships": {"host_id": "HOST-PB-A", "space_ids": []},
    }


def _facade_opening(
    entity_id: str,
    facade: str,
    horizontal: tuple[float, float],
    vertical: tuple[float, float],
    *,
    sill: float,
    level: float,
) -> dict:
    entity = _opening(entity_id)
    if facade in {"A", "B"}:
        fixed = 18.0 if facade == "B" else 0.0
        entity["geometry"].update(
            {"x0": horizontal[0], "x1": horizontal[1], "y0": fixed, "y1": fixed}
        )
    else:
        fixed = 36.0 if facade == "REAR" else 0.0
        entity["geometry"].update(
            {"x0": fixed, "x1": fixed, "y0": horizontal[0], "y1": horizontal[1]}
        )
    entity["geometry"].update({"z0": vertical[0], "z1": vertical[1]})
    entity["parameters"].update(
        {"facade": facade, "sill_m": sill, "level_m": level, "height_m": vertical[1] - vertical[0]}
    )
    return entity


def _snapshot() -> dict:
    unknown_z = {
        "id": "WALL-UNKNOWN-Z",
        "kind": "wall",
        "label": "Unresolved elevation extent",
        "level": "PB",
        "aliases": [],
        "status": "context",
        "source": {"path": "dreamhouse/test.json", "key": "walls[0]"},
        "geometry": {
            "shape": "rect",
            "x0": 8.0,
            "x1": 10.0,
            "y0": 0.0,
            "y1": 0.2,
            "z0": None,
            "z1": None,
        },
        "parameters": {"facade": "A"},
        "relationships": {"host_id": None, "space_ids": []},
    }
    unresolved = {
        "id": "DOOR-UNRESOLVED",
        "kind": "door",
        "label": "Source anchor unresolved",
        "level": "PB",
        "aliases": [],
        "status": "context",
        "source": {"path": "dreamhouse/test.json", "key": "doors[0]"},
        "geometry": {
            "shape": "unresolved",
            "x0": None,
            "x1": None,
            "y0": None,
            "y1": None,
            "z0": None,
            "z1": None,
        },
        "parameters": {"width_m": 0.9, "reason": "anchor unresolved"},
        "relationships": {"host_id": None, "space_ids": []},
    }
    rooflight = {
        "id": "RL-01",
        "kind": "opening",
        "label": "Rooflight context",
        "level": "PROJECT",
        "aliases": [],
        "status": "active",
        "source": {"path": "dreamhouse/roof.json", "key": "rooflights[0]"},
        "geometry": {
            "shape": "rect",
            "x0": 12.0,
            "x1": 14.0,
            "y0": 5.0,
            "y1": 7.0,
            "z0": None,
            "z1": None,
        },
        "parameters": {"facade": "ROOF"},
        "relationships": {"host_id": None, "space_ids": []},
    }
    p2_space = {
        "id": "P2-SPACE",
        "kind": "space",
        "label": "P2 review space",
        "level": "P2",
        "aliases": [],
        "status": "active",
        "source": {"path": "dreamhouse/test.json", "key": "p2_spaces[0]"},
        "geometry": {
            "shape": "rect",
            "x0": 24.0,
            "x1": 29.0,
            "y0": 2.0,
            "y1": 7.0,
            "z0": None,
            "z1": None,
        },
        "parameters": {},
        "relationships": {"host_id": None, "space_ids": []},
    }
    return {
        "schema_version": "coordination-snapshot-test-v1",
        "scenario_id": "baseline-test",
        "input_hash": "input-hash-test",
        "model_hash": "model-hash-test",
        "geometry": {
            "hall": {"length_m": 36.0, "width_m": 18.0},
            "p2": {"level_m": 3.8, "x_m": 21.0, "length_m": 15.0, "width_m": 18.0},
        },
        "entities": {
            "GLZ-A": _opening(),
            "WALL-UNKNOWN-Z": unknown_z,
            "DOOR-UNRESOLVED": unresolved,
            "RL-01": rooflight,
            "P2-SPACE": p2_space,
        },
    }


def _connected_snapshot() -> dict:
    snapshot = _snapshot()
    opening = _opening("GLZ-WS-A")
    opening.update(
        {
            "label": "Side A workstation window",
            "source": {
                "path": "dreamhouse/window_daylight_d083.json",
                "key": "ground_floor_workstation_glazing[id=GLZ-WS-A]",
            },
            "geometry": {
                "shape": "opening",
                "x0": 5.0,
                "x1": 12.2,
                "y0": 0.0,
                "y1": 0.0,
                "z0": 0.75,
                "z1": 3.8,
            },
            "parameters": {
                "facade": "A",
                "start_m": 5.0,
                "width_m": 7.2,
                "height_m": 3.05,
                "sill_m": 0.75,
                "level_m": 0.0,
                "modules": 4,
            },
            "relationships": {"host_id": "HOST-PB-A", "space_ids": []},
        }
    )
    host = {
        "id": "HOST-PB-A",
        "kind": "wall",
        "label": "Side A host reference plane",
        "level": "PB",
        "aliases": [],
        "status": "context",
        "source": {"path": "derived", "key": "facade_planes[PB,A]"},
        "geometry": {
            "shape": "line",
            "x0": 0.0,
            "x1": 36.0,
            "y0": 0.0,
            "y1": 0.0,
            "z0": None,
            "z1": None,
        },
        "parameters": {"facade": "A", "capability": "reference plane; no wall solid"},
        "relationships": {"host_id": None, "space_ids": []},
    }
    snapshot["entities"]["GLZ-WS-A"] = opening
    snapshot["entities"]["HOST-PB-A"] = host
    snapshot["discipline_inputs"] = {
        "equipment": {
            "pb": {
                "workstations": [
                    {
                        "id": "PB-WS-A",
                        "window_id": "GLZ-WS-A",
                        "worktop_height": 0.75,
                        "worktop_depth": 0.9,
                        "worktop_x0": 5.9,
                        "worktop_length": 5.4,
                    }
                ]
            }
        }
    }
    return snapshot


def _add_stair_envelopes(snapshot: dict) -> None:
    for identifier, y0, y1, z0, z1 in (
        ("ST-F1", 7.7, 9.1, 0.0, 1.9),
        ("ST-F2", 9.3, 10.7, 1.9, 3.8),
    ):
        snapshot["entities"][identifier] = {
            "id": identifier,
            "kind": "stair",
            "label": identifier,
            "level": "PROJECT",
            "aliases": [],
            "status": "context",
            "source": {"path": "dreamhouse/stair_core.json", "key": identifier},
            "geometry": {
                "shape": "rect",
                "x0": 31.7,
                "x1": 34.4,
                "y0": y0,
                "y1": y1,
                "z0": z0,
                "z1": z1,
            },
            "parameters": {},
            "relationships": {"host_id": None, "space_ids": []},
        }


def _evaluation() -> dict:
    return {
        "findings": [
            {
                "rule_id": "TEST-OPEN-01",
                "status": "OPEN",
                "coverage": "complete",
                "message": "Opening needs a professional facade check.",
                "entity_ids": ["GLZ-A"],
                "severity": "review",
            }
        ],
        "quantity_ledger": {},
    }


def _parse_svg(document: str) -> ET.Element:
    return ET.fromstring(document)


class _IdsAndControls(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        self.tags.append((tag, values))
        if values.get("id"):
            self.ids.append(str(values["id"]))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)


class TestRenderViews(unittest.TestCase):
    def test_builds_two_plans_four_elevations_detail_sheet_and_index(self) -> None:
        views = render_views(_snapshot(), _evaluation())
        self.assertEqual(
            set(views),
            {
                "plan-pb.svg",
                "plan-p2.svg",
                "elevation-side-a.svg",
                "elevation-side-b.svg",
                "elevation-front.svg",
                "elevation-rear.svg",
                "window-details.svg",
                "window-sections.svg",
                "stair-sections.svg",
                "index.html",
            },
        )
        for filename, svg in views.items():
            if filename == "index.html":
                continue
            with self.subTest(view=filename):
                root = _parse_svg(svg)
                self.assertEqual(root.attrib["data-construction-authority"], "false")
                self.assertEqual(root.attrib["data-status"], "coordination projection")
                self.assertEqual(root.attrib["data-scenario-id"], "baseline-test")
                self.assertIsNotNone(root.find(f"{{{SVG_NS}}}title"))
                self.assertIsNotNone(root.find(f"{{{SVG_NS}}}desc"))
                self.assertIn("NOT FOR CONSTRUCTION", "".join(root.itertext()))

    def test_occurrence_ids_are_unique_and_rooflights_are_overhead_context(self) -> None:
        views = render_views(_snapshot(), _evaluation())
        for filename, document in views.items():
            if filename == "index.html":
                continue
            with self.subTest(view=filename):
                root = _parse_svg(document)
                ids = [node.get("id") for node in root.iter() if node.get("id")]
                self.assertEqual(len(ids), len(set(ids)))

        pb = _parse_svg(views["plan-pb.svg"])
        p2 = _parse_svg(views["plan-p2.svg"])
        roof_occurrences = [node for node in pb.iter() if node.get("data-entity-id") == "RL-01"]
        self.assertEqual(len(roof_occurrences), 1)
        self.assertEqual(roof_occurrences[0].get("data-projection-context"), "overhead")
        self.assertFalse(any(node.get("data-entity-id") == "RL-01" for node in p2.iter()))
        self.assertIn("ROOF OVERHEAD", "".join(pb.itertext()))

    def test_p2_plan_uses_source_envelope_and_omits_out_of_view_rooflights(self) -> None:
        views = render_views(_snapshot(), _evaluation())
        root = _parse_svg(views["plan-p2.svg"])
        envelope = next(node for node in root.iter() if node.get("data-context") == "p2-envelope")
        self.assertEqual(envelope.get("data-source"), "snapshot.geometry.p2")
        self.assertEqual(
            (envelope.get("data-world-x0"), envelope.get("data-world-x1")), ("21", "36")
        )
        self.assertEqual(
            (envelope.get("data-world-y0"), envelope.get("data-world-y1")), ("0", "18")
        )
        self.assertGreater(float(envelope.get("width", "0")), 0)
        self.assertGreater(float(envelope.get("height", "0")), 0)
        self.assertTrue(any(node.get("data-entity-id") == "P2-SPACE" for node in root.iter()))
        self.assertFalse(any(node.get("data-entity-id") == "RL-01" for node in root.iter()))
        dimension_values = {
            node.get("data-dimension-value")
            for node in root.iter()
            if node.get("data-dimension-source") == "geometry"
        }
        self.assertTrue({"15", "18"}.issubset(dimension_values))
        length_dimension = next(
            node for node in root.iter() if node.get("data-dimension-value") == "15"
        )
        expected_center = float(envelope.get("x")) + float(envelope.get("width")) / 2
        self.assertAlmostEqual(float(length_dimension.get("x", "0")), expected_center, places=1)

        fallback = _snapshot()
        fallback["geometry"]["p2"].pop("x_m")
        fallback["geometry"]["p2"].pop("length_m")
        fallback["geometry"]["p2"].pop("width_m")
        fallback_root = _parse_svg(render_views(fallback, _evaluation())["plan-p2.svg"])
        self.assertIn(
            "P2 extent unavailable; hall bounds shown as context only.",
            "".join(fallback_root.itertext()),
        )

    def test_plan_axes_and_stair_section_callouts_are_source_bound(self) -> None:
        snapshot = _snapshot()
        snapshot["geometry"]["axes"] = "X front-to-rear; Y Side A-to-B; Z above PB; units m"
        _add_stair_envelopes(snapshot)
        views = render_views(snapshot, _evaluation())
        inventory = inspect_views(snapshot, views)

        self.assertEqual(inventory["annotation_coverage"]["callouts"], 2)
        for plan_name in ("plan-pb.svg", "plan-p2.svg"):
            with self.subTest(view=plan_name):
                root = _parse_svg(views[plan_name])
                self.assertEqual(
                    root.get("data-plan-axis-directions"), "positive X right; positive Y up"
                )
                self.assertIn("X+ front → rear · Y+ Side A → B", "".join(root.itertext()))
                self.assertNotIn("NORTH", "".join(root.itertext()).upper())
                callout = next(
                    node for node in root.iter() if node.get("data-reference-type")
                )
                self.assertEqual(callout.get("data-callout-target-view-id"), "stair-sections")
                self.assertEqual(callout.get("data-related-view-id"), "stair-sections")
                self.assertEqual(callout.get("data-section-cut-claim"), "false")
                self.assertEqual(
                    len(callout.get("data-callout-refs", "").split()), 4
                )
                self.assertIn("SC-01", "".join(callout.itertext()))
                self.assertFalse(
                    any("stair-sections.svg#" in node.get("href", "") for node in root.iter())
                )

    def test_finding_badges_keep_navigation_without_question_mark_clutter(self) -> None:
        root = _parse_svg(render_views(_snapshot(), _evaluation())["plan-pb.svg"])
        badges = [
            node
            for node in root.iter()
            if node.tag == f"{{{SVG_NS}}}a" and node.get("data-finding-id") == "TEST-OPEN-01"
        ]
        self.assertEqual(len(badges), 1)
        self.assertTrue(badges[0].get("href", "").startswith("#plan-pb-finding-"))
        marker = next(node for node in badges[0].iter() if node.get("class") == "finding-marker")
        self.assertEqual(marker.get("r"), "4.5")
        self.assertNotIn("?", "".join(badges[0].itertext()))
        card = next(
            node
            for node in root.iter()
            if node.tag == f"{{{SVG_NS}}}rect" and node.get("data-finding-id") == "TEST-OPEN-01"
        )
        self.assertEqual(card.get("fill"), "#FFFDFA")

    def test_elevations_keep_sill_anchor_labels_and_coordinate_view_direction(self) -> None:
        snapshot = _snapshot()
        snapshot["entities"].update(
            {
                "GLZ-B": _facade_opening(
                    "GLZ-B", "B", (2.0, 3.2), (0.9, 1.9), sill=0.9, level=0.0
                ),
                "GLZ-DINING-STUDY-B": _facade_opening(
                    "GLZ-DINING-STUDY-B",
                    "B",
                    (23.85, 28.65),
                    (0.75, 2.55),
                    sill=0.75,
                    level=0.0,
                ),
                "W-H2": _facade_opening(
                    "W-H2", "B", (21.5, 25.1), (3.85, 6.75), sill=0.05, level=3.8
                ),
                "W-G": _facade_opening(
                    "W-G", "B", (28.65, 32.25), (3.85, 6.75), sill=0.05, level=3.8
                ),
                "W-EGRESS-P2": _facade_opening(
                    "W-EGRESS-P2",
                    "REAR",
                    (11.25, 12.25),
                    (4.7, 5.9),
                    sill=0.9,
                    level=3.8,
                ),
                "W-WELL": _facade_opening(
                    "W-WELL", "REAR", (13.0, 17.0), (5.2, 6.4), sill=1.4, level=3.8
                ),
            }
        )
        views = render_views(snapshot, _evaluation())
        for filename, expected_direction in (
            ("elevation-side-a.svg", "+Y"),
            ("elevation-side-b.svg", "−Y"),
            ("elevation-rear.svg", "−X"),
        ):
            with self.subTest(view=filename):
                root = _parse_svg(views[filename])
                self.assertEqual(root.get("data-view-direction"), expected_direction)
                self.assertIn("no geographic north assigned", root.get("data-view-direction-basis", ""))
                sill_labels = [
                    node for node in root.iter() if node.get("data-anchor-ref", "").endswith(".opening.sill")
                ]
                self.assertTrue(sill_labels)
                self.assertTrue(all((node.text or "").startswith("SILL ") for node in sill_labels))
                self.assertTrue(all(node.get("data-anchor-target") for node in sill_labels))
                self.assertTrue(all(node.get("data-note-for") for node in sill_labels))
                datum_y = [
                    float(node.get("y1", "0"))
                    for node in root.iter()
                    if node.get("data-datum-level")
                ]
                self.assertTrue(
                    all(
                        abs(float(label.get("y", "0")) - value) > 9
                        for label in sill_labels
                        for value in datum_y
                    )
                )
                shapes = []
                for occurrence in root.iter():
                    if occurrence.get("class") != "entity-occurrence":
                        continue
                    shape = next(
                        (node for node in occurrence.iter() if node.get("class") == "entity-shape"),
                        None,
                    )
                    if shape is not None:
                        x, y = float(shape.get("x", "0")), float(shape.get("y", "0"))
                        shapes.append(
                            (
                                x,
                                y,
                                x + float(shape.get("width", "0")),
                                y + float(shape.get("height", "0")),
                            )
                        )
                collision_labels = [
                    node
                    for node in root.iter()
                    if node.get("data-dimension-direction") == "vertical"
                    or node.get("data-anchor-ref", "").endswith(".opening.sill")
                ]
                horizontal_labels = [
                    node for node in root.iter()
                    if node.get("data-dimension-direction") == "horizontal"
                ]
                for label in collision_labels:
                    font_size = float(label.get("font-size", "10"))
                    text_width = len(label.text or "") * (3.9 if font_size < 8 else 5.6)
                    x = float(label.get("x", "0"))
                    anchor = label.get("text-anchor", "start")
                    if anchor == "middle":
                        left, right = x - text_width / 2, x + text_width / 2
                    elif anchor == "end":
                        left, right = x - text_width, x
                    else:
                        left, right = x, x + text_width
                    label_box = (
                        left,
                        float(label.get("y", "0")) - (8.5 if font_size < 8 else 6),
                        right,
                        float(label.get("y", "0")) + 2.5,
                    )
                    if label.get("data-anchor-ref", "").endswith(".opening.sill"):
                        for dimension in horizontal_labels:
                            dx = float(dimension.get("x"))
                            dy = float(dimension.get("y"))
                            half_width = len(dimension.text or "") * 5.6 / 2
                            self.assertFalse(
                                label_box[0] < dx + half_width + 2
                                and label_box[2] > dx - half_width - 2
                                and label_box[1] < dy + 3
                                and label_box[3] > dy - 10,
                                msg=f"Sill label overlaps width dimension in {filename}",
                            )
                    self.assertFalse(
                        any(
                            label_box[0] < shape[2] + 2
                            and label_box[2] > shape[0] - 2
                            and label_box[1] < shape[3] + 2
                            and label_box[3] > shape[1] - 2
                            for shape in shapes
                        ),
                        msg=f"{label.text} overlaps a projected opening in {filename}",
                    )

    def test_changed_geometry_preserves_identity_and_updates_anchored_dimensions(self) -> None:
        source = _snapshot()
        revised = deepcopy(source)
        revised["entities"]["GLZ-A"]["geometry"]["x1"] = 3.5
        before = render_views(source, _evaluation())
        after = render_views(revised, _evaluation())

        for filename in ("elevation-side-a.svg", "window-details.svg"):
            with self.subTest(view=filename):
                first = _parse_svg(before[filename])
                second = _parse_svg(after[filename])
                first_opening = next(
                    node for node in first.iter() if node.get("data-entity-id") == "GLZ-A"
                )
                second_opening = next(
                    node for node in second.iter() if node.get("data-entity-id") == "GLZ-A"
                )
                self.assertEqual(first_opening.get("data-world-x0"), "2")
                self.assertEqual(second_opening.get("data-world-x0"), "2")
                self.assertEqual(first_opening.get("data-world-x1"), "3.2")
                self.assertEqual(second_opening.get("data-world-x1"), "3.5")
                dimensions = [
                    node for node in second.iter() if node.get("data-dimension-for") == "GLZ-A"
                ]
                self.assertTrue(
                    any(node.get("data-dimension-value") == "1.5" for node in dimensions)
                )
                self.assertTrue(
                    any(node.get("data-dimension-source") == "geometry" for node in dimensions)
                )

    def test_unknown_vertical_extent_is_listed_without_a_fabricated_dimension(self) -> None:
        views = render_views(_snapshot(), _evaluation())
        elevation = _parse_svg(views["elevation-side-a.svg"])
        self.assertFalse(
            any(node.get("data-entity-id") == "WALL-UNKNOWN-Z" for node in elevation.iter())
        )
        self.assertFalse(
            any(node.get("data-dimension-for") == "WALL-UNKNOWN-Z" for node in elevation.iter())
        )
        self.assertIn("WALL-UNKNOWN-Z", "".join(elevation.itertext()))
        self.assertIn("DOOR-UNRESOLVED", "".join(_parse_svg(views["plan-pb.svg"]).itertext()))

    def test_open_findings_link_to_unique_view_panel_occurrences(self) -> None:
        evaluation = _evaluation()
        evaluation["findings"].append(
            {
                "rule_id": "TEST-OPEN-01",
                "status": "FAIL",
                "coverage": "complete",
                "message": "A second occurrence of the same rule identifier.",
                "entity_ids": ["GLZ-A"],
                "severity": "review",
            }
        )
        root = _parse_svg(render_views(_snapshot(), evaluation)["plan-pb.svg"])
        links = [
            node
            for node in root.iter()
            if node.tag == f"{{{SVG_NS}}}a" and node.get("data-finding-id") == "TEST-OPEN-01"
        ]
        self.assertTrue(links)
        targets = {node.get("id") for node in root.iter() if node.get("id")}
        self.assertTrue(all(node.get("href", "").removeprefix("#") in targets for node in links))
        ids = [node.get("id") for node in root.iter() if node.get("id")]
        self.assertEqual(len(ids), len(set(ids)))

    def test_finding_panel_wraps_long_text_and_caps_visible_cards(self) -> None:
        evaluation = _evaluation()
        evaluation["findings"] = [
            {
                "rule_id": f"LONG-RULE-{index}-" + ("x" * 70),
                "status": "OPEN",
                "coverage": "complete",
                "message": f"Finding {index}: " + ("unbroken" * 20),
                "entity_ids": ["GLZ-A"],
                "severity": "review",
            }
            for index in range(12)
        ]
        views = render_views(_snapshot(), evaluation)
        root = _parse_svg(views["plan-pb.svg"])
        cards = [
            node
            for node in root.iter()
            if node.get("data-finding-index") is not None and node.tag == f"{{{SVG_NS}}}rect"
        ]
        self.assertEqual(len(cards), 8)
        self.assertIn("4 additional findings are listed in index.html.", "".join(root.itertext()))
        self.assertTrue(
            all(
                node.text and len(node.text) <= 42
                for node in root.iter()
                if node.get("class") == "finding-heading" and node.text
            )
        )
        self.assertIn("unbroken" * 20, views["index.html"])
        self.assertEqual(
            len(cards[0].find(f"{{{SVG_NS}}}title").text),
            len("OPEN · LONG-RULE-0-" + ("x" * 70) + ". Finding 0: " + ("unbroken" * 20)),
        )

    def test_html_index_has_unique_ids_and_only_read_only_controls(self) -> None:
        index = render_views(_snapshot(), _evaluation())["index.html"]
        parser = _IdsAndControls()
        parser.feed(index)
        parser.close()

        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        tags = {tag for tag, _ in parser.tags}
        self.assertFalse({"form", "textarea", "select"}.intersection(tags))
        self.assertTrue(all("contenteditable" not in attrs for _, attrs in parser.tags))
        self.assertTrue(
            all(attrs.get("draggable") not in {"true", "True"} for _, attrs in parser.tags)
        )
        inputs = [attrs for tag, attrs in parser.tags if tag == "input"]
        self.assertEqual([attrs.get("type") for attrs in inputs], ["search"])
        self.assertTrue(
            all(tag != "button" or attrs.get("type") == "button" for tag, attrs in parser.tags)
        )
        lowered = index.lower()
        self.assertNotIn("fetch(", lowered)
        self.assertNotIn("xmlhttprequest", lowered)
        self.assertNotIn('method="post"', lowered)
        self.assertIn("data-select-entity", index)
        self.assertIn("data-entity-id", index)
        self.assertIn("filterFindings(entityId)", index)
        self.assertIn('href="view_inventory.json"', index)
        self.assertIn('href="anchor_lifecycle.json"', index)

    def test_window_section_tracks_opening_sill_worktop_and_quantity_inputs(self) -> None:
        snapshot = _connected_snapshot()
        evaluation = _evaluation()
        evaluation["findings"][0]["entity_ids"] = ["GLZ-WS-A"]
        evaluation["quantity_ledger"] = {
            "records": [
                {
                    "id": "Q-GLZ-WS-A-AREA",
                    "quantity": 21.96,
                    "unit": "m2",
                    "formula": "width_m * height_m",
                    "measurement_status": "model-derived nominal opening area; net glass area unknown",
                }
            ]
        }
        first = render_views(snapshot, evaluation)
        section = _parse_svg(first["window-sections.svg"])
        anchors = {
            node.get("data-anchor-id"): node
            for node in section.iter()
            if node.get("data-anchor-id")
        }
        self.assertEqual(section.get("data-view-id"), "window-sections")
        self.assertEqual(section.get("data-cut-plane-value-m"), "8.6")
        self.assertEqual(section.get("data-section-members"), "GLZ-WS-A")
        self.assertEqual(anchors["GLZ-WS-A.opening.sill"].get("data-world-z"), "0.75")
        self.assertEqual(anchors["GLZ-WS-A.opening.head"].get("data-world-z"), "3.8")
        self.assertEqual(anchors["PB-WS-A.worktop.top"].get("data-world-z"), "0.75")
        delta = next(
            node
            for node in section.iter()
            if node.get("data-dimension-id")
            == "window-sections-GLZ-WS-A-worktop-sill-level-difference"
        )
        self.assertEqual(delta.get("data-dimension-value"), "0")
        area = next(
            node for node in section.iter() if node.get("data-quantity-id") == "Q-GLZ-WS-A-AREA"
        )
        self.assertEqual(area.get("data-dimension-value"), "21.96")
        self.assertIn("continuity path: unresolved", "".join(section.itertext()).lower())
        self.assertIn("host thickness", "".join(section.itertext()).lower())

        revised = deepcopy(snapshot)
        revised_opening = revised["entities"]["GLZ-WS-A"]
        revised_opening["parameters"].update({"width_m": 7.5, "height_m": 2.9, "sill_m": 0.9})
        revised_opening["geometry"].update({"x1": 12.5, "z0": 0.9, "z1": 3.8})
        revised_evaluation = deepcopy(evaluation)
        revised_evaluation["quantity_ledger"]["records"][0]["quantity"] = 21.75
        after = render_views(revised, revised_evaluation)
        revised_section = _parse_svg(after["window-sections.svg"])
        revised_sill = next(
            node
            for node in revised_section.iter()
            if node.get("data-anchor-id") == "GLZ-WS-A.opening.sill"
        )
        self.assertEqual(revised_sill.get("data-world-z"), "0.9")
        revised_delta = next(
            node
            for node in revised_section.iter()
            if node.get("data-dimension-id")
            == "window-sections-GLZ-WS-A-worktop-sill-level-difference"
        )
        self.assertEqual(revised_delta.get("data-dimension-value"), "-0.15")
        revised_area = next(
            node
            for node in revised_section.iter()
            if node.get("data-quantity-id") == "Q-GLZ-WS-A-AREA"
        )
        self.assertEqual(revised_area.get("data-dimension-value"), "21.75")
        self.assertNotEqual(first["window-sections.svg"], after["window-sections.svg"])

    def test_semantic_dimensions_and_interface_callouts_resolve(self) -> None:
        snapshot = _connected_snapshot()
        inventory = inspect_views(snapshot, render_views(snapshot, _evaluation()))
        window_section = next(
            view for view in inventory["views"] if view["view_id"] == "window-sections"
        )
        self.assertGreaterEqual(len(window_section["dimensions"]), 4)
        self.assertEqual(len(window_section["callouts"]), 3)
        self.assertTrue(all(dimension["anchor_refs"] for dimension in window_section["dimensions"]))

    def test_missing_worktop_context_yields_an_explicit_unresolved_dimension(self) -> None:
        snapshot = _connected_snapshot()
        snapshot.pop("discipline_inputs")
        files = render_views(snapshot, _evaluation())
        inventory = inspect_views(snapshot, files)
        section = _parse_svg(files["window-sections.svg"])
        delta = next(
            node
            for node in section.iter()
            if node.get("data-dimension-id")
            == "window-sections-GLZ-WS-A-worktop-sill-level-difference"
        )
        self.assertEqual(delta.get("data-dimension-status"), "unresolved")
        self.assertIn("no value inferred", "".join(section.itertext()).lower())
        inventory_view = next(
            view for view in inventory["views"] if view["view_id"] == "window-sections"
        )
        delta_record = next(
            item
            for item in inventory_view["dimensions"]
            if item["dimension_id"] == delta.get("data-dimension-id")
        )
        self.assertEqual(delta_record["status"], "unresolved")

    def test_anchor_lifecycle_keeps_submillimetre_geometry_changes(self) -> None:
        baseline = _connected_snapshot()
        revised = deepcopy(baseline)
        revised["entities"]["GLZ-WS-A"]["geometry"]["x0"] = 5.0001
        revised["entities"]["GLZ-WS-A"]["parameters"]["start_m"] = 5.0001
        before = inspect_views(baseline, render_views(baseline, _evaluation()))
        after = inspect_views(revised, render_views(revised, _evaluation()))
        lifecycle = compare_anchors(after, before)
        changed = next(
            item
            for item in lifecycle["items"]
            if item["view_id"] == "elevation-side-a"
            and item["anchor_id"] == "GLZ-WS-A.opening.start"
        )
        self.assertEqual(changed["state"], "changed")
        self.assertEqual(changed["before"]["coordinates"]["data-world-x"], "5")
        self.assertEqual(changed["after"]["coordinates"]["data-world-x"], "5.0001")

    def test_failure_remains_visible_when_open_gates_overflow_the_panel(self) -> None:
        evaluation = {
            "findings": [
                {
                    "rule_id": f"OPEN-{i}",
                    "status": "OPEN",
                    "message": "Pending input",
                    "entity_ids": ["GLZ-A"],
                }
                for i in range(10)
            ]
        }
        evaluation["findings"].append(
            {
                "rule_id": "LATE-FAIL",
                "status": "FAIL",
                "message": "Synthetic geometry conflict",
                "entity_ids": ["GLZ-A"],
            }
        )
        root = _parse_svg(render_views(_snapshot(), evaluation)["plan-pb.svg"])
        cards = [
            node
            for node in root.iter()
            if node.get("data-finding-index") is not None and node.tag == f"{{{SVG_NS}}}rect"
        ]
        self.assertEqual(cards[0].get("data-finding-id"), "LATE-FAIL")
        self.assertTrue(
            any(
                node.get("data-finding-id") == "LATE-FAIL"
                for node in root.iter()
                if node.tag == f"{{{SVG_NS}}}a"
            )
        )

    def test_unlinked_benchmarks_do_not_hide_view_specific_warnings(self) -> None:
        evaluation = {
            "findings": [
                {
                    "rule_id": f"BENCHMARK-{i}",
                    "status": "OPEN",
                    "message": "Unlocated benchmark",
                    "entity_ids": [],
                }
                for i in range(10)
            ]
        }
        evaluation["findings"].append(
            {
                "rule_id": "WINDOW-INTERFACE",
                "status": "OPEN",
                "message": "Unknown window interface",
                "entity_ids": ["GLZ-A"],
            }
        )
        root = _parse_svg(render_views(_snapshot(), evaluation)["elevation-side-a.svg"])
        cards = [
            node
            for node in root.iter()
            if node.get("data-finding-index") is not None and node.tag == f"{{{SVG_NS}}}rect"
        ]
        self.assertEqual(cards[0].get("data-finding-id"), "WINDOW-INTERFACE")

    def test_elevations_label_absolute_floor_datums(self) -> None:
        snapshot = _snapshot()
        snapshot["geometry"]["p2"]["level_m"] = 3.8
        root = _parse_svg(render_views(snapshot, _evaluation())["elevation-side-a.svg"])
        datums = {
            node.get("data-datum-level"): node
            for node in root.iter()
            if node.get("data-datum-level")
        }
        self.assertEqual(set(datums), {"PB", "P2"})
        self.assertEqual(datums["PB"].get("data-elevation-m"), "0")
        self.assertEqual(datums["P2"].get("data-elevation-m"), "3.8")
        self.assertLess(float(datums["P2"].get("y1")), float(datums["PB"].get("y1")))


if __name__ == "__main__":
    unittest.main()

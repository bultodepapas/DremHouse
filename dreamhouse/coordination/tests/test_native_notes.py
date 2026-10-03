"""Legacy captions in connected outputs must follow current SC-01 sources."""

import unittest
from copy import deepcopy
from xml.etree import ElementTree as ET

from dreamhouse import generate_pb_b05
from dreamhouse.coordination.drawing_annotations import annotate_native_view
from dreamhouse.coordination.drawings import _synchronise_native_models
from dreamhouse.coordination.model import CoordinationError, resolve_project
from dreamhouse.coordination.native_notes import audit_native_notes, bind_native_notes
from dreamhouse.coordination.view_contract import inspect_views


class NativeNoteTests(unittest.TestCase):
    def test_level_change_refreshes_core_captions_and_detects_later_text_drift(self):
        snapshot = deepcopy(resolve_project())
        snapshot["discipline_inputs"]["structure"]["stair"]["levels"]["p2_finished_floor"] = 4.0
        pb, _, _, _ = _synchronise_native_models(snapshot)
        name = "drawings/architecture-ground-floor-core.svg"
        root = ET.fromstring(generate_pb_b05.core_sheet(pb))
        root.set("data-view-id", "architecture-ground-floor-core")
        bind_native_notes(snapshot, root)
        annotate_native_view(snapshot, root)
        captions = {
            n.get("data-native-note-key"): n for n in root.iter() if n.get("data-native-note-key")
        }
        self.assertIn("181.8 mm", captions["stair-summary"].text)
        self.assertEqual(captions["riser-height"].text, "R 181.8")
        self.assertIn("vertical extents remain unknown", captions["column-summary"].text)
        inspect_views(snapshot, {name: ET.tostring(root, encoding="unicode")})
        captions["riser-height"].text = "R 172.7"
        with self.assertRaisesRegex(CoordinationError, "Stale source-bound"):
            inspect_views(snapshot, {name: ET.tostring(root, encoding="unicode")})

    def test_deleted_duplicate_and_unrecognized_inherited_captions_fail_closed(self):
        snapshot = resolve_project()
        pb, _, _, _ = _synchronise_native_models(snapshot)
        original = ET.fromstring(generate_pb_b05.core_sheet(pb))
        original.set("data-view-id", "architecture-ground-floor-core")
        bind_native_notes(snapshot, original)
        for mode in ("delete", "duplicate", "remove-tags"):
            root = deepcopy(original)
            target = next(n for n in root.iter() if n.get("data-native-note-key") == "riser-height")
            if mode == "delete":
                parent = next(n for n in root.iter() if target in list(n))
                parent.remove(target)
            elif mode == "duplicate":
                root.append(deepcopy(target))
            else:
                for n in root.iter():
                    n.attrib.pop("data-native-note-key", None)
            with (
                self.subTest(mode=mode),
                self.assertRaisesRegex(CoordinationError, "Missing or duplicate"),
            ):
                audit_native_notes(snapshot, root)
        root = ET.fromstring(generate_pb_b05.core_sheet(pb))
        root.set("data-view-id", "architecture-ground-floor-core")
        next(n for n in root.iter() if n.text == "R 172.7").text = "R 999"
        with self.assertRaisesRegex(CoordinationError, "Missing or duplicate"):
            bind_native_notes(snapshot, root)

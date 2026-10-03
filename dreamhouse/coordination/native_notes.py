"""Refresh inherited SC-01 captions from the same captured source as the diagrams."""

from collections import Counter
from xml.etree import ElementTree as ET

from dreamhouse.coordination.model import CoordinationError


def _captions(snapshot: dict) -> dict[str, tuple[str, str]]:
    source = snapshot["discipline_inputs"]["structure"]["stair"]
    stair, levels, enclosure = (source[k] for k in ("stair", "levels", "enclosure"))
    count = stair["total_risers"]
    rise = (
        (levels["p2_finished_floor"] - levels["pb_finished_floor"]) / count if count > 0 else None
    )
    rise_text = f"{rise * 1000:.1f}" if rise is not None else "unknown"
    width = enclosure["x1"] - enclosure["x0"]
    depth = enclosure["y1"] - enclosure["y0"]
    wall = enclosure["wall_thickness"]
    structure = source["structure"]
    return {
        "riser-count": ("22R", f"{count}R"),
        "riser-height": ("R 172.7", f"R {rise_text}"),
        "going": ("G 270", f"G {stair['going'] * 1000:g}"),
        "stair-summary": (
            "Stair: 22 equal risers at 172.7 mm; 20 goings at 270 mm; two 1.40 m flights.",
            f"Stair source: {count} risers; mean rise {rise_text} mm; {sum(stair['treads_per_flight'])} goings at {stair['going'] * 1000:g} mm; flight width {stair['flight_width']:.2f} m.",
        ),
        "column-summary": (
            "Four 0.30 m column coordination reserves align PB, P2, foundations and roof lines.",
            f"{len(structure['column_reservations'])} column plan reserves, {structure['column_reservation_size']:.2f} m; vertical extents remain unknown.",
        ),
        "enclosure-summary": (
            "The 4.10 x 3.20 m clear stair rectangle closes exactly inside the 4.50 x 3.60 m enclosure.",
            f"Enclosure {width:.2f} x {depth:.2f} m; nominal inner bounds {width - 2 * wall:.2f} x {depth - 2 * wall:.2f} m; clearances require design.",
        ),
        "landing-summary": (
            "CF-011: the rear door meets the +1.90 m landing plane, not PB grade; do not claim discharge.",
            f"CF-011: landing datum {levels['intermediate_landing']:+.2f} m; rear grade-discharge geometry remains unresolved.",
        ),
    }


def bind_native_notes(snapshot: dict, root: ET.Element) -> None:
    captions = _captions(snapshot)
    by_old = {old: (key, text) for key, (old, text) in captions.items()}
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] == "text" and node.text in by_old:
            key, text = by_old[node.text]
            node.text = text
            node.set("data-native-note-key", key)
            node.set("data-native-note-source", "discipline_inputs.structure.stair")
    audit_native_notes(snapshot, root)


def audit_native_notes(snapshot: dict, root: ET.Element) -> None:
    nodes = [node for node in root.iter() if node.get("data-native-note-key") is not None]
    required = root.get("data-view-id") == "architecture-ground-floor-core"
    if not nodes and not required:
        return
    expected = _captions(snapshot)
    counts = Counter(node.get("data-native-note-key") for node in nodes)
    if any(count != 1 for count in counts.values()) or (required and set(counts) != set(expected)):
        raise CoordinationError("Missing or duplicate source-bound native stair caption")
    for node in nodes:
        key = node.get("data-native-note-key")
        if key is not None and (
            key not in expected or "".join(node.itertext()) != expected[key][1]
        ):
            raise CoordinationError(f"Stale source-bound native stair caption: {key}")

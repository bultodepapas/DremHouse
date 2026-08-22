"""Typed panel regions and conservative text boxes for SVG layout QA."""

from __future__ import annotations

import math
from dataclasses import dataclass
from xml.etree import ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"


def q(tag: str) -> str:
    return f"{{{SVG_NS}}}{tag}"


@dataclass(frozen=True)
class Bounds:
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        values = (self.x, self.y, self.width, self.height)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Layout bounds must contain finite values")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Layout bounds width and height must be positive")

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def area(self) -> float:
        return self.width * self.height

    def inset(self, amount: float) -> Bounds:
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("Layout inset must be finite and non-negative")
        return Bounds(
            self.x + amount,
            self.y + amount,
            self.width - 2 * amount,
            self.height - 2 * amount,
        )

    def contains_point(self, x: float, y: float, *, tolerance: float = 0.0) -> bool:
        return (
            self.x - tolerance <= x <= self.right + tolerance
            and self.y - tolerance <= y <= self.bottom + tolerance
        )

    def contains(self, other: Bounds, *, tolerance: float = 0.0) -> bool:
        return (
            other.x >= self.x - tolerance
            and other.y >= self.y - tolerance
            and other.right <= self.right + tolerance
            and other.bottom <= self.bottom + tolerance
        )

    def expanded(self, amount: float) -> Bounds:
        if not math.isfinite(amount) or amount < 0:
            raise ValueError("Layout expansion must be finite and non-negative")
        return Bounds(
            self.x - amount,
            self.y - amount,
            self.width + 2 * amount,
            self.height + 2 * amount,
        )

    def intersects(self, other: Bounds) -> bool:
        return (
            self.x < other.right
            and self.right > other.x
            and self.y < other.bottom
            and self.bottom > other.y
        )

    def serialize(self) -> str:
        return " ".join(f"{value:g}" for value in (self.x, self.y, self.width, self.height))

    @classmethod
    def parse(cls, value: str) -> Bounds:
        parts = value.replace(",", " ").split()
        if len(parts) != 4:
            raise ValueError("Layout bounds require x, y, width and height")
        try:
            return cls(*(float(part) for part in parts))
        except ValueError as error:
            raise ValueError(f"Invalid layout bounds: {value!r}") from error


@dataclass(frozen=True)
class LayoutRegion:
    id: str
    panel: Bounds
    safe: Bounds
    kind: str = "panel"

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Layout region ID is required")
        if not self.panel.contains(self.safe):
            raise ValueError(f"Safe bounds must remain inside panel {self.id!r}")

    @classmethod
    def with_inset(
        cls,
        region_id: str,
        panel: Bounds,
        inset: float,
        *,
        kind: str = "panel",
    ) -> LayoutRegion:
        return cls(region_id, panel, panel.inset(inset), kind)


SHEET_HEADER_REGION = LayoutRegion(
    "sheet-header",
    Bounds(36, 0, 1612, 105),
    Bounds(36, 18, 1612, 82),
    kind="sheet-header",
)
SHEET_FOOTER_REGION = LayoutRegion.with_inset(
    "sheet-footer",
    Bounds(36, 1026, 1612, 129),
    18,
    kind="sheet-footer",
)


def _parent_map(root: ET.Element) -> dict[ET.Element, ET.Element]:
    return {child: parent for parent in root.iter() for child in parent}


def _has_ancestor(
    element: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
    *,
    tag: str | None = None,
    element_id: str | None = None,
) -> bool:
    current: ET.Element | None = element
    while current is not None:
        if tag is not None and current.tag == q(tag):
            return True
        if element_id is not None and current.get("id") == element_id:
            return True
        current = parent_map.get(current)
    return False


def _coordinate(text: ET.Element, name: str) -> float:
    value = text.get(name)
    if value is None:
        raise ValueError(f"Presentation text requires explicit {name}")
    try:
        coordinate = float(value)
    except ValueError as error:
        raise ValueError(f"Presentation text has invalid {name}: {value!r}") from error
    if not math.isfinite(coordinate):
        raise ValueError(f"Presentation text has non-finite {name}")
    return coordinate


def register_text_regions(root: ET.Element, regions: tuple[LayoutRegion, ...]) -> None:
    """Assign every presentation text to one explicit panel/safe region."""

    if len({region.id for region in regions}) != len(regions):
        raise ValueError("Layout region IDs must be unique")
    parent_map = _parent_map(root)
    for text in root.iter(q("text")):
        if _has_ancestor(text, parent_map, element_id="layer-model") or _has_ancestor(
            text,
            parent_map,
            tag="defs",
        ):
            continue
        x = _coordinate(text, "x")
        y = _coordinate(text, "y")
        matches = [region for region in regions if region.panel.contains_point(x, y)]
        if not matches:
            content = " ".join("".join(text.itertext()).split())[:60]
            raise ValueError(f"Presentation text is outside every layout region: {content!r}")
        region = min(matches, key=lambda candidate: candidate.panel.area)
        text.set("data-layout-region", region.id)
        text.set("data-layout-kind", region.kind)
        text.set("data-panel-bounds", region.panel.serialize())
        text.set("data-safe-bounds", region.safe.serialize())
        if "rotate(" in text.get("transform", ""):
            text.set("data-layout-policy", "rotated-skip")


_NARROW_GLYPHS = frozenset("ilI.,;:!|'`")
_WIDE_GLYPHS = frozenset("MW@%&")


def estimate_line_width(value: str, font_size: float, letter_spacing: float = 0.0) -> float:
    """Estimate a conservative Inter-like advance width without a host-font dependency."""

    width = 0.0
    for character in value:
        if character.isspace():
            factor = 0.28
        elif character in _NARROW_GLYPHS:
            factor = 0.28
        elif character in _WIDE_GLYPHS:
            factor = 0.85
        elif character.isupper():
            factor = 0.62
        elif character.isdigit():
            factor = 0.56
        else:
            factor = 0.53
        width += factor * font_size
    return width + max(0, len(value) - 1) * letter_spacing


def estimate_text_bounds(
    text: ET.Element,
    *,
    letter_spacing: float = 0.0,
    stroke_width: float = 0.0,
    bold: bool = False,
) -> Bounds:
    """Estimate the axis-aligned ink/halo box for one unrotated SVG text element."""

    font_size = _coordinate(text, "font-size")
    anchor = text.get("text-anchor", "start")
    lines: list[tuple[str, float, float]] = []
    tspans = list(text.findall(q("tspan")))
    if tspans:
        baseline = _coordinate(text, "y")
        for tspan in tspans:
            baseline += float(tspan.get("dy", "0"))
            value = " ".join("".join(tspan.itertext()).split())
            lines.append((value, float(tspan.get("x", text.get("x", "0"))), baseline))
    else:
        value = " ".join("".join(text.itertext()).split())
        lines.append((value, _coordinate(text, "x"), _coordinate(text, "y")))

    boxes: list[Bounds] = []
    halo = max(0.0, stroke_width) / 2
    weight_factor = 1.02 if bold else 1.0
    for value, x, baseline in lines:
        width = estimate_line_width(value, font_size, letter_spacing) * weight_factor
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        elif anchor != "start":
            raise ValueError(f"Unsupported text-anchor for layout QA: {anchor!r}")
        boxes.append(
            Bounds(
                x - halo,
                baseline - 0.82 * font_size - halo,
                width + 2 * halo,
                1.04 * font_size + 2 * halo,
            )
        )

    left = min(box.x for box in boxes)
    top = min(box.y for box in boxes)
    right = max(box.right for box in boxes)
    bottom = max(box.bottom for box in boxes)
    return Bounds(left, top, right - left, bottom - top)

"""Typed panel regions and conservative text boxes for SVG layout QA."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET


SVG_NS = "http://www.w3.org/2000/svg"
LAYOUT_GEOMETRY_ROLES = frozenset({"keepout", "leader", "marker"})
SUPPORTED_GEOMETRY_TAGS = frozenset({"circle", "ellipse", "line", "polygon", "polyline", "rect"})
NUMBER_PATTERN = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
ROTATE_RE = re.compile(
    rf"^rotate\(\s*({NUMBER_PATTERN})[ ,]+({NUMBER_PATTERN})[ ,]+"
    rf"({NUMBER_PATTERN})\s*\)$"
)


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
class Rotation:
    angle: float
    center_x: float
    center_y: float

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) for value in (self.angle, self.center_x, self.center_y)):
            raise ValueError("Text rotation values must be finite")


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


def parse_text_rotation(transform: str) -> Rotation | None:
    """Parse one explicit SVG rotation or fail closed on every other transform."""

    normalized = transform.strip()
    if not normalized:
        return None
    match = ROTATE_RE.fullmatch(normalized)
    if match is None:
        raise ValueError(
            "Presentation text transform must be one explicit rotate(angle cx cy)"
        )
    return Rotation(*(float(value) for value in match.groups()))


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
        rotation = parse_text_rotation(text.get("transform", ""))
        if rotation is not None:
            text.set("data-layout-policy", "rotated-measured")
        else:
            text.attrib.pop("data-layout-policy", None)


def _geometry_coordinate(element: ET.Element, name: str) -> float:
    value = element.get(name)
    if value is None:
        raise ValueError(f"Registered geometry requires explicit {name}")
    try:
        coordinate = float(value)
    except ValueError as error:
        raise ValueError(f"Registered geometry has invalid {name}: {value!r}") from error
    if not math.isfinite(coordinate):
        raise ValueError(f"Registered geometry has non-finite {name}")
    return coordinate


def _bounds_from_extents(
    left: float,
    top: float,
    right: float,
    bottom: float,
    *,
    stroke_width: float,
) -> Bounds:
    if not math.isfinite(stroke_width) or stroke_width < 0:
        raise ValueError("Geometry stroke width must be finite and non-negative")
    halo = stroke_width / 2
    left -= halo
    top -= halo
    right += halo
    bottom += halo
    epsilon = 1e-9
    if right <= left:
        left -= epsilon / 2
        right += epsilon / 2
    if bottom <= top:
        top -= epsilon / 2
        bottom += epsilon / 2
    return Bounds(left, top, right - left, bottom - top)


def _points(element: ET.Element) -> list[tuple[float, float]]:
    raw = element.get("points", "").replace(",", " ").split()
    if len(raw) < 4 or len(raw) % 2:
        raise ValueError("Registered polyline/polygon requires coordinate pairs")
    try:
        values = [float(value) for value in raw]
    except ValueError as error:
        raise ValueError("Registered polyline/polygon has invalid points") from error
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Registered polyline/polygon has non-finite points")
    return list(zip(values[::2], values[1::2], strict=True))


def estimate_geometry_bounds(element: ET.Element, *, stroke_width: float = 0.0) -> Bounds:
    """Return a conservative paint box for one untransformed registered primitive."""

    tag = element.tag.rsplit("}", 1)[-1]
    if tag not in SUPPORTED_GEOMETRY_TAGS:
        raise ValueError(f"Unsupported registered geometry element: {tag!r}")
    if element.get("transform", "").strip():
        raise ValueError("Transformed registered geometry is not supported by this profile")

    if tag == "rect":
        x = _geometry_coordinate(element, "x")
        y = _geometry_coordinate(element, "y")
        width = _geometry_coordinate(element, "width")
        height = _geometry_coordinate(element, "height")
        if width <= 0 or height <= 0:
            raise ValueError("Registered rectangle width and height must be positive")
        extents = (x, y, x + width, y + height)
    elif tag == "circle":
        cx = _geometry_coordinate(element, "cx")
        cy = _geometry_coordinate(element, "cy")
        radius = _geometry_coordinate(element, "r")
        if radius <= 0:
            raise ValueError("Registered circle radius must be positive")
        extents = (cx - radius, cy - radius, cx + radius, cy + radius)
    elif tag == "ellipse":
        cx = _geometry_coordinate(element, "cx")
        cy = _geometry_coordinate(element, "cy")
        radius_x = _geometry_coordinate(element, "rx")
        radius_y = _geometry_coordinate(element, "ry")
        if radius_x <= 0 or radius_y <= 0:
            raise ValueError("Registered ellipse radii must be positive")
        extents = (cx - radius_x, cy - radius_y, cx + radius_x, cy + radius_y)
    elif tag == "line":
        x1 = _geometry_coordinate(element, "x1")
        y1 = _geometry_coordinate(element, "y1")
        x2 = _geometry_coordinate(element, "x2")
        y2 = _geometry_coordinate(element, "y2")
        extents = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
    else:
        points = _points(element)
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        extents = (min(xs), min(ys), max(xs), max(ys))
    return _bounds_from_extents(*extents, stroke_width=stroke_width)


def register_geometry_regions(root: ET.Element, regions: tuple[LayoutRegion, ...]) -> None:
    """Assign explicitly registered editorial primitives to their smallest panel region."""

    if len({region.id for region in regions}) != len(regions):
        raise ValueError("Layout region IDs must be unique")
    parent_map = _parent_map(root)
    for element in root.iter():
        role = element.get("data-layout-geometry", "").strip()
        if not role:
            continue
        if role not in LAYOUT_GEOMETRY_ROLES:
            raise ValueError(f"Unsupported layout geometry role: {role!r}")
        if _has_ancestor(element, parent_map, element_id="layer-model") or _has_ancestor(
            element,
            parent_map,
            tag="defs",
        ):
            raise ValueError("Model/definition geometry cannot enter the editorial layout gate")
        if role in {"leader", "marker"} and not element.get(
            "data-layout-relation", ""
        ).strip():
            raise ValueError(f"Registered {role} geometry requires data-layout-relation")
        bounds = estimate_geometry_bounds(element)
        x = bounds.x + bounds.width / 2
        y = bounds.y + bounds.height / 2
        matches = [region for region in regions if region.panel.contains_point(x, y)]
        if not matches:
            raise ValueError(f"Registered {role} geometry is outside every layout region")
        region = min(matches, key=lambda candidate: candidate.panel.area)
        element.set("data-layout-region", region.id)


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
    """Estimate the axis-aligned ink/halo box for plain or explicitly rotated text."""

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

    rotation = parse_text_rotation(text.get("transform", ""))
    if rotation is not None:
        radians = math.radians(rotation.angle)
        cosine = math.cos(radians)
        sine = math.sin(radians)
        rotated: list[Bounds] = []
        for box in boxes:
            corners = (
                (box.x, box.y),
                (box.right, box.y),
                (box.right, box.bottom),
                (box.x, box.bottom),
            )
            points = [
                (
                    rotation.center_x
                    + cosine * (x - rotation.center_x)
                    - sine * (y - rotation.center_y),
                    rotation.center_y
                    + sine * (x - rotation.center_x)
                    + cosine * (y - rotation.center_y),
                )
                for x, y in corners
            ]
            left = min(point[0] for point in points)
            top = min(point[1] for point in points)
            right = max(point[0] for point in points)
            bottom = max(point[1] for point in points)
            rotated.append(Bounds(left, top, right - left, bottom - top))
        boxes = rotated

    left = min(box.x for box in boxes)
    top = min(box.y for box in boxes)
    right = max(box.right for box in boxes)
    bottom = max(box.bottom for box in boxes)
    return Bounds(left, top, right - left, bottom - top)

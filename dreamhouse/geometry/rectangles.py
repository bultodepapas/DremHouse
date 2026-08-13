"""Axis-aligned geometry primitives for schematic coordination."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Rect:
    """An axis-aligned rectangle in project metres."""

    id: str
    x: float
    y: float
    width: float
    depth: float

    @classmethod
    def from_mapping(
        cls,
        value: dict[str, Any],
        *,
        width_key: str = "w",
        depth_key: str = "d",
    ) -> Rect:
        return cls(
            id=str(value["id"]),
            x=float(value["x"]),
            y=float(value["y"]),
            width=float(value[width_key]),
            depth=float(value[depth_key]),
        )

    @property
    def x1(self) -> float:
        return self.x + self.width

    @property
    def y1(self) -> float:
        return self.y + self.depth

    @property
    def area(self) -> float:
        return self.width * self.depth

    def contains(self, other: Rect, tolerance: float = 1e-9) -> bool:
        return (
            other.x >= self.x - tolerance
            and other.y >= self.y - tolerance
            and other.x1 <= self.x1 + tolerance
            and other.y1 <= self.y1 + tolerance
        )

    def intersects(self, other: Rect, tolerance: float = 1e-9) -> bool:
        return not (
            self.x1 <= other.x + tolerance
            or other.x1 <= self.x + tolerance
            or self.y1 <= other.y + tolerance
            or other.y1 <= self.y + tolerance
        )

    def expanded(self, x_clearance: float, y_clearance: float | None = None) -> Rect:
        y_clearance = x_clearance if y_clearance is None else y_clearance
        return Rect(
            id=f"{self.id}-CLEAR",
            x=self.x - x_clearance,
            y=self.y - y_clearance,
            width=self.width + 2 * x_clearance,
            depth=self.depth + 2 * y_clearance,
        )


def collision_pairs(rectangles: Iterable[Rect]) -> list[tuple[str, str]]:
    """Return deterministic pairs whose interiors overlap."""

    values = sorted(rectangles, key=lambda item: item.id)
    return [
        (left.id, right.id)
        for index, left in enumerate(values)
        for right in values[index + 1 :]
        if left.intersects(right)
    ]

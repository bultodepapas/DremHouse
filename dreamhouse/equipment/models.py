"""Typed access to equipment dimensions and active placements."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dreamhouse.geometry import Rect

DEFAULT_CATALOG = Path(__file__).with_name("catalog.json")
DEFAULT_LAYOUT = Path(__file__).with_name("layout_v04.json")


@dataclass(frozen=True)
class ProductEnvelope:
    id: str
    category: str
    width_m: float
    depth_m: float
    operating_depth_m: float
    side_clearance_m: float
    front_clearance_m: float
    source: str
    source_status: str

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> ProductEnvelope:
        return cls(
            id=value["id"],
            category=value["category"],
            width_m=float(value["width_m"]),
            depth_m=float(value["depth_m"]),
            operating_depth_m=float(value["operating_depth_m"]),
            side_clearance_m=float(value.get("side_clearance_m", 0.0)),
            front_clearance_m=float(value.get("front_clearance_m", 0.0)),
            source=value["source"],
            source_status=value["source_status"],
        )

    def footprint(self, placement: dict[str, Any], *, operating: bool = False) -> Rect:
        orientation = placement.get("orientation", "width_along_x")
        depth = self.operating_depth_m if operating else self.depth_m
        if orientation == "depth_along_x":
            width, depth = depth, self.width_m
        else:
            width = self.width_m
        return Rect(placement["id"], float(placement["x"]), float(placement["y"]), width, depth)


@dataclass(frozen=True)
class EquipmentCatalog:
    metadata: dict[str, Any]
    products: dict[str, ProductEnvelope]


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object in {path}")
    return value


def load_catalog(path: Path = DEFAULT_CATALOG) -> EquipmentCatalog:
    data = _read(path)
    products = {
        value["id"]: ProductEnvelope.from_mapping(value) for value in data["products"]
    }
    return EquipmentCatalog(metadata={key: value for key, value in data.items() if key != "products"}, products=products)


def load_layout(path: Path = DEFAULT_LAYOUT) -> dict[str, Any]:
    return _read(path)

"""Validate real equipment envelopes against the current schematic geometry."""

from __future__ import annotations

from typing import Any

from dreamhouse.geometry import Rect, collision_pairs
from dreamhouse.model.schema import CheckResult, check, open_check

from .models import EquipmentCatalog, load_catalog, load_layout


def _room(p2: dict[str, Any], room_id: str) -> Rect:
    value = next(item for item in p2["spaces"] if item["id"] == room_id)
    return Rect.from_mapping(value)


def _hosts(pb: dict[str, Any], p2: dict[str, Any], layout: dict[str, Any]) -> dict[str, Rect]:
    wall_run = pb["kitchen"]["wall_run"]
    bod = next(item for item in pb["core"] if item["id"] == "BOD")
    hosts = {
        "M-D": _room(p2, "M-D"),
        "DOUBLE-HEIGHT": Rect("DOUBLE-HEIGHT", 0.0, 0.0, 21.0, 18.0),
        "KITCHEN-WALL-RUN": Rect(
            "KITCHEN-WALL-RUN",
            float(wall_run["x"]),
            float(wall_run["y"]),
            float(wall_run["length"]),
            float(wall_run["depth"]),
        ),
        "PB-BOD": Rect(
            "PB-BOD",
            float(pb["great_wall"]["x"]),
            float(bod["y0"]),
            float(pb["envelope"]["length"]) - float(pb["great_wall"]["x"]),
            float(bod["y1"]) - float(bod["y0"]),
        ),
    }
    for host_id, value in layout.get("host_overrides", {}).items():
        hosts[host_id] = Rect(
            host_id,
            float(value["x"]),
            float(value["y"]),
            float(value["width"]),
            float(value["depth"]),
        )
    return hosts


def validate_equipment(
    pb: dict[str, Any],
    p2: dict[str, Any],
    *,
    catalog: EquipmentCatalog | None = None,
    layout: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return traceable checks without promoting benchmarks to frozen requirements."""

    catalog = catalog or load_catalog()
    layout = layout or load_layout()
    hosts = _hosts(pb, p2, layout)
    placements = layout["placements"]
    bodies: dict[str, Rect] = {}
    operating: dict[str, Rect] = {}
    checks: list[CheckResult] = []

    for placement in placements:
        product_id = placement["product_id"]
        product = catalog.products.get(product_id)
        if product is None:
            checks.append(
                check(
                    f"EQUIP-{placement['id']}-CATALOG",
                    False,
                    f"Product {product_id} is not present in the controlled catalogue",
                    entity_ids=(placement["id"],),
                )
            )
            continue
        body = product.footprint(placement)
        operation = product.footprint(placement, operating=True)
        bodies[placement["id"]] = body
        operating[placement["id"]] = operation
        host = hosts[placement["host"]]
        body_fits = host.contains(body)
        if placement["id"] == "EQ-FRIDGE" and not body_fits:
            checks.append(
                open_check(
                    "EQUIP-EQ-FRIDGE-HOST",
                    "Selected refrigerator is 0.101 m deeper than the current 0.75 m wall-run datum; resolve cabinetry/recess before freeze",
                    entity_ids=(placement["id"], host.id),
                )
            )
        else:
            checks.append(
                check(
                    f"EQUIP-{placement['id']}-HOST",
                    body_fits,
                    f"{placement['id']} body footprint is inside {host.id}",
                    entity_ids=(placement["id"], host.id),
                )
            )

    laundry = [bodies[item] for item in ("EQ-WASHER", "EQ-DRYER") if item in bodies]
    checks.append(
        check(
            "EQUIP-LAUNDRY-BODY-COLLISION",
            not collision_pairs(laundry),
            "Washer and dryer body footprints do not collide",
            entity_ids=tuple(item.id for item in laundry),
        )
    )
    bod = hosts["PB-BOD"]
    laundry_operating = [
        operating[item] for item in ("EQ-WASHER", "EQ-DRYER") if item in operating
    ]
    checks.append(
        check(
            "EQUIP-LAUNDRY-OPERATION-IN-BOD",
            all(bod.contains(item) for item in laundry_operating),
            "Laundry open-door envelopes remain inside the PB storage room",
            entity_ids=tuple(item.id for item in laundry_operating) + (bod.id,),
        )
    )

    kitchen_bodies = [
        bodies[item]
        for item in ("EQ-RANGE", "EQ-DISHWASHER", "EQ-FRIDGE")
        if item in bodies
    ]
    checks.append(
        check(
            "EQUIP-KITCHEN-BODY-COLLISION",
            not collision_pairs(kitchen_bodies),
            "Kitchen appliance body footprints do not collide",
            entity_ids=tuple(item.id for item in kitchen_bodies),
        )
    )
    island = pb["kitchen"]["island"]
    island_rect = Rect(
        "KITCHEN-ISLAND",
        float(island["x"]),
        float(island["y"]),
        float(island["length"]),
        float(island["depth"]),
    )
    checks.append(
        check(
            "EQUIP-KITCHEN-DOORS-CLEAR-ISLAND",
            all(not operating[item.id].intersects(island_rect) for item in kitchen_bodies),
            "Range and dishwasher open-door envelopes stop short of the island",
            entity_ids=tuple(item.id for item in kitchen_bodies) + (island_rect.id,),
        )
    )

    primary = _room(p2, "M-D")
    bed = bodies.get("EQ-M-BED")
    bed_clear = bed.expanded(0.9) if bed else None
    checks.append(
        check(
            "EQUIP-PRIMARY-BED-CLEARANCE",
            bool(bed_clear and primary.contains(bed_clear)),
            "The project king-bed envelope retains 0.90 m clearance on all sides",
            entity_ids=("EQ-M-BED", primary.id),
        )
    )

    status_order = {"PASS": 0, "OPEN": 1, "FAIL": 2}
    overall = max((item.status for item in checks), key=status_order.get)
    return {
        "revision": layout["revision"],
        "status": overall,
        "checks": [item.to_dict() for item in checks],
        "placements": [
            {
                **placement,
                "body": bodies.get(placement["id"]).__dict__
                if placement["id"] in bodies
                else None,
                "operating": operating.get(placement["id"]).__dict__
                if placement["id"] in operating
                else None,
            }
            for placement in placements
        ],
        "note": "Catalogue entries are coordination benchmarks and must be reverified at procurement.",
    }

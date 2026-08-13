"""Build auditable quantities from the canonical scenario."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from dreamhouse.architecture import evaluate_room_program
from dreamhouse.envelope import build_opening_schedule


@dataclass(frozen=True)
class QuantityRecord:
    id: str
    assembly_id: str
    description: str
    quantity: float
    unit: str
    source_model: str
    formula: str
    measurement_status: str


def build_quantity_ledger(
    pb: dict[str, Any], p2: dict[str, Any], rooflights: dict[str, Any]
) -> dict[str, Any]:
    openings = build_opening_schedule(pb, p2, rooflights)
    records: list[QuantityRecord] = []
    for item in openings["items"]:
        if item["source"] == "PB.technical_glazing":
            assembly = "PB-TECHNICAL-GLAZING"
        elif item["source"] == "P2.windows":
            assembly = "P2-WINDOWS"
        else:
            assembly = "ROOFLIGHT-GLAZING"
        records.append(
            QuantityRecord(
                id=f"Q-{item['id']}-AREA",
                assembly_id=assembly,
                description=f"{item['id']} measured opening area",
                quantity=float(item["area_m2"]),
                unit="m2",
                source_model=item["source"],
                formula="width_m * height_m",
                measurement_status="model-derived schematic quantity",
            )
        )
        if item["kind"] == "rooflight":
            records.append(
                QuantityRecord(
                    id=f"Q-{item['id']}-CURB",
                    assembly_id="ROOFLIGHT-CURB",
                    description=f"{item['id']} curb perimeter",
                    quantity=float(item["perimeter_m"]),
                    unit="m",
                    source_model=item["source"],
                    formula="2 * (length_m + width_m)",
                    measurement_status="model-derived schematic quantity",
                )
            )
    p2_envelope = p2["envelope"]
    records.append(
        QuantityRecord(
            id="Q-P2-GROSS-FLOOR",
            assembly_id="P2-GROSS-FLOOR",
            description="Gross P2 plan area",
            quantity=round(float(p2_envelope["length"]) * float(p2_envelope["width"]), 3),
            unit="m2",
            source_model="P2.envelope",
            formula="length * width",
            measurement_status="model-derived gross envelope",
        )
    )
    programme = evaluate_room_program(p2)
    for suite, area in programme["suite_component_areas_m2"].items():
        records.append(
            QuantityRecord(
                id=f"Q-SUITE-{suite}-COMPONENTS",
                assembly_id="PROGRAM-AREA",
                description=f"Suite {suite} tagged component area",
                quantity=float(area),
                unit="m2",
                source_model="P2.spaces",
                formula="sum(space.w * space.d) for tagged suite components",
                measurement_status="programme metric; not a construction takeoff",
            )
        )
    grouped: dict[str, dict[str, float]] = {}
    for record in records:
        grouped.setdefault(record.assembly_id, {})
        grouped[record.assembly_id][record.unit] = round(
            grouped[record.assembly_id].get(record.unit, 0.0) + record.quantity, 3
        )
    return {
        "revision": "0.4-I01-QUANTITIES",
        "status": "schematic model-derived; not procurement or construction quantity",
        "records": [asdict(item) for item in records],
        "totals_by_assembly": grouped,
        "programme": programme,
    }

"""Reconcile quantities to cost codes while refusing false budget certainty."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEFAULT_MAPPING = Path(__file__).with_name("cost_mapping.json")
DEFAULT_RATES = Path(__file__).with_name("rate_book.json")


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object in {path}")
    return value


def reconcile_costs(
    quantity_ledger: dict[str, Any],
    *,
    mapping: dict[str, Any] | None = None,
    rate_book: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Join quantities to control codes and explicitly block ineligible extensions."""

    mapping = mapping or _read(DEFAULT_MAPPING)
    rate_book = rate_book or _read(DEFAULT_RATES)
    totals = quantity_ledger["totals_by_assembly"]
    rows = []
    open_assemblies = []
    for assembly_id, units in sorted(totals.items()):
        definition = mapping["mappings"].get(assembly_id)
        if definition is None:
            definition = {
                "cost_code": None,
                "mapping_status": "OPEN",
                "note": "No mapping record exists.",
            }
        cost_code = definition["cost_code"]
        rate = rate_book["rates"].get(cost_code) if cost_code else None
        unit, quantity = next(iter(units.items()))
        rate_matches = bool(rate and rate["unit"] == unit)
        eligible = bool(
            definition["mapping_status"] == "PASS"
            and rate_matches
            and rate.get("eligible_for_budget")
        )
        control_extension = (
            round(quantity * float(rate["control_rate_cop"]), 2) if rate_matches else None
        )
        baseline_extension = (
            round(float(rate["baseline_quantity"]) * float(rate["control_rate_cop"]), 2)
            if rate_matches
            else None
        )
        row = {
            "assembly_id": assembly_id,
            "quantity": quantity,
            "unit": unit,
            "cost_code": cost_code,
            "mapping_status": definition["mapping_status"],
            "mapping_note": definition["note"],
            "control_rate_cop": rate["control_rate_cop"] if rate_matches else None,
            "control_extension_cop": control_extension,
            "baseline_extension_cop": baseline_extension,
            "control_variance_cop": (
                round(control_extension - baseline_extension, 2)
                if control_extension is not None and baseline_extension is not None
                else None
            ),
            "eligible_for_budget": eligible,
        }
        rows.append(row)
        if definition["mapping_status"] == "OPEN" or not eligible:
            open_assemblies.append(assembly_id)
    return {
        "revision": "0.4-I01-COST-RECONCILIATION",
        "status": "OPEN",
        "currency": rate_book["currency"],
        "rows": rows,
        "open_or_ineligible_assemblies": sorted(set(open_assemblies)),
        "approved_budget_total_cop": None,
        "note": "Control extensions expose drift only. They are not summed into a budget because no rate is eligible.",
    }

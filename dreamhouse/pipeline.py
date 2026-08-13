"""Run the integrated architecture-structure-quantity-cost coordination pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from dreamhouse.architecture import evaluate_room_program
from dreamhouse.cost import reconcile_costs
from dreamhouse.cost.reconcile import DEFAULT_MAPPING, DEFAULT_RATES
from dreamhouse.envelope import build_opening_schedule, validate_rooflights
from dreamhouse.equipment import validate_equipment
from dreamhouse.equipment.models import DEFAULT_CATALOG, DEFAULT_LAYOUT
from dreamhouse.generate_p2_b09 import validate_model as validate_p2
from dreamhouse.generate_rooflight_b11 import generate as generate_rooflight_drawings
from dreamhouse.model import load_project
from dreamhouse.model.io import (
    DEFAULT_MANIFEST,
    REPOSITORY_ROOT,
    canonical_json_hash,
    sha256_path,
)
from dreamhouse.quantities import build_quantity_ledger
from dreamhouse.structure.coordination import compare_support_concepts
from dreamhouse.structure.e1_screening import run_screening

DEFAULT_OUTPUT = REPOSITORY_ROOT / "planos" / "integracion_v0.4_i02"


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _status_counts(groups: list[list[dict[str, Any]]]) -> dict[str, int]:
    counts = {"PASS": 0, "OPEN": 0, "FAIL": 0}
    for checks in groups:
        for item in checks:
            counts[item["status"]] += 1
    return counts


def _evidence_markdown(results: dict[str, Any]) -> str:
    counts = results["status_counts"]
    quantities = results["quantity_ledger"]["totals_by_assembly"]
    programme = results["programme"]["suite_component_areas_m2"]
    cost_rows = results["cost_reconciliation"]["rows"]
    cost_lines = [
        "| Assembly | Model quantity | Control code | Control variance | Budget eligible |",
        "|---|---:|---|---:|---|",
    ]
    for row in cost_rows:
        variance = (
            f"COP {row['control_variance_cop']:,.0f}"
            if row["control_variance_cop"] is not None
            else "not calculable"
        )
        cost_lines.append(
            f"| {row['assembly_id']} | {row['quantity']:.2f} {row['unit']} | "
            f"{row['cost_code'] or 'unmapped'} | {variance} | "
            f"{'yes' if row['eligible_for_budget'] else 'no'} |"
        )
    return "\n".join(
        [
            "# Integrated coordination evidence — v0.4-I02",
            "",
            f"- Scenario: `{results['scenario_id']}`",
            f"- Input hash: `{results['input_hash']}`",
            f"- Overall status: **{results['overall_status']}**",
            f"- Checks: {counts['PASS']} PASS / {counts['OPEN']} OPEN / {counts['FAIL']} FAIL",
            "- Authority: coordination evidence only; not for selection, procurement, budgeting, or construction.",
            "",
            "## Deterministic geometry outcomes",
            "",
            f"- PB technical glazing: {quantities['PB-TECHNICAL-GLAZING']['m2']:.2f} m².",
            f"- P2 windows: {quantities['P2-WINDOWS']['m2']:.2f} m².",
            f"- D-054 rooflights: {quantities['ROOFLIGHT-GLAZING']['m2']:.2f} m² glass and {quantities['ROOFLIGHT-CURB']['m']:.2f} m curb.",
            f"- Suite component areas: M {programme['M']:.2f}, H1 {programme['H1']:.2f}, H2 {programme['H2']:.2f}, G {programme['G']:.2f} m².",
            "",
            "## Explicit coordination blockers",
            "",
            "- Rooflights cross schematic M60 portal lines X=6 and X=18 and purlin line Y=9; trimmers and diaphragm details are not designed.",
            "- The 758 L refrigerator benchmark is 0.101 m deeper than the current kitchen wall-run datum.",
            "- Tagged primary-suite components total 66.28 m² versus the 75 m² owner study target; the gross/net boundary remains unresolved.",
            "- Only the four stair-enclosure corner lines pass the current full-height geometry audit; no structural system is selected.",
            "- Rooflight assemblies have no authorized cost line or eligible rate.",
            "",
            "## Cost-control reconciliation",
            "",
            *cost_lines,
            "",
            "Control extensions show exposure against old low-confidence rates. They are intentionally not summed into an approved budget.",
            "",
        ]
    )


def run_pipeline(
    *,
    scenario_id: str = "D057_P2_W01",
    output_dir: Path = DEFAULT_OUTPUT,
    include_structural_screening: bool = True,
) -> dict[str, Any]:
    """Execute one declared scenario and write a self-auditing evidence package."""

    project = load_project(scenario_id)
    source_hashes = {
        **project.source_hashes,
        "project_manifest": sha256_path(DEFAULT_MANIFEST),
        "equipment_catalog": sha256_path(DEFAULT_CATALOG),
        "equipment_layout": sha256_path(DEFAULT_LAYOUT),
        "cost_mapping": sha256_path(DEFAULT_MAPPING),
        "rate_book": sha256_path(DEFAULT_RATES),
    }
    integration_input_hash = canonical_json_hash(
        {
            "scenario_input_hash": project.input_hash,
            "source_hashes": source_hashes,
        }
    )
    pb = project.models["pb"]
    p2 = project.models["p2"]
    rooflights = project.models["rooflights"]
    programme = evaluate_room_program(p2)
    equipment = validate_equipment(pb, p2)
    rooflight_checks = validate_rooflights(
        rooflights,
        canonical_double_height=project.geometry["double_height"],
    )
    p2_checks = validate_p2(p2)
    opening_schedule = build_opening_schedule(pb, p2, rooflights)
    quantities = build_quantity_ledger(pb, p2, rooflights)
    costs = reconcile_costs(quantities)
    support = compare_support_concepts(
        project.models["structure"], pb, p2, project.models["e1_space"]
    )
    structural = None
    if include_structural_screening:
        structural = run_screening(
            project.models["structure"],
            project.models["roof_space"],
            project.models["e1_space"],
            pb,
            p2,
            rooflights,
        )

    check_groups = [
        [item.to_dict() for item in project.checks],
        p2_checks,
        programme["checks"],
        equipment["checks"],
        rooflight_checks["checks"],
    ]
    counts = _status_counts(check_groups)
    overall_status = (
        "COORDINATION_FAIL"
        if counts["FAIL"]
        else "COORDINATION_OPEN"
        if counts["OPEN"]
        else "COORDINATION_PASS"
    )
    results = {
        "revision": "0.4-I02",
        "date": project.manifest["date"],
        "scenario_id": scenario_id,
        "input_hash": integration_input_hash,
        "overall_status": overall_status,
        "status_counts": counts,
        "selection_or_construction_authority": False,
        "issue_ready": counts["FAIL"] == 0 and counts["OPEN"] == 0,
        "canonical_model_checks": check_groups[0],
        "p2_checks": p2_checks,
        "programme": programme,
        "equipment": equipment,
        "rooflights": rooflight_checks,
        "opening_schedule": opening_schedule,
        "quantity_ledger": quantities,
        "cost_reconciliation": costs,
        "support_alternatives": support,
        "structural_screening": structural,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "compliance.json": {
            key: results[key]
            for key in (
                "revision",
                "date",
                "scenario_id",
                "input_hash",
                "overall_status",
                "status_counts",
                "selection_or_construction_authority",
                "issue_ready",
                "canonical_model_checks",
                "p2_checks",
                "programme",
                "equipment",
                "rooflights",
            )
        },
        "opening_schedule.json": opening_schedule,
        "quantity_ledger.json": quantities,
        "cost_reconciliation.json": costs,
        "support_alternatives.json": support,
    }
    if structural is not None:
        outputs["structural_screening.json"] = structural
    for name, value in outputs.items():
        _write_json(output_dir / name, value)
    evidence = _evidence_markdown(results)
    evidence_path = output_dir / "evidence.md"
    evidence_path.write_text(evidence, encoding="utf-8")

    rooflight_dir = output_dir / "rooflights"
    drawing_revision = rooflights.get("drawing_revision", "R11")
    rooflight_plan_name = (
        f"DH-ARQ-PLN-CUB-001-{drawing_revision}_D054-HALF-CENTRES.svg"
    )
    rooflight_section_name = (
        f"DH-ARQ-SEC-CUB-003-{drawing_revision}_D054-DAYLIGHT.svg"
    )
    generate_rooflight_drawings(
        rooflights,
        rooflight_dir,
        source_path=project.source_paths["rooflights"],
        plan_name=rooflight_plan_name,
        section_name=rooflight_section_name,
    )

    artifact_paths = sorted(
        [
            *(output_dir / name for name in outputs),
            evidence_path,
            rooflight_dir / rooflight_plan_name,
            rooflight_dir / rooflight_section_name,
            rooflight_dir / "compliance.json",
            rooflight_dir / "manifest.json",
        ]
    )
    manifest = {
        "revision": results["revision"],
        "date": results["date"],
        "scenario_id": scenario_id,
        "input_hash": integration_input_hash,
        "source_hashes": source_hashes,
        "generator": "dreamhouse/pipeline.py",
        "overall_status": overall_status,
        "issue_ready": results["issue_ready"],
        "selection_or_construction_authority": False,
        "outputs": [
            {
                "path": path.relative_to(output_dir).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in artifact_paths
        ],
    }
    _write_json(output_dir / "manifest.json", manifest)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="D057_P2_W01")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--skip-structural-screening",
        action="store_true",
        help="Skip the slower E1 numerical screen while retaining geometry coordination.",
    )
    parser.add_argument(
        "--require-issue-ready",
        action="store_true",
        help="Return a nonzero exit code while any declared check remains OPEN or FAIL.",
    )
    arguments = parser.parse_args(argv)
    results = run_pipeline(
        scenario_id=arguments.scenario,
        output_dir=arguments.out,
        include_structural_screening=not arguments.skip_structural_screening,
    )
    print(
        json.dumps(
            {
                "scenario": results["scenario_id"],
                "status": results["overall_status"],
                "checks": results["status_counts"],
                "output": str(arguments.out),
            }
        )
    )
    return 2 if arguments.require_issue_ready and not results["issue_ready"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

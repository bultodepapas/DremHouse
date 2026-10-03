"""Trace the plan's nineteen subphases to this exact generated package.

The build records runtime evidence, not the execution of the test suite or a human sign-off.
"""

from __future__ import annotations

_GATES = [
    ("0.1", [], "Source ownership", ["model.json", "drawing_inventory.json"], ["test_model"]),
    (
        "0.2",
        ["0.1"],
        "Preserved baseline",
        ["changes.json", "model.json"],
        ["test_model", "test_pipeline"],
    ),
    (
        "0.3",
        ["0.1", "0.2"],
        "Current quantities",
        ["openings.json", "quantities.json"],
        ["test_rules"],
    ),
    (
        "1.1",
        ["0.3"],
        "Stable identity and geometry",
        ["model.json", "capabilities.json"],
        ["test_model"],
    ),
    (
        "1.2",
        ["1.1"],
        "Relationships and dependencies",
        ["dependencies.json"],
        ["test_dependencies", "test_family_extension"],
    ),
    ("1.3", ["1.1", "1.2"], "Validated resolver", ["model.json"], ["test_model", "test_migration"]),
    (
        "2.1",
        ["1.3"],
        "Controlled source changes",
        ["changes.json"],
        ["test_migration_cli", "test_pipeline"],
    ),
    (
        "2.2",
        ["1.3"],
        "Rules and geometric coverage",
        ["findings.json", "coverage.json"],
        ["test_rules", "test_disciplines"],
    ),
    (
        "2.3",
        ["2.1", "2.2"],
        "Impact and evidence lifecycle",
        ["finding_lifecycle.json", "dependencies.json", "evidence.json"],
        ["test_dependencies", "test_evidence"],
    ),
    ("3.1", ["2.3"], "Injected drawing consumers", ["drawing_inventory.json"], ["test_drawings"]),
    (
        "3.2",
        ["3.1"],
        "Semantic views and annotations",
        ["view_inventory.json", "anchor_lifecycle.json"],
        ["test_view_contract", "test_view_definitions", "test_drawing_annotations",
         "test_context_annotations", "test_wall_context_annotations", "test_p2_context_annotations",
         "test_native_notes"],
    ),
    (
        "3.3",
        ["3.1", "3.2"],
        "Connected review and saved issues",
        ["window-sections.svg", "viewpoints.json", "index.html"],
        ["test_render", "test_viewpoints", "test_navigation"],
    ),
    (
        "4.1",
        ["3.3"],
        "Complete candidate generation",
        ["model.json", "index.html"],
        ["test_pipeline"],
    ),
    (
        "4.2",
        ["4.1"],
        "Source and rendering invalidation",
        ["dependencies.json"],
        ["test_pipeline", "test_visual", "test_watch"],
    ),
    ("4.3", ["4.1", "4.2"], "Release and recovery", ["review.md"], ["test_publication"]),
    (
        "5.1",
        ["4.3"],
        "Family and operation coverage",
        ["capabilities.json"],
        ["test_family_extension"],
    ),
    (
        "5.2",
        ["5.1"],
        "Stair, wall and cost connections",
        ["stair-sections.svg", "extensions.json", "cost.json"],
        ["test_stair_view", "test_extensions"],
    ),
    (
        "5.3",
        ["5.1"],
        "Service and lifecycle information",
        ["extensions.json", "information_requirements.json", "evidence.json"],
        ["test_extensions", "test_information_requirements", "test_evidence"],
    ),
    (
        "5.4",
        ["5.2", "5.3"],
        "Current consumer rollout",
        ["drawing_inventory.json", "capabilities.json", "viewpoints.json"],
        ["test_drawings", "test_family_extension", "test_pipeline"],
    ),
]


def phase_gate_record(
    snapshot: dict, inventory: dict, drawings: dict, artifact_names: set[str]
) -> dict:
    rows = []
    for identifier, prerequisites, title, artifacts, tests in _GATES:
        missing = sorted(set(artifacts) - artifact_names)
        rows.append(
            {
                "subphase": identifier,
                "depends_on": prerequisites,
                "title": title,
                "runtime_evidence_state": "missing_artifacts" if missing else "generated",
                "artifacts": artifacts,
                "missing_artifacts": missing,
                "acceptance_test_modules": [
                    f"dreamhouse.coordination.tests.{name}" for name in tests
                ],
                "test_execution": "not_run_by_candidate_builder",
                "professional_acceptance": "not_asserted",
            }
        )
    return {
        "schema_version": 1,
        "scenario_id": snapshot["scenario_id"],
        "input_hash": snapshot["input_hash"],
        "model_hash": snapshot["model_hash"],
        "plan": "docs/06_gestion_y_obra/connected_project_coordination_next_step.md",
        "subphases": rows,
        "entity_count": inventory["entity_count"],
        "represented_entity_count": inventory["represented_entity_count"],
        "annotation_coverage": inventory["annotation_coverage"],
        "native_annotation_coverage": drawings.get("annotation_migration", {}),
        "unlocated_entities": sorted(
            k for k, v in snapshot["entities"].items() if v["geometry"]["shape"] == "unresolved"
        ),
        "open_conflicts": snapshot.get("open_conflicts", []),
        "construction_authority": False,
        "scope": "Runtime artifact traceability is separate from test execution, human software review and professional design gates.",
    }


def gate_markdown(record: dict) -> str:
    lines = [
        "# Connected plan gate evidence",
        "",
        f"Scenario: `{record['scenario_id']}`; input: `{record['input_hash']}`.",
        "",
        record["scope"],
        "",
        "| Subphase | Evidence | Runtime status |",
        "| --- | --- | --- |",
    ]
    for row in record["subphases"]:
        links = ", ".join(f"[{name}]({name})" for name in row["artifacts"])
        lines.append(
            f"| {row['subphase']} — {row['title']} | {links} | {row['runtime_evidence_state']} |"
        )
    lines.extend(
        [
            "",
            "See [machine-readable gates](phase_gates.json) for acceptance test modules and dependencies.",
            "",
            f"Unlocated entities: {', '.join(record['unlocated_entities']) or 'none'}.",
            f"Open source conflicts: {', '.join(record['open_conflicts']) or 'none'}.",
            "",
            "Annotation coverage and unsupported native projections remain explicit in [view inventory](view_inventory.json) and [drawing inventory](drawing_inventory.json).",
        ]
    )
    return "\n".join(lines) + "\n"

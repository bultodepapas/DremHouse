"""Compare Great Wall / stair support concepts without selecting a structure."""

from __future__ import annotations

from typing import Any

from .vertical_continuity import evaluate_vertical_continuity


def compare_support_concepts(
    structure: dict[str, Any],
    pb: dict[str, Any],
    p2: dict[str, Any],
    e1_space: dict[str, Any],
) -> dict[str, Any]:
    """Create an auditable alternative matrix from the existing continuity audit."""

    audit = evaluate_vertical_continuity(
        structure,
        pb,
        p2,
        e1_space["vertical_continuity"],
    )
    rejected = [
        {
            "id": item["id"],
            "reasons": item["rejection_reasons"],
        }
        for item in audit["candidates"]
        if not item["geometry_compatible_for_full_height_study"]
    ]
    compatible = audit["compatible_column_ids"]
    alternatives = [
        {
            "id": "SUPPORT-A-STAIR-4",
            "name": "Independent four-column stair-enclosure frame",
            "geometry_status": "PASS",
            "full_height_candidate_ids": compatible,
            "new_rear_columns": audit["new_rear_columns_required"],
            "architectural_conflict_count": 0,
            "advantages": [
                "reuses two current Great Wall column lines",
                "keeps rejected bedroom and glazing lines out of the full-height system",
            ],
            "open_items": [
                "transverse system around the stair portal and discharge door",
                "roof and P2 collectors, bases, fire enclosure, and egress clearances",
            ],
        },
        {
            "id": "SUPPORT-B-GREAT-WALL-6",
            "name": "Extend all six Great Wall column hypotheses to roof level",
            "geometry_status": "FAIL",
            "full_height_candidate_ids": [
                item["id"]
                for item in audit["candidates"]
                if item["source"] == "existing_great_wall_column"
            ],
            "new_rear_columns": 0,
            "architectural_conflict_count": len(rejected),
            "rejected_lines": rejected,
            "advantages": ["minimizes nominal new Great Wall column locations"],
            "open_items": [
                "four conflicts with bedrooms, glazing, or non-corner locations",
                "complete orthogonal lateral path and roof interfaces",
            ],
        },
        {
            "id": "SUPPORT-C-HYBRID-REAR",
            "name": "Four compatible stair lines plus an independent rear support study",
            "geometry_status": "OPEN",
            "full_height_candidate_ids": compatible,
            "new_rear_columns": audit["new_rear_columns_required"],
            "architectural_conflict_count": 0,
            "advantages": [
                "retains the clean Great Wall finish outside the stair zone",
                "allows rear load-path options to be tested separately",
            ],
            "open_items": [
                "rear support locations are not defined in the active architectural model",
                "rear windows, exterior doors, foundations, and roof framing",
            ],
        },
        {
            "id": "SUPPORT-D-FINISH-ONLY",
            "name": "Great Wall as finish only; structure fully independent",
            "geometry_status": "OPEN",
            "full_height_candidate_ids": [],
            "new_rear_columns": None,
            "architectural_conflict_count": 0,
            "advantages": ["maximum separation of finish and primary structure"],
            "open_items": [
                "no independent structural grid has been modeled",
                "floor transfer, lateral system, roof support, foundations, and cost",
            ],
        },
    ]
    return {
        "revision": "0.4-I01-SUPPORT-OPTIONS",
        "status": "comparison only; no structural system selected",
        "source_audit": audit,
        "alternatives": alternatives,
        "screening_preference": "SUPPORT-A-STAIR-4",
        "preference_status": "study preference only; professional structural design required",
        "selection_or_construction_authority": False,
    }

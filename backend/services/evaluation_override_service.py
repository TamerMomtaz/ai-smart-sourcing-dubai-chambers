from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from database import supabase


# Dimension-to-column mapping for chamber_evaluations
DIMENSION_COLUMN_MAP = {
    "relevance": "relevance_score",
    "feasibility": "feasibility_score",
    "compliance": "compliance_score",
    "sector_alignment": "sector_alignment_score",
    "novelty": "novelty_score",
    "composite": "composite_score",
}

VALID_DIMENSIONS = set(DIMENSION_COLUMN_MAP.keys())


def create_override(
    evaluation_id: UUID,
    dimension: str,
    human_adjusted_score: float,
    override_reason: str,
    overridden_by: UUID,
) -> Optional[Dict[str, Any]]:
    """
    Create a human override for an AI evaluation dimension score.

    Steps:
    1. Fetch current evaluation to get the original AI score
    2. Insert override record into chamber_evaluation_overrides
    3. Update the evaluation's score for that dimension
    4. Recalculate composite if a non-composite dimension changed
    5. Return the updated evaluation
    """
    if dimension not in VALID_DIMENSIONS:
        return None

    # 1. Fetch the current evaluation
    eval_response = (
        supabase.table("chamber_evaluations")
        .select("*")
        .eq("id", str(evaluation_id))
        .maybe_single()
        .execute()
    )
    if not eval_response.data:
        return None

    evaluation = eval_response.data
    score_column = DIMENSION_COLUMN_MAP[dimension]
    ai_original_score = evaluation.get(score_column)

    if ai_original_score is None:
        return None

    # 2. Insert override record
    override_payload = {
        "evaluation_id": str(evaluation_id),
        "dimension": dimension,
        "ai_original_score": float(ai_original_score),
        "human_adjusted_score": float(human_adjusted_score),
        "override_reason": override_reason,
        "overridden_by": str(overridden_by),
    }

    override_response = (
        supabase.table("chamber_evaluation_overrides")
        .insert(override_payload)
        .execute()
    )
    if not override_response.data:
        return None

    # 3. Update the evaluation's score for the dimension
    updates = {
        score_column: float(human_adjusted_score),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # 4. Recalculate composite if a non-composite dimension changed
    if dimension != "composite":
        scores = {
            "relevance": float(evaluation.get("relevance_score", 0)),
            "feasibility": float(evaluation.get("feasibility_score", 0)),
            "sector_alignment": float(evaluation.get("sector_alignment_score", 0)),
            "compliance": float(evaluation.get("compliance_score", 0)),
            "novelty": float(evaluation.get("novelty_score") or 0),
        }
        # Apply the override to the recalculation
        scores[dimension] = float(human_adjusted_score)
        # Use default weights: relevance 25%, feasibility 25%, compliance 20%, sector 15%, novelty 15%
        weights = {
            "relevance": 0.25,
            "feasibility": 0.25,
            "compliance": 0.20,
            "sector_alignment": 0.15,
            "novelty": 0.15,
        }
        composite = sum(scores[d] * weights[d] for d in weights)
        updates["composite_score"] = round(composite, 2)

    update_response = (
        supabase.table("chamber_evaluations")
        .update(updates)
        .eq("id", str(evaluation_id))
        .execute()
    )

    if not update_response.data:
        return None

    return update_response.data[0]


def list_overrides(
    evaluation_id: UUID,
) -> List[Dict[str, Any]]:
    """
    List all overrides for a given evaluation, newest first.
    """
    response = (
        supabase.table("chamber_evaluation_overrides")
        .select("*")
        .eq("evaluation_id", str(evaluation_id))
        .order("created_at", desc=True)
        .execute()
    )
    return response.data if response.data else []

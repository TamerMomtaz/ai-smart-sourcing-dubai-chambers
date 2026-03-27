"""Public stats endpoint — aggregate counts only, no auth required."""

from fastapi import APIRouter, HTTPException, status
import logging

from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Public Stats"])


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Get public aggregate stats (no auth required)",
)
async def get_public_stats():
    """Returns only aggregate counts — no sensitive or per-user data."""
    try:
        # Total evaluated proposals
        proposals_result = supabase.table("chamber_proposals").select(
            "id, status", count="exact"
        ).execute()
        proposals = proposals_result.data or []
        evaluated = sum(
            1 for p in proposals
            if p.get("status") in (
                "evaluated", "approved", "rejected",
                "shortlisted", "under_review", "needs_improvement",
            )
        )

        # AI interactions aggregate
        interactions_result = supabase.table("chamber_ai_interactions").select(
            "operation_type, latency_ms, cost_usd"
        ).execute()
        interactions = interactions_result.data or []

        total_cost = sum(float(i.get("cost_usd", 0) or 0) for i in interactions)
        total_ai_ms = sum(i.get("latency_ms", 0) or 0 for i in interactions)

        # Manual hours saved
        manual_hours_map = {
            "proposal_evaluation": 3.0,
            "compliance_check": 8.0,
            "trend_analysis": 16.0,
            "hallucination_check": 2.0,
            "evaluation": 3.0,
        }
        total_manual_hours = sum(
            manual_hours_map.get(i.get("operation_type", ""), 0)
            for i in interactions
        )
        total_ai_hours = total_ai_ms / 3_600_000
        speed_multiplier = round(
            total_manual_hours / max(total_ai_hours, 0.001), 1
        )

        # Hallucination shield checks
        shield_checks = sum(
            1 for i in interactions
            if i.get("operation_type") == "hallucination_check"
        )

        return {
            "evaluated": evaluated,
            "speed_multiplier": int(speed_multiplier),
            "total_cost_usd": round(total_cost, 2),
            "shield_checks": shield_checks,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching public stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )

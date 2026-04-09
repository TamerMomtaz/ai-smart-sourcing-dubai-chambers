from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-team", tags=["AI Team"])


@router.get("/stats")
async def get_ai_team_stats(current_user: Dict = Depends(get_current_user)):
    """Return live counts for each AI specialist's stat card."""
    try:
        # SCOUT — sourcing cases count
        sc_resp = supabase.table("chamber_sourcing_cases").select("id", count="exact").execute()
        sourcing_cases_count = sc_resp.count if sc_resp.count is not None else len(sc_resp.data or [])

        # MATCH — vendors count
        v_resp = supabase.table("chamber_vendors").select("id", count="exact").execute()
        vendors_count = v_resp.count if v_resp.count is not None else len(v_resp.data or [])

        # SENTINEL — gate checks (proposals where compliance_gate_status is not 'pending')
        gate_resp = (
            supabase.table("chamber_proposals")
            .select("id", count="exact")
            .neq("compliance_gate_status", "pending")
            .not_.is_("compliance_gate_status", "null")
            .execute()
        )
        gate_checks_count = gate_resp.count if gate_resp.count is not None else len(gate_resp.data or [])

        # EVALUATOR — evaluations count + avg composite score
        eval_resp = supabase.table("chamber_evaluations").select("id, composite_score", count="exact").execute()
        evaluations_count = eval_resp.count if eval_resp.count is not None else len(eval_resp.data or [])
        eval_data = eval_resp.data or []
        scores = [e["composite_score"] for e in eval_data if e.get("composite_score") is not None]
        avg_composite_score = round(sum(scores) / len(scores), 1) if scores else 0

        # VERIFIER — hallucination shield checks count
        shield_resp = supabase.table("chamber_hallucination_checks").select("id", count="exact").execute()
        shield_checks_count = shield_resp.count if shield_resp.count is not None else len(shield_resp.data or [])

        # GUARDIAN — ai interactions count + integrity hash chain check
        ai_resp = supabase.table("chamber_ai_interactions").select("id, integrity_hash", count="exact").execute()
        ai_interactions_count = ai_resp.count if ai_resp.count is not None else len(ai_resp.data or [])
        ai_data = ai_resp.data or []
        integrity_verified = all(
            row.get("integrity_hash") not in (None, "")
            for row in ai_data
        ) if ai_data else True

        # STRATEGIST — trend analyses count + board briefs generated
        trend_resp = supabase.table("chamber_trend_analyses").select("id", count="exact").execute()
        trend_analyses_count = trend_resp.count if trend_resp.count is not None else len(trend_resp.data or [])

        board_briefs_resp = (
            supabase.table("chamber_ai_interactions")
            .select("id", count="exact")
            .eq("operation_type", "trend_analysis")
            .execute()
        )
        board_briefs_generated = board_briefs_resp.count if board_briefs_resp.count is not None else len(board_briefs_resp.data or [])

        return {
            "scout": {"sourcing_cases_count": sourcing_cases_count},
            "match": {"vendors_count": vendors_count},
            "sentinel": {"gate_checks_count": gate_checks_count},
            "evaluator": {
                "evaluations_count": evaluations_count,
                "avg_composite_score": avg_composite_score,
            },
            "verifier": {"shield_checks_count": shield_checks_count},
            "guardian": {
                "ai_interactions_count": ai_interactions_count,
                "integrity_verified": integrity_verified,
            },
            "strategist": {
                "trend_analyses_count": trend_analyses_count,
                "board_briefs_generated": board_briefs_generated,
            },
        }
    except Exception as e:
        logger.error(f"Error fetching AI team stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to fetch AI team stats", "code": "AI_TEAM_STATS_ERROR"},
        )

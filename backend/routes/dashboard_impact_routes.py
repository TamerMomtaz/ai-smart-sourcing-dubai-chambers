"""σI Impact Meter — live operational impact calculator.

Calculates real-time metrics from chamber_ai_interactions to show
how much time and human effort AI has saved on the platform.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Impact"])

# Conservative manual time estimates per operation (hours)
MANUAL_HOURS = {
    "proposal_evaluation": 3.0,
    "compliance_check": 8.0,
    "trend_analysis": 16.0,
    "hallucination_check": 2.0,
    "evaluation": 3.0,
}

_OP_DESCRIPTIONS = {
    "proposal_evaluation": "AI evaluation of proposals across 4 scoring dimensions",
    "compliance_check": "DESC compliance audit against DESC ISR V3 Controls, DESC AI Security Policy (5-Phase Lifecycle), DESC CSP Standards (ISO/IEC 27001, ISO/IEC 27017, CSA CCM v4.0.5)",
    "trend_analysis": "Market intelligence report with sector analysis and recommendations",
    "hallucination_check": "Source grounding verification of AI evaluation claims",
    "evaluation": "AI evaluation of proposals across 4 scoring dimensions",
}

_METHODOLOGY_ESTIMATES = {
    "proposal_evaluation": "3 hours \u2014 Read proposal, score 4 dimensions, write detailed reasoning with evidence",
    "compliance_check": "8 hours \u2014 Review against 3 DESC frameworks (DESC ISR V3 Controls, DESC AI Security Policy, DESC CSP Standards), document per-control findings",
    "trend_analysis": "16 hours \u2014 Aggregate cross-proposal data, sector breakdown, D33 alignment, write 8+ recommendations",
    "hallucination_check": "2 hours \u2014 Cross-reference each AI claim against source documents, classify grounding",
}


@router.get(
    "/impact",
    status_code=status.HTTP_200_OK,
    summary="Get live impact metrics from AI operations",
)
async def get_dashboard_impact(
    current_user: dict = Depends(get_current_user),
):
    """Returns live impact metrics calculated from chamber_ai_interactions."""
    try:
        result = supabase.table("chamber_ai_interactions").select(
            "operation_type, latency_ms, cost_usd, intelligence_units, created_at"
        ).execute()

        interactions = result.data or []

        # Aggregate by operation type
        ops_count = {}
        total_ai_ms = 0
        total_cost = 0.0
        total_iu = 0.0

        for i in interactions:
            op = i.get("operation_type", "unknown")
            ops_count[op] = ops_count.get(op, 0) + 1
            total_ai_ms += i.get("latency_ms", 0) or 0
            total_cost += float(i.get("cost_usd", 0) or 0)
            total_iu += float(i.get("intelligence_units", 0) or 0)

        # Calculate manual hours saved
        total_manual_hours = 0.0
        breakdown = []
        for op_type, count in ops_count.items():
            manual_hrs = MANUAL_HOURS.get(op_type, 0)
            saved = count * manual_hrs
            total_manual_hours += saved
            if manual_hrs > 0:
                breakdown.append({
                    "operation": op_type,
                    "count": count,
                    "manual_hours_each": manual_hrs,
                    "total_hours_saved": round(saved, 1),
                    "description": _OP_DESCRIPTIONS.get(op_type, op_type),
                })

        # Convert to human-readable units
        working_days_saved = round(total_manual_hours / 8, 1)
        working_months_saved = round(total_manual_hours / (8 * 22), 1)
        ai_minutes = round(total_ai_ms / 60000, 1)
        total_ai_hours = total_ai_ms / 3_600_000  # ms → hours
        speed_multiplier = round(total_manual_hours / max(total_ai_hours, 0.001), 1)

        # People equivalent based on elapsed working days
        days_elapsed = 1
        analysts_equivalent = 0.0

        first = supabase.table("chamber_ai_interactions").select(
            "created_at"
        ).order("created_at").limit(1).execute()

        if first.data:
            first_date = datetime.fromisoformat(
                first.data[0]["created_at"].replace("Z", "+00:00")
            )
            days_elapsed = max((datetime.now(timezone.utc) - first_date).days, 1)
            working_days_elapsed = max(days_elapsed * 5 / 7, 1)
            analysts_equivalent = round(working_days_saved / working_days_elapsed, 1)

        return {
            "time_saved": {
                "total_hours": round(total_manual_hours, 1),
                "working_days": working_days_saved,
                "working_months": working_months_saved,
                "analysts_equivalent": analysts_equivalent,
                "period_days": days_elapsed,
            },
            "ai_performance": {
                "total_operations": len(interactions),
                "ai_minutes": ai_minutes,
                "total_cost_usd": round(total_cost, 2),
                "total_iu": round(total_iu, 1),
                "speed_multiplier": int(speed_multiplier),
                "cost_per_operation": round(
                    total_cost / max(len(interactions), 1), 4
                ),
            },
            "breakdown": sorted(
                breakdown, key=lambda x: x["total_hours_saved"], reverse=True
            ),
            "methodology": {
                "note": "Manual time estimates based on industry benchmarks for procurement analysis tasks",
                "estimates": _METHODOLOGY_ESTIMATES,
                "assumptions": "Based on 8-hour working days, 22 working days per month. Speed multiplier = manual hours / AI hours.",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating impact metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )


@router.get(
    "/impact/timeline",
    status_code=status.HTTP_200_OK,
    summary="Get daily impact accumulation for sparkline chart",
)
async def get_impact_timeline(
    current_user: dict = Depends(get_current_user),
):
    """Returns cumulative hours saved per day for a sparkline chart."""
    try:
        result = supabase.table("chamber_ai_interactions").select(
            "operation_type, created_at"
        ).order("created_at").execute()

        interactions = result.data or []

        # Group by date
        daily = {}
        for i in interactions:
            op = i.get("operation_type", "unknown")
            created = i.get("created_at", "")
            if not created:
                continue
            date_str = created[:10]  # YYYY-MM-DD
            if date_str not in daily:
                daily[date_str] = 0.0
            daily[date_str] += MANUAL_HOURS.get(op, 0)

        # Build cumulative timeline
        timeline = []
        cumulative = 0.0
        for date_str in sorted(daily.keys()):
            hours = daily[date_str]
            cumulative += hours
            timeline.append({
                "date": date_str,
                "daily_hours_saved": round(hours, 1),
                "cumulative_hours": round(cumulative, 1),
            })

        return {"timeline": timeline}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching impact timeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )

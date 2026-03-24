from fastapi import APIRouter, Depends
from typing import Dict
from datetime import datetime
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Board Brief"])


@router.get("/board-brief/data")
async def get_board_brief_data(current_user: Dict = Depends(get_current_user)):
    """Return all data needed for the Executive Board Brief report."""

    # Fetch all relevant tables
    proposals = supabase.table("chamber_proposals").select("*").execute()
    evaluations = supabase.table("chamber_evaluations").select("*").execute()
    audits = supabase.table("chamber_compliance_audits").select("*").execute()
    shield = supabase.table("chamber_hallucination_checks").select("*").execute()
    interactions = supabase.table("chamber_ai_interactions").select("*").execute()
    trends = supabase.table("chamber_trend_analyses").select("*").execute()

    all_proposals = proposals.data or []
    all_evals = evaluations.data or []
    all_audits = audits.data or []
    all_shield = shield.data or []
    all_interactions = interactions.data or []
    all_trends = trends.data or []

    # Evaluated proposals have a composite_score
    evaluated = [p for p in all_proposals if p.get("composite_score") is not None]
    avg_score = round(
        sum(p["composite_score"] for p in evaluated) / max(len(evaluated), 1), 1
    )

    # Top 5 proposals by composite score
    top_proposals = sorted(
        evaluated, key=lambda x: x.get("composite_score", 0), reverse=True
    )[:5]

    # Bottom 3 compliance concerns
    compliance_concerns = sorted(
        evaluated, key=lambda x: x.get("compliance_score", 100)
    )[:3]

    # Sector breakdown
    sectors: Dict[str, Dict] = {}
    for p in evaluated:
        s = p.get("sector", "Unknown")
        if s not in sectors:
            sectors[s] = {"count": 0, "total_score": 0}
        sectors[s]["count"] += 1
        sectors[s]["total_score"] += p.get("composite_score", 0)
    sector_breakdown = [
        {
            "sector": k,
            "count": v["count"],
            "avg_score": round(v["total_score"] / v["count"], 1),
        }
        for k, v in sectors.items()
    ]

    # AI operations summary
    total_cost = sum(i.get("cost_usd", 0) or 0 for i in all_interactions)
    total_iu = sum(i.get("intelligence_units", 0) or 0 for i in all_interactions)
    total_energy = sum(i.get("energy_kwh", 0) or 0 for i in all_interactions)

    # Shield aggregate
    avg_grounding = round(
        sum(float(s.get("grounding_score", 0) or 0) for s in all_shield)
        / max(len(all_shield), 1),
        1,
    )

    # Model usage breakdown
    model_usage: Dict[str, int] = {}
    for i in all_interactions:
        model = i.get("model_name") or i.get("model") or "unknown"
        model_usage[model] = model_usage.get(model, 0) + 1

    # Operations count for hours-saved calculation
    ops_count: Dict[str, int] = {}
    for i in all_interactions:
        op = i.get("operation_type", "unknown")
        ops_count[op] = ops_count.get(op, 0) + 1

    MANUAL_HOURS = {
        "proposal_evaluation": 3.0,
        "evaluation": 3.0,
        "compliance_check": 8.0,
        "trend_analysis": 16.0,
        "hallucination_check": 2.0,
    }
    hours_saved = sum(
        count * MANUAL_HOURS.get(op, 0) for op, count in ops_count.items()
    )

    # Period covered
    created_dates = [p.get("created_at", "") for p in all_proposals if p.get("created_at")]
    period_from = min(created_dates, default="")
    period_to = max(created_dates, default="")

    # Speed multiplier
    total_ai_ms = sum(i.get("latency_ms", 0) or 0 for i in all_interactions)
    total_ai_hours = total_ai_ms / 3_600_000  # ms → hours
    speed_multiplier = round(hours_saved / max(total_ai_hours, 0.001), 1)

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "period": {
            "from": period_from,
            "to": period_to,
        },
        "summary": {
            "total_proposals": len(all_proposals),
            "evaluated": len(evaluated),
            "pending": len(all_proposals) - len(evaluated),
            "avg_score": avg_score,
            "compliance_audits": len(all_audits),
            "trend_reports": len(all_trends),
        },
        "impact": {
            "hours_saved": round(hours_saved, 1),
            "speed_multiplier": speed_multiplier,
            "total_cost_usd": round(total_cost, 2),
            "total_iu": round(total_iu, 1),
            "energy_kwh": round(total_energy, 4),
            "operations": len(all_interactions),
        },
        "top_proposals": [
            {
                "title": p.get("title", "Untitled"),
                "sector": p.get("sector", ""),
                "composite_score": p.get("composite_score"),
                "compliance_score": p.get("compliance_score"),
            }
            for p in top_proposals
        ],
        "compliance_concerns": [
            {
                "title": p.get("title", "Untitled"),
                "compliance_score": p.get("compliance_score"),
                "sector": p.get("sector", ""),
            }
            for p in compliance_concerns
        ],
        "sector_breakdown": sorted(
            sector_breakdown, key=lambda x: x["avg_score"], reverse=True
        ),
        "shield": {
            "avg_grounding": avg_grounding,
            "total_checks": len(all_shield),
            "risk_distribution": {
                "low": len(
                    [s for s in all_shield if s.get("hallucination_risk") == "low"]
                ),
                "medium": len(
                    [s for s in all_shield if s.get("hallucination_risk") == "medium"]
                ),
                "high": len(
                    [s for s in all_shield if s.get("hallucination_risk") == "high"]
                ),
            },
        },
        "model_usage": model_usage,
        "recommendations": [
            {
                "title": p.get("title", "Untitled"),
                "sector": p.get("sector", ""),
                "composite_score": p.get("composite_score"),
            }
            for p in top_proposals[:3]
        ],
    }

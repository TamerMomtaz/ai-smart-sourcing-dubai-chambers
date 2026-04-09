"""Channel Analytics — volume, conversion rates, and performance metrics by intake source channel."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Channel Analytics"])

ALLOWED_ROLES = {"admin", "analyst", "executive"}

CHANNELS = [
    "manual",
    "business_in_dubai",
    "expand_north_star",
    "ignyte",
    "partner_referral",
    "email",
    "api",
]

ACTIVE_STATUSES = {"open", "matching", "evaluating"}


@router.get(
    "/channel-analytics",
    status_code=status.HTTP_200_OK,
    summary="Get channel analytics for sourcing cases",
)
async def get_channel_analytics(
    current_user: dict = Depends(get_current_user),
):
    """Aggregates sourcing case data by source_channel with conversion and performance metrics."""
    user_role = current_user.get("role", "vendor")
    if user_role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Admin, analyst, or executive role required",
                "code": 403,
            },
        )

    try:
        # Fetch sourcing cases
        cases_result = supabase.table("chamber_sourcing_cases").select(
            "id, source_channel, status, created_at, closed_at"
        ).execute()
        cases = cases_result.data or []

        # Fetch proposals linked to sourcing cases
        proposals_result = supabase.table("chamber_proposals").select(
            "id, sourcing_case_id, composite_score"
        ).not_.is_("sourcing_case_id", "null").execute()
        proposals = proposals_result.data or []

        # Build proposal lookup by sourcing_case_id
        proposals_by_case = {}
        for p in proposals:
            cid = p.get("sourcing_case_id")
            if cid:
                proposals_by_case.setdefault(cid, []).append(p)

        # Group cases by channel
        cases_by_channel = {}
        for c in cases:
            ch = c.get("source_channel") or "manual"
            cases_by_channel.setdefault(ch, []).append(c)

        # Build per-channel metrics
        channels = []
        for channel in CHANNELS:
            channel_cases = cases_by_channel.get(channel, [])
            total = len(channel_cases)
            active = sum(1 for c in channel_cases if c.get("status") in ACTIVE_STATUSES)
            completed = sum(1 for c in channel_cases if c.get("status") == "completed")
            conversion_rate = round((completed / total) * 100, 1) if total > 0 else 0.0

            # Avg time to completion (days)
            completion_days = []
            for c in channel_cases:
                if c.get("status") == "completed" and c.get("created_at") and c.get("closed_at"):
                    try:
                        created = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
                        closed = datetime.fromisoformat(c["closed_at"].replace("Z", "+00:00"))
                        delta = (closed - created).total_seconds() / 86400
                        if delta >= 0:
                            completion_days.append(delta)
                    except (ValueError, TypeError):
                        continue

            avg_time = round(sum(completion_days) / len(completion_days), 1) if completion_days else None

            # Linked proposals and avg evaluation score
            linked_proposals = 0
            scores = []
            for c in channel_cases:
                case_proposals = proposals_by_case.get(c["id"], [])
                linked_proposals += len(case_proposals)
                for p in case_proposals:
                    if p.get("composite_score") is not None:
                        scores.append(float(p["composite_score"]))

            avg_score = round(sum(scores) / len(scores), 1) if scores else None

            channels.append({
                "channel": channel,
                "total_cases": total,
                "active_cases": active,
                "completed_cases": completed,
                "conversion_rate": conversion_rate,
                "avg_time_to_completion": avg_time,
                "linked_proposals": linked_proposals,
                "avg_evaluation_score": avg_score,
            })

        # Summary metrics
        total_signals = sum(ch["total_cases"] for ch in channels)
        top_channel = max(channels, key=lambda ch: ch["total_cases"])["channel"] if total_signals > 0 else None
        converting = [ch for ch in channels if ch["total_cases"] > 0]
        best_converting = max(converting, key=lambda ch: ch["conversion_rate"])["channel"] if converting else None

        return {
            "channels": channels,
            "top_channel": top_channel,
            "best_converting": best_converting,
            "total_signals": total_signals,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating channel analytics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )

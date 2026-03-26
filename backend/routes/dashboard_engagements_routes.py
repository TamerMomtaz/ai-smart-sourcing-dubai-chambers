"""Dashboard engagements endpoint - pilot & engagement outcome metrics."""

from fastapi import APIRouter, Depends, HTTPException, status
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Engagements"])


@router.get(
    "/engagements",
    status_code=status.HTTP_200_OK,
    summary="Get engagement outcome metrics for the dashboard",
)
async def get_dashboard_engagements(
    current_user: dict = Depends(get_current_user),
):
    """Returns pilot & engagement outcome aggregates and recent engagements."""
    try:
        user_role = current_user.get("role", "vendor")
        user_id = current_user.get("id")

        # Fetch all engagements (vendor-scoped for vendors)
        query = supabase.table("chamber_vendor_engagements").select(
            "id, vendor_id, engagement_title, engagement_type, outcome, "
            "delivery_rating, start_date, end_date, created_at"
        )
        if user_role == "vendor":
            query = query.eq("vendor_id", str(user_id))

        result = query.execute()
        engagements = result.data or []

        # --- Metric cards ---
        total = len(engagements)
        active_pilots = sum(1 for e in engagements if e.get("outcome") == "ongoing")
        completed = sum(
            1 for e in engagements if e.get("outcome") in ("completed", "exceeded")
        )

        ratings = [
            float(e["delivery_rating"])
            for e in engagements
            if e.get("delivery_rating") is not None
        ]
        avg_delivery_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

        success_rate = round(completed / total * 100, 1) if total > 0 else 0

        # --- Outcome distribution ---
        outcome_labels = ["exceeded", "completed", "ongoing", "partial", "failed", "cancelled"]
        distribution = {label: 0 for label in outcome_labels}
        for e in engagements:
            outcome = e.get("outcome", "")
            if outcome in distribution:
                distribution[outcome] += 1

        # --- Recent engagements (latest 5) with vendor name ---
        recent_query = supabase.table("chamber_vendor_engagements").select(
            "id, vendor_id, engagement_title, engagement_type, outcome, "
            "start_date, end_date, created_at"
        )
        if user_role == "vendor":
            recent_query = recent_query.eq("vendor_id", str(user_id))

        recent_result = recent_query.order(
            "created_at", desc=True
        ).limit(5).execute()
        recent = recent_result.data or []

        # Resolve vendor names
        vendor_ids = list({r["vendor_id"] for r in recent if r.get("vendor_id")})
        vendor_names = {}
        if vendor_ids:
            vendors_result = supabase.table("chamber_vendors").select(
                "id, name"
            ).in_("id", vendor_ids).execute()
            for v in vendors_result.data or []:
                vendor_names[v["id"]] = v.get("name", "Unknown")

        recent_engagements = [
            {
                "id": r["id"],
                "vendor_name": vendor_names.get(r.get("vendor_id"), "Unknown"),
                "engagement_title": r.get("engagement_title"),
                "engagement_type": r.get("engagement_type"),
                "outcome": r.get("outcome"),
                "date": r.get("end_date") or r.get("start_date") or r.get("created_at"),
            }
            for r in recent
        ]

        return {
            "metrics": {
                "active_pilots": active_pilots,
                "completed_engagements": completed,
                "avg_delivery_rating": avg_delivery_rating,
                "success_rate": success_rate,
                "total": total,
            },
            "distribution": distribution,
            "recent_engagements": recent_engagements,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dashboard engagements: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )

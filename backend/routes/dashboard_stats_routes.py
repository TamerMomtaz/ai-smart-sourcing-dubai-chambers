"""Dashboard stats endpoint - returns real aggregate data for all roles."""

from fastapi import APIRouter, Depends, HTTPException, status
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Stats"])


@router.get(
    "/stats",
    status_code=status.HTTP_200_OK,
    summary="Get dashboard statistics from real data",
)
async def get_dashboard_stats(
    current_user: dict = Depends(get_current_user),
):
    """Returns aggregate dashboard stats. Available to all authenticated users."""
    try:
        user_role = current_user.get("role", "vendor")
        user_id = current_user.get("id")

        # Total proposals (role-scoped for vendors)
        proposals_query = supabase.table("chamber_proposals").select(
            "id, status, composite_score", count="exact"
        )
        if user_role == "vendor":
            proposals_query = proposals_query.eq("submitter_id", str(user_id))

        proposals_result = proposals_query.execute()
        proposals = proposals_result.data or []
        total_proposals = proposals_result.count or len(proposals)

        # Count by status
        evaluated_count = 0
        pending_count = 0
        approved_count = 0
        rejected_count = 0
        score_sum = 0.0
        score_count = 0

        for p in proposals:
            s = p.get("status", "")
            if s in ("evaluated", "approved", "rejected"):
                evaluated_count += 1
            if s == "queued":
                pending_count += 1
            if s == "approved":
                approved_count += 1
            if s == "rejected":
                rejected_count += 1
            cs = p.get("composite_score")
            if cs is not None:
                score_sum += float(cs)
                score_count += 1

        average_score = round(score_sum / score_count, 1) if score_count > 0 else None

        # Compliance audits count
        audits_query = supabase.table("chamber_compliance_audits").select(
            "id", count="exact"
        )
        if user_role == "vendor":
            # For vendors, count audits on their proposals
            vendor_proposal_ids = [p["id"] for p in proposals]
            if vendor_proposal_ids:
                audits_query = audits_query.in_("proposal_id", vendor_proposal_ids)
            else:
                audits_query = None

        if audits_query:
            audits_result = audits_query.execute()
            compliance_audits_count = audits_result.count or len(audits_result.data or [])
        else:
            compliance_audits_count = 0

        # Recent proposals (up to 5)
        recent_query = supabase.table("chamber_proposals").select(
            "id, title, sector, status, submission_date, composite_score"
        )
        if user_role == "vendor":
            recent_query = recent_query.eq("submitter_id", str(user_id))
        recent_result = recent_query.order(
            "submission_date", desc=True
        ).limit(5).execute()

        return {
            "total_proposals": total_proposals,
            "evaluated": evaluated_count,
            "pending_evaluation": pending_count,
            "approved": approved_count,
            "rejected": rejected_count,
            "compliance_audits": compliance_audits_count,
            "average_score": average_score,
            "recent_proposals": recent_result.data or [],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )

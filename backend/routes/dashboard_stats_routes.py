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
        shortlisted_count = 0
        score_sum = 0.0
        score_count = 0

        for p in proposals:
            s = p.get("status", "")
            if s in ("evaluated", "approved", "rejected", "shortlisted", "under_review", "needs_improvement"):
                evaluated_count += 1
            if s == "queued":
                pending_count += 1
            if s == "approved":
                approved_count += 1
            if s == "rejected":
                rejected_count += 1
            if s == "shortlisted":
                shortlisted_count += 1
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
            "shortlisted": shortlisted_count,
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


@router.get(
    "/vendor-summary",
    status_code=status.HTTP_200_OK,
    summary="Get vendor-specific dashboard summary",
)
async def get_vendor_dashboard_summary(
    current_user: dict = Depends(get_current_user),
):
    """Returns vendor-specific stats: proposal count, vScore, latest evaluation."""
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role", "vendor")

        if user_role not in ("vendor", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Vendor role required", "code": 403},
            )

        # Proposal count for this vendor
        proposals_result = supabase.table("chamber_proposals").select(
            "id, status, composite_score, evaluation_timestamp, updated_at",
            count="exact",
        ).eq("submitter_id", str(user_id)).execute()

        proposals = proposals_result.data or []
        proposal_count = proposals_result.count or len(proposals)

        # Status breakdown
        status_counts = {}
        for p in proposals:
            s = p.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1

        # Latest evaluated proposal
        latest_evaluation = None
        evaluated_proposals = [
            p for p in proposals
            if p.get("composite_score") is not None
        ]
        if evaluated_proposals:
            evaluated_proposals.sort(
                key=lambda x: x.get("evaluation_timestamp") or x.get("updated_at") or "",
                reverse=True,
            )
            latest = evaluated_proposals[0]
            # Get full evaluation details
            eval_result = supabase.table("chamber_evaluations").select(
                "composite_score, relevance_score, feasibility_score, sector_alignment_score, compliance_score, evaluated_at, summary_en"
            ).eq("proposal_id", str(latest["id"])).order("evaluated_at", desc=True).limit(1).execute()

            if eval_result.data:
                ev = eval_result.data[0]
                latest_evaluation = {
                    "proposal_id": latest["id"],
                    "composite_score": float(ev["composite_score"]) if ev.get("composite_score") else None,
                    "relevance_score": float(ev["relevance_score"]) if ev.get("relevance_score") else None,
                    "feasibility_score": float(ev["feasibility_score"]) if ev.get("feasibility_score") else None,
                    "sector_alignment_score": float(ev["sector_alignment_score"]) if ev.get("sector_alignment_score") else None,
                    "compliance_score": float(ev["compliance_score"]) if ev.get("compliance_score") else None,
                    "evaluated_at": ev.get("evaluated_at"),
                    "summary": ev.get("summary_en"),
                }

        # vScore summary - fetch from vendor intelligence
        vscore_data = None
        try:
            vendor_result = supabase.table("chamber_vendors").select(
                "id, name, average_compliance_score, submission_history_count, is_desc_approved"
            ).eq("id", str(user_id)).maybe_single().execute()

            if vendor_result.data:
                v = vendor_result.data
                vscore_data = {
                    "vendor_id": v["id"],
                    "vendor_name": v.get("name"),
                    "average_compliance_score": float(v["average_compliance_score"]) if v.get("average_compliance_score") else None,
                    "submission_count": v.get("submission_history_count", 0),
                    "is_desc_approved": v.get("is_desc_approved", False),
                }
        except Exception:
            pass

        return {
            "proposal_count": proposal_count,
            "status_counts": status_counts,
            "latest_evaluation": latest_evaluation,
            "vscore": vscore_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching vendor dashboard summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )

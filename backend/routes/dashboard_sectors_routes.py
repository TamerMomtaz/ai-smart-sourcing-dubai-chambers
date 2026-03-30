"""Dashboard sector intelligence endpoint - aggregates proposals by sector."""

from fastapi import APIRouter, Depends, HTTPException, status
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Sectors"])


@router.get(
    "/sectors",
    status_code=status.HTTP_200_OK,
    summary="Get sector intelligence aggregates",
)
async def get_dashboard_sectors(
    current_user: dict = Depends(get_current_user),
):
    """Returns innovation pipeline health by sector with proposal and vendor metrics."""
    try:
        # Fetch all proposals with scores and status
        proposals_result = supabase.table("chamber_proposals").select(
            "id, sector, composite_score, status, submitter_id"
        ).execute()
        proposals = proposals_result.data or []

        # Fetch all vendors with vScore data
        vendors_result = supabase.table("chamber_vendors").select(
            "id, average_compliance_score, is_desc_approved, vscore_tier"
        ).execute()
        vendors = vendors_result.data or []

        # Build vendor lookup by id
        vendor_map = {}
        for v in vendors:
            vendor_map[v["id"]] = v

        # Aggregate by sector
        sector_data = {}
        for p in proposals:
            sector = p.get("sector")
            if not sector:
                continue

            if sector not in sector_data:
                sector_data[sector] = {
                    "sector": sector,
                    "score_sum": 0.0,
                    "score_count": 0,
                    "shortlisted": 0,
                    "under_review": 0,
                    "needs_improvement": 0,
                    "vendor_ids": set(),
                }

            sd = sector_data[sector]
            cs = p.get("composite_score")
            if cs is not None:
                sd["score_sum"] += float(cs)
                sd["score_count"] += 1

            s = p.get("status", "")
            if s == "shortlisted":
                sd["shortlisted"] += 1
            elif s == "under_review":
                sd["under_review"] += 1
            elif s == "needs_improvement":
                sd["needs_improvement"] += 1

            submitter_id = p.get("submitter_id")
            if submitter_id:
                sd["vendor_ids"].add(submitter_id)

        # Build response with vendor metrics
        result = []
        for sector, sd in sector_data.items():
            avg_score = round(sd["score_sum"] / sd["score_count"], 1) if sd["score_count"] > 0 else 0

            # Compute vendor-level metrics for this sector
            vscore_sum = 0.0
            vscore_count = 0
            desc_certified = 0
            top_tier = 0

            for vid in sd["vendor_ids"]:
                v = vendor_map.get(vid)
                if not v:
                    continue
                vsc = v.get("average_compliance_score")
                if vsc is not None:
                    vscore_sum += float(vsc)
                    vscore_count += 1
                if v.get("is_desc_approved"):
                    desc_certified += 1
                tier = v.get("vscore_tier", "")
                if tier in ("platinum", "gold"):
                    top_tier += 1

            avg_vscore = round(vscore_sum / vscore_count, 1) if vscore_count > 0 else 0

            result.append({
                "sector": sector,
                "avg_score": avg_score,
                "avg_vscore": avg_vscore,
                "shortlisted": sd["shortlisted"],
                "under_review": sd["under_review"],
                "flagged": sd["needs_improvement"],
                "desc_certified": desc_certified,
                "top_tier": top_tier,
            })

        # Sort by avg composite score descending
        result.sort(key=lambda x: x["avg_score"], reverse=True)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sector intelligence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )

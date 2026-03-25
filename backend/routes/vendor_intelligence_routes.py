from fastapi import APIRouter, Depends, HTTPException, status
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendors", tags=["Vendor Intelligence"])


@router.get(
    "/intelligence",
    summary="Get Vendor Intelligence overview",
)
async def get_vendor_intelligence(
    current_user: dict = Depends(get_current_user),
):
    """Return the Vendor Intelligence overview for the leaderboard page."""
    try:
        user_role = current_user["role"]
        if user_role not in ["admin", "analyst", "executive", "business_group_lead", "compliance_officer"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "Forbidden", "detail": "Insufficient permissions", "code": "INSUFFICIENT_PERMISSIONS"})

        # Fetch all vendors with vScore data
        vendors_resp = supabase.table("chamber_vendors").select("id, name, vscore, vscore_tier, country, is_desc_approved").order("vscore", desc=True).execute()
        vendors = vendors_resp.data or []

        # Fetch engagement counts per vendor
        eng_resp = supabase.table("chamber_vendor_engagements").select("vendor_id").execute()
        eng_data = eng_resp.data or []
        eng_counts = {}
        for e in eng_data:
            vid = e.get("vendor_id")
            eng_counts[vid] = eng_counts.get(vid, 0) + 1

        # Fetch flags per vendor
        flags_resp = supabase.table("chamber_vendor_flags").select("vendor_id, severity, flag_type, resolution_status").execute()
        flags_data = flags_resp.data or []
        flag_pos_counts = {}
        flag_neg_counts = {}
        cert_summary = {}
        open_risk_count = 0
        positive_types = {"iso_27001", "iso_9001", "iso_14001", "soc2_type2", "commendation", "desc_audit", "award"}

        for f in flags_data:
            vid = f.get("vendor_id")
            ft = f.get("flag_type", "")
            if ft in positive_types or f.get("severity") == "info":
                flag_pos_counts[vid] = flag_pos_counts.get(vid, 0) + 1
                # Track certifications
                if ft in {"iso_27001", "iso_9001", "iso_14001", "soc2_type2"}:
                    cert_summary[ft] = cert_summary.get(ft, 0) + 1
            else:
                flag_neg_counts[vid] = flag_neg_counts.get(vid, 0) + 1
            if f.get("resolution_status") != "resolved" and f.get("severity") in ("high", "critical", "medium"):
                open_risk_count += 1

        # Fetch latest narrative snippets from vscore_history
        hist_resp = supabase.table("chamber_vscore_history").select("vendor_id, ai_narrative").order("created_at", desc=True).execute()
        hist_data = hist_resp.data or []
        narratives = {}
        for h in hist_data:
            vid = h.get("vendor_id")
            if vid not in narratives and h.get("ai_narrative"):
                narratives[vid] = h["ai_narrative"][:200] + "..." if len(h.get("ai_narrative", "")) > 200 else h.get("ai_narrative", "")

        # Fetch sectors from latest proposals per vendor
        proposals_resp = supabase.table("chamber_proposals").select("submitter_id, sector").order("submission_date", desc=True).execute()
        proposals_data = proposals_resp.data or []
        vendor_sectors = {}
        for p in proposals_data:
            sid = p.get("submitter_id")
            if sid and sid not in vendor_sectors and p.get("sector"):
                vendor_sectors[sid] = p["sector"]

        # Build distribution
        distribution = {"platinum": 0, "gold": 0, "silver": 0, "bronze": 0, "under_review": 0}
        total_vscore = 0
        scored_count = 0

        vendor_list = []
        for v in vendors:
            vid = v["id"]
            tier = v.get("vscore_tier", "under_review")
            if tier in distribution:
                distribution[tier] += 1
            vs = v.get("vscore")
            if vs is not None:
                total_vscore += vs
                scored_count += 1

            vendor_list.append({
                "id": vid,
                "name": v.get("name"),
                "vscore": vs,
                "tier": tier,
                "country": v.get("country"),
                "is_desc_approved": v.get("is_desc_approved", False),
                "sector": vendor_sectors.get(vid),
                "engagement_count": eng_counts.get(vid, 0),
                "flag_count_positive": flag_pos_counts.get(vid, 0),
                "flag_count_negative": flag_neg_counts.get(vid, 0),
                "latest_narrative_snippet": narratives.get(vid, ""),
            })

        return {
            "vendors": vendor_list,
            "distribution": distribution,
            "avg_vscore": round(total_vscore / scored_count) if scored_count > 0 else 0,
            "total_engagements": len(eng_data),
            "total_flags": len(flags_data),
            "open_risk_flags": open_risk_count,
            "certifications_summary": cert_summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor intelligence: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": "Internal server error", "detail": "Failed to retrieve vendor intelligence", "code": "INTELLIGENCE_ERROR"})

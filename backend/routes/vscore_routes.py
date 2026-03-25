from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendors", tags=["vScore"])


@router.get(
    "/{vendor_id}/vscore",
    summary="Get vendor vScore dossier",
    responses={
        200: {"description": "vScore dossier retrieved"},
        404: {"description": "Vendor not found"},
    },
)
async def get_vendor_vscore(
    vendor_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Return the full vScore dossier for a vendor."""
    try:
        user_role = current_user["role"]
        if user_role not in ["admin", "analyst", "executive", "business_group_lead", "compliance_officer", "vendor"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "Forbidden", "detail": "Insufficient permissions", "code": "INSUFFICIENT_PERMISSIONS"})

        vid = str(vendor_id)

        # Fetch vendor base data
        vendor_resp = supabase.table("chamber_vendors").select("*").eq("id", vid).maybe_single().execute()
        if not vendor_resp or not vendor_resp.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Not found", "detail": "Vendor not found", "code": "VENDOR_NOT_FOUND"})
        vendor = vendor_resp.data

        # Fetch engagements
        eng_resp = supabase.table("chamber_vendor_engagements").select("*").eq("vendor_id", vid).order("start_date", desc=True).execute()
        engagements = eng_resp.data or []

        # Fetch relationships
        rel_resp1 = supabase.table("chamber_vendor_relationships").select("*").eq("vendor_id", vid).execute()
        rel_resp2 = supabase.table("chamber_vendor_relationships").select("*").eq("related_vendor_id", vid).execute()
        relationships = (rel_resp1.data or []) + (rel_resp2.data or [])

        # Fetch flags
        flags_resp = supabase.table("chamber_vendor_flags").select("*").eq("vendor_id", vid).order("flag_date", desc=True).execute()
        flags = flags_resp.data or []

        # Fetch score history
        hist_resp = supabase.table("chamber_vscore_history").select("*").eq("vendor_id", vid).order("created_at", desc=True).execute()
        history = hist_resp.data or []

        # Build dimension scores from latest history entry
        dimension_scores = {}
        ai_narrative = ""
        if history:
            latest = history[0]
            ds = latest.get("dimension_scores")
            if isinstance(ds, dict):
                dimension_scores = ds
            elif isinstance(ds, str):
                import json
                try:
                    dimension_scores = json.loads(ds)
                except Exception:
                    dimension_scores = {}
            ai_narrative = latest.get("ai_narrative", "")

        # Build positive/negative factors from flags
        factors_positive = []
        factors_negative = []

        # Engagement-based factors
        completed = [e for e in engagements if e.get("outcome") == "completed"]
        if completed:
            factors_positive.append(f"{len(completed)} engagement(s) completed successfully")

        # Flag-based factors
        positive_flag_types = {"iso_27001", "iso_9001", "iso_14001", "soc2_type2", "commendation", "desc_audit", "award"}
        negative_flag_types = {"violation", "delay", "dispute", "concern", "risk", "do_not_procure"}
        for f in flags:
            ft = f.get("flag_type", "")
            title = f.get("title", ft)
            if ft in positive_flag_types or f.get("severity") == "info":
                factors_positive.append(title)
            elif ft in negative_flag_types or f.get("severity") in ("high", "critical"):
                factors_negative.append(title)

        # Score change
        score_change = 0
        if len(history) >= 2:
            score_change = (history[0].get("vscore") or 0) - (history[1].get("vscore") or 0)

        return {
            "vendor_id": vid,
            "vendor_name": vendor.get("name"),
            "vscore": vendor.get("vscore"),
            "vscore_tier": vendor.get("vscore_tier"),
            "dimension_scores": dimension_scores,
            "factors_positive": factors_positive,
            "factors_negative": factors_negative,
            "ai_narrative": ai_narrative,
            "score_change": score_change,
            "engagements": [
                {
                    "engagement_type": e.get("engagement_type"),
                    "engagement_title": e.get("engagement_title"),
                    "outcome": e.get("outcome"),
                    "delivery_rating": e.get("delivery_rating"),
                    "quality_rating": e.get("quality_rating"),
                    "start_date": e.get("start_date"),
                    "end_date": e.get("end_date"),
                    "counterparty": e.get("counterparty"),
                    "contract_value": e.get("contract_value"),
                    "notes": e.get("notes"),
                }
                for e in engagements
            ],
            "relationships": [
                {
                    "related_entity_name": r.get("related_entity_name"),
                    "relationship_type": r.get("relationship_type"),
                    "notes": r.get("notes"),
                    "related_vendor_id": r.get("related_vendor_id") if r.get("vendor_id") == vid else r.get("vendor_id"),
                }
                for r in relationships
            ],
            "flags": [
                {
                    "flag_type": f.get("flag_type"),
                    "severity": f.get("severity"),
                    "title": f.get("title"),
                    "resolution_status": f.get("resolution_status"),
                    "expiry_date": f.get("expiry_date"),
                    "flag_date": f.get("flag_date"),
                    "resolution_notes": f.get("resolution_notes"),
                }
                for f in flags
            ],
            "score_history": [
                {
                    "vscore": h.get("vscore"),
                    "tier": h.get("tier"),
                    "score_change": h.get("score_change"),
                    "created_at": h.get("created_at"),
                    "ai_narrative": h.get("ai_narrative"),
                }
                for h in history
            ],
            "formula": {
                "performance_weight": 0.30,
                "quality_weight": 0.25,
                "compliance_weight": 0.20,
                "integrity_weight": 0.15,
                "entity_weight": 0.10,
                "score_range": "300-900",
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vscore for vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": "Internal server error", "detail": "Failed to retrieve vScore dossier", "code": "VSCORE_ERROR"})


@router.get(
    "/{vendor_id}/engagements",
    summary="Get vendor engagement history",
)
async def get_vendor_engagements(
    vendor_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Return engagement history for a vendor."""
    try:
        vid = str(vendor_id)
        resp = supabase.table("chamber_vendor_engagements").select("*").eq("vendor_id", vid).order("start_date", desc=True).execute()
        return {"vendor_id": vid, "engagements": resp.data or []}
    except Exception as e:
        logger.error(f"Error getting engagements for vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": "Internal server error", "detail": "Failed to retrieve engagements", "code": "ENGAGEMENT_ERROR"})


@router.get(
    "/{vendor_id}/flags",
    summary="Get vendor flags",
)
async def get_vendor_flags(
    vendor_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Return all flags for a vendor."""
    try:
        vid = str(vendor_id)
        resp = supabase.table("chamber_vendor_flags").select("*").eq("vendor_id", vid).order("flag_date", desc=True).execute()
        return {"vendor_id": vid, "flags": resp.data or []}
    except Exception as e:
        logger.error(f"Error getting flags for vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": "Internal server error", "detail": "Failed to retrieve flags", "code": "FLAGS_ERROR"})


@router.get(
    "/{vendor_id}/relationships",
    summary="Get vendor relationships",
)
async def get_vendor_relationships(
    vendor_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Return relationships for a vendor."""
    try:
        vid = str(vendor_id)
        resp1 = supabase.table("chamber_vendor_relationships").select("*").eq("vendor_id", vid).execute()
        resp2 = supabase.table("chamber_vendor_relationships").select("*").eq("related_vendor_id", vid).execute()
        all_rels = (resp1.data or []) + (resp2.data or [])
        return {"vendor_id": vid, "relationships": all_rels}
    except Exception as e:
        logger.error(f"Error getting relationships for vendor {vendor_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"error": "Internal server error", "detail": "Failed to retrieve relationships", "code": "RELATIONSHIPS_ERROR"})

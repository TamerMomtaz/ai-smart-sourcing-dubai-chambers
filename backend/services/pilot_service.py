"""Service layer for Pilot Tracker operations."""
import logging
from datetime import datetime, timezone

from database import supabase

logger = logging.getLogger(__name__)


def create_pilot(
    *,
    proposal_id: str,
    title: str,
    vendor_id: str = None,
    start_date: str = None,
    end_date: str = None,
    success_criteria: str = None,
    budget_allocated: float = None,
    created_by: str,
):
    """Create a new pilot from a shortlisted proposal."""
    data = {
        "proposal_id": proposal_id,
        "title": title,
        "status": "setup",
        "created_by": created_by,
    }
    if vendor_id:
        data["vendor_id"] = vendor_id
    if start_date:
        data["start_date"] = start_date
    if end_date:
        data["end_date"] = end_date
    if success_criteria:
        data["success_criteria"] = success_criteria
    if budget_allocated is not None:
        data["budget_allocated"] = budget_allocated

    # If no vendor_id provided, try to get it from the proposal
    if not vendor_id:
        try:
            proposal = (
                supabase.table("chamber_proposals")
                .select("submitter_id")
                .eq("id", proposal_id)
                .maybe_single()
                .execute()
            )
            if proposal.data and proposal.data.get("submitter_id"):
                data["vendor_id"] = proposal.data["submitter_id"]
        except Exception as e:
            logger.warning(f"Failed to fetch vendor from proposal: {e}")

    result = supabase.table("chamber_pilots").insert(data).execute()
    return result.data[0] if result.data else None


def list_pilots(
    *,
    status_filter: str = None,
    vendor_id_filter: str = None,
):
    """List all pilots with related proposal and vendor info."""
    query = supabase.table("chamber_pilots").select("*")

    if status_filter:
        query = query.eq("status", status_filter)
    if vendor_id_filter:
        query = query.eq("vendor_id", vendor_id_filter)

    query = query.order("created_at", desc=True)
    result = query.execute()
    pilots = result.data or []

    if not pilots:
        return pilots

    # Enrich with proposal titles
    proposal_ids = list({p["proposal_id"] for p in pilots if p.get("proposal_id")})
    if proposal_ids:
        proposals_result = (
            supabase.table("chamber_proposals")
            .select("id, title, composite_score, status")
            .in_("id", proposal_ids)
            .execute()
        )
        proposal_map = {p["id"]: p for p in (proposals_result.data or [])}
        for pilot in pilots:
            prop = proposal_map.get(pilot.get("proposal_id"), {})
            pilot["proposal_title"] = prop.get("title", "")
            pilot["proposal_score"] = prop.get("composite_score")
            pilot["proposal_status"] = prop.get("status", "")

    # Enrich with vendor names
    vendor_ids = list({p["vendor_id"] for p in pilots if p.get("vendor_id")})
    if vendor_ids:
        vendors_result = (
            supabase.table("chamber_vendors")
            .select("id, name, country")
            .in_("id", vendor_ids)
            .execute()
        )
        vendor_map = {v["id"]: v for v in (vendors_result.data or [])}
        for pilot in pilots:
            vendor = vendor_map.get(pilot.get("vendor_id"), {})
            pilot["vendor_name"] = vendor.get("name", "")
            pilot["vendor_country"] = vendor.get("country", "")

    return pilots


def get_pilot(*, pilot_id: str):
    """Get a single pilot with full related data."""
    result = (
        supabase.table("chamber_pilots")
        .select("*")
        .eq("id", pilot_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None

    pilot = result.data

    # Fetch linked proposal
    if pilot.get("proposal_id"):
        proposal_result = (
            supabase.table("chamber_proposals")
            .select("id, title, status, sector, technology_type, composite_score, submission_date")
            .eq("id", pilot["proposal_id"])
            .maybe_single()
            .execute()
        )
        pilot["proposal"] = proposal_result.data
    else:
        pilot["proposal"] = None

    # Fetch linked vendor
    if pilot.get("vendor_id"):
        vendor_result = (
            supabase.table("chamber_vendors")
            .select("id, name, country, contact_email")
            .eq("id", pilot["vendor_id"])
            .maybe_single()
            .execute()
        )
        pilot["vendor"] = vendor_result.data
    else:
        pilot["vendor"] = None

    return pilot


def update_pilot(
    *,
    pilot_id: str,
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    success_criteria: str = None,
    budget_allocated: float = None,
    budget_spent: float = None,
    outcome_rating: int = None,
    outcome_summary: str = None,
    lessons_learned: str = None,
    adoption_decision: str = None,
):
    """Update a pilot's fields."""
    update_data = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if status is not None:
        update_data["status"] = status
    if start_date is not None:
        update_data["start_date"] = start_date
    if end_date is not None:
        update_data["end_date"] = end_date
    if success_criteria is not None:
        update_data["success_criteria"] = success_criteria
    if budget_allocated is not None:
        update_data["budget_allocated"] = budget_allocated
    if budget_spent is not None:
        update_data["budget_spent"] = budget_spent
    if outcome_rating is not None:
        update_data["outcome_rating"] = outcome_rating
    if outcome_summary is not None:
        update_data["outcome_summary"] = outcome_summary
    if lessons_learned is not None:
        update_data["lessons_learned"] = lessons_learned
    if adoption_decision is not None:
        update_data["adoption_decision"] = adoption_decision

    result = (
        supabase.table("chamber_pilots")
        .update(update_data)
        .eq("id", pilot_id)
        .execute()
    )
    return result.data[0] if result.data else None

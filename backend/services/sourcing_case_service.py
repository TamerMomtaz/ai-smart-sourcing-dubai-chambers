"""Service layer for Sourcing Case operations."""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from database import supabase

logger = logging.getLogger(__name__)


def create_sourcing_case(
    *,
    title: str,
    problem_statement: str,
    requesting_entity: str = None,
    business_group_id: str = None,
    sector: str = None,
    technology_domain: str = None,
    urgency: str = "medium",
    compliance_tier: str = "standard",
    compliance_requirements: str = None,
    assigned_analyst_id: str = None,
    created_by: str,
    status: str = "open",
    source_channel: str = "manual",
):
    """Create a new sourcing case."""
    data = {
        "title": title,
        "problem_statement": problem_statement,
        "urgency": urgency,
        "compliance_tier": compliance_tier,
        "status": status,
        "created_by": created_by,
        "source_channel": source_channel,
    }
    if requesting_entity:
        data["requesting_entity"] = requesting_entity
    if business_group_id:
        data["business_group_id"] = business_group_id
    if sector:
        data["sector"] = sector
    if technology_domain:
        data["technology_domain"] = technology_domain
    if compliance_requirements:
        data["compliance_requirements"] = compliance_requirements
    if assigned_analyst_id:
        data["assigned_analyst_id"] = assigned_analyst_id
    elif sector:
        # Auto-assign analyst based on sector mapping
        try:
            mapping = (
                supabase.table("chamber_sector_assignments")
                .select("assigned_user_id")
                .eq("sector", sector)
                .maybe_single()
                .execute()
            )
            if mapping.data and mapping.data.get("assigned_user_id"):
                data["assigned_analyst_id"] = mapping.data["assigned_user_id"]
                logger.info(
                    "Auto-assigned analyst %s for sector '%s'",
                    mapping.data["assigned_user_id"],
                    sector,
                )
        except Exception as e:
            logger.warning("Sector auto-assignment lookup failed: %s", e)

    result = supabase.table("chamber_sourcing_cases").insert(data).execute()
    return result.data[0] if result.data else None


def list_sourcing_cases(
    *,
    status_filter: str = None,
    sector_filter: str = None,
    urgency_filter: str = None,
    source_channel_filter: str = None,
    sort_by: str = "created_at",
):
    """List sourcing cases with optional filters."""
    query = supabase.table("chamber_sourcing_cases").select("*")

    if status_filter:
        query = query.eq("status", status_filter)
    if sector_filter:
        query = query.eq("sector", sector_filter)
    if urgency_filter:
        query = query.eq("urgency", urgency_filter)
    if source_channel_filter:
        query = query.eq("source_channel", source_channel_filter)

    if sort_by == "urgency":
        query = query.order("urgency", desc=False).order("created_at", desc=True)
    else:
        query = query.order("created_at", desc=True)

    result = query.execute()
    cases = result.data or []

    # Attach proposal counts
    if cases:
        case_ids = [c["id"] for c in cases]
        proposals_result = (
            supabase.table("chamber_proposals")
            .select("sourcing_case_id")
            .in_("sourcing_case_id", case_ids)
            .execute()
        )
        count_map = {}
        for p in (proposals_result.data or []):
            cid = p["sourcing_case_id"]
            count_map[cid] = count_map.get(cid, 0) + 1

        for c in cases:
            c["proposal_count"] = count_map.get(c["id"], 0)

    return cases


def get_sourcing_case(*, case_id: str):
    """Get a single sourcing case with linked proposals and evaluations."""
    result = (
        supabase.table("chamber_sourcing_cases")
        .select("*")
        .eq("id", case_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None

    case = result.data

    # Fetch linked proposals
    proposals_result = (
        supabase.table("chamber_proposals")
        .select("id, title, status, sector, technology_type, created_at, composite_score")
        .eq("sourcing_case_id", case_id)
        .order("created_at", desc=True)
        .execute()
    )
    case["proposals"] = proposals_result.data or []

    # Fetch matching vendors by sector (if sector is set)
    if case.get("sector"):
        vendors_result = (
            supabase.table("chamber_vendors")
            .select("id, company_name, country, email")
            .limit(20)
            .execute()
        )
        case["matching_vendors"] = vendors_result.data or []
    else:
        case["matching_vendors"] = []

    # Fetch assigned analyst info
    if case.get("assigned_analyst_id"):
        analyst_result = (
            supabase.table("chamber_users")
            .select("id, email, role")
            .eq("id", case["assigned_analyst_id"])
            .maybe_single()
            .execute()
        )
        case["assigned_analyst"] = analyst_result.data
    else:
        case["assigned_analyst"] = None

    return case


def update_sourcing_case_status(*, case_id: str, new_status: str):
    """Update the status of a sourcing case."""
    update_data = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if new_status in ("completed", "closed"):
        update_data["closed_at"] = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("chamber_sourcing_cases")
        .update(update_data)
        .eq("id", case_id)
        .execute()
    )
    return result.data[0] if result.data else None


def merge_sourcing_cases(*, source_id: str, target_id: str, merged_by: str) -> Optional[Dict[str, Any]]:
    """
    Merge source sourcing case into target.
    - Moves all linked proposals from source to target
    - Moves all vendor matches from source to target
    - Sets source status to 'closed' with merge note
    """
    # Verify both cases exist
    source = (
        supabase.table("chamber_sourcing_cases")
        .select("id, title, status")
        .eq("id", source_id)
        .maybe_single()
        .execute()
    )
    if not source.data:
        return None

    target = (
        supabase.table("chamber_sourcing_cases")
        .select("id, title, status")
        .eq("id", target_id)
        .maybe_single()
        .execute()
    )
    if not target.data:
        return None

    now = datetime.now(timezone.utc).isoformat()

    # Move linked proposals from source to target
    proposals_moved = 0
    try:
        proposals_result = (
            supabase.table("chamber_proposals")
            .select("id")
            .eq("sourcing_case_id", source_id)
            .execute()
        )
        if proposals_result.data:
            proposals_moved = len(proposals_result.data)
            supabase.table("chamber_proposals").update(
                {"sourcing_case_id": target_id, "updated_at": now}
            ).eq("sourcing_case_id", source_id).execute()
    except Exception as e:
        logger.warning(f"Failed to move proposals during merge: {e}")

    # Move vendor matches from source to target
    vendor_matches_moved = 0
    try:
        matches_result = (
            supabase.table("chamber_vendor_matches")
            .select("id")
            .eq("sourcing_case_id", source_id)
            .execute()
        )
        if matches_result.data:
            vendor_matches_moved = len(matches_result.data)
            supabase.table("chamber_vendor_matches").update(
                {"sourcing_case_id": target_id}
            ).eq("sourcing_case_id", source_id).execute()
    except Exception as e:
        logger.warning(f"Failed to move vendor matches during merge: {e}")

    # Close source case with merge note
    merge_note = f"Merged into {target_id}"
    supabase.table("chamber_sourcing_cases").update({
        "status": "closed",
        "compliance_requirements": (
            (source.data.get("compliance_requirements") or "") +
            f"\n[MERGED] {merge_note}"
        ).strip(),
        "updated_at": now,
        "closed_at": now,
    }).eq("id", source_id).execute()

    return {
        "source_case_id": source_id,
        "target_case_id": target_id,
        "source_title": source.data.get("title", ""),
        "target_title": target.data.get("title", ""),
        "proposals_moved": proposals_moved,
        "vendor_matches_moved": vendor_matches_moved,
        "merged_by": merged_by,
        "merged_at": now,
    }

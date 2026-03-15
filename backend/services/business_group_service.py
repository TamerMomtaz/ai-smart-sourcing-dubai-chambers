from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


def create_business_group(
    name: str,
    chamber: str,
    description: Optional[str] = None,
    sector_kpis_json: Optional[Dict[str, Any]] = None,
    evaluation_weight_config_json: Optional[Dict[str, Any]] = None,
    lead_user_id: Optional[UUID] = None,
) -> Optional[Dict[str, Any]]:
    """Create a new business group."""
    insert_data = {
        "name": name,
        "chamber": chamber,
        "description": description,
        "sector_kpis_json": sector_kpis_json,
        "evaluation_weight_config_json": evaluation_weight_config_json,
        "lead_user_id": str(lead_user_id) if lead_user_id else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    result = supabase.table("chamber_business_groups").insert(insert_data).execute()
    return result.data[0] if result.data else None


def list_business_groups(
    page: int = 1,
    page_size: int = 20,
    chamber: Optional[str] = None,
) -> Dict[str, Any]:
    """List business groups with pagination and optional chamber filter."""
    offset = (page - 1) * page_size

    query = supabase.table("chamber_business_groups").select("*", count="exact")

    if chamber:
        query = query.eq("chamber", chamber)

    query = query.order("name").range(offset, offset + page_size - 1)
    result = query.execute()

    total = result.count if result.count is not None else 0

    return {
        "data": result.data,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_business_group_by_id(group_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a business group by ID."""
    result = (
        supabase.table("chamber_business_groups")
        .select("*")
        .eq("id", str(group_id))
        .maybe_single()
        .execute()
    )
    return result.data


def update_business_group(
    group_id: UUID,
    lead_user_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    sector_kpis_json: Optional[Dict[str, Any]] = None,
    evaluation_weight_config_json: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Update a business group. Only group lead can update."""
    existing = get_business_group_by_id(group_id)
    if not existing:
        return None

    if existing.get("lead_user_id") != str(lead_user_id):
        return None

    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if sector_kpis_json is not None:
        update_data["sector_kpis_json"] = sector_kpis_json
    if evaluation_weight_config_json is not None:
        update_data["evaluation_weight_config_json"] = evaluation_weight_config_json

    result = (
        supabase.table("chamber_business_groups")
        .update(update_data)
        .eq("id", str(group_id))
        .execute()
    )
    return result.data[0] if result.data else None


def delete_business_group(group_id: UUID, lead_user_id: UUID) -> bool:
    """Soft delete a business group by setting lead_user_id to NULL. Only group lead can delete."""
    existing = get_business_group_by_id(group_id)
    if not existing:
        return False

    if existing.get("lead_user_id") != str(lead_user_id):
        return False

    result = (
        supabase.table("chamber_business_groups")
        .update(
            {
                "lead_user_id": None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", str(group_id))
        .execute()
    )
    return bool(result.data)


def get_business_group_with_stats(group_id: UUID) -> Optional[Dict[str, Any]]:
    """Get business group with proposal count and average composite score."""
    group = get_business_group_by_id(group_id)
    if not group:
        return None

    proposal_stats = (
        supabase.table("chamber_proposals")
        .select("id, composite_score")
        .eq("business_group_id", str(group_id))
        .execute()
    )

    proposal_count = len(proposal_stats.data) if proposal_stats.data else 0
    scores = [
        p["composite_score"]
        for p in (proposal_stats.data or [])
        if p.get("composite_score") is not None
    ]
    average_composite_score = sum(scores) / len(scores) if scores else None

    return {
        **group,
        "proposal_count": proposal_count,
        "average_composite_score": average_composite_score,
    }


def update_evaluation_weights(
    group_id: UUID,
    lead_user_id: UUID,
    evaluation_weight_config_json: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Update evaluation weight configuration for a business group."""
    return update_business_group(
        group_id=group_id,
        lead_user_id=lead_user_id,
        evaluation_weight_config_json=evaluation_weight_config_json,
    )

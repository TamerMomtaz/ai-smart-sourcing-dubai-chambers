"""Service layer for Sector Assignment operations."""
import logging

from database import supabase

logger = logging.getLogger(__name__)


def list_sector_assignments():
    """List all sector-to-analyst assignments."""
    result = (
        supabase.table("chamber_sector_assignments")
        .select("*")
        .order("sector")
        .execute()
    )
    return result.data or []


def get_assignment_by_sector(*, sector: str):
    """Get the analyst assignment for a specific sector."""
    result = (
        supabase.table("chamber_sector_assignments")
        .select("*")
        .eq("sector", sector)
        .maybe_single()
        .execute()
    )
    return result.data


def upsert_sector_assignment(*, sector: str, assigned_user_id: str):
    """Create or update a sector-to-analyst assignment."""
    existing = get_assignment_by_sector(sector=sector)
    if existing:
        result = (
            supabase.table("chamber_sector_assignments")
            .update({"assigned_user_id": assigned_user_id})
            .eq("id", existing["id"])
            .execute()
        )
    else:
        result = (
            supabase.table("chamber_sector_assignments")
            .insert({"sector": sector, "assigned_user_id": assigned_user_id})
            .execute()
        )
    return result.data[0] if result.data else None


def delete_sector_assignment(*, assignment_id: str):
    """Delete a sector assignment."""
    result = (
        supabase.table("chamber_sector_assignments")
        .delete()
        .eq("id", assignment_id)
        .execute()
    )
    return result.data[0] if result.data else None

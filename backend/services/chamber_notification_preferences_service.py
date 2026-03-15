from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


async def create(user_id: UUID, email_enabled: bool = True, proposal_status_updates: bool = True, weekly_digest: bool = True, compliance_alerts: bool = True) -> Optional[dict]:
    """
    Create notification preferences for a user.
    Returns the created preference record or None if creation fails.
    """
    response = supabase.table("chamber_notification_preferences").insert({
        "user_id": str(user_id),
        "email_enabled": email_enabled,
        "proposal_status_updates": proposal_status_updates,
        "weekly_digest": weekly_digest,
        "compliance_alerts": compliance_alerts,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def get_by_user_id(user_id: UUID) -> Optional[dict]:
    """
    Get notification preferences for a specific user.
    Returns the preference record or None if not found.
    """
    response = supabase.table("chamber_notification_preferences").select("*").eq("user_id", str(user_id)).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def update(user_id: UUID, email_enabled: Optional[bool] = None, proposal_status_updates: Optional[bool] = None, weekly_digest: Optional[bool] = None, compliance_alerts: Optional[bool] = None) -> Optional[dict]:
    """
    Update notification preferences for a user.
    Only updates fields that are provided (not None).
    Returns the updated preference record or None if not found.
    """
    # First verify ownership
    existing = await get_by_user_id(user_id)
    if not existing:
        return None
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if email_enabled is not None:
        update_data["email_enabled"] = email_enabled
    if proposal_status_updates is not None:
        update_data["proposal_status_updates"] = proposal_status_updates
    if weekly_digest is not None:
        update_data["weekly_digest"] = weekly_digest
    if compliance_alerts is not None:
        update_data["compliance_alerts"] = compliance_alerts
    
    response = supabase.table("chamber_notification_preferences").update(update_data).eq("user_id", str(user_id)).execute()
    
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def delete(user_id: UUID) -> bool:
    """
    Delete notification preferences for a user.
    Returns True if deletion was successful, False otherwise.
    Note: This is a hard delete since this table doesn't have a deleted_at column.
    """
    # First verify ownership
    existing = await get_by_user_id(user_id)
    if not existing:
        return False
    
    response = supabase.table("chamber_notification_preferences").delete().eq("user_id", str(user_id)).execute()
    
    return response.data is not None and len(response.data) > 0


async def list_all(page: int = 1, page_size: int = 50) -> tuple[list[dict], int]:
    """
    List all notification preferences with pagination.
    Returns a tuple of (preferences_list, total_count).
    Note: This is an admin-level operation and should be protected at the route level.
    """
    offset = (page - 1) * page_size
    
    # Get total count
    count_response = supabase.table("chamber_notification_preferences").select("*", count="exact").execute()
    total_count = count_response.count if count_response.count else 0
    
    # Get paginated data
    response = supabase.table("chamber_notification_preferences").select("*").range(offset, offset + page_size - 1).order("created_at", desc=True).execute()
    
    return response.data if response.data else [], total_count


async def get_or_create(user_id: UUID) -> dict:
    """
    Get notification preferences for a user, or create default preferences if they don't exist.
    Always returns a preference record.
    """
    existing = await get_by_user_id(user_id)
    if existing:
        return existing
    
    # Create default preferences
    created = await create(user_id)
    return created if created else {}

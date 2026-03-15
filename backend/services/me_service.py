from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


def get_user_profile(user_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get current user profile with business group and permissions.
    Returns None if user not found.
    """
    try:
        # Get user basic info from auth.users via Supabase metadata
        user_response = supabase.auth.admin.get_user_by_id(str(user_id))
        if not user_response or not user_response.user:
            return None

        user = user_response.user
        user_metadata = user.user_metadata or {}

        # Get business group info if user has business_group_id
        business_group_id = user_metadata.get("business_group_id")
        business_group_name = None
        
        if business_group_id:
            bg_response = (
                supabase.table("chamber_business_groups")
                .select("id, name")
                .eq("id", business_group_id)
                .single()
                .execute()
            )
            if bg_response.data:
                business_group_name = bg_response.data.get("name")

        # Build permissions based on role
        role = user_metadata.get("role", "analyst")
        permissions = _get_permissions_for_role(role)

        return {
            "id": user.id,
            "email": user.email,
            "role": role,
            "full_name": user_metadata.get("full_name", ""),
            "chamber": user_metadata.get("chamber", ""),
            "business_group_id": business_group_id,
            "business_group_name": business_group_name,
            "preferred_language": user_metadata.get("preferred_language", "en"),
            "last_login": user.last_sign_in_at,
            "permissions": permissions,
        }

    except Exception:
        return None


def update_user_profile(
    user_id: UUID,
    full_name: Optional[str] = None,
    preferred_language: Optional[str] = None,
    notification_preferences: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update current user profile settings.
    Returns updated user_id and timestamp, or None if update fails.
    """
    try:
        # Get current user metadata
        user_response = supabase.auth.admin.get_user_by_id(str(user_id))
        if not user_response or not user_response.user:
            return None

        current_metadata = user_response.user.user_metadata or {}

        # Build update payload
        updated_metadata = current_metadata.copy()

        if full_name is not None:
            updated_metadata["full_name"] = full_name

        if preferred_language is not None:
            updated_metadata["preferred_language"] = preferred_language

        if notification_preferences is not None:
            updated_metadata["notification_preferences"] = notification_preferences

        # Update user metadata via Supabase Admin API
        supabase.auth.admin.update_user_by_id(
            str(user_id),
            {"user_metadata": updated_metadata}
        )

        return {
            "user_id": str(user_id),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception:
        return None


def _get_permissions_for_role(role: str) -> list[str]:
    """
    Return list of permissions based on user role.
    """
    permissions_map = {
        "analyst": [
            "proposals:view",
            "proposals:evaluate",
            "proposals:comment",
            "vendors:view",
            "evaluations:view",
            "compliance:view",
            "dashboard:analyst",
        ],
        "executive": [
            "proposals:view",
            "proposals:approve",
            "proposals:reject",
            "proposals:comment",
            "vendors:view",
            "evaluations:view",
            "compliance:view",
            "dashboard:executive",
            "trends:view",
            "export:data",
        ],
        "compliance_officer": [
            "proposals:view",
            "proposals:comment",
            "vendors:view",
            "evaluations:view",
            "compliance:view",
            "compliance:audit",
            "compliance:export",
            "certified_providers:view",
            "certified_providers:verify",
        ],
        "business_group_lead": [
            "proposals:view",
            "proposals:evaluate",
            "proposals:comment",
            "vendors:view",
            "evaluations:view",
            "compliance:view",
            "business_group:manage",
            "evaluation_weights:update",
            "dashboard:sector",
        ],
        "vendor": [
            "proposals:create",
            "proposals:view_own",
            "proposals:update_own",
            "documents:upload",
            "vendor:view_own",
            "vendor:update_own",
        ],
        "admin": [
            "*:*",
        ],
    }

    return permissions_map.get(role, [])

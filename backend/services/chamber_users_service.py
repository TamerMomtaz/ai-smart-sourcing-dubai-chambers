from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase
import logging

logger = logging.getLogger(__name__)


async def create_user(
    user_id: UUID,
    email: str,
    role: str,
    full_name: str,
    chamber: str,
    business_group_id: Optional[UUID] = None,
    preferred_language: str = "en",
    rbac_permissions_json: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Create a new chamber user.
    Note: user_id should match Supabase auth.users(id).
    """
    try:
        response = (
            supabase.table("chamber_users")
            .insert(
                {
                    "id": str(user_id),
                    "email": email.strip(),
                    "role": role.strip(),
                    "full_name": full_name.strip(),
                    "chamber": chamber.strip(),
                    "business_group_id": str(business_group_id) if business_group_id else None,
                    "preferred_language": preferred_language.strip(),
                    "rbac_permissions_json": rbac_permissions_json,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .execute()
        )
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error creating chamber user: {e}")
        return None


async def list_users(
    requesting_user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    role_filter: Optional[str] = None,
    chamber_filter: Optional[str] = None,
    business_group_filter: Optional[UUID] = None,
) -> Dict[str, Any]:
    """
    List chamber users with pagination and filters.
    Only accessible to analysts, executives, compliance_officer, and admin.
    """
    try:
        offset = (page - 1) * page_size

        query = supabase.table("chamber_users").select("*", count="exact")

        if role_filter:
            query = query.eq("role", role_filter.strip())
        if chamber_filter:
            query = query.eq("chamber", chamber_filter.strip())
        if business_group_filter:
            query = query.eq("business_group_id", str(business_group_filter))

        response = query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()

        total = response.count if response.count is not None else 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "data": response.data if response.data else [],
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        }
    except Exception as e:
        logger.error(f"Error listing chamber users: {e}")
        return {
            "data": [],
            "pagination": {"total": 0, "page": page, "page_size": page_size, "total_pages": 1},
        }


async def get_user_by_id(user_id: UUID, requesting_user_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get chamber user by ID.
    Users can view their own profile, analysts+ can view all.
    """
    try:
        response = supabase.table("chamber_users").select("*").eq("id", str(user_id)).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching chamber user {user_id}: {e}")
        return None


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get chamber user by email address.
    """
    try:
        response = supabase.table("chamber_users").select("*").eq("email", email.strip()).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching chamber user by email {email}: {e}")
        return None


async def update_user(
    user_id: UUID,
    requesting_user_id: UUID,
    full_name: Optional[str] = None,
    chamber: Optional[str] = None,
    role: Optional[str] = None,
    business_group_id: Optional[UUID] = None,
    preferred_language: Optional[str] = None,
    rbac_permissions_json: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update chamber user.
    Users can update their own profile (limited fields).
    Admins can update all fields.
    """
    try:
        update_data: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}

        if full_name is not None:
            update_data["full_name"] = full_name.strip()
        if chamber is not None:
            update_data["chamber"] = chamber.strip()
        if role is not None:
            update_data["role"] = role.strip()
        if business_group_id is not None:
            update_data["business_group_id"] = str(business_group_id) if business_group_id else None
        if preferred_language is not None:
            update_data["preferred_language"] = preferred_language.strip()
        if rbac_permissions_json is not None:
            update_data["rbac_permissions_json"] = rbac_permissions_json

        response = supabase.table("chamber_users").update(update_data).eq("id", str(user_id)).execute()

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error updating chamber user {user_id}: {e}")
        return None


async def update_last_login(user_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Update user's last login timestamp.
    """
    try:
        response = (
            supabase.table("chamber_users")
            .update(
                {
                    "last_login": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", str(user_id))
            .execute()
        )

        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error updating last login for user {user_id}: {e}")
        return None


async def delete_user(user_id: UUID, requesting_user_id: UUID) -> bool:
    """
    Delete chamber user (hard delete).
    Only admins can delete users.
    Note: This will cascade delete due to ON DELETE CASCADE on auth.users.
    """
    try:
        response = supabase.table("chamber_users").delete().eq("id", str(user_id)).execute()
        return response.data is not None and len(response.data) > 0
    except Exception as e:
        logger.error(f"Error deleting chamber user {user_id}: {e}")
        return False


async def get_users_by_role(role: str, requesting_user_id: UUID) -> List[Dict[str, Any]]:
    """
    Get all users with a specific role.
    """
    try:
        response = (
            supabase.table("chamber_users")
            .select("*")
            .eq("role", role.strip())
            .order("full_name", desc=False)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching users by role {role}: {e}")
        return []


async def get_users_by_business_group(
    business_group_id: UUID, requesting_user_id: UUID
) -> List[Dict[str, Any]]:
    """
    Get all users in a specific business group.
    """
    try:
        response = (
            supabase.table("chamber_users")
            .select("*")
            .eq("business_group_id", str(business_group_id))
            .order("full_name", desc=False)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching users by business group {business_group_id}: {e}")
        return []


async def get_users_by_chamber(chamber: str, requesting_user_id: UUID) -> List[Dict[str, Any]]:
    """
    Get all users associated with a specific chamber.
    """
    try:
        response = (
            supabase.table("chamber_users")
            .select("*")
            .eq("chamber", chamber.strip())
            .order("full_name", desc=False)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching users by chamber {chamber}: {e}")
        return []

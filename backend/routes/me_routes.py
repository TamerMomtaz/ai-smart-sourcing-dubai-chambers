from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone
import logging

from models.user import UserProfile, UserProfileUpdate, UserProfileUpdateResponse
from models.common import ErrorResponse
from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users/me", tags=["me"])


@router.get(
    "",
    response_model=UserProfile,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get current user profile and permissions",
)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get current user profile with permissions, business group, and settings.
    Requires valid JWT authentication.
    
    Returns:
        UserProfile with id, email, role, full_name, chamber, business_group_id,
        business_group_name, preferred_language, last_login, permissions
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            logger.error("Missing user_id in current_user token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid token payload", "code": 401},
            )

        # Query chamber_users table for profile data
        user_response = (
            supabase.table("chamber_users")
            .select(
                "id, email, role, full_name, chamber, business_group_id, "
                "preferred_language, last_login, rbac_permissions_json"
            )
            .eq("id", str(user_id))
            .maybe_single()
            .execute()
        )

        if not user_response.data:
            logger.warning(f"User {user_id} not found in chamber_users")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "User profile not found", "code": 404},
            )

        user_data = user_response.data

        # Fetch business group name if business_group_id exists
        business_group_name = None
        if user_data.get("business_group_id"):
            bg_response = (
                supabase.table("business_groups")
                .select("name")
                .eq("id", user_data["business_group_id"])
                .maybe_single()
                .execute()
            )
            if bg_response.data:
                business_group_name = bg_response.data.get("name")

        # Extract permissions from RBAC JSON
        permissions = []
        rbac_json = user_data.get("rbac_permissions_json")
        if rbac_json and isinstance(rbac_json, dict):
            permissions = rbac_json.get("permissions", [])
        elif rbac_json and isinstance(rbac_json, list):
            permissions = rbac_json

        # Default permissions based on role if RBAC not set
        if not permissions:
            role = user_data.get("role", "")
            if role == "vendor":
                permissions = [
                    "proposals:create_own",
                    "proposals:read_own",
                    "proposals:update_own_draft",
                    "documents:upload_own",
                    "documents:read_own",
                    "vendor_profile:read_own",
                    "vendor_profile:update_own",
                    "notifications:read_own",
                ]
            elif role == "analyst":
                permissions = [
                    "proposals:read_all",
                    "proposals:update_status",
                    "proposals:evaluate",
                    "documents:read_all",
                    "evaluations:read_all",
                    "compliance_audits:read_all",
                    "comments:create",
                    "vendors:read_all",
                ]
            elif role == "executive":
                permissions = [
                    "proposals:read_all",
                    "evaluations:read_all",
                    "compliance_audits:read_all",
                    "dashboards:executive",
                    "trend_analysis:read_all",
                    "export:reports",
                ]
            elif role == "compliance_officer":
                permissions = [
                    "proposals:read_all",
                    "compliance_audits:read_all",
                    "compliance_audits:create",
                    "compliance_audits:generate_report",
                    "audit_trail:read_all",
                ]
            elif role == "business_group_lead":
                permissions = [
                    "proposals:read_sector",
                    "proposals:update_status_sector",
                    "business_groups:read_own",
                    "business_groups:update_config_own",
                    "sector_analytics:read_own",
                ]

        return UserProfile(
            id=UUID(user_data["id"]),
            email=user_data["email"],
            role=user_data["role"],
            full_name=user_data["full_name"],
            chamber=user_data["chamber"],
            business_group_id=UUID(user_data["business_group_id"]) if user_data.get("business_group_id") else None,
            business_group_name=business_group_name,
            preferred_language=user_data.get("preferred_language", "en"),
            last_login=user_data.get("last_login"),
            permissions=permissions,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user profile for {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": "Failed to fetch user profile", "code": 500},
        )


@router.patch(
    "",
    response_model=UserProfileUpdateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "User not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Update current user profile settings",
)
async def update_me(
    update_data: UserProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update current user profile settings.
    Allows updating: full_name, preferred_language, notification_preferences.
    Requires valid JWT authentication.
    
    Args:
        update_data: UserProfileUpdate with optional fields to update
    
    Returns:
        UserProfileUpdateResponse with user_id and updated_at timestamp
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            logger.error("Missing user_id in current_user token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid token payload", "code": 401},
            )

        # Verify user exists
        user_check = (
            supabase.table("chamber_users")
            .select("id")
            .eq("id", str(user_id))
            .maybe_single()
            .execute()
        )

        if not user_check.data:
            logger.warning(f"User {user_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "NotFound", "detail": "User not found", "code": 404},
            )

        # Build update payload
        update_payload = {}
        if update_data.full_name is not None:
            update_payload["full_name"] = update_data.full_name.strip()
        if update_data.preferred_language is not None:
            update_payload["preferred_language"] = update_data.preferred_language

        # Update chamber_users table
        if update_payload:
            update_payload["updated_at"] = datetime.now(timezone.utc).isoformat()
            supabase.table("chamber_users").update(update_payload).eq("id", str(user_id)).execute()

        # Handle notification_preferences separately
        if update_data.notification_preferences is not None:
            notif_prefs = update_data.notification_preferences.model_dump()
            notif_payload = {
                "user_id": str(user_id),
                "email_enabled": notif_prefs.get("email_enabled", True),
                "proposal_status_updates": notif_prefs.get("proposal_status_updates", True),
                "weekly_digest": notif_prefs.get("weekly_digest", True),
                "compliance_alerts": notif_prefs.get("compliance_alerts", True),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Upsert notification preferences
            existing_prefs = (
                supabase.table("chamber_notification_preferences")
                .select("id")
                .eq("user_id", str(user_id))
                .maybe_single()
                .execute()
            )

            if existing_prefs.data:
                supabase.table("chamber_notification_preferences").update(notif_payload).eq(
                    "user_id", str(user_id)
                ).execute()
            else:
                supabase.table("chamber_notification_preferences").insert(notif_payload).execute()

        return UserProfileUpdateResponse(
            user_id=UUID(user_id),
            updated_at=datetime.now(timezone.utc),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile for {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": "Failed to update user profile", "code": 500},
        )

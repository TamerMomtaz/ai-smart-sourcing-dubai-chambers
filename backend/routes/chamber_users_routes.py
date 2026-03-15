from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timezone

from models.user import UserProfile, UserProfileUpdate
from models.common import ErrorResponse
from auth import get_current_user
from services import chamber_users_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chamber-users", tags=["Chamber Users"])


@router.get(
    "/me",
    response_model=UserProfile,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
):
    """
    Get current authenticated user profile.
    Returns user information including role, chamber, business group, and permissions.
    """
    try:
        user_id = UUID(current_user["sub"])
        
        # Get user profile from chamber_users table
        from database import supabase
        
        user_response = (
            supabase.table("chamber_users")
            .select(
                "id, email, role, full_name, chamber, business_group_id, "
                "preferred_language, last_login, rbac_permissions_json"
            )
            .eq("id", str(user_id))
            .single()
            .execute()
        )
        
        if not user_response.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "User not found",
                    "detail": "User profile does not exist in chamber_users table",
                    "code": 404,
                },
            )
        
        user_data = user_response.data
        
        # Get business group name if business_group_id exists
        business_group_name = None
        if user_data.get("business_group_id"):
            bg_response = (
                supabase.table("business_groups")
                .select("name")
                .eq("id", user_data["business_group_id"])
                .single()
                .execute()
            )
            if bg_response.data:
                business_group_name = bg_response.data["name"]
        
        # Extract permissions from rbac_permissions_json
        permissions = []
        if user_data.get("rbac_permissions_json"):
            permissions = user_data["rbac_permissions_json"].get("permissions", [])
        
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
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid request",
                "detail": "Invalid user ID format",
                "code": 400,
            },
        )
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "detail": "Failed to retrieve user profile",
                "code": 500,
            },
        )


@router.put(
    "/me",
    response_model=UserProfile,
    responses={
        400: {"model": ErrorResponse, "description": "Bad request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_current_user_profile(
    profile_update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update current authenticated user profile.
    Allows updating full_name, preferred_language, and notification_preferences.
    """
    try:
        user_id = UUID(current_user["sub"])
        
        from database import supabase
        
        # Build update payload
        update_data = {}
        
        if profile_update.full_name is not None:
            update_data["full_name"] = profile_update.full_name
        
        if profile_update.preferred_language is not None:
            update_data["preferred_language"] = profile_update.preferred_language
        
        if not update_data and profile_update.notification_preferences is None:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Bad request",
                    "detail": "No fields provided for update",
                    "code": 400,
                },
            )
        
        # Update chamber_users table
        if update_data:
            update_response = (
                supabase.table("chamber_users")
                .update(update_data)
                .eq("id", str(user_id))
                .execute()
            )
            
            if not update_response.data:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "User not found",
                        "detail": "User profile does not exist",
                        "code": 404,
                    },
                )
        
        # Update notification preferences if provided
        if profile_update.notification_preferences is not None:
            prefs = profile_update.notification_preferences
            
            # Check if notification preferences exist
            prefs_check = (
                supabase.table("chamber_notification_preferences")
                .select("user_id")
                .eq("user_id", str(user_id))
                .execute()
            )
            
            prefs_data = {
                "email_enabled": prefs.email_enabled,
                "proposal_status_updates": prefs.proposal_status_updates,
                "weekly_digest": prefs.weekly_digest,
                "compliance_alerts": prefs.compliance_alerts,
            }
            
            if prefs_check.data:
                # Update existing preferences
                supabase.table("chamber_notification_preferences").update(
                    prefs_data
                ).eq("user_id", str(user_id)).execute()
            else:
                # Insert new preferences
                prefs_data["user_id"] = str(user_id)
                supabase.table("chamber_notification_preferences").insert(
                    prefs_data
                ).execute()
        
        # Fetch updated user profile
        user_response = (
            supabase.table("chamber_users")
            .select(
                "id, email, role, full_name, chamber, business_group_id, "
                "preferred_language, last_login, rbac_permissions_json"
            )
            .eq("id", str(user_id))
            .single()
            .execute()
        )
        
        if not user_response.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "User not found",
                    "detail": "User profile does not exist after update",
                    "code": 404,
                },
            )
        
        user_data = user_response.data
        
        # Get business group name if business_group_id exists
        business_group_name = None
        if user_data.get("business_group_id"):
            bg_response = (
                supabase.table("business_groups")
                .select("name")
                .eq("id", user_data["business_group_id"])
                .single()
                .execute()
            )
            if bg_response.data:
                business_group_name = bg_response.data["name"]
        
        # Extract permissions
        permissions = []
        if user_data.get("rbac_permissions_json"):
            permissions = user_data["rbac_permissions_json"].get("permissions", [])
        
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
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid request",
                "detail": "Invalid user ID format",
                "code": 400,
            },
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "detail": "Failed to update user profile",
                "code": 500,
            },
        )


@router.get(
    "/{user_id}",
    response_model=UserProfile,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "User not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_user_by_id(
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Get user profile by ID.
    Requires analyst, business_group_lead, compliance_officer, executive, or admin role.
    """
    try:
        user_role = current_user.get("role")
        current_user_id = UUID(current_user["sub"])
        
        # Check permissions
        allowed_roles = ["analyst", "business_group_lead", "compliance_officer", "executive", "admin"]
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Insufficient permissions to view user profiles",
                    "code": 403,
                },
            )
        
        from database import supabase
        
        user_response = (
            supabase.table("chamber_users")
            .select(
                "id, email, role, full_name, chamber, business_group_id, "
                "preferred_language, last_login, rbac_permissions_json"
            )
            .eq("id", str(user_id))
            .single()
            .execute()
        )
        
        if not user_response.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "User not found",
                    "detail": f"User with ID {user_id} does not exist",
                    "code": 404,
                },
            )
        
        user_data = user_response.data
        
        # Business group leads can only view users in their business group
        if user_role == "business_group_lead":
            current_user_response = (
                supabase.table("chamber_users")
                .select("business_group_id")
                .eq("id", str(current_user_id))
                .single()
                .execute()
            )
            
            if not current_user_response.data:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Forbidden",
                        "detail": "Current user business group not found",
                        "code": 403,
                    },
                )
            
            current_bg_id = current_user_response.data.get("business_group_id")
            target_bg_id = user_data.get("business_group_id")
            
            if current_bg_id != target_bg_id:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Forbidden",
                        "detail": "Cannot view users outside your business group",
                        "code": 403,
                    },
                )
        
        # Get business group name
        business_group_name = None
        if user_data.get("business_group_id"):
            bg_response = (
                supabase.table("business_groups")
                .select("name")
                .eq("id", user_data["business_group_id"])
                .single()
                .execute()
            )
            if bg_response.data:
                business_group_name = bg_response.data["name"]
        
        # Extract permissions
        permissions = []
        if user_data.get("rbac_permissions_json"):
            permissions = user_data["rbac_permissions_json"].get("permissions", [])
        
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
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid request",
                "detail": "Invalid user ID format",
                "code": 400,
            },
        )
    except Exception as e:
        logger.error(f"Error fetching user by ID: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "detail": "Failed to retrieve user profile",
                "code": 500,
            },
        )

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone

from auth import get_current_user
from models.user import NotificationPreferences
from database import supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/notification-preferences",
    tags=["notification-preferences"],
    dependencies=[Depends(get_current_user)]
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=Dict[str, Any]
)
async def create_notification_preferences(
    preferences: NotificationPreferences,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Create notification preferences for current user.
    
    Args:
        preferences: Notification preferences settings
        current_user: Authenticated user from JWT
        
    Returns:
        Created preference record with user_id and timestamp
        
    Raises:
        HTTPException: 409 if preferences already exist, 500 on database error
    """
    try:
        user_id = current_user["id"]
        
        existing = supabase.table("chamber_notification_preferences").select("user_id").eq("user_id", str(user_id)).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Conflict", "detail": "Notification preferences already exist for this user", "code": "PREFERENCES_EXIST"}
            )
        
        insert_data = {
            "user_id": str(user_id),
            "email_enabled": preferences.email_enabled,
            "proposal_status_updates": preferences.proposal_status_updates,
            "weekly_digest": preferences.weekly_digest,
            "compliance_alerts": preferences.compliance_alerts,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("chamber_notification_preferences").insert(insert_data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Database Error", "detail": "Failed to create notification preferences", "code": "DB_INSERT_FAILED"}
            )
        
        logger.info(f"Created notification preferences for user {user_id}")
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating notification preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "Failed to create notification preferences", "code": "INTERNAL_ERROR"}
        )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any]
)
async def get_notification_preferences(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current user's notification preferences.
    
    Args:
        current_user: Authenticated user from JWT
        
    Returns:
        Notification preferences record
        
    Raises:
        HTTPException: 404 if preferences not found, 500 on database error
    """
    try:
        user_id = current_user["id"]
        
        response = supabase.table("chamber_notification_preferences").select("*").eq("user_id", str(user_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Notification preferences not found", "code": "PREFERENCES_NOT_FOUND"}
            )
        
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching notification preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "Failed to fetch notification preferences", "code": "INTERNAL_ERROR"}
        )


@router.put(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any]
)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Update current user's notification preferences.
    
    Args:
        preferences: Updated notification preferences
        current_user: Authenticated user from JWT
        
    Returns:
        Updated preferences record
        
    Raises:
        HTTPException: 404 if preferences not found, 500 on database error
    """
    try:
        user_id = current_user["id"]
        
        existing = supabase.table("chamber_notification_preferences").select("user_id").eq("user_id", str(user_id)).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Notification preferences not found", "code": "PREFERENCES_NOT_FOUND"}
            )
        
        update_data = {
            "email_enabled": preferences.email_enabled,
            "proposal_status_updates": preferences.proposal_status_updates,
            "weekly_digest": preferences.weekly_digest,
            "compliance_alerts": preferences.compliance_alerts,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("chamber_notification_preferences").update(update_data).eq("user_id", str(user_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Database Error", "detail": "Failed to update notification preferences", "code": "DB_UPDATE_FAILED"}
            )
        
        logger.info(f"Updated notification preferences for user {user_id}")
        return response.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "Failed to update notification preferences", "code": "INTERNAL_ERROR"}
        )


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, Any]
)
async def delete_notification_preferences(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Delete current user's notification preferences (reset to defaults).
    
    Args:
        current_user: Authenticated user from JWT
        
    Returns:
        Success message with deleted user_id
        
    Raises:
        HTTPException: 404 if preferences not found, 500 on database error
    """
    try:
        user_id = current_user["id"]
        
        existing = supabase.table("chamber_notification_preferences").select("user_id").eq("user_id", str(user_id)).execute()
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Notification preferences not found", "code": "PREFERENCES_NOT_FOUND"}
            )
        
        response = supabase.table("chamber_notification_preferences").delete().eq("user_id", str(user_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Database Error", "detail": "Failed to delete notification preferences", "code": "DB_DELETE_FAILED"}
            )
        
        logger.info(f"Deleted notification preferences for user {user_id}")
        return {
            "message": "Notification preferences deleted successfully",
            "user_id": str(user_id),
            "deleted_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting notification preferences: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "Failed to delete notification preferences", "code": "INTERNAL_ERROR"}
        )

from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from database import supabase
import logging

logger = logging.getLogger(__name__)


async def invalidate_session(user_id: UUID, access_token: str) -> bool:
    """
    Invalidate user session by recording logout event.
    
    Args:
        user_id: User UUID performing logout
        access_token: Access token to invalidate
        
    Returns:
        bool: True if logout recorded successfully
    """
    try:
        # Record logout event in user_sessions table
        logout_record = {
            "user_id": str(user_id),
            "event_type": "logout",
            "event_timestamp": datetime.now(timezone.utc).isoformat(),
            "access_token_hash": _hash_token(access_token),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase.table("user_sessions").insert(logout_record).execute()
        
        if not result.data:
            logger.warning(f"Failed to record logout event for user {user_id}")
            return False
            
        logger.info(f"User {user_id} logged out successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error invalidating session for user {user_id}: {str(e)}")
        return False


async def revoke_refresh_token(user_id: UUID, refresh_token: str) -> bool:
    """
    Revoke refresh token by marking it as invalid.
    
    Args:
        user_id: User UUID
        refresh_token: Refresh token to revoke
        
    Returns:
        bool: True if token revoked successfully
    """
    try:
        token_hash = _hash_token(refresh_token)
        
        # Update refresh token record to mark as revoked
        result = supabase.table("refresh_tokens").update({
            "is_revoked": True,
            "revoked_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("user_id", str(user_id)).eq("token_hash", token_hash).execute()
        
        if not result.data:
            logger.warning(f"No refresh token found to revoke for user {user_id}")
            return False
            
        logger.info(f"Refresh token revoked for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error revoking refresh token for user {user_id}: {str(e)}")
        return False


async def clear_active_sessions(user_id: UUID) -> bool:
    """
    Clear all active sessions for a user.
    
    Args:
        user_id: User UUID
        
    Returns:
        bool: True if sessions cleared successfully
    """
    try:
        # Mark all active sessions as expired
        result = supabase.table("user_sessions").update({
            "is_active": False,
            "ended_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("user_id", str(user_id)).eq("is_active", True).execute()
        
        logger.info(f"Cleared active sessions for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error clearing sessions for user {user_id}: {str(e)}")
        return False


async def get_session_history(user_id: UUID, page: int = 1, page_size: int = 20) -> Optional[dict]:
    """
    Get session history for a user with pagination.
    
    Args:
        user_id: User UUID
        page: Page number (1-indexed)
        page_size: Number of records per page
        
    Returns:
        dict with sessions and pagination info, or None if error
    """
    try:
        offset = (page - 1) * page_size
        
        # Get total count
        count_result = supabase.table("user_sessions").select(
            "id",
            count="exact"
        ).eq("user_id", str(user_id)).execute()
        
        total = count_result.count if count_result.count is not None else 0
        
        # Get paginated sessions
        result = supabase.table("user_sessions").select(
            "id, event_type, event_timestamp, ip_address, user_agent, is_active, ended_at, created_at"
        ).eq("user_id", str(user_id)).order(
            "event_timestamp",
            desc=True
        ).range(offset, offset + page_size - 1).execute()
        
        if not result.data:
            return {
                "sessions": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
        
        total_pages = (total + page_size - 1) // page_size
        
        return {
            "sessions": result.data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Error fetching session history for user {user_id}: {str(e)}")
        return None


def _hash_token(token: str) -> str:
    """
    Hash a token for secure storage.
    
    Args:
        token: Token string to hash
        
    Returns:
        str: Hashed token
    """
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()

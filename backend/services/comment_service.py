from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID
from database import supabase


def create_comment(
    user_id: str,
    proposal_id: str,
    comment_text: str,
    visibility: str = "internal"
) -> Optional[dict]:
    """
    Create a new comment on a proposal.
    
    Args:
        user_id: UUID of the user creating the comment
        proposal_id: UUID of the proposal being commented on
        comment_text: Comment text (max 2000 chars)
        visibility: Comment visibility ("internal" or "vendor_visible")
    
    Returns:
        Comment dict with id, proposal_id, user_id, comment_text, created_at, visibility
        or None if creation fails
    """
    try:
        # First verify the proposal exists and user has access to it
        proposal_check = (
            supabase.table("proposals")
            .select("id, submitter_id, business_group_id")
            .eq("id", proposal_id)
            .eq("deleted_at", None)
            .maybe_single()
            .execute()
        )
        
        if not proposal_check.data:
            return None
        
        # Verify user has permission to comment
        # User can comment if:
        # 1. They are the proposal submitter (vendor)
        # 2. They are a chamber staff member (analyst, executive, compliance_officer, etc.)
        # For now, we allow all authenticated users to comment
        # Additional role-based checks can be added here
        
        comment_data = {
            "proposal_id": proposal_id,
            "user_id": user_id,
            "comment_text": comment_text.strip(),
            "visibility": visibility,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = (
            supabase.table("proposal_comments")
            .insert(comment_data)
            .execute()
        )
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        return None
        
    except Exception:
        return None


def list_comments(
    user_id: str,
    proposal_id: str,
    page: int = 1,
    page_size: int = 50
) -> Optional[dict]:
    """
    List comments for a proposal with pagination.
    
    Args:
        user_id: UUID of the requesting user
        proposal_id: UUID of the proposal
        page: Page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Dict with comments list and pagination metadata, or None if proposal not found
    """
    try:
        # First verify the proposal exists and user has access
        proposal_check = (
            supabase.table("proposals")
            .select("id, submitter_id")
            .eq("id", proposal_id)
            .eq("deleted_at", None)
            .maybe_single()
            .execute()
        )
        
        if not proposal_check.data:
            return None
        
        proposal = proposal_check.data
        is_vendor = proposal["submitter_id"] == user_id
        
        # Build query
        query = (
            supabase.table("proposal_comments")
            .select("*", count="exact")
            .eq("proposal_id", proposal_id)
        )
        
        # If user is a vendor, only show vendor_visible comments
        # Chamber staff see all comments
        if is_vendor:
            query = query.eq("visibility", "vendor_visible")
        
        # Get total count first
        count_result = query.execute()
        total = count_result.count if count_result.count is not None else 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        result = (
            query
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        
        comments = result.data if result.data else []
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        return {
            "comments": comments,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
        
    except Exception:
        return None


def get_comment_by_id(
    user_id: str,
    comment_id: str
) -> Optional[dict]:
    """
    Get a comment by ID.
    
    Args:
        user_id: UUID of the requesting user
        comment_id: UUID of the comment
    
    Returns:
        Comment dict or None if not found or access denied
    """
    try:
        result = (
            supabase.table("proposal_comments")
            .select("*, proposals!inner(submitter_id)")
            .eq("id", comment_id)
            .maybe_single()
            .execute()
        )
        
        if not result.data:
            return None
        
        comment = result.data
        
        # Check visibility permissions
        is_vendor = comment["proposals"]["submitter_id"] == user_id
        
        if is_vendor and comment["visibility"] == "internal":
            return None
        
        # Remove nested proposals data
        comment.pop("proposals", None)
        
        return comment
        
    except Exception:
        return None


def update_comment(
    user_id: str,
    comment_id: str,
    comment_text: Optional[str] = None,
    visibility: Optional[str] = None
) -> Optional[dict]:
    """
    Update a comment (only by the comment creator).
    
    Args:
        user_id: UUID of the requesting user
        comment_id: UUID of the comment to update
        comment_text: New comment text (optional)
        visibility: New visibility setting (optional)
    
    Returns:
        Updated comment dict or None if not found or not authorized
    """
    try:
        # Verify ownership
        existing = (
            supabase.table("proposal_comments")
            .select("id, user_id")
            .eq("id", comment_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        
        if not existing.data:
            return None
        
        update_data = {}
        
        if comment_text is not None:
            update_data["comment_text"] = comment_text.strip()
        
        if visibility is not None:
            update_data["visibility"] = visibility
        
        if not update_data:
            # No updates requested, return existing
            return existing.data
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = (
            supabase.table("proposal_comments")
            .update(update_data)
            .eq("id", comment_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        return None
        
    except Exception:
        return None


def delete_comment(
    user_id: str,
    comment_id: str
) -> bool:
    """
    Soft delete a comment (only by comment creator or admin).
    
    Args:
        user_id: UUID of the requesting user
        comment_id: UUID of the comment to delete
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        # Verify ownership
        existing = (
            supabase.table("proposal_comments")
            .select("id, user_id")
            .eq("id", comment_id)
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        
        if not existing.data:
            return False
        
        # Soft delete by setting deleted_at
        result = (
            supabase.table("proposal_comments")
            .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
            .eq("id", comment_id)
            .eq("user_id", user_id)
            .execute()
        )
        
        return result.data is not None and len(result.data) > 0
        
    except Exception:
        return False


def list_comments_by_user(
    user_id: str,
    page: int = 1,
    page_size: int = 50
) -> Optional[dict]:
    """
    List all comments created by a user.
    
    Args:
        user_id: UUID of the user
        page: Page number (1-indexed)
        page_size: Number of items per page
    
    Returns:
        Dict with comments list and pagination metadata
    """
    try:
        # Get total count
        count_result = (
            supabase.table("proposal_comments")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .execute()
        )
        
        total = count_result.count if count_result.count is not None else 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        result = (
            supabase.table("proposal_comments")
            .select("*")
            .eq("user_id", user_id)
            .is_("deleted_at", "null")
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        
        comments = result.data if result.data else []
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        return {
            "comments": comments,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
        
    except Exception:
        return None

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from auth import get_current_user
from database import supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["comments"])


@router.get(
    "/comment-counts",
    status_code=200,
)
async def get_comment_counts(
    proposal_ids: str = Query(..., description="Comma-separated proposal UUIDs"),
    current_user: dict = Depends(get_current_user),
):
    """Return comment counts for a list of proposal IDs."""
    try:
        ids = [pid.strip() for pid in proposal_ids.split(",") if pid.strip()]
        if not ids:
            return {"counts": {}}

        response = (
            supabase.table("chamber_comments")
            .select("proposal_id", count="exact")
            .in_("proposal_id", ids)
            .execute()
        )

        # Count per proposal
        counts = {}
        for row in response.data or []:
            pid = row["proposal_id"]
            counts[pid] = counts.get(pid, 0) + 1

        return {"counts": counts}
    except Exception as e:
        logger.error(f"Failed to get comment counts: {e}")
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "detail": str(e), "code": 500})


@router.get(
    "/{proposal_id}/comments",
    status_code=200,
)
async def list_proposal_comments(
    proposal_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List comments for a proposal with user info (full_name, role)."""
    try:
        # Verify proposal exists
        proposal_response = (
            supabase.table("chamber_proposals")
            .select("id, submitter_id")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )
        if not proposal_response.data:
            raise HTTPException(
                status_code=404,
                detail={"error": "Not Found", "detail": f"Proposal {proposal_id} not found", "code": 404},
            )

        proposal = proposal_response.data

        # Build query — join chamber_users for name + role
        offset = (page - 1) * page_size
        query = (
            supabase.table("chamber_comments")
            .select("id, proposal_id, user_id, comment_text, visibility, created_at, updated_at, chamber_users!inner(full_name, role)", count="exact")
            .eq("proposal_id", str(proposal_id))
        )

        # Vendors only see vendor_visible comments
        user_role = current_user.get("role", "vendor")
        if user_role == "vendor":
            if str(proposal["submitter_id"]) != str(current_user["id"]):
                raise HTTPException(
                    status_code=403,
                    detail={"error": "Forbidden", "detail": "Vendors can only view comments on their own proposals", "code": 403},
                )
            query = query.eq("visibility", "vendor_visible")

        response = query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()

        total = response.count if response.count is not None else 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        comments = []
        for c in response.data or []:
            user_info = c.get("chamber_users", {})
            comments.append({
                "id": c["id"],
                "proposal_id": c["proposal_id"],
                "user_id": c["user_id"],
                "user_name": user_info.get("full_name", "Unknown"),
                "user_role": user_info.get("role", "vendor"),
                "comment_text": c["comment_text"],
                "visibility": c["visibility"],
                "created_at": c["created_at"],
            })

        return {
            "comments": comments,
            "pagination": {"total": total, "page": page, "page_size": page_size, "total_pages": total_pages},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list comments: {e}")
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "detail": str(e), "code": 500})


@router.post(
    "/{proposal_id}/comments",
    status_code=201,
)
async def create_proposal_comment(
    proposal_id: UUID,
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """Create a comment on a proposal. Returns created comment with user info."""
    try:
        comment_text = (payload.get("content") or payload.get("comment_text") or "").strip()
        if not comment_text:
            raise HTTPException(status_code=422, detail={"error": "Validation Error", "detail": "Comment text is required", "code": 422})
        if len(comment_text) > 2000:
            raise HTTPException(status_code=422, detail={"error": "Validation Error", "detail": "Comment text exceeds 2000 characters", "code": 422})

        visibility = payload.get("visibility", "internal")
        if visibility not in ("internal", "vendor_visible"):
            visibility = "internal"

        # Verify proposal exists
        proposal_response = (
            supabase.table("chamber_proposals")
            .select("id, submitter_id")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )
        if not proposal_response.data:
            raise HTTPException(status_code=404, detail={"error": "Not Found", "detail": f"Proposal {proposal_id} not found", "code": 404})

        proposal = proposal_response.data
        user_id = str(current_user["id"])
        user_role = current_user.get("role", "vendor")

        # Role-based access: vendors can only comment on own proposals
        allowed_roles = ["analyst", "business_group_lead", "compliance_officer", "executive", "admin"]
        if user_role == "vendor":
            if str(proposal["submitter_id"]) != user_id:
                raise HTTPException(status_code=403, detail={"error": "Forbidden", "detail": "Vendors can only comment on their own proposals", "code": 403})
        elif user_role not in allowed_roles:
            raise HTTPException(status_code=403, detail={"error": "Forbidden", "detail": "Insufficient permissions to add comments", "code": 403})

        # Insert comment
        from datetime import datetime, timezone
        comment_data = {
            "proposal_id": str(proposal_id),
            "user_id": user_id,
            "comment_text": comment_text,
            "visibility": visibility,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        result = supabase.table("chamber_comments").insert(comment_data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail={"error": "Internal server error", "detail": "Failed to create comment", "code": 500})

        created = result.data[0]

        # Get user full_name + role for the response
        user_response = (
            supabase.table("chamber_users")
            .select("full_name, role")
            .eq("id", user_id)
            .maybe_single()
            .execute()
        )
        user_info = user_response.data if user_response.data else {}

        return {
            "id": created["id"],
            "proposal_id": created["proposal_id"],
            "user_id": created["user_id"],
            "user_name": user_info.get("full_name", "Unknown"),
            "user_role": user_info.get("role", user_role),
            "comment_text": created["comment_text"],
            "visibility": created["visibility"],
            "created_at": created["created_at"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create comment: {e}")
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "detail": str(e), "code": 500})


@router.delete(
    "/{proposal_id}/comments/{comment_id}",
    status_code=204,
)
async def delete_proposal_comment(
    proposal_id: UUID,
    comment_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Delete a comment. Only the author or admin can delete."""
    try:
        # Fetch comment
        comment_response = (
            supabase.table("chamber_comments")
            .select("id, user_id, proposal_id")
            .eq("id", str(comment_id))
            .eq("proposal_id", str(proposal_id))
            .maybe_single()
            .execute()
        )

        if not comment_response.data:
            raise HTTPException(status_code=404, detail={"error": "Not Found", "detail": f"Comment {comment_id} not found", "code": 404})

        comment = comment_response.data

        # Only author or admin can delete
        if str(comment["user_id"]) != str(current_user["id"]) and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail={"error": "Forbidden", "detail": "You can only delete your own comments", "code": 403})

        supabase.table("chamber_comments").delete().eq("id", str(comment_id)).execute()
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete comment: {e}")
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "detail": str(e), "code": 500})

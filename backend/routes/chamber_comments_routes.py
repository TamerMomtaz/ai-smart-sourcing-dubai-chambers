from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from datetime import datetime

from auth import get_current_user
from models.auth import UserInfo
from models.comment import CommentCreate, CommentResponse
from models.common import ErrorResponse, PaginationResponse
from services import comment_service
from database import supabase

router = APIRouter(prefix="/chamber-comments", tags=["Chamber Comments"])


@router.post(
    "/proposals/{proposal_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_comment(
    proposal_id: UUID,
    comment_data: CommentCreate,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Create a new comment on a proposal.
    Requires analyst, business_group_lead, compliance_officer, or executive role.
    Vendors can only comment on their own proposals.
    """
    try:
        # Verify proposal exists and check access
        proposal_response = (
            supabase.table("chamber_proposals")
            .select("id, submitter_id, business_group_id")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )

        if not proposal_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Proposal not found",
                    "detail": f"Proposal {proposal_id} does not exist",
                    "code": "PROPOSAL_NOT_FOUND",
                },
            )

        proposal = proposal_response.data

        # Role-based access control
        if current_user.role == "vendor":
            if str(proposal["submitter_id"]) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Access denied",
                        "detail": "Vendors can only comment on their own proposals",
                        "code": "VENDOR_ACCESS_DENIED",
                    },
                )
        elif current_user.role == "business_group_lead":
            # Business group lead can only comment on proposals in their sector
            user_response = (
                supabase.table("chamber_users")
                .select("business_group_id")
                .eq("id", str(current_user.id))
                .maybe_single()
                .execute()
            )
            if not user_response.data or str(user_response.data.get("business_group_id")) != str(
                proposal.get("business_group_id")
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Access denied",
                        "detail": "Business group lead can only comment on proposals in their sector",
                        "code": "SECTOR_ACCESS_DENIED",
                    },
                )
        elif current_user.role not in ["analyst", "compliance_officer", "executive", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Access denied",
                    "detail": "Insufficient permissions to create comments",
                    "code": "INSUFFICIENT_PERMISSIONS",
                },
            )

        # Create comment
        comment = comment_service.create_comment(
            user_id=current_user.id,
            proposal_id=proposal_id,
            comment_text=comment_data.comment_text.strip(),
            visibility=comment_data.visibility,
        )

        if not comment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Comment creation failed",
                    "detail": "Failed to create comment in database",
                    "code": "COMMENT_CREATION_FAILED",
                },
            )

        # Get user name for response
        user_response = (
            supabase.table("chamber_users")
            .select("full_name")
            .eq("id", str(current_user.id))
            .maybe_single()
            .execute()
        )
        user_name = user_response.data.get("full_name") if user_response.data else "Unknown User"

        return CommentResponse(
            comment_id=comment["id"],
            proposal_id=comment["proposal_id"],
            user_id=comment["user_id"],
            comment_text=comment["comment_text"],
            created_at=comment["created_at"],
            visibility=comment["visibility"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": str(e),
                "code": "INTERNAL_ERROR",
            },
        )


@router.get(
    "/proposals/{proposal_id}/comments",
    response_model=dict,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_comments(
    proposal_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    List comments on a proposal with pagination.
    Vendors see only vendor_visible comments.
    Analysts and above see all comments.
    """
    try:
        # Verify proposal exists and check access
        proposal_response = (
            supabase.table("chamber_proposals")
            .select("id, submitter_id, business_group_id")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )

        if not proposal_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Proposal not found",
                    "detail": f"Proposal {proposal_id} does not exist",
                    "code": "PROPOSAL_NOT_FOUND",
                },
            )

        proposal = proposal_response.data

        # Role-based access control
        if current_user.role == "vendor":
            if str(proposal["submitter_id"]) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Access denied",
                        "detail": "Vendors can only view comments on their own proposals",
                        "code": "VENDOR_ACCESS_DENIED",
                    },
                )
        elif current_user.role == "business_group_lead":
            user_response = (
                supabase.table("chamber_users")
                .select("business_group_id")
                .eq("id", str(current_user.id))
                .maybe_single()
                .execute()
            )
            if not user_response.data or str(user_response.data.get("business_group_id")) != str(
                proposal.get("business_group_id")
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Access denied",
                        "detail": "Business group lead can only view comments on proposals in their sector",
                        "code": "SECTOR_ACCESS_DENIED",
                    },
                )

        # Build query
        offset = (page - 1) * page_size
        query = (
            supabase.table("chamber_comments")
            .select("*, chamber_users!inner(full_name)", count="exact")
            .eq("proposal_id", str(proposal_id))
        )

        # Filter visibility for vendors
        if current_user.role == "vendor":
            query = query.eq("visibility", "vendor_visible")

        # Execute query with pagination
        response = query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()

        total = response.count if response.count is not None else 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        comments = []
        for comment in response.data:
            comments.append(
                {
                    "comment_id": comment["id"],
                    "proposal_id": comment["proposal_id"],
                    "user_id": comment["user_id"],
                    "user_name": comment["chamber_users"]["full_name"],
                    "comment_text": comment["comment_text"],
                    "created_at": comment["created_at"],
                    "visibility": comment["visibility"],
                }
            )

        return {
            "comments": comments,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": str(e),
                "code": "INTERNAL_ERROR",
            },
        )


@router.get(
    "/{comment_id}",
    response_model=CommentResponse,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Comment not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_comment(
    comment_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Get a specific comment by ID.
    Access control based on proposal ownership and comment visibility.
    """
    try:
        # Fetch comment with proposal info
        comment_response = (
            supabase.table("chamber_comments")
            .select("*, chamber_proposals!inner(submitter_id, business_group_id)")
            .eq("id", str(comment_id))
            .maybe_single()
            .execute()
        )

        if not comment_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Comment not found",
                    "detail": f"Comment {comment_id} does not exist",
                    "code": "COMMENT_NOT_FOUND",
                },
            )

        comment = comment_response.data
        proposal = comment["chamber_proposals"]

        # Role-based access control
        if current_user.role == "vendor":
            if str(proposal["submitter_id"]) != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Access denied",
                        "detail": "Vendors can only view comments on their own proposals",
                        "code": "VENDOR_ACCESS_DENIED",
                    },
                )
            if comment["visibility"] != "vendor_visible":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Access denied",
                        "detail": "This comment is internal only",
                        "code": "INTERNAL_COMMENT",
                    },
                )
        elif current_user.role == "business_group_lead":
            user_response = (
                supabase.table("chamber_users")
                .select("business_group_id")
                .eq("id", str(current_user.id))
                .maybe_single()
                .execute()
            )
            if not user_response.data or str(user_response.data.get("business_group_id")) != str(
                proposal.get("business_group_id")
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Access denied",
                        "detail": "Business group lead can only view comments on proposals in their sector",
                        "code": "SECTOR_ACCESS_DENIED",
                    },
                )

        return CommentResponse(
            comment_id=comment["id"],
            proposal_id=comment["proposal_id"],
            user_id=comment["user_id"],
            comment_text=comment["comment_text"],
            created_at=comment["created_at"],
            visibility=comment["visibility"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": str(e),
                "code": "INTERNAL_ERROR",
            },
        )


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Comment not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_comment(
    comment_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Delete a comment.
    Only the comment author or admin can delete comments.
    """
    try:
        # Fetch comment
        comment_response = (
            supabase.table("chamber_comments")
            .select("id, user_id")
            .eq("id", str(comment_id))
            .maybe_single()
            .execute()
        )

        if not comment_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Comment not found",
                    "detail": f"Comment {comment_id} does not exist",
                    "code": "COMMENT_NOT_FOUND",
                },
            )

        comment = comment_response.data

        # Only comment author or admin can delete
        if str(comment["user_id"]) != str(current_user.id) and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Access denied",
                    "detail": "You can only delete your own comments",
                    "code": "DELETE_ACCESS_DENIED",
                },
            )

        # Delete comment
        delete_response = supabase.table("chamber_comments").delete().eq("id", str(comment_id)).execute()

        if not delete_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Delete failed",
                    "detail": "Failed to delete comment from database",
                    "code": "DELETE_FAILED",
                },
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": str(e),
                "code": "INTERNAL_ERROR",
            },
        )

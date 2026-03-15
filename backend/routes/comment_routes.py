from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Path
from models.comment import CommentCreate, CommentResponse
from models.common import ErrorResponse
from auth.dependencies import get_current_user
from services.comment_service import create_comment
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/proposals", tags=["comments"])


@router.post(
    "/{proposal_id}/comments",
    response_model=CommentResponse,
    status_code=201,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        422: {"model": ErrorResponse, "description": "Comment text too long"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def add_comment_to_proposal(
    proposal_id: UUID = Path(..., description="Proposal UUID"),
    payload: CommentCreate = ...,
    current_user: dict = Depends(get_current_user),
):
    """
    Add a comment to a proposal.

    - **proposal_id**: UUID of the proposal to comment on
    - **comment_text**: Comment content (max 2000 characters)
    - **visibility**: Comment visibility - 'internal' (default) or 'vendor_visible'

    Requires authentication. Analysts, business group leads, compliance officers, and executives can comment.
    Comments are linked to the authenticated user.
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user.get("role", "")

        # Validate role permissions for commenting
        allowed_roles = ["analyst", "business_group_lead", "compliance_officer", "executive", "admin"]
        if user_role not in allowed_roles:
            logger.warning(f"User {user_id} with role {user_role} attempted to comment on proposal {proposal_id}")
            raise HTTPException(
                status_code=403,
                detail={"error": "Forbidden", "detail": "Insufficient permissions to add comments", "code": 403},
            )

        # Validate comment text length
        if len(payload.comment_text) > 2000:
            raise HTTPException(
                status_code=422,
                detail={"error": "Validation Error", "detail": "Comment text exceeds 2000 characters", "code": 422},
            )

        # Create comment
        comment = create_comment(
            user_id=user_id,
            proposal_id=proposal_id,
            comment_text=payload.comment_text.strip(),
            visibility=payload.visibility,
        )

        if not comment:
            logger.error(f"Failed to create comment for proposal {proposal_id} by user {user_id}")
            raise HTTPException(
                status_code=404,
                detail={"error": "Not Found", "detail": "Proposal not found or access denied", "code": 404},
            )

        return CommentResponse(
            comment_id=UUID(comment["id"]),
            proposal_id=UUID(comment["proposal_id"]),
            user_id=UUID(comment["user_id"]),
            comment_text=comment["comment_text"],
            created_at=comment["created_at"],
            visibility=comment["visibility"],
        )

    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"Value error creating comment: {str(ve)}")
        raise HTTPException(
            status_code=422,
            detail={"error": "Validation Error", "detail": str(ve), "code": 422},
        )
    except Exception as e:
        logger.exception(f"Unexpected error creating comment for proposal {proposal_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "Failed to create comment", "code": 500},
        )

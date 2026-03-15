from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
import logging

from models.proposal import DuplicateCheckResponse
from models.common import ErrorResponse
from auth import get_current_user
from services.duplicate_check_service import run_duplicate_check

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/proposals",
    tags=["duplicate-check"],
)


@router.post(
    "/{proposal_id}/duplicate-check",
    response_model=DuplicateCheckResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Run semantic similarity check against existing proposals",
)
async def run_duplicate_check_endpoint(
    proposal_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> DuplicateCheckResponse:
    """
    Run semantic similarity check against existing proposals.

    This endpoint performs AI-powered semantic analysis to detect potential duplicates.
    It compares the target proposal against all previously submitted proposals
    and returns a list of similar proposals with similarity scores.

    **Authentication Required**: Yes (JWT)

    **Rate Limit**: 30 requests per minute

    **Permissions Required**:
    - Analysts: Can check any proposal
    - Business Group Leads: Can check proposals in their sector
    - Vendors: Can check only their own proposals

    **Args**:
    - **proposal_id**: UUID of the proposal to check for duplicates

    **Returns**:
    - **proposal_id**: UUID of the checked proposal
    - **is_duplicate**: Boolean flag indicating if duplicates were found
    - **similar_proposals**: List of similar proposals with scores

    **Error Responses**:
    - **401**: Unauthorized - Invalid or missing JWT token
    - **404**: Proposal not found or user does not have access
    - **500**: Internal server error during duplicate check
    """
    try:
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")

        if not user_id:
            logger.error("Missing user_id in current_user context")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Unauthorized",
                    "detail": "User ID missing from authentication context",
                    "code": "MISSING_USER_ID",
                },
            )

        logger.info(
            f"User {user_id} (role: {user_role}) running duplicate check on proposal {proposal_id}"
        )

        # Call service layer to run duplicate check
        result = await run_duplicate_check(
            user_id=str(user_id),
            proposal_id=proposal_id,
        )

        if result is None:
            logger.warning(
                f"Proposal {proposal_id} not found or user {user_id} lacks access"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "NotFound",
                    "detail": f"Proposal {proposal_id} not found or you do not have permission to access it",
                    "code": "PROPOSAL_NOT_FOUND",
                },
            )

        logger.info(
            f"Duplicate check completed for proposal {proposal_id}: is_duplicate={result.get('is_duplicate')}, similar_count={len(result.get('similar_proposals', []))}"
        )

        return DuplicateCheckResponse(
            proposal_id=result["proposal_id"],
            is_duplicate=result["is_duplicate"],
            similar_proposals=result.get("similar_proposals", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during duplicate check for proposal {proposal_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "detail": "An unexpected error occurred while running duplicate check",
                "code": "DUPLICATE_CHECK_FAILED",
            },
        )

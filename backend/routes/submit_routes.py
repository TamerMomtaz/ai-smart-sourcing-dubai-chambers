from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
import logging

from auth import get_current_user
from models.auth import UserInfo
from models.proposal import ProposalSubmitResponse
from models.common import ErrorResponse
from services.submit_service import submit_proposal

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/proposals",
    tags=["submit"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)


@router.post(
    "/{proposal_id}/submit",
    response_model=ProposalSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Finalize proposal submission and trigger AI evaluation queue",
    description="""
    Finalize proposal submission and trigger AI evaluation queue.
    
    This endpoint:
    - Validates proposal exists and belongs to the authenticated vendor
    - Verifies at least one document has been uploaded
    - Updates proposal status to 'queued_for_evaluation'
    - Calculates estimated completion time (5 minutes from submission)
    - Returns proposal ID, status, and estimated completion timestamp
    
    **Access Control:**
    - Requires authentication (vendor role)
    - Vendors can only submit their own proposals
    - Proposals must be in 'draft' or 'submitted' status
    
    **Error Cases:**
    - 400: Cannot submit proposal without documents
    - 401: Unauthorized (invalid or missing token)
    - 403: Forbidden (attempting to submit another vendor's proposal)
    - 404: Proposal not found
    - 500: Internal server error
    """,
)
async def submit_proposal_endpoint(
    proposal_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
) -> ProposalSubmitResponse:
    """
    Finalize proposal submission and trigger AI evaluation queue.
    
    Args:
        proposal_id: UUID of proposal to submit
        current_user: Authenticated user from JWT
        
    Returns:
        ProposalSubmitResponse with proposal_id, status, and estimated_completion
        
    Raises:
        HTTPException: 400, 401, 403, 404, or 500
    """
    try:
        # Validate vendor role
        if current_user.role != "vendor":
            logger.warning(
                f"Non-vendor user {current_user.id} attempted to submit proposal {proposal_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Only vendors can submit proposals",
                    "code": "INVALID_ROLE",
                },
            )

        # Call service layer
        result = submit_proposal(
            user_id=current_user.id,
            proposal_id=proposal_id,
        )

        if not result:
            logger.error(
                f"Proposal submission failed for proposal_id={proposal_id}, user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not Found",
                    "detail": "Proposal not found or cannot be submitted",
                    "code": "PROPOSAL_NOT_FOUND",
                },
            )

        # Handle specific error cases from service
        if "error" in result:
            error_code = result.get("code", "UNKNOWN_ERROR")
            error_detail = result.get("detail", "An error occurred")
            
            if error_code == "NO_DOCUMENTS":
                logger.warning(
                    f"Proposal {proposal_id} submission rejected: no documents uploaded"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Bad Request",
                        "detail": error_detail,
                        "code": error_code,
                    },
                )
            elif error_code == "INVALID_STATUS":
                logger.warning(
                    f"Proposal {proposal_id} submission rejected: invalid status"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Bad Request",
                        "detail": error_detail,
                        "code": error_code,
                    },
                )
            elif error_code == "UNAUTHORIZED":
                logger.warning(
                    f"User {current_user.id} unauthorized to submit proposal {proposal_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Forbidden",
                        "detail": error_detail,
                        "code": error_code,
                    },
                )
            else:
                logger.error(
                    f"Unexpected error submitting proposal {proposal_id}: {error_detail}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "Internal Server Error",
                        "detail": error_detail,
                        "code": error_code,
                    },
                )

        # Calculate estimated completion (5 minutes from now)
        estimated_completion = datetime.now(timezone.utc) + timedelta(minutes=5)

        # Log success
        logger.info(
            f"Proposal {proposal_id} submitted successfully by user {current_user.id}, "
            f"status=queued_for_evaluation, estimated_completion={estimated_completion.isoformat()}"
        )

        # Return response
        return ProposalSubmitResponse(
            proposal_id=proposal_id,
            status="queued_for_evaluation",
            estimated_completion=estimated_completion,
        )

    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        # Catch-all for unexpected errors
        logger.exception(
            f"Unexpected error in submit_proposal_endpoint for proposal_id={proposal_id}, "
            f"user_id={current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while submitting the proposal",
                "code": "INTERNAL_ERROR",
            },
        )

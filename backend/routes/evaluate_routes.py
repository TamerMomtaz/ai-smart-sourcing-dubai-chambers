from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from models.batch import BatchEvaluateRequest, BatchJobResponse
from models.common import ErrorResponse
from auth import get_current_user
from services.evaluate_service import trigger_proposal_evaluation, trigger_batch_evaluation
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["evaluate"])


@router.post(
    "/proposals/{proposal_id}/evaluate",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - only analysts can trigger re-evaluation"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        409: {"model": ErrorResponse, "description": "Proposal is already being evaluated"},
    },
)
async def evaluate_proposal(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger manual re-evaluation of proposal (analyst only).
    
    This endpoint queues a proposal for AI-powered re-evaluation.
    Only users with analyst role or higher can trigger evaluations.
    
    Returns:
        - proposal_id: UUID of the proposal
        - status: Current status (queued_for_evaluation)
        - job_id: UUID of the evaluation job
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid user session", "code": 401}
            )
        
        # Verify analyst role
        allowed_roles = ["analyst", "business_group_lead", "compliance_officer", "executive", "admin"]
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Only analysts can trigger re-evaluation", "code": 403}
            )
        
        # Trigger evaluation
        result = trigger_proposal_evaluation(user_id=UUID(user_id), proposal_id=proposal_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Proposal not found or already being evaluated", "code": 404}
            )
        
        # Check if already evaluating
        if result.get("status") == "evaluating":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Conflict", "detail": "Proposal is already being evaluated", "code": 409}
            )
        
        return {
            "proposal_id": str(result.get("proposal_id")),
            "status": result.get("status", "queued_for_evaluation"),
            "job_id": str(result.get("job_id"))
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering evaluation for proposal {proposal_id}: {str(e)}")
        is_ai_failure = "All AI providers failed" in str(e)
        raise HTTPException(
            status_code=503 if is_ai_failure else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "AI service temporarily busy. Please try again in 1-2 minutes."} if is_ai_failure else {"error": "Internal Server Error", "detail": "Failed to trigger evaluation", "code": 500}
        )


@router.post(
    "/batch/proposals/evaluate",
    response_model=BatchJobResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - analyst role required"},
        422: {"model": ErrorResponse, "description": "Batch size exceeds limit of 100"},
    },
)
async def batch_evaluate_proposals(
    request: BatchEvaluateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger batch evaluation for multiple proposals (analyst only).
    
    This endpoint allows analysts to queue multiple proposals for evaluation in a single request.
    Maximum batch size is 100 proposals.
    
    Args:
        request: BatchEvaluateRequest containing list of proposal_ids
    
    Returns:
        - batch_job_id: UUID of the batch job
        - proposal_count: Number of proposals in batch
        - status: Batch job status (queued)
        - estimated_completion: Estimated completion timestamp
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid user session", "code": 401}
            )
        
        # Verify analyst role
        allowed_roles = ["analyst", "business_group_lead", "compliance_officer", "executive", "admin"]
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Analyst role required", "code": 403}
            )
        
        # Validate batch size
        if len(request.proposal_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Validation Error", "detail": "Batch size exceeds limit of 100", "code": 422}
            )
        
        if len(request.proposal_ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "Validation Error", "detail": "Batch must contain at least one proposal_id", "code": 422}
            )
        
        # Trigger batch evaluation
        result = trigger_batch_evaluation(user_id=UUID(user_id), proposal_ids=request.proposal_ids)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Internal Server Error", "detail": "Failed to create batch evaluation job", "code": 500}
            )
        
        return BatchJobResponse(
            batch_job_id=result.get("batch_job_id"),
            proposal_count=result.get("proposal_count"),
            status=result.get("status", "queued"),
            estimated_completion=result.get("estimated_completion")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering batch evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "Failed to trigger batch evaluation", "code": 500}
        )

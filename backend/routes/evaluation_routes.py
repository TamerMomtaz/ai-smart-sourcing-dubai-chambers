from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from models import EvaluationDetail, ErrorResponse
from auth import get_current_user
from services import evaluation_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/evaluations",
    tags=["evaluations"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Evaluation not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)


@router.get(
    "/{proposal_id}",
    response_model=EvaluationDetail,
    status_code=status.HTTP_200_OK,
    summary="Get detailed evaluation results for proposal",
    description="Retrieve comprehensive evaluation results including scores, reasoning, AI interactions, and security checks for a specific proposal. Requires authentication.",
)
async def get_evaluation_by_proposal(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> EvaluationDetail:
    """
    Get detailed evaluation results for a proposal.
    
    Args:
        proposal_id: UUID of the proposal to retrieve evaluation for
        current_user: Authenticated user from JWT token
    
    Returns:
        EvaluationDetail: Complete evaluation data including scores, reasoning, and AI interactions
    
    Raises:
        HTTPException: 401 if unauthorized, 403 if forbidden, 404 if not found
    """
    try:
        user_id = UUID(current_user["user_id"])
        user_role = current_user.get("role", "")
        
        logger.info(
            f"User {user_id} (role: {user_role}) requesting evaluation for proposal {proposal_id}"
        )
        
        # Call service layer to get evaluation
        evaluation = evaluation_service.get_by_proposal_id(
            user_id=user_id,
            proposal_id=proposal_id
        )
        
        if not evaluation:
            logger.warning(
                f"Evaluation not found for proposal {proposal_id} by user {user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Evaluation not found",
                    "detail": f"No evaluation exists for proposal {proposal_id} or you do not have permission to access it",
                    "code": "EVALUATION_NOT_FOUND",
                },
            )
        
        # Transform service response to Pydantic model
        evaluation_detail = EvaluationDetail(
            id=UUID(evaluation["id"]),
            proposal_id=UUID(evaluation["proposal_id"]),
            relevance_score=evaluation["relevance_score"],
            relevance_reasoning=evaluation["relevance_reasoning"],
            feasibility_score=evaluation["feasibility_score"],
            feasibility_reasoning=evaluation["feasibility_reasoning"],
            sector_alignment_score=evaluation["sector_alignment_score"],
            sector_reasoning=evaluation["sector_reasoning"],
            compliance_score=evaluation["compliance_score"],
            compliance_reasoning=evaluation["compliance_reasoning"],
            composite_score=evaluation["composite_score"],
            evaluated_at=evaluation["evaluated_at"],
            evaluator_agent_versions=evaluation.get("evaluator_agent_versions"),
            hallucination_check_passed=evaluation["hallucination_check_passed"],
            prompt_injection_detected=evaluation["prompt_injection_detected"],
            summary_en=evaluation["summary_en"],
            summary_ar=evaluation["summary_ar"],
            ai_interactions=[
                {
                    "model_name": ai["model_name"],
                    "prompt_tokens": ai["prompt_tokens"],
                    "completion_tokens": ai["completion_tokens"],
                    "latency_ms": ai["latency_ms"],
                    "cost_usd": ai["cost_usd"],
                    "operation_type": ai["operation_type"],
                }
                for ai in evaluation.get("ai_interactions", [])
            ],
        )
        
        logger.info(
            f"Successfully retrieved evaluation {evaluation['id']} for proposal {proposal_id}"
        )
        
        return evaluation_detail
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid UUID format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid request",
                "detail": f"Invalid UUID format: {str(e)}",
                "code": "INVALID_UUID",
            },
        )
    except Exception as e:
        logger.error(
            f"Error retrieving evaluation for proposal {proposal_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred while retrieving evaluation data",
                "code": "INTERNAL_ERROR",
            },
        )

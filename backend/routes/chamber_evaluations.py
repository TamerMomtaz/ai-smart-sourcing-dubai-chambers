from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from auth import get_current_user
from models.auth import UserInfo
from models.evaluation import EvaluationResponse, EvaluationDetail
from models.common import PaginationResponse, ErrorResponse
from services import evaluation_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chamber-evaluations", tags=["Chamber Evaluations"])


@router.get(
    "/proposal/{proposal_id}",
    response_model=EvaluationDetail,
    summary="Get evaluation for proposal",
    description="Retrieve detailed evaluation results for a specific proposal. Requires analyst+ permissions."
)
async def get_evaluation_by_proposal(
    proposal_id: UUID,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get detailed evaluation for a proposal.
    
    Permissions:
    - analyst: Can view all evaluations
    - business_group_lead: Can view evaluations in their sector
    - compliance_officer: Can view all evaluations
    - executive: Can view all evaluations
    - vendor: Can view evaluations for their own proposals
    """
    try:
        evaluation = evaluation_service.get_by_proposal_id(
            user_id=current_user.id,
            proposal_id=proposal_id
        )
        
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Evaluation not found",
                    "detail": f"No evaluation found for proposal {proposal_id} or access denied",
                    "code": 404
                }
            )
        
        return evaluation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching evaluation for proposal {proposal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "Failed to retrieve evaluation",
                "code": 500
            }
        )


@router.get(
    "/{evaluation_id}",
    response_model=EvaluationDetail,
    summary="Get evaluation by ID",
    description="Retrieve evaluation details by evaluation ID. Requires analyst+ permissions."
)
async def get_evaluation_by_id(
    evaluation_id: UUID,
    current_user: UserInfo = Depends(get_current_user)
):
    """
    Get evaluation by ID.
    
    Permissions:
    - analyst: Can view all evaluations
    - business_group_lead: Can view evaluations in their sector
    - compliance_officer: Can view all evaluations
    - executive: Can view all evaluations
    - vendor: Can view evaluations for their own proposals
    """
    try:
        evaluation = evaluation_service.get_by_id(
            user_id=current_user.id,
            evaluation_id=evaluation_id
        )
        
        if not evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Evaluation not found",
                    "detail": f"Evaluation {evaluation_id} not found or access denied",
                    "code": 404
                }
            )
        
        return evaluation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching evaluation {evaluation_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "Failed to retrieve evaluation",
                "code": 500
            }
        )


@router.get(
    "/",
    response_model=dict,
    summary="List evaluations",
    description="List evaluations with pagination and optional filtering. Requires analyst+ permissions."
)
async def list_evaluations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    proposal_id: Optional[UUID] = Query(None, description="Filter by proposal ID"),
    min_composite_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum composite score"),
    max_composite_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum composite score"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    List evaluations with pagination and filtering.
    
    Permissions:
    - analyst: Can view all evaluations
    - business_group_lead: Can view evaluations in their sector
    - compliance_officer: Can view all evaluations
    - executive: Can view all evaluations
    - vendor: Can view evaluations for their own proposals
    """
    try:
        result = evaluation_service.list_evaluations(
            user_id=current_user.id,
            user_role=current_user.role,
            page=page,
            page_size=page_size,
            proposal_id=proposal_id,
            min_composite_score=min_composite_score,
            max_composite_score=max_composite_score,
            sector=sector
        )
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Database error",
                    "detail": "Failed to retrieve evaluations",
                    "code": 500
                }
            )
        
        return {
            "evaluations": result["evaluations"],
            "pagination": result["pagination"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing evaluations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "Failed to list evaluations",
                "code": 500
            }
        )

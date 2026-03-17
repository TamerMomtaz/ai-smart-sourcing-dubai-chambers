from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from datetime import datetime, timezone
import logging

from auth import get_current_user
from models.business_group import (
    BusinessGroup,
    BusinessGroupDetail,
    EvaluationWeightConfigUpdate,
    EvaluationWeightConfigUpdateResponse,
)
from models.common import ErrorResponse
from services import business_group_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/business-groups", tags=["business-groups"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_business_groups(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    List all business groups with sector information.
    
    **Authentication Required**: Yes
    
    **Permissions**: All authenticated users can list business groups.
    
    **Returns**:
    - List of business groups with lead information and sector KPIs
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "User ID not found in token", "code": "AUTH_001"},
            )

        result = business_group_service.list_business_groups()

        if result is None:
            return {"business_groups": []}

        return {"business_groups": result.get("data", [])}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing business groups: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": "SRV_001"},
        )


@router.get(
    "/{group_id}",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Business group not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_business_group_detail(
    group_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> BusinessGroupDetail:
    """
    Get business group details and evaluation configuration.
    
    **Authentication Required**: Yes
    
    **Permissions**: All authenticated users can view business group details.
    
    **Path Parameters**:
    - `group_id`: Business group UUID
    
    **Returns**:
    - Detailed business group information including evaluation weights, proposal count, and average score
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "User ID not found in token", "code": "AUTH_001"},
            )

        group_detail = business_group_service.get_business_group_detail(group_id=group_id)
        
        if group_detail is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Business group not found", "code": "RES_001"},
            )

        return BusinessGroupDetail(**group_detail)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving business group {group_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": "SRV_001"},
        )


@router.patch(
    "/{group_id}/evaluation-config",
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - only business group lead can update config"},
        404: {"model": ErrorResponse, "description": "Business group not found"},
        422: {"model": ErrorResponse, "description": "Weights must sum to 1.0"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_evaluation_config(
    group_id: UUID,
    config_update: EvaluationWeightConfigUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> EvaluationWeightConfigUpdateResponse:
    """
    Update evaluation weight configuration for business group.
    
    **Authentication Required**: Yes
    
    **Permissions**: Only the business group lead can update evaluation configuration.
    
    **Path Parameters**:
    - `group_id`: Business group UUID
    
    **Request Body**:
    - `evaluation_weight_config`: Updated weight configuration (weights must sum to 1.0)
    
    **Returns**:
    - Updated evaluation weight configuration with timestamp
    
    **Validation**:
    - All weights must be between 0 and 1
    - Sum of all weights must equal 1.0
    - Only business group lead can perform this operation
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")
        
        if not user_id or not user_role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "User credentials not found in token", "code": "AUTH_001"},
            )

        # Validate weights sum to 1.0
        weights = config_update.evaluation_weight_config
        total_weight = (
            weights.relevance_weight +
            weights.feasibility_weight +
            weights.sector_alignment_weight +
            weights.compliance_weight
        )
        
        if abs(total_weight - 1.0) > 0.001:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Validation Error",
                    "detail": f"Weights must sum to 1.0, current sum is {total_weight}",
                    "code": "VAL_001",
                },
            )

        # Update configuration via service
        result = business_group_service.update_evaluation_config(
            user_id=UUID(user_id),
            group_id=group_id,
            user_role=user_role,
            evaluation_weight_config=weights.model_dump(),
        )
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Business group not found", "code": "RES_001"},
            )
        
        if result.get("error") == "forbidden":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Only the business group lead can update evaluation configuration",
                    "code": "PERM_001",
                },
            )

        return EvaluationWeightConfigUpdateResponse(
            business_group_id=UUID(result["business_group_id"]),
            evaluation_weight_config=result["evaluation_weight_config"],
            updated_at=datetime.now(timezone.utc),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating evaluation config for group {group_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": "SRV_001"},
        )

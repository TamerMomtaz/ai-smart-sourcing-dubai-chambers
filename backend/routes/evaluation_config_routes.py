from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone
import logging

from auth import get_current_user
from models.auth import UserInfo
from models.business_group import (
    EvaluationWeightConfigUpdate,
    EvaluationWeightConfigUpdateResponse,
)
from models.common import ErrorResponse
from services import evaluation_config_service
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/business-groups",
    tags=["evaluation-config"],
)


@router.patch(
    "/{group_id}/evaluation-config",
    response_model=EvaluationWeightConfigUpdateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - only business group lead can update config"},
        404: {"model": ErrorResponse, "description": "Business group not found"},
        422: {"model": ErrorResponse, "description": "Weights must sum to 1.0"},
    },
)
async def update_evaluation_config(
    group_id: UUID,
    payload: EvaluationWeightConfigUpdate,
    current_user: UserInfo = Depends(get_current_user),
) -> EvaluationWeightConfigUpdateResponse:
    """
    Update evaluation weight configuration for business group.
    Only business group lead can update their group's config.
    
    Validates:
    - User is business_group_lead role
    - User is lead of this specific group
    - Weights sum to 1.0
    
    Args:
        group_id: Business group UUID
        payload: Evaluation weight configuration update
        current_user: Authenticated user info
    
    Returns:
        Updated evaluation weight configuration with timestamp
    
    Raises:
        401: Unauthorized
        403: User is not lead of this group or not business_group_lead role
        404: Business group not found
        422: Weights do not sum to 1.0
    """
    try:
        # Validate role
        if current_user.role != "business_group_lead":
            logger.warning(
                f"User {current_user.id} with role {current_user.role} attempted to update evaluation config for group {group_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Only business group leads can update evaluation configuration",
                    "code": "ROLE_NOT_AUTHORIZED",
                },
            )

        # Validate weights sum to 1.0
        weights = payload.evaluation_weight_config
        total_weight = (
            weights.relevance_weight
            + weights.feasibility_weight
            + weights.sector_alignment_weight
            + weights.compliance_weight
        )
        
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(
                f"Invalid weight configuration: weights sum to {total_weight} instead of 1.0 for group {group_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "ValidationError",
                    "detail": f"Evaluation weights must sum to 1.0 (current sum: {total_weight})",
                    "code": "INVALID_WEIGHT_SUM",
                },
            )

        # Verify business group exists and user is the lead
        group_response = (
            supabase.table("business_groups")
            .select("id, name, lead_user_id")
            .eq("id", str(group_id))
            .maybe_single()
            .execute()
        )

        if not group_response.data:
            logger.warning(f"Business group {group_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "NotFound",
                    "detail": f"Business group {group_id} not found",
                    "code": "GROUP_NOT_FOUND",
                },
            )

        group_data = group_response.data
        
        # Verify user is the lead of this group
        if str(group_data.get("lead_user_id")) != str(current_user.id):
            logger.warning(
                f"User {current_user.id} attempted to update config for group {group_id} but is not the lead (lead_user_id: {group_data.get('lead_user_id')})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "You are not the lead of this business group",
                    "code": "NOT_GROUP_LEAD",
                },
            )

        # Build evaluation_weight_config JSON
        config_json = {
            "relevance_weight": weights.relevance_weight,
            "feasibility_weight": weights.feasibility_weight,
            "sector_alignment_weight": weights.sector_alignment_weight,
            "compliance_weight": weights.compliance_weight,
        }

        # Update business group evaluation_weight_config
        update_response = (
            supabase.table("business_groups")
            .update({
                "evaluation_weight_config": config_json,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", str(group_id))
            .execute()
        )

        if not update_response.data:
            logger.error(f"Failed to update evaluation config for group {group_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "InternalServerError",
                    "detail": "Failed to update evaluation configuration",
                    "code": "UPDATE_FAILED",
                },
            )

        updated_group = update_response.data[0]
        updated_at = datetime.fromisoformat(updated_group["updated_at"].replace("Z", "+00:00"))

        logger.info(
            f"User {current_user.id} updated evaluation config for business group {group_id}"
        )

        return EvaluationWeightConfigUpdateResponse(
            business_group_id=UUID(updated_group["id"]),
            evaluation_weight_config=updated_group["evaluation_weight_config"],
            updated_at=updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error updating evaluation config for group {group_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "detail": "Failed to update evaluation configuration",
                "code": "INTERNAL_ERROR",
            },
        )

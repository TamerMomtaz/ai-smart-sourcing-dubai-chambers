from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from models.business_group import (
    BusinessGroup,
    BusinessGroupDetail,
    EvaluationWeightConfig,
    EvaluationWeightConfigUpdate,
    EvaluationWeightConfigUpdateResponse,
)
from models.common import ErrorResponse, PaginationResponse
from auth import get_current_user
import services.business_group_service as business_group_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chamber-business-groups", tags=["Chamber Business Groups"])


@router.get(
    "",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_business_groups(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List all business groups visible to the current user.
    Analysts and executives see all groups.
    Business group leads see their own group.
    Vendors see groups relevant to their proposals.
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")

        if not user_id or not user_role:
            raise HTTPException(
                status_code=401,
                detail={"error": "Unauthorized", "detail": "Invalid user context", "code": 401},
            )

        groups = business_group_service.list_business_groups(user_id=str(user_id))

        if groups is None:
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal Server Error", "detail": "Failed to retrieve business groups", "code": 500},
            )

        # Apply pagination
        total = len(groups)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_groups = groups[start_idx:end_idx]

        return paginated_groups

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing business groups: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": 500},
        )


@router.get(
    "/{group_id}",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Business group not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_business_group(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Get detailed information about a specific business group.
    Includes proposal count, average composite score, and evaluation weight configuration.
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")

        if not user_id or not user_role:
            raise HTTPException(
                status_code=401,
                detail={"error": "Unauthorized", "detail": "Invalid user context", "code": 401},
            )

        group_detail = business_group_service.get_business_group_detail(
            user_id=str(user_id),
            group_id=group_id,
        )

        if group_detail is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "Not Found", "detail": "Business group not found or access denied", "code": 404},
            )

        return group_detail

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving business group {group_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": 500},
        )


@router.put(
    "/{group_id}/evaluation-config",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid evaluation weight configuration"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - business group lead only"},
        404: {"model": ErrorResponse, "description": "Business group not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_evaluation_config(
    group_id: UUID,
    config_update: EvaluationWeightConfigUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update evaluation weight configuration for a business group.
    Only business group leads can update their group's configuration.
    Weights must sum to 1.0.
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")

        if not user_id or not user_role:
            raise HTTPException(
                status_code=401,
                detail={"error": "Unauthorized", "detail": "Invalid user context", "code": 401},
            )

        if user_role not in ["business_group_lead", "executive", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Only business group leads, executives, or admins can update evaluation configuration",
                    "code": 403,
                },
            )

        # Validate weights sum to 1.0
        weights = config_update.evaluation_weight_config
        total_weight = (
            weights.relevance_weight
            + weights.feasibility_weight
            + weights.sector_alignment_weight
            + weights.compliance_weight
        )

        if not (0.99 <= total_weight <= 1.01):  # Allow small floating point tolerance
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Bad Request",
                    "detail": f"Evaluation weights must sum to 1.0, current sum: {total_weight}",
                    "code": 400,
                },
            )

        updated_config = business_group_service.update_evaluation_weight_config(
            user_id=str(user_id),
            group_id=group_id,
            evaluation_weight_config=weights.model_dump(),
        )

        if updated_config is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "Not Found", "detail": "Business group not found or access denied", "code": 404},
            )

        return EvaluationWeightConfigUpdateResponse(
            business_group_id=group_id,
            evaluation_weight_config=updated_config.get("evaluation_weight_config"),
            updated_at=datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating evaluation config for group {group_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": 500},
        )


@router.get(
    "/{group_id}/evaluation-config",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Business group not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_evaluation_config(
    group_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Get current evaluation weight configuration for a business group.
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")

        if not user_id or not user_role:
            raise HTTPException(
                status_code=401,
                detail={"error": "Unauthorized", "detail": "Invalid user context", "code": 401},
            )

        config = business_group_service.get_evaluation_weight_config(
            user_id=str(user_id),
            group_id=group_id,
        )

        if config is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "Not Found", "detail": "Business group or evaluation config not found", "code": 404},
            )

        return config

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving evaluation config for group {group_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": 500},
        )

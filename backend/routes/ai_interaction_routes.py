from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timezone
import logging
import math

from auth import get_current_user
from models.ai_interaction import AIInteractionResponse, RecentInteraction
from models.common import ErrorResponse
from services.ai_interaction_service import get_ai_interaction_summary, list_interactions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-interactions", tags=["ai-interactions"])


@router.get(
    "/summary",
    response_model=AIInteractionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get ΣI transparency dashboard summary aggregates",
)
async def get_ai_interactions_summary(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> AIInteractionResponse:
    """
    Returns aggregate totals for the ΣI Transparency Dashboard:
    total intelligence units, cost, energy, carbon, and model breakdowns.
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role", "")

        allowed_roles = ["analyst", "executive", "compliance_officer", "admin"]
        if user_role not in allowed_roles:
            return AIInteractionResponse(
                total_interactions=0,
                total_tokens=0,
                total_cost_usd=0.0,
                total_energy_kwh=0.0,
                total_carbon_gco2=0.0,
                total_intelligence_units=0.0,
                model_breakdown=[],
                recent_interactions=[],
            )

        summary_data = get_ai_interaction_summary(user_id=user_id, limit=10)

        if summary_data is None:
            logger.error(f"Failed to retrieve AI interaction summary for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "DatabaseError",
                    "detail": "Unable to retrieve AI interaction tracking data",
                    "code": "DB_QUERY_FAILED",
                },
            )

        return AIInteractionResponse(
            total_interactions=summary_data.get("total_interactions", 0),
            total_tokens=summary_data.get("total_tokens", 0),
            total_cost_usd=summary_data.get("total_cost_usd", 0.0),
            total_energy_kwh=summary_data.get("total_energy_kwh", 0.0),
            total_carbon_gco2=summary_data.get("total_carbon_gco2", 0.0),
            total_intelligence_units=summary_data.get("total_intelligence_units", 0.0),
            model_breakdown=summary_data.get("model_breakdown", []),
            recent_interactions=summary_data.get("recent_interactions", []),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in get_ai_interactions_summary for user {current_user.get('id')}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "detail": "An unexpected error occurred while processing your request",
                "code": "INTERNAL_ERROR",
            },
        )


@router.get(
    "",
    response_model=AIInteractionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - analyst or executive role required"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get ΣI (sigma intelligence) tracking data for AI model usage",
)
async def get_ai_interactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Retrieve paginated AI interactions list for the ΣI Transparency Dashboard table.
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role", "")

        allowed_roles = ["analyst", "executive", "compliance_officer", "admin"]
        if user_role not in allowed_roles:
            return {"interactions": [], "pagination": {"page": page, "page_size": page_size, "total": 0, "total_pages": 0}}

        interactions, total = list_interactions(user_id=user_id, page=page, page_size=page_size)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return {
            "interactions": interactions,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in get_ai_interactions for user {current_user.get('id')}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "detail": "An unexpected error occurred while processing your request",
                "code": "INTERNAL_ERROR",
            },
        )

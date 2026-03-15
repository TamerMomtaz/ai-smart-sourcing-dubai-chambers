from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
import logging

from auth import get_current_user
from models.auth import UserInfo
from models.ai_interaction import AIInteractionResponse
from models.common import ErrorResponse
from services.ai_interaction_service import get_ai_interaction_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai-interactions", tags=["ai-interactions"])


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
    current_user: UserInfo = Depends(get_current_user),
) -> AIInteractionResponse:
    """
    Retrieve comprehensive AI model usage tracking data including:
    - Total interactions, tokens, costs, energy consumption, carbon emissions
    - Intelligence units (ΣI metric)
    - Model-specific breakdowns (Claude, GPT-4, Gemini)
    - Recent interaction history
    
    **Access Control:**
    - Analyst: View own session interactions
    - Executive: View aggregated system-wide metrics
    - Compliance Officer: View all interactions for audit
    
    **Rate Limit:** 60 requests/minute
    """
    try:
        # Role-based access control
        allowed_roles = ["analyst", "executive", "compliance_officer"]
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Access denied for user {current_user.id} with role {current_user.role} to AI interactions endpoint"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Analyst, executive, or compliance officer role required to access AI interaction data",
                    "code": "ROLE_NOT_AUTHORIZED",
                },
            )

        # Fetch AI interaction summary from service layer
        summary_data = get_ai_interaction_summary(user_id=current_user.id, limit=10)

        if summary_data is None:
            logger.error(f"Failed to retrieve AI interaction summary for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "DatabaseError",
                    "detail": "Unable to retrieve AI interaction tracking data",
                    "code": "DB_QUERY_FAILED",
                },
            )

        # Transform service response to Pydantic model
        response = AIInteractionResponse(
            total_interactions=summary_data.get("total_interactions", 0),
            total_tokens=summary_data.get("total_tokens", 0),
            total_cost_usd=summary_data.get("total_cost_usd", 0.0),
            total_energy_kwh=summary_data.get("total_energy_kwh", 0.0),
            total_carbon_gco2=summary_data.get("total_carbon_gco2", 0.0),
            total_intelligence_units=summary_data.get("total_intelligence_units", 0.0),
            model_breakdown=summary_data.get("model_breakdown", []),
            recent_interactions=summary_data.get("recent_interactions", []),
        )

        logger.info(
            f"User {current_user.id} ({current_user.role}) retrieved AI interaction summary: "
            f"{response.total_interactions} interactions, {response.total_tokens} tokens, "
            f"${response.total_cost_usd:.4f} cost"
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in get_ai_interactions for user {current_user.id}: {str(e)}",
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

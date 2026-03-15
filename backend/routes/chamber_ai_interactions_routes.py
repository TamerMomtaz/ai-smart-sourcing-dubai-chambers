from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from auth import get_current_user
from models.auth import UserInfo
from models.ai_interaction import AIInteractionResponse, AIInteractionSummary, ModelBreakdown, RecentInteraction
from models.common import ErrorResponse
from services.ai_interaction_service import get_ai_interaction_summary
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/chamber-ai-interactions",
    tags=["chamber_ai_interactions"]
)


@router.get(
    "/summary",
    response_model=AIInteractionResponse,
    responses={
        200: {"description": "AI interaction summary retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get AI Interaction Summary",
    description="""Retrieve Sigma Intelligence (ΣI) tracking data for AI model usage.
    
    Aggregates:
    - Total interactions
    - Total tokens (prompt + completion)
    - Total cost in USD
    - Energy consumption (kWh)
    - Carbon emissions (gCO2)
    - Intelligence units
    
    Returns model-level breakdown and recent interactions.
    
    **Permissions:**
    - Analyst: Own session interactions
    - Business Group Lead: Sector-level interactions
    - Compliance Officer: All compliance-related interactions
    - Executive: Aggregated system-wide metrics
    - Admin: All interactions
    """
)
async def get_interaction_summary(
    limit: int = Query(10, ge=1, le=100, description="Number of recent interactions to return"),
    current_user: UserInfo = Depends(get_current_user)
) -> AIInteractionResponse:
    try:
        summary_data = get_ai_interaction_summary(user_id=current_user.id, limit=limit)
        
        if summary_data is None:
            raise HTTPException(
                status_code=500,
                detail={"error": "Service Error", "detail": "Failed to retrieve AI interaction summary", "code": 500}
            )
        
        return AIInteractionResponse(
            total_interactions=summary_data.get("total_interactions", 0),
            total_tokens=summary_data.get("total_tokens", 0),
            total_cost_usd=summary_data.get("total_cost_usd", 0.0),
            total_energy_kwh=summary_data.get("total_energy_kwh", 0.0),
            total_carbon_gco2=summary_data.get("total_carbon_gco2", 0.0),
            total_intelligence_units=summary_data.get("total_intelligence_units", 0.0),
            model_breakdown=[ModelBreakdown(**m) for m in summary_data.get("model_breakdown", [])],
            recent_interactions=[RecentInteraction(**i) for i in summary_data.get("recent_interactions", [])]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving AI interaction summary for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "Failed to retrieve AI interaction summary", "code": 500}
        )


@router.get(
    "/model/{model_name}",
    response_model=ModelBreakdown,
    responses={
        200: {"description": "Model breakdown retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Model not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get Model-Specific Breakdown",
    description="""Retrieve usage metrics for a specific AI model.
    
    Returns:
    - Interaction count
    - Total tokens consumed
    - Total cost in USD
    - Average latency in milliseconds
    
    **Permissions:**
    - Analyst: Own session model usage
    - Executive: System-wide model metrics
    - Compliance Officer: All model usage for compliance tracking
    - Admin: All model usage
    """
)
async def get_model_breakdown(
    model_name: str,
    current_user: UserInfo = Depends(get_current_user)
) -> ModelBreakdown:
    try:
        summary_data = get_ai_interaction_summary(user_id=current_user.id, limit=0)
        
        if summary_data is None:
            raise HTTPException(
                status_code=500,
                detail={"error": "Service Error", "detail": "Failed to retrieve model breakdown", "code": 500}
            )
        
        model_breakdown = summary_data.get("model_breakdown", [])
        model_data = next((m for m in model_breakdown if m["model_name"] == model_name), None)
        
        if model_data is None:
            raise HTTPException(
                status_code=404,
                detail={"error": "Not Found", "detail": f"Model '{model_name}' not found in interaction history", "code": 404}
            )
        
        return ModelBreakdown(**model_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving model breakdown for {model_name}, user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "Failed to retrieve model breakdown", "code": 500}
        )


@router.get(
    "/recent",
    response_model=list[RecentInteraction],
    responses={
        200: {"description": "Recent interactions retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Get Recent AI Interactions",
    description="""Retrieve recent AI model interactions with detailed metrics.
    
    Returns list of interactions with:
    - Timestamp
    - Model name
    - Operation type
    - Token counts (prompt + completion)
    - Latency in milliseconds
    - Cost in USD
    
    **Permissions:**
    - Analyst: Own recent interactions
    - Executive: System-wide recent interactions
    - Compliance Officer: Recent interactions for audit purposes
    - Admin: All recent interactions
    """
)
async def get_recent_interactions(
    limit: int = Query(20, ge=1, le=100, description="Number of recent interactions to return"),
    current_user: UserInfo = Depends(get_current_user)
) -> list[RecentInteraction]:
    try:
        summary_data = get_ai_interaction_summary(user_id=current_user.id, limit=limit)
        
        if summary_data is None:
            raise HTTPException(
                status_code=500,
                detail={"error": "Service Error", "detail": "Failed to retrieve recent interactions", "code": 500}
            )
        
        recent_interactions = summary_data.get("recent_interactions", [])
        return [RecentInteraction(**i) for i in recent_interactions]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving recent interactions for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "Failed to retrieve recent interactions", "code": 500}
        )

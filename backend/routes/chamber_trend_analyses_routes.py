from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID
from datetime import date

from models.trend_analysis import (
    TrendAnalysis,
    TrendAnalysisGenerateRequest,
    TrendAnalysisGenerateResponse,
)
from models.common import PaginationResponse, ErrorResponse
from auth import get_current_user
from services import trend_analysis_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trend-analyses", tags=["Trend Analyses"])


@router.get(
    "",
    response_model=dict,
    summary="List trend analyses",
    description="Retrieve paginated list of AI-generated trend analyses. Executives can filter by sector and date range.",
)
async def list_trend_analyses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    current_user: dict = Depends(get_current_user),
):
    """
    List trend analyses with pagination.
    
    Requires: executive role
    
    Returns:
    - List of trend analyses
    - Pagination metadata
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user["role"]
        
        if user_role not in ["executive", "analyst", "business_group_lead", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Only executives, analysts, and business group leads can access trend analyses",
                    "code": 403,
                },
            )
        
        result = trend_analysis_service.list_trend_analyses(
            user_id=user_id,
            page=page,
            page_size=page_size,
            sector=sector,
        )
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal Server Error",
                    "detail": "Failed to retrieve trend analyses",
                    "code": 500,
                },
            )
        
        return {
            "trend_analyses": result.get("trend_analyses", []),
            "pagination": result.get("pagination", {}),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing trend analyses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while retrieving trend analyses",
                "code": 500,
            },
        )


@router.get(
    "/{analysis_id}",
    response_model=TrendAnalysis,
    summary="Get trend analysis by ID",
    description="Retrieve detailed trend analysis by UUID. Executives only.",
)
async def get_trend_analysis(
    analysis_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Get trend analysis detail.
    
    Requires: executive role
    
    Args:
    - analysis_id: Trend analysis UUID
    
    Returns:
    - Trend analysis detail including technology trends, submission volume, average scores
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user["role"]
        
        if user_role not in ["executive", "analyst", "business_group_lead", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Only executives, analysts, and business group leads can access trend analysis details",
                    "code": 403,
                },
            )
        
        result = trend_analysis_service.get_by_id(
            user_id=user_id,
            analysis_id=analysis_id,
        )
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not Found",
                    "detail": f"Trend analysis {analysis_id} not found",
                    "code": 404,
                },
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving trend analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while retrieving trend analysis",
                "code": 500,
            },
        )


@router.post(
    "/generate",
    response_model=TrendAnalysisGenerateResponse,
    status_code=202,
    summary="Trigger trend analysis generation",
    description="Trigger AI-powered trend analysis generation for specified sector and date range. Executives only.",
)
async def generate_trend_analysis(
    request: TrendAnalysisGenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger AI trend analysis generation.
    
    Requires: executive role
    
    Args:
    - sector: Optional sector to analyze (None for all sectors)
    - date_range_start: Analysis start date
    - date_range_end: Analysis end date
    
    Returns:
    - job_id: Background job UUID
    - status: Job status (processing)
    - estimated_completion: Estimated completion time
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user["role"]
        
        if user_role not in ["executive", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Only executives can trigger trend analysis generation",
                    "code": 403,
                },
            )
        
        result = trend_analysis_service.trigger_generation(
            user_id=user_id,
            sector=request.sector,
            date_range_start=request.date_range_start,
            date_range_end=request.date_range_end,
        )
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal Server Error",
                    "detail": "Failed to trigger trend analysis generation",
                    "code": 500,
                },
            )
        
        return result
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(f"Invalid trend analysis generation request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Bad Request",
                "detail": str(e),
                "code": 400,
            },
        )
    except Exception as e:
        logger.error(f"Error triggering trend analysis generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while triggering trend analysis",
                "code": 500,
            },
        )


@router.delete(
    "/{analysis_id}",
    status_code=204,
    summary="Delete trend analysis",
    description="Delete a trend analysis record. Executives and admins only.",
)
async def delete_trend_analysis(
    analysis_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete trend analysis.
    
    Requires: executive or admin role
    
    Args:
    - analysis_id: Trend analysis UUID to delete
    
    Returns:
    - 204 No Content on success
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user["role"]
        
        if user_role not in ["executive", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Only executives and admins can delete trend analyses",
                    "code": 403,
                },
            )
        
        success = trend_analysis_service.delete(
            user_id=user_id,
            analysis_id=analysis_id,
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not Found",
                    "detail": f"Trend analysis {analysis_id} not found",
                    "code": 404,
                },
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trend analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while deleting trend analysis",
                "code": 500,
            },
        )

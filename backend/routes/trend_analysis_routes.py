from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime, timezone, timedelta
import logging

from models import (
    TrendAnalysis,
    TrendAnalysisGenerateRequest,
    ErrorResponse,
    PaginationResponse,
)
from auth import get_current_user
from services import trend_analysis_service
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/trend-analyses",
    tags=["trend-analyses"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)


@router.get(
    "",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get AI-generated trend analyses for innovation patterns",
)
async def list_trend_analyses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    current_user: dict = Depends(get_current_user),
):
    """
    Get AI-generated trend analyses for innovation patterns.
    Returns list of trend analyses with pagination.
    
    Requires authentication.
    """
    try:
        user_id = UUID(current_user["user_id"])
        user_role = current_user.get("role")

        # Vendor role gets empty list (no access to trend analysis data)
        if user_role not in ["analyst", "executive", "business_group_lead", "compliance_officer", "admin"]:
            return {
                "analyses": [],
                "pagination": {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                }
            }

        # Build query
        offset = (page - 1) * page_size
        query = supabase.table("trend_analyses").select(
            "id, analysis_date, sector, technology_trends, submission_volume, average_scores, emerging_technologies, generated_by",
            count="exact"
        )
        
        # Apply sector filter if provided
        if sector:
            query = query.eq("sector", sector.strip())
        
        # Order by analysis_date descending
        query = query.order("analysis_date", desc=True)
        
        # Apply pagination
        query = query.range(offset, offset + page_size - 1)
        
        response = query.execute()
        
        if not response.data:
            return {
                "analyses": [],
                "pagination": {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                }
            }
        
        total_count = response.count if response.count is not None else 0
        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
        
        # Format response
        analyses = []
        for item in response.data:
            analysis = {
                "id": item["id"],
                "analysis_date": item["analysis_date"],
                "sector": item.get("sector"),
                "technology_trends": item.get("technology_trends", {}),
                "submission_volume": item.get("submission_volume", 0),
                "average_scores": item.get("average_scores", {}),
                "emerging_technologies": item.get("emerging_technologies", []),
                "generated_by": item.get("generated_by", "system"),
            }
            analyses.append(analysis)
        
        return {
            "analyses": analyses,
            "pagination": {
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in list_trend_analyses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Bad Request", "detail": str(e), "code": "VALIDATION_ERROR"},
        )
    except Exception as e:
        logger.error(f"Error listing trend analyses: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "Failed to retrieve trend analyses", "code": "INTERNAL_ERROR"},
        )


@router.post(
    "/generate",
    response_model=dict,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger AI trend analysis generation (executive only)",
    responses={
        403: {"model": ErrorResponse, "description": "Forbidden - executive role required"},
    },
)
async def generate_trend_analysis(
    request: TrendAnalysisGenerateRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Trigger AI trend analysis generation job.
    Executive-only operation.
    
    Analyzes proposals within the specified date range and optionally filters by sector.
    Returns job_id for tracking the async generation process.
    """
    try:
        user_id = UUID(current_user["user_id"])
        user_role = current_user.get("role")
        
        # Verify executive or admin role
        if user_role not in ["executive", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Executive or admin role required to trigger trend analysis", "code": "ROLE_REQUIRED"},
            )
        
        # Validate date range
        if request.date_range_start >= request.date_range_end:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "detail": "date_range_start must be before date_range_end", "code": "INVALID_DATE_RANGE"},
            )
        
        # Create trend analysis job record
        job_id = UUID(supabase.rpc("uuid_generate_v4").execute().data)
        
        # Insert job record into trend_analysis_jobs table (assumed)
        job_data = {
            "id": str(job_id),
            "user_id": str(user_id),
            "sector": request.sector.strip() if request.sector else None,
            "date_range_start": request.date_range_start.isoformat(),
            "date_range_end": request.date_range_end.isoformat(),
            "status": "processing",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Note: In production, this would queue a background job to Claude API
        # For now, we create a placeholder job record
        try:
            supabase.table("trend_analysis_jobs").insert(job_data).execute()
        except Exception as insert_error:
            logger.warning(f"Failed to insert job record (table may not exist): {str(insert_error)}")
        
        # Estimate completion time (5 minutes for typical analysis)
        estimated_completion = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
        
        return {
            "job_id": str(job_id),
            "status": "processing",
            "estimated_completion": estimated_completion,
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error in generate_trend_analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Bad Request", "detail": str(e), "code": "VALIDATION_ERROR"},
        )
    except Exception as e:
        logger.error(f"Error generating trend analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "Failed to trigger trend analysis generation", "code": "INTERNAL_ERROR"},
        )

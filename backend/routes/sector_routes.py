from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging

from auth import get_current_user
from models.dashboard import SectorDashboard
from models.common import ErrorResponse
from services.sector_service import get_sector_dashboard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard/sector", tags=["sector"])


@router.get(
    "/{sector}",
    response_model=SectorDashboard,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Sector not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get sector-specific dashboard metrics",
    description="Retrieve comprehensive dashboard metrics for a specific industry sector including proposal counts, average scores, technology distribution, maturity distribution, and top proposals.",
)
async def get_sector_dashboard_metrics(
    sector: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> SectorDashboard:
    """
    Get sector-specific dashboard metrics.
    
    Requires authentication and analyst+ permissions.
    Returns aggregated metrics including:
    - Total proposals in sector
    - Average evaluation scores (relevance, feasibility, sector_alignment, compliance, composite)
    - Technology type distribution
    - Maturity level distribution
    - Top-scoring proposals in sector
    
    Args:
        sector: Industry sector name (fintech, healthcare, logistics, energy, education, government, tourism, other)
        current_user: Authenticated user from JWT token
    
    Returns:
        SectorDashboard: Sector-specific metrics and analytics
    
    Raises:
        HTTPException: 401 if unauthorized, 403 if insufficient permissions, 404 if sector not found
    """
    try:
        user_id = current_user.get("user_id")
        user_role = current_user.get("role")
        
        if not user_id:
            logger.error("Missing user_id in current_user token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ErrorResponse(
                    error="Unauthorized",
                    detail="User ID not found in authentication token",
                    code="AUTH_USER_ID_MISSING"
                ).dict(),
            )
        
        # Verify user has analyst+ permissions
        allowed_roles = ["analyst", "business_group_lead", "compliance_officer", "executive", "admin"]
        if user_role not in allowed_roles:
            logger.warning(f"User {user_id} with role {user_role} attempted to access sector dashboard")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    error="Forbidden",
                    detail="Insufficient permissions to access sector dashboard",
                    code="PERMISSION_DENIED"
                ).dict(),
            )
        
        # Validate sector parameter
        valid_sectors = [
            "fintech",
            "healthcare",
            "logistics",
            "energy",
            "education",
            "government",
            "tourism",
            "other",
        ]
        if sector.lower() not in valid_sectors:
            logger.warning(f"Invalid sector requested: {sector}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse(
                    error="Invalid Sector",
                    detail=f"Sector must be one of: {', '.join(valid_sectors)}",
                    code="INVALID_SECTOR"
                ).dict(),
            )
        
        # Fetch sector dashboard data
        dashboard_data = get_sector_dashboard(user_id=user_id, sector=sector.lower())
        
        if dashboard_data is None:
            logger.warning(f"No data found for sector: {sector}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error="Sector Not Found",
                    detail=f"No proposals found for sector '{sector}' or insufficient permissions",
                    code="SECTOR_NOT_FOUND"
                ).dict(),
            )
        
        logger.info(f"User {user_id} retrieved sector dashboard for {sector}")
        return SectorDashboard(**dashboard_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving sector dashboard for {sector}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="Internal Server Error",
                detail="An unexpected error occurred while retrieving sector dashboard",
                code="SECTOR_DASHBOARD_ERROR"
            ).dict(),
        )

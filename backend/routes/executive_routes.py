from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging

from models import ExecutiveDashboard, ErrorResponse
from services import executive_service
from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dashboard",
    tags=["executive"],
)


@router.get(
    "/executive",
    response_model=ExecutiveDashboard,
    status_code=status.HTTP_200_OK,
    summary="Get executive dashboard aggregated metrics",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - executive role required"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_executive_dashboard(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get executive dashboard with aggregated metrics including:
    - Pipeline status (proposals by status)
    - Sector trends (proposal counts, average scores, trend direction)
    - D33 alignment metrics
    - Vendor onboarding funnel
    - Compliance summary
    
    Requires: executive role
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")
        
        if not user_id or not user_role:
            logger.error("Missing user_id or user_role in token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid token payload", "code": 401},
            )
        
        # Enforce executive role requirement
        if user_role != "executive":
            logger.warning(f"User {user_id} with role {user_role} attempted to access executive dashboard")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Executive role required", "code": 403},
            )
        
        # Fetch dashboard data from service
        dashboard_data = executive_service.get_executive_dashboard(user_id)
        
        if not dashboard_data:
            logger.error(f"Failed to retrieve executive dashboard for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "InternalServerError", "detail": "Failed to retrieve dashboard data", "code": 500},
            )
        
        return dashboard_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in get_executive_dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": "An unexpected error occurred", "code": 500},
        )

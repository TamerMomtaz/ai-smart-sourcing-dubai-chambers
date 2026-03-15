from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
from auth import get_current_user
from models.dashboard import AnalystDashboard
from models.common import ErrorResponse
from services.analyst_service import get_analyst_dashboard
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["analyst"])


@router.get(
    "/analyst",
    response_model=AnalystDashboard,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - analyst role required"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get analyst dashboard with proposal queue and assignments",
)
async def get_analyst_dashboard_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get analyst dashboard with pending reviews, recent evaluations, and daily stats.
    
    Requires:
    - analyst role
    
    Returns:
    - pending_reviews: Proposals requiring manual review or evaluation
    - recent_evaluations: Recently completed evaluations
    - daily_stats: Today's review statistics
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")
        
        if not user_id:
            logger.error("User ID missing from token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "User ID not found in token", "code": "AUTH_001"},
            )
        
        if user_role != "analyst":
            logger.warning(f"Access denied: User {user_id} with role {user_role} attempted to access analyst dashboard")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Analyst role required to access this dashboard", "code": "AUTHZ_001"},
            )
        
        dashboard_data = get_analyst_dashboard(str(user_id))
        
        if dashboard_data is None:
            logger.error(f"Failed to retrieve analyst dashboard for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Internal Server Error", "detail": "Failed to retrieve dashboard data", "code": "DASH_001"},
            )
        
        return AnalystDashboard(**dashboard_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error retrieving analyst dashboard: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": "DASH_002"},
        )

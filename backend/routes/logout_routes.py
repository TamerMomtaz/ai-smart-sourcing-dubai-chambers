from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from auth import get_current_user
from models.auth import LogoutResponse
from models.common import ErrorResponse
from services.logout_service import invalidate_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Invalidate user session and tokens",
    description="Logs out the current user by invalidating their session and tokens. Requires valid authentication.",
)
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> LogoutResponse:
    """
    Logout endpoint - invalidates user session and tokens.
    
    - **Authentication Required**: Yes
    - **Rate Limit**: 20 requests per window
    - **Roles Allowed**: All authenticated users
    
    Returns:
        LogoutResponse: Confirmation message
    
    Raises:
        401: If user is not authenticated
        500: If session invalidation fails
    """
    try:
        user_id = current_user.get("user_id")
        access_token = current_user.get("access_token", "")
        
        if not user_id:
            logger.error("Logout failed: user_id missing from current_user")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Unauthorized",
                    "detail": "User ID not found in authentication context",
                    "code": 401
                }
            )
        
        # Invalidate session in Supabase
        success = await invalidate_session(user_id, access_token)
        
        if not success:
            logger.warning(f"Session invalidation returned False for user_id={user_id}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "LogoutFailed",
                    "detail": "Failed to invalidate session",
                    "code": 500
                }
            )
        
        logger.info(f"User {user_id} logged out successfully")
        return LogoutResponse(message="Logged out successfully")
    
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "detail": "An error occurred during logout",
                "code": 500
            }
        )

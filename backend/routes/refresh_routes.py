from fastapi import APIRouter, HTTPException, status
from models.auth import RefreshTokenRequest, TokenResponse
from models.common import ErrorResponse
import logging
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid or expired refresh token"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Refresh expired access token using refresh token",
)
async def refresh_access_token(request: RefreshTokenRequest):
    """
    Refresh expired access token using Supabase Auth refresh.

    Validates the refresh token via Supabase and issues new tokens.
    Rate limit: 20 requests per minute.
    """
    try:
        refresh_token = request.refresh_token.strip()

        # Refresh session via Supabase Auth
        try:
            response = supabase.auth.refresh_session(refresh_token)
        except Exception as e:
            logger.warning(f"Supabase refresh_session failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid or expired refresh token", "code": 401}
            )

        if not response or not response.session:
            logger.warning("Refresh token invalid: no session returned")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid or expired refresh token", "code": 401}
            )

        session = response.session
        user = response.user

        if not user:
            logger.warning("Refresh succeeded but no user returned")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "User not found", "code": 401}
            )

        # Fetch user profile from chamber_users
        user_data = None
        try:
            user_response = supabase.table("chamber_users").select(
                "id, email, role, full_name, chamber"
            ).eq("id", str(user.id)).maybe_single().execute()
            if user_response and user_response.data:
                user_data = user_response.data
        except Exception as e:
            logger.warning(f"Failed to fetch chamber_users profile during refresh: {e}")

        # Fall back to Supabase auth user info if chamber_users lookup fails
        if not user_data:
            user_data = {
                "id": str(user.id),
                "email": user.email,
                "role": "vendor",
                "full_name": "",
                "chamber": "",
            }

        # Update last_login timestamp
        try:
            from datetime import datetime, timezone
            supabase.table("chamber_users").update({
                "last_login": datetime.now(timezone.utc).isoformat()
            }).eq("id", str(user.id)).execute()
        except Exception as e:
            logger.warning(f"Failed to update last_login for user {user.id}: {e}")

        logger.info(f"Successfully refreshed tokens for user {user.id}")

        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            user={
                "id": user_data["id"],
                "email": user_data["email"],
                "role": user_data.get("role", "vendor"),
                "full_name": user_data.get("full_name", ""),
                "chamber": user_data.get("chamber", ""),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": "Failed to refresh token", "code": 500}
        )

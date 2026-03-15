from fastapi import APIRouter, HTTPException, status
from models.auth import RefreshTokenRequest, TokenResponse
from models.common import ErrorResponse
import logging
import os
import jwt
from datetime import datetime, timezone, timedelta
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip()
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15").strip())
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7").strip())

if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable must be set")


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
    Refresh expired access token using refresh token.
    
    Validates the refresh token and issues new access + refresh tokens.
    Rate limit: 20 requests per minute.
    
    Args:
        request: RefreshTokenRequest containing refresh_token
        
    Returns:
        TokenResponse with new access_token, refresh_token, and user info
        
    Raises:
        HTTPException 401: Invalid or expired refresh token
        HTTPException 500: Internal server error
    """
    try:
        refresh_token = request.refresh_token.strip()
        
        # Decode and validate refresh token
        try:
            payload = jwt.decode(
                refresh_token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Refresh token has expired", "code": 401}
            )
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid refresh token", "code": 401}
            )
        
        # Validate token type
        if payload.get("type") != "refresh":
            logger.warning("Token is not a refresh token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid token type", "code": 401}
            )
        
        user_id = payload.get("sub")
        if not user_id:
            logger.error("No user_id in refresh token payload")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid token payload", "code": 401}
            )
        
        # Fetch user from database to validate existence and get current data
        user_response = supabase.table("chamber_users").select(
            "id, email, role, full_name, chamber"
        ).eq("id", user_id).maybeSingle().execute()
        
        if not user_response.data:
            logger.warning(f"User {user_id} not found during refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "User not found", "code": 401}
            )
        
        user_data = user_response.data
        
        # Update last_login timestamp
        try:
            supabase.table("chamber_users").update({
                "last_login": datetime.now(timezone.utc).isoformat()
            }).eq("id", user_id).execute()
        except Exception as e:
            logger.warning(f"Failed to update last_login for user {user_id}: {str(e)}")
        
        # Generate new access token
        access_token_payload = {
            "sub": str(user_data["id"]),
            "email": user_data["email"],
            "role": user_data["role"],
            "type": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
            "iat": datetime.now(timezone.utc)
        }
        
        new_access_token = jwt.encode(
            access_token_payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        
        # Generate new refresh token
        refresh_token_payload = {
            "sub": str(user_data["id"]),
            "type": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.now(timezone.utc)
        }
        
        new_refresh_token = jwt.encode(
            refresh_token_payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )
        
        logger.info(f"Successfully refreshed tokens for user {user_id}")
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user={
                "id": user_data["id"],
                "email": user_data["email"],
                "role": user_data["role"],
                "full_name": user_data["full_name"],
                "chamber": user_data["chamber"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalServerError", "detail": "Failed to refresh token", "code": 500}
        )

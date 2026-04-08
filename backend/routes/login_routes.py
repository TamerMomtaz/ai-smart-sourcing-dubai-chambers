from fastapi import APIRouter, HTTPException, status, Request
from models.auth import LoginRequest, TokenResponse
from models.common import ErrorResponse
from services.login_service import authenticate_user
from services.chamber_alerts_service import create_alert
from typing import Dict, Any
import logging
import time
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# In-memory rate limiting store (for production, use Redis)
rate_limit_store: Dict[str, Dict[str, Any]] = {}
RATE_LIMIT_WINDOW = 300  # 5 minutes
MAX_ATTEMPTS = 10


def check_rate_limit(ip_address: str) -> bool:
    """
    Check if IP has exceeded rate limit.
    Returns True if request is allowed, False if rate limited.
    """
    now = time.time()
    
    if ip_address not in rate_limit_store:
        rate_limit_store[ip_address] = {
            "attempts": 1,
            "window_start": now
        }
        return True
    
    record = rate_limit_store[ip_address]
    window_elapsed = now - record["window_start"]
    
    if window_elapsed > RATE_LIMIT_WINDOW:
        rate_limit_store[ip_address] = {
            "attempts": 1,
            "window_start": now
        }
        return True
    
    if record["attempts"] >= MAX_ATTEMPTS:
        return False
    
    rate_limit_store[ip_address]["attempts"] += 1
    return True


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        429: {"model": ErrorResponse, "description": "Too many login attempts"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Authenticate user with email/password and return JWT token",
)
async def login(
    login_request: LoginRequest,
    request: Request
):
    """
    Authenticate user with email and password.
    
    Returns JWT access token, refresh token, and user information.
    
    **Rate Limit:** 10 attempts per 5 minutes per IP address.
    
    **Returns:**
    - access_token: JWT access token (valid for 60 minutes)
    - refresh_token: JWT refresh token (valid for 7 days)
    - user: User profile information including role and chamber
    
    **Error Codes:**
    - 401: Invalid email or password
    - 429: Too many login attempts - rate limit exceeded
    - 500: Internal authentication error
    """
    try:
        client_ip = request.client.host if request.client else "unknown"
        
        if not check_rate_limit(client_ip):
            logger.warning(
                f"Rate limit exceeded for IP {client_ip}",
                extra={"ip": client_ip, "endpoint": "/api/v1/auth/login"}
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "rate_limit_exceeded",
                    "detail": "Too many login attempts. Please try again in 5 minutes.",
                    "code": 429
                }
            )
        
        logger.info(
            f"Login attempt for email: {login_request.email}",
            extra={"email": login_request.email, "ip": client_ip}
        )
        
        result = authenticate_user(
            email=login_request.email.strip(),
            password=login_request.password
        )
        
        if not result:
            logger.warning(
                f"Failed login attempt for email: {login_request.email}",
                extra={"email": login_request.email, "ip": client_ip}
            )
            # Generate security alert after 3+ failed attempts in window
            ip_record = rate_limit_store.get(client_ip)
            if ip_record and ip_record["attempts"] >= 3:
                create_alert(
                    alert_type="security",
                    severity="high",
                    title="Multiple failed login attempts",
                    description=f"IP {client_ip} has {ip_record['attempts']} failed login attempts in the last 5 minutes. Last email tried: {login_request.email}",
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "authentication_failed",
                    "detail": "Invalid email or password",
                    "code": 401
                }
            )
        
        logger.info(
            f"Successful login for user: {result['user']['id']}",
            extra={
                "user_id": str(result['user']['id']),
                "role": result['user']['role'],
                "chamber": result['user']['chamber']
            }
        )
        
        return TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user=result["user"]
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(
            f"Login error: {str(e)}",
            exc_info=True,
            extra={"email": login_request.email}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "authentication_error",
                "detail": "An error occurred during authentication. Please try again.",
                "code": 500
            }
        )

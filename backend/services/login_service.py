from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import logging
from database import supabase

logger = logging.getLogger(__name__)


def _get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user by email from Supabase."""
    result = supabase.table("chamber_users").select("*").eq("email", email).eq("is_active", True).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


def _update_last_login(user_id) -> None:
    """Update user's last login timestamp."""
    supabase.table("chamber_users").update({
        "last_login": datetime.now(timezone.utc).isoformat()
    }).eq("id", str(user_id)).execute()


def _record_login_attempt(email: str, success: bool, ip_address: Optional[str] = None) -> None:
    """Record login attempt for rate limiting and auditing."""
    supabase.table("login_attempts").insert({
        "email": email,
        "success": success,
        "ip_address": ip_address,
        "attempted_at": datetime.now(timezone.utc).isoformat()
    }).execute()


def _check_rate_limit(email: str, window_minutes: int = 15, max_attempts: int = 10) -> bool:
    """Check if user has exceeded login attempts rate limit."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    result = supabase.table("login_attempts").select("id").eq("email", email).gte(
        "attempted_at", cutoff.isoformat()
    ).execute()

    if result.data and len(result.data) >= max_attempts:
        return False
    return True


def authenticate_user(email: str, password: str, ip_address: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Authenticate user with email and password via Supabase Auth.
    Returns user data with Supabase tokens if successful, None otherwise.
    """
    # Check rate limit
    if not _check_rate_limit(email):
        _record_login_attempt(email, False, ip_address)
        return None

    try:
        # Sign in via Supabase Auth (returns native Supabase tokens)
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })

        user = response.user
        session = response.session

        if not user or not session:
            _record_login_attempt(email, False, ip_address)
            return None

        # Get role and profile from chamber_users table
        role = "vendor"
        full_name = ""
        chamber = ""
        try:
            chamber_user = (
                supabase.table("chamber_users")
                .select("role, full_name, chamber")
                .eq("id", str(user.id))
                .maybe_single()
                .execute()
            )
            if chamber_user and chamber_user.data:
                role = chamber_user.data.get("role", "vendor")
                full_name = chamber_user.data.get("full_name", "")
                chamber = chamber_user.data.get("chamber", "")
        except Exception as e:
            logger.warning(f"Failed to fetch chamber_users profile: {e}")

        # Update last login
        _update_last_login(user.id)

        # Record successful login
        _record_login_attempt(email, True, ip_address)

        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": role,
                "full_name": full_name,
                "chamber": chamber,
            },
        }

    except Exception as e:
        logger.warning(f"Supabase sign_in_with_password failed for {email}: {e}")
        _record_login_attempt(email, False, ip_address)
        return None


def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """
    Refresh session using Supabase Auth.
    Returns new access and refresh tokens if valid, None otherwise.
    """
    try:
        response = supabase.auth.refresh_session(refresh_token)

        if not response or not response.session:
            return None

        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
        }

    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        return None


def logout_user(user_id: UUID, refresh_token: Optional[str] = None) -> bool:
    """
    Logout user by invalidating their Supabase session.
    """
    if refresh_token:
        try:
            supabase.table("token_blacklist").insert({
                "token_hash": refresh_token[:32],
                "user_id": str(user_id),
                "expires_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception:
            pass  # Silent fail for blacklist

    return True


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify token via Supabase Auth and return user payload.
    Returns user info dict if valid, None otherwise.
    """
    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user
        if not user:
            return None
        return {
            "sub": str(user.id),
            "email": user.email,
            "id": str(user.id),
        }
    except Exception:
        return None

from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging
from database import supabase

logger = logging.getLogger(__name__)


def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """
    Validate refresh token and issue new access + refresh tokens via Supabase Auth.

    Args:
        refresh_token: Supabase refresh token

    Returns:
        Dict with access_token and refresh_token, or None if invalid
    """
    try:
        response = supabase.auth.refresh_session(refresh_token)

        if not response or not response.session:
            return None

        session = response.session
        user = response.user

        # Update last_login if user is available
        if user:
            try:
                supabase.table("chamber_users").update({
                    "last_login": datetime.now(timezone.utc).isoformat()
                }).eq("id", str(user.id)).execute()
            except Exception as e:
                logger.warning(f"Failed to update last_login: {e}")

        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
        }

    except Exception as e:
        logger.warning(f"Token refresh failed: {e}")
        return None


def _hash_token(token: str) -> str:
    """
    Create a hash of the token for revocation tracking.
    Uses SHA-256 for consistency.
    """
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()

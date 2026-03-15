from datetime import datetime, timezone
from typing import Optional, Dict, Any
import os
import jwt
from database import supabase

JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable not set")


def refresh_access_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    """
    Validate refresh token and issue new access + refresh tokens.
    
    Args:
        refresh_token: JWT refresh token
    
    Returns:
        Dict with access_token and refresh_token, or None if invalid
    """
    try:
        # Decode and validate refresh token
        payload = jwt.decode(
            refresh_token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if not user_id or token_type != "refresh":
            return None
        
        # Verify user still exists and is active
        result = supabase.table("users").select(
            "id, email, role, full_name, chamber, business_group_id"
        ).eq("id", user_id).eq("is_active", True).execute()
        
        if not result.data or len(result.data) == 0:
            return None
        
        user = result.data[0]
        
        # Check if refresh token is revoked
        revoked_check = supabase.table("revoked_tokens").select(
            "token_hash"
        ).eq("token_hash", _hash_token(refresh_token)).execute()
        
        if revoked_check.data and len(revoked_check.data) > 0:
            return None
        
        # Generate new tokens
        now = datetime.now(timezone.utc)
        
        access_payload = {
            "sub": user["id"],
            "email": user["email"],
            "role": user["role"],
            "type": "access",
            "iat": now,
            "exp": now.timestamp() + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        }
        
        refresh_payload = {
            "sub": user["id"],
            "type": "refresh",
            "iat": now,
            "exp": now.timestamp() + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        }
        
        new_access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        new_refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Revoke old refresh token
        supabase.table("revoked_tokens").insert({
            "token_hash": _hash_token(refresh_token),
            "revoked_at": now.isoformat(),
            "reason": "token_refresh"
        }).execute()
        
        # Update last_login
        supabase.table("users").update({
            "last_login": now.isoformat()
        }).eq("id", user_id).execute()
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token
        }
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None


def _hash_token(token: str) -> str:
    """
    Create a hash of the token for revocation tracking.
    Uses SHA-256 for consistency.
    """
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()

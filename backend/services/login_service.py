from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
import os
import jwt
import bcrypt
from database import supabase

# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip()
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60").strip())
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7").strip())

if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hashed password."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def _create_token(data: Dict[str, Any], expires_delta: timedelta) -> str:
    """Create a JWT token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieve user by email from Supabase."""
    result = supabase.table("chamber_users").select("*").eq("email", email).eq("is_active", True).execute()
    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


def _update_last_login(user_id: UUID) -> None:
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
    Authenticate user with email and password.
    Returns user data with tokens if successful, None otherwise.
    """
    # Check rate limit
    if not _check_rate_limit(email):
        _record_login_attempt(email, False, ip_address)
        return None
    
    # Get user by email
    user = _get_user_by_email(email)
    if not user:
        _record_login_attempt(email, False, ip_address)
        return None
    
    # Verify password
    if not _verify_password(password, user.get("password_hash", "")):
        _record_login_attempt(email, False, ip_address)
        return None
    
    # Generate tokens
    user_id = user["id"]
    access_token = _create_token(
        {"sub": str(user_id), "email": user["email"], "role": user["role"]},
        timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh_token = _create_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    # Update last login
    _update_last_login(user_id)
    
    # Record successful login
    _record_login_attempt(email, True, ip_address)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "full_name": user.get("full_name", ""),
            "chamber": user.get("chamber", "")
        }
    }


def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """
    Generate new access token from refresh token.
    Returns new access token if valid, None otherwise.
    """
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Get user to ensure still active
        result = supabase.table("chamber_users").select("id, email, role, is_active").eq(
            "id", user_id
        ).eq("is_active", True).execute()
        
        if not result.data or len(result.data) == 0:
            return None
        
        user = result.data[0]
        
        # Generate new access token
        access_token = _create_token(
            {"sub": str(user["id"]), "email": user["email"], "role": user["role"]},
            timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {"access_token": access_token}
    
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def logout_user(user_id: UUID, refresh_token: Optional[str] = None) -> bool:
    """
    Logout user and invalidate refresh token.
    In a production system, store invalidated tokens in a blacklist table.
    """
    # Optional: Add token to blacklist table
    if refresh_token:
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            exp = payload.get("exp")
            if exp:
                supabase.table("token_blacklist").insert({
                    "token_hash": refresh_token[:32],  # Store hash prefix for lookup
                    "user_id": str(user_id),
                    "expires_at": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()
                }).execute()
        except Exception:
            pass  # Silent fail for blacklist
    
    return True


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and return payload.
    Returns payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

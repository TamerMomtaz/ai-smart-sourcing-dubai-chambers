from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, List
import logging

from database import supabase

logger = logging.getLogger(__name__)


class UserContext(dict):
    """Dict subclass that supports attribute access.

    Routes use both dict-style (current_user["id"]) and attribute-style
    (current_user.id) access.  This class supports both so that all route
    files work regardless of which pattern they use.
    """

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'UserContext' has no attribute '{name}'") from None

    def __setattr__(self, name, value):
        self[name] = value

security = HTTPBearer()

# Permission matrix matching Dubai Chambers RBAC
PERMISSION_MATRIX: Dict[str, List[str]] = {
    "vendor": [
        "proposals:create_own",
        "proposals:read_own",
        "proposals:update_own_draft",
        "documents:upload_own",
        "documents:read_own",
        "vendor_profile:read_own",
        "vendor_profile:update_own",
        "notifications:read_own"
    ],
    "analyst": [
        "proposals:read_all",
        "proposals:update_status",
        "proposals:evaluate",
        "documents:read_all",
        "documents:download_all",
        "evaluations:read_all",
        "evaluations:create",
        "compliance_audits:read_all",
        "compliance_audits:create",
        "comments:create",
        "comments:read_all",
        "vendors:read_all",
        "business_groups:read_all",
        "ai_interactions:read_own_sessions",
        "notifications:read_own"
    ],
    "business_group_lead": [
        "proposals:read_sector",
        "proposals:update_status_sector",
        "proposals:evaluate_sector",
        "documents:read_sector",
        "evaluations:read_sector",
        "compliance_audits:read_sector",
        "comments:create",
        "comments:read_sector",
        "vendors:read_sector",
        "business_groups:read_own",
        "business_groups:update_config_own",
        "sector_analytics:read_own",
        "ai_interactions:read_sector_sessions",
        "notifications:read_own"
    ],
    "compliance_officer": [
        "proposals:read_all",
        "documents:read_all",
        "evaluations:read_all",
        "compliance_audits:read_all",
        "compliance_audits:create",
        "compliance_audits:generate_report",
        "desc_registry:read",
        "ai_interactions:read_all_compliance",
        "audit_trail:read_all",
        "notifications:read_own"
    ],
    "executive": [
        "proposals:read_all",
        "evaluations:read_all",
        "compliance_audits:read_all",
        "trend_analysis:read_all",
        "dashboards:executive",
        "business_groups:read_all",
        "sector_analytics:read_all",
        "vendors:read_all",
        "ai_interactions:read_all_aggregated",
        "export:reports",
        "notifications:read_own"
    ],
    "admin": ["*:*"]
}


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """
    Validate Supabase auth token using supabase.auth.get_user().
    Extract user id, email, role, and permissions.
    Default role to 'vendor' (lowest privilege) if not specified.
    """
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "detail": "Invalid or expired token",
                    "code": 401
                }
            )

        user_id = user.id
        email = user.email

        # Try to get role from chamber_users table first (source of truth),
        # then fall back to app_metadata, then default to 'vendor'.
        role = None
        try:
            chamber_user = supabase.table("chamber_users").select("role").eq("id", user_id).maybe_single().execute()
            if chamber_user and chamber_user.data:
                role = chamber_user.data.get("role")
        except Exception as db_err:
            logger.warning(f"Failed to fetch role from chamber_users: {db_err}")

        if not role:
            app_metadata = user.app_metadata or {}
            role = app_metadata.get("role", "vendor")

        # Get permissions for role
        permissions = PERMISSION_MATRIX.get(role, PERMISSION_MATRIX["vendor"])

        return UserContext({
            "id": user_id,
            "sub": user_id,
            "user_id": user_id,
            "email": email,
            "role": role,
            "permissions": permissions,
            "access_token": token,
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "detail": "Invalid or expired token",
                "code": 401
            }
        ) from e


def require_permission(required_permission: str):
    """
    Dependency to check if current user has required permission.
    Admin role with '*:*' bypasses all checks.
    """
    async def permission_checker(current_user: Dict = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        
        # Admin has all permissions
        if "*:*" in user_permissions:
            return current_user
        
        # Check specific permission
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_permissions",
                    "detail": f"Permission '{required_permission}' required",
                    "code": 403
                }
            )
        
        return current_user
    
    return permission_checker


def require_role(required_role: str):
    """
    Dependency to check if current user has required role.
    """
    async def role_checker(current_user: Dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        
        if user_role != required_role and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_role",
                    "detail": f"Role '{required_role}' required",
                    "code": 403
                }
            )
        
        return current_user
    
    return role_checker

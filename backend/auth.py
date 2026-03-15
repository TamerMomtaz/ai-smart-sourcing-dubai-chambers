from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Dict, List
from config import SUPABASE_JWT_SECRET

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
    Decode and validate Supabase JWT token.
    Extract user id, email, role, and permissions.
    Default role to 'vendor' (lowest privilege) if not specified.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "detail": "Token missing user identifier",
                    "code": 401
                }
            )
        
        email = payload.get("email")
        role = payload.get("role", "vendor")
        
        # Get permissions for role
        permissions = PERMISSION_MATRIX.get(role, PERMISSION_MATRIX["vendor"])
        
        return {
            "id": user_id,
            "email": email,
            "role": role,
            "permissions": permissions
        }
    
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "detail": "Invalid or expired token",
                "code": 401
            }
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "auth_error",
                "detail": "Authentication processing failed",
                "code": 500
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

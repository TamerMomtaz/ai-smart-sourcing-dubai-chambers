from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
import logging

from services.ai_interaction_service import verify_integrity

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/transparency",
    tags=["transparency"],
)


@router.get(
    "/verify-integrity",
    summary="Verify AI interaction audit log integrity",
    description="Walks the hash chain from newest to oldest to detect tampering. "
    "Returns chain validity status and the first broken record if any.",
    responses={
        200: {"description": "Integrity verification result"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden — admin or compliance_officer role required"},
        500: {"description": "Internal server error"},
    },
)
async def verify_audit_integrity(
    current_user=Depends(get_current_user),
):
    allowed_roles = ["admin", "compliance_officer"]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Forbidden",
                "detail": "Admin or compliance officer role required",
                "code": 403,
            },
        )

    try:
        result = verify_integrity()
        return result
    except Exception as e:
        logger.error(f"Integrity verification failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to verify audit log integrity",
                "code": 500,
            },
        )

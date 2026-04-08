from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
import logging

from services.ai_interaction_service import verify_integrity, get_retention_info

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/transparency",
    tags=["transparency"],
)


@router.get(
    "/retention-info",
    summary="Get data retention policy information",
    description="Returns retention policy metadata including record counts, date ranges, "
    "and compliance status. Informational only — no data is deleted or archived.",
    responses={
        200: {"description": "Retention policy information"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden — admin or compliance_officer role required"},
        500: {"description": "Internal server error"},
    },
)
async def retention_info(
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
        result = get_retention_info()
        return result
    except Exception as e:
        logger.error(f"Failed to retrieve retention info: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to retrieve retention policy information",
                "code": 500,
            },
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

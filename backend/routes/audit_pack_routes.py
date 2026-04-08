"""Routes for DESC Audit Evidence Pack generation."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
import logging

from auth import get_current_user
from services.audit_pack_service import generate_audit_pack

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compliance",
    tags=["Audit Evidence Pack"],
)


@router.post(
    "/audit-pack",
    summary="Generate DESC Audit Evidence Pack",
    description="Aggregates platform controls, compliance audits, AI transparency logs, "
    "incidents, access control, data residency, model inventory, and evidence "
    "validation into a comprehensive audit evidence bundle. "
    "Admin and compliance_officer roles only.",
)
async def generate_audit_evidence_pack(
    current_user: dict = Depends(get_current_user),
):
    """Generate comprehensive DESC audit evidence pack."""
    try:
        user_role = current_user.get("role", "").strip()
        allowed_roles = ["admin", "compliance_officer"]

        if user_role not in allowed_roles:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "detail": "Only admin and compliance officers can generate audit packs",
                    "code": "ROLE_ADMIN_OR_COMPLIANCE_REQUIRED",
                },
            )

        pack = generate_audit_pack()
        pack["generated_by"] = current_user.get("email", "unknown")

        return pack

    except Exception as e:
        logger.error(f"Error generating audit evidence pack: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "Failed to generate audit evidence pack",
                "code": "AUDIT_PACK_GENERATION_FAILED",
            },
        )

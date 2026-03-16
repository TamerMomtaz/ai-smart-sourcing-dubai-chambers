from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
from models.compliance import ComplianceReportResponse
from models.common import ErrorResponse
from auth import get_current_user
from services import report_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compliance-audits",
    tags=["compliance-reports"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - Compliance officer role required"},
        404: {"model": ErrorResponse, "description": "Audit report not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)


@router.get(
    "/{audit_id}/report",
    response_model=ComplianceReportResponse,
    summary="Download DESC-format compliance audit report PDF",
    status_code=status.HTTP_200_OK,
)
async def download_compliance_report(
    audit_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ComplianceReportResponse:
    """
    Generate and download DESC-format compliance audit report PDF.
    
    **Authorization:** Compliance Officer role required
    
    **Rate Limit:** 60 requests per minute
    
    **Returns:**
    - report_url: Pre-signed URL for report download
    - expires_at: URL expiration timestamp
    
    **Error Responses:**
    - 401: Unauthorized - Invalid or missing authentication
    - 403: Forbidden - User does not have compliance_officer role
    - 404: Audit report not found or does not exist
    - 500: Internal server error during report generation
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")
        
        if not user_id:
            logger.error("Missing user_id in current_user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid authentication token", "code": "AUTH_INVALID"},
            )
        
        # RBAC check: Only compliance officers can download reports
        if user_role != "compliance_officer":
            logger.warning(
                f"User {user_id} with role {user_role} attempted to download compliance report for audit {audit_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Only compliance officers can download audit reports",
                    "code": "RBAC_COMPLIANCE_OFFICER_REQUIRED",
                },
            )
        
        # Generate report via service
        report_data = report_service.generate_compliance_report(
            user_id=str(user_id),
            audit_id=audit_id,
        )
        
        if not report_data:
            logger.error(f"Compliance audit {audit_id} not found or report generation failed")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not Found",
                    "detail": f"Compliance audit report with ID {audit_id} not found",
                    "code": "AUDIT_REPORT_NOT_FOUND",
                },
            )
        
        logger.info(f"Compliance officer {user_id} downloaded report for audit {audit_id}")
        
        return ComplianceReportResponse(
            report_url=report_data["report_url"],
            expires_at=report_data["expires_at"],
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating compliance report for audit {audit_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to generate compliance audit report",
                "code": "REPORT_GENERATION_FAILED",
            },
        )

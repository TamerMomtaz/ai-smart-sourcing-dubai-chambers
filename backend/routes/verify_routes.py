from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import logging

from auth import get_current_user
from models.compliance import (
    CertifiedProviderVerifyRequest,
    CertifiedProviderVerifyResponse,
    CertificationDetails,
)
from models.common import ErrorResponse
from services.verify_service import verify_vendor_certification

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/desc-certified-providers",
    tags=["DESC Certified Providers"],
)


@router.post(
    "/verify",
    response_model=CertifiedProviderVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify vendor against DESC certified providers registry",
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Vendor not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def verify_vendor(
    request: CertifiedProviderVerifyRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> CertifiedProviderVerifyResponse:
    """
    Verify if a vendor has DESC (Dubai Electronic Security Center) certification.
    
    This endpoint checks the vendor against the DESC certified providers registry
    and returns certification status and details if certified.
    
    **Required Permission:** Authenticated user (any role)
    
    **Args:**
    - vendor_id: UUID of the vendor to verify
    
    **Returns:**
    - vendor_id: Verified vendor UUID
    - is_certified: Boolean indicating certification status
    - certification_details: Details if certified (null otherwise)
        - certification_number: Official certification number
        - valid_until: Expiration date of certification
        - compliance_frameworks: List of compliance frameworks covered
    
    **Error Codes:**
    - 401: User not authenticated
    - 404: Vendor not found in system
    - 500: Internal server error during verification
    """
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            logger.error("verify_vendor: Missing user_id in token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "Unauthorized",
                    "detail": "Invalid authentication token",
                    "code": "INVALID_TOKEN",
                },
            )

        vendor_id = request.vendor_id
        logger.info(
            f"verify_vendor: user_id={user_id} verifying vendor_id={vendor_id}"
        )

        # Call service layer to verify vendor certification
        result = await verify_vendor_certification(
            user_id=str(user_id),
            vendor_id=vendor_id,
        )

        if result is None:
            logger.warning(f"verify_vendor: vendor_id={vendor_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not Found",
                    "detail": f"Vendor with ID {vendor_id} not found",
                    "code": "VENDOR_NOT_FOUND",
                },
            )

        # Build certification details if vendor is certified
        certification_details = None
        if result.get("is_certified"):
            cert_data = result.get("certification_details", {})
            certification_details = CertificationDetails(
                certification_number=cert_data.get("certification_number", ""),
                valid_until=cert_data.get("valid_until"),
                compliance_frameworks=cert_data.get("compliance_frameworks", []),
            )

        response = CertifiedProviderVerifyResponse(
            vendor_id=vendor_id,
            is_certified=result.get("is_certified", False),
            certification_details=certification_details,
        )

        logger.info(
            f"verify_vendor: vendor_id={vendor_id} is_certified={response.is_certified}"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"verify_vendor: Unexpected error verifying vendor_id={request.vendor_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to verify vendor certification",
                "code": "VERIFICATION_FAILED",
            },
        )

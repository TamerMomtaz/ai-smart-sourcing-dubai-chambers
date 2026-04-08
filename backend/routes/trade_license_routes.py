from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID, uuid4
from datetime import datetime, timezone

from auth import get_current_user
from models.vendor import TradeLicenseVerifyRequest, TradeLicenseStatusResponse
from models.common import ErrorResponse
from database import supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendors", tags=["Trade License Verification"])


@router.post(
    "/{vendor_id}/verify-license",
    response_model=TradeLicenseStatusResponse,
    summary="Submit trade license for verification",
    responses={
        200: {"description": "Verification request submitted"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Vendor not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def verify_trade_license(
    vendor_id: UUID,
    body: TradeLicenseVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Submit a trade license number for Dubai GRP verification (stub).
    Admin and analyst roles only."""
    try:
        user_role = current_user["role"]
        user_id = current_user["id"]

        if user_role not in ["admin", "analyst"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Only admin or analyst can verify trade licenses",
                    "code": "INSUFFICIENT_PERMISSIONS",
                },
            )

        # Check vendor exists
        vendor_resp = (
            supabase.table("chamber_vendors")
            .select("id, name")
            .eq("id", str(vendor_id))
            .maybe_single()
            .execute()
        )

        if not vendor_resp.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not found",
                    "detail": "Vendor not found",
                    "code": "VENDOR_NOT_FOUND",
                },
            )

        # Store trade license number and set status to pending
        supabase.table("chamber_vendors").update({
            "trade_license_number": body.trade_license_number,
            "trade_license_status": "pending",
            "trade_license_details": {
                "submitted_by": str(user_id),
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "source": "stub — awaiting Dubai GRP integration",
            },
        }).eq("id", str(vendor_id)).execute()

        # Log to chamber_ai_interactions audit trail
        try:
            supabase.table("chamber_ai_interactions").insert({
                "session_id": str(uuid4()),
                "user_id": str(user_id),
                "operation_type": "license_verification",
                "model_name": f"trade_license_stub:{body.trade_license_number}",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "latency_ms": 0,
                "cost_usd": 0,
                "energy_kwh": 0,
                "carbon_gco2": 0,
                "intelligence_units": 0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as audit_err:
            logger.warning(f"Failed to log license verification audit: {audit_err}")

        return TradeLicenseStatusResponse(
            vendor_id=vendor_id,
            trade_license_number=body.trade_license_number,
            trade_license_status="pending",
            trade_license_verified_at=None,
            trade_license_details=None,
            message=(
                "Verification request submitted to Dubai GRP. "
                "In production, this connects to developer.dubai.gov.ae "
                "for real-time corporate registry verification."
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying trade license for vendor {vendor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred during license verification",
                "code": "LICENSE_VERIFY_ERROR",
            },
        )


@router.get(
    "/{vendor_id}/license-status",
    response_model=TradeLicenseStatusResponse,
    summary="Get trade license verification status",
    responses={
        200: {"description": "License status retrieved"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Vendor not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_license_status(
    vendor_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get the current trade license verification status for a vendor."""
    try:
        vendor_resp = (
            supabase.table("chamber_vendors")
            .select(
                "id, trade_license_number, trade_license_status, "
                "trade_license_verified_at, trade_license_details"
            )
            .eq("id", str(vendor_id))
            .maybe_single()
            .execute()
        )

        if not vendor_resp.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not found",
                    "detail": "Vendor not found",
                    "code": "VENDOR_NOT_FOUND",
                },
            )

        v = vendor_resp.data
        return TradeLicenseStatusResponse(
            vendor_id=UUID(v["id"]),
            trade_license_number=v.get("trade_license_number"),
            trade_license_status=v.get("trade_license_status", "unverified"),
            trade_license_verified_at=v.get("trade_license_verified_at"),
            trade_license_details=v.get("trade_license_details"),
            message=None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting license status for vendor {vendor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred while retrieving license status",
                "code": "LICENSE_STATUS_ERROR",
            },
        )

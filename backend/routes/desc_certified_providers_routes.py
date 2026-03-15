from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import date
import logging

from auth import get_current_user
from models.compliance import (
    CertifiedProvider,
    CertifiedProviderVerifyRequest,
    CertifiedProviderVerifyResponse,
)
from models.common import ErrorResponse
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/desc-certified-providers",
    tags=["desc-certified-providers"],
)


@router.get(
    "",
    response_model=dict,
    responses={
        200: {"description": "List of DESC certified providers"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_desc_certified_providers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
):
    """
    Query DESC certified providers registry.
    Returns paginated list of certified providers with certification details.
    Auth required: All authenticated users.
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail={"error": "Unauthorized", "detail": "Invalid user token", "code": "AUTH_INVALID_TOKEN"},
            )

        offset = (page - 1) * page_size

        # Query desc_certified_providers table with pagination
        query = supabase.table("desc_certified_providers").select(
            "id, provider_name, certification_number, valid_until, services_offered, compliance_frameworks",
            count="exact",
        )

        # Apply pagination
        response = query.range(offset, offset + page_size - 1).execute()

        if not response:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "DatabaseError",
                    "detail": "Failed to query certified providers",
                    "code": "DB_QUERY_FAILED",
                },
            )

        providers_data = response.data if response.data else []
        total_count = response.count if hasattr(response, "count") and response.count is not None else 0

        # Map database records to CertifiedProvider models
        providers = []
        for record in providers_data:
            try:
                provider = CertifiedProvider(
                    id=UUID(record["id"]),
                    provider_name=record["provider_name"],
                    certification_number=record["certification_number"],
                    valid_until=date.fromisoformat(record["valid_until"]) if isinstance(record["valid_until"], str) else record["valid_until"],
                    services_offered=record.get("services_offered", []),
                    compliance_frameworks=record.get("compliance_frameworks", []),
                )
                providers.append(provider)
            except Exception as parse_error:
                logger.warning(f"Failed to parse provider record {record.get('id')}: {parse_error}")
                continue

        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

        return {
            "providers": [p.model_dump() for p in providers],
            "pagination": {
                "total": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing DESC certified providers: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "detail": "Failed to retrieve certified providers",
                "code": "INTERNAL_ERROR",
            },
        )


@router.post(
    "/verify",
    response_model=CertifiedProviderVerifyResponse,
    responses={
        200: {"description": "Vendor certification verification result"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Vendor not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def verify_vendor_certification(
    request: CertifiedProviderVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Verify vendor against DESC certified providers registry.
    Checks if vendor has valid DESC certification and returns certification details.
    Auth required: All authenticated users.
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail={"error": "Unauthorized", "detail": "Invalid user token", "code": "AUTH_INVALID_TOKEN"},
            )

        vendor_id = request.vendor_id

        # Verify vendor exists
        vendor_response = supabase.table("chamber_vendors").select(
            "id, name, is_desc_approved, desc_badge_issued_date"
        ).eq("id", str(vendor_id)).maybeSingle().execute()

        if not vendor_response or not vendor_response.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "NotFound",
                    "detail": f"Vendor {vendor_id} not found",
                    "code": "VENDOR_NOT_FOUND",
                },
            )

        vendor = vendor_response.data
        is_desc_approved = vendor.get("is_desc_approved", False)

        # If vendor is DESC approved, look up certification details
        certification_details = None
        if is_desc_approved:
            # Try to find matching certification record by vendor name
            cert_response = supabase.table("desc_certified_providers").select(
                "certification_number, valid_until, compliance_frameworks"
            ).eq("provider_name", vendor["name"]).maybeSingle().execute()

            if cert_response and cert_response.data:
                cert_data = cert_response.data
                certification_details = {
                    "certification_number": cert_data["certification_number"],
                    "valid_until": date.fromisoformat(cert_data["valid_until"]) if isinstance(cert_data["valid_until"], str) else cert_data["valid_until"],
                    "compliance_frameworks": cert_data.get("compliance_frameworks", []),
                }

        return CertifiedProviderVerifyResponse(
            vendor_id=vendor_id,
            is_certified=is_desc_approved,
            certification_details=certification_details,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying vendor certification for {request.vendor_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "detail": "Failed to verify vendor certification",
                "code": "INTERNAL_ERROR",
            },
        )

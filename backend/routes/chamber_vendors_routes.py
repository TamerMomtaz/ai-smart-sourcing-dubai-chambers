from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from datetime import datetime, timezone

from auth import get_current_user
from models.vendor import (
    Vendor,
    VendorResponse,
    VendorProfileUpdate,
    VendorUpdateResponse,
)
from models.common import PaginationResponse, ErrorResponse
from services import chamber_vendor_service, chamber_vendor_profile_service
from database import supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendors", tags=["Vendors"])


@router.post(
    "",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create vendor profile",
    responses={
        201: {"description": "Vendor created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_vendor(
    vendor: Vendor,
    current_user: dict = Depends(get_current_user),
):
    """Create new vendor profile. Admin/analyst only operation."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user["role"]

        if user_role not in ["admin", "analyst"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Only admin or analyst can create vendor profiles",
                    "code": "INSUFFICIENT_PERMISSIONS",
                },
            )

        result = await chamber_vendor_service.create_vendor(
            name=vendor.name,
            company_registration=vendor.company_registration,
            country=vendor.country,
            contact_email=vendor.contact_email,
            contact_phone=vendor.contact_phone,
            website=vendor.website,
            is_desc_approved=vendor.is_desc_approved,
            desc_badge_issued_date=vendor.desc_badge_issued_date,
            onboarding_status=vendor.onboarding_status,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Creation failed",
                    "detail": "Failed to create vendor profile",
                    "code": "VENDOR_CREATE_FAILED",
                },
            )

        return VendorResponse(
            id=UUID(result["id"]),
            name=result["name"],
            company_registration=result["company_registration"],
            country=result["country"],
            contact_email=result["contact_email"],
            contact_phone=result.get("contact_phone"),
            website=result.get("website"),
            is_desc_approved=result["is_desc_approved"],
            desc_badge_issued_date=result.get("desc_badge_issued_date"),
            onboarding_status=result["onboarding_status"],
            submission_history_count=result.get("submission_history_count", 0),
            average_compliance_score=result.get("average_compliance_score"),
            profile=None,
            desc_certified=result.get("desc_certified", False),
            desc_certification_level=result.get("desc_certification_level"),
            desc_provider_name=result.get("desc_provider_name"),
            reputation_score=result.get("reputation_score"),
            reputation_tier=result.get("reputation_tier"),
            vscore=result.get("vscore"),
            vscore_tier=result.get("vscore_tier"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vendor: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred while creating vendor",
                "code": "VENDOR_CREATE_ERROR",
            },
        )


@router.get(
    "",
    response_model=dict,
    summary="List all vendors",
    responses={
        200: {"description": "Vendors retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_vendors(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    current_user: dict = Depends(get_current_user),
):
    """List vendors with pagination. Analyst/executive/business_group_lead access."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user["role"]

        # Vendor role gets empty list (they access their own profile via /vendors/{id})
        if user_role not in ["admin", "analyst", "executive", "business_group_lead", "compliance_officer"]:
            return {
                "vendors": [],
                "pagination": PaginationResponse(
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0,
                ),
            }

        vendor_data, total = await chamber_vendor_service.list_vendors(
            user_id=user_id,
            user_role=user_role,
            page=page,
            page_size=page_size,
            sector=sector,
        )

        if vendor_data is None:
            vendor_data = []
            total = 0

        vendors = [
            VendorResponse(
                id=UUID(v["id"]),
                name=v["name"],
                company_registration=v["company_registration"],
                country=v["country"],
                contact_email=v["contact_email"],
                contact_phone=v.get("contact_phone"),
                website=v.get("website"),
                is_desc_approved=v["is_desc_approved"],
                desc_badge_issued_date=v.get("desc_badge_issued_date"),
                onboarding_status=v["onboarding_status"],
                submission_history_count=v.get("submission_history_count", 0),
                average_compliance_score=v.get("average_compliance_score"),
                profile=None,
                desc_certified=v.get("desc_certified", False),
                desc_certification_level=v.get("desc_certification_level"),
                desc_provider_name=v.get("desc_provider_name"),
                reputation_score=v.get("reputation_score"),
                reputation_tier=v.get("reputation_tier"),
                vscore=v.get("vscore"),
                vscore_tier=v.get("vscore_tier"),
            )
            for v in vendor_data
        ]

        total_pages = (total + page_size - 1) // page_size

        return {
            "vendors": vendors,
            "pagination": PaginationResponse(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing vendors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred while listing vendors",
                "code": "VENDOR_LIST_ERROR",
            },
        )


@router.get(
    "/{vendor_id}",
    response_model=VendorResponse,
    summary="Get vendor by ID",
    responses={
        200: {"description": "Vendor retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Vendor not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_vendor(
    vendor_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get vendor profile by ID. Vendors can only view their own profile."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user["role"]

        result = await chamber_vendor_service.get_vendor_by_id(
            user_id=user_id,
            vendor_id=vendor_id,
            user_role=user_role,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not found",
                    "detail": "Vendor not found or access denied",
                    "code": "VENDOR_NOT_FOUND",
                },
            )

        return VendorResponse(
            id=UUID(result["id"]),
            name=result["name"],
            company_registration=result["company_registration"],
            country=result["country"],
            contact_email=result["contact_email"],
            contact_phone=result.get("contact_phone"),
            website=result.get("website"),
            is_desc_approved=result["is_desc_approved"],
            desc_badge_issued_date=result.get("desc_badge_issued_date"),
            onboarding_status=result["onboarding_status"],
            submission_history_count=result.get("submission_history_count", 0),
            average_compliance_score=result.get("average_compliance_score"),
            profile=result.get("profile"),
            desc_certified=result.get("desc_certified", False),
            desc_certification_level=result.get("desc_certification_level"),
            desc_provider_name=result.get("desc_provider_name"),
            reputation_score=result.get("reputation_score"),
            reputation_tier=result.get("reputation_tier"),
            vscore=result.get("vscore"),
            vscore_tier=result.get("vscore_tier"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred while retrieving vendor",
                "code": "VENDOR_GET_ERROR",
            },
        )


@router.put(
    "/{vendor_id}",
    response_model=VendorUpdateResponse,
    summary="Update vendor profile",
    responses={
        200: {"description": "Vendor updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Vendor not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_vendor(
    vendor_id: UUID,
    update_data: VendorProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update vendor profile. Vendors can only update their own profile."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user["role"]

        if user_role == "vendor":
            vendor_check = await chamber_vendor_service.get_vendor_by_id(
                user_id=user_id,
                vendor_id=vendor_id,
                user_role=user_role,
            )
            if not vendor_check or UUID(vendor_check["id"]) != vendor_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Forbidden",
                        "detail": "Vendors can only update their own profile",
                        "code": "INSUFFICIENT_PERMISSIONS",
                    },
                )

        update_dict = update_data.model_dump(exclude_unset=True)
        
        result = await chamber_vendor_service.update_vendor(
            user_id=user_id,
            vendor_id=vendor_id,
            update_data=update_dict,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not found",
                    "detail": "Vendor not found or update failed",
                    "code": "VENDOR_UPDATE_FAILED",
                },
            )

        return VendorUpdateResponse(
            vendor_id=UUID(result["id"]),
            updated_at=datetime.now(timezone.utc),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred while updating vendor",
                "code": "VENDOR_UPDATE_ERROR",
            },
        )


@router.delete(
    "/{vendor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete vendor",
    responses={
        204: {"description": "Vendor deleted successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Vendor not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_vendor(
    vendor_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Delete vendor profile. Admin only operation."""
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user["role"]

        if user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Only admin can delete vendor profiles",
                    "code": "INSUFFICIENT_PERMISSIONS",
                },
            )

        result = await chamber_vendor_service.delete_vendor(
            user_id=user_id,
            vendor_id=vendor_id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not found",
                    "detail": "Vendor not found or delete failed",
                    "code": "VENDOR_DELETE_FAILED",
                },
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred while deleting vendor",
                "code": "VENDOR_DELETE_ERROR",
            },
        )


@router.get(
    "/{vendor_id}/reputation",
    summary="Get vendor reputation profile",
    responses={
        200: {"description": "Reputation profile retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Vendor not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_vendor_reputation(
    vendor_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get full reputation profile for a vendor including submission history."""
    try:
        user_role = current_user["role"]

        if user_role not in ["admin", "analyst", "executive", "business_group_lead", "compliance_officer", "vendor"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Insufficient permissions",
                    "code": "INSUFFICIENT_PERMISSIONS",
                },
            )

        vendor = await chamber_vendor_service.get_vendor_by_id(
            vendor_id=vendor_id,
            user_id=UUID(current_user["id"]),
            user_role=user_role,
        )

        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not found",
                    "detail": "Vendor not found",
                    "code": "VENDOR_NOT_FOUND",
                },
            )

        # Fetch submission history from chamber_proposals
        proposals_response = (
            supabase.table("chamber_proposals")
            .select("id, title, composite_score, submission_date, status, compliance_score, grounding_score")
            .eq("submitter_id", str(vendor_id))
            .order("submission_date", desc=True)
            .execute()
        )
        proposals = proposals_response.data or []

        submission_history = []
        for p in proposals:
            submission_history.append({
                "proposal_title": p.get("title", "Untitled"),
                "score": p.get("composite_score"),
                "date": p.get("submission_date"),
                "status": p.get("status", "submitted"),
                "compliance": p.get("compliance_score"),
                "grounding": p.get("grounding_score"),
            })

        desc_certified = vendor.get("desc_certified", False) or vendor.get("is_desc_approved", False)

        return {
            "vendor_id": str(vendor["id"]),
            "vendor_name": vendor.get("name"),
            "reputation_score": vendor.get("reputation_score"),
            "reputation_tier": vendor.get("reputation_tier"),
            "total_evaluations": vendor.get("total_evaluations", 0),
            "avg_evaluation_score": vendor.get("avg_evaluation_score"),
            "avg_grounding_score": vendor.get("avg_grounding_score"),
            "compliance_pass_rate": vendor.get("compliance_pass_rate"),
            "desc_certified": desc_certified,
            "shortlist_count": vendor.get("shortlist_count", 0),
            "rejection_count": vendor.get("rejection_count", 0),
            "submission_history": submission_history,
            "formula": {
                "evaluation_weight": 0.30,
                "compliance_weight": 0.25,
                "grounding_weight": 0.20,
                "desc_weight": 0.15,
                "engagement_weight": 0.10,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vendor reputation {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred while retrieving vendor reputation",
                "code": "VENDOR_REPUTATION_ERROR",
            },
        )

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
import logging

from auth.dependencies import get_current_user
from models.auth import UserInfo
from models.vendor import VendorProfile, VendorProfileUpdate
from models.common import ErrorResponse, PaginationResponse
from database import supabase

router = APIRouter(prefix="/chamber-vendor-profiles", tags=["Chamber Vendor Profiles"])
logger = logging.getLogger(__name__)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    responses={
        201: {"description": "Vendor profile created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - vendor only"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_vendor_profile(
    profile_data: VendorProfile,
    current_user: UserInfo = Depends(get_current_user),
):
    """Create vendor profile for authenticated vendor."""
    try:
        if current_user.role != "vendor":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Only vendors can create vendor profiles", "code": 403},
            )

        vendor_response = (
            supabase.table("chamber_vendors")
            .select("id")
            .eq("user_id", str(current_user.id))
            .maybeSingle()
            .execute()
        )

        if not vendor_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Vendor record not found for current user", "code": 404},
            )

        vendor_id = vendor_response.data["id"]

        existing_profile = (
            supabase.table("chamber_vendor_profiles")
            .select("id")
            .eq("vendor_id", vendor_id)
            .maybeSingle()
            .execute()
        )

        if existing_profile.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Bad Request", "detail": "Vendor profile already exists", "code": 400},
            )

        insert_data = {
            "vendor_id": vendor_id,
            "team_size": profile_data.team_size,
            "funding_stage": profile_data.funding_stage,
            "technology_stack": profile_data.technology_stack,
            "certifications": profile_data.certifications,
            "onboarding_stage": profile_data.onboarding_stage,
            "pilot_status": profile_data.pilot_status,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = supabase.table("chamber_vendor_profiles").insert(insert_data).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Internal Server Error", "detail": "Failed to create vendor profile", "code": 500},
            )

        return {"vendor_profile_id": result.data[0]["id"], "vendor_id": vendor_id, "created_at": result.data[0]["created_at"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating vendor profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": str(e), "code": 500},
        )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    responses={
        200: {"description": "List of vendor profiles retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_vendor_profiles(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: UserInfo = Depends(get_current_user),
):
    """List vendor profiles with pagination. Analysts/executives see all, vendors see their own."""
    try:
        if current_user.role not in ["analyst", "executive", "compliance_officer", "business_group_lead", "vendor"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": "Forbidden", "detail": "Insufficient permissions", "code": 403},
            )

        offset = (page - 1) * page_size

        query = supabase.table("chamber_vendor_profiles").select(
            "id, vendor_id, team_size, funding_stage, technology_stack, certifications, onboarding_stage, pilot_status, created_at, updated_at, chamber_vendors(id, name, company_registration, country, is_desc_approved)",
            count="exact",
        )

        if current_user.role == "vendor":
            vendor_response = (
                supabase.table("chamber_vendors")
                .select("id")
                .eq("user_id", str(current_user.id))
                .maybeSingle()
                .execute()
            )
            if not vendor_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "Not Found", "detail": "Vendor record not found", "code": 404},
                )
            query = query.eq("vendor_id", vendor_response.data["id"])

        result = query.range(offset, offset + page_size - 1).execute()

        total = result.count if result.count is not None else 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "profiles": result.data or [],
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing vendor profiles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": str(e), "code": 500},
        )


@router.get(
    "/{profile_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    responses={
        200: {"description": "Vendor profile retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Vendor profile not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_vendor_profile_by_id(
    profile_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """Get vendor profile by ID."""
    try:
        result = (
            supabase.table("chamber_vendor_profiles")
            .select(
                "id, vendor_id, team_size, funding_stage, technology_stack, certifications, onboarding_stage, pilot_status, created_at, updated_at, chamber_vendors(id, name, company_registration, country, contact_email, is_desc_approved, desc_badge_issued_date, onboarding_status, user_id)"
            )
            .eq("id", str(profile_id))
            .maybeSingle()
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Vendor profile not found", "code": 404},
            )

        vendor_data = result.data.get("chamber_vendors")
        if current_user.role == "vendor":
            if not vendor_data or vendor_data.get("user_id") != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"error": "Forbidden", "detail": "Cannot access other vendor profiles", "code": 403},
                )

        return result.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving vendor profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": str(e), "code": 500},
        )


@router.put(
    "/{profile_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    responses={
        200: {"description": "Vendor profile updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - vendor can only update own profile"},
        404: {"model": ErrorResponse, "description": "Vendor profile not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_vendor_profile(
    profile_id: UUID,
    profile_update: VendorProfile,
    current_user: UserInfo = Depends(get_current_user),
):
    """Update vendor profile."""
    try:
        existing = (
            supabase.table("chamber_vendor_profiles")
            .select("id, vendor_id, chamber_vendors(user_id)")
            .eq("id", str(profile_id))
            .maybeSingle()
            .execute()
        )

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Vendor profile not found", "code": 404},
            )

        vendor_data = existing.data.get("chamber_vendors")
        if current_user.role == "vendor":
            if not vendor_data or vendor_data.get("user_id") != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"error": "Forbidden", "detail": "Cannot update other vendor profiles", "code": 403},
                )

        update_data = {
            "team_size": profile_update.team_size,
            "funding_stage": profile_update.funding_stage,
            "technology_stack": profile_update.technology_stack,
            "certifications": profile_update.certifications,
            "onboarding_stage": profile_update.onboarding_stage,
            "pilot_status": profile_update.pilot_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = (
            supabase.table("chamber_vendor_profiles")
            .update(update_data)
            .eq("id", str(profile_id))
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Internal Server Error", "detail": "Failed to update vendor profile", "code": 500},
            )

        return {"profile_id": str(profile_id), "updated_at": result.data[0]["updated_at"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating vendor profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": str(e), "code": 500},
        )


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    responses={
        200: {"description": "Vendor profile deleted successfully"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - vendor can only delete own profile"},
        404: {"model": ErrorResponse, "description": "Vendor profile not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_vendor_profile(
    profile_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """Delete vendor profile."""
    try:
        existing = (
            supabase.table("chamber_vendor_profiles")
            .select("id, vendor_id, chamber_vendors(user_id)")
            .eq("id", str(profile_id))
            .maybeSingle()
            .execute()
        )

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Vendor profile not found", "code": 404},
            )

        vendor_data = existing.data.get("chamber_vendors")
        if current_user.role == "vendor":
            if not vendor_data or vendor_data.get("user_id") != str(current_user.id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"error": "Forbidden", "detail": "Cannot delete other vendor profiles", "code": 403},
                )

        result = supabase.table("chamber_vendor_profiles").delete().eq("id", str(profile_id)).execute()

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "Internal Server Error", "detail": "Failed to delete vendor profile", "code": 500},
            )

        return {"message": "Vendor profile deleted successfully", "profile_id": str(profile_id)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting vendor profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": str(e), "code": 500},
        )

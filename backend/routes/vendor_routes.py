from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime

from models.vendor import VendorResponse, VendorProfileUpdate, VendorUpdateResponse
from models.common import ErrorResponse
from auth.dependencies import get_current_user
from services import vendor_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/vendors",
    tags=["vendors"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)


@router.get(
    "/{vendor_id}",
    response_model=VendorResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vendor profile and submission history",
    responses={
        404: {"model": ErrorResponse, "description": "Vendor not found"},
    },
)
async def get_vendor(
    vendor_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Get vendor profile and submission history.
    
    Vendors can only view their own profile.
    Analysts, executives, business group leads, and compliance officers can view any vendor.
    
    Returns:
        - Vendor basic info
        - DESC approval status and badge date
        - Onboarding status
        - Submission history count
        - Average compliance score
        - Extended vendor profile (team size, funding, tech stack, certifications)
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")
        
        if not user_id or not user_role:
            logger.error("get_vendor: Missing user_id or role in token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid authentication token", "code": 401},
            )
        
        vendor_data = vendor_service.get_vendor_by_id(
            user_id=user_id,
            vendor_id=vendor_id,
            user_role=user_role,
        )
        
        if not vendor_data:
            logger.warning(f"get_vendor: Vendor {vendor_id} not found or access denied for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Not Found", "detail": "Vendor not found or access denied", "code": 404},
            )
        
        return vendor_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_vendor: Unexpected error for vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "Failed to retrieve vendor profile", "code": 500},
        )


@router.patch(
    "/{vendor_id}",
    response_model=VendorUpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Update vendor profile",
    responses={
        404: {"model": ErrorResponse, "description": "Vendor not found"},
    },
)
async def update_vendor(
    vendor_id: UUID,
    update_data: VendorProfileUpdate,
    current_user: dict = Depends(get_current_user),
):
    """
    Update vendor profile.
    
    Vendors can only update their own profile.
    Analysts and business group leads can update vendor profiles in their scope.
    
    Updatable fields:
    - name (company name)
    - contact_email
    - contact_phone
    - website
    - profile (extended profile: team_size, funding_stage, technology_stack, certifications)
    
    Returns:
        - vendor_id: Updated vendor UUID
        - updated_at: Timestamp of update
    """
    try:
        user_id = current_user.get("id")
        user_role = current_user.get("role")
        
        if not user_id or not user_role:
            logger.error("update_vendor: Missing user_id or role in token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Unauthorized", "detail": "Invalid authentication token", "code": 401},
            )
        
        # Check permissions: vendors can only update their own profile
        if user_role == "vendor":
            # Verify vendor_id matches user's vendor_id
            vendor_check = vendor_service.get_vendor_by_id(
                user_id=user_id,
                vendor_id=vendor_id,
                user_role=user_role,
            )
            if not vendor_check or str(vendor_check.get("id")) != str(vendor_id):
                logger.warning(f"update_vendor: Vendor {user_id} attempted to update {vendor_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={"error": "Forbidden", "detail": "You can only update your own vendor profile", "code": 403},
                )
        
        # Prepare update payload
        update_payload = {}
        if update_data.name is not None:
            update_payload["name"] = update_data.name
        if update_data.contact_email is not None:
            update_payload["contact_email"] = str(update_data.contact_email)
        if update_data.contact_phone is not None:
            update_payload["contact_phone"] = update_data.contact_phone
        if update_data.website is not None:
            update_payload["website"] = str(update_data.website)
        
        # Handle profile update
        profile_data = None
        if update_data.profile is not None:
            profile_data = update_data.profile.model_dump(exclude_none=True)
        
        # Call service to update vendor
        from services import chamber_vendor_service, chamber_vendor_profile_service
        
        # Update vendor base fields
        if update_payload:
            updated_vendor = await chamber_vendor_service.update_vendor(
                vendor_id=vendor_id,
                **update_payload
            )
            if not updated_vendor:
                logger.error(f"update_vendor: Failed to update vendor {vendor_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": "Not Found", "detail": "Vendor not found", "code": 404},
                )
        
        # Update vendor profile if provided
        if profile_data:
            updated_profile = await chamber_vendor_profile_service.update(
                vendor_id=vendor_id,
                **profile_data
            )
            if not updated_profile:
                # If profile doesn't exist, create it
                created_profile = await chamber_vendor_profile_service.create(
                    vendor_id=vendor_id,
                    **profile_data
                )
                if not created_profile:
                    logger.error(f"update_vendor: Failed to create/update profile for vendor {vendor_id}")
        
        return VendorUpdateResponse(
            vendor_id=vendor_id,
            updated_at=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update_vendor: Unexpected error updating vendor {vendor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": "Failed to update vendor profile", "code": 500},
        )

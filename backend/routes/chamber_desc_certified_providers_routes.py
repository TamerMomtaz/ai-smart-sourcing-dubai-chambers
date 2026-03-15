from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from uuid import UUID
from datetime import date
from models.compliance import CertifiedProvider, CertifiedProviderVerifyRequest, CertifiedProviderVerifyResponse
from models.common import ErrorResponse, PaginationResponse
from auth.dependencies import get_current_user
from services import chamber_desc_certified_providers_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/certified-providers",
    tags=["certified_providers"],
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}}
)


@router.post(
    "/",
    response_model=CertifiedProvider,
    status_code=201,
    summary="Create certified provider entry",
    description="Register a new DESC-certified provider (compliance officer only)"
)
async def create_certified_provider(
    provider_name: str,
    certification_number: str,
    valid_until: date,
    services_offered: List[str] = [],
    compliance_frameworks: List[str] = [],
    current_user: dict = Depends(get_current_user)
):
    """Create new DESC-certified provider entry."""
    try:
        user_id = current_user["id"]
        user_role = current_user["role"]
        
        if user_role not in ["compliance_officer", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={"error": "Forbidden", "detail": "Only compliance officers can register certified providers", "code": 403}
            )
        
        result = chamber_desc_certified_providers_service.create(
            user_id=UUID(user_id),
            provider_name=provider_name,
            certification_number=certification_number,
            valid_until=valid_until,
            services_offered=services_offered,
            compliance_frameworks=compliance_frameworks
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal Server Error", "detail": "Failed to create certified provider entry", "code": 500}
            )
        
        return CertifiedProvider(
            id=UUID(result["id"]),
            provider_name=result["provider_name"],
            certification_number=result["certification_number"],
            valid_until=result["valid_until"],
            services_offered=result.get("services_offered", []),
            compliance_frameworks=result.get("compliance_frameworks", [])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating certified provider: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": 500}
        )


@router.get(
    "/",
    response_model=dict,
    summary="List certified providers",
    description="Retrieve paginated list of DESC-certified providers"
)
async def list_certified_providers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user)
):
    """List all DESC-certified providers with pagination."""
    try:
        user_id = current_user["id"]
        
        result = chamber_desc_certified_providers_service.list_providers(
            user_id=UUID(user_id),
            page=page,
            page_size=page_size
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal Server Error", "detail": "Failed to retrieve certified providers", "code": 500}
            )
        
        providers = [
            CertifiedProvider(
                id=UUID(p["id"]),
                provider_name=p["provider_name"],
                certification_number=p["certification_number"],
                valid_until=p["valid_until"],
                services_offered=p.get("services_offered", []),
                compliance_frameworks=p.get("compliance_frameworks", [])
            )
            for p in result["providers"]
        ]
        
        total_pages = (result["total"] + page_size - 1) // page_size
        
        return {
            "providers": providers,
            "pagination": PaginationResponse(
                total=result["total"],
                page=page,
                page_size=page_size,
                total_pages=total_pages
            )
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing certified providers: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": 500}
        )


@router.get(
    "/{provider_id}",
    response_model=CertifiedProvider,
    summary="Get certified provider by ID",
    description="Retrieve detailed information for a specific certified provider"
)
async def get_certified_provider(
    provider_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Get certified provider details by ID."""
    try:
        user_id = current_user["id"]
        
        result = chamber_desc_certified_providers_service.get_by_id(
            user_id=UUID(user_id),
            provider_id=provider_id
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail={"error": "Not Found", "detail": "Certified provider not found", "code": 404}
            )
        
        return CertifiedProvider(
            id=UUID(result["id"]),
            provider_name=result["provider_name"],
            certification_number=result["certification_number"],
            valid_until=result["valid_until"],
            services_offered=result.get("services_offered", []),
            compliance_frameworks=result.get("compliance_frameworks", [])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving certified provider: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": 500}
        )


@router.put(
    "/{provider_id}",
    response_model=CertifiedProvider,
    summary="Update certified provider",
    description="Update certified provider information (compliance officer only)"
)
async def update_certified_provider(
    provider_id: UUID,
    provider_name: str = None,
    certification_number: str = None,
    valid_until: date = None,
    services_offered: List[str] = None,
    compliance_frameworks: List[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Update certified provider details."""
    try:
        user_id = current_user["id"]
        user_role = current_user["role"]
        
        if user_role not in ["compliance_officer", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={"error": "Forbidden", "detail": "Only compliance officers can update certified providers", "code": 403}
            )
        
        result = chamber_desc_certified_providers_service.update(
            user_id=UUID(user_id),
            provider_id=provider_id,
            provider_name=provider_name,
            certification_number=certification_number,
            valid_until=valid_until,
            services_offered=services_offered,
            compliance_frameworks=compliance_frameworks
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail={"error": "Not Found", "detail": "Certified provider not found or update failed", "code": 404}
            )
        
        return CertifiedProvider(
            id=UUID(result["id"]),
            provider_name=result["provider_name"],
            certification_number=result["certification_number"],
            valid_until=result["valid_until"],
            services_offered=result.get("services_offered", []),
            compliance_frameworks=result.get("compliance_frameworks", [])
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating certified provider: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": 500}
        )


@router.delete(
    "/{provider_id}",
    status_code=204,
    summary="Delete certified provider",
    description="Remove a certified provider from registry (admin only)"
)
async def delete_certified_provider(
    provider_id: UUID,
    current_user: dict = Depends(get_current_user)
):
    """Delete certified provider entry."""
    try:
        user_id = current_user["id"]
        user_role = current_user["role"]
        
        if user_role != "admin":
            raise HTTPException(
                status_code=403,
                detail={"error": "Forbidden", "detail": "Only admins can delete certified providers", "code": 403}
            )
        
        result = chamber_desc_certified_providers_service.delete(
            user_id=UUID(user_id),
            provider_id=provider_id
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail={"error": "Not Found", "detail": "Certified provider not found", "code": 404}
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting certified provider: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": 500}
        )


@router.post(
    "/verify",
    response_model=CertifiedProviderVerifyResponse,
    summary="Verify vendor certification",
    description="Check if a vendor has DESC certification"
)
async def verify_vendor_certification(
    request: CertifiedProviderVerifyRequest,
    current_user: dict = Depends(get_current_user)
):
    """Verify if a vendor is DESC certified."""
    try:
        user_id = current_user["id"]
        
        result = chamber_desc_certified_providers_service.verify_vendor(
            user_id=UUID(user_id),
            vendor_id=request.vendor_id
        )
        
        if not result:
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal Server Error", "detail": "Verification failed", "code": 500}
            )
        
        return CertifiedProviderVerifyResponse(
            vendor_id=request.vendor_id,
            is_certified=result["is_certified"],
            certification_details=result.get("certification_details")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying vendor certification: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal Server Error", "detail": "An unexpected error occurred", "code": 500}
        )

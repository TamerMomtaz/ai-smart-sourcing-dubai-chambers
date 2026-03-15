from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from auth import get_current_user
from models.auth import UserInfo
from models.business_council import BusinessCouncil
from models.common import ErrorResponse, PaginationResponse
from services import chamber_business_council_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chamber-business-councils",
    tags=["Chamber Business Councils"],
)


@router.post(
    "",
    response_model=BusinessCouncil,
    status_code=201,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - admin only"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_business_council(
    name: str = Query(..., max_length=255, description="Council name"),
    country: str = Query(..., max_length=100, description="Country focus"),
    description: Optional[str] = Query(None, description="Council description"),
    representative_office_locations: Optional[str] = Query(
        None, description="JSON string of office locations"
    ),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Create a new business council (admin only).
    
    Requires admin role. Creates a chamber business council with country focus
    and optional representative office locations.
    """
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail={"error": "Forbidden", "detail": "Admin role required", "code": 403},
            )

        import json
        locations = None
        if representative_office_locations:
            try:
                locations = json.loads(representative_office_locations)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Invalid JSON",
                        "detail": "representative_office_locations must be valid JSON",
                        "code": 400,
                    },
                )

        result = chamber_business_council_service.create(
            name=name,
            country=country,
            description=description,
            representative_office_locations=locations,
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Creation failed",
                    "detail": "Failed to create business council",
                    "code": 500,
                },
            )

        return BusinessCouncil(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating business council: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred",
                "code": 500,
            },
        )


@router.get(
    "",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_business_councils(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    country: Optional[str] = Query(None, description="Filter by country"),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    List all chamber business councils with pagination.
    
    Returns councils with optional country filtering.
    All authenticated users can view councils.
    """
    try:
        from database import supabase

        offset = (page - 1) * page_size

        query = supabase.table("chamber_business_councils").select(
            "id, name, country, description, representative_office_locations",
            count="exact",
        )

        if country:
            query = query.eq("country", country.strip())

        result = query.order("name").range(offset, offset + page_size - 1).execute()

        if not result:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Query failed",
                    "detail": "Failed to retrieve business councils",
                    "code": 500,
                },
            )

        total = result.count or 0
        councils = result.data or []

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "councils": [BusinessCouncil(**council) for council in councils],
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
        logger.error(f"Error listing business councils: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred",
                "code": 500,
            },
        )


@router.get(
    "/{council_id}",
    response_model=BusinessCouncil,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Council not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_business_council_by_id(
    council_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Get a specific business council by ID.
    
    Returns full council details including representative office locations.
    All authenticated users can view council details.
    """
    try:
        from database import supabase

        result = (
            supabase.table("chamber_business_councils")
            .select("id, name, country, description, representative_office_locations")
            .eq("id", str(council_id))
            .single()
            .execute()
        )

        if not result or not result.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not found",
                    "detail": "Business council not found",
                    "code": 404,
                },
            )

        return BusinessCouncil(**result.data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving business council {council_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred",
                "code": 500,
            },
        )


@router.put(
    "/{council_id}",
    response_model=BusinessCouncil,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - admin only"},
        404: {"model": ErrorResponse, "description": "Council not found"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def update_business_council(
    council_id: UUID,
    name: Optional[str] = Query(None, max_length=255, description="Council name"),
    country: Optional[str] = Query(None, max_length=100, description="Country focus"),
    description: Optional[str] = Query(None, description="Council description"),
    representative_office_locations: Optional[str] = Query(
        None, description="JSON string of office locations"
    ),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Update an existing business council (admin only).
    
    Only provided fields will be updated. Requires admin role.
    """
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail={"error": "Forbidden", "detail": "Admin role required", "code": 403},
            )

        from database import supabase
        import json

        existing = (
            supabase.table("chamber_business_councils")
            .select("id")
            .eq("id", str(council_id))
            .single()
            .execute()
        )

        if not existing or not existing.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not found",
                    "detail": "Business council not found",
                    "code": 404,
                },
            )

        update_data = {}
        if name is not None:
            update_data["name"] = name.strip()
        if country is not None:
            update_data["country"] = country.strip()
        if description is not None:
            update_data["description"] = description.strip()
        if representative_office_locations is not None:
            try:
                locations = json.loads(representative_office_locations)
                update_data["representative_office_locations"] = locations
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "Invalid JSON",
                        "detail": "representative_office_locations must be valid JSON",
                        "code": 400,
                    },
                )

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "No data provided",
                    "detail": "At least one field must be provided for update",
                    "code": 400,
                },
            )

        result = (
            supabase.table("chamber_business_councils")
            .update(update_data)
            .eq("id", str(council_id))
            .execute()
        )

        if not result or not result.data:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Update failed",
                    "detail": "Failed to update business council",
                    "code": 500,
                },
            )

        return BusinessCouncil(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating business council {council_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred",
                "code": 500,
            },
        )


@router.delete(
    "/{council_id}",
    status_code=204,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - admin only"},
        404: {"model": ErrorResponse, "description": "Council not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_business_council(
    council_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Delete a business council (admin only).
    
    Permanently removes the council. This operation cannot be undone.
    Requires admin role.
    """
    try:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail={"error": "Forbidden", "detail": "Admin role required", "code": 403},
            )

        from database import supabase

        existing = (
            supabase.table("chamber_business_councils")
            .select("id")
            .eq("id", str(council_id))
            .single()
            .execute()
        )

        if not existing or not existing.data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not found",
                    "detail": "Business council not found",
                    "code": 404,
                },
            )

        result = (
            supabase.table("chamber_business_councils")
            .delete()
            .eq("id", str(council_id))
            .execute()
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Deletion failed",
                    "detail": "Failed to delete business council",
                    "code": 500,
                },
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting business council {council_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred",
                "code": 500,
            },
        )

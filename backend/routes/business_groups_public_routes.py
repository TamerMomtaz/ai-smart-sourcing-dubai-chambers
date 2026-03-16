"""Public endpoint for business groups (no auth required for dropdown population)."""

from fastapi import APIRouter, HTTPException, status
import logging

from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/business-groups", tags=["Business Groups Public"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Business groups retrieved"},
        500: {"description": "Internal server error"},
    },
)
async def list_business_groups_public():
    """List all business groups (public, no auth required for dropdown)."""
    try:
        result = (
            supabase.table("chamber_business_groups")
            .select("id, name, chamber, description")
            .order("name")
            .execute()
        )
        return {"business_groups": result.data or []}
    except Exception as e:
        logger.error(f"Error listing business groups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "Failed to retrieve business groups",
                "code": 500,
            },
        )

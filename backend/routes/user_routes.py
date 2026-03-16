from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, Optional
from uuid import UUID
import logging

from auth import get_current_user
from models.common import ErrorResponse
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="List users",
)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> dict:
    """
    List users with pagination.
    Admin/analyst/executive roles see all users.
    Other roles get empty list.
    """
    try:
        user_role = current_user.get("role", "")

        # Only privileged roles can list users
        if user_role not in ["admin", "analyst", "executive", "compliance_officer", "business_group_lead"]:
            return {
                "users": [],
                "pagination": {
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                },
            }

        offset = (page - 1) * page_size

        query = supabase.table("chamber_users").select(
            "id, email, role, full_name, chamber, business_group_id, last_login",
            count="exact",
        )

        if role:
            query = query.eq("role", role.strip())

        response = (
            query.order("full_name")
            .range(offset, offset + page_size - 1)
            .execute()
        )

        users = response.data if response.data else []
        total = response.count if hasattr(response, "count") and response.count else len(users)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "users": users,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        }

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to list users",
                "code": "INTERNAL_ERROR",
            },
        )

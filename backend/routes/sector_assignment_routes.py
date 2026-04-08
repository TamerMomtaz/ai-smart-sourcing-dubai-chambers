"""Routes for Sector-to-Analyst Assignment management."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import logging

from auth import get_current_user
from services import sector_assignment_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sector-assignments", tags=["Sector Assignments"])


class SectorAssignmentUpsert(BaseModel):
    sector: str = Field(..., min_length=1)
    assigned_user_id: str = Field(..., min_length=1)


@router.get("")
async def list_sector_assignments(
    current_user: dict = Depends(get_current_user),
):
    """List all sector-to-analyst assignments (admin only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin can manage sector assignments",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    assignments = sector_assignment_service.list_sector_assignments()
    return {"sector_assignments": assignments}


@router.put("")
async def upsert_sector_assignment(
    payload: SectorAssignmentUpsert,
    current_user: dict = Depends(get_current_user),
):
    """Create or update a sector-to-analyst assignment (admin only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin can manage sector assignments",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = sector_assignment_service.upsert_sector_assignment(
        sector=payload.sector.strip(),
        assigned_user_id=payload.assigned_user_id.strip(),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "detail": "Failed to save sector assignment",
                "code": "UPSERT_FAILED",
            },
        )

    return result


@router.delete("/{assignment_id}")
async def delete_sector_assignment(
    assignment_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a sector assignment (admin only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin can manage sector assignments",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = sector_assignment_service.delete_sector_assignment(
        assignment_id=assignment_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Sector assignment not found",
                "code": "ASSIGNMENT_NOT_FOUND",
            },
        )

    return {"deleted": True}

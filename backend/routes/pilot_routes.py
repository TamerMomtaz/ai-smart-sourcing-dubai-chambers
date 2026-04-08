"""Routes for Pilot Tracker."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from auth import get_current_user
from services import pilot_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pilots", tags=["Pilots"])


class PilotCreate(BaseModel):
    proposal_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=500)
    vendor_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    success_criteria: Optional[str] = None
    budget_allocated: Optional[float] = None


class PilotUpdate(BaseModel):
    status: Optional[str] = Field(
        default=None,
        pattern="^(setup|active|completed|cancelled|extended)$",
    )
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    success_criteria: Optional[str] = None
    budget_allocated: Optional[float] = None
    budget_spent: Optional[float] = None
    outcome_rating: Optional[int] = Field(default=None, ge=1, le=5)
    outcome_summary: Optional[str] = None
    lessons_learned: Optional[str] = None
    adoption_decision: Optional[str] = Field(
        default=None,
        pattern="^(adopt|extend|pivot|terminate|pending)$",
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_pilot(
    payload: PilotCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new pilot from a shortlisted proposal (admin/analyst only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin and analyst roles can create pilots",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = pilot_service.create_pilot(
        proposal_id=payload.proposal_id.strip(),
        title=payload.title.strip(),
        vendor_id=payload.vendor_id.strip() if payload.vendor_id else None,
        start_date=payload.start_date,
        end_date=payload.end_date,
        success_criteria=payload.success_criteria.strip() if payload.success_criteria else None,
        budget_allocated=payload.budget_allocated,
        created_by=str(current_user["id"]),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "detail": "Failed to create pilot",
                "code": "CREATE_FAILED",
            },
        )

    return result


@router.get("")
async def list_pilots(
    status_filter: Optional[str] = Query(None, alias="status"),
    vendor_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """List all pilots with filters."""
    pilots = pilot_service.list_pilots(
        status_filter=status_filter,
        vendor_id_filter=vendor_id,
    )
    return {"pilots": pilots}


@router.get("/{pilot_id}")
async def get_pilot(
    pilot_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get full pilot detail with linked proposal and vendor info."""
    result = pilot_service.get_pilot(pilot_id=str(pilot_id))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Pilot not found",
                "code": "PILOT_NOT_FOUND",
            },
        )
    return result


@router.put("/{pilot_id}")
async def update_pilot(
    pilot_id: UUID,
    payload: PilotUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update pilot details (admin/analyst only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin and analyst roles can update pilots",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = pilot_service.update_pilot(
        pilot_id=str(pilot_id),
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        success_criteria=payload.success_criteria,
        budget_allocated=payload.budget_allocated,
        budget_spent=payload.budget_spent,
        outcome_rating=payload.outcome_rating,
        outcome_summary=payload.outcome_summary,
        lessons_learned=payload.lessons_learned,
        adoption_decision=payload.adoption_decision,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Pilot not found",
                "code": "PILOT_NOT_FOUND",
            },
        )

    return result

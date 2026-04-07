"""Routes for Sourcing Case Engine."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from auth import get_current_user
from services import sourcing_case_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sourcing-cases", tags=["Sourcing Cases"])


class SourcingCaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    problem_statement: str = Field(..., min_length=1)
    requesting_entity: Optional[str] = None
    business_group_id: Optional[str] = None
    sector: Optional[str] = None
    technology_domain: Optional[str] = None
    urgency: Optional[str] = Field(default="medium")
    compliance_requirements: Optional[str] = None
    assigned_analyst_id: Optional[str] = None


class SourcingCaseStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|matching|evaluating|shortlisted|pilot|completed|closed)$")


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_sourcing_case(
    payload: SourcingCaseCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new sourcing case (admin/analyst only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin and analyst roles can create sourcing cases",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = sourcing_case_service.create_sourcing_case(
        title=payload.title.strip(),
        problem_statement=payload.problem_statement.strip(),
        requesting_entity=payload.requesting_entity.strip() if payload.requesting_entity else None,
        business_group_id=payload.business_group_id,
        sector=payload.sector.strip() if payload.sector else None,
        technology_domain=payload.technology_domain.strip() if payload.technology_domain else None,
        urgency=payload.urgency or "medium",
        compliance_requirements=payload.compliance_requirements.strip() if payload.compliance_requirements else None,
        assigned_analyst_id=payload.assigned_analyst_id,
        created_by=str(current_user["id"]),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "detail": "Failed to create sourcing case",
                "code": "CREATE_FAILED",
            },
        )

    return result


@router.get("")
async def list_sourcing_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    sector: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    current_user: dict = Depends(get_current_user),
):
    """List all sourcing cases with filters."""
    cases = sourcing_case_service.list_sourcing_cases(
        status_filter=status_filter,
        sector_filter=sector,
        urgency_filter=urgency,
        sort_by=sort_by or "created_at",
    )
    return {"sourcing_cases": cases}


@router.get("/{case_id}")
async def get_sourcing_case(
    case_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get full sourcing case detail including linked proposals."""
    result = sourcing_case_service.get_sourcing_case(case_id=str(case_id))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Sourcing case not found",
                "code": "CASE_NOT_FOUND",
            },
        )
    return result


@router.put("/{case_id}/status")
async def update_sourcing_case_status(
    case_id: UUID,
    payload: SourcingCaseStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update sourcing case status (admin/analyst only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin and analyst roles can update sourcing case status",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = sourcing_case_service.update_sourcing_case_status(
        case_id=str(case_id),
        new_status=payload.status,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Sourcing case not found",
                "code": "CASE_NOT_FOUND",
            },
        )
    return result

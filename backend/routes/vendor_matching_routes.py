"""Routes for AI-powered vendor matching on sourcing cases."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from auth import get_current_user
from services import vendor_matching_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sourcing-cases", tags=["Vendor Matching"])


@router.post(
    "/{case_id}/discover-vendors",
    status_code=status.HTTP_200_OK,
)
async def discover_vendors(
    case_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Run AI-powered vendor discovery for a sourcing case (admin/analyst only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin and analyst roles can discover vendors",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = await vendor_matching_service.discover_vendors(
        case_id=str(case_id),
        user_id=str(current_user["id"]),
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Sourcing case not found",
                "code": "CASE_NOT_FOUND",
            },
        )

    return {"matched_vendors": result, "count": len(result)}


@router.get(
    "/{case_id}/matched-vendors",
    status_code=status.HTTP_200_OK,
)
async def get_matched_vendors(
    case_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Return cached AI-discovered vendor matches for a sourcing case."""
    result = vendor_matching_service.get_matched_vendors(
        case_id=str(case_id),
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Sourcing case not found",
                "code": "CASE_NOT_FOUND",
            },
        )

    matches = result["matches"]
    return {
        "matched_vendors": matches,
        "count": len(matches),
        "compliance_tier": result.get("compliance_tier", "standard"),
    }


class MatchStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(suggested|invited|submitted|declined)$")


@router.put(
    "/vendor-matches/{match_id}/status",
    status_code=status.HTTP_200_OK,
)
async def update_match_status(
    match_id: UUID,
    payload: MatchStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update vendor match status (e.g. invite a vendor)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin and analyst roles can update vendor match status",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = vendor_matching_service.update_match_status(
        match_id=str(match_id),
        new_status=payload.status,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Vendor match not found",
                "code": "MATCH_NOT_FOUND",
            },
        )

    return result

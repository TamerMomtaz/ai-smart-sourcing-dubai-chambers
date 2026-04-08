"""Routes for Sourcing Case deduplication detection and merge."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from auth import get_current_user
from services import case_deduplication_service
from services import sourcing_case_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sourcing-cases", tags=["Sourcing Case Deduplication"])


class DuplicateCheckRequest(BaseModel):
    title: str = Field(..., min_length=1)
    problem_statement: str = Field(..., min_length=1)
    sector: Optional[str] = None
    technology_domain: Optional[str] = None


@router.post(
    "/check-duplicate",
    status_code=status.HTTP_200_OK,
)
async def check_duplicate(
    payload: DuplicateCheckRequest,
    current_user: dict = Depends(get_current_user),
):
    """Check if a new sourcing case is a potential duplicate of existing ones."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin and analyst roles can check for duplicates",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = await case_deduplication_service.check_duplicates(
        title=payload.title.strip(),
        problem_statement=payload.problem_statement.strip(),
        sector=payload.sector.strip() if payload.sector else None,
        technology_domain=payload.technology_domain.strip() if payload.technology_domain else None,
        user_id=str(current_user["id"]),
    )

    return result


@router.post(
    "/{source_id}/merge/{target_id}",
    status_code=status.HTTP_200_OK,
)
async def merge_cases(
    source_id: UUID,
    target_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Merge source sourcing case into target (admin only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin can merge sourcing cases",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    if str(source_id) == str(target_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "BadRequest",
                "detail": "Cannot merge a case with itself",
                "code": "SELF_MERGE",
            },
        )

    result = sourcing_case_service.merge_sourcing_cases(
        source_id=str(source_id),
        target_id=str(target_id),
        merged_by=str(current_user["id"]),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "One or both sourcing cases not found",
                "code": "CASE_NOT_FOUND",
            },
        )

    return result


@router.post(
    "/scan-duplicates",
    status_code=status.HTTP_200_OK,
)
async def scan_all_duplicates(
    current_user: dict = Depends(get_current_user),
):
    """Scan all open sourcing cases for potential overlaps (admin only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin can scan all cases for duplicates",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = await case_deduplication_service.scan_all_open_cases(
        user_id=str(current_user["id"]),
    )

    return result

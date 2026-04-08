"""Routes for Vendor Factsheet generation and retrieval."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict
from uuid import UUID
import logging

from auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


class FactsheetRequest(BaseModel):
    sourcing_case_id: Optional[str] = None


@router.post("/vendors/{vendor_id}/factsheet")
async def generate_factsheet(
    vendor_id: UUID,
    body: FactsheetRequest = FactsheetRequest(),
    current_user: Dict = Depends(get_current_user),
):
    """Generate a structured factsheet for a vendor. Admin/analyst only."""
    role = current_user.get("role")
    if role not in ("admin", "analyst"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or analyst can generate factsheets",
        )

    from services.factsheet_service import generate_factsheet as gen_fs

    try:
        result = await gen_fs(
            vendor_id=str(vendor_id),
            sourcing_case_id=body.sourcing_case_id,
            generated_by=current_user.get("id"),
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as exc:
        logger.error("Factsheet generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Factsheet generation failed",
        )


@router.get("/vendors/{vendor_id}/factsheet")
async def get_factsheet(
    vendor_id: UUID,
    sourcing_case_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user),
):
    """Return the most recently generated factsheet for a vendor."""
    from services.factsheet_service import get_latest_factsheet

    result = get_latest_factsheet(
        vendor_id=str(vendor_id),
        sourcing_case_id=sourcing_case_id,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No factsheet found for this vendor",
        )
    return result

"""Routes for the Pre-Evaluation Compliance Gate."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import supabase
from services.compliance_gate_service import run_compliance_gate

router = APIRouter(prefix="/proposals", tags=["Compliance Gate"])


@router.post(
    "/{proposal_id}/compliance-gate",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Compliance gate checks completed"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden — admin or analyst role required"},
        404: {"description": "Proposal not found"},
        500: {"description": "Internal server error"},
    },
)
async def run_proposal_compliance_gate(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Run pre-evaluation compliance gate checks on a proposal.

    This is Layer 1: deterministic, rule-based checks that run BEFORE AI evaluation.
    No AI tokens are consumed. Allowed roles: admin, analyst.
    """
    if current_user["role"] not in ("admin", "analyst"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Admin or analyst role required to run compliance gate",
                "code": 403,
            },
        )

    result = run_compliance_gate(proposal_id=str(proposal_id))

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Proposal not found",
                "code": 404,
            },
        )

    return result

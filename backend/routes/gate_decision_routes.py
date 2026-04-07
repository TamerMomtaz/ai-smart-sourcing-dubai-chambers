from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from datetime import datetime, timezone
import logging

from auth import get_current_user
from services import gate_decision_service
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["Gate Decisions"])


@router.post(
    "/{proposal_id}/gate-decision",
    status_code=status.HTTP_201_CREATED,
)
async def create_gate_decision(
    proposal_id: UUID,
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """
    Record a stage-gate decision for a proposal (admin/analyst only).
    AI recommends, human decides at every gate.
    """
    try:
        user_role = current_user.get("role", "").strip()
        user_id = current_user["id"]

        if user_role not in ("admin", "analyst"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Only admin and analyst roles can record gate decisions",
                    "code": "INSUFFICIENT_PERMISSIONS",
                },
            )

        gate_name = payload.get("gate_name", "").strip()
        decision = payload.get("decision", "").strip()
        decision_reason = payload.get("decision_reason", "").strip() if payload.get("decision_reason") else None
        conditions = payload.get("conditions", "").strip() if payload.get("conditions") else None

        valid_gates = ("discovery", "scoping", "evaluation", "pilot_approval", "procurement")
        valid_decisions = ("go", "kill", "hold", "recycle", "conditional_go")

        if gate_name not in valid_gates:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "ValidationError",
                    "detail": f"Invalid gate_name. Must be one of: {', '.join(valid_gates)}",
                    "code": "INVALID_GATE_NAME",
                },
            )

        if decision not in valid_decisions:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "ValidationError",
                    "detail": f"Invalid decision. Must be one of: {', '.join(valid_decisions)}",
                    "code": "INVALID_DECISION",
                },
            )

        if not decision_reason:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "ValidationError",
                    "detail": "decision_reason is required",
                    "code": "MISSING_DECISION_REASON",
                },
            )

        if decision == "conditional_go" and not conditions:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "ValidationError",
                    "detail": "conditions is required for conditional_go decisions",
                    "code": "MISSING_CONDITIONS",
                },
            )

        result = gate_decision_service.create_gate_decision(
            proposal_id=proposal_id,
            gate_name=gate_name,
            decision=decision,
            decided_by=UUID(user_id),
            decision_reason=decision_reason,
            conditions=conditions,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "NotFound",
                    "detail": "Proposal not found",
                    "code": "PROPOSAL_NOT_FOUND",
                },
            )

        # Log to chamber_ai_interactions as a gate decision event
        try:
            supabase.table("chamber_ai_interactions").insert({
                "user_id": user_id,
                "session_id": user_id,
                "model_name": "human_committee",
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "latency_ms": 0,
                "cost_usd": 0,
                "energy_kwh": 0,
                "carbon_gco2": 0,
                "intelligence_units": 0,
                "operation_type": "evaluation",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }).execute()
        except Exception as log_err:
            logger.warning(f"Failed to log gate decision AI interaction: {log_err}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating gate decision: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_ERROR",
            },
        )


@router.get(
    "/{proposal_id}/gate-history",
    status_code=status.HTTP_200_OK,
)
async def get_gate_history(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Get all gate decisions for a proposal in chronological order.
    Any authenticated user can view gate history.
    """
    try:
        history = gate_decision_service.get_gate_history(proposal_id=proposal_id)
        return {"gate_decisions": history}

    except Exception as e:
        logger.error(f"Error fetching gate history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_ERROR",
            },
        )

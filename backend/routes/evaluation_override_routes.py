from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, timezone
import logging

from auth import get_current_user
from services import evaluation_override_service, ai_interaction_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluations", tags=["Evaluation Overrides"])

ALLOWED_ROLES = {"admin", "analyst"}


class OverrideRequest(BaseModel):
    dimension: str = Field(
        ...,
        description="Dimension to override: relevance, feasibility, compliance, sector_alignment, or composite",
    )
    human_adjusted_score: float = Field(
        ..., ge=0, le=100, description="Adjusted score (0-100)"
    )
    override_reason: str = Field(
        ..., min_length=1, description="Reason for the adjustment"
    )


@router.post(
    "/{evaluation_id}/override",
    summary="Override an AI evaluation score",
    description="Analysts and admins can adjust AI scores with documented reasoning.",
)
async def create_override(
    evaluation_id: UUID,
    body: OverrideRequest,
    current_user: dict = Depends(get_current_user),
):
    user_role = current_user.get("role")
    if user_role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_role",
                "detail": "Only admin or analyst can override evaluation scores",
                "code": 403,
            },
        )

    if body.dimension not in evaluation_override_service.VALID_DIMENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "invalid_dimension",
                "detail": f"Dimension must be one of: {', '.join(sorted(evaluation_override_service.VALID_DIMENSIONS))}",
                "code": 400,
            },
        )

    try:
        updated_evaluation = evaluation_override_service.create_override(
            evaluation_id=evaluation_id,
            dimension=body.dimension,
            human_adjusted_score=body.human_adjusted_score,
            override_reason=body.override_reason,
            overridden_by=current_user.get("id"),
        )

        if not updated_evaluation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "not_found",
                    "detail": f"Evaluation {evaluation_id} not found",
                    "code": 404,
                },
            )

        # Log to chamber_ai_interactions as human_override
        try:
            import uuid

            ai_interaction_service.create(
                user_id=current_user.get("id"),
                session_id=uuid.uuid4(),
                model_name="human_override",
                prompt_tokens=0,
                completion_tokens=0,
                latency_ms=0,
                cost_usd=0.0,
                energy_kwh=0.0,
                carbon_gco2=0.0,
                intelligence_units=0.0,
                operation_type="human_override",
                evaluation_id=evaluation_id,
            )
        except Exception as log_err:
            logger.warning(f"Failed to log human_override AI interaction: {log_err}")

        return updated_evaluation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating override for evaluation {evaluation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "detail": "Failed to create override",
                "code": 500,
            },
        )


@router.get(
    "/{evaluation_id}/overrides",
    summary="Get override history for an evaluation",
    description="Returns all human overrides for an evaluation, newest first.",
)
async def get_overrides(
    evaluation_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    try:
        overrides = evaluation_override_service.list_overrides(
            evaluation_id=evaluation_id,
        )
        return {"overrides": overrides}
    except Exception as e:
        logger.error(f"Error fetching overrides for evaluation {evaluation_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "internal_error",
                "detail": "Failed to fetch overrides",
                "code": 500,
            },
        )

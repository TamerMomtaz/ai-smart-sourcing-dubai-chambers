from fastapi import APIRouter, Depends, HTTPException
from auth import get_current_user
from services.ai_interaction_service import get_model_inventory
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["AI Model Inventory"],
)


@router.get(
    "/model-inventory",
    summary="AI Model Inventory",
    description="Returns aggregated per-model stats from chamber_ai_interactions: "
    "total_calls, total_cost, total_tokens, avg_latency, last_used, first_used.",
    responses={
        200: {"description": "Model inventory retrieved successfully"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - admin or compliance_officer role required"},
        500: {"description": "Internal server error"},
    },
)
async def get_model_inventory_endpoint(
    current_user=Depends(get_current_user),
):
    allowed_roles = ["admin", "compliance_officer"]
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Forbidden",
                "detail": "Admin or compliance officer role required",
                "code": 403,
            },
        )

    try:
        inventory = get_model_inventory()
        return {"models": inventory}
    except Exception as e:
        logger.error(f"Model inventory retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to retrieve model inventory",
                "code": 500,
            },
        )

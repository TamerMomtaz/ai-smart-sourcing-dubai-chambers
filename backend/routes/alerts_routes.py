from uuid import UUID
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from auth import get_current_user
from services.chamber_alerts_service import list_unresolved_alerts, resolve_alert
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
async def get_alerts(
    current_user: dict = Depends(get_current_user),
):
    """Get unresolved alerts. Admin and compliance_officer roles only."""
    try:
        user_role = current_user.get("role", "").strip()
        allowed_roles = ["admin", "compliance_officer"]

        if user_role not in allowed_roles:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "detail": "Only admin and compliance officers can view alerts",
                    "code": "ROLE_ADMIN_OR_COMPLIANCE_REQUIRED",
                },
            )

        alerts = list_unresolved_alerts()
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "Failed to retrieve alerts",
                "code": "INTERNAL_ERROR",
            },
        )


@router.put(
    "/{alert_id}/resolve",
    status_code=status.HTTP_200_OK,
)
async def resolve_alert_endpoint(
    alert_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Mark an alert as resolved. Admin and compliance_officer roles only."""
    try:
        user_role = current_user.get("role", "").strip()
        allowed_roles = ["admin", "compliance_officer"]

        if user_role not in allowed_roles:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "detail": "Only admin and compliance officers can resolve alerts",
                    "code": "ROLE_ADMIN_OR_COMPLIANCE_REQUIRED",
                },
            )

        result = resolve_alert(alert_id=alert_id)
        if not result:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "detail": f"Alert {alert_id} not found",
                    "code": "ALERT_NOT_FOUND",
                },
            )

        return result
    except Exception as e:
        logger.error(f"Error resolving alert {alert_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "Failed to resolve alert",
                "code": "INTERNAL_ERROR",
            },
        )

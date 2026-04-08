from uuid import UUID
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from typing import List

from models.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
    IncidentSummary,
)
from models.common import ErrorResponse
from auth import get_current_user
from services.incident_service import (
    list_incidents,
    create_incident,
    update_incident,
    get_incident_summary,
)
from services.chamber_alerts_service import create_alert
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/incidents",
    tags=["incidents"],
)


@router.get(
    "/summary",
    response_model=IncidentSummary,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def incidents_summary(
    current_user: dict = Depends(get_current_user),
):
    """Get incident summary counts."""
    try:
        summary = get_incident_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting incident summary: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "Failed to retrieve incident summary",
                "code": "INTERNAL_ERROR",
            },
        )


@router.get(
    "",
    response_model=List[IncidentResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_incidents(
    current_user: dict = Depends(get_current_user),
):
    """Get all incidents ordered by created_at DESC."""
    try:
        incidents = list_incidents()
        return incidents
    except Exception as e:
        logger.error(f"Error listing incidents: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "Failed to retrieve incidents",
                "code": "INTERNAL_ERROR",
            },
        )


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - admin or compliance role required"},
    },
)
async def create_new_incident(
    request: IncidentCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new incident. Admin and compliance_officer roles only."""
    try:
        user_role = current_user.get("role", "").strip()
        allowed_roles = ["admin", "compliance_officer"]

        if user_role not in allowed_roles:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "detail": "Only admin and compliance officers can create incidents",
                    "code": "ROLE_ADMIN_OR_COMPLIANCE_REQUIRED",
                },
            )

        incident = create_incident(
            title=request.title,
            description=request.description,
            severity=request.severity,
            incident_type=request.incident_type,
            affected_systems=request.affected_systems,
            reported_by=UUID(current_user["id"]),
            desc_report_required=request.desc_report_required or False,
        )

        if not incident:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "detail": "Failed to create incident",
                    "code": "INCIDENT_CREATION_FAILED",
                },
            )

        # Generate compliance alert for high-severity incidents
        if request.severity in ("high", "critical"):
            create_alert(
                alert_type="compliance",
                severity="high",
                title="High-severity incident reported",
                description=f"Incident \"{request.title}\" created with severity={request.severity}, type={request.incident_type}.",
            )

        return incident
    except Exception as e:
        logger.error(f"Error creating incident: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while creating the incident",
                "code": "INTERNAL_ERROR",
            },
        )


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - admin or compliance role required"},
        404: {"model": ErrorResponse, "description": "Incident not found"},
    },
)
async def update_existing_incident(
    incident_id: UUID,
    request: IncidentUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an incident's status, resolution, or details."""
    try:
        user_role = current_user.get("role", "").strip()
        allowed_roles = ["admin", "compliance_officer"]

        if user_role not in allowed_roles:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "detail": "Only admin and compliance officers can update incidents",
                    "code": "ROLE_ADMIN_OR_COMPLIANCE_REQUIRED",
                },
            )

        updates = request.model_dump(exclude_unset=True)
        if not updates:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Bad Request",
                    "detail": "No fields to update",
                    "code": "NO_UPDATE_FIELDS",
                },
            )

        # Convert UUID fields to strings for Supabase
        if "assigned_to" in updates and updates["assigned_to"] is not None:
            updates["assigned_to"] = str(updates["assigned_to"])

        incident = update_incident(
            incident_id=incident_id,
            updates=updates,
        )

        if not incident:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "detail": f"Incident {incident_id} not found",
                    "code": "INCIDENT_NOT_FOUND",
                },
            )

        return incident
    except Exception as e:
        logger.error(f"Error updating incident {incident_id}: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while updating the incident",
                "code": "INTERNAL_ERROR",
            },
        )

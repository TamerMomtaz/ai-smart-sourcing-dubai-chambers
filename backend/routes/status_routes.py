from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
import logging

from auth import get_current_user
from models.auth import UserInfo
from models.proposal import ProposalStatusUpdate, ProposalStatusUpdateResponse
from models.batch import BatchJobStatus
from models.common import ErrorResponse
from services import status_service
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["status"]
)


@router.patch(
    "/proposals/{proposal_id}/status",
    response_model=ProposalStatusUpdateResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - only analysts and executives can update status"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        422: {"model": ErrorResponse, "description": "Invalid status transition"},
    },
)
async def update_proposal_status(
    proposal_id: UUID,
    body: ProposalStatusUpdate,
    current_user: UserInfo = Depends(get_current_user)
) -> ProposalStatusUpdateResponse:
    """
    Update proposal status (analyst/executive only).
    
    Allowed status transitions:
    - under_review: Proposal moved to manual review queue
    - approved: Proposal approved for procurement pipeline
    - rejected: Proposal rejected with reason
    - requires_manual_review: Flag for manual review required
    
    Args:
        proposal_id: Proposal UUID
        body: Status update request with status and optional reason
        current_user: Authenticated user from JWT
        
    Returns:
        Updated proposal status response
        
    Raises:
        HTTPException: 403 if user role not analyst/executive
        HTTPException: 404 if proposal not found
        HTTPException: 422 if invalid status transition
    """
    try:
        # Verify user has analyst or executive role
        if current_user.role not in ["analyst", "executive"]:
            logger.warning(
                f"User {current_user.id} with role {current_user.role} attempted status update on proposal {proposal_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Only analysts and executives can update proposal status",
                    "code": "INSUFFICIENT_PERMISSIONS"
                }
            )
        
        # Validate status value
        allowed_statuses = ["under_review", "approved", "rejected", "requires_manual_review"]
        if body.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Invalid Status",
                    "detail": f"Status must be one of: {', '.join(allowed_statuses)}",
                    "code": "INVALID_STATUS"
                }
            )
        
        # Call service to update status
        result = status_service.update_proposal_status(
            user_id=current_user.id,
            proposal_id=proposal_id,
            status=body.status,
            reason=body.reason
        )
        
        if not result:
            logger.error(f"Proposal {proposal_id} not found or status update failed")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not Found",
                    "detail": f"Proposal {proposal_id} not found or update failed",
                    "code": "PROPOSAL_NOT_FOUND"
                }
            )
        
        logger.info(
            f"Proposal {proposal_id} status updated to {body.status} by user {current_user.id}"
        )
        
        return ProposalStatusUpdateResponse(
            proposal_id=result["id"],
            status=result["status"],
            updated_at=result["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating proposal {proposal_id} status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to update proposal status",
                "code": "STATUS_UPDATE_FAILED"
            }
        )


@router.get(
    "/batch/{batch_job_id}/status",
    response_model=BatchJobStatus,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Batch job not found"},
    },
)
async def get_batch_job_status(
    batch_job_id: UUID,
    current_user: UserInfo = Depends(get_current_user)
) -> BatchJobStatus:
    """
    Get status of batch processing job.
    
    Returns detailed status of a batch evaluation job including:
    - Current status (queued, processing, completed, failed)
    - Total proposals in batch
    - Number of processed proposals
    - Number of failed proposals
    - Start and completion timestamps
    
    Args:
        batch_job_id: Batch job UUID
        current_user: Authenticated user from JWT
        
    Returns:
        Batch job status with processing metrics
        
    Raises:
        HTTPException: 404 if batch job not found
    """
    try:
        # Query batch job from database
        batch_response = supabase.table("chamber_batch_jobs").select(
            "id, status, total_proposals, processed_count, failed_count, started_at, completed_at, created_by"
        ).eq("id", str(batch_job_id)).maybe_single().execute()
        
        if not batch_response.data:
            logger.warning(f"Batch job {batch_job_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not Found",
                    "detail": f"Batch job {batch_job_id} not found",
                    "code": "BATCH_JOB_NOT_FOUND"
                }
            )
        
        batch_data = batch_response.data
        
        # Verify user has access to this batch job
        # Vendors can only see their own batch jobs
        if current_user.role == "vendor" and str(batch_data["created_by"]) != str(current_user.id):
            logger.warning(
                f"User {current_user.id} attempted to access batch job {batch_job_id} created by {batch_data['created_by']}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not Found",
                    "detail": f"Batch job {batch_job_id} not found",
                    "code": "BATCH_JOB_NOT_FOUND"
                }
            )
        
        logger.info(f"Batch job {batch_job_id} status retrieved by user {current_user.id}")
        
        return BatchJobStatus(
            batch_job_id=batch_data["id"],
            status=batch_data["status"],
            total_proposals=batch_data["total_proposals"],
            processed=batch_data["processed_count"] or 0,
            failed=batch_data["failed_count"] or 0,
            started_at=batch_data["started_at"],
            completed_at=batch_data.get("completed_at")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving batch job {batch_job_id} status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to retrieve batch job status",
                "code": "BATCH_STATUS_RETRIEVAL_FAILED"
            }
        )

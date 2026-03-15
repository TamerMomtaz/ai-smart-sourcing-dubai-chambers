from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
import logging
from database import supabase

logger = logging.getLogger(__name__)


async def trigger_trend_analysis_generation(
    user_id: UUID,
    sector: Optional[str],
    date_range_start: str,
    date_range_end: str,
) -> Optional[dict]:
    """
    Trigger AI trend analysis generation job.
    
    Args:
        user_id: UUID of requesting user (must be executive)
        sector: Optional sector filter
        date_range_start: Start date (ISO format)
        date_range_end: End date (ISO format)
    
    Returns:
        Dict with job_id, status, estimated_completion or None if failed
    """
    try:
        # Verify user role is executive
        user_response = supabase.table("auth_users").select("role").eq("id", str(user_id)).execute()
        if not user_response.data or len(user_response.data) == 0:
            logger.warning(f"User {user_id} not found for trend analysis generation")
            return None
        
        user_role = user_response.data[0].get("role")
        if user_role != "executive":
            logger.warning(f"User {user_id} with role {user_role} attempted trend analysis generation (executive only)")
            return None
        
        # Create background job record
        job_id = uuid4()
        now = datetime.now(timezone.utc)
        estimated_completion = datetime.now(timezone.utc).replace(hour=now.hour, minute=now.minute + 15)
        
        job_data = {
            "id": str(job_id),
            "job_type": "trend_analysis_generation",
            "status": "processing",
            "created_by": str(user_id),
            "parameters": {
                "sector": sector,
                "date_range_start": date_range_start,
                "date_range_end": date_range_end,
            },
            "created_at": now.isoformat(),
            "estimated_completion": estimated_completion.isoformat(),
        }
        
        # Insert job into background_jobs table
        job_response = supabase.table("background_jobs").insert(job_data).execute()
        if not job_response.data or len(job_response.data) == 0:
            logger.error(f"Failed to create trend analysis generation job for user {user_id}")
            return None
        
        logger.info(f"Trend analysis generation job {job_id} created by user {user_id}")
        
        return {
            "job_id": str(job_id),
            "status": "processing",
            "estimated_completion": estimated_completion.isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Error triggering trend analysis generation for user {user_id}: {str(e)}")
        return None


async def get_trend_analysis_job_status(user_id: UUID, job_id: UUID) -> Optional[dict]:
    """
    Get status of trend analysis generation job.
    
    Args:
        user_id: UUID of requesting user (ownership check)
        job_id: UUID of background job
    
    Returns:
        Dict with job status or None if not found/unauthorized
    """
    try:
        response = supabase.table("background_jobs").select("*").eq("id", str(job_id)).eq("created_by", str(user_id)).execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"Job {job_id} not found or not owned by user {user_id}")
            return None
        
        job = response.data[0]
        
        return {
            "job_id": job["id"],
            "status": job["status"],
            "created_at": job["created_at"],
            "estimated_completion": job.get("estimated_completion"),
            "completed_at": job.get("completed_at"),
            "result": job.get("result"),
            "error": job.get("error"),
        }
    
    except Exception as e:
        logger.error(f"Error fetching job status for job {job_id}, user {user_id}: {str(e)}")
        return None

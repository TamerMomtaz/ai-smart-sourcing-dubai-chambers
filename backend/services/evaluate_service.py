from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from database import supabase
import logging

logger = logging.getLogger(__name__)


def trigger_proposal_evaluation(
    user_id: UUID,
    proposal_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Trigger manual re-evaluation of a proposal.
    Analyst only operation.
    
    Args:
        user_id: UUID of the requesting user
        proposal_id: UUID of the proposal to re-evaluate
    
    Returns:
        Dict with proposal_id, status, and job_id if successful, None if not found
    """
    try:
        # Check if proposal exists
        proposal_response = supabase.table("chamber_proposals").select("id, status").eq("id", str(proposal_id)).execute()
        
        if not proposal_response.data or len(proposal_response.data) == 0:
            return None
        
        proposal = proposal_response.data[0]
        
        # Check if proposal is already being evaluated
        if proposal.get("status") in ["queued_for_evaluation", "evaluating"]:
            return {"conflict": True, "message": "Proposal is already being evaluated"}
        
        # Update proposal status to queued_for_evaluation
        update_response = supabase.table("chamber_proposals").update({
            "status": "queued_for_evaluation",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", str(proposal_id)).execute()
        
        if not update_response.data:
            logger.error(f"Failed to update proposal status for {proposal_id}")
            return None
        
        # Create evaluation job record
        job_id = UUID(supabase.rpc("uuid_generate_v4", {}).execute().data)
        
        job_response = supabase.table("evaluation_jobs").insert({
            "id": str(job_id),
            "proposal_id": str(proposal_id),
            "status": "queued",
            "triggered_by": str(user_id),
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        if not job_response.data:
            logger.error(f"Failed to create evaluation job for proposal {proposal_id}")
            return None
        
        return {
            "proposal_id": str(proposal_id),
            "status": "queued_for_evaluation",
            "job_id": str(job_id)
        }
    
    except Exception as e:
        logger.error(f"Error triggering proposal evaluation for {proposal_id}: {str(e)}")
        return None


def trigger_batch_evaluation(
    user_id: UUID,
    proposal_ids: List[UUID]
) -> Optional[Dict[str, Any]]:
    """
    Trigger batch evaluation for multiple proposals.
    Analyst only operation.
    
    Args:
        user_id: UUID of the requesting user
        proposal_ids: List of proposal UUIDs to evaluate
    
    Returns:
        Dict with batch_job_id, proposal_count, status, and estimated_completion if successful
    """
    try:
        # Validate proposal_ids limit
        if len(proposal_ids) > 100:
            return {"error": "batch_size_exceeded", "message": "Batch size exceeds limit of 100"}
        
        # Check all proposals exist
        proposal_ids_str = [str(pid) for pid in proposal_ids]
        proposals_response = supabase.table("chamber_proposals").select("id, status").in_("id", proposal_ids_str).execute()
        
        if not proposals_response.data or len(proposals_response.data) != len(proposal_ids):
            return {"error": "proposals_not_found", "message": "One or more proposals not found"}
        
        # Filter out proposals already being evaluated
        evaluating_statuses = ["queued_for_evaluation", "evaluating"]
        valid_proposals = [
            p for p in proposals_response.data 
            if p.get("status") not in evaluating_statuses
        ]
        
        if not valid_proposals:
            return {"error": "no_valid_proposals", "message": "All proposals are already being evaluated"}
        
        # Create batch job
        batch_job_id = UUID(supabase.rpc("uuid_generate_v4", {}).execute().data)
        
        batch_job_response = supabase.table("batch_evaluation_jobs").insert({
            "id": str(batch_job_id),
            "status": "queued",
            "total_proposals": len(valid_proposals),
            "processed": 0,
            "failed": 0,
            "triggered_by": str(user_id),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        if not batch_job_response.data:
            logger.error(f"Failed to create batch evaluation job")
            return None
        
        # Update proposal statuses and create individual evaluation jobs
        for proposal in valid_proposals:
            proposal_id = proposal["id"]
            
            # Update proposal status
            supabase.table("chamber_proposals").update({
                "status": "queued_for_evaluation",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", proposal_id).execute()
            
            # Create evaluation job
            job_id = UUID(supabase.rpc("uuid_generate_v4", {}).execute().data)
            
            supabase.table("evaluation_jobs").insert({
                "id": str(job_id),
                "proposal_id": proposal_id,
                "batch_job_id": str(batch_job_id),
                "status": "queued",
                "triggered_by": str(user_id),
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
        
        # Estimate completion time (5 minutes per proposal)
        estimated_minutes = len(valid_proposals) * 5
        estimated_completion = datetime.now(timezone.utc)
        from datetime import timedelta
        estimated_completion = estimated_completion + timedelta(minutes=estimated_minutes)
        
        return {
            "batch_job_id": str(batch_job_id),
            "proposal_count": len(valid_proposals),
            "status": "queued",
            "estimated_completion": estimated_completion.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error triggering batch evaluation: {str(e)}")
        return None


def get_batch_job_status(
    user_id: UUID,
    batch_job_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Get status of a batch evaluation job.
    
    Args:
        user_id: UUID of the requesting user
        batch_job_id: UUID of the batch job
    
    Returns:
        Dict with batch job status if successful, None if not found
    """
    try:
        batch_job_response = supabase.table("batch_evaluation_jobs").select(
            "id, status, total_proposals, processed, failed, started_at, completed_at"
        ).eq("id", str(batch_job_id)).execute()
        
        if not batch_job_response.data or len(batch_job_response.data) == 0:
            return None
        
        batch_job = batch_job_response.data[0]
        
        return {
            "batch_job_id": batch_job["id"],
            "status": batch_job["status"],
            "total_proposals": batch_job["total_proposals"],
            "processed": batch_job["processed"],
            "failed": batch_job["failed"],
            "started_at": batch_job["started_at"],
            "completed_at": batch_job.get("completed_at")
        }
    
    except Exception as e:
        logger.error(f"Error retrieving batch job status for {batch_job_id}: {str(e)}")
        return None


def check_user_is_analyst(user_id: UUID) -> bool:
    """
    Check if user has analyst role.
    
    Args:
        user_id: UUID of the user
    
    Returns:
        True if user is analyst, False otherwise
    """
    try:
        user_response = supabase.table("chamber_users").select("role").eq("id", str(user_id)).execute()
        
        if not user_response.data or len(user_response.data) == 0:
            return False
        
        user_role = user_response.data[0].get("role")
        return user_role in ["analyst", "admin"]
    
    except Exception as e:
        logger.error(f"Error checking user role for {user_id}: {str(e)}")
        return False

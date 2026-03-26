from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


def update_proposal_status(
    user_id: UUID,
    proposal_id: UUID,
    status: str,
    reason: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update proposal status (analyst/executive only)."""
    
    # Verify proposal exists and get current data
    result = supabase.table("chamber_proposals").select("id, status, created_by").eq("id", str(proposal_id)).maybe_single().execute()
    
    if not result.data:
        return None
    
    proposal = result.data
    
    # Validate status transition
    current_status = proposal.get("status")
    valid_transitions = {
        "submitted": ["queued_for_evaluation", "rejected"],
        "queued_for_evaluation": ["evaluating", "rejected"],
        "evaluating": ["evaluated", "failed", "rejected", "shortlisted", "under_review", "needs_improvement"],
        "evaluated": ["under_review", "approved", "rejected", "requires_manual_review", "shortlisted"],
        "shortlisted": ["approved", "rejected", "under_review"],
        "under_review": ["approved", "rejected", "requires_manual_review", "shortlisted"],
        "needs_improvement": ["under_review", "rejected", "requires_manual_review"],
        "requires_manual_review": ["under_review", "approved", "rejected", "shortlisted"],
        "approved": [],
        "rejected": []
    }
    
    allowed = valid_transitions.get(current_status, [])
    if status not in allowed and current_status != status:
        # Invalid transition - caller should handle with 422
        return {"error": "invalid_transition", "current_status": current_status, "requested_status": status}
    
    # Update proposal status
    update_data = {
        "status": status,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    update_result = supabase.table("chamber_proposals").update(update_data).eq("id", str(proposal_id)).execute()
    
    if not update_result.data:
        return None
    
    # Log status change in proposal_status_history if reason provided
    if reason:
        history_data = {
            "proposal_id": str(proposal_id),
            "status": status,
            "changed_by": str(user_id),
            "reason": reason,
            "changed_at": datetime.now(timezone.utc).isoformat()
        }
        supabase.table("chamber_proposal_status_history").insert(history_data).execute()
    
    return {
        "proposal_id": str(proposal_id),
        "status": status,
        "updated_at": update_result.data[0].get("updated_at")
    }


def get_batch_job_status(
    user_id: UUID,
    batch_job_id: UUID
) -> Optional[Dict[str, Any]]:
    """Get status of batch processing job."""
    
    # Fetch batch job
    result = supabase.table("chamber_batch_jobs").select(
        "id, status, total_proposals, processed, failed, started_at, completed_at, created_by"
    ).eq("id", str(batch_job_id)).maybe_single().execute()
    
    if not result.data:
        return None
    
    job = result.data
    
    # Verify ownership
    if job.get("created_by") != str(user_id):
        return None
    
    return {
        "batch_job_id": job.get("id"),
        "status": job.get("status"),
        "total_proposals": job.get("total_proposals", 0),
        "processed": job.get("processed", 0),
        "failed": job.get("failed", 0),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at")
    }

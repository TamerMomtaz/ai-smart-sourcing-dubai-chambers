from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from database import supabase


def submit_proposal(user_id: UUID, proposal_id: UUID) -> Optional[dict]:
    """
    Finalize proposal submission and trigger AI evaluation queue.
    Validates proposal exists, has documents, and belongs to user.
    Updates status to 'queued_for_evaluation' and sets estimated completion.
    """
    # Fetch proposal with ownership check
    proposal_response = supabase.table("chamber_proposals").select("*").eq("id", str(proposal_id)).eq("submitter_id", str(user_id)).execute()
    
    if not proposal_response.data or len(proposal_response.data) == 0:
        return None
    
    proposal = proposal_response.data[0]
    
    # Check if proposal has attached documents
    documents_response = supabase.table("chamber_documents").select("id").eq("proposal_id", str(proposal_id)).eq("is_deleted", False).execute()
    
    if not documents_response.data or len(documents_response.data) == 0:
        # Return error indicator - route handler will raise 400
        return {"error": "no_documents", "detail": "Cannot submit proposal without documents"}
    
    # Update proposal status to queued_for_evaluation
    now = datetime.now(timezone.utc)
    estimated_completion = now + timedelta(minutes=10)
    
    update_response = supabase.table("chamber_proposals").update({
        "status": "queued_for_evaluation",
        "submission_date": now.isoformat(),
        "updated_at": now.isoformat()
    }).eq("id", str(proposal_id)).eq("submitter_id", str(user_id)).execute()
    
    if not update_response.data or len(update_response.data) == 0:
        return None
    
    # Create evaluation queue entry (if chamber_evaluation_queue table exists)
    try:
        supabase.table("chamber_evaluation_queue").insert({
            "proposal_id": str(proposal_id),
            "status": "queued",
            "priority": 100,
            "created_at": now.isoformat(),
            "estimated_completion": estimated_completion.isoformat()
        }).execute()
    except Exception:
        # If queue table doesn't exist, continue anyway
        pass
    
    return {
        "proposal_id": proposal_id,
        "status": "queued_for_evaluation",
        "estimated_completion": estimated_completion
    }

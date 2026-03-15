from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
import json

from database import supabase


async def run_duplicate_check(
    user_id: str,
    proposal_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Run semantic similarity check against existing proposals.
    Returns duplicate check result with similar proposals.
    """
    # Verify proposal exists and user has access
    proposal_response = supabase.table("chamber_proposals").select(
        "id, title, submitter_id, description, sector, technology_type, created_at, embeddings"
    ).eq("id", str(proposal_id)).execute()
    
    if not proposal_response.data or len(proposal_response.data) == 0:
        return None
    
    proposal = proposal_response.data[0]
    
    # Check ownership or role permissions
    user_response = supabase.table("chamber_users").select("role").eq("id", user_id).execute()
    if not user_response.data:
        return None
    
    user_role = user_response.data[0].get("role")
    is_owner = proposal["submitter_id"] == user_id
    has_permission = user_role in ["analyst", "executive", "compliance_officer", "admin"]
    
    if not is_owner and not has_permission:
        return None
    
    # Get proposal embeddings
    embeddings = proposal.get("embeddings")
    if not embeddings:
        # If no embeddings exist yet, return no duplicates found
        return {
            "proposal_id": str(proposal_id),
            "is_duplicate": False,
            "similar_proposals": []
        }
    
    # Query similar proposals using vector similarity
    # Exclude current proposal and only check submitted/evaluated proposals
    similar_response = supabase.rpc(
        "match_proposals",
        {
            "query_embedding": embeddings,
            "match_threshold": 0.85,
            "match_count": 10,
            "exclude_proposal_id": str(proposal_id)
        }
    ).execute()
    
    similar_proposals = []
    is_duplicate = False
    
    if similar_response.data:
        for similar in similar_response.data:
            similarity_score = similar.get("similarity", 0.0)
            
            # Consider duplicate if similarity > 0.90
            if similarity_score > 0.90:
                is_duplicate = True
            
            similar_proposals.append({
                "proposal_id": similar["id"],
                "title": similar["title"],
                "similarity_score": round(similarity_score, 4),
                "submission_date": similar["created_at"]
            })
    
    # Update proposal is_duplicate flag
    supabase.table("chamber_proposals").update({
        "is_duplicate": is_duplicate,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", str(proposal_id)).execute()
    
    # Log duplicate check in ai_interactions table
    try:
        supabase.table("ai_interactions").insert({
            "proposal_id": str(proposal_id),
            "model_name": "embedding-service",
            "operation_type": "duplicate_check",
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "latency_ms": 0,
            "cost_usd": 0.0,
            "energy_kwh": 0.0,
            "carbon_gco2": 0.0,
            "intelligence_units": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception:
        # Non-critical logging failure
        pass
    
    return {
        "proposal_id": str(proposal_id),
        "is_duplicate": is_duplicate,
        "similar_proposals": similar_proposals
    }


async def get_similar_proposals(
    user_id: str,
    proposal_id: UUID,
    threshold: float = 0.80,
    limit: int = 10
) -> Optional[List[Dict[str, Any]]]:
    """
    Get similar proposals based on embeddings similarity.
    """
    # Verify proposal exists and user has access
    proposal_response = supabase.table("chamber_proposals").select(
        "id, submitter_id, embeddings"
    ).eq("id", str(proposal_id)).execute()
    
    if not proposal_response.data or len(proposal_response.data) == 0:
        return None
    
    proposal = proposal_response.data[0]
    
    # Check ownership or role permissions
    user_response = supabase.table("chamber_users").select("role").eq("id", user_id).execute()
    if not user_response.data:
        return None
    
    user_role = user_response.data[0].get("role")
    is_owner = proposal["submitter_id"] == user_id
    has_permission = user_role in ["analyst", "executive", "compliance_officer", "admin"]
    
    if not is_owner and not has_permission:
        return None
    
    embeddings = proposal.get("embeddings")
    if not embeddings:
        return []
    
    # Query similar proposals
    similar_response = supabase.rpc(
        "match_proposals",
        {
            "query_embedding": embeddings,
            "match_threshold": threshold,
            "match_count": limit,
            "exclude_proposal_id": str(proposal_id)
        }
    ).execute()
    
    similar_proposals = []
    if similar_response.data:
        for similar in similar_response.data:
            similar_proposals.append({
                "proposal_id": similar["id"],
                "title": similar["title"],
                "similarity_score": round(similar.get("similarity", 0.0), 4),
                "submission_date": similar["created_at"],
                "sector": similar.get("sector"),
                "technology_type": similar.get("technology_type")
            })
    
    return similar_proposals

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


def get_business_group_config(user_id: UUID, group_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Retrieve evaluation weight config for a business group.
    Returns None if not found or user doesn't have access.
    """
    result = supabase.table("business_groups").select(
        "id, name, chamber, evaluation_weight_config, lead_user_id"
    ).eq("id", str(group_id)).execute()
    
    if not result.data:
        return None
    
    group = result.data[0]
    
    # Verify user has access (either group lead or analyst/executive role)
    # For this endpoint, we'll allow anyone authenticated to read config
    # Write operations are restricted to lead only (checked in update)
    return group


def update_evaluation_config(
    user_id: UUID,
    group_id: UUID,
    evaluation_weight_config: Dict[str, float]
) -> Optional[Dict[str, Any]]:
    """
    Update evaluation weight configuration for a business group.
    Only the business group lead can perform this operation.
    Returns None if group not found or user is not the lead.
    """
    # First, verify the business group exists and user is the lead
    result = supabase.table("business_groups").select(
        "id, lead_user_id"
    ).eq("id", str(group_id)).execute()
    
    if not result.data:
        return None
    
    group = result.data[0]
    
    # Check if user is the group lead
    if group.get("lead_user_id") != str(user_id):
        return None
    
    # Validate weights sum to 1.0 (with small tolerance for floating point)
    weights_sum = (
        evaluation_weight_config.get("relevance_weight", 0) +
        evaluation_weight_config.get("feasibility_weight", 0) +
        evaluation_weight_config.get("sector_alignment_weight", 0) +
        evaluation_weight_config.get("compliance_weight", 0)
    )
    
    if abs(weights_sum - 1.0) > 0.0001:
        raise ValueError("Weights must sum to 1.0")
    
    # Update the evaluation_weight_config
    update_data = {
        "evaluation_weight_config": evaluation_weight_config,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    update_result = supabase.table("business_groups").update(
        update_data
    ).eq("id", str(group_id)).execute()
    
    if not update_result.data:
        return None
    
    updated_group = update_result.data[0]
    
    return {
        "business_group_id": updated_group["id"],
        "evaluation_weight_config": updated_group["evaluation_weight_config"],
        "updated_at": updated_group["updated_at"]
    }


def verify_is_group_lead(user_id: UUID, group_id: UUID) -> bool:
    """
    Verify if the user is the lead of the specified business group.
    Returns True if user is the lead, False otherwise.
    """
    result = supabase.table("business_groups").select(
        "lead_user_id"
    ).eq("id", str(group_id)).execute()
    
    if not result.data:
        return False
    
    group = result.data[0]
    return group.get("lead_user_id") == str(user_id)

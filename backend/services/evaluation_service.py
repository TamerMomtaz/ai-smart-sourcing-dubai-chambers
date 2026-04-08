from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID
from database import supabase


def get_by_proposal_id(user_id: UUID, proposal_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get detailed evaluation results for a proposal.
    Verifies user has access to the proposal.
    """
    # First verify the proposal exists and user has access
    proposal_response = supabase.table("chamber_proposals").select(
        "id, submitter_id, business_group_id, sourcing_case_id"
    ).eq("id", str(proposal_id)).maybe_single().execute()

    if not proposal_response.data:
        return None

    proposal = proposal_response.data

    # Get user info to check permissions
    user_response = supabase.table("chamber_users").select(
        "id, role, business_group_id"
    ).eq("id", str(user_id)).maybe_single().execute()

    if not user_response.data:
        return None

    user = user_response.data
    user_role = user.get("role")

    # Check access permissions
    has_access = False

    # Vendors can only see their own proposals
    if user_role == "vendor":
        has_access = str(proposal.get("submitter_id")) == str(user_id)
    # Business group leads can see proposals in their group
    elif user_role == "business_group_lead":
        has_access = (
            proposal.get("business_group_id") and
            str(proposal.get("business_group_id")) == str(user.get("business_group_id"))
        )
    # Analysts, executives, compliance officers can see all
    elif user_role in ("analyst", "executive", "compliance_officer", "admin"):
        has_access = True

    if not has_access:
        return None

    # Fetch evaluation data
    eval_response = supabase.table("chamber_evaluations").select(
        "*"
    ).eq("proposal_id", str(proposal_id)).maybe_single().execute()

    if not eval_response.data:
        return None

    evaluation = eval_response.data

    # Fetch AI interactions for this evaluation
    ai_interactions = []
    if evaluation.get("id"):
        ai_response = supabase.table("chamber_ai_interactions").select(
            "model_name, prompt_tokens, completion_tokens, latency_ms, cost_usd, operation_type"
        ).eq("evaluation_id", str(evaluation["id"])).order(
            "timestamp", desc=False
        ).execute()

        if ai_response.data:
            ai_interactions = ai_response.data

    # Fetch sourcing case context if proposal is linked to one
    sourcing_case_context = None
    if proposal.get("sourcing_case_id"):
        try:
            case_response = supabase.table("chamber_sourcing_cases").select(
                "id, title, problem_statement, sector, technology_domain, compliance_requirements"
            ).eq("id", str(proposal["sourcing_case_id"])).maybe_single().execute()
            if case_response.data:
                sourcing_case_context = {
                    "id": case_response.data["id"],
                    "title": case_response.data.get("title", ""),
                    "problem_statement": case_response.data.get("problem_statement", ""),
                    "sector": case_response.data.get("sector"),
                    "technology_domain": case_response.data.get("technology_domain"),
                    "compliance_requirements": case_response.data.get("compliance_requirements"),
                }
        except Exception:
            pass  # Non-critical — evaluation still valid without case context

    # Build response
    result = {
        "id": evaluation["id"],
        "proposal_id": evaluation["proposal_id"],
        "relevance_score": evaluation.get("relevance_score"),
        "relevance_reasoning": evaluation.get("relevance_reasoning", ""),
        "feasibility_score": evaluation.get("feasibility_score"),
        "feasibility_reasoning": evaluation.get("feasibility_reasoning", ""),
        "sector_alignment_score": evaluation.get("sector_alignment_score"),
        "sector_reasoning": evaluation.get("sector_reasoning", ""),
        "compliance_score": evaluation.get("compliance_score"),
        "compliance_reasoning": evaluation.get("compliance_reasoning", ""),
        "composite_score": evaluation.get("composite_score"),
        "evaluated_at": evaluation.get("evaluated_at"),
        "evaluator_agent_versions": evaluation.get("evaluator_agent_versions"),
        "hallucination_check_passed": evaluation.get("hallucination_check_passed", False),
        "prompt_injection_detected": evaluation.get("prompt_injection_detected", False),
        "summary_en": evaluation.get("summary_en", ""),
        "summary_ar": evaluation.get("summary_ar", ""),
        "ai_interactions": ai_interactions,
        "sourcing_case_context": sourcing_case_context,
    }

    return result


def create(
    user_id: UUID,
    proposal_id: UUID,
    relevance_score: float,
    relevance_reasoning: str,
    feasibility_score: float,
    feasibility_reasoning: str,
    sector_alignment_score: float,
    sector_reasoning: str,
    compliance_score: float,
    compliance_reasoning: str,
    composite_score: float,
    summary_en: str,
    summary_ar: str,
    evaluator_agent_versions: Optional[Dict[str, Any]] = None,
    hallucination_check_passed: bool = True,
    prompt_injection_detected: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Create a new evaluation record.
    Only system/admin users should call this directly.
    """
    now = datetime.now(timezone.utc)

    evaluation_data = {
        "proposal_id": str(proposal_id),
        "relevance_score": relevance_score,
        "relevance_reasoning": relevance_reasoning,
        "feasibility_score": feasibility_score,
        "feasibility_reasoning": feasibility_reasoning,
        "sector_alignment_score": sector_alignment_score,
        "sector_reasoning": sector_reasoning,
        "compliance_score": compliance_score,
        "compliance_reasoning": compliance_reasoning,
        "composite_score": composite_score,
        "evaluated_at": now.isoformat(),
        "evaluator_agent_versions": evaluator_agent_versions,
        "hallucination_check_passed": hallucination_check_passed,
        "prompt_injection_detected": prompt_injection_detected,
        "summary_en": summary_en,
        "summary_ar": summary_ar,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }

    response = supabase.table("chamber_evaluations").insert(
        evaluation_data
    ).execute()

    if not response.data:
        return None

    return response.data[0]


def list_by_proposal_ids(
    user_id: UUID,
    proposal_ids: List[UUID]
) -> List[Dict[str, Any]]:
    """
    Get evaluations for multiple proposals.
    Used for batch operations.
    """
    if not proposal_ids:
        return []

    # Convert UUIDs to strings
    proposal_ids_str = [str(pid) for pid in proposal_ids]

    # Get user role for access control
    user_response = supabase.table("chamber_users").select(
        "id, role, business_group_id"
    ).eq("id", str(user_id)).maybe_single().execute()

    if not user_response.data:
        return []

    user = user_response.data
    user_role = user.get("role")

    # For vendors, filter proposals they own
    if user_role == "vendor":
        proposals_response = supabase.table("chamber_proposals").select(
            "id"
        ).eq("submitter_id", str(user_id)).in_("id", proposal_ids_str).execute()

        if not proposals_response.data:
            return []

        accessible_ids = [p["id"] for p in proposals_response.data]
    # For business group leads, filter by their group
    elif user_role == "business_group_lead":
        proposals_response = supabase.table("chamber_proposals").select(
            "id"
        ).eq("business_group_id", str(user.get("business_group_id"))).in_(
            "id", proposal_ids_str
        ).execute()

        if not proposals_response.data:
            return []

        accessible_ids = [p["id"] for p in proposals_response.data]
    # Analysts, executives, compliance officers see all
    else:
        accessible_ids = proposal_ids_str

    if not accessible_ids:
        return []

    # Fetch evaluations
    eval_response = supabase.table("chamber_evaluations").select(
        "id, proposal_id, relevance_score, feasibility_score, sector_alignment_score, compliance_score, composite_score, evaluated_at, summary_en, summary_ar"
    ).in_("proposal_id", accessible_ids).execute()

    if not eval_response.data:
        return []

    return eval_response.data


def update(
    user_id: UUID,
    evaluation_id: UUID,
    updates: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update evaluation record.
    Only admin/system should call this.
    """
    # Verify evaluation exists
    eval_response = supabase.table("chamber_evaluations").select(
        "id"
    ).eq("id", str(evaluation_id)).maybe_single().execute()

    if not eval_response.data:
        return None

    # Add updated_at timestamp
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Update
    update_response = supabase.table("chamber_evaluations").update(
        updates
    ).eq("id", str(evaluation_id)).execute()

    if not update_response.data:
        return None

    return update_response.data[0]


def get_by_id(user_id: UUID, evaluation_id: UUID) -> Optional[Dict[str, Any]]:
    """Get evaluation by ID."""
    eval_response = supabase.table("chamber_evaluations").select(
        "*"
    ).eq("id", str(evaluation_id)).maybe_single().execute()

    if not eval_response.data:
        return None

    return eval_response.data


def list_evaluations(
    user_id: UUID,
    page: int = 1,
    page_size: int = 50,
    proposal_id: Optional[UUID] = None,
    min_composite_score: Optional[float] = None,
    max_composite_score: Optional[float] = None,
    **kwargs,
) -> Optional[Dict[str, Any]]:
    """List evaluations with pagination and filters."""
    offset = (page - 1) * page_size

    query = supabase.table("chamber_evaluations").select("*", count="exact")

    if proposal_id:
        query = query.eq("proposal_id", str(proposal_id))
    if min_composite_score is not None:
        query = query.gte("composite_score", min_composite_score)
    if max_composite_score is not None:
        query = query.lte("composite_score", max_composite_score)

    query = query.order("evaluated_at", desc=True)
    query = query.range(offset, offset + page_size - 1)

    result = query.execute()
    evaluations = result.data or []
    total = result.count or 0
    total_pages = (total + page_size - 1) // page_size

    return {
        "evaluations": evaluations,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        },
    }


def delete(user_id: UUID, evaluation_id: UUID) -> bool:
    """
    Soft delete evaluation.
    Only admin should call this.
    """
    now = datetime.now(timezone.utc)

    delete_response = supabase.table("chamber_evaluations").update({
        "deleted_at": now.isoformat(),
        "updated_at": now.isoformat()
    }).eq("id", str(evaluation_id)).is_("deleted_at", "null").execute()

    return len(delete_response.data) > 0

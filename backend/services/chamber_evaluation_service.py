from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


def create_evaluation(
    user_id: UUID,
    proposal_id: UUID,
    relevance_score: Optional[float] = None,
    relevance_reasoning: Optional[str] = None,
    feasibility_score: Optional[float] = None,
    feasibility_reasoning: Optional[str] = None,
    sector_alignment_score: Optional[float] = None,
    sector_reasoning: Optional[str] = None,
    compliance_score: Optional[float] = None,
    compliance_reasoning: Optional[str] = None,
    composite_score: Optional[float] = None,
    evaluator_agent_versions: Optional[Dict[str, Any]] = None,
    hallucination_check_passed: bool = True,
    prompt_injection_detected: bool = False,
    summary_en: Optional[str] = None,
    summary_ar: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Create a new chamber evaluation."""
    payload = {
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
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "evaluator_agent_versions": evaluator_agent_versions,
        "hallucination_check_passed": hallucination_check_passed,
        "prompt_injection_detected": prompt_injection_detected,
        "summary_en": summary_en,
        "summary_ar": summary_ar,
    }

    result = (
        supabase.table("chamber_evaluations")
        .insert(payload)
        .execute()
    )

    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


def list_evaluations(
    user_id: UUID,
    page: int = 1,
    page_size: int = 50,
    proposal_id: Optional[UUID] = None,
    min_composite_score: Optional[float] = None,
    max_composite_score: Optional[float] = None,
) -> tuple[List[Dict[str, Any]], int]:
    """List chamber evaluations with pagination and filters."""
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

    return evaluations, total


def get_evaluation_by_id(
    user_id: UUID,
    evaluation_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Get a single chamber evaluation by ID."""
    result = (
        supabase.table("chamber_evaluations")
        .select("*")
        .eq("id", str(evaluation_id))
        .maybe_single()
        .execute()
    )

    return result.data


def get_evaluation_by_proposal_id(
    user_id: UUID,
    proposal_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Get chamber evaluation by proposal ID (unique constraint)."""
    result = (
        supabase.table("chamber_evaluations")
        .select("*")
        .eq("proposal_id", str(proposal_id))
        .maybe_single()
        .execute()
    )

    return result.data


def update_evaluation(
    user_id: UUID,
    evaluation_id: UUID,
    relevance_score: Optional[float] = None,
    relevance_reasoning: Optional[str] = None,
    feasibility_score: Optional[float] = None,
    feasibility_reasoning: Optional[str] = None,
    sector_alignment_score: Optional[float] = None,
    sector_reasoning: Optional[str] = None,
    compliance_score: Optional[float] = None,
    compliance_reasoning: Optional[str] = None,
    composite_score: Optional[float] = None,
    evaluator_agent_versions: Optional[Dict[str, Any]] = None,
    hallucination_check_passed: Optional[bool] = None,
    prompt_injection_detected: Optional[bool] = None,
    summary_en: Optional[str] = None,
    summary_ar: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update an existing chamber evaluation."""
    evaluation = get_evaluation_by_id(user_id, evaluation_id)
    if not evaluation:
        return None

    payload: Dict[str, Any] = {}

    if relevance_score is not None:
        payload["relevance_score"] = relevance_score
    if relevance_reasoning is not None:
        payload["relevance_reasoning"] = relevance_reasoning
    if feasibility_score is not None:
        payload["feasibility_score"] = feasibility_score
    if feasibility_reasoning is not None:
        payload["feasibility_reasoning"] = feasibility_reasoning
    if sector_alignment_score is not None:
        payload["sector_alignment_score"] = sector_alignment_score
    if sector_reasoning is not None:
        payload["sector_reasoning"] = sector_reasoning
    if compliance_score is not None:
        payload["compliance_score"] = compliance_score
    if compliance_reasoning is not None:
        payload["compliance_reasoning"] = compliance_reasoning
    if composite_score is not None:
        payload["composite_score"] = composite_score
    if evaluator_agent_versions is not None:
        payload["evaluator_agent_versions"] = evaluator_agent_versions
    if hallucination_check_passed is not None:
        payload["hallucination_check_passed"] = hallucination_check_passed
    if prompt_injection_detected is not None:
        payload["prompt_injection_detected"] = prompt_injection_detected
    if summary_en is not None:
        payload["summary_en"] = summary_en
    if summary_ar is not None:
        payload["summary_ar"] = summary_ar

    if not payload:
        return evaluation

    payload["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("chamber_evaluations")
        .update(payload)
        .eq("id", str(evaluation_id))
        .execute()
    )

    if result.data and len(result.data) > 0:
        return result.data[0]
    return None


def delete_evaluation(
    user_id: UUID,
    evaluation_id: UUID,
) -> bool:
    """Soft delete a chamber evaluation (mark as deleted)."""
    evaluation = get_evaluation_by_id(user_id, evaluation_id)
    if not evaluation:
        return False

    result = (
        supabase.table("chamber_evaluations")
        .delete()
        .eq("id", str(evaluation_id))
        .execute()
    )

    return result.data is not None and len(result.data) > 0


def get_evaluations_by_score_range(
    user_id: UUID,
    min_score: float,
    max_score: float,
    page: int = 1,
    page_size: int = 50,
) -> tuple[List[Dict[str, Any]], int]:
    """Get evaluations within a composite score range."""
    offset = (page - 1) * page_size

    result = (
        supabase.table("chamber_evaluations")
        .select("*", count="exact")
        .gte("composite_score", min_score)
        .lte("composite_score", max_score)
        .order("composite_score", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    evaluations = result.data or []
    total = result.count or 0

    return evaluations, total


def get_failed_hallucination_checks(
    user_id: UUID,
    page: int = 1,
    page_size: int = 50,
) -> tuple[List[Dict[str, Any]], int]:
    """Get evaluations that failed hallucination checks."""
    offset = (page - 1) * page_size

    result = (
        supabase.table("chamber_evaluations")
        .select("*", count="exact")
        .eq("hallucination_check_passed", False)
        .order("evaluated_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    evaluations = result.data or []
    total = result.count or 0

    return evaluations, total


def get_prompt_injection_detections(
    user_id: UUID,
    page: int = 1,
    page_size: int = 50,
) -> tuple[List[Dict[str, Any]], int]:
    """Get evaluations where prompt injection was detected."""
    offset = (page - 1) * page_size

    result = (
        supabase.table("chamber_evaluations")
        .select("*", count="exact")
        .eq("prompt_injection_detected", True)
        .order("evaluated_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    evaluations = result.data or []
    total = result.count or 0

    return evaluations, total

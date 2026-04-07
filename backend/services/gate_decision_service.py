from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


# Gate ordering for stage advancement
GATE_ORDER = ['discovery', 'scoping', 'evaluation', 'pilot_approval', 'procurement']

# Decision-to-status mapping
DECISION_STATUS_MAP = {
    'go': None,  # advance to next gate — handled separately
    'kill': 'rejected',
    'hold': 'on_hold',
    'recycle': 'revision_requested',
    'conditional_go': 'conditional',
}


def _next_gate(current_gate: str) -> Optional[str]:
    """Return the next gate after current, or None if at the end."""
    try:
        idx = GATE_ORDER.index(current_gate)
        if idx + 1 < len(GATE_ORDER):
            return GATE_ORDER[idx + 1]
    except ValueError:
        pass
    return None


def _get_latest_evaluation(proposal_id: str) -> Optional[Dict[str, Any]]:
    """Fetch the latest AI evaluation for a proposal."""
    response = (
        supabase.table("chamber_evaluations")
        .select("composite_score, summary_en")
        .eq("proposal_id", proposal_id)
        .order("evaluated_at", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def create_gate_decision(
    proposal_id: UUID,
    gate_name: str,
    decision: str,
    decided_by: UUID,
    decision_reason: Optional[str] = None,
    conditions: Optional[str] = None,
    committee_members: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Record a stage-gate decision and update proposal status accordingly.
    """
    proposal_id_str = str(proposal_id)

    # Verify proposal exists
    proposal_resp = (
        supabase.table("chamber_proposals")
        .select("id, status")
        .eq("id", proposal_id_str)
        .maybe_single()
        .execute()
    )
    if not proposal_resp.data:
        return None

    # Get AI recommendation from latest evaluation
    eval_data = _get_latest_evaluation(proposal_id_str)
    ai_recommendation = eval_data.get("summary_en") if eval_data else None
    ai_score = eval_data.get("composite_score") if eval_data else None

    # Insert gate decision
    decision_data = {
        "proposal_id": proposal_id_str,
        "gate_name": gate_name,
        "decision": decision,
        "decision_reason": decision_reason,
        "decided_by": str(decided_by),
        "committee_members": committee_members,
        "ai_recommendation": ai_recommendation,
        "ai_score": float(ai_score) if ai_score is not None else None,
        "conditions": conditions,
    }

    insert_resp = supabase.table("chamber_gate_decisions").insert(decision_data).execute()
    if not insert_resp.data:
        return None

    gate_decision = insert_resp.data[0]

    # Update proposal status based on decision
    new_status = DECISION_STATUS_MAP.get(decision)
    if decision == 'go':
        next_gate = _next_gate(gate_name)
        if next_gate == 'procurement':
            new_status = 'approved'
        else:
            new_status = 'under_review'

    if new_status:
        supabase.table("chamber_proposals").update({
            "status": new_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", proposal_id_str).execute()

    gate_decision["new_status"] = new_status

    return gate_decision


def get_gate_history(
    proposal_id: UUID,
) -> List[Dict[str, Any]]:
    """
    Return all gate decisions for a proposal in chronological order.
    """
    response = (
        supabase.table("chamber_gate_decisions")
        .select("*")
        .eq("proposal_id", str(proposal_id))
        .order("created_at", desc=False)
        .execute()
    )
    return response.data if response.data else []

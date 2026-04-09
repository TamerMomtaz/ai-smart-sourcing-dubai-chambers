"""Service layer for Sourcing Case operations."""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from database import supabase

logger = logging.getLogger(__name__)


def create_sourcing_case(
    *,
    title: str,
    problem_statement: str,
    requesting_entity: str = None,
    business_group_id: str = None,
    sector: str = None,
    technology_domain: str = None,
    urgency: str = "medium",
    compliance_tier: str = "standard",
    compliance_requirements: str = None,
    assigned_analyst_id: str = None,
    created_by: str,
    status: str = "open",
    source_channel: str = "manual",
):
    """Create a new sourcing case."""
    data = {
        "title": title,
        "problem_statement": problem_statement,
        "urgency": urgency,
        "compliance_tier": compliance_tier,
        "status": status,
        "created_by": created_by,
        "source_channel": source_channel,
    }
    if requesting_entity:
        data["requesting_entity"] = requesting_entity
    if business_group_id:
        data["business_group_id"] = business_group_id
    if sector:
        data["sector"] = sector
    if technology_domain:
        data["technology_domain"] = technology_domain
    if compliance_requirements:
        data["compliance_requirements"] = compliance_requirements
    if assigned_analyst_id:
        data["assigned_analyst_id"] = assigned_analyst_id
    elif sector:
        # Auto-assign analyst based on sector mapping
        try:
            mapping = (
                supabase.table("chamber_sector_assignments")
                .select("assigned_user_id")
                .eq("sector", sector)
                .maybe_single()
                .execute()
            )
            if mapping.data and mapping.data.get("assigned_user_id"):
                data["assigned_analyst_id"] = mapping.data["assigned_user_id"]
                logger.info(
                    "Auto-assigned analyst %s for sector '%s'",
                    mapping.data["assigned_user_id"],
                    sector,
                )
        except Exception as e:
            logger.warning("Sector auto-assignment lookup failed: %s", e)

    result = supabase.table("chamber_sourcing_cases").insert(data).execute()
    return result.data[0] if result.data else None


def list_sourcing_cases(
    *,
    status_filter: str = None,
    sector_filter: str = None,
    urgency_filter: str = None,
    source_channel_filter: str = None,
    sort_by: str = "created_at",
):
    """List sourcing cases with optional filters."""
    query = supabase.table("chamber_sourcing_cases").select("*")

    if status_filter:
        query = query.eq("status", status_filter)
    if sector_filter:
        query = query.eq("sector", sector_filter)
    if urgency_filter:
        query = query.eq("urgency", urgency_filter)
    if source_channel_filter:
        query = query.eq("source_channel", source_channel_filter)

    if sort_by == "urgency":
        query = query.order("urgency", desc=False).order("created_at", desc=True)
    else:
        query = query.order("created_at", desc=True)

    result = query.execute()
    cases = result.data or []

    # Attach proposal counts
    if cases:
        case_ids = [c["id"] for c in cases]
        proposals_result = (
            supabase.table("chamber_proposals")
            .select("sourcing_case_id")
            .in_("sourcing_case_id", case_ids)
            .execute()
        )
        count_map = {}
        for p in (proposals_result.data or []):
            cid = p["sourcing_case_id"]
            count_map[cid] = count_map.get(cid, 0) + 1

        for c in cases:
            c["proposal_count"] = count_map.get(c["id"], 0)

    return cases


def get_sourcing_case(*, case_id: str):
    """Get a single sourcing case with linked proposals and evaluations."""
    result = (
        supabase.table("chamber_sourcing_cases")
        .select("*")
        .eq("id", case_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        return None

    case = result.data

    # Fetch linked proposals
    proposals_result = (
        supabase.table("chamber_proposals")
        .select("id, title, status, sector, technology_type, created_at, composite_score")
        .eq("sourcing_case_id", case_id)
        .order("created_at", desc=True)
        .execute()
    )
    case["proposals"] = proposals_result.data or []

    # Fetch matching vendors by sector (if sector is set)
    if case.get("sector"):
        vendors_result = (
            supabase.table("chamber_vendors")
            .select("id, company_name, country, email")
            .limit(20)
            .execute()
        )
        case["matching_vendors"] = vendors_result.data or []
    else:
        case["matching_vendors"] = []

    # Fetch assigned analyst info
    if case.get("assigned_analyst_id"):
        analyst_result = (
            supabase.table("chamber_users")
            .select("id, email, role")
            .eq("id", case["assigned_analyst_id"])
            .maybe_single()
            .execute()
        )
        case["assigned_analyst"] = analyst_result.data
    else:
        case["assigned_analyst"] = None

    return case


def update_sourcing_case_status(*, case_id: str, new_status: str):
    """Update the status of a sourcing case."""
    update_data = {
        "status": new_status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if new_status in ("completed", "closed"):
        update_data["closed_at"] = datetime.now(timezone.utc).isoformat()

    result = (
        supabase.table("chamber_sourcing_cases")
        .update(update_data)
        .eq("id", case_id)
        .execute()
    )
    return result.data[0] if result.data else None


def get_compare_proposals(*, case_id: str) -> Optional[Dict[str, Any]]:
    """Get all proposals linked to a sourcing case with evaluation data for comparison."""
    # Verify case exists
    case_result = (
        supabase.table("chamber_sourcing_cases")
        .select("id, title, problem_statement, sector, compliance_tier")
        .eq("id", case_id)
        .maybe_single()
        .execute()
    )
    if not case_result.data:
        return None

    case = case_result.data

    # Fetch linked proposals with vendor info
    proposals_result = (
        supabase.table("chamber_proposals")
        .select("id, title, status, sector, technology_type, created_at, composite_score, submitter_id")
        .eq("sourcing_case_id", case_id)
        .order("composite_score", desc=True)
        .execute()
    )
    proposals = proposals_result.data or []
    if not proposals:
        return {"case": case, "proposals": []}

    proposal_ids = [p["id"] for p in proposals]
    submitter_ids = list({p["submitter_id"] for p in proposals if p.get("submitter_id")})

    # Fetch evaluations for these proposals
    eval_result = (
        supabase.table("chamber_evaluations")
        .select("proposal_id, composite_score, relevance_score, feasibility_score, sector_alignment_score, compliance_score, innovation_score, ai_recommendation, evaluated_at")
        .in_("proposal_id", proposal_ids)
        .execute()
    )
    eval_map = {}
    for ev in (eval_result.data or []):
        eval_map[ev["proposal_id"]] = ev

    # Fetch compliance gate results
    compliance_map = {}
    try:
        comp_result = (
            supabase.table("chamber_compliance_gates")
            .select("proposal_id, gate_status, checked_at")
            .in_("proposal_id", proposal_ids)
            .execute()
        )
        for cg in (comp_result.data or []):
            compliance_map[cg["proposal_id"]] = cg
    except Exception as e:
        logger.warning("Failed to fetch compliance gates: %s", e)

    # Fetch hallucination shield (evidence grounding) data
    shield_map = {}
    try:
        shield_result = (
            supabase.table("chamber_hallucination_checks")
            .select("evaluation_id, grounding_score")
            .execute()
        )
        # Map evaluation_id -> grounding_score, then we'll map via proposal
        eval_id_to_grounding = {}
        for sh in (shield_result.data or []):
            eval_id_to_grounding[sh["evaluation_id"]] = sh.get("grounding_score")
        # Now map proposal_id -> grounding_score via eval
        for pid, ev in eval_map.items():
            if ev.get("id") in eval_id_to_grounding:
                shield_map[pid] = eval_id_to_grounding[ev["id"]]
    except Exception as e:
        logger.warning("Failed to fetch hallucination checks: %s", e)

    # Fetch vendor info
    vendor_map = {}
    if submitter_ids:
        try:
            vendor_result = (
                supabase.table("chamber_vendors")
                .select("id, company_name")
                .in_("id", submitter_ids)
                .execute()
            )
            for v in (vendor_result.data or []):
                vendor_map[v["id"]] = v
        except Exception as e:
            logger.warning("Failed to fetch vendors: %s", e)

    # Fetch vendor vScores
    vscore_map = {}
    if submitter_ids:
        try:
            vscore_result = (
                supabase.table("chamber_vendor_scores")
                .select("vendor_id, vscore, tier")
                .in_("vendor_id", submitter_ids)
                .execute()
            )
            for vs in (vscore_result.data or []):
                vscore_map[vs["vendor_id"]] = vs
        except Exception as e:
            logger.warning("Failed to fetch vendor scores: %s", e)

    # Build enriched proposal list
    enriched = []
    for p in proposals:
        ev = eval_map.get(p["id"], {})
        vendor = vendor_map.get(p.get("submitter_id"), {})
        vscore = vscore_map.get(p.get("submitter_id"), {})
        gate = compliance_map.get(p["id"], {})
        grounding = shield_map.get(p["id"])

        enriched.append({
            "id": p["id"],
            "title": p["title"],
            "status": p["status"],
            "sector": p.get("sector"),
            "technology_type": p.get("technology_type"),
            "created_at": p.get("created_at"),
            "vendor_name": vendor.get("company_name", "Unknown"),
            "vendor_id": p.get("submitter_id"),
            # Evaluation scores
            "composite_score": ev.get("composite_score") or p.get("composite_score"),
            "relevance_score": ev.get("relevance_score"),
            "feasibility_score": ev.get("feasibility_score"),
            "sector_alignment_score": ev.get("sector_alignment_score"),
            "compliance_score": ev.get("compliance_score"),
            "innovation_score": ev.get("innovation_score"),
            "ai_recommendation": ev.get("ai_recommendation"),
            "evaluated_at": ev.get("evaluated_at"),
            # Compliance gate
            "gate_status": gate.get("gate_status"),
            # Evidence grounding
            "grounding_score": grounding,
            # Vendor vScore
            "vscore": vscore.get("vscore"),
            "vscore_tier": vscore.get("tier"),
        })

    return {"case": case, "proposals": enriched}


def merge_sourcing_cases(*, source_id: str, target_id: str, merged_by: str) -> Optional[Dict[str, Any]]:
    """
    Merge source sourcing case into target.
    - Moves all linked proposals from source to target
    - Moves all vendor matches from source to target
    - Sets source status to 'closed' with merge note
    """
    # Verify both cases exist
    source = (
        supabase.table("chamber_sourcing_cases")
        .select("id, title, status")
        .eq("id", source_id)
        .maybe_single()
        .execute()
    )
    if not source.data:
        return None

    target = (
        supabase.table("chamber_sourcing_cases")
        .select("id, title, status")
        .eq("id", target_id)
        .maybe_single()
        .execute()
    )
    if not target.data:
        return None

    now = datetime.now(timezone.utc).isoformat()

    # Move linked proposals from source to target
    proposals_moved = 0
    try:
        proposals_result = (
            supabase.table("chamber_proposals")
            .select("id")
            .eq("sourcing_case_id", source_id)
            .execute()
        )
        if proposals_result.data:
            proposals_moved = len(proposals_result.data)
            supabase.table("chamber_proposals").update(
                {"sourcing_case_id": target_id, "updated_at": now}
            ).eq("sourcing_case_id", source_id).execute()
    except Exception as e:
        logger.warning(f"Failed to move proposals during merge: {e}")

    # Move vendor matches from source to target
    vendor_matches_moved = 0
    try:
        matches_result = (
            supabase.table("chamber_vendor_matches")
            .select("id")
            .eq("sourcing_case_id", source_id)
            .execute()
        )
        if matches_result.data:
            vendor_matches_moved = len(matches_result.data)
            supabase.table("chamber_vendor_matches").update(
                {"sourcing_case_id": target_id}
            ).eq("sourcing_case_id", source_id).execute()
    except Exception as e:
        logger.warning(f"Failed to move vendor matches during merge: {e}")

    # Close source case with merge note
    merge_note = f"Merged into {target_id}"
    supabase.table("chamber_sourcing_cases").update({
        "status": "closed",
        "compliance_requirements": (
            (source.data.get("compliance_requirements") or "") +
            f"\n[MERGED] {merge_note}"
        ).strip(),
        "updated_at": now,
        "closed_at": now,
    }).eq("id", source_id).execute()

    return {
        "source_case_id": source_id,
        "target_case_id": target_id,
        "source_title": source.data.get("title", ""),
        "target_title": target.data.get("title", ""),
        "proposals_moved": proposals_moved,
        "vendor_matches_moved": vendor_matches_moved,
        "merged_by": merged_by,
        "merged_at": now,
    }

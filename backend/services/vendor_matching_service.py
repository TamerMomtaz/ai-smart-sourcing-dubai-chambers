"""Service layer for AI-powered vendor matching against sourcing cases."""
import json
import logging
import time
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from database import supabase
from services.ai_provider import ai_complete
from services import ai_interaction_service

logger = logging.getLogger(__name__)

VENDOR_MATCH_SYSTEM_PROMPT = """You are an AI sourcing analyst for Dubai Chambers.
You are given a sourcing case and a list of candidate vendors. Rank the top vendors
by how well their capabilities match the sourcing case requirements.

For each vendor, provide:
- match_score: integer 0-100
- match_reasoning: 1-2 sentence explanation of why this vendor is a good (or poor) match

Return JSON only — an array of objects:
[
  {
    "vendor_id": "<uuid>",
    "match_score": <0-100>,
    "match_reasoning": "<explanation>"
  }
]
Return ONLY the top 10 vendors, sorted by match_score descending.
Return ONLY valid JSON, no markdown fences or extra text."""


async def discover_vendors(*, case_id: str, user_id: str) -> List[Dict[str, Any]]:
    """Run AI-powered vendor discovery for a sourcing case.

    Steps:
    1. Fetch sourcing case details
    2. Query candidate vendors (sector match, vScore >= 500)
    3. Enrich with proposal history and evaluation scores
    4. Call AI to rank top 10 with reasoning
    5. Store results in chamber_vendor_matches
    6. Log AI interaction
    """
    # 1. Fetch sourcing case
    case_result = (
        supabase.table("chamber_sourcing_cases")
        .select("*")
        .eq("id", case_id)
        .maybe_single()
        .execute()
    )
    if not case_result.data:
        return None  # signals 404

    case = case_result.data
    compliance_tier = case.get("compliance_tier", "standard")

    # 2. Query candidate vendors
    vendor_query = supabase.table("chamber_vendors").select(
        "id, company_name:name, country, email:contact_email, sector, vscore, desc_certified, is_desc_approved, iso_27001_certified, uae_data_residency"
    )

    # Apply vScore threshold
    vendor_query = vendor_query.gte("vscore", 500)

    # Apply tier-based compliance filters
    if compliance_tier == "government":
        # ONLY DESC-certified vendors
        vendor_query = vendor_query.eq("is_desc_approved", True)
    elif compliance_tier == "critical":
        # DESC-certified + ISO 27001 + UAE data residency
        vendor_query = vendor_query.eq("is_desc_approved", True)
        vendor_query = vendor_query.eq("iso_27001_certified", True)
        vendor_query = vendor_query.eq("uae_data_residency", True)
    # 'open' and 'standard' have no hard filters at the query level

    # Limit to a reasonable candidate pool
    vendor_query = vendor_query.order("vscore", desc=True).limit(50)

    vendor_result = vendor_query.execute()
    candidates = vendor_result.data or []

    if not candidates:
        return []

    # 3. Enrich with proposal history & evaluation averages
    vendor_ids = [v["id"] for v in candidates]

    # Fetch proposals from these vendors
    proposals_result = (
        supabase.table("chamber_proposals")
        .select("submitter_id, title, sector, technology_type, composite_score")
        .in_("submitter_id", vendor_ids)
        .execute()
    )
    proposals_by_vendor: Dict[str, list] = {}
    for p in (proposals_result.data or []):
        vid = p["submitter_id"]
        if vid not in proposals_by_vendor:
            proposals_by_vendor[vid] = []
        proposals_by_vendor[vid].append(p)

    # Build vendor summaries for AI
    vendor_summaries = []
    for v in candidates:
        vid = v["id"]
        props = proposals_by_vendor.get(vid, [])
        scores = [p["composite_score"] for p in props if p.get("composite_score")]
        avg_score = round(sum(scores) / len(scores), 1) if scores else None
        proposal_descriptions = "; ".join(
            [f"{p.get('title', 'Untitled')} ({p.get('sector', 'N/A')})" for p in props[:5]]
        )

        vendor_summaries.append({
            "vendor_id": vid,
            "company_name": v.get("company_name", "Unknown"),
            "sector": v.get("sector"),
            "vscore": v.get("vscore"),
            "desc_certified": v.get("desc_certified", False),
            "is_desc_approved": v.get("is_desc_approved", False),
            "iso_27001_certified": v.get("iso_27001_certified", False),
            "uae_data_residency": v.get("uae_data_residency", False),
            "past_proposals": proposal_descriptions or "No prior proposals",
            "avg_evaluation_score": avg_score,
        })

    # For 'standard' tier, prefer DESC-certified vendors (soft preference via AI prompt)
    tier_instruction = ""
    if compliance_tier == "standard":
        tier_instruction = "Compliance tier is 'standard': prefer DESC-certified vendors but allow non-certified ones with lower scores."
    elif compliance_tier == "government":
        tier_instruction = "Compliance tier is 'government': only DESC-certified vendors are eligible. Reject any non-certified vendor."
    elif compliance_tier == "critical":
        tier_instruction = "Compliance tier is 'critical': only vendors with DESC certification, ISO 27001, AND UAE data residency are eligible."

    # 4. Call AI to rank
    user_prompt = json.dumps({
        "sourcing_case": {
            "title": case.get("title"),
            "problem_statement": case.get("problem_statement"),
            "sector": case.get("sector"),
            "technology_domain": case.get("technology_domain"),
            "compliance_requirements": case.get("compliance_requirements"),
            "compliance_tier": compliance_tier,
            "tier_instruction": tier_instruction,
        },
        "candidate_vendors": vendor_summaries,
    }, indent=2)

    start_time = time.time()
    ai_response = await ai_complete(
        system_prompt=VENDOR_MATCH_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=4096,
    )
    latency_ms = int((time.time() - start_time) * 1000)

    # Parse AI response
    try:
        cleaned = ai_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        ranked = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("Failed to parse AI vendor matching response: %s\nResponse: %s", e, ai_response)
        ranked = []

    if not isinstance(ranked, list):
        ranked = []

    # Build a lookup for valid vendor IDs
    valid_vendor_ids = {v["id"] for v in candidates}

    # 5. Store results — delete old matches first, then insert new ones
    try:
        supabase.table("chamber_vendor_matches").delete().eq(
            "sourcing_case_id", case_id
        ).execute()
    except Exception as e:
        logger.warning("Failed to clear old vendor matches: %s", e)

    stored_matches = []
    for item in ranked[:10]:
        vid = item.get("vendor_id")
        if vid not in valid_vendor_ids:
            continue
        score = item.get("match_score", 0)
        reasoning = item.get("match_reasoning", "")
        try:
            insert_result = (
                supabase.table("chamber_vendor_matches")
                .insert({
                    "sourcing_case_id": case_id,
                    "vendor_id": vid,
                    "match_score": score,
                    "match_reasoning": reasoning,
                    "status": "suggested",
                })
                .execute()
            )
            if insert_result.data:
                stored_matches.append(insert_result.data[0])
        except Exception as e:
            logger.warning("Failed to insert vendor match for %s: %s", vid, e)

    # 6. Log AI interaction
    prompt_tokens = len(user_prompt.split()) + len(VENDOR_MATCH_SYSTEM_PROMPT.split())
    completion_tokens = len(ai_response.split()) if ai_response else 0

    try:
        ai_interaction_service.create(
            user_id=user_id,
            session_id=uuid4(),
            model_name="claude-sonnet-4-5-20250929",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=round(prompt_tokens * 0.000003 + completion_tokens * 0.000015, 6),
            energy_kwh=round(latency_ms * 0.0000003, 6),
            carbon_gco2=round(latency_ms * 0.0000001, 6),
            intelligence_units=round((prompt_tokens + completion_tokens) * 0.001, 4),
            operation_type="classification",
        )
    except Exception as e:
        logger.warning("Failed to log AI interaction for vendor matching: %s", e)

    # Enrich stored matches with vendor info
    vendor_lookup = {v["id"]: v for v in candidates}
    for match in stored_matches:
        vendor = vendor_lookup.get(match.get("vendor_id"), {})
        match["vendor_name"] = vendor.get("company_name", "Unknown")
        match["vendor_email"] = vendor.get("email")
        match["vendor_country"] = vendor.get("country")
        match["vendor_vscore"] = vendor.get("vscore")
        match["vendor_desc_certified"] = vendor.get("desc_certified", False)
        # Add avg evaluation score
        props = proposals_by_vendor.get(match.get("vendor_id"), [])
        scores = [p["composite_score"] for p in props if p.get("composite_score")]
        match["avg_evaluation_score"] = round(sum(scores) / len(scores), 1) if scores else None

    return stored_matches


def get_matched_vendors(*, case_id: str) -> Optional[Dict[str, Any]]:
    """Return cached vendor matches for a sourcing case, enriched with vendor info."""
    # Verify case exists and get compliance_tier
    case_check = (
        supabase.table("chamber_sourcing_cases")
        .select("id, compliance_tier")
        .eq("id", case_id)
        .maybe_single()
        .execute()
    )
    if not case_check.data:
        return None  # signals 404

    compliance_tier = case_check.data.get("compliance_tier", "standard")

    matches_result = (
        supabase.table("chamber_vendor_matches")
        .select("*")
        .eq("sourcing_case_id", case_id)
        .order("match_score", desc=True)
        .execute()
    )
    matches = matches_result.data or []

    if not matches:
        return {"matches": [], "compliance_tier": compliance_tier}

    # Enrich with vendor details
    vendor_ids = list({m["vendor_id"] for m in matches})
    vendors_result = (
        supabase.table("chamber_vendors")
        .select("id, company_name:name, country, email:contact_email, vscore, desc_certified, is_desc_approved, iso_27001_certified, uae_data_residency")
        .in_("id", vendor_ids)
        .execute()
    )
    vendor_lookup = {v["id"]: v for v in (vendors_result.data or [])}

    # Get evaluation averages
    proposals_result = (
        supabase.table("chamber_proposals")
        .select("submitter_id, composite_score")
        .in_("submitter_id", vendor_ids)
        .execute()
    )
    scores_by_vendor: Dict[str, list] = {}
    for p in (proposals_result.data or []):
        vid = p["submitter_id"]
        if p.get("composite_score"):
            if vid not in scores_by_vendor:
                scores_by_vendor[vid] = []
            scores_by_vendor[vid].append(p["composite_score"])

    for match in matches:
        vendor = vendor_lookup.get(match.get("vendor_id"), {})
        match["vendor_name"] = vendor.get("company_name", "Unknown")
        match["vendor_email"] = vendor.get("email")
        match["vendor_country"] = vendor.get("country")
        match["vendor_vscore"] = vendor.get("vscore")
        match["vendor_desc_certified"] = vendor.get("desc_certified", False)
        match["vendor_is_desc_approved"] = vendor.get("is_desc_approved", False)
        match["vendor_iso_27001_certified"] = vendor.get("iso_27001_certified", False)
        match["vendor_uae_data_residency"] = vendor.get("uae_data_residency", False)
        vscores = scores_by_vendor.get(match.get("vendor_id"), [])
        match["avg_evaluation_score"] = round(sum(vscores) / len(vscores), 1) if vscores else None

        # Compute whether vendor meets the compliance tier requirements
        match["meets_tier"] = _vendor_meets_tier(vendor=vendor, tier=compliance_tier)

    return {"matches": matches, "compliance_tier": compliance_tier}


def _vendor_meets_tier(*, vendor: Dict[str, Any], tier: str) -> bool:
    """Check if a vendor meets the compliance tier requirements."""
    if tier == "open":
        return True
    if tier == "standard":
        return True  # all vendors allowed, DESC just preferred
    if tier == "government":
        return bool(vendor.get("is_desc_approved"))
    if tier == "critical":
        return (
            bool(vendor.get("is_desc_approved"))
            and bool(vendor.get("iso_27001_certified"))
            and bool(vendor.get("uae_data_residency"))
        )
    return True


def update_match_status(*, match_id: str, new_status: str) -> Optional[Dict[str, Any]]:
    """Update the status of a vendor match (e.g. suggested -> invited)."""
    result = (
        supabase.table("chamber_vendor_matches")
        .update({"status": new_status})
        .eq("id", match_id)
        .execute()
    )
    return result.data[0] if result.data else None

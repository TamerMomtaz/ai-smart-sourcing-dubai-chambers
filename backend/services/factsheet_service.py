"""Service layer for Vendor Factsheet generation."""
import json
import logging
import time
import uuid
from typing import Optional, Dict, Any

from database import supabase
from services.ai_provider import ai_complete
from services import ai_interaction_service

logger = logging.getLogger(__name__)

# Cost estimates for Claude Sonnet (per-token)
PROMPT_COST_PER_TOKEN = 3.0 / 1_000_000
COMPLETION_COST_PER_TOKEN = 15.0 / 1_000_000
ENERGY_PER_TOKEN = 0.001  # kWh estimate
CARBON_PER_KWH = 300  # gCO2 per kWh


def get_latest_factsheet(*, vendor_id: str, sourcing_case_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Return the most recently generated factsheet for a vendor."""
    query = (
        supabase.table("chamber_vendor_factsheets")
        .select("*")
        .eq("vendor_id", vendor_id)
        .order("created_at", desc=True)
        .limit(1)
    )
    if sourcing_case_id:
        query = query.eq("sourcing_case_id", sourcing_case_id)

    result = query.execute()
    if result.data and len(result.data) > 0:
        row = result.data[0]
        # content is stored as JSONB — ensure it comes back as dict
        if isinstance(row.get("content"), str):
            row["content"] = json.loads(row["content"])
        return row
    return None


async def generate_factsheet(
    *,
    vendor_id: str,
    sourcing_case_id: Optional[str] = None,
    generated_by: str,
) -> Dict[str, Any]:
    """Aggregate vendor data, call AI for executive summary, persist and return factsheet."""

    # ── 1. Vendor profile ──
    vendor_resp = supabase.table("chamber_vendors").select(
        "id, name, country, contact_email, website, is_desc_approved, "
        "desc_badge_issued_date, onboarding_status, average_compliance_score, "
        "trade_license_status, desc_certified_provider_id, "
        "vscore, vscore_tier"
    ).eq("id", vendor_id).maybe_single().execute()

    if not vendor_resp.data:
        raise ValueError("Vendor not found")

    vendor = vendor_resp.data

    # Extended profile
    profile_resp = supabase.table("chamber_vendor_profiles").select(
        "team_size, funding_stage, technology_stack, certifications"
    ).eq("vendor_id", vendor_id).maybe_single().execute()
    profile = profile_resp.data or {}

    # ── 2. vScore breakdown (5 dimensions) ──
    vscore_data = {
        "vscore": vendor.get("vscore"),
        "vscore_tier": vendor.get("vscore_tier"),
    }
    # Fetch dimension scores from vscore_history (latest)
    vscore_hist_resp = (
        supabase.table("chamber_vscore_history")
        .select("dimension_scores")
        .eq("vendor_id", vendor_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    dimension_scores = {}
    if vscore_hist_resp.data:
        dimension_scores = vscore_hist_resp.data[0].get("dimension_scores") or {}
    vscore_data["dimension_scores"] = dimension_scores

    # ── 3. Trade license status ──
    trade_license = {
        "status": vendor.get("trade_license_status") or "unverified",
    }

    # ── 4. Best evaluation scores — top 3 proposals by composite_score ──
    proposals_resp = (
        supabase.table("chamber_proposals")
        .select("id, title, status, composite_score, sector, technology_type, submission_date")
        .eq("submitter_id", vendor_id)
        .order("composite_score", desc=True)
        .limit(3)
        .execute()
    )
    top_proposals = proposals_resp.data or []

    # Fetch evaluation detail for those proposals
    top_evaluations = []
    for prop in top_proposals:
        eval_resp = (
            supabase.table("chamber_evaluations")
            .select(
                "relevance_score, feasibility_score, sector_alignment_score, "
                "compliance_score, novelty_score, composite_score, summary_en"
            )
            .eq("proposal_id", prop["id"])
            .order("evaluated_at", desc=True)
            .limit(1)
            .execute()
        )
        ev = eval_resp.data[0] if eval_resp.data else {}
        top_evaluations.append({
            "proposal_title": prop.get("title"),
            "proposal_status": prop.get("status"),
            "sector": prop.get("sector"),
            "composite_score": ev.get("composite_score") or prop.get("composite_score"),
            "relevance": ev.get("relevance_score"),
            "feasibility": ev.get("feasibility_score"),
            "sector_alignment": ev.get("sector_alignment_score"),
            "compliance": ev.get("compliance_score"),
            "novelty": ev.get("novelty_score"),
        })

    # ── 5. Sourcing case context (if provided) ──
    sourcing_case_context = None
    if sourcing_case_id:
        case_resp = (
            supabase.table("chamber_sourcing_cases")
            .select("id, title, problem_statement, sector, technology_domain, urgency, compliance_tier")
            .eq("id", sourcing_case_id)
            .maybe_single()
            .execute()
        )
        if case_resp.data:
            sourcing_case_context = case_resp.data

    # ── 6. Pilot history ──
    pilots_resp = (
        supabase.table("chamber_pilots")
        .select("id, title, status, outcome_rating, adoption_decision, start_date, end_date")
        .eq("vendor_id", vendor_id)
        .order("created_at", desc=True)
        .execute()
    )
    pilots = pilots_resp.data or []

    # ── 7. AI-generated executive summary ──
    system_prompt = (
        "You are an analyst at Dubai Chambers. Write a 3-sentence executive overview "
        "of the vendor's strengths and fit for chamber sourcing. Be specific, cite scores "
        "and outcomes where available. Output ONLY the 3 sentences, no preamble."
    )

    user_prompt_parts = [
        f"Vendor: {vendor.get('name')} — {vendor.get('country')}",
        f"Sector certifications: {profile.get('certifications') or 'N/A'}",
        f"vScore: {vscore_data.get('vscore') or 'N/A'} ({vscore_data.get('vscore_tier') or 'N/A'})",
        f"DESC approved: {vendor.get('is_desc_approved')}",
        f"Trade license: {trade_license.get('status')}",
    ]

    if top_evaluations:
        best = top_evaluations[0]
        user_prompt_parts.append(
            f"Best evaluation composite: {best.get('composite_score')}/100 "
            f"(Relevance={best.get('relevance')}, Feasibility={best.get('feasibility')}, "
            f"Compliance={best.get('compliance')})"
        )

    completed_pilots = [p for p in pilots if p.get("status") == "completed"]
    if completed_pilots:
        ratings = [p["outcome_rating"] for p in completed_pilots if p.get("outcome_rating")]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        adopted = sum(1 for p in completed_pilots if p.get("adoption_decision") == "adopt")
        user_prompt_parts.append(
            f"Completed pilots: {len(completed_pilots)}, avg rating: {avg_rating}/5, adopted: {adopted}"
        )

    if sourcing_case_context:
        user_prompt_parts.append(
            f"Sourcing case context: {sourcing_case_context.get('title')} — "
            f"{sourcing_case_context.get('problem_statement', '')[:300]}"
        )

    user_prompt = "\n".join(user_prompt_parts)

    start_ms = time.time()
    ai_summary = await ai_complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=512,
    )
    latency_ms = int((time.time() - start_ms) * 1000)

    # Rough token estimates
    prompt_tokens = len(user_prompt.split()) + len(system_prompt.split())
    completion_tokens = len(ai_summary.split())
    total_tokens = prompt_tokens + completion_tokens
    cost_usd = round(prompt_tokens * PROMPT_COST_PER_TOKEN + completion_tokens * COMPLETION_COST_PER_TOKEN, 6)
    energy_kwh = round(total_tokens * ENERGY_PER_TOKEN, 6)
    carbon_gco2 = round(energy_kwh * CARBON_PER_KWH, 4)
    intelligence_units = round(total_tokens * 0.001, 4)

    # Log AI interaction
    session_id = uuid.uuid4()
    try:
        ai_interaction_service.create(
            user_id=generated_by,
            session_id=session_id,
            model_name="claude-sonnet-4-5-20250929",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            energy_kwh=energy_kwh,
            carbon_gco2=carbon_gco2,
            intelligence_units=intelligence_units,
            operation_type="factsheet_generation",
        )
    except Exception as log_err:
        logger.warning("Failed to log AI interaction for factsheet: %s", log_err)

    # ── Build content payload ──
    content = {
        "vendor": {
            "id": vendor.get("id"),
            "name": vendor.get("name"),
            "country": vendor.get("country"),
            "contact_email": vendor.get("contact_email"),
            "website": vendor.get("website"),
            "sector": profile.get("technology_stack"),
            "team_size": profile.get("team_size"),
            "funding_stage": profile.get("funding_stage"),
            "certifications": profile.get("certifications"),
        },
        "desc_status": {
            "approved": vendor.get("is_desc_approved", False),
            "certified": bool(vendor.get("desc_certified_provider_id")) or vendor.get("is_desc_approved", False),
            "certification_level": vendor.get("desc_certification_level"),
            "badge_issued_date": vendor.get("desc_badge_issued_date"),
        },
        "trade_license": trade_license,
        "vscore": vscore_data,
        "top_evaluations": top_evaluations,
        "pilots": [
            {
                "title": p.get("title"),
                "status": p.get("status"),
                "outcome_rating": p.get("outcome_rating"),
                "adoption_decision": p.get("adoption_decision"),
                "start_date": p.get("start_date"),
                "end_date": p.get("end_date"),
            }
            for p in pilots
        ],
        "sourcing_case_context": sourcing_case_context,
    }

    # ── Persist ──
    insert_payload = {
        "vendor_id": vendor_id,
        "content": json.dumps(content),
        "ai_summary": ai_summary,
        "generated_by": generated_by,
    }
    if sourcing_case_id:
        insert_payload["sourcing_case_id"] = sourcing_case_id

    insert_resp = supabase.table("chamber_vendor_factsheets").insert(insert_payload).execute()
    row = insert_resp.data[0] if insert_resp.data else {}

    return {
        "id": row.get("id"),
        "vendor_id": vendor_id,
        "sourcing_case_id": sourcing_case_id,
        "content": content,
        "ai_summary": ai_summary,
        "generated_by": generated_by,
        "created_at": row.get("created_at"),
    }

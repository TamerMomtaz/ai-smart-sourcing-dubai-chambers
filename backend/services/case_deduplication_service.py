"""Service layer for Sourcing Case deduplication detection."""
import json
import logging
import time
from typing import List, Dict, Any, Optional
from uuid import uuid4

from database import supabase
from services.ai_provider import ai_complete
from services import ai_interaction_service

logger = logging.getLogger(__name__)

DEDUPLICATION_SYSTEM_PROMPT = """You are a deduplication analyst for Dubai Chambers' innovation sourcing platform.
You compare a NEW sourcing case against EXISTING sourcing cases to detect potential duplicates.

Evaluate similarity across these dimensions:
1. Semantic similarity of problem statements (most important — 50% weight)
2. Sector and technology domain overlap (30% weight)
3. Requesting entity similarity (20% weight)

For each existing case, return a similarity score (0-100) and brief reasoning.

Return JSON only:
{
  "matches": [
    {
      "case_id": "the existing case id",
      "similarity_score": 85,
      "reasoning": "brief explanation of why these cases are similar or different"
    }
  ],
  "recommendation": "merge | proceed | review"
}

Recommendation rules:
- "merge": if any match has similarity >= 85
- "review": if any match has similarity >= 60
- "proceed": if all matches have similarity < 60

Return ONLY valid JSON, no markdown fences or extra text."""


async def check_duplicates(
    *,
    title: str,
    problem_statement: str,
    sector: Optional[str] = None,
    technology_domain: Optional[str] = None,
    user_id: str,
) -> Dict[str, Any]:
    """
    Check if a new sourcing case is a potential duplicate of existing ones.
    Uses AI to compare semantic similarity of problem statements.
    """
    # Query open/matching/evaluating sourcing cases
    active_statuses = ["intake", "open", "matching", "evaluating", "shortlisted"]
    existing_cases = []
    for s in active_statuses:
        result = (
            supabase.table("chamber_sourcing_cases")
            .select("id, title, problem_statement, sector, technology_domain, requesting_entity, source_channel, status, created_at")
            .eq("status", s)
            .execute()
        )
        if result.data:
            existing_cases.extend(result.data)

    if not existing_cases:
        return {
            "duplicates_found": False,
            "matches": [],
            "recommendation": "proceed",
        }

    # Build the comparison prompt
    new_case_text = (
        f"Title: {title}\n"
        f"Problem Statement: {problem_statement}\n"
        f"Sector: {sector or 'Not specified'}\n"
        f"Technology Domain: {technology_domain or 'Not specified'}"
    )

    existing_cases_text = ""
    for c in existing_cases:
        existing_cases_text += (
            f"\n---\nCase ID: {c['id']}\n"
            f"Title: {c['title']}\n"
            f"Problem Statement: {c.get('problem_statement', 'N/A')}\n"
            f"Sector: {c.get('sector', 'N/A')}\n"
            f"Technology Domain: {c.get('technology_domain', 'N/A')}\n"
            f"Requesting Entity: {c.get('requesting_entity', 'N/A')}\n"
            f"Source Channel: {c.get('source_channel', 'N/A')}\n"
            f"Status: {c['status']}\n"
        )

    user_prompt = (
        f"NEW CASE:\n{new_case_text}\n\n"
        f"EXISTING CASES:{existing_cases_text}"
    )

    start_time = time.time()
    try:
        ai_response = await ai_complete(
            system_prompt=DEDUPLICATION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=4096,
        )
    except Exception as e:
        logger.error(f"AI deduplication check failed: {e}")
        # Return empty result on AI failure rather than blocking case creation
        return {
            "duplicates_found": False,
            "matches": [],
            "recommendation": "proceed",
        }
    latency_ms = int((time.time() - start_time) * 1000)

    # Parse AI response
    try:
        cleaned = ai_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse AI deduplication response: {e}\nResponse: {ai_response}")
        return {
            "duplicates_found": False,
            "matches": [],
            "recommendation": "proceed",
        }

    # Build enriched matches with case metadata
    case_lookup = {str(c["id"]): c for c in existing_cases}
    matches = []
    duplicates_found = False

    for m in parsed.get("matches", []):
        case_id = str(m.get("case_id", ""))
        score = m.get("similarity_score", 0)
        if score < 40:
            continue  # Skip low-similarity matches

        case_data = case_lookup.get(case_id, {})
        if not case_data:
            continue

        if score >= 60:
            duplicates_found = True

        matches.append({
            "case_id": case_id,
            "title": case_data.get("title", ""),
            "similarity_score": score,
            "reasoning": m.get("reasoning", ""),
            "source_channel": case_data.get("source_channel", ""),
            "status": case_data.get("status", ""),
            "sector": case_data.get("sector", ""),
            "technology_domain": case_data.get("technology_domain", ""),
        })

    # Sort by similarity score descending
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)

    recommendation = parsed.get("recommendation", "proceed")
    # Validate recommendation
    if recommendation not in ("merge", "proceed", "review"):
        recommendation = "review" if duplicates_found else "proceed"

    # Log to chamber_ai_interactions
    prompt_tokens = len(user_prompt.split()) + len(DEDUPLICATION_SYSTEM_PROMPT.split())
    completion_tokens = len(ai_response.split())

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
            operation_type="deduplication_check",
        )
    except Exception as e:
        logger.warning(f"Failed to log AI interaction for deduplication: {e}")

    return {
        "duplicates_found": duplicates_found,
        "matches": matches,
        "recommendation": recommendation,
    }


async def scan_all_open_cases(*, user_id: str) -> Dict[str, Any]:
    """
    Scan all open sourcing cases for potential overlaps among themselves.
    Returns groups of cases that may be duplicates.
    """
    active_statuses = ["intake", "open", "matching", "evaluating", "shortlisted"]
    all_cases = []
    for s in active_statuses:
        result = (
            supabase.table("chamber_sourcing_cases")
            .select("id, title, problem_statement, sector, technology_domain, requesting_entity, source_channel, status")
            .eq("status", s)
            .execute()
        )
        if result.data:
            all_cases.extend(result.data)

    if len(all_cases) < 2:
        return {"groups": [], "total_cases_scanned": len(all_cases)}

    # Build prompt for batch comparison
    cases_text = ""
    for c in all_cases:
        cases_text += (
            f"\n---\nCase ID: {c['id']}\n"
            f"Title: {c['title']}\n"
            f"Problem Statement: {c.get('problem_statement', 'N/A')}\n"
            f"Sector: {c.get('sector', 'N/A')}\n"
            f"Technology Domain: {c.get('technology_domain', 'N/A')}\n"
            f"Source Channel: {c.get('source_channel', 'N/A')}\n"
        )

    scan_system_prompt = """You are a deduplication analyst for Dubai Chambers.
Analyze ALL the sourcing cases below and identify groups of cases that appear to be duplicates or near-duplicates.

Compare across: problem statement semantics, sector, technology domain.

Return JSON only:
{
  "groups": [
    {
      "case_ids": ["id1", "id2"],
      "similarity_score": 85,
      "reasoning": "why these cases overlap"
    }
  ]
}

Only include groups with similarity >= 60. Return ONLY valid JSON, no markdown fences."""

    start_time = time.time()
    try:
        ai_response = await ai_complete(
            system_prompt=scan_system_prompt,
            user_prompt=f"CASES TO ANALYZE:{cases_text}",
            max_tokens=4096,
        )
    except Exception as e:
        logger.error(f"AI batch deduplication scan failed: {e}")
        return {"groups": [], "total_cases_scanned": len(all_cases)}
    latency_ms = int((time.time() - start_time) * 1000)

    try:
        cleaned = ai_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse AI scan response: {e}")
        return {"groups": [], "total_cases_scanned": len(all_cases)}

    # Enrich groups with case titles
    case_lookup = {str(c["id"]): c for c in all_cases}
    enriched_groups = []
    for group in parsed.get("groups", []):
        cases_in_group = []
        for cid in group.get("case_ids", []):
            case_data = case_lookup.get(str(cid))
            if case_data:
                cases_in_group.append({
                    "case_id": str(cid),
                    "title": case_data.get("title", ""),
                    "sector": case_data.get("sector", ""),
                    "source_channel": case_data.get("source_channel", ""),
                    "status": case_data.get("status", ""),
                })
        if len(cases_in_group) >= 2:
            enriched_groups.append({
                "cases": cases_in_group,
                "similarity_score": group.get("similarity_score", 0),
                "reasoning": group.get("reasoning", ""),
            })

    # Log AI interaction
    prompt_tokens = len(cases_text.split()) + len(scan_system_prompt.split())
    completion_tokens = len(ai_response.split())
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
            operation_type="deduplication_check",
        )
    except Exception as e:
        logger.warning(f"Failed to log AI interaction for scan: {e}")

    return {
        "groups": enriched_groups,
        "total_cases_scanned": len(all_cases),
    }

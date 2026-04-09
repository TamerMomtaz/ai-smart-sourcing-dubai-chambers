"""Routes for Sourcing Case Engine."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
import logging
import json
import time

from auth import get_current_user
from services import sourcing_case_service
from services.ai_provider import ai_complete
from services import ai_interaction_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sourcing-cases", tags=["Sourcing Cases"])


class SourcingCaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    problem_statement: str = Field(..., min_length=1)
    requesting_entity: Optional[str] = None
    business_group_id: Optional[str] = None
    sector: Optional[str] = None
    technology_domain: Optional[str] = None
    urgency: Optional[str] = Field(default="medium")
    compliance_tier: Optional[str] = Field(default="standard", pattern="^(open|standard|government|critical)$")
    compliance_requirements: Optional[str] = None
    assigned_analyst_id: Optional[str] = None


class SourcingCaseStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(intake|open|matching|evaluating|shortlisted|pilot|completed|closed)$")


class AIStructureRequest(BaseModel):
    raw_text: str = Field(..., min_length=10, max_length=10000)


class AIStructureResponse(BaseModel):
    suggested_title: str
    problem_statement: str
    sector: str
    technology_domain: str
    urgency: str
    compliance_flags: List[str]
    reasoning: str


AI_STRUCTURE_SYSTEM_PROMPT = """You are an innovation sourcing analyst for Dubai Chambers.
Analyze this raw request and extract structured fields.
Return JSON only:
{
  "suggested_title": "concise title for the sourcing case",
  "problem_statement": "structured problem statement describing the need",
  "sector": "one of: FinTech, Healthcare, Logistics, Energy, Education, Government, Tourism, Cybersecurity, AI/ML, Smart City, Real Estate, Retail, Manufacturing, Agriculture, Media",
  "technology_domain": "primary technology area (e.g. AI/ML, IoT, Blockchain, Cloud, Cybersecurity, Data Analytics, Robotics)",
  "urgency": "low|medium|high|critical",
  "compliance_flags": ["list of applicable compliance considerations, e.g. DESC required, UAE data residency, GDPR, ISO 27001"],
  "reasoning": "brief explanation of your classification decisions"
}
Return ONLY valid JSON, no markdown fences or extra text."""


@router.post(
    "/ai-structure",
    status_code=status.HTTP_200_OK,
)
async def ai_structure_raw_text(
    payload: AIStructureRequest,
    current_user: dict = Depends(get_current_user),
):
    """Use AI to extract structured sourcing case fields from raw text."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin and analyst roles can use AI structuring",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    start_time = time.time()
    try:
        ai_response = await ai_complete(
            system_prompt=AI_STRUCTURE_SYSTEM_PROMPT,
            user_prompt=payload.raw_text,
            max_tokens=2048,
        )
    except Exception as e:
        logger.error(f"AI structuring failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "AI Service Error",
                "detail": "All AI providers failed to process the request",
                "code": "AI_PROVIDERS_FAILED",
            },
        )
    latency_ms = int((time.time() - start_time) * 1000)

    # Parse the AI response JSON
    try:
        # Strip markdown fences if present
        cleaned = ai_response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        structured = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse AI response as JSON: {e}\nResponse: {ai_response}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "AI Parse Error",
                "detail": "AI response was not valid JSON",
                "code": "AI_PARSE_FAILED",
            },
        )

    # Validate urgency value
    valid_urgencies = ["low", "medium", "high", "critical"]
    if structured.get("urgency", "").lower() not in valid_urgencies:
        structured["urgency"] = "medium"
    else:
        structured["urgency"] = structured["urgency"].lower()

    # Ensure compliance_flags is a list
    if not isinstance(structured.get("compliance_flags"), list):
        structured["compliance_flags"] = []

    # Log to chamber_ai_interactions (σI tracking)
    # Estimate token counts from text lengths
    prompt_tokens = len(payload.raw_text.split()) + len(AI_STRUCTURE_SYSTEM_PROMPT.split())
    completion_tokens = len(ai_response.split())

    try:
        ai_interaction_service.create(
            user_id=current_user["id"],
            session_id=uuid4(),
            model_name="claude-sonnet-4-5-20250929",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=round(prompt_tokens * 0.000003 + completion_tokens * 0.000015, 6),
            energy_kwh=round(latency_ms * 0.0000003, 6),
            carbon_gco2=round(latency_ms * 0.0000001, 6),
            intelligence_units=round((prompt_tokens + completion_tokens) * 0.001, 4),
            operation_type="extraction",
        )
    except Exception as e:
        logger.warning(f"Failed to log AI interaction: {e}")

    return {
        "suggested_title": structured.get("suggested_title", ""),
        "problem_statement": structured.get("problem_statement", ""),
        "sector": structured.get("sector", ""),
        "technology_domain": structured.get("technology_domain", ""),
        "urgency": structured.get("urgency", "medium"),
        "compliance_flags": structured.get("compliance_flags", []),
        "reasoning": structured.get("reasoning", ""),
    }


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_sourcing_case(
    payload: SourcingCaseCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new sourcing case (admin/analyst only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin and analyst roles can create sourcing cases",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = sourcing_case_service.create_sourcing_case(
        title=payload.title.strip(),
        problem_statement=payload.problem_statement.strip(),
        requesting_entity=payload.requesting_entity.strip() if payload.requesting_entity else None,
        business_group_id=payload.business_group_id,
        sector=payload.sector.strip() if payload.sector else None,
        technology_domain=payload.technology_domain.strip() if payload.technology_domain else None,
        urgency=payload.urgency or "medium",
        compliance_tier=payload.compliance_tier or "standard",
        compliance_requirements=payload.compliance_requirements.strip() if payload.compliance_requirements else None,
        assigned_analyst_id=payload.assigned_analyst_id,
        created_by=str(current_user["id"]),
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalError",
                "detail": "Failed to create sourcing case",
                "code": "CREATE_FAILED",
            },
        )

    return result


@router.get("")
async def list_sourcing_cases(
    status_filter: Optional[str] = Query(None, alias="status"),
    sector: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    source_channel: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    current_user: dict = Depends(get_current_user),
):
    """List all sourcing cases with filters."""
    cases = sourcing_case_service.list_sourcing_cases(
        status_filter=status_filter,
        sector_filter=sector,
        urgency_filter=urgency,
        source_channel_filter=source_channel,
        sort_by=sort_by or "created_at",
    )
    return {"sourcing_cases": cases}


@router.get("/{case_id}")
async def get_sourcing_case(
    case_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get full sourcing case detail including linked proposals."""
    result = sourcing_case_service.get_sourcing_case(case_id=str(case_id))
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Sourcing case not found",
                "code": "CASE_NOT_FOUND",
            },
        )
    return result


@router.put("/{case_id}/status")
async def update_sourcing_case_status(
    case_id: UUID,
    payload: SourcingCaseStatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update sourcing case status (admin/analyst only)."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin and analyst roles can update sourcing case status",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    result = sourcing_case_service.update_sourcing_case_status(
        case_id=str(case_id),
        new_status=payload.status,
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Sourcing case not found",
                "code": "CASE_NOT_FOUND",
            },
        )
    return result


@router.get("/{case_id}/compare-proposals")
async def compare_proposals(
    case_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get all proposals linked to a sourcing case with evaluation data for comparison."""
    result = sourcing_case_service.get_compare_proposals(case_id=str(case_id))
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Sourcing case not found",
                "code": "CASE_NOT_FOUND",
            },
        )
    return result


class AIComparisonRequest(BaseModel):
    proposal_ids: List[str] = Field(..., min_length=2, max_length=4)


@router.post("/{case_id}/compare-proposals/ai-summary")
async def ai_comparison_summary(
    case_id: UUID,
    payload: AIComparisonRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate an AI comparison summary for selected proposals within a sourcing case."""
    user_role = current_user.get("role", "").strip()
    allowed_roles = ["admin", "analyst", "executive", "business_group_lead"]
    if user_role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Insufficient permissions for AI comparison",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    # Fetch case + proposal data
    compare_data = sourcing_case_service.get_compare_proposals(case_id=str(case_id))
    if compare_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "NotFound",
                "detail": "Sourcing case not found",
                "code": "CASE_NOT_FOUND",
            },
        )

    case_info = compare_data["case"]
    all_proposals = compare_data["proposals"]

    # Filter to only selected proposals
    selected = [p for p in all_proposals if p["id"] in payload.proposal_ids]
    if len(selected) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "BadRequest",
                "detail": "At least 2 valid proposal IDs required from this sourcing case",
                "code": "INSUFFICIENT_PROPOSALS",
            },
        )

    # Build AI prompt
    proposals_text = ""
    for i, p in enumerate(selected, 1):
        proposals_text += f"""
Proposal {i}: "{p['title']}" by {p['vendor_name']}
- Composite Score: {p.get('composite_score', 'N/A')}
- Relevance: {p.get('relevance_score', 'N/A')}
- Feasibility: {p.get('feasibility_score', 'N/A')}
- Sector Alignment: {p.get('sector_alignment_score', 'N/A')}
- Compliance: {p.get('compliance_score', 'N/A')}
- Innovation: {p.get('innovation_score', 'N/A')}
- Compliance Gate: {p.get('gate_status', 'N/A')}
- Evidence Grounding: {p.get('grounding_score', 'N/A')}
- Vendor vScore: {p.get('vscore', 'N/A')} ({p.get('vscore_tier', 'N/A')})
"""

    system_prompt = """You are an AI sourcing analyst for Dubai Chambers.
Compare the given proposals and provide a concise 2-paragraph summary.
Paragraph 1: Compare strengths and weaknesses across all evaluation dimensions.
Paragraph 2: Recommend the strongest match and explain why, considering all dimensions.
Be specific, data-driven, and reference actual scores. Keep it professional and concise."""

    user_prompt = f"""Given these {len(selected)} proposals for sourcing case "{case_info['title']}":
Problem Statement: {case_info.get('problem_statement', 'N/A')}
Sector: {case_info.get('sector', 'N/A')}
{proposals_text}
Which is the strongest match and why? Consider all dimensions."""

    start_time = time.time()
    try:
        ai_response = await ai_complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1024,
        )
    except Exception as e:
        logger.error(f"AI comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "AI Service Error",
                "detail": "All AI providers failed to process the request",
                "code": "AI_PROVIDERS_FAILED",
            },
        )
    latency_ms = int((time.time() - start_time) * 1000)

    # Log to chamber_ai_interactions
    prompt_tokens = len(user_prompt.split()) + len(system_prompt.split())
    completion_tokens = len(ai_response.split())
    try:
        ai_interaction_service.create(
            user_id=current_user["id"],
            session_id=uuid4(),
            model_name="claude-sonnet-4-5-20250929",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency_ms,
            cost_usd=round(prompt_tokens * 0.000003 + completion_tokens * 0.000015, 6),
            energy_kwh=round(latency_ms * 0.0000003, 6),
            carbon_gco2=round(latency_ms * 0.0000001, 6),
            intelligence_units=round((prompt_tokens + completion_tokens) * 0.001, 4),
            operation_type="proposal_evaluation",
        )
    except Exception as e:
        logger.warning(f"Failed to log AI interaction: {e}")

    return {
        "case_id": str(case_id),
        "case_title": case_info["title"],
        "proposals_compared": len(selected),
        "proposal_ids": [p["id"] for p in selected],
        "summary": ai_response,
    }

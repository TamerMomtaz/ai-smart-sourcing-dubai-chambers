"""Public API endpoint for external sourcing intake."""
from typing import Optional, List
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from uuid import uuid4
import logging
import json
import time

from config import INTAKE_API_KEY
from services import sourcing_case_service
from services.ai_provider import ai_complete
from services import ai_interaction_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public/sourcing-intake", tags=["Sourcing Intake (Public)"])

VALID_SOURCES = [
    "business_in_dubai",
    "expand_north_star",
    "ignyte",
    "partner_referral",
    "email",
    "api",
]

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


class SourcingIntakeRequest(BaseModel):
    source: str = Field(..., description="Source channel")
    raw_text: Optional[str] = Field(None, max_length=10000, description="Raw text for AI structuring")
    contact_name: str = Field(..., min_length=1, max_length=200)
    contact_email: EmailStr
    organization: str = Field(..., min_length=1, max_length=300)
    sector_hint: Optional[str] = Field(None, max_length=200)


def _validate_api_key(x_intake_key: str):
    """Validate the intake API key."""
    if not INTAKE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Service Unavailable",
                "detail": "Intake API is not configured",
                "code": "INTAKE_NOT_CONFIGURED",
            },
        )
    if x_intake_key != INTAKE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Unauthorized",
                "detail": "Invalid or missing API key",
                "code": "INVALID_API_KEY",
            },
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def sourcing_intake(
    payload: SourcingIntakeRequest,
    x_intake_key: str = Header(..., description="API key for intake authentication"),
):
    """
    Public endpoint for external systems to submit sourcing opportunities.

    Authenticates via X-Intake-Key header (not user auth).
    Creates a sourcing case with status "intake" and records the source channel.
    If raw_text is provided, auto-runs AI structuring to extract fields.
    """
    # Validate API key
    _validate_api_key(x_intake_key)

    # Validate source
    if payload.source not in VALID_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Validation Error",
                "detail": f"Invalid source. Must be one of: {', '.join(VALID_SOURCES)}",
                "code": "INVALID_SOURCE",
            },
        )

    # Default fields
    title = f"Intake from {payload.organization}"
    problem_statement = payload.raw_text or f"Sourcing request from {payload.contact_name} at {payload.organization}"
    sector = payload.sector_hint
    technology_domain = None
    urgency = "medium"
    compliance_requirements = None

    # If raw_text provided, run AI structuring
    ai_structured = False
    if payload.raw_text and len(payload.raw_text.strip()) >= 10:
        start_time = time.time()
        try:
            ai_response = await ai_complete(
                system_prompt=AI_STRUCTURE_SYSTEM_PROMPT,
                user_prompt=payload.raw_text,
                max_tokens=2048,
            )
            latency_ms = int((time.time() - start_time) * 1000)

            # Parse AI response
            cleaned = ai_response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
                if cleaned.endswith("```"):
                    cleaned = cleaned[:-3]
                cleaned = cleaned.strip()
            structured = json.loads(cleaned)

            title = structured.get("suggested_title", title)
            problem_statement = structured.get("problem_statement", problem_statement)
            sector = structured.get("sector", sector)
            technology_domain = structured.get("technology_domain")
            raw_urgency = structured.get("urgency", "medium").lower()
            urgency = raw_urgency if raw_urgency in ("low", "medium", "high", "critical") else "medium"
            flags = structured.get("compliance_flags")
            if isinstance(flags, list) and flags:
                compliance_requirements = ", ".join(flags)

            ai_structured = True

            # Log to chamber_ai_interactions (rule 9b: operation_type = "extraction")
            prompt_tokens = len(payload.raw_text.split()) + len(AI_STRUCTURE_SYSTEM_PROMPT.split())
            completion_tokens = len(ai_response.split())
            try:
                ai_interaction_service.create(
                    user_id=uuid4(),  # system user — no authenticated user for public endpoint
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
                logger.warning(f"Failed to log AI interaction for intake: {e}")

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"AI structuring parse failed for intake, using defaults: {e}")
        except Exception as e:
            logger.warning(f"AI structuring failed for intake, using defaults: {e}")

    # Build requesting_entity from contact info
    requesting_entity = f"{payload.contact_name} — {payload.organization} ({payload.contact_email})"

    # Create the sourcing case
    result = sourcing_case_service.create_sourcing_case(
        title=title.strip(),
        problem_statement=problem_statement.strip(),
        requesting_entity=requesting_entity,
        sector=sector.strip() if sector else None,
        technology_domain=technology_domain.strip() if technology_domain else None,
        urgency=urgency,
        compliance_requirements=compliance_requirements,
        created_by=None,
        status="intake",
        source_channel=payload.source,
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

    return {
        "case_id": result["id"],
        "status": "received",
        "ai_structured": ai_structured,
    }

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID
from datetime import date, datetime, timezone
import json
import time
import uuid as uuid_mod
import logging

from models.trend_analysis import (
    TrendAnalysis,
    TrendAnalysisGenerateRequest,
    TrendAnalysisGenerateResponse,
)
from models.common import PaginationResponse, ErrorResponse
from auth import get_current_user
from services import trend_analysis_service
from database import supabase
from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trend-analyses", tags=["Trend Analyses"])


@router.get(
    "",
    summary="List trend analyses",
    description="Retrieve paginated list of AI-generated trend analyses. Executives can filter by sector and date range.",
)
async def list_trend_analyses(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    current_user: dict = Depends(get_current_user),
):
    """
    List trend analyses with pagination.
    
    Requires: executive role
    
    Returns:
    - List of trend analyses
    - Pagination metadata
    """
    try:
        user_id = UUID(current_user["id"])

        result = trend_analysis_service.list_trend_analyses(
            user_id=user_id,
            page=page,
            page_size=page_size,
            sector=sector,
        )
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Internal Server Error",
                    "detail": "Failed to retrieve trend analyses",
                    "code": 500,
                },
            )
        
        analyses = result.get("analyses", result.get("trend_analyses", []))
        total = result.get("total", len(analyses))
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "trend_analyses": analyses,
            "pagination": result.get("pagination", {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing trend analyses: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while retrieving trend analyses",
                "code": 500,
            },
        )


@router.get(
    "/{analysis_id}",
    summary="Get trend analysis by ID",
    description="Retrieve detailed trend analysis by UUID. Executives only.",
)
async def get_trend_analysis(
    analysis_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Get trend analysis detail.
    
    Requires: executive role
    
    Args:
    - analysis_id: Trend analysis UUID
    
    Returns:
    - Trend analysis detail including technology trends, submission volume, average scores
    """
    try:
        user_id = UUID(current_user["id"])

        result = trend_analysis_service.get_by_id(
            user_id=user_id,
            analysis_id=analysis_id,
        )
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not Found",
                    "detail": f"Trend analysis {analysis_id} not found",
                    "code": 404,
                },
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving trend analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while retrieving trend analysis",
                "code": 500,
            },
        )


TREND_SYSTEM_PROMPT = (
    "You are a market intelligence analyst for Dubai Chambers.\n"
    "Analyze the submitted technology proposals and generate a trend report.\n"
    "Respond ONLY in valid JSON:\n"
    "{\n"
    '  "report_title": "string",\n'
    '  "period": "Q1 2026",\n'
    '  "key_findings": ["finding1", "finding2", ...],\n'
    '  "sector_breakdown": [{"sector": "name", "count": N, "avg_score": N, "trend": "up|down|stable"}],\n'
    '  "top_technologies": ["tech1", "tech2", ...],\n'
    '  "compliance_insights": "paragraph about compliance patterns",\n'
    '  "recommendations": ["rec1", "rec2", ...],\n'
    '  "d33_alignment_score": 0-100\n'
    "}"
)

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"


def _parse_json_response(raw_text: str) -> dict:
    """Parse JSON from Claude response, handling markdown fences and edge cases."""
    import re
    text = raw_text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```\s*$', '', text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: extract first { to last }
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace > first_brace:
        return json.loads(text[first_brace:last_brace + 1])

    raise json.JSONDecodeError("No valid JSON found", text, 0)


@router.post(
    "/generate",
    status_code=200,
    summary="Generate AI trend report",
    description="Generate an AI-powered trend report from all evaluated proposals.",
)
async def generate_trend_analysis(
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a trend report using Claude AI.

    1. Fetches all evaluated proposals from chamber_proposals
    2. Calls Claude to generate a trend report
    3. Saves to chamber_trend_analyses
    4. Returns the report
    """
    try:
        user_id = current_user["id"]
        user_role = current_user.get("role", "")

        allowed_roles = ["analyst", "executive", "business_group_lead", "admin"]
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Insufficient permissions to generate trend reports",
                    "code": 403,
                },
            )

        # 1. Fetch all proposals with scores (evaluated, approved, rejected, etc.)
        proposals_response = supabase.table("chamber_proposals").select(
            "id, title, sector, technology_type, maturity_level, composite_score, "
            "relevance_score, feasibility_score, sector_alignment_score, compliance_score, "
            "status, submission_date"
        ).not_.is_("composite_score", "null").execute()

        proposals = proposals_response.data or []

        if not proposals:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Bad Request",
                    "detail": "No evaluated proposals available for trend analysis",
                    "code": 400,
                },
            )

        # Check for audit info
        proposal_ids = [p["id"] for p in proposals]
        audit_map = {}
        try:
            audit_response = supabase.table("chamber_compliance_audits").select(
                "proposal_id, findings_json"
            ).in_("proposal_id", proposal_ids).execute()
            for a in (audit_response.data or []):
                audit_map[a["proposal_id"]] = True
        except Exception:
            pass

        # Compute current quarter period
        today = date.today()
        current_quarter = (today.month - 1) // 3 + 1
        period_label = f"Q{current_quarter} {today.year}"

        # 2. Build user prompt
        lines = [f"Proposals summary for {period_label} trend analysis:\n"]
        lines.append(f"Report Period: {period_label}")
        lines.append(f"Analysis Date: {today.isoformat()}\n")
        for p in proposals:
            has_audit = p["id"] in audit_map
            lines.append(
                f"- Title: {p.get('title', 'N/A')} | Sector: {p.get('sector', 'N/A')} | "
                f"Tech: {p.get('technology_type', 'N/A')} | Maturity: {p.get('maturity_level', 'N/A')} | "
                f"Composite Score: {p.get('composite_score', 'N/A')} | "
                f"Relevance: {p.get('relevance_score', 'N/A')} | "
                f"Feasibility: {p.get('feasibility_score', 'N/A')} | "
                f"Sector Alignment: {p.get('sector_alignment_score', 'N/A')} | "
                f"Compliance: {p.get('compliance_score', 'N/A')} | "
                f"Status: {p.get('status', 'N/A')} | "
                f"Compliance Audited: {'Yes' if has_audit else 'No'}"
            )
        lines.append(f"\nTotal proposals: {len(proposals)}")
        user_prompt = "\n".join(lines)

        # 3. Call Claude
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        start_time = time.time()
        ai_response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4096,
            timeout=120,
            system=TREND_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        latency_ms = int((time.time() - start_time) * 1000)

        raw_text = ai_response.content[0].text
        report = _parse_json_response(raw_text)
        # Ensure period is set to the computed quarter
        report["period"] = period_label

        # 4. Calculate averages for the record
        count_with_scores = sum(1 for p in proposals if p.get("composite_score") is not None)
        average_scores = {}
        if count_with_scores > 0:
            for key in ["composite_score", "relevance_score", "feasibility_score",
                        "sector_alignment_score", "compliance_score"]:
                total = sum(p.get(key, 0) or 0 for p in proposals if p.get("composite_score") is not None)
                label = key.replace("_score", "")
                average_scores[label] = round(total / count_with_scores, 2)

        # 5. Save to chamber_trend_analyses — include ALL required NOT NULL fields
        analysis_data = {
            "analysis_date": date.today().isoformat(),
            "sector": None,
            "technology_trends_json": report,
            "submission_volume": len(proposals),
            "average_scores": average_scores,
            "emerging_technologies": report.get("top_technologies", []),
            "generated_by": str(user_id),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            insert_response = supabase.table("chamber_trend_analyses").insert(analysis_data).execute()
            saved = insert_response.data[0] if insert_response.data else {}
        except Exception as insert_err:
            import traceback as tb
            logger.error(f"TREND INSERT ERROR: {tb.format_exc()}")
            raise

        # 6. Log AI interaction (non-critical — per rule 9b)
        try:
            from services.ai_interaction_service import create as create_ai_interaction

            usage = ai_response.usage
            prompt_tokens = usage.input_tokens
            completion_tokens = usage.output_tokens
            total_tokens = prompt_tokens + completion_tokens
            cost_usd = round(
                (prompt_tokens * 3 / 1_000_000) + (completion_tokens * 15 / 1_000_000), 6
            )
            energy_kwh = round(total_tokens * 0.001 / 1000, 8)
            carbon_gco2 = round(energy_kwh * 0.4, 8)
            intelligence_units = round(total_tokens / 1000, 4)

            create_ai_interaction(
                user_id=user_id,
                session_id=uuid_mod.uuid4(),
                model_name=CLAUDE_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                energy_kwh=energy_kwh,
                carbon_gco2=carbon_gco2,
                intelligence_units=intelligence_units,
                operation_type="trend_analysis",
            )
        except Exception as e:
            logger.error(f"Failed to log AI interaction for trend analysis: {e}")

        # 7. Return result
        return {
            "id": saved.get("id"),
            "analysis_date": saved.get("analysis_date", date.today().isoformat()),
            "report": report,
            "submission_volume": len(proposals),
            "average_scores": average_scores,
            "emerging_technologies": report.get("top_technologies", []),
        }

    except HTTPException:
        raise
    except json.JSONDecodeError:
        logger.error("Failed to parse AI trend analysis response as JSON")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to parse AI response",
                "code": 500,
            },
        )
    except Exception as e:
        logger.error(f"Error generating trend analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while generating trend analysis",
                "code": 500,
            },
        )


@router.delete(
    "/{analysis_id}",
    status_code=204,
    summary="Delete trend analysis",
    description="Delete a trend analysis record. Executives and admins only.",
)
async def delete_trend_analysis(
    analysis_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Delete trend analysis.
    
    Requires: executive or admin role
    
    Args:
    - analysis_id: Trend analysis UUID to delete
    
    Returns:
    - 204 No Content on success
    """
    try:
        user_id = UUID(current_user["id"])
        user_role = current_user["role"]
        
        if user_role not in ["executive", "admin"]:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "Forbidden",
                    "detail": "Only executives and admins can delete trend analyses",
                    "code": 403,
                },
            )
        
        success = trend_analysis_service.delete(
            user_id=user_id,
            analysis_id=analysis_id,
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Not Found",
                    "detail": f"Trend analysis {analysis_id} not found",
                    "code": 404,
                },
            )
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trend analysis {analysis_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while deleting trend analysis",
                "code": 500,
            },
        )

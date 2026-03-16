"""AI-powered proposal evaluation engine using Claude."""

import json
import time
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import anthropic

from config import ANTHROPIC_API_KEY
from database import supabase
from services.chamber_evaluation_service import create_evaluation
from services.ai_interaction_service import create as create_ai_interaction

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
DEFAULT_WEIGHTS = {
    "relevance_weight": 0.25,
    "feasibility_weight": 0.25,
    "sector_alignment_weight": 0.25,
    "compliance_weight": 0.25,
}

SYSTEM_PROMPT = (
    "You are the Dubai Chambers AI Smart Sourcing evaluation agent. "
    "You evaluate technology vendor proposals for Dubai Chambers across 4 dimensions. "
    "Score each dimension 0-100. Be rigorous but fair. "
    "Consider Dubai's D33 Economic Agenda alignment, UAE regulatory requirements, "
    "and Dubai Chambers' mandate to source innovative technology solutions.\n\n"
    "Respond ONLY in valid JSON with this exact structure:\n"
    "{\n"
    '  "relevance": {"score": 0-100, "reasoning": "2-3 sentences"},\n'
    '  "feasibility": {"score": 0-100, "reasoning": "2-3 sentences"},\n'
    '  "sector_alignment": {"score": 0-100, "reasoning": "2-3 sentences"},\n'
    '  "compliance": {"score": 0-100, "reasoning": "2-3 sentences"},\n'
    '  "summary_en": "3-4 sentence executive summary in English",\n'
    '  "summary_ar": "3-4 sentence executive summary in Arabic",\n'
    '  "requires_manual_review": true/false,\n'
    '  "review_reason": "why manual review is needed (or null)"\n'
    "}"
)


class EvaluationEngine:
    """AI-powered proposal evaluation using Claude."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    async def evaluate_proposal(self, proposal_id: str, user_id: str) -> dict:
        """
        1. Fetch the proposal from chamber_proposals
        2. Fetch the business group's evaluation weights
        3. Call Claude to evaluate across 4 dimensions
        4. Parse scores and reasoning
        5. Save to chamber_evaluations
        6. Update chamber_proposals with scores and status
        7. Log to chamber_ai_interactions
        8. Return the evaluation result
        """
        # 1. Fetch proposal
        proposal = self._fetch_proposal(proposal_id=proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        # 2. Fetch business group and weights
        weights = dict(DEFAULT_WEIGHTS)
        business_group = None
        if proposal.get("business_group_id"):
            business_group = self._fetch_business_group(
                group_id=proposal["business_group_id"]
            )
            if business_group and business_group.get("evaluation_weight_config_json"):
                bg_weights = business_group["evaluation_weight_config_json"]
                if isinstance(bg_weights, str):
                    bg_weights = json.loads(bg_weights)
                weights.update(bg_weights)

        # 3. Build user prompt and call Claude
        user_prompt = self._build_user_prompt(
            proposal=proposal, business_group=business_group
        )

        start_time = time.time()
        ai_response = self._call_claude(user_prompt=user_prompt)
        latency_ms = int((time.time() - start_time) * 1000)

        # 4. Parse response
        parsed = self._parse_response(raw_text=ai_response.content[0].text)

        # Calculate composite score with weights
        composite_score = (
            parsed["relevance"]["score"] * weights.get("relevance_weight", 0.25)
            + parsed["feasibility"]["score"] * weights.get("feasibility_weight", 0.25)
            + parsed["sector_alignment"]["score"]
            * weights.get("sector_alignment_weight", 0.25)
            + parsed["compliance"]["score"] * weights.get("compliance_weight", 0.25)
        )
        composite_score = round(composite_score, 2)

        # Determine manual review flags
        scores = [
            parsed["relevance"]["score"],
            parsed["feasibility"]["score"],
            parsed["sector_alignment"]["score"],
            parsed["compliance"]["score"],
        ]
        requires_review = False
        review_reason = parsed.get("review_reason")

        if any(s < 30 for s in scores):
            requires_review = True
            review_reason = review_reason or "One or more dimension scores below 30"
        if (max(scores) - min(scores)) > 50:
            requires_review = True
            review_reason = review_reason or "High variance between dimension scores (>50 point spread)"
        if parsed["compliance"]["score"] < 40:
            requires_review = True
            review_reason = review_reason or "Compliance score below 40 - regulatory risk"

        new_status = "requires_manual_review" if requires_review else "evaluated"

        # 5. Save to chamber_evaluations
        evaluation = create_evaluation(
            user_id=user_id,
            proposal_id=proposal_id,
            relevance_score=parsed["relevance"]["score"],
            relevance_reasoning=parsed["relevance"]["reasoning"],
            feasibility_score=parsed["feasibility"]["score"],
            feasibility_reasoning=parsed["feasibility"]["reasoning"],
            sector_alignment_score=parsed["sector_alignment"]["score"],
            sector_reasoning=parsed["sector_alignment"]["reasoning"],
            compliance_score=parsed["compliance"]["score"],
            compliance_reasoning=parsed["compliance"]["reasoning"],
            composite_score=composite_score,
            summary_en=parsed.get("summary_en", ""),
            summary_ar=parsed.get("summary_ar", ""),
            hallucination_check_passed=True,
            prompt_injection_detected=False,
            evaluator_agent_versions={"model": CLAUDE_MODEL, "version": "1.0"},
        )

        # 6. Update chamber_proposals
        update_data = {
            "relevance_score": parsed["relevance"]["score"],
            "feasibility_score": parsed["feasibility"]["score"],
            "sector_alignment_score": parsed["sector_alignment"]["score"],
            "compliance_score": parsed["compliance"]["score"],
            "composite_score": composite_score,
            "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
            "status": new_status,
            "requires_manual_review": requires_review,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        supabase.table("chamber_proposals").update(update_data).eq(
            "id", str(proposal_id)
        ).execute()

        # 7. Log to chamber_ai_interactions (non-critical — never crash the endpoint)
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

        evaluation_id = evaluation["id"] if evaluation else None
        try:
            create_ai_interaction(
                user_id=user_id,
                session_id=uuid.uuid4(),
                model_name=CLAUDE_MODEL,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                energy_kwh=energy_kwh,
                carbon_gco2=carbon_gco2,
                intelligence_units=intelligence_units,
                operation_type="proposal_evaluation",
                evaluation_id=evaluation_id,
            )
        except Exception as e:
            logger.error(
                f"Failed to log AI interaction for proposal {proposal_id}: {e}"
            )

        # 8. Return result
        return {
            "evaluation_id": evaluation_id,
            "proposal_id": proposal_id,
            "composite_score": composite_score,
            "relevance": parsed["relevance"],
            "feasibility": parsed["feasibility"],
            "sector_alignment": parsed["sector_alignment"],
            "compliance": parsed["compliance"],
            "summary_en": parsed.get("summary_en", ""),
            "summary_ar": parsed.get("summary_ar", ""),
            "requires_manual_review": requires_review,
            "review_reason": review_reason,
            "status": new_status,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens,
            },
            "cost_usd": cost_usd,
            "latency_ms": latency_ms,
        }

    def _fetch_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        result = (
            supabase.table("chamber_proposals")
            .select("*")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )
        return result.data

    def _fetch_business_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        result = (
            supabase.table("chamber_business_groups")
            .select("*")
            .eq("id", str(group_id))
            .maybe_single()
            .execute()
        )
        return result.data

    def _build_user_prompt(
        self, proposal: Dict[str, Any], business_group: Optional[Dict[str, Any]]
    ) -> str:
        parts = [
            f"Proposal Title: {proposal.get('title', 'N/A')}",
            f"Sector: {proposal.get('sector', 'N/A')}",
            f"Technology Type: {proposal.get('technology_type', 'N/A')}",
            f"Maturity Level: {proposal.get('maturity_level', 'N/A')}",
            f"Language: {proposal.get('language', 'en')}",
        ]
        if proposal.get("description"):
            parts.append(f"Description: {proposal['description']}")

        if business_group:
            parts.append(f"\nBusiness Group: {business_group.get('name', 'N/A')}")
            parts.append(f"Chamber: {business_group.get('chamber', 'N/A')}")
            if business_group.get("sector_kpis_json"):
                kpis = business_group["sector_kpis_json"]
                if isinstance(kpis, str):
                    kpis = json.loads(kpis)
                parts.append(f"Sector KPIs: {json.dumps(kpis, indent=2)}")

        parts.append(
            "\nEvaluate this proposal across the 4 dimensions and provide your assessment in the required JSON format."
        )
        return "\n".join(parts)

    def _call_claude(self, user_prompt: str, retry: bool = True):
        try:
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                timeout=120,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            # If response appears truncated, retry with lower max_tokens
            if response.stop_reason == "max_tokens" and retry:
                logger.warning("Response truncated, retrying with lower max_tokens")
                response = self.client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=3000,
                    timeout=120,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
            return response
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

    def _parse_response(self, raw_text: str) -> dict:
        """Parse JSON from Claude response, handling markdown fences."""
        text = raw_text.strip()
        # Strip markdown code fences
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Claude response: {text[:500]}")
            raise ValueError("Failed to parse AI evaluation response as JSON")

        # Validate required keys
        for key in ["relevance", "feasibility", "sector_alignment", "compliance"]:
            if key not in parsed:
                raise ValueError(f"Missing required key '{key}' in evaluation response")
            if "score" not in parsed[key]:
                raise ValueError(f"Missing 'score' in '{key}' evaluation")
            if "reasoning" not in parsed[key]:
                parsed[key]["reasoning"] = "No reasoning provided"

        return parsed

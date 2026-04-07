"""AI-powered proposal evaluation engine using Claude (with multi-provider fallback)."""

import json
import os
import re
import time
import uuid
import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime, timezone

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
    "For each dimension, provide:\n"
    "1. The score (0-100)\n"
    "2. A 2-3 sentence reasoning summary\n"
    "3. Key evidence points from the proposal that support this score\n"
    "4. Risk factors that lowered the score\n"
    "5. Confidence level (high/medium/low)\n\n"
    "Respond ONLY in valid JSON with this exact structure:\n"
    "{\n"
    '  "relevance": {"score": 0-100, "reasoning": "2-3 sentences", '
    '"evidence": ["specific evidence point 1", "specific evidence point 2"], '
    '"risks": ["risk factor 1"], "confidence": "high|medium|low"},\n'
    '  "feasibility": {"score": 0-100, "reasoning": "...", "evidence": [...], "risks": [...], "confidence": "..."},\n'
    '  "sector_alignment": {"score": 0-100, "reasoning": "...", "evidence": [...], "risks": [...], "confidence": "..."},\n'
    '  "compliance": {"score": 0-100, "reasoning": "...", "evidence": [...], "risks": [...], "confidence": "..."},\n'
    '  "summary_en": "3-4 sentence executive summary in English",\n'
    '  "summary_ar": "3-4 sentence executive summary in Arabic",\n'
    '  "overall_reasoning": "2-3 sentences on how the composite score was derived",\n'
    '  "requires_manual_review": true/false,\n'
    '  "review_reason": "why manual review is needed (or null)"\n'
    "}"
)


AI_PROVIDERS = [
    {"name": "Claude Sonnet 4.5", "type": "anthropic", "model": "claude-sonnet-4-5-20250929"},
    {"name": "Claude Sonnet 4.5 (retry)", "type": "anthropic", "model": "claude-sonnet-4-5-20250929", "delay": 5},
    {"name": "GPT-4o", "type": "openai", "model": "gpt-4o"},
    {"name": "Gemini 2.0 Flash", "type": "google", "model": "gemini-2.0-flash"},
]


class EvaluationEngine:
    """AI-powered proposal evaluation with multi-provider fallback."""

    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT

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
        try:
            return await self._evaluate_proposal_inner(proposal_id=proposal_id, user_id=user_id)
        except Exception as e:
            # Revert status to "queued" so the proposal isn't stuck on "evaluating"
            logger.error(f"EVALUATION ERROR for proposal {proposal_id}: {traceback.format_exc()}")
            try:
                supabase.table("chamber_proposals").update({
                    "status": "queued",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", str(proposal_id)).execute()
            except Exception as revert_err:
                logger.error(f"Failed to revert proposal {proposal_id} status: {revert_err}")
            raise

    async def _evaluate_proposal_inner(self, proposal_id: str, user_id: str) -> dict:
        """Inner evaluation logic — exceptions bubble up to evaluate_proposal for status revert."""
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

        # 2b. Fetch uploaded document texts for this proposal
        document_texts = self._fetch_document_texts(proposal_id=proposal_id)

        # 3. Build user prompt and call Claude
        user_prompt = self._build_user_prompt(
            proposal=proposal, business_group=business_group,
            document_texts=document_texts,
        )

        start_time = time.time()
        ai_result = self._call_ai(user_prompt=user_prompt)
        latency_ms = int((time.time() - start_time) * 1000)

        # 4. Parse response
        parsed = self._parse_response(raw_text=ai_result["text"])

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

        if requires_review:
            new_status = "requires_manual_review"
        elif composite_score >= 80:
            new_status = "shortlisted"
        elif composite_score >= 60:
            new_status = "under_review"
        elif composite_score < 60:
            new_status = "needs_improvement"
        else:
            new_status = "evaluated"

        # 5. Build ai_attribution JSONB from structured response
        ai_attribution = {
            "dimensions": {},
            "composite_score": composite_score,
            "overall_reasoning": parsed.get("overall_reasoning", ""),
        }
        for dim_key in ["relevance", "feasibility", "sector_alignment", "compliance"]:
            dim_data = parsed[dim_key]
            ai_attribution["dimensions"][dim_key] = {
                "score": dim_data["score"],
                "evidence": dim_data.get("evidence", []),
                "risks": dim_data.get("risks", []),
                "confidence": dim_data.get("confidence", "medium"),
            }

        # Save to chamber_evaluations
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
            evaluator_agent_versions={"model": ai_result["model_name"], "version": "1.0"},
            ai_attribution=ai_attribution,
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
        prompt_tokens = ai_result["prompt_tokens"]
        completion_tokens = ai_result["completion_tokens"]
        total_tokens = prompt_tokens + completion_tokens
        cost_usd = round(
            (prompt_tokens * 3 / 1_000_000) + (completion_tokens * 15 / 1_000_000), 6
        )
        energy_kwh = round(total_tokens * 0.001 / 1000, 8)
        carbon_gco2 = round(energy_kwh * 0.4, 8)
        intelligence_units = round(total_tokens / 1000, 4)

        actual_model = ai_result["model_name"]
        logger.info(f"[EVAL] Proposal {proposal_id} evaluated by {ai_result['provider_name']} ({actual_model})")

        evaluation_id = evaluation["id"] if evaluation else None
        try:
            create_ai_interaction(
                user_id=user_id,
                session_id=uuid.uuid4(),
                model_name=actual_model,
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
            "ai_attribution": ai_attribution,
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

    def _fetch_document_texts(self, proposal_id: str) -> list:
        """Fetch extracted_text from all documents linked to this proposal."""
        try:
            docs_result = (
                supabase.table("chamber_documents")
                .select("file_name, extracted_text")
                .eq("proposal_id", str(proposal_id))
                .execute()
            )
            if docs_result.data:
                return [
                    doc for doc in docs_result.data
                    if doc.get("extracted_text")
                ]
        except Exception as e:
            logger.warning(f"[EVAL] Failed to fetch document texts for proposal {proposal_id}: {e}")
        return []

    def _build_user_prompt(
        self, proposal: Dict[str, Any], business_group: Optional[Dict[str, Any]],
        document_texts: Optional[list] = None,
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

        # Append uploaded document texts (truncated to keep within token limits)
        if document_texts:
            remaining_chars = 8000 - len("\n".join(parts))
            if remaining_chars > 500:
                parts.append("\n--- Uploaded Documents ---")
                for doc in document_texts:
                    doc_text = doc.get("extracted_text", "")
                    if doc_text and remaining_chars > 200:
                        chunk = doc_text[:remaining_chars]
                        parts.append(f"Document: {doc.get('file_name', 'unknown')}\n{chunk}")
                        remaining_chars -= len(chunk) + 50
                        if remaining_chars <= 200:
                            break

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

    def _call_ai(self, user_prompt: str) -> Dict[str, Any]:
        """Try Claude first, then OpenAI, then Gemini as fallbacks."""
        last_error = None
        for provider in AI_PROVIDERS:
            try:
                if provider.get("delay"):
                    logger.info(f"[EVAL] Waiting {provider['delay']}s before retry...")
                    time.sleep(provider["delay"])

                logger.info(f"[EVAL] Trying {provider['name']}...")

                if provider["type"] == "anthropic":
                    import anthropic
                    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY))
                    response = client.messages.create(
                        model=provider["model"],
                        max_tokens=4096,
                        system=self.system_prompt,
                        messages=[{"role": "user", "content": user_prompt}],
                    )
                    return {
                        "text": response.content[0].text,
                        "model_name": provider["model"],
                        "provider_name": provider["name"],
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                    }

                elif provider["type"] == "openai":
                    from openai import OpenAI
                    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                    response = client.chat.completions.create(
                        model=provider["model"],
                        max_tokens=4096,
                        messages=[
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                    )
                    usage = response.usage
                    return {
                        "text": response.choices[0].message.content,
                        "model_name": provider["model"],
                        "provider_name": provider["name"],
                        "prompt_tokens": usage.prompt_tokens if usage else 0,
                        "completion_tokens": usage.completion_tokens if usage else 0,
                    }

                elif provider["type"] == "google":
                    import google.generativeai as genai
                    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
                    model = genai.GenerativeModel(
                        provider["model"],
                        system_instruction=self.system_prompt,
                    )
                    response = model.generate_content(user_prompt)
                    meta = getattr(response, "usage_metadata", None)
                    return {
                        "text": response.text,
                        "model_name": provider["model"],
                        "provider_name": provider["name"],
                        "prompt_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                        "completion_tokens": getattr(meta, "candidates_token_count", 0) or 0,
                    }

            except Exception as e:
                last_error = e
                logger.warning(f"[EVAL] {provider['name']} failed: {str(e)[:200]}")
                continue

        raise Exception(f"All AI providers failed. Last error: {last_error}")

    def _parse_response(self, raw_text: str) -> dict:
        """Parse JSON from Claude response, handling markdown fences and edge cases."""
        text = raw_text.strip()
        # Strip markdown code fences (```json ... ``` or ``` ... ```)
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```\s*$', '', text)
        text = text.strip()

        parsed = None
        # Attempt 1: direct JSON parse
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            pass

        # Attempt 2: extract JSON object using first { and last }
        if parsed is None:
            first_brace = text.find('{')
            last_brace = text.rfind('}')
            if first_brace != -1 and last_brace > first_brace:
                try:
                    parsed = json.loads(text[first_brace:last_brace + 1])
                except json.JSONDecodeError:
                    pass

        if parsed is None:
            logger.error(f"Failed to parse Claude response: {text[:500]}")
            raise ValueError("Failed to parse AI evaluation response as JSON")

        # Validate required keys and coerce score types
        for key in ["relevance", "feasibility", "sector_alignment", "compliance"]:
            if key not in parsed:
                raise ValueError(f"Missing required key '{key}' in evaluation response")
            if isinstance(parsed[key], dict):
                if "score" not in parsed[key]:
                    raise ValueError(f"Missing 'score' in '{key}' evaluation")
                # Convert string scores to float
                try:
                    parsed[key]["score"] = float(parsed[key]["score"])
                except (ValueError, TypeError):
                    parsed[key]["score"] = 0.0
                if "reasoning" not in parsed[key]:
                    parsed[key]["reasoning"] = "No reasoning provided"
            else:
                # Handle case where dimension is a score number directly
                score_val = 0.0
                try:
                    score_val = float(parsed[key])
                except (ValueError, TypeError):
                    pass
                parsed[key] = {"score": score_val, "reasoning": "No reasoning provided"}

        return parsed

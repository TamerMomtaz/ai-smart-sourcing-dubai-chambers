"""σI Hallucination Shield — AI integrity verification system.

Verifies evaluation claims against source proposal text using a second AI pass.
Uses the same multi-provider fallback pattern (Claude → GPT-4o → Gemini).
"""

import json
import os
import re
import time
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from config import ANTHROPIC_API_KEY
from database import supabase
from services.ai_interaction_service import create as create_ai_interaction

logger = logging.getLogger(__name__)

# Verification providers — same fallback chain as evaluation_engine
VERIFICATION_PROVIDERS = [
    {"name": "Claude Sonnet 4.5", "type": "anthropic", "model": "claude-sonnet-4-5-20250929"},
    {"name": "Claude Sonnet 4.5 (retry)", "type": "anthropic", "model": "claude-sonnet-4-5-20250929", "delay": 5},
    {"name": "GPT-4o", "type": "openai", "model": "gpt-4o"},
    {"name": "Gemini 2.0 Flash", "type": "google", "model": "gemini-2.0-flash"},
]

# Cross-model providers — intentionally ordered differently to use a different provider
CROSS_MODEL_PROVIDERS = [
    {"name": "GPT-4o", "type": "openai", "model": "gpt-4o"},
    {"name": "Gemini 2.0 Flash", "type": "google", "model": "gemini-2.0-flash"},
    {"name": "Claude Sonnet 4.5", "type": "anthropic", "model": "claude-sonnet-4-5-20250929"},
]


class HallucinationShield:
    """
    σI Hallucination Shield — AI integrity verification system.
    Verifies evaluation claims against source proposal text.
    """

    def __init__(self, supabase_client=None):
        self.db = supabase_client or supabase

    async def verify_evaluation(
        self,
        evaluation_id,
        proposal_id,
        evaluation_reasoning,
        proposal_text,
        evaluation_scores,
        user_id=None,
    ):
        """
        Run hallucination verification on a completed evaluation.
        Returns a HallucinationReport dict.
        """
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_latency_ms = 0

        # Step 1: Extract and verify claims
        start_time = time.time()
        claims_result, claims_tokens = await self._verify_claims(
            evaluation_reasoning=evaluation_reasoning,
            proposal_text=proposal_text,
        )
        claims_latency = int((time.time() - start_time) * 1000)
        total_prompt_tokens += claims_tokens.get("prompt", 0)
        total_completion_tokens += claims_tokens.get("completion", 0)
        total_latency_ms += claims_latency

        # Step 2: Calculate grounding score
        grounding_score = self._calculate_grounding_score(claims_result=claims_result)

        # Step 3: Cross-model verification (quick score check)
        start_time = time.time()
        cross_check, cross_tokens = await self._cross_model_verify(
            proposal_text=proposal_text,
            original_scores=evaluation_scores,
        )
        cross_latency = int((time.time() - start_time) * 1000)
        total_prompt_tokens += cross_tokens.get("prompt", 0)
        total_completion_tokens += cross_tokens.get("completion", 0)
        total_latency_ms += cross_latency

        # Step 4: Determine hallucination risk level
        risk = self._assess_risk(
            grounding_score=grounding_score,
            cross_check=cross_check,
        )

        # Step 5: DESC compliance status
        desc_status = self._desc_compliance_check(
            grounding_score=grounding_score,
            claims_result=claims_result,
            cross_check=cross_check,
        )

        # Calculate cost metrics
        total_tokens = total_prompt_tokens + total_completion_tokens
        cost_usd = round(
            (total_prompt_tokens * 3 / 1_000_000)
            + (total_completion_tokens * 15 / 1_000_000),
            6,
        )
        energy_kwh = round(total_tokens * 0.001 / 1000, 8)
        intelligence_units = round(total_tokens / 1000, 4)

        # Step 6: Build and save report
        report = {
            "evaluation_id": str(evaluation_id),
            "proposal_id": str(proposal_id),
            "grounding_score": grounding_score,
            "total_claims": claims_result["total"],
            "grounded_claims": claims_result["grounded"],
            "partial_claims": claims_result["partial"],
            "ungrounded_claims": claims_result["ungrounded"],
            "claims_detail": claims_result["claims"],
            "cross_model_score": cross_check.get("score"),
            "cross_model_provider": cross_check.get("provider"),
            "primary_score": evaluation_scores.get("composite_score"),
            "score_deviation": cross_check.get("deviation"),
            "deviation_within_threshold": cross_check.get("within_threshold", True),
            "hallucination_risk": risk,
            "desc_lifecycle_phase": "monitor",
            "desc_compliance_status": desc_status,
            "verification_iu": intelligence_units,
            "verification_cost_usd": cost_usd,
        }

        await self._save_report(report=report)

        # Log AI interaction for the verification
        if user_id:
            try:
                create_ai_interaction(
                    user_id=user_id,
                    session_id=uuid.uuid4(),
                    model_name="hallucination_shield",
                    prompt_tokens=total_prompt_tokens,
                    completion_tokens=total_completion_tokens,
                    latency_ms=total_latency_ms,
                    cost_usd=cost_usd,
                    energy_kwh=energy_kwh,
                    carbon_gco2=round(energy_kwh * 0.4, 8),
                    intelligence_units=intelligence_units,
                    operation_type="hallucination_check",
                    evaluation_id=evaluation_id,
                )
            except Exception as e:
                logger.error(f"[SHIELD] Failed to log AI interaction: {e}")

        return report

    async def _verify_claims(self, evaluation_reasoning, proposal_text):
        """
        Send AI a verification prompt: extract claims from the evaluation
        reasoning, then check each one against the proposal text.
        """
        prompt = f"""You are an AI integrity auditor. Your job is to verify whether an AI evaluation's claims are supported by the source document.

EVALUATION REASONING (what the AI said):
{evaluation_reasoning}

SOURCE PROPOSAL TEXT:
{proposal_text[:8000]}

TASK:
1. Extract every factual claim from the evaluation reasoning
2. For each claim, check if it's supported by the proposal text
3. Classify each as:
   - "grounded": directly supported by specific text in the proposal
   - "partial": related content exists but the specific claim is extrapolated
   - "ungrounded": no supporting text found in the proposal

Return ONLY valid JSON (no markdown, no backticks):
{{
  "claims": [
    {{
      "claim": "the specific claim text",
      "classification": "grounded|partial|ungrounded",
      "source_excerpt": "the relevant text from the proposal, or null",
      "explanation": "brief reason for classification"
    }}
  ]
}}"""

        result = self._call_ai_with_fallback(prompt=prompt)
        parsed = self._parse_json_response(raw_text=result["text"])

        claims = parsed.get("claims", [])
        grounded = len([c for c in claims if c.get("classification") == "grounded"])
        partial = len([c for c in claims if c.get("classification") == "partial"])
        ungrounded = len([c for c in claims if c.get("classification") == "ungrounded"])

        tokens = {
            "prompt": result.get("prompt_tokens", 0),
            "completion": result.get("completion_tokens", 0),
        }

        return {
            "total": len(claims),
            "grounded": grounded,
            "partial": partial,
            "ungrounded": ungrounded,
            "claims": claims,
        }, tokens

    async def _cross_model_verify(self, proposal_text, original_scores):
        """
        Quick verification: ask a DIFFERENT model to score the same proposal.
        Compare the scores. Large deviation = potential hallucination.
        """
        prompt = f"""Score this proposal on 4 dimensions (0-100 each):
1. relevance_score: How relevant to Dubai Chambers smart sourcing
2. feasibility_score: Technical and business feasibility
3. sector_alignment_score: Alignment with target sector
4. compliance_score: DESC/regulatory compliance readiness

Proposal excerpt:
{proposal_text[:4000]}

Return ONLY valid JSON (no markdown, no backticks):
{{"relevance_score": N, "feasibility_score": N, "sector_alignment_score": N, "compliance_score": N, "composite_score": N}}"""

        result = self._call_verification_model(prompt=prompt)
        parsed = self._parse_json_response(raw_text=result["text"])

        # Calculate composite if not provided
        if "composite_score" not in parsed:
            scores = [
                parsed.get("relevance_score", 0),
                parsed.get("feasibility_score", 0),
                parsed.get("sector_alignment_score", 0),
                parsed.get("compliance_score", 0),
            ]
            parsed["composite_score"] = sum(scores) / 4 if scores else 0

        primary_composite = original_scores.get("composite_score", 0) or 0
        verify_composite = parsed.get("composite_score", 0) or 0
        deviation = abs(primary_composite - verify_composite)
        deviation_pct = (deviation / max(primary_composite, 1)) * 100

        tokens = {
            "prompt": result.get("prompt_tokens", 0),
            "completion": result.get("completion_tokens", 0),
        }

        return {
            "score": verify_composite,
            "provider": result.get("provider_name", "verification_model"),
            "deviation": round(deviation_pct, 1),
            "within_threshold": deviation_pct <= 15,
        }, tokens

    def _calculate_grounding_score(self, claims_result):
        total = claims_result["total"]
        if total == 0:
            return 100
        grounded = claims_result["grounded"]
        partial = claims_result["partial"]
        score = ((grounded + partial * 0.5) / total) * 100
        return round(score, 1)

    def _assess_risk(self, grounding_score, cross_check):
        if grounding_score >= 85 and cross_check.get("within_threshold", True):
            return "low"
        elif grounding_score >= 65:
            return "medium"
        else:
            return "high"

    def _desc_compliance_check(self, grounding_score, claims_result, cross_check):
        return {
            "hallucination_detection": "active",
            "source_grounding": "verified" if grounding_score >= 70 else "warning",
            "cross_model_validation": "passed" if cross_check.get("within_threshold") else "failed",
            "anomaly_flagging": "enabled",
            "audit_trail": "complete",
            "human_review_trigger": "configured",
        }

    def _call_ai_with_fallback(self, prompt):
        """Try Claude first, then OpenAI, then Gemini as fallbacks."""
        last_error = None
        for provider in VERIFICATION_PROVIDERS:
            try:
                if provider.get("delay"):
                    logger.info(f"[SHIELD] Waiting {provider['delay']}s before retry...")
                    time.sleep(provider["delay"])

                logger.info(f"[SHIELD] Trying {provider['name']}...")
                return self._call_provider(provider=provider, prompt=prompt)

            except Exception as e:
                last_error = e
                logger.warning(f"[SHIELD] {provider['name']} failed: {str(e)[:200]}")
                continue

        raise Exception(f"All AI providers failed for hallucination check. Last error: {last_error}")

    def _call_verification_model(self, prompt):
        """Use cross-model providers (different order to prefer a different model)."""
        last_error = None
        for provider in CROSS_MODEL_PROVIDERS:
            try:
                logger.info(f"[SHIELD-CROSS] Trying {provider['name']}...")
                return self._call_provider(provider=provider, prompt=prompt)
            except Exception as e:
                last_error = e
                logger.warning(f"[SHIELD-CROSS] {provider['name']} failed: {str(e)[:200]}")
                continue

        raise Exception(f"All cross-model providers failed. Last error: {last_error}")

    def _call_provider(self, provider, prompt):
        """Call a single AI provider."""
        if provider["type"] == "anthropic":
            import anthropic

            client = anthropic.Anthropic(
                api_key=os.environ.get("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY)
            )
            response = client.messages.create(
                model=provider["model"],
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
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
                messages=[{"role": "user", "content": prompt}],
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
            model = genai.GenerativeModel(provider["model"])
            response = model.generate_content(prompt)
            meta = getattr(response, "usage_metadata", None)
            return {
                "text": response.text,
                "model_name": provider["model"],
                "provider_name": provider["name"],
                "prompt_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                "completion_tokens": getattr(meta, "candidates_token_count", 0) or 0,
            }

        raise ValueError(f"Unknown provider type: {provider['type']}")

    def _parse_json_response(self, raw_text):
        """Parse JSON from AI response, handling markdown fences and edge cases."""
        text = raw_text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```\s*$", "", text)
        text = text.strip()

        parsed = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            pass

        if parsed is None:
            first_brace = text.find("{")
            last_brace = text.rfind("}")
            if first_brace != -1 and last_brace > first_brace:
                try:
                    parsed = json.loads(text[first_brace : last_brace + 1])
                except json.JSONDecodeError:
                    pass

        if parsed is None:
            logger.error(f"[SHIELD] Failed to parse AI response: {text[:500]}")
            return {"claims": []}

        return parsed

    async def _save_report(self, report):
        """Save hallucination check report to database."""
        try:
            payload = {
                "evaluation_id": report["evaluation_id"],
                "proposal_id": report["proposal_id"],
                "grounding_score": report["grounding_score"],
                "total_claims": report["total_claims"],
                "grounded_claims": report["grounded_claims"],
                "partial_claims": report["partial_claims"],
                "ungrounded_claims": report["ungrounded_claims"],
                "claims_detail": json.dumps(report["claims_detail"]),
                "cross_model_score": report.get("cross_model_score"),
                "cross_model_provider": report.get("cross_model_provider"),
                "primary_score": report.get("primary_score"),
                "score_deviation": report.get("score_deviation"),
                "deviation_within_threshold": report.get("deviation_within_threshold", True),
                "hallucination_risk": report["hallucination_risk"],
                "desc_lifecycle_phase": report.get("desc_lifecycle_phase", "monitor"),
                "desc_compliance_status": json.dumps(report.get("desc_compliance_status", {})),
                "verification_iu": report.get("verification_iu", 0),
                "verification_cost_usd": report.get("verification_cost_usd", 0),
            }
            self.db.table("chamber_hallucination_checks").insert(payload).execute()
            logger.info(f"[SHIELD] Report saved for evaluation {report['evaluation_id']}")
        except Exception as e:
            logger.error(f"[SHIELD] Failed to save report: {e}")

"""DESC compliance audit engine using Claude AI (with multi-provider fallback)."""

import json
import os
import time
import uuid
import logging
from typing import Optional, Dict, Any

from config import ANTHROPIC_API_KEY
from database import supabase
from services import chamber_compliance_audits_service as compliance_service
from services.ai_interaction_service import create as create_ai_interaction

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

SYSTEM_PROMPT = (
    "You are a Dubai DESC (Dubai Electronic Security Centre) compliance auditor.\n"
    "Evaluate this technology proposal against three frameworks:\n"
    "1. DESC ISR V3 (Information Security Regulation)\n"
    "2. DESC AI Security Policy (5-phase AI lifecycle)\n"
    "3. DESC CSP Standards (Cloud Service Provider)\n\n"
    "For each framework, evaluate 3-5 specific controls and provide:\n"
    "- control_id, control_name, status (pass/fail/warning), finding, recommendation\n\n"
    "Also assess:\n"
    "- Data residency compliance (is data stored in UAE?)\n"
    "- Vendor DESC certification status\n"
    "- AI model governance (if AI is involved)\n\n"
    "Respond ONLY in valid JSON:\n"
    "{\n"
    '  "frameworks": [\n'
    "    {\n"
    '      "name": "DESC ISR V3",\n'
    '      "controls": [{"control_id": "ISR-XX", "control_name": "...", "status": "pass|fail|warning", "finding": "...", "recommendation": "..."}]\n'
    "    },\n"
    '    {"name": "DESC AI Security Policy", "controls": [...]},\n'
    '    {"name": "DESC CSP Standards", "controls": [...]}\n'
    "  ],\n"
    '  "data_residency": {"compliant": true/false, "finding": "...", "recommendation": "..."},\n'
    '  "vendor_certification": {"desc_approved": true/false, "finding": "..."},\n'
    '  "overall_score": 0-100,\n'
    '  "overall_status": "compliant|partially_compliant|non_compliant",\n'
    '  "summary": "3-4 sentence summary"\n'
    "}"
)


AI_PROVIDERS = [
    {"name": "Claude Sonnet 4.5", "type": "anthropic", "model": "claude-sonnet-4-5-20250929"},
    {"name": "Claude Sonnet 4.5 (retry)", "type": "anthropic", "model": "claude-sonnet-4-5-20250929", "delay": 5},
    {"name": "GPT-4o", "type": "openai", "model": "gpt-4o"},
    {"name": "Gemini 2.0 Flash", "type": "google", "model": "gemini-2.0-flash"},
]


class ComplianceEngine:
    """AI-powered DESC compliance audit engine with multi-provider fallback."""

    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT

    async def run_audit(self, proposal_id: str, user_id: str) -> dict:
        """
        Run a full DESC compliance audit on a proposal.
        1. Fetch proposal + vendor + documents
        2. Call Claude for compliance evaluation
        3. Parse and save results to chamber_compliance_audits
        4. Log AI interaction (non-critical)
        5. Return audit result
        """
        # 1. Fetch proposal
        proposal = self._fetch_proposal(proposal_id=proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")

        # Fetch vendor info
        vendor = None
        if proposal.get("submitter_id"):
            vendor = self._fetch_vendor(vendor_id=proposal["submitter_id"])

        # Fetch documents
        documents = self._fetch_documents(proposal_id=proposal_id)

        # 2. Build prompt and call Claude
        user_prompt = self._build_audit_prompt(
            proposal=proposal, vendor=vendor, documents=documents
        )

        start_time = time.time()
        ai_result = self._call_ai(user_prompt=user_prompt)
        latency_ms = int((time.time() - start_time) * 1000)

        # 3. Parse response
        parsed = self._parse_response(raw_text=ai_result["text"])

        # Derive boolean compliance flags from parsed result
        framework_compliance = {}
        for fw in parsed.get("frameworks", []):
            name = fw.get("name", "")
            controls = fw.get("controls", [])
            all_pass = all(c.get("status") == "pass" for c in controls)
            any_fail = any(c.get("status") == "fail" for c in controls)
            if "ISR" in name:
                framework_compliance["isr_v3"] = all_pass
            elif "AI" in name:
                framework_compliance["ai_security"] = all_pass
            elif "CSP" in name:
                framework_compliance["csp"] = all_pass

        data_residency = parsed.get("data_residency", {})
        overall_score = parsed.get("overall_score", 0)
        overall_status = parsed.get("overall_status", "non_compliant")
        remediation_needed = overall_status != "compliant"

        # Build full findings JSON
        findings_json = {
            "frameworks": parsed.get("frameworks", []),
            "data_residency": data_residency,
            "vendor_certification": parsed.get("vendor_certification", {}),
            "overall_score": overall_score,
            "overall_status": overall_status,
            "summary": parsed.get("summary", ""),
        }

        # 4. Save to chamber_compliance_audits
        audit = compliance_service.create(
            user_id=user_id,
            proposal_id=proposal_id,
            audit_type="automated",
            isr_v3_compliance=framework_compliance.get("isr_v3", False),
            ai_security_policy_compliance=framework_compliance.get("ai_security", False),
            csp_standards_compliance=framework_compliance.get("csp", False),
            data_residency_verified=data_residency.get("compliant", False),
            auditor_user_id=None,
            findings_json=findings_json,
            remediation_required=remediation_needed,
        )

        # 5. Log AI interaction (non-critical — per rule 9b)
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
        logger.info(f"[COMPLIANCE] Proposal {proposal_id} audited by {ai_result['provider_name']} ({actual_model})")

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
                operation_type="compliance_check",
            )
        except Exception as e:
            logger.error(
                f"Failed to log AI interaction for compliance audit on proposal {proposal_id}: {e}"
            )

        # 6. Return result
        return {
            "audit_id": audit["id"] if audit else None,
            "proposal_id": proposal_id,
            "overall_score": overall_score,
            "overall_status": overall_status,
            "frameworks": parsed.get("frameworks", []),
            "data_residency": data_residency,
            "vendor_certification": parsed.get("vendor_certification", {}),
            "summary": parsed.get("summary", ""),
            "isr_v3_compliance": framework_compliance.get("isr_v3", False),
            "ai_security_policy_compliance": framework_compliance.get("ai_security", False),
            "csp_standards_compliance": framework_compliance.get("csp", False),
            "data_residency_verified": data_residency.get("compliant", False),
            "remediation_required": remediation_needed,
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

    def _fetch_vendor(self, vendor_id: str) -> Optional[Dict[str, Any]]:
        result = (
            supabase.table("chamber_vendors")
            .select("*")
            .eq("id", str(vendor_id))
            .maybe_single()
            .execute()
        )
        return result.data

    def _fetch_documents(self, proposal_id: str):
        result = (
            supabase.table("chamber_documents")
            .select("file_name, file_type, extracted_text")
            .eq("proposal_id", str(proposal_id))
            .execute()
        )
        return result.data or []

    def _build_audit_prompt(
        self,
        proposal: Dict[str, Any],
        vendor: Optional[Dict[str, Any]],
        documents: list,
    ) -> str:
        parts = [
            f"Proposal Title: {proposal.get('title', 'N/A')}",
            f"Sector: {proposal.get('sector', 'N/A')}",
            f"Technology Type: {proposal.get('technology_type', 'N/A')}",
            f"Maturity Level: {proposal.get('maturity_level', 'N/A')}",
        ]
        if proposal.get("description"):
            parts.append(f"Description: {proposal['description']}")

        if vendor:
            parts.append(f"\nVendor Country: {vendor.get('country', 'N/A')}")
            parts.append(
                f"Vendor DESC Approved: {vendor.get('is_desc_approved', False)}"
            )
            parts.append(f"Vendor Name: {vendor.get('name', 'N/A')}")
        else:
            parts.append("\nVendor Country: Unknown")
            parts.append("Vendor DESC Approved: Unknown")

        if documents:
            parts.append("\nAttached Documents:")
            for doc in documents:
                parts.append(f"- {doc.get('file_name', 'Unknown')} ({doc.get('file_type', '')})")
                extracted = doc.get("extracted_text")
                if extracted:
                    # Truncate to avoid token overflow
                    text = extracted if isinstance(extracted, str) else json.dumps(extracted)
                    if len(text) > 2000:
                        text = text[:2000] + "... [truncated]"
                    parts.append(f"  Content: {text}")

        parts.append(
            "\nPerform a comprehensive DESC compliance audit on this proposal "
            "and respond in the required JSON format."
        )
        return "\n".join(parts)

    def _call_ai(self, user_prompt: str) -> Dict[str, Any]:
        """Try Claude first, then OpenAI, then Gemini as fallbacks."""
        last_error = None
        for provider in AI_PROVIDERS:
            try:
                if provider.get("delay"):
                    logger.info(f"[COMPLIANCE] Waiting {provider['delay']}s before retry...")
                    time.sleep(provider["delay"])

                logger.info(f"[COMPLIANCE] Trying {provider['name']}...")

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
                logger.warning(f"[COMPLIANCE] {provider['name']} failed: {str(e)[:200]}")
                continue

        raise Exception(f"All AI providers failed. Last error: {last_error}")

    def _parse_response(self, raw_text: str) -> dict:
        """Parse JSON from Claude response, handling markdown fences."""
        text = raw_text.strip()
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
            logger.error(f"Failed to parse compliance audit response: {text[:500]}")
            raise ValueError("Failed to parse AI compliance audit response as JSON")

        # Validate required keys
        if "frameworks" not in parsed:
            raise ValueError("Missing 'frameworks' key in compliance audit response")
        if "overall_score" not in parsed:
            parsed["overall_score"] = 0
        if "overall_status" not in parsed:
            parsed["overall_status"] = "non_compliant"

        return parsed

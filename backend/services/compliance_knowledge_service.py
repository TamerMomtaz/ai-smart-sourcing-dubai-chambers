"""RAG-based Compliance Knowledge Service.

Seeds an official knowledge base and verifies vendor claims against it
using vector similarity search + AI reasoning.
"""

import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional

from database import supabase
from services.ai_interaction_service import create as create_ai_interaction

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def _get_openai_client():
    from openai import OpenAI
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def _generate_embedding(text: str) -> List[float]:
    """Generate an embedding vector for the given text using OpenAI."""
    client = _get_openai_client()
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
        dimensions=EMBEDDING_DIMENSIONS,
    )
    return response.data[0].embedding


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks for embedding."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


# ---------------------------------------------------------------------------
# Knowledge base content — official compliance reference material
# ---------------------------------------------------------------------------

ISO_FRAMEWORK_CONTENT = [
    {
        "source": "iso_27001_framework",
        "content": (
            "ISO/IEC 27001 Information Security Management System (ISMS) Requirements: "
            "Organizations must establish, implement, maintain and continually improve an ISMS. "
            "Key controls include: A.5 Information security policies, A.6 Organization of information security, "
            "A.7 Human resource security, A.8 Asset management, A.9 Access control, "
            "A.10 Cryptography, A.11 Physical and environmental security, A.12 Operations security, "
            "A.13 Communications security, A.14 System acquisition, development and maintenance, "
            "A.15 Supplier relationships, A.16 Information security incident management, "
            "A.17 Business continuity management, A.18 Compliance. "
            "Certification requires an accredited third-party audit and annual surveillance audits."
        ),
        "metadata": {"framework": "ISO 27001", "version": "2022", "type": "requirements_summary"},
    },
    {
        "source": "iso_27001_framework",
        "content": (
            "ISO 27001 Certification Process: Organizations must complete a Stage 1 documentation review "
            "and a Stage 2 on-site audit by an accredited certification body. Certification is valid for 3 years "
            "with annual surveillance audits. Common certification bodies include BSI, TUV, and Bureau Veritas. "
            "The scope of certification must clearly define the boundaries of the ISMS. "
            "Organizations must demonstrate risk assessment methodology, Statement of Applicability (SoA), "
            "and evidence of management commitment and continual improvement."
        ),
        "metadata": {"framework": "ISO 27001", "version": "2022", "type": "certification_process"},
    },
]

CSA_CCM_CONTENT = [
    {
        "source": "csa_ccm_controls",
        "content": (
            "Cloud Security Alliance (CSA) Cloud Controls Matrix (CCM) v4 Domains: "
            "1. Audit & Assurance (A&A) — Independent audit program governance. "
            "2. Application & Interface Security (AIS) — Secure application development lifecycle. "
            "3. Business Continuity Management & Operational Resilience (BCR) — Service continuity planning. "
            "4. Change Control & Configuration Management (CCC) — Change management processes. "
            "5. Cryptography, Encryption & Key Management (CEK) — Data protection in transit and at rest. "
            "6. Datacenter Security (DCS) — Physical security of data center facilities. "
            "7. Data Security & Privacy Lifecycle Management (DSP) — Data classification and handling. "
            "8. Governance, Risk Management & Compliance (GRC) — Enterprise risk framework. "
            "9. Human Resources Security (HRS) — Personnel screening and awareness. "
            "10. Identity & Access Management (IAM) — Authentication and authorization controls. "
            "11. Interoperability & Portability (IPY) — Data portability and vendor lock-in avoidance. "
            "12. Infrastructure & Virtualization Security (IVS) — Network and hypervisor security. "
            "13. Logging & Monitoring (LOG) — Security event logging and monitoring. "
            "14. Security Incident Management (SEF) — Incident response procedures. "
            "15. Supply Chain Management (STA) — Third-party risk management. "
            "16. Threat & Vulnerability Management (TVM) — Vulnerability assessment and remediation. "
            "17. Universal Endpoint Management (UEM) — Endpoint security controls."
        ),
        "metadata": {"framework": "CSA CCM", "version": "4.0", "type": "control_domains"},
    },
]

ISR_V3_CONTENT = [
    {
        "source": "isr_v3_framework",
        "content": (
            "UAE Information Security Regulation (ISR) V3 — Domain Summaries: "
            "Domain 1: Information Security Governance — Establish governance structure, assign CISO role, "
            "define security policies aligned with UAE national strategy. "
            "Domain 2: Asset Management — Classify and manage information assets, maintain asset inventory. "
            "Domain 3: Human Resources Security — Background checks, security awareness training, "
            "disciplinary procedures for security violations. "
            "Domain 4: Physical & Environmental Security — Secure areas, equipment protection, "
            "clear desk/clear screen policies. "
            "Domain 5: Communications & Operations Management — Network security, malware protection, "
            "backup procedures, media handling."
        ),
        "metadata": {"framework": "ISR V3", "version": "3.0", "type": "domain_summary"},
    },
    {
        "source": "isr_v3_framework",
        "content": (
            "UAE ISR V3 Continued — "
            "Domain 6: Access Control — User registration, privilege management, password management, "
            "network access control, operating system access control. "
            "Domain 7: Information Systems Acquisition, Development & Maintenance — Security requirements, "
            "cryptographic controls, system file security, development security. "
            "Domain 8: Information Security Incident Management — Incident reporting, response procedures, "
            "evidence collection, lessons learned. "
            "Domain 9: Business Continuity Management — BCM framework, business impact analysis, "
            "continuity plans, testing and maintenance. "
            "Domain 10: Compliance — Legal requirements, security policy compliance, audit considerations. "
            "ISR V3 compliance is mandatory for UAE government entities and critical infrastructure operators."
        ),
        "metadata": {"framework": "ISR V3", "version": "3.0", "type": "domain_summary"},
    },
]


def seed_knowledge_base(user_id: str) -> Dict[str, Any]:
    """Seed the compliance knowledge base with official documents.

    Sources:
    - DESC certified providers (from chamber_desc_certified_providers table)
    - ISO 27001 framework requirements
    - CSA CCM control domains
    - ISR V3 domain summaries
    """
    start_time = time.time()
    total_seeded = 0
    sources_seeded: List[str] = []
    total_prompt_tokens = 0

    # 1. Seed DESC certified providers from the database
    try:
        providers_result = (
            supabase.table("chamber_desc_certified_providers")
            .select("*")
            .execute()
        )
        providers = providers_result.data or []
        for provider in providers:
            content = (
                f"DESC Certified Cloud Service Provider: {provider.get('provider_name', 'Unknown')}. "
                f"Certification Number: {provider.get('certification_number', 'N/A')}. "
                f"Valid Until: {provider.get('valid_until', 'N/A')}. "
                f"Services Offered: {', '.join(provider.get('services_offered', []))}. "
                f"Compliance Frameworks: {', '.join(provider.get('compliance_frameworks', []))}. "
                f"This provider is officially registered in the Dubai Electronic Security Center (DESC) "
                f"certified providers list and has passed DESC audit requirements."
            )
            embedding = _generate_embedding(text=content)
            total_prompt_tokens += len(content.split()) * 2  # rough token estimate

            supabase.table("chamber_compliance_knowledge").insert({
                "source": "desc_certified_providers",
                "content": content,
                "embedding": embedding,
                "metadata": json.dumps({
                    "provider_id": str(provider.get("id", "")),
                    "provider_name": provider.get("provider_name"),
                    "certification_number": provider.get("certification_number"),
                    "type": "certified_provider",
                }),
            }).execute()
            total_seeded += 1

        if providers:
            sources_seeded.append(f"desc_certified_providers ({len(providers)} providers)")
    except Exception as e:
        logger.error(f"[RAG] Failed to seed DESC providers: {e}")

    # 2. Seed static compliance content (ISO, CSA CCM, ISR V3)
    static_sources = [
        ("iso_27001", ISO_FRAMEWORK_CONTENT),
        ("csa_ccm", CSA_CCM_CONTENT),
        ("isr_v3", ISR_V3_CONTENT),
    ]

    for source_name, documents in static_sources:
        try:
            for doc in documents:
                chunks = _chunk_text(text=doc["content"])
                for i, chunk in enumerate(chunks):
                    embedding = _generate_embedding(text=chunk)
                    total_prompt_tokens += len(chunk.split()) * 2

                    metadata = dict(doc.get("metadata", {}))
                    metadata["chunk_index"] = i
                    metadata["total_chunks"] = len(chunks)

                    supabase.table("chamber_compliance_knowledge").insert({
                        "source": doc["source"],
                        "content": chunk,
                        "embedding": embedding,
                        "metadata": json.dumps(metadata),
                    }).execute()
                    total_seeded += 1

            sources_seeded.append(source_name)
        except Exception as e:
            logger.error(f"[RAG] Failed to seed {source_name}: {e}")

    # Log AI interaction for embedding generation
    latency_ms = int((time.time() - start_time) * 1000)
    cost_usd = round(total_prompt_tokens * 0.02 / 1_000_000, 6)  # text-embedding-3-small pricing
    try:
        create_ai_interaction(
            user_id=user_id,
            session_id=uuid.uuid4(),
            model_name=EMBEDDING_MODEL,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=0,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            energy_kwh=round(total_prompt_tokens * 0.0001 / 1000, 8),
            carbon_gco2=round(total_prompt_tokens * 0.0001 / 1000 * 0.4, 8),
            intelligence_units=round(total_prompt_tokens / 1000, 4),
            operation_type="compliance_check",
        )
    except Exception as e:
        logger.error(f"[RAG] Failed to log seed AI interaction: {e}")

    logger.info(f"[RAG] Seeded {total_seeded} knowledge chunks from {len(sources_seeded)} sources")
    return {
        "documents_seeded": total_seeded,
        "sources": sources_seeded,
    }


def vector_search(query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
    """Perform vector similarity search against the knowledge base using Supabase RPC."""
    try:
        # Use Supabase's built-in vector similarity via rpc or direct query
        # Since Supabase Python SDK doesn't natively support pgvector operators,
        # we use a raw RPC call or fall back to fetching all and computing locally
        result = supabase.rpc("match_compliance_knowledge", {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,
            "match_count": top_k,
        }).execute()

        if result.data:
            return result.data
    except Exception as e:
        logger.warning(f"[RAG] RPC vector search failed, using fallback: {e}")

    # Fallback: fetch all records and compute cosine similarity in Python
    try:
        all_records = (
            supabase.table("chamber_compliance_knowledge")
            .select("id, source, content, metadata, embedding")
            .not_.is_("embedding", "null")
            .execute()
        )
        if not all_records.data:
            return []

        import numpy as np

        query_vec = np.array(query_embedding)
        scored = []
        for record in all_records.data:
            emb = record.get("embedding")
            if not emb:
                continue
            if isinstance(emb, str):
                emb = json.loads(emb)
            record_vec = np.array(emb)
            # Cosine similarity
            dot = np.dot(query_vec, record_vec)
            norm = np.linalg.norm(query_vec) * np.linalg.norm(record_vec)
            similarity = float(dot / norm) if norm > 0 else 0.0
            if similarity >= 0.5:
                scored.append({
                    "id": record["id"],
                    "source": record["source"],
                    "content": record["content"],
                    "metadata": record["metadata"],
                    "similarity": round(similarity, 4),
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]
    except Exception as e:
        logger.error(f"[RAG] Fallback vector search failed: {e}")
        return []


def verify_claim(claim: str, user_id: str) -> Dict[str, Any]:
    """Verify a vendor claim against the compliance knowledge base.

    1. Generate embedding of the claim
    2. Vector search top-5 relevant knowledge chunks
    3. Send to AI for verification with source evidence
    4. Return result with source citations
    """
    start_time = time.time()
    total_prompt_tokens = 0
    total_completion_tokens = 0

    # Step 1: Generate embedding for the claim
    claim_embedding = _generate_embedding(text=claim)
    total_prompt_tokens += len(claim.split()) * 2

    # Step 2: Vector search for relevant knowledge
    relevant_chunks = vector_search(query_embedding=claim_embedding, top_k=5)

    if not relevant_chunks:
        return {
            "claim": claim,
            "status": "unverified",
            "confidence": 0.0,
            "reasoning": "No relevant documents found in the compliance knowledge base to verify this claim.",
            "sources": [],
        }

    # Step 3: Build context and ask AI to verify
    evidence_text = "\n\n".join([
        f"[Source: {chunk['source']}] {chunk['content']}"
        for chunk in relevant_chunks
    ])

    prompt = f"""You are a compliance verification officer for Dubai Chambers. Your job is to verify vendor claims against official compliance records.

CLAIM TO VERIFY:
"{claim}"

OFFICIAL KNOWLEDGE BASE EVIDENCE:
{evidence_text}

TASK:
Based ONLY on the evidence provided above, determine if the claim is supported.

Return ONLY valid JSON (no markdown, no backticks):
{{
  "status": "verified" | "unverified" | "partial",
  "confidence": <float 0.0-1.0>,
  "reasoning": "<detailed explanation of why the claim is verified/unverified/partial, citing specific evidence>"
}}

Rules:
- "verified": The claim is directly and fully supported by the evidence
- "partial": Some aspects of the claim are supported but others cannot be confirmed
- "unverified": The evidence does not support the claim, or contradicts it
- Be conservative — if evidence is ambiguous, use "partial"
- Always cite which specific source supports or contradicts the claim"""

    # Call AI for verification
    ai_result = _call_verification_ai(prompt=prompt)
    total_prompt_tokens += ai_result.get("prompt_tokens", 0)
    total_completion_tokens += ai_result.get("completion_tokens", 0)

    parsed = _parse_json_response(raw_text=ai_result["text"])

    # Build source citations
    sources = []
    for chunk in relevant_chunks:
        metadata = chunk.get("metadata")
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        sources.append({
            "source": chunk.get("source", "unknown"),
            "content_excerpt": chunk.get("content", "")[:200],
            "similarity": chunk.get("similarity", 0),
            "metadata": metadata or {},
        })

    # Log AI interaction
    latency_ms = int((time.time() - start_time) * 1000)
    total_tokens = total_prompt_tokens + total_completion_tokens
    cost_usd = round(
        (total_prompt_tokens * 3 / 1_000_000)
        + (total_completion_tokens * 15 / 1_000_000),
        6,
    )
    try:
        create_ai_interaction(
            user_id=user_id,
            session_id=uuid.uuid4(),
            model_name=ai_result.get("model_name", "claude-sonnet-4-5-20250929"),
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            energy_kwh=round(total_tokens * 0.001 / 1000, 8),
            carbon_gco2=round(total_tokens * 0.001 / 1000 * 0.4, 8),
            intelligence_units=round(total_tokens / 1000, 4),
            operation_type="compliance_check",
        )
    except Exception as e:
        logger.error(f"[RAG] Failed to log verify AI interaction: {e}")

    return {
        "claim": claim,
        "status": parsed.get("status", "unverified"),
        "confidence": float(parsed.get("confidence", 0.0)),
        "reasoning": parsed.get("reasoning", "Verification could not be completed."),
        "sources": sources,
    }


def _call_verification_ai(prompt: str) -> Dict[str, Any]:
    """Call AI for claim verification, with multi-provider fallback."""
    import re

    providers = [
        {"name": "Claude Sonnet 4.5", "type": "anthropic", "model": "claude-sonnet-4-5-20250929"},
        {"name": "GPT-4o", "type": "openai", "model": "gpt-4o"},
        {"name": "Gemini 2.0 Flash", "type": "google", "model": "gemini-2.0-flash"},
    ]

    last_error = None
    for provider in providers:
        try:
            logger.info(f"[RAG] Trying {provider['name']}...")
            if provider["type"] == "anthropic":
                import anthropic
                client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
                response = client.messages.create(
                    model=provider["model"],
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}],
                )
                return {
                    "text": response.content[0].text,
                    "model_name": provider["model"],
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                }
            elif provider["type"] == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
                response = client.chat.completions.create(
                    model=provider["model"],
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}],
                )
                usage = response.usage
                return {
                    "text": response.choices[0].message.content,
                    "model_name": provider["model"],
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
                    "prompt_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                    "completion_tokens": getattr(meta, "candidates_token_count", 0) or 0,
                }
        except Exception as e:
            last_error = e
            logger.warning(f"[RAG] {provider['name']} failed: {str(e)[:200]}")
            continue

    raise Exception(f"All AI providers failed for RAG verification. Last error: {last_error}")


def _parse_json_response(raw_text: str) -> Dict[str, Any]:
    """Parse JSON from AI response, handling markdown fences."""
    import re

    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    logger.error(f"[RAG] Failed to parse AI response: {text[:500]}")
    return {"status": "unverified", "confidence": 0.0, "reasoning": "Failed to parse AI response"}

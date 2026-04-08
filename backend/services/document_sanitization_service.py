"""Document sanitization service for proposal uploads.

Extracts text-only content from PDFs (stripping images, embedded objects,
macros, JavaScript, form fields, annotations) and scans for prompt injection
patterns. Flags suspicious content for human review without auto-rejecting.
"""

import io
import re
import json
import uuid
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone

from database import supabase

logger = logging.getLogger(__name__)

# Prompt injection patterns to detect
INJECTION_PATTERNS = [
    (r"ignore\s+(?:all\s+)?previous\s+instructions", "prompt_injection", "Attempt to override AI instructions"),
    (r"ignore\s+all\s+instructions", "prompt_injection", "Attempt to override AI instructions"),
    (r"you\s+are\s+now", "prompt_injection", "Attempt to reassign AI role"),
    (r"system\s+prompt", "prompt_injection", "Reference to system prompt"),
    (r"forget\s+everything", "prompt_injection", "Attempt to reset AI context"),
    (r"disregard\s+(?:all\s+)?(?:previous|prior|above)", "prompt_injection", "Attempt to override AI instructions"),
    (r"new\s+instructions?\s*:", "prompt_injection", "Attempt to inject new instructions"),
    (r"act\s+as\s+(?:a\s+)?(?:different|new)", "prompt_injection", "Attempt to reassign AI role"),
]

# Score manipulation patterns
SCORE_MANIPULATION_PATTERNS = [
    (r"score\s+this\s+(?:a\s+)?100", "score_manipulation", "Attempt to force maximum score"),
    (r"give\s+(?:this\s+)?(?:a\s+)?maximum\s+score", "score_manipulation", "Attempt to force maximum score"),
    (r"give\s+(?:this\s+)?(?:a\s+)?(?:perfect|full|highest)\s+(?:score|rating|mark)", "score_manipulation", "Attempt to force perfect score"),
    (r"rate\s+(?:this\s+)?(?:at\s+)?100", "score_manipulation", "Attempt to force maximum score"),
    (r"must\s+(?:be\s+)?(?:scored?|rated?)\s+(?:at\s+)?(?:least\s+)?(?:9[0-9]|100)", "score_manipulation", "Attempt to force high score"),
    (r"automatically\s+approve", "score_manipulation", "Attempt to bypass evaluation"),
    (r"skip\s+(?:the\s+)?(?:evaluation|review|compliance)", "score_manipulation", "Attempt to bypass evaluation"),
]


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text-only content from PDF, stripping images, embedded objects,
    macros, JavaScript, form fields, and annotations."""
    # Try pdfplumber first (better text extraction)
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages[:50]:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        if text_parts:
            return "\n".join(text_parts)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed: {e}")

    # Fallback to PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages[:50]:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {e}")

    return ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text-only content from DOCX, stripping embedded objects and macros."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        return ""
    except Exception as e:
        logger.warning(f"DOCX extraction failed: {e}")
        return ""


def scan_for_injections(text: str) -> List[Dict[str, str]]:
    """Scan text for prompt injection and score manipulation patterns.

    Returns a list of detected flags, each with:
      - pattern_type: 'prompt_injection' or 'score_manipulation'
      - description: human-readable description
      - matched_text: the actual text that matched (truncated)
    """
    flags = []
    text_lower = text.lower()

    for pattern, pattern_type, description in INJECTION_PATTERNS + SCORE_MANIPULATION_PATTERNS:
        matches = list(re.finditer(pattern, text_lower))
        for match in matches:
            matched = match.group(0)
            # Get surrounding context (up to 50 chars each side)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].strip()

            flags.append({
                "pattern_type": pattern_type,
                "description": description,
                "matched_text": matched[:100],
                "context": context[:200],
            })

    # Deduplicate by matched_text
    seen = set()
    unique_flags = []
    for flag in flags:
        key = (flag["pattern_type"], flag["matched_text"])
        if key not in seen:
            seen.add(key)
            unique_flags.append(flag)

    return unique_flags


def sanitize_text(raw_text: str) -> str:
    """Remove potentially dangerous patterns from text while preserving content.

    This produces a cleaned version for AI evaluation. The original is always
    kept for reference — we never discard user content.
    """
    if not raw_text:
        return ""

    sanitized = raw_text

    # Remove null bytes and control characters (except newline/tab)
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', sanitized)

    # Remove potential HTML/script tags that might confuse AI
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)
    sanitized = re.sub(r'<style[^>]*>.*?</style>', '', sanitized, flags=re.DOTALL | re.IGNORECASE)

    # Remove excessively long lines of repeated characters (potential padding attacks)
    sanitized = re.sub(r'(.)\1{100,}', r'\1\1\1...', sanitized)

    # Collapse excessive whitespace while preserving paragraph breaks
    sanitized = re.sub(r'[ \t]{10,}', '  ', sanitized)
    sanitized = re.sub(r'\n{5,}', '\n\n\n', sanitized)

    return sanitized.strip()


def sanitize_proposal_content(
    proposal_id: str,
    raw_text: str,
    user_id: str,
    source: str = "document_upload",
) -> Dict[str, Any]:
    """Full sanitization pipeline for proposal content.

    1. Sanitize text (strip dangerous patterns)
    2. Scan for injection attempts
    3. Store sanitized_text and content_flags on chamber_proposals
    4. Log to chamber_ai_interactions as 'content_scan'

    Args:
        proposal_id: The proposal UUID
        raw_text: Raw extracted text to sanitize
        user_id: ID of the user who uploaded
        source: Origin of the text (document_upload, ingest, description)

    Returns:
        Dict with sanitized_text, flags, and flagged status
    """
    if not raw_text or not raw_text.strip():
        return {
            "sanitized_text": "",
            "flags": [],
            "flagged": False,
        }

    # Step 1: Sanitize text
    cleaned_text = sanitize_text(raw_text=raw_text)

    # Step 2: Scan for injections (scan original text, not sanitized)
    detected_flags = scan_for_injections(text=raw_text)

    # Build content_flags JSONB
    content_flags = None
    if detected_flags:
        content_flags = {
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "flags": detected_flags,
            "total_flags": len(detected_flags),
            "has_prompt_injection": any(f["pattern_type"] == "prompt_injection" for f in detected_flags),
            "has_score_manipulation": any(f["pattern_type"] == "score_manipulation" for f in detected_flags),
        }

    # Step 3: Update chamber_proposals with sanitized text and flags
    try:
        update_data = {
            "sanitized_text": cleaned_text,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if content_flags:
            update_data["content_flags"] = json.dumps(content_flags)
            update_data["requires_manual_review"] = True

        supabase.table("chamber_proposals").update(update_data).eq(
            "id", str(proposal_id)
        ).execute()

        if content_flags:
            logger.warning(
                f"[SANITIZE] Proposal {proposal_id}: {len(detected_flags)} "
                f"security flag(s) detected — flagged for human review"
            )
        else:
            logger.info(f"[SANITIZE] Proposal {proposal_id}: clean — no flags detected")

    except Exception as e:
        logger.error(f"[SANITIZE] Failed to update proposal {proposal_id}: {e}")

    # Step 4: Log to chamber_ai_interactions
    try:
        from services.ai_interaction_service import create as create_ai_interaction
        create_ai_interaction(
            user_id=user_id,
            session_id=uuid.uuid4(),
            model_name="document_sanitizer_v1",
            prompt_tokens=len(raw_text.split()),
            completion_tokens=0,
            latency_ms=0,
            cost_usd=0.0,
            energy_kwh=0.0,
            carbon_gco2=0.0,
            intelligence_units=0.0,
            operation_type="content_scan",
        )
    except Exception as e:
        logger.error(f"[SANITIZE] Failed to log AI interaction for proposal {proposal_id}: {e}")

    return {
        "sanitized_text": cleaned_text,
        "flags": detected_flags,
        "flagged": len(detected_flags) > 0,
    }

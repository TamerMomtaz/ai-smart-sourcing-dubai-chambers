"""Proposal document ingestion route — upload PDF/DOCX, extract details via AI."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from datetime import datetime, timezone
import logging
import json
import time
import uuid as uuid_mod

from auth import get_current_user
from database import supabase
from config import DOCUMENT_STORAGE_BUCKET
from services.ai_provider import ai_complete
from services.document_sanitization_service import sanitize_proposal_content

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Proposal Document Ingestion"])

EXTRACTION_SYSTEM_PROMPT = (
    "You are extracting structured proposal information from "
    "a vendor submission document for Dubai Chambers. Extract the following "
    "and respond ONLY in JSON:\n"
    "{\n"
    '  "title": "proposal title",\n'
    '  "sector": "one of: AI/ML, FinTech, HealthTech, CleanTech, EdTech, '
    'Construction, Cybersecurity, Supply Chain, AgTech, SpaceTech, Retail",\n'
    '  "technology_type": "main technology",\n'
    '  "maturity_level": "one of: concept, prototype, mvp, production, scaled",\n'
    '  "language": "en or ar or mixed",\n'
    '  "description": "2-3 sentence summary of the proposal",\n'
    '  "company_name": "vendor company name",\n'
    '  "company_country": "country"\n'
    "}"
)

ALLOWED_EXTENSIONS = {"pdf", "docx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyPDF2 or pdfplumber if available."""
    try:
        import pdfplumber
        import io
        text_parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages[:30]:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfReader
        import io
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = []
        for page in reader.pages[:30]:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts)
    except ImportError:
        pass

    return ""


def _extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes."""
    try:
        import docx
        import io
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except ImportError:
        return ""


def _parse_json_response(raw_text: str) -> dict:
    """Parse JSON from AI response, handling markdown fences."""
    import re
    text = raw_text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```\s*$', '', text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace > first_brace:
        return json.loads(text[first_brace:last_brace + 1])

    raise json.JSONDecodeError("No valid JSON found", text, 0)


@router.post(
    "/proposals/ingest-document",
    status_code=status.HTTP_200_OK,
    summary="Upload and extract proposal from document",
    description="Upload a PDF/DOCX file. AI extracts proposal details for review before submission.",
)
async def ingest_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a document (PDF/DOCX), extract proposal details via AI.

    1. Validate file type and size
    2. Extract text from document
    3. Call AI to extract structured proposal fields
    4. Return extracted details for user review
    """
    user_id = current_user["id"]
    user_email = current_user.get("email", "")

    # Validate file extension
    filename = file.filename or "document"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid file type", "detail": "Only PDF and DOCX files are accepted", "code": 400},
        )

    # Read file content
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "File too large", "detail": "Maximum file size is 50 MB", "code": 400},
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Empty file", "detail": "The uploaded file is empty", "code": 400},
        )

    # Extract text
    if ext == "pdf":
        extracted_text = _extract_text_from_pdf(file_bytes)
    else:
        extracted_text = _extract_text_from_docx(file_bytes)

    # Build AI prompt
    if extracted_text.strip():
        # Limit text to ~8000 chars to stay within token limits
        truncated = extracted_text[:8000]
        user_prompt = f"Document filename: {filename}\n\nDocument content:\n{truncated}"
    else:
        user_prompt = (
            f"Document filename: {filename}\n\n"
            "Could not extract text from this document. "
            "Based on the filename, infer reasonable defaults for the proposal fields. "
            "Use 'concept' for maturity_level and 'en' for language if uncertain."
        )

    # Call AI with multi-provider fallback
    start_time = time.time()
    try:
        raw_ai_text = await ai_complete(
            system_prompt=EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=2048,
        )
    except Exception as ai_err:
        logger.error(f"AI extraction failed: {ai_err}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "AI service temporarily unavailable", "detail": "Please try again in a moment", "code": 503},
        )
    latency_ms = int((time.time() - start_time) * 1000)

    try:
        extracted = _parse_json_response(raw_ai_text)
    except (json.JSONDecodeError, Exception):
        logger.error(f"Failed to parse AI extraction response: {raw_ai_text[:500]}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to parse AI response", "code": 500},
        )

    # Validate and normalize extracted fields
    valid_sectors = ["AI/ML", "FinTech", "HealthTech", "CleanTech", "EdTech",
                     "Construction", "Cybersecurity", "Supply Chain", "AgTech", "SpaceTech", "Retail"]
    valid_maturity = ["concept", "prototype", "mvp", "production", "scaled"]
    valid_languages = ["en", "ar", "mixed"]

    sector = extracted.get("sector", "AI/ML")
    if sector not in valid_sectors:
        sector = "AI/ML"

    maturity = extracted.get("maturity_level", "concept")
    if maturity not in valid_maturity:
        maturity = "concept"

    lang = extracted.get("language", "en")
    if lang not in valid_languages:
        lang = "en"

    # Upload file to Supabase Storage
    storage_path = f"proposals/ingested/{user_id}/{uuid_mod.uuid4()}/{filename}"
    file_url = None
    try:
        supabase.storage.from_(DOCUMENT_STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type or "application/octet-stream"},
        )
        file_url = f"{DOCUMENT_STORAGE_BUCKET}/{storage_path}"
    except Exception as storage_err:
        logger.warning(f"Storage upload failed (non-blocking): {storage_err}")

    # Log AI interaction (non-critical, per rule 9b)
    try:
        from services.ai_interaction_service import create as create_ai_interaction
        # Estimate tokens since multi-provider may not give exact counts
        est_prompt_tokens = len(user_prompt.split()) * 2
        est_completion_tokens = len(raw_ai_text.split()) * 2
        total_tokens = est_prompt_tokens + est_completion_tokens
        cost_usd = round((est_prompt_tokens * 3 / 1_000_000) + (est_completion_tokens * 15 / 1_000_000), 6)
        energy_kwh = round(total_tokens * 0.001 / 1000, 8)
        carbon_gco2 = round(energy_kwh * 0.4, 8)
        intelligence_units = round(total_tokens / 1000, 4)

        create_ai_interaction(
            user_id=user_id,
            session_id=uuid_mod.uuid4(),
            model_name="claude-sonnet-4-5-20250929",
            prompt_tokens=est_prompt_tokens,
            completion_tokens=est_completion_tokens,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            energy_kwh=energy_kwh,
            carbon_gco2=carbon_gco2,
            intelligence_units=intelligence_units,
            operation_type="extraction",
        )
    except Exception as log_err:
        logger.error(f"Failed to log AI interaction for document ingestion: {log_err}")

    return {
        "extracted": {
            "title": extracted.get("title", filename.rsplit(".", 1)[0]),
            "sector": sector,
            "technology_type": extracted.get("technology_type", ""),
            "maturity_level": maturity,
            "language": lang,
            "description": extracted.get("description", ""),
            "company_name": extracted.get("company_name", ""),
            "company_country": extracted.get("company_country", "UAE"),
        },
        "file_name": filename,
        "file_size": len(file_bytes),
        "storage_path": storage_path if file_url else None,
        "text_extracted": bool(extracted_text.strip()),
        "extracted_text": extracted_text if extracted_text.strip() else None,
        "message": "Document processed successfully. Review the extracted details and confirm submission.",
    }


@router.post(
    "/proposals/confirm-ingestion",
    status_code=status.HTTP_201_CREATED,
    summary="Confirm and create proposal from ingested document",
    description="After reviewing AI-extracted details, confirm to create the proposal.",
)
async def confirm_ingestion(
    payload: dict,
    current_user: dict = Depends(get_current_user),
):
    """
    Create proposal from reviewed/edited extraction data.

    Expects JSON body with fields: title, sector, technology_type, maturity_level,
    language, description, company_name, company_country, storage_path (optional).
    """
    user_id = current_user["id"]
    user_email = current_user.get("email", "")

    title = payload.get("title", "").strip()
    sector = payload.get("sector", "").strip()
    technology_type = payload.get("technology_type", "").strip()
    maturity_level = payload.get("maturity_level", "concept")
    language = payload.get("language", "en")
    description = payload.get("description", "").strip()
    company_name = payload.get("company_name", "").strip()
    company_country = payload.get("company_country", "UAE").strip()
    storage_path = payload.get("storage_path")

    if not title or not sector or not technology_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Missing required fields", "detail": "title, sector, and technology_type are required", "code": 400},
        )

    # Look up or create vendor by company_name (not current user)
    vendor_id_for_proposal = None
    if company_name:
        vendor_check = (
            supabase.table("chamber_vendors")
            .select("id")
            .eq("name", company_name)
            .maybe_single()
            .execute()
        )
        if vendor_check.data:
            vendor_id_for_proposal = vendor_check.data["id"]
        else:
            # Extract contact_email from payload if available
            contact_email = payload.get("contact_email", "pending@review.com")
            new_vendor_id = str(uuid_mod.uuid4())
            vendor_data = {
                "id": new_vendor_id,
                "name": company_name,
                "country": company_country,
                "contact_email": contact_email,
                "is_desc_approved": False,
                "onboarding_status": "submitted",
                "submission_history_count": 0,
            }
            supabase.table("chamber_vendors").insert(vendor_data).execute()
            vendor_id_for_proposal = new_vendor_id
            logger.info(f"Auto-created vendor '{company_name}' with id {new_vendor_id}")
    else:
        # Fallback: ensure current user has a vendor record
        vendor_check = (
            supabase.table("chamber_vendors")
            .select("id")
            .eq("id", str(user_id))
            .maybe_single()
            .execute()
        )
        if vendor_check.data:
            vendor_id_for_proposal = vendor_check.data["id"]
        else:
            vendor_data = {
                "id": str(user_id),
                "name": user_email.split("@")[0] if user_email else "unknown",
                "country": company_country,
                "contact_email": user_email or "pending@review.com",
                "is_desc_approved": False,
                "onboarding_status": "submitted",
                "submission_history_count": 0,
            }
            supabase.table("chamber_vendors").insert(vendor_data).execute()
            vendor_id_for_proposal = str(user_id)
            logger.info(f"Auto-created vendor record for user {user_id}")

    # Auto-assign business_group_id
    business_group_id = None
    try:
        bg_result = supabase.table("chamber_business_groups").select("id, name").execute()
        if bg_result.data:
            sector_lower = sector.lower()
            for bg in bg_result.data:
                if sector_lower in bg["name"].lower():
                    business_group_id = bg["id"]
                    break
    except Exception as bg_err:
        logger.warning(f"Business group lookup failed: {bg_err}")

    proposal_data = {
        "title": title,
        "sector": sector,
        "technology_type": technology_type,
        "maturity_level": maturity_level,
        "language": language,
        "description": description or None,
        "submitter_id": str(vendor_id_for_proposal),
        "status": "queued",
        "submission_date": datetime.now(timezone.utc).isoformat(),
        "is_duplicate": False,
        "requires_manual_review": False,
    }
    if business_group_id:
        proposal_data["business_group_id"] = str(business_group_id)

    result = supabase.table("chamber_proposals").insert(proposal_data).execute()

    if not result.data or len(result.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to create proposal", "code": 500},
        )

    proposal = result.data[0]

    # Attach document record if storage_path exists
    if storage_path:
        try:
            doc_data = {
                "proposal_id": str(proposal["id"]),
                "file_name": payload.get("file_name", "uploaded_document"),
                "file_type": "application/pdf",
                "file_size": payload.get("file_size", 0),
                "storage_path": storage_path,
                "uploaded_at": datetime.now(timezone.utc).isoformat(),
            }
            # Store extracted text from the ingestion step for Shield and evaluation use
            extracted_text_val = payload.get("extracted_text")
            if extracted_text_val:
                doc_data["extracted_text"] = extracted_text_val
            supabase.table("chamber_documents").insert(doc_data).execute()
        except Exception as doc_err:
            logger.warning(f"Failed to create document record: {doc_err}")

    # Increment vendor submission count
    try:
        vendor_row = (
            supabase.table("chamber_vendors")
            .select("submission_history_count")
            .eq("id", str(vendor_id_for_proposal))
            .maybe_single()
            .execute()
        )
        current_count = (vendor_row.data or {}).get("submission_history_count", 0)
        supabase.table("chamber_vendors").update({
            "submission_history_count": current_count + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", str(vendor_id_for_proposal)).execute()
    except Exception as inc_err:
        logger.warning(f"Failed to increment submission count: {inc_err}")

    # Run document sanitization on extracted text and/or description
    try:
        text_to_sanitize = payload.get("extracted_text", "") or description or ""
        if text_to_sanitize.strip():
            sanitize_proposal_content(
                proposal_id=str(proposal["id"]),
                raw_text=text_to_sanitize,
                user_id=str(user_id),
                source="ingest",
            )
    except Exception as san_err:
        logger.warning(f"Document sanitization failed (non-blocking): {san_err}")

    return {
        "proposal": proposal,
        "message": "Proposal created successfully from uploaded document",
    }

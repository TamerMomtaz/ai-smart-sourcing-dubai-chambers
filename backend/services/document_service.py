from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone, timedelta
from database import supabase
import os

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_FILE_TYPES = ["pdf", "docx", "pptx", "xlsx"]
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "proposal-documents").strip()


def create_document(
    user_id: UUID,
    proposal_id: UUID,
    file_name: str,
    file_type: str,
    file_size: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """
    Create a document record and return upload URL.
    Verifies proposal ownership before creating document.
    """
    # Verify proposal exists and user owns it
    proposal_response = (
        supabase.table("chamber_proposals")
        .select("id, created_by")
        .eq("id", str(proposal_id))
        .eq("created_by", str(user_id))
        .eq("deleted_at", None)
        .maybe_single()
        .execute()
    )

    if not proposal_response.data:
        return None

    # Validate file type
    if file_type not in ALLOWED_FILE_TYPES:
        return None

    # Validate file size
    if file_size and file_size > MAX_FILE_SIZE:
        return None

    # Create document record
    now = datetime.now(timezone.utc)
    document_data = {
        "proposal_id": str(proposal_id),
        "file_name": file_name,
        "file_type": file_type,
        "file_size": file_size or 0,
        "uploaded_at": now.isoformat(),
        "storage_path": f"{proposal_id}/{UUID.__new__(UUID).hex}.{file_type}",
        "created_by": str(user_id),
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    response = supabase.table("chamber_documents").insert(document_data).execute()

    if not response.data or len(response.data) == 0:
        return None

    document = response.data[0]
    document_id = document["id"]
    storage_path = document["storage_path"]

    # Generate signed upload URL (60 minute expiry)
    try:
        upload_url = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).create_signed_upload_url(
            storage_path
        )
        expires_at = now + timedelta(minutes=60)

        return {
            "document_id": document_id,
            "upload_url": upload_url["signedURL"] if isinstance(upload_url, dict) else upload_url,
            "expires_at": expires_at.isoformat(),
            "storage_path": storage_path,
        }
    except Exception:
        # Cleanup document record if URL generation fails
        supabase.table("chamber_documents").update({"deleted_at": now.isoformat()}).eq(
            "id", document_id
        ).execute()
        return None


def get_document_by_id(user_id: UUID, document_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get document by ID with ownership verification.
    Checks if user owns the proposal that the document belongs to.
    """
    response = (
        supabase.table("chamber_documents")
        .select(
            "id, proposal_id, file_name, file_type, file_size, uploaded_at, storage_path, "
            "extraction_status, extracted_at, chamber_proposals!inner(id, created_by)"
        )
        .eq("id", str(document_id))
        .eq("deleted_at", None)
        .eq("chamber_proposals.created_by", str(user_id))
        .eq("chamber_proposals.deleted_at", None)
        .maybe_single()
        .execute()
    )

    if not response.data:
        return None

    return response.data


def generate_download_url(user_id: UUID, document_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Generate temporary download URL for document.
    Verifies ownership before generating URL.
    """
    document = get_document_by_id(user_id, document_id)

    if not document:
        return None

    storage_path = document.get("storage_path")
    if not storage_path:
        return None

    # Generate signed download URL (15 minute expiry)
    try:
        download_url = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).create_signed_url(
            storage_path, expires_in=900
        )
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=15)

        return {
            "download_url": download_url["signedURL"] if isinstance(download_url, dict) else download_url,
            "expires_at": expires_at.isoformat(),
        }
    except Exception:
        return None


def get_extracted_data(user_id: UUID, document_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get AI-extracted data from document.
    Verifies ownership and extraction completion.
    """
    response = (
        supabase.table("chamber_documents")
        .select(
            "id, file_name, extraction_status, extracted_text, extracted_tables, "
            "extracted_charts, financial_data, language_detected, extracted_at, "
            "chamber_proposals!inner(id, created_by)"
        )
        .eq("id", str(document_id))
        .eq("deleted_at", None)
        .eq("chamber_proposals.created_by", str(user_id))
        .eq("chamber_proposals.deleted_at", None)
        .maybe_single()
        .execute()
    )

    if not response.data:
        return None

    document = response.data

    # Check extraction status
    extraction_status = document.get("extraction_status")
    if extraction_status != "completed":
        return {"status": extraction_status or "pending", "document_id": document_id}

    return {
        "document_id": document["id"],
        "file_name": document["file_name"],
        "extracted_text": document.get("extracted_text"),
        "extracted_tables": document.get("extracted_tables"),
        "extracted_charts": document.get("extracted_charts"),
        "financial_data": document.get("financial_data"),
        "language_detected": document.get("language_detected"),
        "extracted_at": document.get("extracted_at"),
    }


def list_documents_by_proposal(
    user_id: UUID, proposal_id: UUID, page: int = 1, page_size: int = 50
) -> Optional[Dict[str, Any]]:
    """
    List all documents for a proposal with pagination.
    Verifies proposal ownership.
    """
    # Verify proposal ownership
    proposal_response = (
        supabase.table("chamber_proposals")
        .select("id")
        .eq("id", str(proposal_id))
        .eq("created_by", str(user_id))
        .eq("deleted_at", None)
        .maybe_single()
        .execute()
    )

    if not proposal_response.data:
        return None

    offset = (page - 1) * page_size

    # Get total count
    count_response = (
        supabase.table("chamber_documents")
        .select("id", count="exact")
        .eq("proposal_id", str(proposal_id))
        .eq("deleted_at", None)
        .execute()
    )

    total = count_response.count or 0

    # Get paginated documents
    response = (
        supabase.table("chamber_documents")
        .select("id, file_name, file_type, file_size, uploaded_at, extraction_status")
        .eq("proposal_id", str(proposal_id))
        .eq("deleted_at", None)
        .order("uploaded_at", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    documents = response.data or []

    return {
        "documents": documents,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if page_size > 0 else 0,
        },
    }


def update_extraction_status(
    user_id: UUID,
    document_id: UUID,
    extraction_status: str,
    extracted_text: Optional[str] = None,
    extracted_tables: Optional[List[Dict[str, Any]]] = None,
    extracted_charts: Optional[List[Dict[str, Any]]] = None,
    financial_data: Optional[Dict[str, Any]] = None,
    language_detected: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update document extraction status and data.
    Verifies ownership before updating.
    """
    document = get_document_by_id(user_id, document_id)

    if not document:
        return None

    now = datetime.now(timezone.utc)
    update_data = {
        "extraction_status": extraction_status,
        "updated_at": now.isoformat(),
    }

    if extraction_status == "completed":
        update_data["extracted_at"] = now.isoformat()
        if extracted_text is not None:
            update_data["extracted_text"] = extracted_text
        if extracted_tables is not None:
            update_data["extracted_tables"] = extracted_tables
        if extracted_charts is not None:
            update_data["extracted_charts"] = extracted_charts
        if financial_data is not None:
            update_data["financial_data"] = financial_data
        if language_detected is not None:
            update_data["language_detected"] = language_detected

    response = (
        supabase.table("chamber_documents")
        .update(update_data)
        .eq("id", str(document_id))
        .execute()
    )

    if not response.data or len(response.data) == 0:
        return None

    return response.data[0]


def delete_document(user_id: UUID, document_id: UUID) -> bool:
    """
    Soft delete a document.
    Verifies ownership before deletion.
    """
    document = get_document_by_id(user_id, document_id)

    if not document:
        return False

    now = datetime.now(timezone.utc)
    response = (
        supabase.table("chamber_documents")
        .update({"deleted_at": now.isoformat(), "updated_at": now.isoformat()})
        .eq("id", str(document_id))
        .execute()
    )

    return bool(response.data and len(response.data) > 0)

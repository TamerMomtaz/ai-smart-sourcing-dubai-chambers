from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import JSONResponse
from uuid import UUID
import logging

from auth import get_current_user
from database import supabase
from services.document_sanitization_service import (
    extract_text_from_pdf,
    extract_text_from_docx,
    sanitize_proposal_content,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["proposal-documents"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "xlsx"}
ALLOWED_CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


def _get_extension(filename: str) -> Optional[str]:
    if "." not in filename:
        return None
    return filename.rsplit(".", 1)[-1].lower()


@router.post(
    "/{proposal_id}/documents",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Document uploaded successfully"},
        400: {"description": "Invalid file type or size"},
        403: {"description": "Access denied"},
        404: {"description": "Proposal not found"},
    },
)
async def upload_proposal_document(
    proposal_id: UUID,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload a document to a proposal. Accepts PDF, DOCX, PPTX, XLSX up to 20MB."""
    # Validate extension
    ext = _get_extension(file.filename or "")
    if not ext or ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validate content-type
    expected_ct = ALLOWED_CONTENT_TYPES.get(ext)
    if expected_ct and file.content_type and file.content_type != expected_ct:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content-Type mismatch. Expected {expected_ct} for .{ext} file.",
        )

    # Read file bytes and validate size
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds 20MB limit.",
        )

    # Verify proposal exists
    try:
        proposal_resp = (
            supabase.table("chamber_proposals")
            .select("id, submitter_id")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )
    except Exception as e:
        logger.error(f"Error checking proposal: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    if not proposal_resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    storage_path = f"{proposal_id}/{file.filename}"

    # Upload to Supabase Storage
    content_type = file.content_type or "application/octet-stream"
    try:
        print(f"UPLOAD: Uploading {file.filename} to proposal-documents/{storage_path}")
        storage_result = supabase.storage.from_("proposal-documents").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type},
        )
        print(f"UPLOAD: Storage result: {storage_result}")
    except Exception as e:
        import traceback as tb
        print(f"UPLOAD STORAGE ERROR: {tb.format_exc()}")
        error_msg = str(e)
        # If file already exists, remove and re-upload
        if "Duplicate" in error_msg or "already exists" in error_msg:
            try:
                supabase.storage.from_("proposal-documents").remove([storage_path])
                storage_result = supabase.storage.from_("proposal-documents").upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={"content-type": content_type},
                )
                print(f"UPLOAD: Re-upload storage result: {storage_result}")
            except Exception as retry_err:
                import traceback as tb2
                print(f"UPLOAD STORAGE RE-UPLOAD ERROR: {tb2.format_exc()}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Storage upload failed")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Storage upload failed")

    # Insert into chamber_documents
    try:
        doc_data = {
            "proposal_id": str(proposal_id),
            "file_name": file.filename,
            "file_type": ext,
            "file_size": len(file_bytes),
            "storage_path": storage_path,
        }
        print(f"UPLOAD: Inserting into chamber_documents: {doc_data}")
        result = supabase.table("chamber_documents").insert(doc_data).execute()
        print(f"UPLOAD: DB result: {result}")
        if not result.data:
            raise Exception("Insert returned no data")
        doc = result.data[0]

        # Run document sanitization (non-blocking — errors logged, not raised)
        sanitization_result = None
        try:
            extracted_text = ""
            if ext == "pdf":
                extracted_text = extract_text_from_pdf(file_bytes=file_bytes)
            elif ext == "docx":
                extracted_text = extract_text_from_docx(file_bytes=file_bytes)

            if extracted_text.strip():
                sanitization_result = sanitize_proposal_content(
                    proposal_id=str(proposal_id),
                    raw_text=extracted_text,
                    user_id=str(current_user["id"]),
                    source="document_upload",
                )
        except Exception as san_err:
            logger.warning(f"Document sanitization failed (non-blocking): {san_err}")

        response_content = {
            "document": {
                "id": str(doc.get("id", "")),
                "file_name": doc.get("file_name", ""),
                "file_type": doc.get("file_type", ""),
                "file_size": doc.get("file_size", 0),
                "storage_path": doc.get("storage_path", ""),
                "proposal_id": str(doc.get("proposal_id", "")),
                "uploaded_at": str(doc.get("uploaded_at", "")),
            },
            "message": "Document uploaded successfully",
        }
        if sanitization_result and sanitization_result.get("flagged"):
            response_content["security_flags_detected"] = True
            response_content["flag_count"] = len(sanitization_result.get("flags", []))

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=response_content,
        )
    except Exception as e:
        import traceback as tb
        print(f"UPLOAD DB ERROR: {tb.format_exc()}")
        # Clean up storage on DB failure
        try:
            supabase.storage.from_("proposal-documents").remove([storage_path])
        except Exception:
            pass
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create document record")


@router.get(
    "/{proposal_id}/documents",
    responses={
        200: {"description": "List of documents for proposal"},
        404: {"description": "Proposal not found"},
    },
)
async def list_proposal_documents(
    proposal_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """List all documents for a proposal with download URLs."""
    try:
        # Verify proposal exists
        proposal_resp = (
            supabase.table("chamber_proposals")
            .select("id")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )
        if not proposal_resp.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

        # Fetch documents
        docs_resp = (
            supabase.table("chamber_documents")
            .select("id, proposal_id, file_name, file_type, file_size, storage_path, uploaded_at, language_detected")
            .eq("proposal_id", str(proposal_id))
            .order("uploaded_at", desc=True)
            .execute()
        )

        documents = docs_resp.data or []

        # Generate signed download URLs
        for doc in documents:
            try:
                signed = supabase.storage.from_("proposal-documents").create_signed_url(
                    path=doc["storage_path"],
                    expires_in=3600,
                )
                doc["download_url"] = signed.get("signedURL") or signed.get("signedUrl") or ""
            except Exception:
                doc["download_url"] = ""

        return {"documents": documents}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing proposal documents: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list documents")


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Document deleted"},
        403: {"description": "Admin only"},
        404: {"description": "Document not found"},
    },
)
async def delete_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Delete a document from storage and database. Admin only."""
    user_role = current_user.get("role", "")
    if user_role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    try:
        # Get document record
        doc_resp = (
            supabase.table("chamber_documents")
            .select("id, storage_path")
            .eq("id", str(document_id))
            .maybe_single()
            .execute()
        )
        if not doc_resp.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        storage_path = doc_resp.data["storage_path"]

        # Remove from storage
        try:
            supabase.storage.from_("proposal-documents").remove([storage_path])
        except Exception as e:
            logger.warning(f"Storage deletion failed (continuing): {e}")

        # Remove from database
        supabase.table("chamber_documents").delete().eq("id", str(document_id)).execute()

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete document")

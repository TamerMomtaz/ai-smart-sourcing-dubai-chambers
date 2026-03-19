from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from datetime import datetime

from auth import get_current_user
from models.auth import UserInfo
from models.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentUploadResponse,
    DocumentDownloadResponse,
    ExtractedDocumentData,
)
from models.common import ErrorResponse, PaginationResponse
from services.chamber_document_service import ChamberDocumentService
from services.extracted_data_service import get_extracted_data_by_document_id
from services.download_service import generate_download_url
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chamber-documents", tags=["chamber-documents"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Document created, upload URL generated"},
        400: {"model": ErrorResponse, "description": "Invalid file type or size"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_document(
    proposal_id: UUID,
    document: DocumentCreate,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Create document record and generate pre-signed upload URL.
    Vendor can only upload to own proposals.
    """
    try:
        allowed_types = ["pdf", "docx", "pptx", "xlsx"]
        if document.file_type.lower() not in allowed_types:
            return {
                "error": "invalid_file_type",
                "detail": f"File type {document.file_type} not allowed. Allowed: {', '.join(allowed_types)}",
                "code": status.HTTP_400_BAD_REQUEST,
            }

        max_size = 50 * 1024 * 1024
        if document.file_size and document.file_size > max_size:
            return {
                "error": "file_too_large",
                "detail": f"File size exceeds 50MB limit",
                "code": status.HTTP_400_BAD_REQUEST,
            }

        storage_path = f"proposals/{str(proposal_id)}/{document.file_name}"

        result = ChamberDocumentService.create(
            user_id=current_user.id,
            proposal_id=proposal_id,
            file_name=document.file_name,
            file_type=document.file_type.lower(),
            file_size=document.file_size or 0,
            storage_path=storage_path,
        )

        if not result:
            return {
                "error": "creation_failed",
                "detail": "Failed to create document record or proposal not found",
                "code": status.HTTP_404_NOT_FOUND,
            }

        upload_url = f"https://api.supabase.io/storage/v1/upload/proposal-documents/{storage_path}"
        expires_at = datetime.utcnow().replace(tzinfo=None)
        expires_at = expires_at.replace(hour=expires_at.hour + 1)

        return DocumentUploadResponse(
            document_id=result["id"],
            upload_url=upload_url,
            expires_at=expires_at,
        )

    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        return {
            "error": "internal_error",
            "detail": "An error occurred while creating document",
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }


@router.get(
    "",
    response_model=dict,
    responses={
        200: {"description": "List of documents with pagination"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_documents(
    proposal_id: Optional[UUID] = Query(None, description="Filter by proposal ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: UserInfo = Depends(get_current_user),
):
    """
    List documents with optional proposal filter.
    Vendors see only own documents, analysts see all.
    """
    try:
        offset = (page - 1) * page_size

        from database import supabase

        query = supabase.table("chamber_documents").select(
            "id, proposal_id, file_name, file_type, file_size, uploaded_at, storage_path",
            count="exact",
        )

        if proposal_id:
            query = query.eq("proposal_id", str(proposal_id))

        if current_user.role == "vendor":
            vendor_proposals_response = (
                supabase.table("chamber_proposals")
                .select("id")
                .eq("submitter_id", str(current_user.id))
                .execute()
            )
            if not vendor_proposals_response.data:
                return {
                    "documents": [],
                    "pagination": PaginationResponse(
                        total=0, page=page, page_size=page_size, total_pages=0
                    ),
                }
            proposal_ids = [p["id"] for p in vendor_proposals_response.data]
            query = query.in_("proposal_id", proposal_ids)

        response = query.order("uploaded_at", desc=True).range(offset, offset + page_size - 1).execute()

        total = response.count if hasattr(response, "count") else len(response.data)
        total_pages = (total + page_size - 1) // page_size

        documents = [
            {
                "id": doc["id"],
                "proposal_id": doc.get("proposal_id"),
                "file_name": doc["file_name"],
                "file_type": doc["file_type"],
                "file_size": doc["file_size"],
                "uploaded_at": doc["uploaded_at"],
            }
            for doc in response.data
        ]

        return {
            "documents": documents,
            "pagination": PaginationResponse(
                total=total, page=page, page_size=page_size, total_pages=total_pages
            ),
        }

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        return {
            "error": "internal_error",
            "detail": "An error occurred while listing documents",
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    responses={
        200: {"description": "Document details"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_document(
    document_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Get document details by ID.
    Vendors can only access documents from their own proposals.
    """
    try:
        from database import supabase

        doc_response = (
            supabase.table("chamber_documents")
            .select("id, proposal_id, file_name, file_type, file_size, uploaded_at, storage_path")
            .eq("id", str(document_id))
            .maybe_single()
            .execute()
        )

        if not doc_response.data:
            return {
                "error": "not_found",
                "detail": "Document not found",
                "code": status.HTTP_404_NOT_FOUND,
            }

        doc = doc_response.data

        if current_user.role == "vendor":
            proposal_response = (
                supabase.table("chamber_proposals")
                .select("submitter_id")
                .eq("id", doc["proposal_id"])
                .maybe_single()
                .execute()
            )
            if not proposal_response.data or str(
                proposal_response.data["submitter_id"]
            ) != str(current_user.id):
                return {
                    "error": "access_denied",
                    "detail": "You do not have permission to access this document",
                    "code": status.HTTP_403_FORBIDDEN,
                }

        return DocumentResponse(
            id=doc["id"],
            file_name=doc["file_name"],
            file_type=doc["file_type"],
            file_size=doc["file_size"],
            uploaded_at=doc["uploaded_at"],
        )

    except Exception as e:
        logger.error(f"Error fetching document: {str(e)}")
        return {
            "error": "internal_error",
            "detail": "An error occurred while fetching document",
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }


@router.get(
    "/{document_id}/download",
    responses={
        200: {"description": "Pre-signed download URL"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def download_document(
    document_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Generate pre-signed download URL for document.
    Vendors can only download their own documents.
    """
    try:
        result = generate_download_url(
            user_id=str(current_user.id),
            document_id=str(document_id),
            user_role=current_user.role,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or access denied",
            )

        return DocumentDownloadResponse(
            download_url=result["download_url"],
            expires_at=result["expires_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while generating download URL",
        )


@router.get(
    "/{document_id}/extracted-data",
    response_model=ExtractedDocumentData,
    responses={
        200: {"description": "AI-extracted document data"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Document or extracted data not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_extracted_data(
    document_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Get AI-extracted data from document.
    Analysts and executives only.
    """
    try:
        if current_user.role not in ["analyst", "executive", "business_group_lead", "compliance_officer"]:
            return {
                "error": "access_denied",
                "detail": "Only analysts and executives can access extracted data",
                "code": status.HTTP_403_FORBIDDEN,
            }

        result = get_extracted_data_by_document_id(
            user_id=current_user.id, document_id=document_id
        )

        if not result:
            return {
                "error": "not_found",
                "detail": "Extracted data not found for this document",
                "code": status.HTTP_404_NOT_FOUND,
            }

        return result

    except Exception as e:
        logger.error(f"Error fetching extracted data: {str(e)}")
        return {
            "error": "internal_error",
            "detail": "An error occurred while fetching extracted data",
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Document deleted successfully"},
        403: {"model": ErrorResponse, "description": "Access denied"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_document(
    document_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
):
    """
    Delete document and storage file.
    Vendors can only delete documents from draft proposals.
    """
    try:
        from database import supabase

        doc_response = (
            supabase.table("chamber_documents")
            .select("id, proposal_id, storage_path")
            .eq("id", str(document_id))
            .maybe_single()
            .execute()
        )

        if not doc_response.data:
            return {
                "error": "not_found",
                "detail": "Document not found",
                "code": status.HTTP_404_NOT_FOUND,
            }

        doc = doc_response.data

        if current_user.role == "vendor":
            proposal_response = (
                supabase.table("chamber_proposals")
                .select("submitter_id, status")
                .eq("id", doc["proposal_id"])
                .maybe_single()
                .execute()
            )

            if not proposal_response.data:
                return {
                    "error": "not_found",
                    "detail": "Proposal not found",
                    "code": status.HTTP_404_NOT_FOUND,
                }

            proposal = proposal_response.data

            if str(proposal["submitter_id"]) != str(current_user.id):
                return {
                    "error": "access_denied",
                    "detail": "You do not have permission to delete this document",
                    "code": status.HTTP_403_FORBIDDEN,
                }

            if proposal["status"] not in ["draft", "submitted"]:
                return {
                    "error": "invalid_state",
                    "detail": "Cannot delete documents from proposals that are being evaluated or completed",
                    "code": status.HTTP_400_BAD_REQUEST,
                }

        delete_response = (
            supabase.table("chamber_documents")
            .delete()
            .eq("id", str(document_id))
            .execute()
        )

        if not delete_response.data:
            return {
                "error": "deletion_failed",
                "detail": "Failed to delete document",
                "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            }

        return None

    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        return {
            "error": "internal_error",
            "detail": "An error occurred while deleting document",
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        }

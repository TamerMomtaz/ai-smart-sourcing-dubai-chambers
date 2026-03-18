from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
import logging

from models import (
    DocumentResponse,
    DocumentDownloadResponse,
    ExtractedDocumentData,
    ErrorResponse,
    PaginationResponse,
)
from auth import get_current_user
from services import download_service, extracted_data_service
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])


@router.get(
    "/documents",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def list_documents(
    proposal_id: Optional[UUID] = Query(None, description="Filter by proposal ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> dict:
    """List documents with optional proposal filter and pagination."""
    try:
        user_id = current_user["id"]
        user_role = current_user["role"]
        offset = (page - 1) * page_size

        query = supabase.table("chamber_documents").select(
            "id, proposal_id, file_name, file_type, file_size, uploaded_at, storage_path",
            count="exact",
        )

        if proposal_id:
            query = query.eq("proposal_id", str(proposal_id))

        if user_role == "vendor":
            vendor_proposals_response = (
                supabase.table("chamber_proposals")
                .select("id")
                .eq("submitter_id", str(user_id))
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

        documents = response.data if response.data else []
        total = response.count if hasattr(response, "count") and response.count else len(documents)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "documents": [
                DocumentResponse(
                    id=doc["id"],
                    file_name=doc["file_name"],
                    file_type=doc["file_type"],
                    file_size=doc["file_size"],
                    uploaded_at=doc["uploaded_at"],
                )
                for doc in documents
            ],
            "pagination": PaginationResponse(
                total=total, page=page, page_size=page_size, total_pages=total_pages
            ),
        }

    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "Failed to list documents",
                "code": 500,
            },
        )


@router.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_document(
    document_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> DocumentResponse:
    """Get document details by ID."""
    try:
        user_id = current_user["id"]
        user_role = current_user["role"]

        doc_response = (
            supabase.table("chamber_documents")
            .select("id, proposal_id, file_name, file_type, file_size, uploaded_at, storage_path")
            .eq("id", str(document_id))
            .maybe_single()
            .execute()
        )

        if not doc_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Not found",
                    "detail": "Document not found",
                    "code": 404,
                },
            )

        doc = doc_response.data

        if user_role == "vendor":
            proposal_response = (
                supabase.table("chamber_proposals")
                .select("submitter_id")
                .eq("id", doc["proposal_id"])
                .maybe_single()
                .execute()
            )
            if not proposal_response.data or str(proposal_response.data["submitter_id"]) != str(user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Forbidden",
                        "detail": "You do not have permission to access this document",
                        "code": 403,
                    },
                )

        return DocumentResponse(
            id=doc["id"],
            file_name=doc["file_name"],
            file_type=doc["file_type"],
            file_size=doc["file_size"],
            uploaded_at=doc["uploaded_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "Failed to retrieve document",
                "code": 500,
            },
        )


@router.get(
    "/documents/{document_id}/download",
    response_model=DocumentDownloadResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions to access this document"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def generate_document_download_url(
    document_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> DocumentDownloadResponse:
    """
    Generate temporary download URL for proposal document.
    Verifies user has permission to access the document via proposal ownership or role.
    Returns pre-signed URL valid for 1 hour.
    """
    try:
        user_id = current_user["id"]
        user_role = current_user["role"]

        # Generate download URL with permission verification
        result = download_service.generate_download_url(
            user_id=user_id,
            document_id=str(document_id),
            user_role=user_role,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Document not found",
                    "detail": f"Document {document_id} not found or you do not have permission to access it",
                    "code": 404,
                },
            )

        # Check for explicit permission denial
        if result.get("error") == "forbidden":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "You do not have permission to access this document",
                    "code": 403,
                },
            )

        return DocumentDownloadResponse(
            download_url=result["download_url"],
            expires_at=result["expires_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download URL for document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "Failed to generate document download URL",
                "code": 500,
            },
        )


@router.get(
    "/documents/{document_id}/extracted-data",
    response_model=ExtractedDocumentData,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        425: {"model": ErrorResponse, "description": "Extraction not yet complete"},
    },
)
async def get_extracted_document_data(
    document_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ExtractedDocumentData:
    """
    Get AI-extracted data from document.
    Returns text, tables, charts, and financial data extracted via Claude API.
    Only accessible to analysts, business group leads, compliance officers, and executives.
    Vendors cannot access extracted data.
    """
    try:
        user_id = current_user["id"]
        user_role = current_user["role"]

        # Role-based access control
        allowed_roles = ["analyst", "business_group_lead", "compliance_officer", "executive", "admin"]
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "You do not have permission to access extracted document data",
                    "code": 403,
                },
            )

        # Retrieve extracted data
        result = extracted_data_service.get_extracted_data_by_document_id(
            user_id=UUID(user_id),
            document_id=document_id,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Document not found",
                    "detail": f"Document {document_id} not found or you do not have permission to access it",
                    "code": 404,
                },
            )

        # Check if extraction is still in progress
        if result.extracted_text is None and result.extracted_tables is None:
            raise HTTPException(
                status_code=status.HTTP_425_TOO_EARLY,
                detail={
                    "error": "Extraction not yet complete",
                    "detail": "Document extraction is still in progress. Please try again later.",
                    "code": 425,
                },
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving extracted data for document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "Failed to retrieve extracted document data",
                "code": 500,
            },
        )

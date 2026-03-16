from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
import logging

from models import (
    DocumentCreate,
    DocumentUploadResponse,
    DocumentDownloadResponse,
    ExtractedDocumentData,
    ErrorResponse,
)
from auth import get_current_user
from services import document_service, download_service, extracted_data_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])


@router.post(
    "/proposals/{proposal_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Proposal not found"},
        413: {"model": ErrorResponse, "description": "File too large - max 50MB"},
    },
)
async def upload_document_to_proposal(
    proposal_id: UUID,
    body: DocumentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> DocumentUploadResponse:
    """
    Upload document to existing proposal.
    Generates pre-signed upload URL for direct client upload to Supabase Storage.
    Validates file type and size limits.
    """
    try:
        user_id = current_user["id"]
        user_role = current_user["role"]

        # Validate file type
        if body.file_type not in ["pdf", "docx", "pptx", "xlsx"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Invalid file type",
                    "detail": f"File type {body.file_type} not allowed. Allowed types: pdf, docx, pptx, xlsx",
                    "code": 400,
                },
            )

        # Validate file size (max 50MB)
        max_file_size = 50 * 1024 * 1024  # 50MB in bytes
        if body.file_size and body.file_size > max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": "File too large",
                    "detail": f"File size {body.file_size} bytes exceeds maximum allowed size of 50MB",
                    "code": 413,
                },
            )

        # Create document record and generate upload URL
        result = document_service.create_document(
            user_id=UUID(user_id),
            proposal_id=proposal_id,
            file_name=body.file_name,
            file_type=body.file_type,
            file_size=body.file_size or 0,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Proposal not found",
                    "detail": f"Proposal {proposal_id} not found or you do not have permission to upload documents",
                    "code": 404,
                },
            )

        return DocumentUploadResponse(
            document_id=result["document_id"],
            upload_url=result["upload_url"],
            expires_at=result["expires_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document to proposal {proposal_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "Failed to create document upload URL",
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

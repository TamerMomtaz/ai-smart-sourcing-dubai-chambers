from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
import logging
import os

from auth.dependencies import get_current_user
from models.auth import UserInfo
from models.document import DocumentDownloadResponse
from models.common import ErrorResponse
from services.download_service import generate_download_url
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["download"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)

SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "proposal-documents").strip()
DOWNLOAD_URL_EXPIRY_SECONDS = int(os.getenv("DOWNLOAD_URL_EXPIRY_SECONDS", "3600").strip())


@router.get(
    "/{document_id}/download",
    response_model=DocumentDownloadResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate temporary download URL for proposal document",
    description="Generate a pre-signed temporary download URL for a document. Verifies user has access to the document's proposal before generating URL. Supports analyst, business_group_lead, compliance_officer, and executive roles with appropriate scope filtering.",
)
async def get_document_download_url(
    document_id: UUID,
    current_user: UserInfo = Depends(get_current_user),
) -> DocumentDownloadResponse:
    """
    Generate temporary download URL for proposal document.

    **Access Control:**
    - Vendors: Can download documents from their own proposals only
    - Analysts: Can download all documents
    - Business Group Leads: Can download documents from proposals in their sector
    - Compliance Officers: Can download all documents
    - Executives: Can download all documents

    **Security:**
    - Pre-signed URL expires after 1 hour (configurable)
    - Document access verified via proposal ownership/permissions
    - All access attempts logged for audit trail

    **Rate Limit:** 120 requests/minute
    """
    try:
        # Step 1: Fetch document and verify it exists
        document_response = (
            supabase.table("chamber_documents")
            .select("id, proposal_id, file_name, storage_path, uploaded_at")
            .eq("id", str(document_id))
            .maybe_single()
            .execute()
        )

        if not document_response.data:
            logger.warning(
                f"Document not found: document_id={document_id}, user_id={current_user.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Document not found",
                    "detail": f"Document with ID {document_id} does not exist",
                    "code": "DOCUMENT_NOT_FOUND",
                },
            )

        document = document_response.data
        proposal_id = document["proposal_id"]
        storage_path = document["storage_path"]

        # Step 2: Verify user has access to the proposal
        proposal_response = (
            supabase.table("chamber_proposals")
            .select("id, submitter_id, business_group_id, status")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )

        if not proposal_response.data:
            logger.error(
                f"Proposal not found for document: document_id={document_id}, proposal_id={proposal_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Data integrity error",
                    "detail": "Document references non-existent proposal",
                    "code": "DATA_INTEGRITY_ERROR",
                },
            )

        proposal = proposal_response.data
        submitter_id = proposal["submitter_id"]
        business_group_id = proposal.get("business_group_id")

        # Step 3: Role-based access control
        user_role = current_user.role
        user_id_str = str(current_user.id)

        if user_role == "vendor":
            # Vendors can only download documents from their own proposals
            if submitter_id != user_id_str:
                logger.warning(
                    f"Vendor access denied: user_id={current_user.id}, document_id={document_id}, submitter_id={submitter_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Forbidden",
                        "detail": "You do not have permission to access this document",
                        "code": "INSUFFICIENT_PERMISSIONS",
                    },
                )

        elif user_role == "business_group_lead":
            # Business group leads can only download documents from proposals in their sector
            if not current_user.business_group_id:
                logger.error(
                    f"Business group lead missing business_group_id: user_id={current_user.id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Forbidden",
                        "detail": "Business group lead not assigned to any business group",
                        "code": "NO_BUSINESS_GROUP_ASSIGNED",
                    },
                )

            if business_group_id != str(current_user.business_group_id):
                logger.warning(
                    f"Business group lead access denied: user_id={current_user.id}, document_id={document_id}, user_business_group={current_user.business_group_id}, proposal_business_group={business_group_id}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "Forbidden",
                        "detail": "You do not have permission to access documents from this business group",
                        "code": "INSUFFICIENT_PERMISSIONS",
                    },
                )

        elif user_role in ["analyst", "compliance_officer", "executive", "admin"]:
            # Full access - no additional checks needed
            pass

        else:
            logger.error(f"Unknown user role: user_id={current_user.id}, role={user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Forbidden",
                    "detail": "Invalid user role",
                    "code": "INVALID_ROLE",
                },
            )

        # Step 4: Generate pre-signed download URL
        try:
            download_url_response = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).create_signed_url(
                storage_path, DOWNLOAD_URL_EXPIRY_SECONDS
            )

            if not download_url_response or "signedURL" not in download_url_response:
                logger.error(
                    f"Failed to generate signed URL: document_id={document_id}, storage_path={storage_path}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail={
                        "error": "Storage error",
                        "detail": "Failed to generate download URL",
                        "code": "STORAGE_URL_GENERATION_FAILED",
                    },
                )

            signed_url = download_url_response["signedURL"]
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=DOWNLOAD_URL_EXPIRY_SECONDS)

            logger.info(
                f"Download URL generated: user_id={current_user.id}, role={user_role}, document_id={document_id}, proposal_id={proposal_id}"
            )

            return DocumentDownloadResponse(
                download_url=signed_url,
                expires_at=expires_at,
            )

        except Exception as storage_error:
            logger.error(
                f"Storage error generating signed URL: document_id={document_id}, error={str(storage_error)}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Storage error",
                    "detail": "Failed to generate download URL from storage backend",
                    "code": "STORAGE_BACKEND_ERROR",
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in get_document_download_url: document_id={document_id}, user_id={current_user.id}, error={str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": "An unexpected error occurred while generating download URL",
                "code": "INTERNAL_ERROR",
            },
        )

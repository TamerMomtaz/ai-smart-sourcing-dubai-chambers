from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from uuid import UUID
import logging

from auth import get_current_user
from models.document import ExtractedDocumentData
from models.common import ErrorResponse
from services.extracted_data_service import get_extracted_data_by_document_id

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["extracted-data"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Document not found"},
        425: {"model": ErrorResponse, "description": "Extraction not yet complete"},
    },
)


@router.get(
    "/{document_id}/extracted-data",
    response_model=ExtractedDocumentData,
    summary="Get AI-extracted data from document",
    description="Retrieve AI-extracted text, tables, charts, and financial data from a document. Requires document ownership through proposal relationship.",
    status_code=status.HTTP_200_OK,
)
async def get_extracted_data(
    document_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> ExtractedDocumentData:
    """
    Get AI-extracted data from document (text, tables, charts, financials).
    
    **Authorization**: Requires valid JWT token. User must have access to the proposal
    that owns this document (vendors can only access their own documents, analysts/executives
    can access all documents).
    
    **Business Logic**:
    - Verifies document exists
    - Validates user has access through proposal ownership
    - Returns extraction status if processing incomplete
    - Returns full extracted data including text, tables, charts, financial data
    - Language detection included in response
    
    **Error Cases**:
    - 401: Missing or invalid authentication token
    - 403: User does not have access to this document
    - 404: Document does not exist
    - 425: Document extraction is still in progress
    """
    try:
        user_id = UUID(current_user["user_id"])
        user_role = current_user.get("role", "")
        
        logger.info(
            f"User {user_id} ({user_role}) requesting extracted data for document {document_id}"
        )
        
        extracted_data = get_extracted_data_by_document_id(
            user_id=user_id,
            document_id=document_id,
        )
        
        if extracted_data is None:
            logger.warning(
                f"Document {document_id} not found or user {user_id} lacks access"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Document Not Found",
                    "detail": "Document does not exist or you do not have permission to access it",
                    "code": "DOCUMENT_NOT_FOUND",
                },
            )
        
        # Check if extraction is complete
        if extracted_data.extracted_text is None and extracted_data.extracted_tables is None:
            logger.info(
                f"Document {document_id} extraction not yet complete"
            )
            raise HTTPException(
                status_code=status.HTTP_425_TOO_EARLY,
                detail={
                    "error": "Extraction In Progress",
                    "detail": "Document extraction has not completed yet. Please try again in a few moments.",
                    "code": "EXTRACTION_NOT_COMPLETE",
                },
            )
        
        logger.info(
            f"Successfully retrieved extracted data for document {document_id}"
        )
        
        return extracted_data
    
    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"Validation error retrieving extracted data: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid Request",
                "detail": str(ve),
                "code": "INVALID_DOCUMENT_ID",
            },
        )
    except Exception as e:
        logger.error(
            f"Unexpected error retrieving extracted data for document {document_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred while retrieving extracted data",
                "code": "INTERNAL_ERROR",
            },
        )

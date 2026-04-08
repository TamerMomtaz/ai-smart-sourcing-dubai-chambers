"""RAG-based Compliance Knowledge Base — API routes.

Provides endpoints to seed the compliance knowledge base and verify
vendor claims against official records.
"""

from fastapi import APIRouter, Depends, HTTPException, status
import logging

from auth import get_current_user
from models.compliance import ClaimVerifyRequest, ClaimVerifyResponse, KnowledgeSeedResponse
from services import compliance_knowledge_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["Compliance Knowledge Base"])


@router.post(
    "/knowledge/seed",
    status_code=status.HTTP_201_CREATED,
    response_model=KnowledgeSeedResponse,
)
async def seed_knowledge_base(
    current_user: dict = Depends(get_current_user),
):
    """Seed the compliance knowledge base with official compliance documents.

    Admin only. Seeds DESC certified providers, ISO framework requirements,
    CSA CCM control domains, and ISR V3 domain summaries.
    """
    allowed_roles = ["admin"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Admin role required", "code": 403},
        )

    try:
        result = compliance_knowledge_service.seed_knowledge_base(
            user_id=current_user["id"],
        )
        return result
    except Exception as e:
        logger.error(f"[RAG] Seed failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to seed knowledge base", "detail": str(e), "code": 500},
        )


@router.post(
    "/verify-claim",
    status_code=status.HTTP_200_OK,
    response_model=ClaimVerifyResponse,
)
async def verify_claim(
    payload: ClaimVerifyRequest,
    current_user: dict = Depends(get_current_user),
):
    """Verify a vendor compliance claim against the official knowledge base.

    Admin and analyst roles. Uses RAG to find relevant official documents
    and AI to determine if the claim is supported.
    """
    allowed_roles = ["admin", "analyst"]
    if current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "Admin or analyst role required", "code": 403},
        )

    try:
        result = compliance_knowledge_service.verify_claim(
            claim=payload.claim,
            user_id=current_user["id"],
        )
        return result
    except Exception as e:
        logger.error(f"[RAG] Verify claim failed: {e}", exc_info=True)
        is_ai_failure = "All AI providers failed" in str(e)
        raise HTTPException(
            status_code=503 if is_ai_failure else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AI service temporarily busy. Please try again in 1-2 minutes."
            }
            if is_ai_failure
            else {"error": "Failed to verify claim", "detail": str(e), "code": 500},
        )

"""σI Hallucination Shield — API routes for AI integrity verification."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from auth import get_current_user
from database import supabase
from services.hallucination_service import HallucinationShield

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Hallucination Shield"])

shield = HallucinationShield()


@router.post(
    "/evaluations/{evaluation_id}/verify",
    status_code=status.HTTP_200_OK,
)
async def verify_evaluation(
    evaluation_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """
    Run σI Hallucination Shield verification on a completed evaluation.
    Extracts claims, checks grounding, and runs cross-model verification.
    """
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized", "detail": "Invalid user session", "code": 401},
        )

    try:
        # Fetch the evaluation
        eval_result = (
            supabase.table("chamber_evaluations")
            .select("*")
            .eq("id", str(evaluation_id))
            .maybe_single()
            .execute()
        )
        if not eval_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Evaluation not found", "code": 404},
            )

        evaluation = eval_result.data
        proposal_id = evaluation.get("proposal_id")

        # Fetch the proposal
        proposal_result = (
            supabase.table("chamber_proposals")
            .select("*")
            .eq("id", str(proposal_id))
            .maybe_single()
            .execute()
        )
        if not proposal_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "Proposal not found", "code": 404},
            )

        proposal = proposal_result.data
        proposal_text = proposal.get("description", "") or ""

        # Fetch extracted text from ALL uploaded documents for this proposal
        try:
            doc_result = (
                supabase.table("chamber_documents")
                .select("file_name, extracted_text")
                .eq("proposal_id", str(proposal_id))
                .execute()
            )
            if doc_result.data:
                for doc in doc_result.data:
                    if doc.get("extracted_text"):
                        proposal_text += f"\n\n--- Document: {doc['file_name']} ---\n{doc['extracted_text']}"
        except Exception as doc_err:
            logger.warning(f"[SHIELD] Failed to fetch document texts: {doc_err}")

        # Build combined reasoning text from all dimensions
        reasoning_parts = []
        for dim in ["relevance", "feasibility", "sector", "compliance"]:
            reasoning_key = f"{dim}_reasoning"
            if evaluation.get(reasoning_key):
                reasoning_parts.append(f"{dim.title()}: {evaluation[reasoning_key]}")
        if evaluation.get("summary_en"):
            reasoning_parts.append(f"Summary: {evaluation['summary_en']}")
        evaluation_reasoning = "\n".join(reasoning_parts)

        # Build scores dict
        evaluation_scores = {
            "composite_score": evaluation.get("composite_score"),
            "relevance_score": evaluation.get("relevance_score"),
            "feasibility_score": evaluation.get("feasibility_score"),
            "sector_alignment_score": evaluation.get("sector_alignment_score"),
            "compliance_score": evaluation.get("compliance_score"),
        }

        # Run verification
        report = await shield.verify_evaluation(
            evaluation_id=str(evaluation_id),
            proposal_id=str(proposal_id),
            evaluation_reasoning=evaluation_reasoning,
            proposal_text=proposal_text,
            evaluation_scores=evaluation_scores,
            user_id=user_id,
        )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SHIELD] Verification error: {e}", exc_info=True)
        is_ai_failure = "All AI providers failed" in str(e)
        raise HTTPException(
            status_code=503 if is_ai_failure else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AI service temporarily busy. Please try again in 1-2 minutes."
            }
            if is_ai_failure
            else {"error": "Verification failed", "detail": str(e), "code": 500},
        )


@router.get(
    "/evaluations/{evaluation_id}/shield",
    status_code=status.HTTP_200_OK,
)
async def get_shield_report(
    evaluation_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get existing hallucination check for an evaluation."""
    try:
        result = (
            supabase.table("chamber_hallucination_checks")
            .select("*")
            .eq("evaluation_id", str(evaluation_id))
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "No hallucination check found for this evaluation", "code": 404},
            )

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[SHIELD] Error fetching shield report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to fetch shield report", "detail": str(e), "code": 500},
        )


@router.get(
    "/hallucination/stats",
    status_code=status.HTTP_200_OK,
)
async def get_hallucination_stats(
    current_user: dict = Depends(get_current_user),
):
    """Aggregate hallucination shield stats for the ΣI dashboard."""
    try:
        result = (
            supabase.table("chamber_hallucination_checks")
            .select("grounding_score, hallucination_risk, verification_iu, verification_cost_usd")
            .execute()
        )

        checks = result.data or []
        total_checks = len(checks)

        if total_checks == 0:
            return {
                "total_checks": 0,
                "average_grounding_score": 0,
                "risk_distribution": {"low": 0, "medium": 0, "high": 0},
                "total_verification_iu": 0,
                "total_verification_cost_usd": 0,
                "all_verified": False,
            }

        avg_score = sum(float(c.get("grounding_score", 0)) for c in checks) / total_checks
        risk_dist = {"low": 0, "medium": 0, "high": 0}
        for c in checks:
            risk = c.get("hallucination_risk", "low")
            if risk in risk_dist:
                risk_dist[risk] += 1

        total_iu = sum(float(c.get("verification_iu", 0)) for c in checks)
        total_cost = sum(float(c.get("verification_cost_usd", 0)) for c in checks)

        # Check if all evaluations have been verified
        eval_count_result = (
            supabase.table("chamber_evaluations")
            .select("id", count="exact")
            .execute()
        )
        total_evaluations = eval_count_result.count if eval_count_result.count else 0
        all_verified = total_checks >= total_evaluations and total_evaluations > 0

        return {
            "total_checks": total_checks,
            "average_grounding_score": round(avg_score, 1),
            "risk_distribution": risk_dist,
            "total_verification_iu": round(total_iu, 4),
            "total_verification_cost_usd": round(total_cost, 6),
            "all_verified": all_verified,
            "total_evaluations": total_evaluations,
        }

    except Exception as e:
        logger.error(f"[SHIELD] Error fetching stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Failed to fetch shield stats", "detail": str(e), "code": 500},
        )

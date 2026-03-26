from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


def create_proposal(
    user_id: UUID,
    title: str,
    sector: str,
    technology_type: str,
    maturity_level: str,
    language: str,
    business_group_id: Optional[UUID] = None,
    description: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Create new proposal (vendor-only operation)."""
    try:
        proposal_data = {
            "title": title,
            "submitter_id": str(user_id),
            "sector": sector,
            "technology_type": technology_type,
            "maturity_level": maturity_level,
            "language": language,
            "status": "submitted",
            "submission_date": datetime.now(timezone.utc).isoformat(),
            "is_duplicate": False,
            "requires_manual_review": False,
            "created_by": str(user_id),
        }
        
        if business_group_id:
            proposal_data["business_group_id"] = str(business_group_id)
        if description:
            proposal_data["description"] = description
        
        response = supabase.table("chamber_proposals").insert(proposal_data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception:
        return None


def list_proposals(
    user_id: UUID,
    user_role: str,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    sector: Optional[str] = None,
    submitter_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """List proposals with filtering and pagination."""
    try:
        offset = (page - 1) * page_size
        
        query = supabase.table("chamber_proposals").select(
            "id, title, submitter_id, submission_date, status, sector, "
            "technology_type, maturity_level, composite_score, is_duplicate, "
            "requires_manual_review, evaluation_timestamp, updated_at",
            count="exact"
        )
        
        # Vendors can only see their own proposals
        if user_role == "vendor":
            query = query.eq("submitter_id", str(user_id))
        elif submitter_id:
            query = query.eq("submitter_id", str(submitter_id))
        
        if status:
            query = query.eq("status", status)
        if sector:
            query = query.eq("sector", sector)
        
        query = query.order("submission_date", desc=True)
        query = query.range(offset, offset + page_size - 1)
        
        response = query.execute()

        total = response.count if hasattr(response, "count") else 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        proposals = response.data or []

        # Enrich proposals with audit data from chamber_compliance_audits
        if proposals:
            proposal_ids = [p["id"] for p in proposals]
            try:
                audit_response = supabase.table("chamber_compliance_audits").select(
                    "proposal_id, findings_json"
                ).in_("proposal_id", proposal_ids).order(
                    "audit_timestamp", desc=True
                ).execute()

                # Build map: proposal_id -> latest audit score
                audit_map = {}
                for audit in (audit_response.data or []):
                    pid = audit["proposal_id"]
                    if pid not in audit_map:
                        findings = audit.get("findings_json")
                        if isinstance(findings, str):
                            import json as _json
                            try:
                                findings = _json.loads(findings)
                            except Exception:
                                findings = {}
                        elif findings is None:
                            findings = {}
                        audit_map[pid] = findings.get("overall_score")

                for p in proposals:
                    if p["id"] in audit_map:
                        p["has_audit"] = True
                        p["audit_score"] = audit_map[p["id"]]
                    else:
                        p["has_audit"] = False
                        p["audit_score"] = None
            except Exception:
                for p in proposals:
                    p["has_audit"] = False
                    p["audit_score"] = None

        return {
            "proposals": proposals,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
        }
    except Exception:
        return {
            "proposals": [],
            "pagination": {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
            },
        }


def get_proposal_by_id(
    user_id: UUID,
    user_role: str,
    proposal_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Get detailed proposal information."""
    try:
        # Fetch proposal
        proposal_response = supabase.table("chamber_proposals").select("*").eq("id", str(proposal_id)).execute()
        
        if not proposal_response.data or len(proposal_response.data) == 0:
            return None
        
        proposal = proposal_response.data[0]
        
        # Verify ownership for vendors
        if user_role == "vendor" and proposal.get("submitter_id") != str(user_id):
            return None
        
        # Fetch vendor info
        vendor_response = supabase.table("chamber_vendors").select(
            "id, name, company_registration, is_desc_approved"
        ).eq("id", proposal.get("submitter_id")).execute()
        
        proposal["vendor"] = vendor_response.data[0] if vendor_response.data else None
        
        # Fetch documents
        docs_response = supabase.table("chamber_documents").select(
            "id, file_name, file_type, file_size, uploaded_at"
        ).eq("proposal_id", str(proposal_id)).execute()
        
        proposal["documents"] = docs_response.data or []
        
        # Fetch evaluation
        eval_response = supabase.table("chamber_evaluations").select("*").eq(
            "proposal_id", str(proposal_id)
        ).execute()
        
        if eval_response.data and len(eval_response.data) > 0:
            evaluation = eval_response.data[0]
            proposal["evaluation"] = {
                "relevance_reasoning": evaluation.get("relevance_reasoning"),
                "feasibility_reasoning": evaluation.get("feasibility_reasoning"),
                "sector_reasoning": evaluation.get("sector_reasoning"),
                "compliance_reasoning": evaluation.get("compliance_reasoning"),
                "summary_en": evaluation.get("summary_en"),
                "summary_ar": evaluation.get("summary_ar"),
                "hallucination_check_passed": evaluation.get("hallucination_check_passed", False),
                "prompt_injection_detected": evaluation.get("prompt_injection_detected", False),
            }
        else:
            proposal["evaluation"] = None
        
        # Fetch compliance audits
        audit_response = supabase.table("chamber_compliance_audits").select(
            "id, audit_type, isr_v3_compliance, ai_security_policy_compliance, "
            "csp_standards_compliance, data_residency_verified, audit_timestamp, remediation_required"
        ).eq("proposal_id", str(proposal_id)).execute()
        
        proposal["compliance_audits"] = audit_response.data or []
        
        # Fetch comments
        comment_query = supabase.table("chamber_comments").select(
            "id, user_id, comment_text, created_at, visibility"
        ).eq("proposal_id", str(proposal_id))
        
        # Vendors can only see vendor_visible comments
        if user_role == "vendor":
            comment_query = comment_query.eq("visibility", "vendor_visible")
        
        comment_response = comment_query.execute()
        
        # Fetch user names for comments
        comments = []
        for comment in comment_response.data or []:
            user_response = supabase.table("chamber_users").select("full_name").eq(
                "id", comment.get("user_id")
            ).execute()
            comment["user_name"] = user_response.data[0].get("full_name") if user_response.data else "Unknown"
            comments.append(comment)
        
        proposal["comments"] = comments
        
        return proposal
    except Exception:
        return None


def update_proposal_status(
    user_id: UUID,
    proposal_id: UUID,
    status: str,
    reason: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update proposal status (analyst/executive only)."""
    try:
        update_data = {
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        response = supabase.table("chamber_proposals").update(update_data).eq(
            "id", str(proposal_id)
        ).execute()
        
        if response.data and len(response.data) > 0:
            proposal = response.data[0]
            
            # Log status change if reason provided
            if reason:
                supabase.table("chamber_comments").insert({
                    "proposal_id": str(proposal_id),
                    "user_id": str(user_id),
                    "comment_text": f"Status changed to {status}. Reason: {reason}",
                    "visibility": "internal",
                    "created_by": str(user_id),
                }).execute()
            
            return proposal
        return None
    except Exception:
        return None


def finalize_proposal_submission(
    user_id: UUID,
    proposal_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Finalize proposal submission and queue for evaluation."""
    try:
        # Verify ownership
        proposal_response = supabase.table("chamber_proposals").select("submitter_id").eq(
            "id", str(proposal_id)
        ).eq("submitter_id", str(user_id)).execute()
        
        if not proposal_response.data or len(proposal_response.data) == 0:
            return None
        
        # Check if documents exist
        docs_response = supabase.table("chamber_documents").select("id").eq(
            "proposal_id", str(proposal_id)
        ).execute()
        
        if not docs_response.data or len(docs_response.data) == 0:
            return {"error": "Cannot submit proposal without documents"}
        
        update_data = {
            "status": "queued_for_evaluation",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        response = supabase.table("chamber_proposals").update(update_data).eq(
            "id", str(proposal_id)
        ).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception:
        return None


def trigger_proposal_evaluation(
    user_id: UUID,
    proposal_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Trigger manual re-evaluation of proposal (analyst only)."""
    try:
        # Check current status
        proposal_response = supabase.table("chamber_proposals").select("status").eq(
            "id", str(proposal_id)
        ).execute()
        
        if not proposal_response.data or len(proposal_response.data) == 0:
            return None
        
        current_status = proposal_response.data[0].get("status")
        
        if current_status in ["evaluating", "queued_for_evaluation"]:
            return {"error": "Proposal is already being evaluated"}
        
        update_data = {
            "status": "queued_for_evaluation",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        response = supabase.table("chamber_proposals").update(update_data).eq(
            "id", str(proposal_id)
        ).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception:
        return None


def add_comment_to_proposal(
    user_id: UUID,
    proposal_id: UUID,
    comment_text: str,
    visibility: str = "internal",
) -> Optional[Dict[str, Any]]:
    """Add comment to proposal."""
    try:
        # Verify proposal exists
        proposal_response = supabase.table("chamber_proposals").select("id").eq(
            "id", str(proposal_id)
        ).execute()
        
        if not proposal_response.data or len(proposal_response.data) == 0:
            return None
        
        comment_data = {
            "proposal_id": str(proposal_id),
            "user_id": str(user_id),
            "comment_text": comment_text,
            "visibility": visibility,
            "created_by": str(user_id),
        }
        
        response = supabase.table("chamber_comments").insert(comment_data).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception:
        return None


def run_duplicate_check(
    user_id: UUID,
    proposal_id: UUID,
) -> Optional[Dict[str, Any]]:
    """Run semantic similarity check against existing proposals."""
    try:
        # Verify proposal exists
        proposal_response = supabase.table("chamber_proposals").select(
            "id, title, submission_date"
        ).eq("id", str(proposal_id)).execute()
        
        if not proposal_response.data or len(proposal_response.data) == 0:
            return None
        
        # Placeholder for semantic similarity logic
        # In production, this would use vector embeddings and similarity search
        similar_proposals = []
        
        # Update is_duplicate flag if needed
        is_duplicate = len(similar_proposals) > 0
        
        if is_duplicate:
            supabase.table("chamber_proposals").update({
                "is_duplicate": True,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", str(proposal_id)).execute()
        
        return {
            "proposal_id": str(proposal_id),
            "is_duplicate": is_duplicate,
            "similar_proposals": similar_proposals,
        }
    except Exception:
        return None


def batch_evaluate_proposals(
    user_id: UUID,
    proposal_ids: List[UUID],
) -> Optional[Dict[str, Any]]:
    """Trigger batch evaluation for multiple proposals."""
    try:
        # Update all proposals to queued_for_evaluation
        proposal_ids_str = [str(pid) for pid in proposal_ids]
        
        update_data = {
            "status": "queued_for_evaluation",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        
        response = supabase.table("chamber_proposals").update(update_data).in_(
            "id", proposal_ids_str
        ).execute()
        
        # Create batch job record (placeholder)
        batch_job_id = UUID(int=0)  # Generate proper UUID in production
        
        return {
            "batch_job_id": str(batch_job_id),
            "proposal_count": len(proposal_ids),
            "status": "queued",
        }
    except Exception:
        return None


def export_proposals(
    user_id: UUID,
    export_format: str = "csv",
    status: Optional[str] = None,
    sector: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Export proposals data as CSV/Excel."""
    try:
        query = supabase.table("chamber_proposals").select("*")
        
        if status:
            query = query.eq("status", status)
        if sector:
            query = query.eq("sector", sector)
        
        response = query.execute()
        
        # Placeholder for export generation
        # In production, generate actual CSV/Excel file and upload to storage
        export_url = "https://storage.example.com/exports/proposals.csv"
        expires_at = datetime.now(timezone.utc)
        
        return {
            "export_url": export_url,
            "expires_at": expires_at.isoformat(),
            "format": export_format,
        }
    except Exception:
        return None

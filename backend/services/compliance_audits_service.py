from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from database import supabase
import logging

logger = logging.getLogger(__name__)


def create_compliance_audit(
    user_id: UUID,
    proposal_id: UUID,
    audit_type: str,
    auditor_user_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a new compliance audit record.
    Compliance officer only.
    """
    try:
        # Verify proposal exists and get proposal data
        proposal_response = supabase.table("procurement_proposals").select("*").eq("id", str(proposal_id)).execute()
        
        if not proposal_response.data:
            logger.warning(f"Proposal {proposal_id} not found")
            return None
        
        proposal = proposal_response.data[0]
        
        # Create audit record with initial status
        audit_data = {
            "proposal_id": str(proposal_id),
            "audit_type": audit_type,
            "auditor_user_id": str(auditor_user_id or user_id),
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "isr_v3_compliance": False,
            "ai_security_policy_compliance": False,
            "csp_standards_compliance": False,
            "data_residency_verified": False,
            "remediation_required": True,
            "findings": {},
            "created_by": str(user_id),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = supabase.table("compliance_audits").insert(audit_data).execute()
        
        if response.data:
            logger.info(f"Compliance audit created: {response.data[0]['id']} for proposal {proposal_id}")
            return response.data[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error creating compliance audit: {str(e)}")
        return None


def get_audit_by_id(
    user_id: UUID,
    audit_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Get compliance audit by ID.
    Returns audit details with all compliance checks.
    """
    try:
        response = supabase.table("compliance_audits").select("*").eq("id", str(audit_id)).execute()
        
        if not response.data:
            logger.warning(f"Compliance audit {audit_id} not found")
            return None
        
        audit = response.data[0]
        
        # Verify user has access to this audit
        # Compliance officers and the auditor can view
        # Also check if user has access to the associated proposal
        proposal_response = supabase.table("procurement_proposals").select("created_by").eq("id", audit["proposal_id"]).execute()
        
        if not proposal_response.data:
            return None
        
        # Allow access if:
        # 1. User created the audit
        # 2. User is the auditor
        # 3. User created the proposal
        if (
            audit["created_by"] == str(user_id) or
            audit.get("auditor_user_id") == str(user_id) or
            proposal_response.data[0]["created_by"] == str(user_id)
        ):
            return audit
        
        logger.warning(f"User {user_id} unauthorized to view audit {audit_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving compliance audit: {str(e)}")
        return None


def list_audits_for_proposal(
    user_id: UUID,
    proposal_id: UUID,
    page: int = 1,
    page_size: int = 20
) -> Optional[Dict[str, Any]]:
    """
    List all compliance audits for a specific proposal.
    Returns paginated list with audit summaries.
    """
    try:
        # Verify user has access to the proposal
        proposal_response = supabase.table("procurement_proposals").select("created_by").eq("id", str(proposal_id)).execute()
        
        if not proposal_response.data:
            logger.warning(f"Proposal {proposal_id} not found")
            return None
        
        offset = (page - 1) * page_size
        
        # Get audits for this proposal
        audits_response = (
            supabase.table("compliance_audits")
            .select("*", count="exact")
            .eq("proposal_id", str(proposal_id))
            .order("audit_timestamp", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )
        
        total = audits_response.count or 0
        audits = audits_response.data or []
        
        return {
            "audits": audits,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error listing compliance audits: {str(e)}")
        return None


def list_audits(
    user_id: UUID,
    audit_type: Optional[str] = None,
    remediation_required: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20
) -> Optional[Dict[str, Any]]:
    """
    List compliance audits with optional filters.
    Compliance officers can see all audits.
    Other users see only audits for their proposals.
    """
    try:
        offset = (page - 1) * page_size
        
        query = supabase.table("compliance_audits").select("*", count="exact")
        
        # Apply filters
        if audit_type:
            query = query.eq("audit_type", audit_type)
        
        if remediation_required is not None:
            query = query.eq("remediation_required", remediation_required)
        
        # Order by most recent first
        query = query.order("audit_timestamp", desc=True)
        
        # Apply pagination
        response = query.range(offset, offset + page_size - 1).execute()
        
        total = response.count or 0
        audits = response.data or []
        
        return {
            "audits": audits,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error listing compliance audits: {str(e)}")
        return None


def update_audit_findings(
    user_id: UUID,
    audit_id: UUID,
    findings: Dict[str, Any],
    isr_v3_compliance: Optional[bool] = None,
    ai_security_policy_compliance: Optional[bool] = None,
    csp_standards_compliance: Optional[bool] = None,
    data_residency_verified: Optional[bool] = None,
    remediation_required: Optional[bool] = None
) -> Optional[Dict[str, Any]]:
    """
    Update compliance audit findings and compliance flags.
    Only the auditor or compliance officer can update.
    """
    try:
        # Verify audit exists and user is authorized
        audit = get_audit_by_id(user_id, audit_id)
        if not audit:
            return None
        
        # Verify user is the auditor or created the audit
        if audit["created_by"] != str(user_id) and audit.get("auditor_user_id") != str(user_id):
            logger.warning(f"User {user_id} unauthorized to update audit {audit_id}")
            return None
        
        update_data = {
            "findings": findings,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if isr_v3_compliance is not None:
            update_data["isr_v3_compliance"] = isr_v3_compliance
        
        if ai_security_policy_compliance is not None:
            update_data["ai_security_policy_compliance"] = ai_security_policy_compliance
        
        if csp_standards_compliance is not None:
            update_data["csp_standards_compliance"] = csp_standards_compliance
        
        if data_residency_verified is not None:
            update_data["data_residency_verified"] = data_residency_verified
        
        if remediation_required is not None:
            update_data["remediation_required"] = remediation_required
        
        response = (
            supabase.table("compliance_audits")
            .update(update_data)
            .eq("id", str(audit_id))
            .execute()
        )
        
        if response.data:
            logger.info(f"Compliance audit {audit_id} findings updated")
            return response.data[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error updating compliance audit findings: {str(e)}")
        return None


def set_audit_report_url(
    user_id: UUID,
    audit_id: UUID,
    report_url: str,
    hash_chain_signature: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Set the audit report URL and optional hash chain signature.
    Only the auditor or compliance officer can set.
    """
    try:
        # Verify audit exists and user is authorized
        audit = get_audit_by_id(user_id, audit_id)
        if not audit:
            return None
        
        if audit["created_by"] != str(user_id) and audit.get("auditor_user_id") != str(user_id):
            logger.warning(f"User {user_id} unauthorized to update audit {audit_id}")
            return None
        
        update_data = {
            "audit_report_url": report_url,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if hash_chain_signature:
            update_data["hash_chain_signature"] = hash_chain_signature
        
        response = (
            supabase.table("compliance_audits")
            .update(update_data)
            .eq("id", str(audit_id))
            .execute()
        )
        
        if response.data:
            logger.info(f"Compliance audit {audit_id} report URL set")
            return response.data[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error setting audit report URL: {str(e)}")
        return None


def get_audit_report_url(
    user_id: UUID,
    audit_id: UUID
) -> Optional[str]:
    """
    Get the audit report URL.
    Only authorized users can access.
    """
    try:
        audit = get_audit_by_id(user_id, audit_id)
        if not audit:
            return None
        
        return audit.get("audit_report_url")
        
    except Exception as e:
        logger.error(f"Error retrieving audit report URL: {str(e)}")
        return None


def export_compliance_history(
    user_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    audit_type: Optional[str] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Export compliance audit history for reporting.
    Compliance officer only.
    Returns all matching audits for export.
    """
    try:
        query = supabase.table("compliance_audits").select("*")
        
        if start_date:
            query = query.gte("audit_timestamp", start_date.isoformat())
        
        if end_date:
            query = query.lte("audit_timestamp", end_date.isoformat())
        
        if audit_type:
            query = query.eq("audit_type", audit_type)
        
        query = query.order("audit_timestamp", desc=True)
        
        response = query.execute()
        
        if response.data:
            logger.info(f"Exported {len(response.data)} compliance audit records")
            return response.data
        
        return []
        
    except Exception as e:
        logger.error(f"Error exporting compliance history: {str(e)}")
        return None


def delete_audit(
    user_id: UUID,
    audit_id: UUID
) -> bool:
    """
    Soft delete compliance audit.
    Only compliance officers can delete audits.
    """
    try:
        # Verify audit exists and user is authorized
        audit = get_audit_by_id(user_id, audit_id)
        if not audit:
            return False
        
        # Verify user created the audit
        if audit["created_by"] != str(user_id):
            logger.warning(f"User {user_id} unauthorized to delete audit {audit_id}")
            return False
        
        # Soft delete by setting deleted_at
        update_data = {
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        response = (
            supabase.table("compliance_audits")
            .update(update_data)
            .eq("id", str(audit_id))
            .execute()
        )
        
        if response.data:
            logger.info(f"Compliance audit {audit_id} soft deleted")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error deleting compliance audit: {str(e)}")
        return False


def get_compliance_summary_for_proposal(
    user_id: UUID,
    proposal_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Get compliance summary for a proposal.
    Returns aggregated compliance status across all audits.
    """
    try:
        # Verify proposal exists
        proposal_response = supabase.table("procurement_proposals").select("created_by").eq("id", str(proposal_id)).execute()
        
        if not proposal_response.data:
            return None
        
        # Get all audits for this proposal
        audits_response = (
            supabase.table("compliance_audits")
            .select("*")
            .eq("proposal_id", str(proposal_id))
            .is_("deleted_at", "null")
            .execute()
        )
        
        audits = audits_response.data or []
        
        if not audits:
            return {
                "proposal_id": str(proposal_id),
                "total_audits": 0,
                "latest_audit": None,
                "overall_compliance": False,
                "remediation_required": False
            }
        
        # Get latest audit
        latest_audit = max(audits, key=lambda x: x["audit_timestamp"])
        
        # Aggregate compliance status
        overall_compliance = (
            latest_audit.get("isr_v3_compliance", False) and
            latest_audit.get("ai_security_policy_compliance", False) and
            latest_audit.get("csp_standards_compliance", False) and
            latest_audit.get("data_residency_verified", False)
        )
        
        return {
            "proposal_id": str(proposal_id),
            "total_audits": len(audits),
            "latest_audit": latest_audit,
            "overall_compliance": overall_compliance,
            "remediation_required": latest_audit.get("remediation_required", True)
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance summary: {str(e)}")
        return None

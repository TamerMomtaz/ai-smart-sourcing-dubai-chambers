from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from database import supabase
import json


def create(
    user_id: UUID,
    proposal_id: UUID,
    audit_type: str,
    isr_v3_compliance: Optional[bool] = None,
    ai_security_policy_compliance: Optional[bool] = None,
    csp_standards_compliance: Optional[bool] = None,
    data_residency_verified: Optional[bool] = None,
    auditor_user_id: Optional[UUID] = None,
    findings_json: Optional[Dict[str, Any]] = None,
    remediation_required: bool = False,
    audit_report_path: Optional[str] = None,
    hash_chain_signature: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Create a new compliance audit record."""
    audit_data = {
        "proposal_id": str(proposal_id),
        "audit_type": audit_type,
        "isr_v3_compliance": isr_v3_compliance,
        "ai_security_policy_compliance": ai_security_policy_compliance,
        "csp_standards_compliance": csp_standards_compliance,
        "data_residency_verified": data_residency_verified,
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "auditor_user_id": str(auditor_user_id) if auditor_user_id else None,
        "findings_json": json.dumps(findings_json) if findings_json else None,
        "remediation_required": remediation_required,
        "audit_report_path": audit_report_path,
        "hash_chain_signature": hash_chain_signature,
    }

    response = supabase.table("chamber_compliance_audits").insert(audit_data).execute()

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def list(
    user_id: UUID,
    proposal_id: Optional[UUID] = None,
    audit_type: Optional[str] = None,
    remediation_required: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[Dict[str, Any]], int]:
    """List compliance audits with pagination and filters."""
    offset = (page - 1) * page_size

    query = supabase.table("chamber_compliance_audits").select("*", count="exact")

    if proposal_id:
        query = query.eq("proposal_id", str(proposal_id))

    if audit_type:
        query = query.eq("audit_type", audit_type)

    if remediation_required is not None:
        query = query.eq("remediation_required", remediation_required)

    query = query.order("audit_timestamp", desc=True)
    query = query.range(offset, offset + page_size - 1)

    response = query.execute()

    audits = response.data if response.data else []
    total = response.count if hasattr(response, "count") and response.count else 0

    for audit in audits:
        if audit.get("findings_json") and isinstance(audit["findings_json"], str):
            try:
                audit["findings_json"] = json.loads(audit["findings_json"])
            except json.JSONDecodeError:
                audit["findings_json"] = None

    return audits, total


def get_by_id(user_id: UUID, audit_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a single compliance audit by ID."""
    response = (
        supabase.table("chamber_compliance_audits")
        .select("*")
        .eq("id", str(audit_id))
        .execute()
    )

    if response.data and len(response.data) > 0:
        audit = response.data[0]
        if audit.get("findings_json") and isinstance(audit["findings_json"], str):
            try:
                audit["findings_json"] = json.loads(audit["findings_json"])
            except json.JSONDecodeError:
                audit["findings_json"] = None
        return audit

    return None


def get_by_proposal(user_id: UUID, proposal_id: UUID) -> List[Dict[str, Any]]:
    """Get all compliance audits for a specific proposal."""
    response = (
        supabase.table("chamber_compliance_audits")
        .select("*")
        .eq("proposal_id", str(proposal_id))
        .order("audit_timestamp", desc=True)
        .execute()
    )

    audits = response.data if response.data else []

    for audit in audits:
        if audit.get("findings_json") and isinstance(audit["findings_json"], str):
            try:
                audit["findings_json"] = json.loads(audit["findings_json"])
            except json.JSONDecodeError:
                audit["findings_json"] = None

    return audits


def update(
    user_id: UUID,
    audit_id: UUID,
    isr_v3_compliance: Optional[bool] = None,
    ai_security_policy_compliance: Optional[bool] = None,
    csp_standards_compliance: Optional[bool] = None,
    data_residency_verified: Optional[bool] = None,
    findings_json: Optional[Dict[str, Any]] = None,
    remediation_required: Optional[bool] = None,
    audit_report_path: Optional[str] = None,
    hash_chain_signature: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update an existing compliance audit."""
    existing = get_by_id(user_id, audit_id)
    if not existing:
        return None

    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if isr_v3_compliance is not None:
        update_data["isr_v3_compliance"] = isr_v3_compliance

    if ai_security_policy_compliance is not None:
        update_data["ai_security_policy_compliance"] = ai_security_policy_compliance

    if csp_standards_compliance is not None:
        update_data["csp_standards_compliance"] = csp_standards_compliance

    if data_residency_verified is not None:
        update_data["data_residency_verified"] = data_residency_verified

    if findings_json is not None:
        update_data["findings_json"] = json.dumps(findings_json)

    if remediation_required is not None:
        update_data["remediation_required"] = remediation_required

    if audit_report_path is not None:
        update_data["audit_report_path"] = audit_report_path

    if hash_chain_signature is not None:
        update_data["hash_chain_signature"] = hash_chain_signature

    response = (
        supabase.table("chamber_compliance_audits")
        .update(update_data)
        .eq("id", str(audit_id))
        .execute()
    )

    if response.data and len(response.data) > 0:
        audit = response.data[0]
        if audit.get("findings_json") and isinstance(audit["findings_json"], str):
            try:
                audit["findings_json"] = json.loads(audit["findings_json"])
            except json.JSONDecodeError:
                audit["findings_json"] = None
        return audit

    return None


def delete(user_id: UUID, audit_id: UUID) -> bool:
    """Soft delete a compliance audit (mark as deleted)."""
    existing = get_by_id(user_id, audit_id)
    if not existing:
        return False

    response = (
        supabase.table("chamber_compliance_audits")
        .delete()
        .eq("id", str(audit_id))
        .execute()
    )

    return response.data is not None and len(response.data) > 0


def get_latest_by_proposal(user_id: UUID, proposal_id: UUID) -> Optional[Dict[str, Any]]:
    """Get the most recent audit for a proposal."""
    response = (
        supabase.table("chamber_compliance_audits")
        .select("*")
        .eq("proposal_id", str(proposal_id))
        .order("audit_timestamp", desc=True)
        .limit(1)
        .execute()
    )

    if response.data and len(response.data) > 0:
        audit = response.data[0]
        if audit.get("findings_json") and isinstance(audit["findings_json"], str):
            try:
                audit["findings_json"] = json.loads(audit["findings_json"])
            except json.JSONDecodeError:
                audit["findings_json"] = None
        return audit

    return None


def get_remediation_required(user_id: UUID, page: int = 1, page_size: int = 20) -> tuple[List[Dict[str, Any]], int]:
    """Get all audits requiring remediation."""
    offset = (page - 1) * page_size

    response = (
        supabase.table("chamber_compliance_audits")
        .select("*", count="exact")
        .eq("remediation_required", True)
        .order("audit_timestamp", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    audits = response.data if response.data else []
    total = response.count if hasattr(response, "count") and response.count else 0

    for audit in audits:
        if audit.get("findings_json") and isinstance(audit["findings_json"], str):
            try:
                audit["findings_json"] = json.loads(audit["findings_json"])
            except json.JSONDecodeError:
                audit["findings_json"] = None

    return audits, total

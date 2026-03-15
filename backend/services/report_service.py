from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID
from database import supabase
import os


def generate_compliance_report(
    user_id: str,
    audit_id: UUID,
) -> Optional[dict]:
    """
    Generate DESC-format compliance audit report PDF.
    
    Args:
        user_id: User UUID performing the action
        audit_id: Compliance audit UUID
        
    Returns:
        Dict with report_url and expires_at, or None if audit not found
    """
    # Verify user is compliance officer
    user_response = supabase.table("chamber_users").select("role").eq("id", user_id).execute()
    
    if not user_response.data or len(user_response.data) == 0:
        return None
        
    user_role = user_response.data[0].get("role")
    if user_role != "compliance_officer":
        raise PermissionError("Only compliance officers can download reports")
    
    # Get audit details
    audit_response = (
        supabase.table("compliance_audits")
        .select("*")
        .eq("id", str(audit_id))
        .execute()
    )
    
    if not audit_response.data or len(audit_response.data) == 0:
        return None
        
    audit = audit_response.data[0]
    
    # Get proposal details for the audit
    proposal_id = audit.get("proposal_id")
    proposal_response = (
        supabase.table("chamber_proposals")
        .select("*")
        .eq("id", str(proposal_id))
        .execute()
    )
    
    if not proposal_response.data or len(proposal_response.data) == 0:
        return None
        
    proposal = proposal_response.data[0]
    
    # Get vendor details
    vendor_id = proposal.get("submitter_id")
    vendor_response = (
        supabase.table("chamber_vendors")
        .select("name, company_registration, country")
        .eq("id", str(vendor_id))
        .execute()
    )
    
    vendor = vendor_response.data[0] if vendor_response.data else {}
    
    # Generate report file name
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_filename = f"compliance_report_{audit_id}_{timestamp}.pdf"
    report_path = f"compliance-reports/{report_filename}"
    
    # Generate PDF content (DESC format)
    from services.pdf_generator_service import generate_desc_compliance_pdf
    
    pdf_content = generate_desc_compliance_pdf(
        audit=audit,
        proposal=proposal,
        vendor=vendor,
    )
    
    # Upload to Supabase Storage
    bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "chamber-documents").strip()
    
    upload_response = supabase.storage.from_(bucket_name).upload(
        path=report_path,
        file=pdf_content,
        file_options={"content-type": "application/pdf"},
    )
    
    if upload_response.status_code not in [200, 201]:
        raise Exception(f"Failed to upload report: {upload_response.json()}")
    
    # Generate signed URL (expires in 1 hour)
    expiry_seconds = 3600
    signed_url_response = supabase.storage.from_(bucket_name).create_signed_url(
        path=report_path,
        expires_in=expiry_seconds,
    )
    
    if not signed_url_response or "signedURL" not in signed_url_response:
        raise Exception("Failed to generate signed URL for report")
    
    signed_url = signed_url_response["signedURL"]
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds)
    
    # Update audit record with report URL
    supabase.table("compliance_audits").update({
        "audit_report_url": report_path,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", str(audit_id)).execute()
    
    # Log report generation activity
    supabase.table("activity_logs").insert({
        "user_id": user_id,
        "action": "compliance_report_generated",
        "entity_type": "compliance_audit",
        "entity_id": str(audit_id),
        "details": {
            "report_path": report_path,
            "audit_type": audit.get("audit_type"),
            "proposal_id": str(proposal_id),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    
    return {
        "report_url": signed_url,
        "expires_at": expires_at,
    }


def get_compliance_report(
    user_id: str,
    audit_id: UUID,
) -> Optional[dict]:
    """
    Retrieve existing compliance report URL.
    
    Args:
        user_id: User UUID requesting the report
        audit_id: Compliance audit UUID
        
    Returns:
        Dict with report_url and expires_at, or None if not found
    """
    # Verify user is compliance officer
    user_response = supabase.table("chamber_users").select("role").eq("id", user_id).execute()
    
    if not user_response.data or len(user_response.data) == 0:
        return None
        
    user_role = user_response.data[0].get("role")
    if user_role != "compliance_officer":
        raise PermissionError("Only compliance officers can access reports")
    
    # Get audit with report URL
    audit_response = (
        supabase.table("compliance_audits")
        .select("audit_report_url")
        .eq("id", str(audit_id))
        .execute()
    )
    
    if not audit_response.data or len(audit_response.data) == 0:
        return None
        
    audit = audit_response.data[0]
    report_path = audit.get("audit_report_url")
    
    if not report_path:
        return None
    
    # Generate fresh signed URL
    bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "chamber-documents").strip()
    expiry_seconds = 3600
    
    signed_url_response = supabase.storage.from_(bucket_name).create_signed_url(
        path=report_path,
        expires_in=expiry_seconds,
    )
    
    if not signed_url_response or "signedURL" not in signed_url_response:
        raise Exception("Failed to generate signed URL for report")
    
    signed_url = signed_url_response["signedURL"]
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expiry_seconds)
    
    return {
        "report_url": signed_url,
        "expires_at": expires_at,
    }

from typing import Optional
from uuid import UUID
from datetime import datetime, timezone, timedelta
from database import supabase


def generate_download_url(
    user_id: str,
    document_id: str,
    user_role: str
) -> Optional[dict]:
    """
    Generate temporary download URL for a document.
    Verifies ownership or access permissions before generating URL.
    
    Args:
        user_id: UUID of requesting user
        document_id: UUID of document to download
        user_role: Role of requesting user
    
    Returns:
        dict with download_url and expires_at, or None if not found/unauthorized
    """
    # Fetch document metadata
    doc_response = supabase.table("chamber_documents").select(
        "id, proposal_id, file_name, storage_path"
    ).eq("id", document_id).execute()
    
    if not doc_response.data or len(doc_response.data) == 0:
        return None
    
    document = doc_response.data[0]
    
    # Verify access permissions
    # Check if user owns the proposal (vendor) or has analyst/executive/compliance role
    proposal_response = supabase.table("chamber_proposals").select(
        "id, submitter_id"
    ).eq("id", document["proposal_id"]).execute()
    
    if not proposal_response.data or len(proposal_response.data) == 0:
        return None
    
    proposal = proposal_response.data[0]
    
    # Authorization check
    is_owner = str(proposal["submitter_id"]) == str(user_id)
    is_staff = user_role in ["admin", "analyst", "executive", "compliance_officer", "business_group_lead"]
    
    if not (is_owner or is_staff):
        return None
    
    # Generate signed URL (expires in 1 hour)
    storage_path = document.get("storage_path")
    if not storage_path:
        return None
    
    try:
        # Generate signed URL using Supabase Storage
        signed_url_response = supabase.storage.from_("proposal-documents").create_signed_url(
            storage_path,
            3600  # 1 hour expiry
        )
        
        download_url = None
        if signed_url_response:
            download_url = signed_url_response.get("signedURL") or signed_url_response.get("signedUrl")
        if not download_url:
            return None
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        return {
            "download_url": download_url,
            "expires_at": expires_at
        }
    except Exception:
        return None

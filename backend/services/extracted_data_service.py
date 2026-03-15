from typing import Optional, Dict, Any
from uuid import UUID
from database import supabase
from models.document import ExtractedDocumentData


def get_extracted_data_by_document_id(
    user_id: UUID, document_id: UUID
) -> Optional[ExtractedDocumentData]:
    """
    Get AI-extracted data for a specific document.
    Verifies ownership through the proposal -> documents relationship.
    
    Args:
        user_id: UUID of requesting user
        document_id: UUID of document
        
    Returns:
        ExtractedDocumentData if found and user has access, None otherwise
    """
    # First, verify the user has access to this document through proposals
    # Get document with its proposal relationship
    doc_response = (
        supabase.table("chamber_documents")
        .select("id, file_name, proposal_id, extracted_text, extracted_tables, extracted_charts, financial_data, language_detected")
        .eq("id", str(document_id))
        .eq("deleted_at", None)
        .maybe_single()
        .execute()
    )
    
    if not doc_response.data:
        return None
    
    document = doc_response.data
    proposal_id = document.get("proposal_id")
    
    if not proposal_id:
        return None
    
    # Verify user owns the proposal (vendor) or has analyst/executive access
    proposal_response = (
        supabase.table("chamber_proposals")
        .select("id, submitter_id")
        .eq("id", str(proposal_id))
        .eq("deleted_at", None)
        .maybe_single()
        .execute()
    )
    
    if not proposal_response.data:
        return None
    
    proposal = proposal_response.data
    submitter_id = proposal.get("submitter_id")
    
    # Check if user is the vendor who submitted the proposal
    if str(submitter_id) != str(user_id):
        # Check if user has analyst/executive role (they can view all)
        user_response = (
            supabase.table("chamber_users")
            .select("role")
            .eq("id", str(user_id))
            .maybe_single()
            .execute()
        )
        
        if not user_response.data:
            return None
        
        user_role = user_response.data.get("role")
        if user_role not in ["analyst", "executive", "compliance_officer", "business_group_lead"]:
            return None
    
    # Check if extraction is complete
    extraction_status = document.get("extraction_status")
    if extraction_status and extraction_status != "completed":
        # Extraction not complete - caller should return 425
        return None
    
    # Build response
    extracted_data = ExtractedDocumentData(
        document_id=UUID(document["id"]),
        file_name=document["file_name"],
        extracted_text=document.get("extracted_text"),
        extracted_tables=document.get("extracted_tables"),
        extracted_charts=document.get("extracted_charts"),
        financial_data=document.get("financial_data"),
        language_detected=document.get("language_detected")
    )
    
    return extracted_data


def check_extraction_status(user_id: UUID, document_id: UUID) -> Optional[str]:
    """
    Check the extraction status of a document.
    Returns status string or None if document not found/no access.
    
    Possible statuses: 'pending', 'processing', 'completed', 'failed'
    """
    # Verify access first
    doc_response = (
        supabase.table("chamber_documents")
        .select("id, proposal_id, extraction_status")
        .eq("id", str(document_id))
        .eq("deleted_at", None)
        .maybe_single()
        .execute()
    )
    
    if not doc_response.data:
        return None
    
    document = doc_response.data
    proposal_id = document.get("proposal_id")
    
    if not proposal_id:
        return None
    
    # Verify ownership
    proposal_response = (
        supabase.table("chamber_proposals")
        .select("id, submitter_id")
        .eq("id", str(proposal_id))
        .eq("deleted_at", None)
        .maybe_single()
        .execute()
    )
    
    if not proposal_response.data:
        return None
    
    proposal = proposal_response.data
    submitter_id = proposal.get("submitter_id")
    
    if str(submitter_id) != str(user_id):
        user_response = (
            supabase.table("chamber_users")
            .select("role")
            .eq("id", str(user_id))
            .maybe_single()
            .execute()
        )
        
        if not user_response.data:
            return None
        
        user_role = user_response.data.get("role")
        if user_role not in ["analyst", "executive", "compliance_officer", "business_group_lead"]:
            return None
    
    return document.get("extraction_status", "pending")

from typing import Optional
from uuid import UUID
from database import supabase
import logging

logger = logging.getLogger(__name__)


async def verify_vendor_certification(
    user_id: str,
    vendor_id: UUID
) -> Optional[dict]:
    """
    Verify if a vendor has DESC certification.
    
    Args:
        user_id: ID of requesting user
        vendor_id: UUID of vendor to verify
    
    Returns:
        dict with verification result or None if vendor not found
    """
    try:
        # First, verify the vendor exists
        vendor_response = supabase.table("chamber_vendors").select(
            "id, name, is_desc_approved, desc_badge_issued_date, company_registration"
        ).eq("id", str(vendor_id)).execute()
        
        if not vendor_response.data or len(vendor_response.data) == 0:
            return None
        
        vendor = vendor_response.data[0]
        
        # If DESC approved, fetch certification details from certified providers
        certification_details = None
        if vendor.get("is_desc_approved"):
            cert_response = supabase.table("desc_certified_providers").select(
                "certification_number, valid_until, compliance_frameworks"
            ).eq("vendor_id", str(vendor_id)).execute()
            
            if cert_response.data and len(cert_response.data) > 0:
                cert_data = cert_response.data[0]
                certification_details = {
                    "certification_number": cert_data.get("certification_number"),
                    "valid_until": cert_data.get("valid_until"),
                    "compliance_frameworks": cert_data.get("compliance_frameworks", [])
                }
        
        return {
            "vendor_id": vendor_id,
            "is_certified": vendor.get("is_desc_approved", False),
            "certification_details": certification_details
        }
    
    except Exception as e:
        logger.error(f"Error verifying vendor certification: {e}")
        raise

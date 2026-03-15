from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


def list_certified_providers(
    user_id: str,
    page: int = 1,
    page_size: int = 50
) -> Optional[Dict[str, Any]]:
    """
    Query DESC certified providers registry.
    Returns list of certified providers with pagination.
    """
    offset = (page - 1) * page_size
    
    # Query certified providers from desc_certified_providers table
    response = supabase.table("desc_certified_providers") \
        .select("*", count="exact") \
        .eq("is_active", True) \
        .order("provider_name") \
        .range(offset, offset + page_size - 1) \
        .execute()
    
    if not response.data:
        return {
            "providers": [],
            "total": 0,
            "page": page,
            "page_size": page_size
        }
    
    return {
        "providers": response.data,
        "total": response.count or 0,
        "page": page,
        "page_size": page_size
    }


def verify_vendor_certification(
    user_id: str,
    vendor_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Verify if a vendor is DESC certified by checking against certified providers registry.
    Returns certification status and details if certified.
    """
    # First get vendor details
    vendor_response = supabase.table("chamber_vendors") \
        .select("id, name, company_registration, is_desc_approved, desc_badge_issued_date") \
        .eq("id", str(vendor_id)) \
        .single() \
        .execute()
    
    if not vendor_response.data:
        return None
    
    vendor = vendor_response.data
    
    # Check if vendor is in DESC certified providers registry
    # Match by company_registration or name
    cert_response = supabase.table("desc_certified_providers") \
        .select("*") \
        .eq("is_active", True) \
        .or_(f"certification_number.eq.{vendor.get('company_registration')},provider_name.ilike.%{vendor.get('name')}%") \
        .maybeSingle() \
        .execute()
    
    is_certified = cert_response.data is not None
    certification_details = None
    
    if is_certified:
        cert_data = cert_response.data
        certification_details = {
            "certification_number": cert_data.get("certification_number"),
            "valid_until": cert_data.get("valid_until"),
            "compliance_frameworks": cert_data.get("compliance_frameworks") or []
        }
        
        # Update vendor DESC approval status if not already set
        if not vendor.get("is_desc_approved"):
            supabase.table("chamber_vendors") \
                .update({
                    "is_desc_approved": True,
                    "desc_badge_issued_date": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }) \
                .eq("id", str(vendor_id)) \
                .execute()
    
    return {
        "vendor_id": str(vendor_id),
        "is_certified": is_certified,
        "certification_details": certification_details
    }


def get_certified_provider_by_id(
    user_id: str,
    provider_id: UUID
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a specific DESC certified provider.
    """
    response = supabase.table("desc_certified_providers") \
        .select("*") \
        .eq("id", str(provider_id)) \
        .eq("is_active", True) \
        .single() \
        .execute()
    
    return response.data if response.data else None


def search_certified_providers(
    user_id: str,
    search_term: Optional[str] = None,
    compliance_framework: Optional[str] = None,
    service_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
) -> Optional[Dict[str, Any]]:
    """
    Search DESC certified providers with filters.
    """
    offset = (page - 1) * page_size
    
    query = supabase.table("desc_certified_providers") \
        .select("*", count="exact") \
        .eq("is_active", True)
    
    if search_term:
        query = query.ilike("provider_name", f"%{search_term}%")
    
    if compliance_framework:
        query = query.contains("compliance_frameworks", [compliance_framework])
    
    if service_type:
        query = query.contains("services_offered", [service_type])
    
    response = query \
        .order("provider_name") \
        .range(offset, offset + page_size - 1) \
        .execute()
    
    if not response.data:
        return {
            "providers": [],
            "total": 0,
            "page": page,
            "page_size": page_size
        }
    
    return {
        "providers": response.data,
        "total": response.count or 0,
        "page": page,
        "page_size": page_size
    }


def check_certification_expiry(
    user_id: str,
    days_threshold: int = 30
) -> Optional[List[Dict[str, Any]]]:
    """
    Get list of certified providers whose certification is expiring soon.
    Used for compliance monitoring.
    """
    from datetime import timedelta
    
    expiry_date = (datetime.now(timezone.utc) + timedelta(days=days_threshold)).date()
    
    response = supabase.table("desc_certified_providers") \
        .select("*") \
        .eq("is_active", True) \
        .lte("valid_until", expiry_date.isoformat()) \
        .gte("valid_until", datetime.now(timezone.utc).date().isoformat()) \
        .order("valid_until") \
        .execute()
    
    return response.data if response.data else []


def bulk_verify_vendors(
    user_id: str,
    vendor_ids: List[UUID]
) -> Optional[List[Dict[str, Any]]]:
    """
    Verify multiple vendors against DESC certified providers registry.
    Returns list of verification results.
    """
    results = []
    
    for vendor_id in vendor_ids:
        verification = verify_vendor_certification(user_id, vendor_id)
        if verification:
            results.append(verification)
    
    return results


def get_compliance_statistics(
    user_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get statistics about DESC certified providers.
    Used for compliance reporting and dashboard.
    """
    # Total certified providers
    total_response = supabase.table("desc_certified_providers") \
        .select("id", count="exact") \
        .eq("is_active", True) \
        .execute()
    
    total_certified = total_response.count or 0
    
    # Expiring soon (within 30 days)
    expiring_soon = check_certification_expiry(user_id, 30)
    expiring_count = len(expiring_soon) if expiring_soon else 0
    
    # Frameworks distribution
    all_providers = supabase.table("desc_certified_providers") \
        .select("compliance_frameworks") \
        .eq("is_active", True) \
        .execute()
    
    frameworks_count: Dict[str, int] = {}
    if all_providers.data:
        for provider in all_providers.data:
            frameworks = provider.get("compliance_frameworks") or []
            for framework in frameworks:
                frameworks_count[framework] = frameworks_count.get(framework, 0) + 1
    
    # Services distribution
    services_count: Dict[str, int] = {}
    services_response = supabase.table("desc_certified_providers") \
        .select("services_offered") \
        .eq("is_active", True) \
        .execute()
    
    if services_response.data:
        for provider in services_response.data:
            services = provider.get("services_offered") or []
            for service in services:
                services_count[service] = services_count.get(service, 0) + 1
    
    return {
        "total_certified_providers": total_certified,
        "expiring_within_30_days": expiring_count,
        "compliance_frameworks_distribution": frameworks_count,
        "services_distribution": services_count,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }

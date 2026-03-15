from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


async def create_vendor(
    name: str,
    company_registration: str,
    country: str,
    contact_email: str,
    contact_phone: Optional[str] = None,
    website: Optional[str] = None,
    is_desc_approved: bool = False,
    desc_badge_issued_date: Optional[datetime] = None,
    onboarding_status: str = "submitted",
) -> Optional[Dict[str, Any]]:
    """Create a new chamber vendor."""
    data = {
        "name": name,
        "company_registration": company_registration,
        "country": country,
        "contact_email": contact_email,
        "contact_phone": contact_phone,
        "website": website,
        "is_desc_approved": is_desc_approved,
        "desc_badge_issued_date": desc_badge_issued_date.isoformat() if desc_badge_issued_date else None,
        "onboarding_status": onboarding_status,
        "submission_history_count": 0,
        "api_access_enabled": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    response = supabase.table("chamber_vendors").insert(data).execute()
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def list_vendors(
    page: int = 1,
    page_size: int = 20,
    onboarding_status: Optional[str] = None,
    is_desc_approved: Optional[bool] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
) -> tuple[List[Dict[str, Any]], int]:
    """List chamber vendors with pagination and filters."""
    offset = (page - 1) * page_size

    query = supabase.table("chamber_vendors").select("*", count="exact")

    if onboarding_status:
        query = query.eq("onboarding_status", onboarding_status)
    if is_desc_approved is not None:
        query = query.eq("is_desc_approved", is_desc_approved)
    if country:
        query = query.eq("country", country)
    if search:
        query = query.or_(f"name.ilike.%{search}%,contact_email.ilike.%{search}%,company_registration.ilike.%{search}%")

    query = query.order("created_at", desc=True)
    query = query.range(offset, offset + page_size - 1)

    response = query.execute()
    total = response.count if response.count else 0
    return response.data, total


async def get_vendor_by_id(vendor_id: UUID) -> Optional[Dict[str, Any]]:
    """Get chamber vendor by ID."""
    response = (
        supabase.table("chamber_vendors")
        .select("*")
        .eq("id", str(vendor_id))
        .execute()
    )
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def get_vendor_by_email(contact_email: str) -> Optional[Dict[str, Any]]:
    """Get chamber vendor by email."""
    response = (
        supabase.table("chamber_vendors")
        .select("*")
        .eq("contact_email", contact_email)
        .execute()
    )
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def get_vendor_by_registration(company_registration: str) -> Optional[Dict[str, Any]]:
    """Get chamber vendor by company registration number."""
    response = (
        supabase.table("chamber_vendors")
        .select("*")
        .eq("company_registration", company_registration)
        .execute()
    )
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def update_vendor(
    vendor_id: UUID,
    name: Optional[str] = None,
    company_registration: Optional[str] = None,
    country: Optional[str] = None,
    contact_email: Optional[str] = None,
    contact_phone: Optional[str] = None,
    website: Optional[str] = None,
    is_desc_approved: Optional[bool] = None,
    desc_badge_issued_date: Optional[datetime] = None,
    onboarding_status: Optional[str] = None,
    submission_history_count: Optional[int] = None,
    average_compliance_score: Optional[float] = None,
    api_access_enabled: Optional[bool] = None,
    api_key_hash: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Update chamber vendor."""
    data = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if name is not None:
        data["name"] = name
    if company_registration is not None:
        data["company_registration"] = company_registration
    if country is not None:
        data["country"] = country
    if contact_email is not None:
        data["contact_email"] = contact_email
    if contact_phone is not None:
        data["contact_phone"] = contact_phone
    if website is not None:
        data["website"] = website
    if is_desc_approved is not None:
        data["is_desc_approved"] = is_desc_approved
    if desc_badge_issued_date is not None:
        data["desc_badge_issued_date"] = desc_badge_issued_date.isoformat()
    if onboarding_status is not None:
        data["onboarding_status"] = onboarding_status
    if submission_history_count is not None:
        data["submission_history_count"] = submission_history_count
    if average_compliance_score is not None:
        data["average_compliance_score"] = average_compliance_score
    if api_access_enabled is not None:
        data["api_access_enabled"] = api_access_enabled
    if api_key_hash is not None:
        data["api_key_hash"] = api_key_hash

    response = (
        supabase.table("chamber_vendors")
        .update(data)
        .eq("id", str(vendor_id))
        .execute()
    )
    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


async def delete_vendor(vendor_id: UUID) -> bool:
    """Soft delete chamber vendor by setting is_active=false (if column exists) or hard delete."""
    response = (
        supabase.table("chamber_vendors")
        .delete()
        .eq("id", str(vendor_id))
        .execute()
    )
    return response.data is not None and len(response.data) > 0


async def increment_submission_count(vendor_id: UUID) -> Optional[Dict[str, Any]]:
    """Increment submission history count for a vendor."""
    vendor = await get_vendor_by_id(vendor_id)
    if not vendor:
        return None

    current_count = vendor.get("submission_history_count", 0)
    return await update_vendor(
        vendor_id=vendor_id,
        submission_history_count=current_count + 1,
    )


async def update_compliance_score(
    vendor_id: UUID,
    new_score: float,
) -> Optional[Dict[str, Any]]:
    """Update average compliance score for a vendor."""
    vendor = await get_vendor_by_id(vendor_id)
    if not vendor:
        return None

    current_avg = vendor.get("average_compliance_score")
    submission_count = vendor.get("submission_history_count", 0)

    if current_avg is None:
        new_avg = new_score
    else:
        new_avg = ((current_avg * submission_count) + new_score) / (submission_count + 1)

    return await update_vendor(
        vendor_id=vendor_id,
        average_compliance_score=round(new_avg, 2),
    )


async def grant_desc_badge(vendor_id: UUID) -> Optional[Dict[str, Any]]:
    """Grant DESC badge to a vendor."""
    return await update_vendor(
        vendor_id=vendor_id,
        is_desc_approved=True,
        desc_badge_issued_date=datetime.now(timezone.utc),
    )


async def revoke_desc_badge(vendor_id: UUID) -> Optional[Dict[str, Any]]:
    """Revoke DESC badge from a vendor."""
    return await update_vendor(
        vendor_id=vendor_id,
        is_desc_approved=False,
        desc_badge_issued_date=None,
    )


async def enable_api_access(
    vendor_id: UUID,
    api_key_hash: str,
) -> Optional[Dict[str, Any]]:
    """Enable API access for a vendor."""
    return await update_vendor(
        vendor_id=vendor_id,
        api_access_enabled=True,
        api_key_hash=api_key_hash,
    )


async def disable_api_access(vendor_id: UUID) -> Optional[Dict[str, Any]]:
    """Disable API access for a vendor."""
    return await update_vendor(
        vendor_id=vendor_id,
        api_access_enabled=False,
        api_key_hash=None,
    )


async def get_vendors_by_status(onboarding_status: str) -> List[Dict[str, Any]]:
    """Get all vendors with a specific onboarding status."""
    response = (
        supabase.table("chamber_vendors")
        .select("*")
        .eq("onboarding_status", onboarding_status)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data


async def get_desc_approved_vendors() -> List[Dict[str, Any]]:
    """Get all DESC approved vendors."""
    response = (
        supabase.table("chamber_vendors")
        .select("*")
        .eq("is_desc_approved", True)
        .order("desc_badge_issued_date", desc=True)
        .execute()
    )
    return response.data


async def get_vendors_by_country(country: str) -> List[Dict[str, Any]]:
    """Get all vendors from a specific country."""
    response = (
        supabase.table("chamber_vendors")
        .select("*")
        .eq("country", country)
        .order("name")
        .execute()
    )
    return response.data


async def get_vendor_statistics() -> Dict[str, Any]:
    """Get overall vendor statistics."""
    all_vendors = supabase.table("chamber_vendors").select("*").execute()
    vendors = all_vendors.data

    total_vendors = len(vendors)
    desc_approved = len([v for v in vendors if v.get("is_desc_approved")])
    api_enabled = len([v for v in vendors if v.get("api_access_enabled")])

    status_distribution = {}
    for vendor in vendors:
        status = vendor.get("onboarding_status", "unknown")
        status_distribution[status] = status_distribution.get(status, 0) + 1

    country_distribution = {}
    for vendor in vendors:
        country = vendor.get("country", "unknown")
        country_distribution[country] = country_distribution.get(country, 0) + 1

    compliance_scores = [v.get("average_compliance_score") for v in vendors if v.get("average_compliance_score")]
    avg_compliance = sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0

    return {
        "total_vendors": total_vendors,
        "desc_approved_count": desc_approved,
        "api_enabled_count": api_enabled,
        "average_compliance_score": round(avg_compliance, 2),
        "status_distribution": status_distribution,
        "country_distribution": country_distribution,
    }

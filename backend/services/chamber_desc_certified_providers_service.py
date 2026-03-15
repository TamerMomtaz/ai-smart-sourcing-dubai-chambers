from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, date
from database import supabase


def create(
    user_id: UUID,
    provider_name: str,
    certification_number: str,
    valid_until: date,
    services_offered: Optional[List[str]] = None,
    compliance_frameworks: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Create a new DESC-certified provider entry."""
    try:
        data = {
            "provider_name": provider_name,
            "certification_number": certification_number,
            "valid_until": valid_until.isoformat(),
            "services_offered": services_offered or [],
            "compliance_frameworks": compliance_frameworks or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = (
            supabase.table("chamber_desc_certified_providers")
            .insert(data)
            .execute()
        )

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception:
        return None


def list_providers(
    user_id: UUID,
    page: int = 1,
    page_size: int = 20,
    certification_number: Optional[str] = None,
    valid_only: bool = False,
) -> tuple[List[Dict[str, Any]], int]:
    """List DESC-certified providers with pagination and optional filters."""
    try:
        offset = (page - 1) * page_size

        query = supabase.table("chamber_desc_certified_providers").select("*", count="exact")

        if certification_number:
            query = query.eq("certification_number", certification_number)

        if valid_only:
            today = date.today().isoformat()
            query = query.gte("valid_until", today)

        query = query.order("provider_name", desc=False)
        query = query.range(offset, offset + page_size - 1)

        result = query.execute()

        total = result.count if result.count is not None else 0
        providers = result.data if result.data else []

        return providers, total
    except Exception:
        return [], 0


def get_by_id(user_id: UUID, provider_id: UUID) -> Optional[Dict[str, Any]]:
    """Get a DESC-certified provider by ID."""
    try:
        result = (
            supabase.table("chamber_desc_certified_providers")
            .select("*")
            .eq("id", str(provider_id))
            .execute()
        )

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception:
        return None


def get_by_certification_number(
    user_id: UUID, certification_number: str
) -> Optional[Dict[str, Any]]:
    """Get a DESC-certified provider by certification number."""
    try:
        result = (
            supabase.table("chamber_desc_certified_providers")
            .select("*")
            .eq("certification_number", certification_number)
            .execute()
        )

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception:
        return None


def get_by_provider_name(
    user_id: UUID, provider_name: str
) -> Optional[Dict[str, Any]]:
    """Get a DESC-certified provider by provider name."""
    try:
        result = (
            supabase.table("chamber_desc_certified_providers")
            .select("*")
            .eq("provider_name", provider_name)
            .execute()
        )

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception:
        return None


def update(
    user_id: UUID,
    provider_id: UUID,
    provider_name: Optional[str] = None,
    certification_number: Optional[str] = None,
    valid_until: Optional[date] = None,
    services_offered: Optional[List[str]] = None,
    compliance_frameworks: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Update a DESC-certified provider entry."""
    try:
        existing = get_by_id(user_id, provider_id)
        if not existing:
            return None

        data = {"updated_at": datetime.now(timezone.utc).isoformat()}

        if provider_name is not None:
            data["provider_name"] = provider_name
        if certification_number is not None:
            data["certification_number"] = certification_number
        if valid_until is not None:
            data["valid_until"] = valid_until.isoformat()
        if services_offered is not None:
            data["services_offered"] = services_offered
        if compliance_frameworks is not None:
            data["compliance_frameworks"] = compliance_frameworks

        result = (
            supabase.table("chamber_desc_certified_providers")
            .update(data)
            .eq("id", str(provider_id))
            .execute()
        )

        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception:
        return None


def delete(user_id: UUID, provider_id: UUID) -> bool:
    """Delete a DESC-certified provider entry (hard delete)."""
    try:
        existing = get_by_id(user_id, provider_id)
        if not existing:
            return False

        result = (
            supabase.table("chamber_desc_certified_providers")
            .delete()
            .eq("id", str(provider_id))
            .execute()
        )

        return True
    except Exception:
        return False


def verify_certification(
    user_id: UUID,
    certification_number: str,
    check_validity: bool = True,
) -> Optional[Dict[str, Any]]:
    """Verify a DESC certification number and optionally check if still valid."""
    try:
        provider = get_by_certification_number(user_id, certification_number)
        if not provider:
            return None

        if check_validity:
            valid_until_str = provider.get("valid_until")
            if valid_until_str:
                valid_until = date.fromisoformat(valid_until_str)
                if valid_until < date.today():
                    return {
                        **provider,
                        "is_valid": False,
                        "expired": True,
                    }

        return {
            **provider,
            "is_valid": True,
            "expired": False,
        }
    except Exception:
        return None


def list_expiring_soon(
    user_id: UUID,
    days_threshold: int = 30,
    page: int = 1,
    page_size: int = 20,
) -> tuple[List[Dict[str, Any]], int]:
    """List DESC certifications expiring within specified days."""
    try:
        offset = (page - 1) * page_size
        today = date.today()
        threshold_date = date.fromordinal(today.toordinal() + days_threshold)

        query = (
            supabase.table("chamber_desc_certified_providers")
            .select("*", count="exact")
            .gte("valid_until", today.isoformat())
            .lte("valid_until", threshold_date.isoformat())
            .order("valid_until", desc=False)
            .range(offset, offset + page_size - 1)
        )

        result = query.execute()

        total = result.count if result.count is not None else 0
        providers = result.data if result.data else []

        return providers, total
    except Exception:
        return [], 0

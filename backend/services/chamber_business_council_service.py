from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


def create(
    name: str,
    country: str,
    description: Optional[str] = None,
    representative_office_locations: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Create a new business council.
    Admin-only operation (enforced by RLS).
    """
    data = {
        "name": name,
        "country": country,
        "description": description,
        "representative_office_locations": representative_office_locations,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    response = supabase.table("chamber_business_councils").insert(data).execute()

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def list_councils(
    page: int = 1,
    page_size: int = 20,
    country: Optional[str] = None,
) -> tuple[List[Dict[str, Any]], int]:
    """
    List business councils with pagination and optional country filter.
    All authenticated users can view (enforced by RLS).
    """
    offset = (page - 1) * page_size

    query = supabase.table("chamber_business_councils").select("*", count="exact")

    if country:
        query = query.eq("country", country)

    query = query.order("name").range(offset, offset + page_size - 1)

    response = query.execute()

    councils = response.data if response.data else []
    total = response.count if response.count is not None else 0

    return councils, total


def get_by_id(council_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get business council by ID.
    All authenticated users can view (enforced by RLS).
    """
    response = (
        supabase.table("chamber_business_councils")
        .select("*")
        .eq("id", str(council_id))
        .execute()
    )

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def update(
    council_id: UUID,
    name: Optional[str] = None,
    country: Optional[str] = None,
    description: Optional[str] = None,
    representative_office_locations: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update business council.
    Admin-only operation (enforced by RLS).
    """
    data: Dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if name is not None:
        data["name"] = name
    if country is not None:
        data["country"] = country
    if description is not None:
        data["description"] = description
    if representative_office_locations is not None:
        data["representative_office_locations"] = representative_office_locations

    response = (
        supabase.table("chamber_business_councils")
        .update(data)
        .eq("id", str(council_id))
        .execute()
    )

    if response.data and len(response.data) > 0:
        return response.data[0]
    return None


def delete(council_id: UUID) -> bool:
    """
    Soft delete business council by setting deleted flag.
    Admin-only operation (enforced by RLS).
    Note: Table has no deleted_at column, so this performs hard delete.
    Consider adding deleted_at column for soft deletes in production.
    """
    response = (
        supabase.table("chamber_business_councils")
        .delete()
        .eq("id", str(council_id))
        .execute()
    )

    return response.data is not None and len(response.data) > 0


def get_by_country(country: str) -> List[Dict[str, Any]]:
    """
    Get all business councils for a specific country.
    All authenticated users can view (enforced by RLS).
    """
    response = (
        supabase.table("chamber_business_councils")
        .select("*")
        .eq("country", country)
        .order("name")
        .execute()
    )

    return response.data if response.data else []


def search_councils(search_term: str) -> List[Dict[str, Any]]:
    """
    Search business councils by name or country.
    All authenticated users can view (enforced by RLS).
    """
    response = (
        supabase.table("chamber_business_councils")
        .select("*")
        .or_(f"name.ilike.%{search_term}%,country.ilike.%{search_term}%")
        .order("name")
        .execute()
    )

    return response.data if response.data else []

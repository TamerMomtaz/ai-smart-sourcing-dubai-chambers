from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import uuid4
from datetime import datetime, timezone, timedelta
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vendors", tags=["Vendor Invites"])


# ---------- Request / Response schemas ----------

class InviteRequest(BaseModel):
    vendor_name: str
    vendor_email: EmailStr
    sector: str


class OnboardRequest(BaseModel):
    company_name: str
    country: str
    sector: str
    website: Optional[str] = None
    contact_name: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    year_established: Optional[int] = None
    employee_count: Optional[str] = None
    desc_certified: Optional[bool] = False
    certifications: Optional[str] = None
    previous_government_work: Optional[str] = None
    data_residency_country: Optional[str] = None
    brief_description: Optional[str] = None


# ---------- Table readiness check ----------

_table_ready = None  # cached after first successful check


def _check_invites_table():
    """Verify chamber_vendor_invites is reachable via PostgREST. Caches result."""
    global _table_ready
    if _table_ready:
        return True
    try:
        supabase.table("chamber_vendor_invites").select("id").limit(1).execute()
        _table_ready = True
        return True
    except Exception as e:
        logger.error(
            "chamber_vendor_invites table is not accessible via PostgREST. "
            "Run the migration: database/vendor_invite_migration.sql "
            "then execute: NOTIFY pgrst, 'reload schema'; — error: %s",
            e,
        )
        return False


# ---------- POST /api/v1/vendors/invite  (auth required) ----------

@router.post(
    "/invite",
    status_code=status.HTTP_201_CREATED,
    summary="Invite a vendor to onboard",
)
async def invite_vendor(
    body: InviteRequest,
    current_user: dict = Depends(get_current_user),
):
    user_role = current_user.get("role")
    if user_role not in ["admin", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Only admin or analyst can invite vendors",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    if not _check_invites_table():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "Service Unavailable",
                "detail": "Vendor invites table is not provisioned. Run database/vendor_invite_migration.sql",
                "code": "TABLE_NOT_PROVISIONED",
            },
        )

    token = str(uuid4())
    now = datetime.now(timezone.utc)

    row = {
        "id": str(uuid4()),
        "token": token,
        "vendor_name": body.vendor_name,
        "vendor_email": body.vendor_email,
        "sector": body.sector,
        "status": "pending",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=30)).isoformat(),
    }

    try:
        result = supabase.table("chamber_vendor_invites").insert(row).execute()
        if not result.data:
            raise Exception("Insert returned no data")
    except Exception as e:
        logger.error(f"Failed to create invite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to create vendor invite",
                "code": "INVITE_CREATE_FAILED",
            },
        )

    return {
        "token": token,
        "invite_url": f"/onboard/{token}",
    }


# ---------- Public router (no auth) ----------

public_router = APIRouter(prefix="/vendors", tags=["Vendor Onboarding (Public)"])


@public_router.get(
    "/onboard/{token}",
    summary="Get invite details by token (public)",
)
async def get_invite(token: str):
    """Return invite details so the onboarding form can pre-fill fields."""
    try:
        result = (
            supabase.table("chamber_vendor_invites")
            .select("*")
            .eq("token", token)
            .maybe_single()
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to fetch invite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": str(e)},
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Not Found",
                "detail": "This invitation link is invalid or has expired. Please contact the Chamber for a new invitation.",
                "code": "INVITE_NOT_FOUND",
            },
        )

    invite = result.data
    now = datetime.now(timezone.utc)
    expires_at = datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00"))

    if invite["status"] != "pending" or now > expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={
                "error": "Gone",
                "detail": "This invitation link is invalid or has expired. Please contact the Chamber for a new invitation.",
                "code": "INVITE_EXPIRED",
            },
        )

    return {
        "vendor_name": invite["vendor_name"],
        "vendor_email": invite["vendor_email"],
        "sector": invite["sector"],
    }


@public_router.post(
    "/onboard/{token}",
    status_code=status.HTTP_201_CREATED,
    summary="Complete vendor onboarding (public)",
)
async def onboard_vendor(token: str, body: OnboardRequest):
    """Public endpoint — creates vendor from invite token."""

    # 1. Validate token
    try:
        result = (
            supabase.table("chamber_vendor_invites")
            .select("*")
            .eq("token", token)
            .maybe_single()
            .execute()
        )
    except Exception as e:
        logger.error(f"Failed to fetch invite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "detail": str(e)},
        )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Not Found",
                "detail": "This invitation link is invalid or has expired.",
                "code": "INVITE_NOT_FOUND",
            },
        )

    invite = result.data
    now = datetime.now(timezone.utc)
    expires_at = datetime.fromisoformat(invite["expires_at"].replace("Z", "+00:00"))

    if invite["status"] != "pending" or now > expires_at:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={
                "error": "Gone",
                "detail": "This invitation link is invalid or has expired.",
                "code": "INVITE_EXPIRED",
            },
        )

    # 2. Create vendor record
    vendor_id = str(uuid4())
    vendor_data = {
        "id": vendor_id,
        "name": body.company_name,
        "country": body.country,
        "contact_email": str(body.contact_email),
        "contact_phone": body.contact_phone,
        "website": body.website,
        "company_registration": "",
        "is_desc_approved": body.desc_certified or False,
        "onboarding_status": "submitted",
        "submission_history_count": 0,
        "api_access_enabled": False,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    try:
        vendor_result = supabase.table("chamber_vendors").insert(vendor_data).execute()
        if not vendor_result.data:
            raise Exception("Vendor insert returned no data")
    except Exception as e:
        logger.error(f"Failed to create vendor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "detail": "Failed to create vendor record",
                "code": "VENDOR_CREATE_FAILED",
            },
        )

    # 3. Create vendor profile with extended data
    try:
        profile_data = {
            "id": str(uuid4()),
            "vendor_id": vendor_id,
            "team_size": body.employee_count,
            "certifications": [c.strip() for c in body.certifications.split(",")] if body.certifications else [],
            "year_established": body.year_established,
            "data_residency_country": body.data_residency_country,
            "previous_government_work": body.previous_government_work,
            "brief_description": body.brief_description,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        supabase.table("chamber_vendor_profiles").insert(profile_data).execute()
    except Exception as e:
        logger.warning(f"Failed to create vendor profile (non-fatal): {e}")

    # 4. Mark invite as completed
    try:
        supabase.table("chamber_vendor_invites").update({
            "status": "completed",
            "completed_at": now.isoformat(),
        }).eq("token", token).execute()
    except Exception as e:
        logger.warning(f"Failed to update invite status: {e}")

    return {
        "success": True,
        "vendor_id": vendor_id,
        "message": "Welcome to AI Smart Sourcing",
    }

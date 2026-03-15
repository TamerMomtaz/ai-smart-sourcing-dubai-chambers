from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


class ChamberVendorProfileService:
    """
    Service for managing chamber vendor profiles.
    All operations verify vendor_id ownership.
    """

    @staticmethod
    async def create(
        vendor_id: UUID,
        team_size: Optional[int] = None,
        funding_stage: Optional[str] = None,
        technology_stack: Optional[List[str]] = None,
        certifications: Optional[List[str]] = None,
        onboarding_stage: Optional[str] = None,
        pilot_status: Optional[str] = None,
        procurement_status: Optional[str] = None,
        api_documentation_url: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new vendor profile.
        Returns None if vendor does not exist or profile already exists.
        """
        # Verify vendor exists
        vendor_check = supabase.table("chamber_vendors").select("id").eq("id", str(vendor_id)).execute()
        if not vendor_check.data:
            return None

        # Check if profile already exists
        existing = supabase.table("chamber_vendor_profiles").select("id").eq("vendor_id", str(vendor_id)).execute()
        if existing.data:
            return None

        profile_data = {
            "vendor_id": str(vendor_id),
            "team_size": team_size,
            "funding_stage": funding_stage,
            "technology_stack": technology_stack,
            "certifications": certifications,
            "onboarding_stage": onboarding_stage,
            "pilot_status": pilot_status,
            "procurement_status": procurement_status,
            "api_documentation_url": api_documentation_url,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = supabase.table("chamber_vendor_profiles").insert(profile_data).execute()
        if result.data:
            return result.data[0]
        return None

    @staticmethod
    async def get_by_vendor_id(vendor_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get vendor profile by vendor_id.
        Returns None if not found.
        """
        result = (
            supabase.table("chamber_vendor_profiles")
            .select("*")
            .eq("vendor_id", str(vendor_id))
            .execute()
        )
        if result.data:
            return result.data[0]
        return None

    @staticmethod
    async def get_by_id(profile_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get vendor profile by profile ID.
        Returns None if not found.
        """
        result = (
            supabase.table("chamber_vendor_profiles")
            .select("*")
            .eq("id", str(profile_id))
            .execute()
        )
        if result.data:
            return result.data[0]
        return None

    @staticmethod
    async def list_profiles(
        page: int = 1,
        page_size: int = 50,
        funding_stage: Optional[str] = None,
        pilot_status: Optional[str] = None,
        procurement_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List vendor profiles with pagination and optional filters.
        Returns dict with 'data' and 'total' keys.
        """
        offset = (page - 1) * page_size

        # Build query
        query = supabase.table("chamber_vendor_profiles").select("*", count="exact")

        # Apply filters
        if funding_stage:
            query = query.eq("funding_stage", funding_stage)
        if pilot_status:
            query = query.eq("pilot_status", pilot_status)
        if procurement_status:
            query = query.eq("procurement_status", procurement_status)

        # Apply pagination and ordering
        query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)

        result = query.execute()

        return {
            "data": result.data or [],
            "total": result.count or 0,
        }

    @staticmethod
    async def update(
        vendor_id: UUID,
        team_size: Optional[int] = None,
        funding_stage: Optional[str] = None,
        technology_stack: Optional[List[str]] = None,
        certifications: Optional[List[str]] = None,
        onboarding_stage: Optional[str] = None,
        pilot_status: Optional[str] = None,
        procurement_status: Optional[str] = None,
        api_documentation_url: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Update vendor profile.
        Returns None if profile not found.
        """
        # Check if profile exists
        existing = await ChamberVendorProfileService.get_by_vendor_id(vendor_id)
        if not existing:
            return None

        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}

        if team_size is not None:
            update_data["team_size"] = team_size
        if funding_stage is not None:
            update_data["funding_stage"] = funding_stage
        if technology_stack is not None:
            update_data["technology_stack"] = technology_stack
        if certifications is not None:
            update_data["certifications"] = certifications
        if onboarding_stage is not None:
            update_data["onboarding_stage"] = onboarding_stage
        if pilot_status is not None:
            update_data["pilot_status"] = pilot_status
        if procurement_status is not None:
            update_data["procurement_status"] = procurement_status
        if api_documentation_url is not None:
            update_data["api_documentation_url"] = api_documentation_url

        result = (
            supabase.table("chamber_vendor_profiles")
            .update(update_data)
            .eq("vendor_id", str(vendor_id))
            .execute()
        )

        if result.data:
            return result.data[0]
        return None

    @staticmethod
    async def delete(vendor_id: UUID) -> bool:
        """
        Delete vendor profile (hard delete - cascade handled by DB).
        Returns True if deleted, False if not found.
        """
        existing = await ChamberVendorProfileService.get_by_vendor_id(vendor_id)
        if not existing:
            return False

        result = (
            supabase.table("chamber_vendor_profiles")
            .delete()
            .eq("vendor_id", str(vendor_id))
            .execute()
        )

        return bool(result.data)

    @staticmethod
    async def get_profiles_by_funding_stage(funding_stage: str) -> List[Dict[str, Any]]:
        """
        Get all profiles by funding stage.
        """
        result = (
            supabase.table("chamber_vendor_profiles")
            .select("*")
            .eq("funding_stage", funding_stage)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    @staticmethod
    async def get_profiles_by_pilot_status(pilot_status: str) -> List[Dict[str, Any]]:
        """
        Get all profiles by pilot status.
        """
        result = (
            supabase.table("chamber_vendor_profiles")
            .select("*")
            .eq("pilot_status", pilot_status)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    @staticmethod
    async def get_profiles_by_procurement_status(procurement_status: str) -> List[Dict[str, Any]]:
        """
        Get all profiles by procurement status.
        """
        result = (
            supabase.table("chamber_vendor_profiles")
            .select("*")
            .eq("procurement_status", procurement_status)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []

    @staticmethod
    async def get_profiles_with_vendor_details(
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """
        Get profiles joined with vendor details.
        Returns dict with 'data' and 'total' keys.
        """
        offset = (page - 1) * page_size

        result = (
            supabase.table("chamber_vendor_profiles")
            .select(
                """
                *,
                chamber_vendors (
                    id,
                    name,
                    company_registration,
                    country,
                    contact_email,
                    is_desc_approved,
                    onboarding_status
                )
            """,
                count="exact",
            )
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        return {
            "data": result.data or [],
            "total": result.count or 0,
        }

    @staticmethod
    async def update_onboarding_stage(vendor_id: UUID, onboarding_stage: str) -> Optional[Dict[str, Any]]:
        """
        Update only the onboarding stage.
        Returns None if profile not found.
        """
        existing = await ChamberVendorProfileService.get_by_vendor_id(vendor_id)
        if not existing:
            return None

        update_data = {
            "onboarding_stage": onboarding_stage,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = (
            supabase.table("chamber_vendor_profiles")
            .update(update_data)
            .eq("vendor_id", str(vendor_id))
            .execute()
        )

        if result.data:
            return result.data[0]
        return None

    @staticmethod
    async def update_pilot_status(vendor_id: UUID, pilot_status: str) -> Optional[Dict[str, Any]]:
        """
        Update only the pilot status.
        Returns None if profile not found.
        """
        existing = await ChamberVendorProfileService.get_by_vendor_id(vendor_id)
        if not existing:
            return None

        update_data = {
            "pilot_status": pilot_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = (
            supabase.table("chamber_vendor_profiles")
            .update(update_data)
            .eq("vendor_id", str(vendor_id))
            .execute()
        )

        if result.data:
            return result.data[0]
        return None

    @staticmethod
    async def update_procurement_status(vendor_id: UUID, procurement_status: str) -> Optional[Dict[str, Any]]:
        """
        Update only the procurement status.
        Returns None if profile not found.
        """
        existing = await ChamberVendorProfileService.get_by_vendor_id(vendor_id)
        if not existing:
            return None

        update_data = {
            "procurement_status": procurement_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        result = (
            supabase.table("chamber_vendor_profiles")
            .update(update_data)
            .eq("vendor_id", str(vendor_id))
            .execute()
        )

        if result.data:
            return result.data[0]
        return None

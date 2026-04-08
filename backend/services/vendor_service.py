from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from database import supabase


def get_vendor_by_id(user_id: str, vendor_id: UUID, user_role: str) -> Optional[Dict[str, Any]]:
    """
    Get vendor profile and submission history by vendor ID.
    Analysts/executives can view any vendor, vendors can only view their own profile.
    """
    try:
        # Check permissions
        if user_role == "vendor":
            # Vendors can only view their own profile
            if str(vendor_id) != user_id:
                return None
        elif user_role not in ["analyst", "executive", "compliance_officer", "business_group_lead", "admin"]:
            return None

        # Fetch vendor data
        vendor_response = supabase.table("chamber_vendors").select(
            "id, name, company_registration, country, contact_email, contact_phone, website, "
            "is_desc_approved, desc_badge_issued_date, onboarding_status, submission_history_count, "
            "average_compliance_score, created_at, updated_at"
        ).eq("id", str(vendor_id)).execute()

        if not vendor_response.data or len(vendor_response.data) == 0:
            return None

        vendor = vendor_response.data[0]

        # Fetch vendor profile (extended data)
        profile_response = supabase.table("chamber_vendor_profiles").select(
            "team_size, funding_stage, technology_stack, certifications, onboarding_stage, pilot_status"
        ).eq("vendor_id", str(vendor_id)).execute()

        profile = None
        if profile_response.data and len(profile_response.data) > 0:
            profile_data = profile_response.data[0]
            profile = {
                "team_size": profile_data.get("team_size"),
                "funding_stage": profile_data.get("funding_stage"),
                "technology_stack": profile_data.get("technology_stack"),
                "certifications": profile_data.get("certifications"),
                "onboarding_stage": profile_data.get("onboarding_stage"),
                "pilot_status": profile_data.get("pilot_status"),
            }

        # Build response
        return {
            "id": vendor["id"],
            "name": vendor["name"],
            "company_registration": vendor["company_registration"],
            "country": vendor["country"],
            "contact_email": vendor["contact_email"],
            "contact_phone": vendor.get("contact_phone"),
            "website": vendor.get("website"),
            "is_desc_approved": vendor["is_desc_approved"],
            "desc_badge_issued_date": vendor.get("desc_badge_issued_date"),
            "onboarding_status": vendor["onboarding_status"],
            "submission_history_count": vendor["submission_history_count"],
            "average_compliance_score": vendor.get("average_compliance_score"),
            "profile": profile,
        }

    except Exception as e:
        print(f"Error fetching vendor by ID: {e}")
        return None


def update_vendor_profile(
    user_id: str,
    vendor_id: UUID,
    user_role: str,
    update_data: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Update vendor profile.
    Vendors can only update their own profile.
    Analysts can update any vendor profile.
    """
    try:
        # Check permissions
        if user_role == "vendor":
            # Vendors can only update their own profile
            if str(vendor_id) != user_id:
                return None
        elif user_role not in ["analyst", "executive", "compliance_officer", "business_group_lead", "admin"]:
            return None

        # Verify vendor exists
        vendor_response = supabase.table("chamber_vendors").select("id").eq(
            "id", str(vendor_id)
        ).execute()

        if not vendor_response.data or len(vendor_response.data) == 0:
            return None

        # Separate vendor fields from profile fields
        vendor_fields = {}
        profile_fields = {}

        allowed_vendor_fields = ["name", "contact_email", "contact_phone", "website"]
        
        for key, value in update_data.items():
            if key == "profile" and isinstance(value, dict):
                profile_fields = value
            elif key in allowed_vendor_fields:
                vendor_fields[key] = value

        # Update vendor table if there are vendor fields
        if vendor_fields:
            vendor_fields["updated_at"] = datetime.now(timezone.utc).isoformat()
            supabase.table("chamber_vendors").update(vendor_fields).eq(
                "id", str(vendor_id)
            ).execute()

        # Update or insert vendor profile if there are profile fields
        if profile_fields:
            # Check if profile exists
            profile_check = supabase.table("chamber_vendor_profiles").select("id").eq(
                "vendor_id", str(vendor_id)
            ).execute()

            profile_update_data = {
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

            allowed_profile_fields = [
                "team_size", "funding_stage", "technology_stack",
                "certifications", "onboarding_stage", "pilot_status"
            ]

            for key, value in profile_fields.items():
                if key in allowed_profile_fields:
                    profile_update_data[key] = value

            if profile_check.data and len(profile_check.data) > 0:
                # Update existing profile
                supabase.table("chamber_vendor_profiles").update(profile_update_data).eq(
                    "vendor_id", str(vendor_id)
                ).execute()
            else:
                # Insert new profile
                profile_update_data["vendor_id"] = str(vendor_id)
                profile_update_data["created_at"] = datetime.now(timezone.utc).isoformat()
                supabase.table("chamber_vendor_profiles").insert(profile_update_data).execute()

        return {
            "vendor_id": str(vendor_id),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        print(f"Error updating vendor profile: {e}")
        return None


def list_vendors(
    user_id: str,
    user_role: str,
    page: int = 1,
    page_size: int = 20,
    filters: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    List vendors with pagination and filters.
    Only accessible by analysts, executives, and compliance officers.
    """
    try:
        # Check permissions - only internal roles can list all vendors
        if user_role not in ["analyst", "executive", "compliance_officer", "business_group_lead", "admin"]:
            return None

        offset = (page - 1) * page_size

        # Build query
        query = supabase.table("chamber_vendors").select(
            "id, name, company_registration, country, contact_email, is_desc_approved, "
            "onboarding_status, submission_history_count, average_compliance_score, created_at",
            count="exact"
        )

        # Apply filters
        if filters:
            if "country" in filters and filters["country"]:
                query = query.eq("country", filters["country"])
            if "is_desc_approved" in filters and filters["is_desc_approved"] is not None:
                query = query.eq("is_desc_approved", filters["is_desc_approved"])
            if "onboarding_status" in filters and filters["onboarding_status"]:
                query = query.eq("onboarding_status", filters["onboarding_status"])

        # Apply pagination and ordering
        query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)

        response = query.execute()

        total = response.count if hasattr(response, "count") else 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "vendors": response.data or [],
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            }
        }

    except Exception as e:
        print(f"Error listing vendors: {e}")
        return None


def create_vendor(user_id: str, user_role: str, vendor_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create a new vendor.
    Only accessible by analysts and admins.
    """
    try:
        # Check permissions
        if user_role not in ["analyst", "admin"]:
            return None

        # Prepare vendor data
        insert_data = {
            "name": vendor_data["name"],
            "company_registration": vendor_data["company_registration"],
            "country": vendor_data["country"],
            "contact_email": vendor_data["contact_email"],
            "contact_phone": vendor_data.get("contact_phone"),
            "website": vendor_data.get("website"),
            "is_desc_approved": vendor_data.get("is_desc_approved", False),
            "onboarding_status": vendor_data.get("onboarding_status", "submitted"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Insert vendor
        response = supabase.table("chamber_vendors").insert(insert_data).execute()

        if not response.data or len(response.data) == 0:
            return None

        vendor = response.data[0]

        # Insert profile if provided
        if "profile" in vendor_data and isinstance(vendor_data["profile"], dict):
            profile_data = {
                "vendor_id": vendor["id"],
                "team_size": vendor_data["profile"].get("team_size"),
                "funding_stage": vendor_data["profile"].get("funding_stage"),
                "technology_stack": vendor_data["profile"].get("technology_stack"),
                "certifications": vendor_data["profile"].get("certifications"),
                "onboarding_stage": vendor_data["profile"].get("onboarding_stage"),
                "pilot_status": vendor_data["profile"].get("pilot_status"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            supabase.table("chamber_vendor_profiles").insert(profile_data).execute()

        return {
            "id": vendor["id"],
            "created_at": vendor["created_at"]
        }

    except Exception as e:
        print(f"Error creating vendor: {e}")
        return None


def delete_vendor(user_id: str, user_role: str, vendor_id: UUID) -> bool:
    """
    Soft delete a vendor (mark as deleted).
    Only accessible by admins.
    """
    try:
        # Check permissions - only admins can delete vendors
        if user_role != "admin":
            return False

        # Verify vendor exists
        vendor_response = supabase.table("chamber_vendors").select("id").eq(
            "id", str(vendor_id)
        ).execute()

        if not vendor_response.data or len(vendor_response.data) == 0:
            return False

        # Soft delete by updating a deleted_at field or status
        # Since schema doesn't have deleted_at, we'll update onboarding_status to 'rejected'
        supabase.table("chamber_vendors").update({
            "onboarding_status": "rejected",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", str(vendor_id)).execute()

        return True

    except Exception as e:
        print(f"Error deleting vendor: {e}")
        return False


def get_procurement_readiness(user_id: str, vendor_id: UUID, user_role: str) -> Optional[Dict[str, Any]]:
    """
    Get procurement readiness data for a vendor.
    Aggregates proposals, pilots, evaluations, hallucination checks,
    DESC compliance, and trade license status.
    """
    try:
        # Check permissions
        if user_role == "vendor":
            if str(vendor_id) != user_id:
                return None
        elif user_role not in ["analyst", "executive", "compliance_officer", "business_group_lead", "admin"]:
            return None

        vendor_id_str = str(vendor_id)

        # Fetch vendor DESC status
        vendor_resp = supabase.table("chamber_vendors").select(
            "is_desc_approved"
        ).eq("id", vendor_id_str).execute()
        is_desc_approved = False
        if vendor_resp.data:
            is_desc_approved = vendor_resp.data[0].get("is_desc_approved", False)

        # Fetch proposals for this vendor (shortlisted/evaluated/approved)
        proposals_resp = supabase.table("chamber_proposals").select(
            "id, title, status, composite_score"
        ).eq("submitter_id", vendor_id_str).in_(
            "status", ["shortlisted", "evaluated", "approved"]
        ).order("composite_score", desc=True).execute()
        proposals = proposals_resp.data or []

        has_shortlisted = any(p.get("status") == "shortlisted" for p in proposals)
        has_evaluated = len(proposals) > 0
        best_score = proposals[0].get("composite_score") if proposals else None

        # Fetch pilots for this vendor
        pilots_resp = supabase.table("chamber_pilots").select(
            "id, status, outcome_rating, adoption_decision"
        ).eq("vendor_id", vendor_id_str).execute()
        pilots = pilots_resp.data or []

        completed_pilots = [p for p in pilots if p.get("status") == "completed"]
        active_pilots = [p for p in pilots if p.get("status") in ("active", "extended")]
        has_completed_pilot = len(completed_pilots) > 0
        has_active_pilot = len(active_pilots) > 0
        pilot_rating = completed_pilots[0].get("outcome_rating") if completed_pilots else None

        # Fetch grounding scores from hallucination checks for this vendor's proposals
        grounding_score = None
        if proposals:
            proposal_ids = [p["id"] for p in proposals]
            evals_resp = supabase.table("chamber_evaluations").select(
                "id"
            ).in_("proposal_id", proposal_ids).execute()
            eval_ids = [e["id"] for e in (evals_resp.data or [])]

            if eval_ids:
                hall_resp = supabase.table("chamber_hallucination_checks").select(
                    "grounding_score"
                ).in_("evaluation_id", eval_ids).order(
                    "created_at", desc=True
                ).limit(1).execute()
                if hall_resp.data:
                    grounding_score = hall_resp.data[0].get("grounding_score")

        # Fetch trade license status
        license_resp = supabase.table("chamber_vendors").select(
            "trade_license_status"
        ).eq("id", vendor_id_str).execute()
        trade_license_verified = False
        trade_license_status = "unverified"
        if license_resp.data:
            trade_license_status = license_resp.data[0].get("trade_license_status", "unverified") or "unverified"
            trade_license_verified = trade_license_status == "verified"

        # Determine readiness status
        if has_completed_pilot and any(p.get("adoption_decision") == "adopt" for p in completed_pilots):
            readiness_status = "ready_for_procurement"
        elif has_active_pilot:
            readiness_status = "in_pilot"
        elif has_shortlisted or has_evaluated:
            readiness_status = "under_evaluation"
        else:
            readiness_status = "not_ready"

        return {
            "readiness_status": readiness_status,
            "evaluation": {
                "complete": has_evaluated,
                "composite_score": best_score,
            },
            "evidence_validation": {
                "verified": grounding_score is not None and grounding_score >= 70,
                "grounding_score": grounding_score,
            },
            "desc_compliance": {
                "checked": True,
                "approved": is_desc_approved,
            },
            "trade_license": {
                "verified": trade_license_verified,
                "status": trade_license_status,
            },
            "pilot": {
                "completed": has_completed_pilot,
                "outcome_rating": pilot_rating,
            },
        }

    except Exception as e:
        print(f"Error fetching procurement readiness: {e}")
        return None

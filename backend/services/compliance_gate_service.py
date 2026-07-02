"""Pre-Evaluation Compliance Gate — Layer 1: deterministic, rule-based checks.

Runs BEFORE AI evaluation. No AI tokens spent.
All checks are binary pass/fail/flag. Flagged proposals are NOT auto-rejected.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import logging

from database import supabase

logger = logging.getLogger(__name__)

REQUIRED_PROPOSAL_FIELDS = ["title", "sector", "technology_type", "maturity_level"]


def _check_desc_certification(*, vendor: Dict[str, Any]) -> Dict[str, Any]:
    """Rule 1: Is the submitting vendor DESC-certified?"""
    is_approved = vendor.get("is_desc_approved", False)
    desc_provider_id = vendor.get("desc_certified_provider_id")
    certified = bool(is_approved) or bool(desc_provider_id)
    return {
        "rule": "DESC Certification",
        "result": "pass" if certified else "flag",
        "detail": (
            f"Certified (DESC approved)"
            if certified
            else "Vendor is not DESC-certified — flagged for review"
        ),
    }


def _check_data_residency(*, vendor: Dict[str, Any]) -> Dict[str, Any]:
    """Rule 2: Does the vendor's hosting country match UAE?"""
    country = (vendor.get("country") or "").strip().upper()
    # Also check vendor profile data_residency if available
    data_residency = (vendor.get("data_residency") or "").strip().upper()
    is_uae = country in ("UAE", "AE", "UNITED ARAB EMIRATES") or data_residency in (
        "UAE",
        "AE",
        "UNITED ARAB EMIRATES",
    )
    location = country or data_residency or "Unknown"
    return {
        "rule": "Data Residency",
        "result": "pass" if is_uae else "flag",
        "detail": (
            f"Vendor hosted in UAE"
            if is_uae
            else f"Vendor hosted in {location} — flagged for review"
        ),
    }


def _check_required_certifications(*, vendor_id: str) -> Dict[str, Any]:
    """Rule 3: Does the vendor hold minimum certifications (ISO 27001)?"""
    try:
        flags_resp = (
            supabase.table("chamber_vendor_flags")
            .select("flag_type, expiry_date, resolution_status")
            .eq("vendor_id", vendor_id)
            .in_("flag_type", ["iso_27001"])
            .execute()
        )
        today_str = datetime.now(timezone.utc).date().isoformat()  # ISO string for date comparison
        valid_certs = [
            f
            for f in (flags_resp.data or [])
            if (
                f.get("expiry_date") is None
                or f["expiry_date"] >= today_str  # both sides are strings now
            )
            and f.get("resolution_status") != "dismissed"
        ]
        has_iso = any(f["flag_type"] == "iso_27001" for f in valid_certs)
        return {
            "rule": "Required Certifications",
            "result": "pass" if has_iso else "flag",
            "detail": (
                "ISO 27001 certification present"
                if has_iso
                else "ISO 27001 certification not found — flagged for review"
            ),
        }
    except Exception as e:
        logger.warning("certification check failed: %s", e)
        return {
            "rule": "Required Certifications",
            "result": "flag",
            "detail": "Unable to verify certifications",
        }


def _check_duplicate_submission(
    *, vendor_id: str, proposal_id: str, sector: Optional[str], sourcing_case_id: Optional[str]
) -> Dict[str, Any]:
    """Rule 4: Has this vendor already submitted for the same sector/sourcing case?"""
    try:
        query = (
            supabase.table("chamber_proposals")
            .select("id, title, sector")
            .eq("submitter_id", vendor_id)
            .neq("id", proposal_id)
        )
        if sourcing_case_id:
            query = query.eq("sourcing_case_id", sourcing_case_id)
        elif sector:
            query = query.eq("sector", sector)
        else:
            return {
                "rule": "Duplicate Check",
                "result": "pass",
                "detail": "No sector or sourcing case to check against",
            }

        resp = query.execute()
        duplicates = resp.data or []
        if duplicates:
            titles = ", ".join(d["title"] for d in duplicates[:3])
            return {
                "rule": "Duplicate Check",
                "result": "flag",
                "detail": f"Vendor has {len(duplicates)} other submission(s) in same sector/case: {titles}",
            }
        return {
            "rule": "Duplicate Check",
            "result": "pass",
            "detail": "No duplicate submissions found",
        }
    except Exception as e:
        logger.warning("duplicate check failed: %s", e)
        return {
            "rule": "Duplicate Check",
            "result": "flag",
            "detail": f"Unable to check duplicates — {e}",
        }


def _check_completeness(*, proposal: Dict[str, Any]) -> Dict[str, Any]:
    """Rule 5: Are all required proposal fields populated?"""
    missing = [
        f for f in REQUIRED_PROPOSAL_FIELDS if not proposal.get(f)
    ]
    if missing:
        return {
            "rule": "Completeness Check",
            "result": "fail",
            "detail": f"Missing required fields: {', '.join(missing)}",
        }
    return {
        "rule": "Completeness Check",
        "result": "pass",
        "detail": "All required fields are populated",
    }


def run_compliance_gate(*, proposal_id: str) -> Dict[str, Any]:
    """Run all compliance gate checks on a proposal.

    Returns the gate result dict with overall status, checks list, and recommendation.
    Also persists the result to the chamber_proposals table.
    """
    # Fetch proposal
    proposal_resp = (
        supabase.table("chamber_proposals")
        .select("id, title, submitter_id, sector, technology_type, maturity_level, language, sourcing_case_id")
        .eq("id", proposal_id)
        .maybe_single()
        .execute()
    )
    if not proposal_resp.data:
        return None

    proposal = proposal_resp.data
    vendor_id = str(proposal["submitter_id"])

    # Fetch vendor info
    vendor_resp = (
        supabase.table("chamber_vendors")
        .select("id, name, is_desc_approved, desc_certified_provider_id, country")
        .eq("id", vendor_id)
        .maybe_single()
        .execute()
    )
    vendor = vendor_resp.data or {}

    # Run all five checks
    checks: List[Dict[str, Any]] = [
        _check_desc_certification(vendor=vendor),
        _check_data_residency(vendor=vendor),
        _check_required_certifications(vendor_id=vendor_id),
        _check_duplicate_submission(
            vendor_id=vendor_id,
            proposal_id=proposal_id,
            sector=proposal.get("sector"),
            sourcing_case_id=proposal.get("sourcing_case_id"),
        ),
        _check_completeness(proposal=proposal),
    ]

    # Determine overall status
    results = [c["result"] for c in checks]
    if "fail" in results:
        overall = "fail"
        recommendation = "Blocked — incomplete submission"
    elif "flag" in results:
        overall = "flagged"
        recommendation = "Review flags before evaluation"
    else:
        overall = "pass"
        recommendation = "Proceed to AI evaluation"

    gate_result = {
        "overall": overall,
        "checks": checks,
        "recommendation": recommendation,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "ran_by": "system",
    }

    # Persist to database
    supabase.table("chamber_proposals").update(
        {
            "compliance_gate_result": gate_result,
            "compliance_gate_status": overall,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    ).eq("id", proposal_id).execute()

    logger.info("compliance gate completed for proposal %s: %s", proposal_id, overall)
    return gate_result

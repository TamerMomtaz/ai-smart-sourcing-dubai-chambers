#!/usr/bin/env python3
"""
Seed E2E Test Data — Demo Data for Dubai Chambers Smart Sourcing Platform
=========================================================================
Creates realistic, clearly-labeled demo data that exercises all new features:
  - 2 Sourcing Cases (Gap 1)
  - Links 2 existing proposals to sourcing cases (Gap 3)
  - 1 Pilot (Gap 4)
  - 2 Alerts (Gap 22)
  - 1 Sector Assignment (Gap 30)

Usage:
  cd backend && python ../database/seed_e2e_test_data.py

Requires SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY env vars.
"""

import sys
import os
import json

# Allow running from repo root or backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
sys.path.insert(0, "backend")

from database import supabase

DEMO_TAG = "[DEMO]"


def log(msg):
    print(f"  {msg}")


def fatal(msg):
    print(f"\n  FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def query_existing_data():
    """Query existing users, vendors, and proposals needed for seeding."""
    print("\n=== Querying existing data ===")

    # --- Users (find an analyst) ---
    users_resp = supabase.table("chamber_users").select("id, email, role, full_name").execute()
    users = users_resp.data or []
    log(f"Found {len(users)} users")
    for u in users:
        log(f"  {u['role']:20s} | {u['id'][:8]}... | {u.get('full_name', '?')}")

    analyst = next((u for u in users if u["role"] == "analyst"), None)
    admin = next((u for u in users if u["role"] == "admin"), None)
    # Fall back to admin if no analyst exists
    staff_user = analyst or admin
    if not staff_user:
        fatal("No analyst or admin user found in chamber_users. Seed at least one user first.")
    log(f"Using staff user: {staff_user['full_name']} ({staff_user['role']}) — {staff_user['id'][:8]}...")

    # --- Vendors ---
    vendors_resp = supabase.table("chamber_vendors").select("id, name, country").limit(5).execute()
    vendors = vendors_resp.data or []
    log(f"Found {len(vendors)} vendors")
    if not vendors:
        fatal("No vendors found in chamber_vendors. Seed at least one vendor first.")

    # --- Proposals (prefer ones without sourcing_case_id) ---
    proposals_resp = (
        supabase.table("chamber_proposals")
        .select("id, title, status, sector, technology_type, submitter_id, sourcing_case_id")
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    proposals = proposals_resp.data or []
    log(f"Found {len(proposals)} proposals")
    if len(proposals) < 2:
        fatal("Need at least 2 existing proposals. Seed proposals first.")

    # Prefer proposals without an existing sourcing case link
    unlinked = [p for p in proposals if not p.get("sourcing_case_id")]
    log(f"  {len(unlinked)} unlinked proposals available")

    return staff_user, vendors, proposals, unlinked


def find_best_proposal(proposals, preferred_sector=None, exclude_ids=None):
    """Find the best proposal to link, preferring sector match and unlinked."""
    exclude_ids = exclude_ids or set()
    candidates = [p for p in proposals if p["id"] not in exclude_ids]

    if preferred_sector:
        # Try sector match first
        sector_match = [
            p for p in candidates
            if p.get("sector") and preferred_sector.lower() in p["sector"].lower()
        ]
        if sector_match:
            return sector_match[0]

    # Fall back to first available unlinked
    unlinked = [p for p in candidates if not p.get("sourcing_case_id")]
    if unlinked:
        return unlinked[0]

    # Last resort: any available
    return candidates[0] if candidates else None


def seed_sourcing_cases(staff_user):
    """Insert 2 sourcing cases (Gap 1)."""
    print("\n=== Step 1: Creating 2 Sourcing Cases (Gap 1) ===")

    cases_data = [
        {
            "title": f"{DEMO_TAG} Smart Building IoT Security Platform",
            "problem_statement": (
                "Dubai Municipality requires an integrated IoT security solution "
                "for 50+ smart buildings across the emirate. Must support real-time "
                "threat detection, DESC compliance, and Arabic interface."
            ),
            "requesting_entity": "Dubai Municipality",
            "sector": "Cybersecurity & Digital Trust",
            "technology_domain": "IoT Security",
            "urgency": "high",
            "status": "open",
            "source_channel": "partner_referral",
            "created_by": staff_user["id"],
        },
        {
            "title": f"{DEMO_TAG} AI-Powered Trade Document Processing",
            "problem_statement": (
                "Dubai Chambers needs automated processing of trade certificates, "
                "COOs, and attestation documents using AI. Must handle Arabic and "
                "English documents with 99%+ accuracy."
            ),
            "requesting_entity": "Dubai Chambers",
            "sector": "FinTech & Financial Services",
            "technology_domain": "Document AI",
            "urgency": "critical",
            "status": "evaluating",
            "source_channel": "business_in_dubai",
            "created_by": staff_user["id"],
        },
    ]

    created_cases = []
    for case_data in cases_data:
        result = supabase.table("chamber_sourcing_cases").insert(case_data).execute()
        if result.data:
            c = result.data[0]
            created_cases.append(c)
            log(f"Created sourcing case: {c['id'][:8]}... — {c['title']}")
        else:
            fatal(f"Failed to create sourcing case: {case_data['title']}")

    return created_cases


def link_proposals_to_cases(cases, proposals, unlinked):
    """Link 2 existing proposals to the sourcing cases (Gap 3)."""
    print("\n=== Step 2: Linking proposals to sourcing cases (Gap 3) ===")

    used_ids = set()
    linked = []

    for case in cases:
        proposal = find_best_proposal(
            unlinked if unlinked else proposals,
            preferred_sector=case.get("sector"),
            exclude_ids=used_ids,
        )
        if not proposal:
            fatal("Could not find enough proposals to link to sourcing cases.")

        result = (
            supabase.table("chamber_proposals")
            .update({"sourcing_case_id": case["id"]})
            .eq("id", proposal["id"])
            .execute()
        )
        if result.data:
            p = result.data[0]
            used_ids.add(proposal["id"])
            linked.append(p)
            log(
                f"Linked proposal {proposal['id'][:8]}... "
                f"('{proposal['title'][:40]}...') "
                f"→ case {case['id'][:8]}... ('{case['title'][:40]}...')"
            )
        else:
            fatal(f"Failed to link proposal {proposal['id']} to case {case['id']}")

    return linked


def seed_pilot(linked_proposals, staff_user):
    """Insert 1 pilot (Gap 4)."""
    print("\n=== Step 3: Creating 1 Pilot (Gap 4) ===")

    proposal = linked_proposals[0]  # Use the first linked proposal
    pilot_data = {
        "proposal_id": proposal["id"],
        "title": f"{DEMO_TAG} Smart Building IoT Security - Phase 1 Pilot",
        "status": "active",
        "start_date": "2026-03-01",
        "end_date": "2026-06-30",
        "success_criteria": "Successfully monitor 5 buildings with <1% false positive rate",
        "budget_allocated": 150000,
        "created_by": staff_user["id"],
    }

    # If proposal has a submitter_id, use it as vendor_id
    if proposal.get("submitter_id"):
        pilot_data["vendor_id"] = proposal["submitter_id"]

    result = supabase.table("chamber_pilots").insert(pilot_data).execute()
    if result.data:
        p = result.data[0]
        log(f"Created pilot: {p['id'][:8]}... — {p['title']}")
        return p
    else:
        fatal("Failed to create pilot")


def seed_alerts(linked_proposals):
    """Insert 2 test alerts (Gap 22)."""
    print("\n=== Step 4: Creating 2 Alerts (Gap 22) ===")

    # Use first linked proposal ID in alert description for realism
    proposal_ref = linked_proposals[0]["id"][:8] if linked_proposals else "XYZ"

    alerts_data = [
        {
            "alert_type": "ai_anomaly",
            "severity": "medium",
            "title": f"{DEMO_TAG} Low grounding score detected",
            "description": (
                f"Evaluation for proposal {proposal_ref}... returned 28% grounding "
                "score — below the 60% threshold. Manual review recommended."
            ),
        },
        {
            "alert_type": "compliance",
            "severity": "high",
            "title": f"{DEMO_TAG} High-severity incident reported",
            "description": (
                "Unauthorized API access attempt detected from IP 203.0.113.42. "
                "Rate-limit policy triggered. Vendor API key temporarily suspended."
            ),
        },
    ]

    created_alerts = []
    for alert_data in alerts_data:
        result = supabase.table("chamber_alerts").insert(alert_data).execute()
        if result.data:
            a = result.data[0]
            created_alerts.append(a)
            log(f"Created alert: {a['id'][:8]}... — [{a['severity']}] {a['title']}")
        else:
            fatal(f"Failed to create alert: {alert_data['title']}")

    return created_alerts


def seed_sector_assignment(staff_user):
    """Insert 1 sector assignment (Gap 30)."""
    print("\n=== Step 5: Creating 1 Sector Assignment (Gap 30) ===")

    assignment_data = {
        "sector": "Cybersecurity & Digital Trust",
        "assigned_user_id": staff_user["id"],
    }

    # Check if assignment already exists for this sector
    existing = (
        supabase.table("chamber_sector_assignments")
        .select("id")
        .eq("sector", "Cybersecurity & Digital Trust")
        .execute()
    )
    if existing.data:
        log(f"Sector assignment already exists for 'Cybersecurity & Digital Trust' — updating")
        result = (
            supabase.table("chamber_sector_assignments")
            .update({"assigned_user_id": staff_user["id"]})
            .eq("id", existing.data[0]["id"])
            .execute()
        )
    else:
        result = supabase.table("chamber_sector_assignments").insert(assignment_data).execute()

    if result.data:
        s = result.data[0]
        log(f"Sector assignment: {s['id'][:8]}... — '{s['sector']}' → user {staff_user['id'][:8]}...")
        return s
    else:
        fatal("Failed to create sector assignment")


def print_summary(cases, linked, pilot, alerts, assignment):
    """Print a summary of all seeded data."""
    print("\n" + "=" * 60)
    print("  E2E TEST DATA SEEDED SUCCESSFULLY")
    print("=" * 60)
    print(f"\n  Sourcing Cases:     {len(cases)} created")
    for c in cases:
        print(f"    • {c['id']} — {c['title']}")
    print(f"\n  Proposals Linked:   {len(linked)}")
    for p in linked:
        print(f"    • {p['id']} → case {p.get('sourcing_case_id', '?')}")
    print(f"\n  Pilots:             1 created")
    print(f"    • {pilot['id']} — {pilot['title']}")
    print(f"\n  Alerts:             {len(alerts)} created")
    for a in alerts:
        print(f"    • {a['id']} — [{a['severity']}] {a['title']}")
    print(f"\n  Sector Assignments: 1 created/updated")
    print(f"    • {assignment['id']} — {assignment['sector']}")
    print(f"\n  All demo data is tagged with '{DEMO_TAG}' for easy identification.")
    print("=" * 60)


def main():
    print("=" * 60)
    print("  Dubai Chambers — E2E Test Data Seeder")
    print("  All records tagged with [DEMO] for identification")
    print("=" * 60)

    # 0. Query existing data
    staff_user, vendors, proposals, unlinked = query_existing_data()

    # 1. Create 2 sourcing cases
    cases = seed_sourcing_cases(staff_user=staff_user)

    # 2. Link 2 existing proposals to the cases
    linked = link_proposals_to_cases(
        cases=cases,
        proposals=proposals,
        unlinked=unlinked,
    )

    # 3. Create 1 pilot
    pilot = seed_pilot(linked_proposals=linked, staff_user=staff_user)

    # 4. Create 2 alerts
    alerts = seed_alerts(linked_proposals=linked)

    # 5. Create 1 sector assignment
    assignment = seed_sector_assignment(staff_user=staff_user)

    # Summary
    print_summary(cases, linked, pilot, alerts, assignment)


if __name__ == "__main__":
    main()

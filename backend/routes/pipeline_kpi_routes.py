"""Pipeline KPI Dashboard — operational performance metrics for the sourcing workflow."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from auth import get_current_user
from database import supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard Pipeline KPIs"])

ALLOWED_ROLES = {"admin", "analyst", "executive"}


@router.get(
    "/pipeline-kpis",
    status_code=status.HTTP_200_OK,
    summary="Get pipeline operational KPIs",
)
async def get_pipeline_kpis(
    current_user: dict = Depends(get_current_user),
):
    """Returns operational KPIs for the innovation sourcing pipeline."""
    user_role = current_user.get("role", "vendor")
    if user_role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Forbidden",
                "detail": "Admin, analyst, or executive role required",
                "code": 403,
            },
        )

    try:
        # Fetch data from all relevant tables in sequence
        proposals_result = supabase.table("chamber_proposals").select(
            "id, status, submission_date, created_at"
        ).execute()
        proposals = proposals_result.data or []
        total_proposals = len(proposals)

        evaluations_result = supabase.table("chamber_evaluations").select(
            "id, proposal_id, evaluated_at, created_at"
        ).execute()
        evaluations = evaluations_result.data or []
        total_evaluations = len(evaluations)

        audits_result = supabase.table("chamber_compliance_audits").select(
            "id, isr_v3_compliance, ai_security_policy_compliance, csp_standards_compliance, data_residency_verified"
        ).execute()
        audits = audits_result.data or []
        total_audits = len(audits)

        vendors_result = supabase.table("chamber_vendors").select(
            "id, is_desc_approved"
        ).execute()
        vendors = vendors_result.data or []
        total_vendors = len(vendors)

        ai_result = supabase.table("chamber_ai_interactions").select(
            "id, cost_usd"
        ).execute()
        ai_interactions = ai_result.data or []

        # ── KPI 1: Median Time to First Decision ────────────────────
        proposal_dates = {
            p["id"]: p.get("submission_date") or p.get("created_at")
            for p in proposals
        }
        first_eval_per_proposal = {}
        for ev in evaluations:
            pid = ev.get("proposal_id")
            ev_date = ev.get("evaluated_at") or ev.get("created_at")
            if pid and ev_date:
                if pid not in first_eval_per_proposal or ev_date < first_eval_per_proposal[pid]:
                    first_eval_per_proposal[pid] = ev_date

        decision_deltas = []
        for pid, eval_date_str in first_eval_per_proposal.items():
            sub_date_str = proposal_dates.get(pid)
            if sub_date_str and eval_date_str:
                try:
                    sub_dt = datetime.fromisoformat(sub_date_str.replace("Z", "+00:00"))
                    eval_dt = datetime.fromisoformat(eval_date_str.replace("Z", "+00:00"))
                    delta_hours = (eval_dt - sub_dt).total_seconds() / 3600
                    if delta_hours >= 0:
                        decision_deltas.append(delta_hours)
                except (ValueError, TypeError):
                    continue

        decision_deltas.sort()
        if decision_deltas:
            n = len(decision_deltas)
            median_hours = (
                decision_deltas[n // 2]
                if n % 2 == 1
                else (decision_deltas[n // 2 - 1] + decision_deltas[n // 2]) / 2
            )
        else:
            median_hours = None

        if median_hours is not None:
            median_display = (
                f"{median_hours / 24:.1f} days"
                if median_hours >= 48
                else f"{median_hours:.1f} hours"
            )
        else:
            median_display = "No data"

        # ── KPI 2: Auto-Classification Accuracy ─────────────────────
        if total_proposals > 0:
            accurate_count = sum(
                1 for p in proposals if p.get("status") != "needs_improvement"
            )
            accuracy_pct = round((accurate_count / total_proposals) * 100, 1)
            accuracy_display = f"{accuracy_pct}%"
        else:
            accuracy_pct = None
            accuracy_display = "No data"

        # ── KPI 3: Compliance First-Pass Rate ────────────────────────
        if total_audits > 0:
            pass_count = 0
            for a in audits:
                score = sum([
                    bool(a.get("isr_v3_compliance")),
                    bool(a.get("ai_security_policy_compliance")),
                    bool(a.get("csp_standards_compliance")),
                    bool(a.get("data_residency_verified")),
                ]) * 25
                if score >= 80:
                    pass_count += 1
            first_pass_pct = round((pass_count / total_audits) * 100, 1)
            first_pass_display = f"{first_pass_pct}% pass on first review"
        else:
            first_pass_pct = None
            first_pass_display = "No audits yet"

        # ── KPI 4: Shortlist Conversion Rate ─────────────────────────
        shortlisted_count = sum(
            1 for p in proposals if p.get("status") == "shortlisted"
        )
        if total_proposals > 0:
            conversion_pct = round(
                (shortlisted_count / total_proposals) * 100, 1
            )
            conversion_display = (
                f"{shortlisted_count} of {total_proposals} proposals "
                f"shortlisted ({conversion_pct}%)"
            )
        else:
            conversion_pct = None
            conversion_display = "No proposals yet"

        # ── KPI 5: DESC Vendor Coverage ──────────────────────────────
        desc_approved = sum(1 for v in vendors if v.get("is_desc_approved"))
        if total_vendors > 0:
            desc_pct = round((desc_approved / total_vendors) * 100, 1)
            desc_display = (
                f"{desc_approved} of {total_vendors} vendors "
                f"DESC certified ({desc_pct}%)"
            )
        else:
            desc_pct = None
            desc_display = "No vendors yet"

        # ── KPI 6: AI Cost Per Decision ──────────────────────────────
        total_ai_cost = sum(
            float(i.get("cost_usd", 0) or 0) for i in ai_interactions
        )
        if total_evaluations > 0:
            cost_per_decision = round(total_ai_cost / total_evaluations, 2)
            cost_display = f"${cost_per_decision:.2f} per evaluation"
        else:
            cost_per_decision = None
            cost_display = "No evaluations yet"

        # ── KPI 7: Pipeline Throughput ───────────────────────────────
        throughput = None
        throughput_display = "No proposals yet"
        if total_proposals > 0:
            valid_dates = []
            for p in proposals:
                ds = p.get("submission_date") or p.get("created_at")
                if ds:
                    try:
                        valid_dates.append(
                            datetime.fromisoformat(ds.replace("Z", "+00:00"))
                        )
                    except (ValueError, TypeError):
                        continue
            if valid_dates:
                earliest = min(valid_dates)
                days_since = max(
                    (datetime.now(timezone.utc) - earliest).days, 1
                )
                throughput = round(total_proposals / days_since, 2)
                throughput_display = f"{throughput} proposals/day"

        return {
            "kpis": [
                {
                    "id": "median_decision_time",
                    "name": "Median Time to First Decision",
                    "value": round(median_hours, 1) if median_hours is not None else None,
                    "unit": "hours",
                    "display": median_display,
                    "benchmark": "Industry avg: 48hrs",
                },
                {
                    "id": "auto_classification_accuracy",
                    "name": "Auto-Classification Accuracy",
                    "value": accuracy_pct,
                    "unit": "percent",
                    "display": accuracy_display,
                    "benchmark": "Target: 95%",
                },
                {
                    "id": "compliance_first_pass",
                    "name": "Compliance First-Pass Rate",
                    "value": first_pass_pct,
                    "unit": "percent",
                    "display": first_pass_display,
                    "benchmark": "Target: 80%",
                },
                {
                    "id": "shortlist_conversion",
                    "name": "Shortlist Conversion Rate",
                    "value": conversion_pct,
                    "unit": "percent",
                    "display": conversion_display,
                    "benchmark": "Typical: 15-25%",
                },
                {
                    "id": "desc_vendor_coverage",
                    "name": "DESC Vendor Coverage",
                    "value": desc_pct,
                    "unit": "percent",
                    "display": desc_display,
                    "benchmark": "Target: 100%",
                },
                {
                    "id": "ai_cost_per_decision",
                    "name": "AI Cost Per Decision",
                    "value": cost_per_decision,
                    "unit": "usd",
                    "display": cost_display,
                    "benchmark": "Manual avg: $150",
                },
                {
                    "id": "pipeline_throughput",
                    "name": "Pipeline Throughput",
                    "value": throughput,
                    "unit": "proposals_per_day",
                    "display": throughput_display,
                    "benchmark": "Target: 5/day",
                },
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating pipeline KPIs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "detail": str(e), "code": 500},
        )

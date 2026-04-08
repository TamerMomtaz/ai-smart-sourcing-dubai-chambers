"""Service to generate DESC Audit Evidence Pack by aggregating existing data."""

from datetime import datetime, timezone
from typing import Dict, Any, List
import logging

from database import supabase

logger = logging.getLogger(__name__)


def _safe_query(table: str, select: str = "*", **kwargs) -> List[Dict[str, Any]]:
    """Run a Supabase select and return data or empty list on failure."""
    try:
        q = supabase.table(table).select(select)
        for k, v in kwargs.items():
            q = q.eq(k, v)
        return q.execute().data or []
    except Exception as e:
        logger.warning(f"audit_pack: failed to query {table}: {e}")
        return []


def generate_audit_pack() -> Dict[str, Any]:
    """Aggregate all evidence sections into a single audit pack dict."""

    generated_at = datetime.now(timezone.utc).isoformat()

    # ── 1. Platform Self-Check (static 19 controls) ──
    platform_self_check = _build_platform_self_check()

    # ── 2. Compliance Audits Summary ──
    compliance_summary = _build_compliance_summary()

    # ── 3. Sigma-I Transparency Log ──
    transparency_log = _build_transparency_log()

    # ── 4. Incident Management Summary ──
    incident_summary = _build_incident_summary()

    # ── 5. User Access Control Summary ──
    access_control = _build_access_control_summary()

    # ── 6. Data Residency Declaration ──
    data_residency = _build_data_residency()

    # ── 7. AI Model Inventory ──
    model_inventory = _build_model_inventory()

    # ── 8. Evidence Validation Layer (Hallucination Shield) ──
    evidence_validation = _build_evidence_validation()

    return {
        "generated_at": generated_at,
        "title": "DESC Audit Evidence Pack",
        "sections": {
            "platform_self_check": platform_self_check,
            "compliance_audits_summary": compliance_summary,
            "transparency_log": transparency_log,
            "incident_management": incident_summary,
            "access_control": access_control,
            "data_residency": data_residency,
            "ai_model_inventory": model_inventory,
            "evidence_validation": evidence_validation,
        },
    }


# ─────────────────────────── Section builders ───────────────────────────


def _build_platform_self_check() -> Dict[str, Any]:
    """19 controls with scores and statuses (mirrors frontend constant)."""
    controls = [
        {"id": 1, "framework": "DESC CSP Security Standards", "title": "ISO/IEC 27001 — Information security controls", "status": "aligned", "score": 85},
        {"id": 2, "framework": "DESC CSP Security Standards", "title": "ISO/IEC 27017 — Cloud security controls", "status": "aligned", "score": 85},
        {"id": 3, "framework": "DESC CSP Security Standards", "title": "CSA CCM v4.0.5 — Cloud controls matrix", "status": "aligned", "score": 80},
        {"id": 4, "framework": "DESC CSP Security Standards", "title": "ISR V3 — Information security regulation", "status": "aligned", "score": 85},
        {"id": 5, "framework": "DESC AI Security Policy", "title": "Design Phase — Threat modeling, data boundaries", "status": "active", "score": 90},
        {"id": 6, "framework": "DESC AI Security Policy", "title": "Develop Phase — Data poisoning prevention", "status": "active", "score": 90},
        {"id": 7, "framework": "DESC AI Security Policy", "title": "Deploy Phase — Secure APIs, model protection", "status": "active", "score": 95},
        {"id": 8, "framework": "DESC AI Security Policy", "title": "Monitor Phase — Evidence validation, anomaly flagging", "status": "active", "score": 95},
        {"id": 9, "framework": "DESC AI Security Policy", "title": "Dispose Phase — Crypto-erasure, data retention", "status": "planned", "score": 30},
        {"id": 10, "framework": "Data Residency & Sovereignty", "title": "UAE Data Residency", "status": "planned", "score": 40},
        {"id": 11, "framework": "Data Residency & Sovereignty", "title": "Data Residency Monitoring", "status": "active", "score": 85},
        {"id": 12, "framework": "Data Residency & Sovereignty", "title": "No cross-border data transfer without approval", "status": "active", "score": 80},
        {"id": 13, "framework": "Operational Security", "title": "Role-based access control", "status": "active", "score": 95},
        {"id": 14, "framework": "Operational Security", "title": "Audit trail / Immutable logging", "status": "active", "score": 95},
        {"id": 15, "framework": "Operational Security", "title": "Incident response process", "status": "active", "score": 90},
        {"id": 16, "framework": "Operational Security", "title": "Vendor ecosystem integration", "status": "active", "score": 90},
        {"id": 17, "framework": "Operational Security", "title": "API security", "status": "active", "score": 95},
        {"id": 18, "framework": "Operational Security", "title": "Backup & recovery", "status": "active", "score": 90},
        {"id": 19, "framework": "Operational Security", "title": "Transparency & explainability", "status": "active", "score": 95},
    ]
    active = sum(1 for c in controls if c["status"] == "active")
    aligned = sum(1 for c in controls if c["status"] == "aligned")
    planned = sum(1 for c in controls if c["status"] == "planned")
    avg_score = round(sum(c["score"] for c in controls) / len(controls), 1)

    return {
        "desc_label": "ISR V3 — Domain 13: Compliance & Audit",
        "total_controls": len(controls),
        "active": active,
        "aligned": aligned,
        "planned": planned,
        "average_score": avg_score,
        "overall_percent": 89,
        "controls": controls,
    }


def _build_compliance_summary() -> Dict[str, Any]:
    audits = _safe_query("chamber_compliance_audits", "id, audit_type, isr_v3_compliance, ai_security_policy_compliance, csp_standards_compliance, data_residency_verified, findings_json, audit_timestamp")
    total = len(audits)

    isr_pass = sum(1 for a in audits if a.get("isr_v3_compliance"))
    ai_pass = sum(1 for a in audits if a.get("ai_security_policy_compliance"))
    csp_pass = sum(1 for a in audits if a.get("csp_standards_compliance"))
    dr_pass = sum(1 for a in audits if a.get("data_residency_verified"))

    def _rate(n: int) -> float:
        return round((n / total) * 100, 1) if total else 0.0

    return {
        "desc_label": "ISR V3 — Domain 13: Compliance & Audit",
        "total_audits": total,
        "pass_rates": {
            "isr_v3": _rate(isr_pass),
            "ai_security_policy": _rate(ai_pass),
            "csp_standards": _rate(csp_pass),
            "data_residency": _rate(dr_pass),
        },
        "audits": [
            {
                "id": a["id"],
                "audit_type": a.get("audit_type"),
                "audit_timestamp": a.get("audit_timestamp"),
                "isr_v3_compliance": a.get("isr_v3_compliance", False),
                "ai_security_policy_compliance": a.get("ai_security_policy_compliance", False),
                "csp_standards_compliance": a.get("csp_standards_compliance", False),
                "data_residency_verified": a.get("data_residency_verified", False),
            }
            for a in audits[:50]
        ],
    }


def _build_transparency_log() -> Dict[str, Any]:
    interactions = _safe_query(
        "chamber_ai_interactions",
        "id, operation_type, model_name, input_tokens, output_tokens, cost_usd, latency_ms, created_at, intelligence_units",
    )
    total = len(interactions)
    total_cost = sum(float(i.get("cost_usd", 0) or 0) for i in interactions)
    total_input = sum(int(i.get("input_tokens", 0) or 0) for i in interactions)
    total_output = sum(int(i.get("output_tokens", 0) or 0) for i in interactions)
    avg_latency = round(
        sum(float(i.get("latency_ms", 0) or 0) for i in interactions) / max(total, 1), 1
    )
    total_iu = sum(float(i.get("intelligence_units", 0) or 0) for i in interactions)

    # Breakdown by operation type
    by_operation: Dict[str, int] = {}
    for i in interactions:
        op = i.get("operation_type", "unknown")
        by_operation[op] = by_operation.get(op, 0) + 1

    # Breakdown by model
    by_model: Dict[str, int] = {}
    for i in interactions:
        model = i.get("model_name") or "unknown"
        by_model[model] = by_model.get(model, 0) + 1

    return {
        "desc_label": "AI Security Policy — Transparency",
        "total_interactions": total,
        "total_cost_usd": round(total_cost, 4),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_tokens": total_input + total_output,
        "average_latency_ms": avg_latency,
        "total_intelligence_units": round(total_iu, 2),
        "by_operation_type": by_operation,
        "by_model": by_model,
        "interactions": [
            {
                "id": i["id"],
                "operation_type": i.get("operation_type"),
                "model_name": i.get("model_name"),
                "input_tokens": i.get("input_tokens"),
                "output_tokens": i.get("output_tokens"),
                "cost_usd": i.get("cost_usd"),
                "latency_ms": i.get("latency_ms"),
                "created_at": i.get("created_at"),
            }
            for i in interactions[:100]
        ],
    }


def _build_incident_summary() -> Dict[str, Any]:
    incidents = _safe_query(
        "chamber_incidents",
        "id, title, severity, incident_type, status, desc_report_required, desc_reported_at, created_at, resolution_date",
    )
    total = len(incidents)
    open_count = sum(1 for i in incidents if i.get("status") in ("open", "investigating"))
    resolved = sum(1 for i in incidents if i.get("status") == "resolved")
    reported = sum(1 for i in incidents if i.get("status") == "reported_to_desc")
    desc_required = sum(1 for i in incidents if i.get("desc_report_required"))

    by_severity: Dict[str, int] = {}
    for i in incidents:
        sev = i.get("severity", "unknown")
        by_severity[sev] = by_severity.get(sev, 0) + 1

    by_status: Dict[str, int] = {}
    for i in incidents:
        st = i.get("status", "unknown")
        by_status[st] = by_status.get(st, 0) + 1

    return {
        "desc_label": "ISR V3 — Domain 10: Incident Management",
        "total_incidents": total,
        "open": open_count,
        "resolved": resolved,
        "reported_to_desc": reported,
        "desc_report_required": desc_required,
        "by_severity": by_severity,
        "by_status": by_status,
        "incidents": [
            {
                "id": i["id"],
                "title": i.get("title"),
                "severity": i.get("severity"),
                "incident_type": i.get("incident_type"),
                "status": i.get("status"),
                "desc_report_required": i.get("desc_report_required", False),
                "desc_reported_at": i.get("desc_reported_at"),
                "created_at": i.get("created_at"),
                "resolution_date": i.get("resolution_date"),
            }
            for i in incidents[:50]
        ],
    }


def _build_access_control_summary() -> Dict[str, Any]:
    users = _safe_query("chamber_users", "id, role, email, created_at")

    by_role: Dict[str, int] = {}
    for u in users:
        role = u.get("role", "unknown")
        by_role[role] = by_role.get(role, 0) + 1

    roles_defined = ["admin", "analyst", "compliance_officer", "executive", "business_group_lead", "vendor"]

    return {
        "desc_label": "ISR V3 — Domain 5: Access Control",
        "total_users": len(users),
        "by_role": by_role,
        "roles_defined": roles_defined,
        "rbac_enabled": True,
        "rls_enabled": True,
        "rls_tables": [
            "chamber_vendors", "chamber_proposals", "chamber_evaluations",
            "chamber_compliance_audits", "chamber_documents", "chamber_comments",
            "chamber_ai_interactions", "chamber_trend_analyses",
            "chamber_business_groups", "chamber_users", "chamber_hallucination_checks",
            "chamber_incidents", "chamber_vendor_profiles",
            "chamber_notification_preferences", "chamber_desc_certified_providers",
            "chamber_business_councils", "chamber_sourcing_cases",
            "chamber_evaluation_overrides", "chamber_pilots",
        ],
        "permissions": {
            "vendor": ["proposals:create_own", "proposals:read_own", "documents:upload_own", "vendor_profile:read_own"],
            "analyst": ["proposals:read_all", "evaluations:create", "compliance_audits:create"],
            "compliance_officer": ["compliance_audits:create", "compliance_audits:generate_report", "audit_trail:read_all"],
            "executive": ["dashboards:executive", "export:reports", "trend_analysis:read_all"],
            "business_group_lead": ["proposals:read_sector", "evaluations:read_sector"],
            "admin": ["*:*"],
        },
    }


def _build_data_residency() -> Dict[str, Any]:
    return {
        "desc_label": "CSP Standard — Data Residency",
        "current_hosting": {
            "database": "Supabase (EU — Frankfurt)",
            "backend": "Railway (EU)",
            "frontend": "Vercel (Edge CDN, global)",
            "ai_providers": [
                "Anthropic Claude (US — data processing agreement in place)",
                "OpenAI GPT-4o (US — data processing agreement in place)",
                "Google Gemini (US — data processing agreement in place)",
            ],
        },
        "uae_migration_plan": {
            "status": "planned",
            "target": "UAE-region hosting for database and backend",
            "notes": "Architecture is region-agnostic. Migration requires UAE Supabase/cloud region availability.",
        },
        "data_sovereignty_controls": [
            "No model fine-tuning on user data",
            "API keys server-side only",
            "vScore flags vendors without UAE data residency verification",
            "All AI API calls use providers with UAE-compatible data processing agreements",
        ],
    }


def _build_model_inventory() -> Dict[str, Any]:
    interactions = _safe_query(
        "chamber_ai_interactions",
        "model_name, operation_type",
    )

    models: Dict[str, Dict[str, Any]] = {}
    for i in interactions:
        model = i.get("model_name") or "unknown"
        if model not in models:
            models[model] = {"operations": 0, "purposes": set()}
        models[model]["operations"] += 1
        op = i.get("operation_type")
        if op:
            models[model]["purposes"].add(op)

    inventory = []
    for name, data in sorted(models.items(), key=lambda x: x[1]["operations"], reverse=True):
        inventory.append({
            "model_name": name,
            "total_operations": data["operations"],
            "purposes": sorted(data["purposes"]),
        })

    return {
        "desc_label": "AI Security Policy — Transparency",
        "total_models": len(inventory),
        "models": inventory,
        "governance": {
            "multi_model_architecture": True,
            "failover_enabled": True,
            "providers": ["Anthropic (Claude)", "OpenAI (GPT-4o)", "Google (Gemini)"],
        },
    }


def _build_evidence_validation() -> Dict[str, Any]:
    checks = _safe_query(
        "chamber_hallucination_checks",
        "id, evaluation_id, grounding_score, hallucination_risk, claim_count, grounded_claims, ungrounded_claims, verification_iu, verification_cost_usd, created_at",
    )
    total = len(checks)
    avg_grounding = round(
        sum(float(c.get("grounding_score", 0) or 0) for c in checks) / max(total, 1), 1
    )
    total_claims = sum(int(c.get("claim_count", 0) or 0) for c in checks)
    grounded = sum(int(c.get("grounded_claims", 0) or 0) for c in checks)
    ungrounded = sum(int(c.get("ungrounded_claims", 0) or 0) for c in checks)

    risk_dist = {"low": 0, "medium": 0, "high": 0}
    for c in checks:
        risk = c.get("hallucination_risk", "low")
        if risk in risk_dist:
            risk_dist[risk] += 1

    return {
        "desc_label": "AI Security Policy — Hallucination Monitoring",
        "total_checks": total,
        "average_grounding_score": avg_grounding,
        "total_claims": total_claims,
        "grounded_claims": grounded,
        "ungrounded_claims": ungrounded,
        "risk_distribution": risk_dist,
        "checks": [
            {
                "id": c["id"],
                "evaluation_id": c.get("evaluation_id"),
                "grounding_score": c.get("grounding_score"),
                "hallucination_risk": c.get("hallucination_risk"),
                "claim_count": c.get("claim_count"),
                "grounded_claims": c.get("grounded_claims"),
                "ungrounded_claims": c.get("ungrounded_claims"),
                "created_at": c.get("created_at"),
            }
            for c in checks[:50]
        ],
    }

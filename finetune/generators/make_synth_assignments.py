"""Build deterministic synthesis assignments: 24 families x 35 cells = 840.

Each family is capped at 35 pairs (4.17% of 840, under the 5% rule).  Cells vary
structurally (axes) AND across a broad real-entity vocabulary; generic-utility
families vary structurally only (no entity field use).  Fixed seed -> identical
assignments every run.  One assignment file per family for a focused subagent.
"""
import json
import os

# NOTE: data tables (ENTITIES, FAMILIES, A) and pick() are module-level so this
# module can be imported (e.g. by make_synth_topup) WITHOUT side effects.  The
# assignment-file generation runs only under __main__.

# Real domain entities with REAL columns (harvested from the repo's models/SQL).
ENTITIES = [
    ("vendor", "Vendor", "chamber_vendors", ["name", "contact_email", "sector", "trade_license_status", "vscore", "country"]),
    ("proposal", "Proposal", "chamber_proposals", ["title", "status", "sector", "technology_type", "composite_score", "submitter_id", "sourcing_case_id"]),
    ("sourcing_case", "SourcingCase", "chamber_sourcing_cases", ["title", "problem_statement", "sector", "compliance_tier", "status", "urgency"]),
    ("vendor_match", "VendorMatch", "chamber_vendor_matches", ["sourcing_case_id", "vendor_id", "match_score", "match_reasoning", "status"]),
    ("evaluation", "Evaluation", "chamber_evaluations", ["proposal_id", "relevance_score", "feasibility_score", "compliance_score", "novelty_score", "composite_score"]),
    ("evaluation_override", "EvaluationOverride", "chamber_evaluation_overrides", ["evaluation_id", "dimension", "human_adjusted_score", "override_reason", "overridden_by"]),
    ("compliance_audit", "ComplianceAudit", "chamber_compliance_audits", ["proposal_id", "findings", "status", "report_url", "auditor_id"]),
    ("gate_decision", "GateDecision", "chamber_gate_decisions", ["proposal_id", "stage", "decision", "decided_by", "rationale"]),
    ("document", "Document", "chamber_documents", ["proposal_id", "filename", "storage_path", "sanitized", "content_type"]),
    ("alert", "Alert", "chamber_alerts", ["title", "severity", "status", "sector", "source"]),
    ("incident", "Incident", "chamber_incidents", ["title", "severity", "status", "resolved_at", "owner_id"]),
    ("pilot", "Pilot", "chamber_pilots", ["proposal_id", "vendor_id", "status", "success_criteria", "budget_allocated"]),
    ("sector_assignment", "SectorAssignment", "chamber_sector_assignments", ["sector", "analyst_id", "active"]),
    ("business_group", "BusinessGroup", "chamber_business_groups", ["name", "lead_id", "config"]),
    ("ai_interaction", "AIInteraction", "chamber_ai_interactions", ["operation_type", "model", "tokens_used", "integrity_hash", "previous_hash"]),
    ("factsheet", "Factsheet", "chamber_vendor_factsheets", ["vendor_id", "summary", "generated_at"]),
    ("trend_analysis", "TrendAnalysis", "chamber_trend_analyses", ["sector", "period", "metrics", "summary"]),
    ("comment", "Comment", "chamber_comments", ["entity_id", "body", "author_id", "created_at"]),
    ("desc_provider", "DescProvider", "chamber_desc_certified_providers", ["name", "cert_status", "expiry_date"]),
    ("audit_pack", "AuditPack", "chamber_audit_packs", ["scope", "generated_at", "checksum"]),
    ("channel_analytic", "ChannelAnalytic", "chamber_channel_analytics", ["channel", "volume", "conversion_rate"]),
    ("compliance_knowledge", "ComplianceKnowledge", "chamber_compliance_knowledge", ["topic", "content", "embedding", "source"]),
    ("sourcing_intake", "SourcingIntake", "chamber_sourcing_intake", ["source_channel", "raw_text", "processed", "case_id"]),
    ("notification_pref", "NotificationPref", "chamber_notification_preferences", ["user_id", "channel", "enabled"]),
    ("trade_license", "TradeLicense", "chamber_trade_licenses", ["vendor_id", "license_no", "status", "expiry_date"]),
    ("pipeline_kpi", "PipelineKpi", "chamber_pipeline_kpis", ["metric", "value", "period"]),
]

# axis option pools
A = {
    "sync": ["async", "sync"],
    "retry": ["exponential backoff with jitter", "fixed-delay retry", "no retry (fail fast)"],
    "idem": ["Idempotency-Key header dedup", "version-based optimistic concurrency", "no idempotency"],
    "valid": ["strict (raise on bad input)", "lenient (coerce + warn)"],
    "ret": ["return a result dataclass", "raise on error"],
    "page": ["keyset/cursor pagination", "offset/limit pagination"],
    "rl": ["token-bucket", "sliding-window-log", "fixed-window-counter", "leaky-bucket"],
    "rls": ["role-scoped RLS via chamber_users.role", "owner-only RLS via auth.uid()"],
    "obs": ["structured JSON logging", "Prometheus-style counters", "audit-row side effect"],
}

# 24 families: key, lang, fence, output_kind, entity_usage, spec, axes(list of axis keys)
FAMILIES = [
    ("async_route", "python", "python", "file", "entity",
     "An async FastAPI route module (APIRouter) with one or two endpoints operating on the entity's chamber_ table. Import get_current_user from auth and the supabase client from database; admin must be allowed; gate by role. Use Pydantic v2 request/response models with Field constraints over the entity's REAL fields. Wrap DB writes per the assigned retry axis; honor the assigned idempotency axis. Return proper status codes and HTTPException.",
     ["sync", "retry", "idem"]),
    ("sync_service_crud", "python", "python", "file", "entity",
     "A sync service module with keyword-only functions (create/get/list/update_status) over the entity's chamber_ table using the supabase client. Build insert/update payloads from the entity's REAL fields; omit optional fields when None. Module-level logging. Honor the assigned validation and return-style axes.",
     ["valid", "ret"]),
    ("service_aggregate", "python", "python", "file", "entity",
     "A sync service that computes an aggregate/report for the entity: fetch rows, join a related table, and derive metrics (counts, averages, grouping) over the entity's REAL numeric/categorical fields. Return a structured summary dict. Honor the assigned return-style axis.",
     ["ret", "valid"]),
    ("pydantic_model", "python", "python", "file", "entity",
     "Pydantic v2 models for the entity: a Create model, an Update (all-optional) model, and a Response model, using Field constraints (min_length/ge/le/pattern) and at least one @field_validator over the entity's REAL fields. Use enums where a field has a known value set. Honor the validation axis (strict vs lenient coercion).",
     ["valid"]),
    ("idempotency", "python", "python", "file", "entity",
     "An idempotency helper for writes to the entity's chamber_ table: compute/lookup an idempotency key, return the prior row on replay, else insert. Honor the assigned idempotency + concurrency axis. Materially use the entity's REAL fields in the payload.",
     ["idem", "sync"]),
    ("pagination", "python", "python", "file", "entity",
     "A pagination utility over the entity's chamber_ table returning a page object (items, next_cursor/offset, has_more). Implement per the assigned pagination axis. Order by the entity's created_at + id (keyset) or use offset/limit. Strict cursor handling.",
     ["page", "sync"]),
    ("rate_limiter", "python", "python", "file", "generic",
     "A GENERIC rate limiter class implementing the assigned algorithm. Pure logic, injected clock, thread-unaware but documented. Do NOT use domain entity fields — vary structurally by algorithm only. Include a small usage docstring referencing throttling outbound AI-provider calls.",
     ["rl", "sync"]),
    ("retry_decorator", "python", "python", "file", "generic",
     "A GENERIC retry/backoff decorator (both a sync and an async variant) honoring the assigned retry axis, max attempts, jitter, and a retryable-exception predicate. Pure utility, no domain entity fields.",
     ["retry", "sync"]),
    ("webhook_ingest", "python", "python", "file", "entity",
     "An inbound webhook/intake FastAPI route for the entity: verify an HMAC signature header (secret read from env), parse + validate the payload into the entity's REAL fields, dedup on an external id, and persist. Honor the assigned validation axis. Never hardcode secrets.",
     ["valid", "idem"]),
    ("background_task", "python", "python", "file", "entity",
     "An async background worker that processes pending rows of the entity's chamber_ table in batches with bounded concurrency (asyncio.Semaphore), per-item error isolation, and graceful cancellation. Honor the assigned retry + observability axes. Use the entity's REAL fields.",
     ["retry", "obs"]),
    ("ai_provider_call", "python", "python", "file", "entity",
     "A service wrapping ai_complete (from services.ai_provider) for an entity task: build a system+user prompt referencing the entity's REAL fields, enforce a timeout, parse JSON defensively, retry per the assigned axis, fall back on failure, and log via ai_interaction_service with a valid operation_type. Never hardcode keys.",
     ["retry", "ret"]),
    ("audit_logger", "python", "python", "file", "entity",
     "A tamper-evident audit logger for the entity: each row stores integrity_hash = sha256(previous_hash + canonical fields). Provide append + verify-chain functions over the entity's REAL fields. Honor the observability axis.",
     ["obs", "sync"]),
    ("rbac_dependency", "python", "python", "file", "entity",
     "A FastAPI dependency factory enforcing role/permission for entity operations (admin ALWAYS allowed), returning the user context or raising 403. Include a permission matrix relevant to the entity. Follow the project's auth rules (supabase.auth.get_user; role from chamber_users).",
     ["valid"]),
    ("table_migration", "sql", "sql", "file", "entity",
     "A Postgres migration creating the entity's chamber_ table with a uuid PK (gen_random_uuid()), FKs to related chamber_ tables, NOT NULL + CHECK constraints over the entity's REAL fields, sensible defaults, created_at/updated_at timestamptz, and an updated_at trigger.",
     ["sync"]),
    ("rls_policy", "sql", "sql", "file", "entity",
     "A Postgres migration enabling Row Level Security on the entity's chamber_ table and creating policies per the assigned RLS axis, plus appropriate GRANTs to authenticated. Use chamber_users.role / auth.uid() in USING clauses.",
     ["rls"]),
    ("index_constraint", "sql", "sql", "file", "entity",
     "A Postgres migration adding indexes (a composite index and a partial index with a WHERE over a status/boolean field) and a CHECK or UNIQUE constraint on the entity's chamber_ table, using the entity's REAL fields. Idempotent (IF NOT EXISTS).",
     ["sync"]),
    ("sql_view", "sql", "sql", "file", "entity",
     "A Postgres analytical VIEW (or MATERIALIZED VIEW) aggregating the entity's chamber_ table — counts/averages grouped by a categorical field — joining one related chamber_ table, using the entity's REAL fields.",
     ["sync"]),
    ("trigger_fn", "sql", "sql", "file", "entity",
     "A Postgres plpgsql trigger function + trigger on the entity's chamber_ table that maintains a derived value or writes an audit row on INSERT/UPDATE, using the entity's REAL fields.",
     ["sync"]),
    ("react_list", "jsx", "jsx", "file", "entity",
     "A React (.jsx) list/table page for the entity using hooks. Fetch from an /api/v1 endpoint with axios, support filtering by a categorical REAL field and the assigned pagination axis, and render loading/empty/error states plus rows showing the entity's REAL fields. Use Tailwind classes. Abort in-flight requests on unmount.",
     ["page", "obs"]),
    ("react_form", "jsx", "jsx", "file", "entity",
     "A React (.jsx) form component to create the entity. Controlled inputs for the entity's REAL fields with client validation, submit via axios, OPTIMISTIC update with rollback on failure per the assigned axis, disabled state while submitting, and friendly error display. Tailwind classes.",
     ["idem", "valid"]),
    ("react_hook", "javascript", "javascript", "file", "entity",
     "A React data hook use<Entity>(params) in a .js file: manages loading/data/error, uses AbortController, exposes refetch, and normalizes errors. Fetches the entity list/detail from /api/v1. No JSX. Honor the assigned pagination axis.",
     ["page", "sync"]),
    ("react_dashboard", "jsx", "jsx", "file", "entity",
     "A React (.jsx) dashboard for the entity using recharts: fetch rows, derive stats from the entity's REAL numeric fields, and render a chart (Bar/Line/Pie) plus KPI cards. Loading/empty/error states. Tailwind classes.",
     ["obs"]),
    ("pytest_service", "python", "python", "file", "entity",
     "A pytest module testing a service function for the entity using a mocked supabase client (monkeypatch/unittest.mock), parametrized cases, and fixtures. Assert the payload uses the entity's REAL fields and that error paths behave per the assigned return-style axis.",
     ["ret", "valid"]),
    ("pytest_logic", "python", "python", "file", "generic",
     "A pytest module for a GENERIC pure-logic utility (a limiter, a cursor codec, or a validation function) with an injected clock and parametrized edge cases. No domain entity fields — vary structurally only.",
     ["rl", "page"]),
]

assert len(FAMILIES) == 24, len(FAMILIES)


def pick(opts, i):
    return opts[i % len(opts)]


ASSIGN_DIR = os.environ.get("ASSIGN_DIR", "")
PER_FAMILY = int(os.environ.get("PER_FAMILY", "35"))
if ASSIGN_DIR:
    os.makedirs(ASSIGN_DIR, exist_ok=True)
total = 0
for fi, (key, lang, fence, kind, usage, spec, axiskeys) in enumerate(FAMILIES):
    cells = []
    for c in range(PER_FAMILY):
        ent = ENTITIES[(c * 7 + fi * 3) % len(ENTITIES)]
        name, Name, table, fields = ent
        axes = {ak: pick(A[ak], c + fi) for ak in axiskeys}
        # target file naming
        if lang == "sql":
            tf = f"database/{name}_{key.split('_')[-1]}_migration.sql" if key != "sql_view" else f"database/{name}_view.sql"
        elif key == "react_list":
            tf = f"frontend/src/pages/{Name}List.jsx"
        elif key == "react_form":
            tf = f"frontend/src/components/{Name}Form.jsx"
        elif key == "react_hook":
            tf = f"frontend/src/hooks/use{Name}.js"
        elif key == "react_dashboard":
            tf = f"frontend/src/pages/{Name}Dashboard.jsx"
        elif key.startswith("pytest"):
            tf = f"backend/tests/test_{name}_{ 'logic' if usage=='generic' else key.split('_')[-1] }.py"
        elif lang == "python" and key in ("rate_limiter", "retry_decorator"):
            tf = f"backend/lib/{key}_{c}.py"
        elif key == "async_route" or key == "webhook_ingest" or key == "rbac_dependency":
            sub = {"async_route": "routes", "webhook_ingest": "routes", "rbac_dependency": "deps"}[key]
            tf = f"backend/{sub}/{name}_{key}.py"
        elif key == "background_task":
            tf = f"backend/workers/{name}_worker.py"
        elif key == "pydantic_model":
            tf = f"backend/models/{name}_models.py"
        else:
            tf = f"backend/services/{name}_{key}.py"
        cells.append({
            "cell_id": f"syn-{fi:02d}-{c:02d}",
            "entity": {"name": name, "Name": Name, "table": table, "fields": fields} if usage == "entity" else None,
            "axes": axes,
            "target_file": tf,
        })
        total += 1
    payload = {
        "family": {"key": key, "lang": lang, "fence": fence, "output_kind": kind,
                   "entity_usage": usage, "spec": spec},
        "cells": cells,
    }
    with open(os.path.join(ASSIGN_DIR, f"assign_{fi:02d}_{key}.json"), "w") as f:
        json.dump(payload, f, indent=1)

print(f"wrote {len(FAMILIES)} family assignment files, {total} cells total into {ASSIGN_DIR}")
print(f"per-family cap: {PER_FAMILY} ({PER_FAMILY/total*100:.2f}% of {total})")

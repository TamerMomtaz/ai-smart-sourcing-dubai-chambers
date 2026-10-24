# Capability Map — AI Smart Sourcing (Dubai Chambers)

Project code: **SSDC** · Distilled 2026-10-24 from the repository on `main` (head `30d1017`, merged PRs up to #162).
Sources are limited to this repository. The git history available in the clone starts at 2026-04-07 (PR #112), so earlier history was not reviewed.

**Method note.** The platform's own marketing pages (`frontend/src/pages/PlatformManual.jsx`, `frontend/src/pages/HowItWorks.jsx`) claim more than the code implements. Every card below was checked against the backend code. Where the claim and the code differ, the card follows the code and records the difference under Constraints or Gap.

---

## 1. Project summary

**AI Smart Sourcing — Dubai Chambers.** A FastAPI + Supabase (Postgres/pgvector) + React/Vite web platform, deployed on Railway and Vercel, that runs an innovation-sourcing pipeline for a chamber of commerce: intake of needs and proposals, AI structuring, vendor matching, rule-based compliance gating, LLM evaluation, stage-gate decisions and pilot tracking.
Its distinctive layer is AI governance: every LLM call is logged with cost, energy and carbon estimates in a SHA-256 hash chain, evaluations are re-checked for grounding against source documents, and uploads are screened for prompt injection, all mapped to Dubai DESC regulatory frameworks, with a bilingual EN/AR (RTL) UI.

---

## 2. Capability cards

### READY

#### SSDC-R01 — Score proposals against a weighted, configurable rubric with per-criterion reasoning
- **What it does:** Reads a proposal and its attached documents and scores it 0–100 on five criteria, each with reasoning, evidence points, risks and a confidence level, plus a composite score and summaries in English and Arabic.
- **Client problem it solves:** Reviewing many proposals by hand is slow and inconsistent between reviewers.
- **Built from:** `EvaluationEngine` (5 dimensions: relevance, feasibility, sector alignment, compliance, novelty; default weights 0.25/0.25/0.15/0.20/0.15); weights can be overridden per business group via `evaluation_weight_config_json`; human override with written reasoning (`evaluation_override_service.py`); flag for manual review in the model output; proposal status reverts on failure.
- **Evidence:** `backend/services/evaluation_engine.py` (SYSTEM_PROMPT, DEFAULT_WEIGHTS, `_evaluate_proposal_inner`); `backend/routes/evaluation_override_routes.py`; `database/evaluation_overrides_migration.sql`.
- **Gap to client-ready:** None for an equivalent use case. The prompt is written for Dubai Chambers and the D33 agenda, so a new client needs the rubric text rewritten (content, 1–3 days).
- **Constraints:** Claude Sonnet 4.5 first, then GPT-4o, then Gemini as **fallbacks** (sequential, not consensus; the manual's "three-model consensus" claim is not implemented). "Evidence" is produced by the model, not linked to document spans. "Novelty" is compared only against other proposals in the same sector on the platform, not against patents or the market (the manual's patent-database claim is not implemented). The LLMs run in the US. No accuracy benchmark exists in the repo.
- **Domain:** Analyze & model
- **Fits client types:** government, accelerators, VCs, corporate innovation and procurement teams, donors and development programs (grant review)
- **Confidence:** high

#### SSDC-R02 — Check AI-generated assessments against the source documents (grounding check)
- **What it does:** After an evaluation, a second AI pass pulls out each claim the evaluation made and labels it grounded, partly grounded or ungrounded against the proposal text and documents. It then gets an independent score from a different provider and reports the gap and a risk level.
- **Client problem it solves:** People can't trust AI scores they can't check, and regulators expect checks against hallucination.
- **Built from:** `HallucinationShield` (claim verification, grounding score, cross-model score with deviation, risk level, token/cost accounting); results stored in `chamber_hallucination_checks`.
- **Evidence:** `backend/services/hallucination_service.py`; `backend/routes/hallucination_routes.py`; `database/hallucination_shield_migration.sql`.
- **Gap to client-ready:** None. Can be pointed at any LLM output plus source text with minor wiring (days).
- **Constraints:** A real cross-model check needs OpenAI or Google keys. With only an Anthropic key the cross-check runs on Claude again. The verifier is itself an LLM. No calibration against human labels.
- **Domain:** Analyze & model
- **Fits client types:** any client using AI for decisions; government, research and advisory firms, financial institutions
- **Confidence:** high

#### SSDC-R03 — Screen uploaded documents for prompt injection and score manipulation before AI reads them
- **What it does:** Extracts plain text from PDF/DOCX (dropping embedded objects) and scans it for instructions aimed at the AI, such as "ignore previous instructions" or "score this 100". Suspicious files are flagged for human review, not rejected.
- **Client problem it solves:** Applicants can hide instructions in documents to game an AI reviewer.
- **Built from:** `INJECTION_PATTERNS` and `SCORE_MANIPULATION_PATTERNS` regex sets, pdfplumber/PyPDF2/python-docx extraction, `sanitize_text`, persisted sanitization results.
- **Evidence:** `backend/services/document_sanitization_service.py`; `database/document_sanitization_migration.sql`.
- **Gap to client-ready:** None as a module.
- **Constraints:** About 15 English-only regex patterns. No Arabic patterns and no detection by a classifier or LLM, so paraphrased or obfuscated attacks get through. No OCR (scanned PDFs yield no text).
- **Domain:** Clean & structure
- **Fits client types:** anyone running LLMs over third-party documents (procurement, grants, admissions, KYC)
- **Confidence:** high (that it exists), medium (how well it protects)

#### SSDC-R04 — Log every AI call with cost, energy, carbon, and a tamper-evident hash chain
- **What it does:** Records each AI operation (model, operation type, tokens, latency, USD cost, kWh, gCO2), chains the records with SHA-256 so later edits can be detected, verifies the chain on demand, and shows per-model inventory and totals.
- **Client problem it solves:** Organisations can't account for what their AI spends, emits or did, or prove that the log wasn't altered.
- **Built from:** `_compute_integrity_hash` / chain walk, `get_retention_info`, model inventory aggregation, Transparency and Model Inventory pages.
- **Evidence:** `backend/services/ai_interaction_service.py`; `backend/routes/transparency_routes.py`; `backend/routes/model_inventory_routes.py`; `frontend/src/pages/AIInteractionsList.jsx`, `ModelInventory.jsx`; `database/add_ai_attribution_column.sql`.
- **Gap to client-ready:** None for logging AI calls made by this platform. Logging an external system's calls is SSDC-L01.
- **Constraints:** Energy and carbon are fixed per-token estimates (≈0.001 kWh per 1k tokens, 300 gCO2/kWh). Cost uses Claude Sonnet prices regardless of the model that served the call. The chain reads the latest hash and then inserts, which is not atomic, so concurrent writes can fork it. The hash covers metadata, not prompt or response content. "7-year retention" is reported as policy metadata. No deletion lock is enforced in code.
- **Domain:** Deliver & control access
- **Fits client types:** government, regulated enterprises, ESG-reporting organisations, any AI buyer facing an AI audit
- **Confidence:** high

#### SSDC-R05 — Turn free-text requests into structured cases, through a UI and an API
- **What it does:** Paste or POST a raw description (such as an email body) and get back a structured case: title, problem statement, sector, technology domain, urgency and compliance tier. An authenticated public API accepts intake from partner channels.
- **Client problem it solves:** Needs arrive as unstructured messages from many channels and get lost or retyped.
- **Built from:** AI Assist endpoint and `AI_STRUCTURE_SYSTEM_PROMPT`; `/public/sourcing-intake` with an `X-Intake-Key` header check and source labels (business_in_dubai, expand_north_star, ignyte, partner_referral, email, api); channel analytics by source.
- **Evidence:** `backend/routes/sourcing_case_routes.py` (POST at line 66); `backend/routes/sourcing_intake_routes.py`; `backend/routes/channel_analytics_routes.py`; `database/sourcing_intake_migration.sql`.
- **Gap to client-ready:** None for API/UI intake. Mailbox ingestion doesn't exist (see Constraints).
- **Constraints:** "Email" is a source label only. No IMAP/SMTP or mail provider integration exists. Single shared intake key. Token counts for this call are estimated from word counts.
- **Domain:** Ingest & extract
- **Fits client types:** chambers, accelerators, government innovation units, corporate procurement, donors (call-for-proposals intake)
- **Confidence:** high

#### SSDC-R06 — Extract structured fields from uploaded proposal documents
- **What it does:** Upload a PDF or DOCX proposal and the AI pre-fills the submission form (title, description, sector, technology, maturity and so on) after the document has been sanitised.
- **Client problem it solves:** Applicants and staff re-key information that is already in the document.
- **Built from:** `EXTRACTION_SYSTEM_PROMPT`, document sanitization (R03), Supabase Storage upload with object cleanup on delete.
- **Evidence:** `backend/routes/proposal_ingest_routes.py`; `backend/services/chamber_document_service.py`; commits `eac9ce2`, `3b85943` (storage cleanup).
- **Gap to client-ready:** None. A new schema needs prompt and field edits (days).
- **Constraints:** Text-layer PDFs and DOCX only, no OCR. Arabic documents work only if the PDF has an extractable text layer, and this hasn't been tested in the repo.
- **Domain:** Ingest & extract
- **Fits client types:** procurement, grants, accelerators, research and advisory firms
- **Confidence:** high

#### SSDC-R07 — Detect duplicate requests across intake channels
- **What it does:** Compares a new case with open cases, weighting problem-statement meaning 50%, sector/technology 30% and requester 20%. Returns similarity scores with reasoning, and can scan all open cases at once.
- **Client problem it solves:** The same need arrives through several channels and gets evaluated twice.
- **Built from:** `check_duplicates`, `scan_all_open_cases`, `DEDUPLICATION_SYSTEM_PROMPT`; logged as `deduplication_check`.
- **Evidence:** `backend/services/case_deduplication_service.py`; `backend/routes/case_deduplication_routes.py`.
- **Gap to client-ready:** None at small scale.
- **Constraints:** The LLM compares cases inside one prompt, without embeddings, so cost and context length limit it to tens to low hundreds of open cases. The embedding-based `duplicate_check_service.py` depends on a `match_*` RPC and on stored embeddings, and neither is created anywhere in the repo.
- **Domain:** Clean & structure
- **Fits client types:** chambers, government service desks, innovation programs, CRM-heavy organisations
- **Confidence:** high (LLM path), low (embedding path)

#### SSDC-R08 — Rank vendors for a requirement and filter them by compliance tier
- **What it does:** Given a need, ranks candidate vendors from the database 0–100 with a reason for each and marks whether each vendor meets the case's compliance tier (open / standard / government / critical; critical requires a verified ISO 27001 flag).
- **Client problem it solves:** Finding qualified suppliers for a specific need is manual and depends on whom the analyst knows.
- **Built from:** `discover_vendors`, `_vendor_meets_tier`, `chamber_vendor_flags` for ISO 27001; match status workflow.
- **Evidence:** `backend/services/vendor_matching_service.py`; `database/vendor_matches_migration.sql`, `compliance_tier_migration.sql`; commit `500e7af`.
- **Gap to client-ready:** None, if the client has a vendor list to load.
- **Constraints:** LLM ranking over a candidate list, not semantic or embedding retrieval (the manual's "semantic matching" claim is not implemented). Quality depends on how complete the vendor profiles are. Several column-name bugs were fixed recently (PRs #153–#155), which suggests this path had little use before.
- **Domain:** Analyze & model
- **Fits client types:** procurement, chambers, accelerators, corporate venturing, real estate developers (contractor shortlisting)
- **Confidence:** medium-high

#### SSDC-R09 — Run deterministic eligibility checks before any AI is used
- **What it does:** Runs five binary rules on each submission (vendor certification, data residency, required certifications by tier, duplicate submission, form completeness) and returns pass or flag at no AI cost. Flagged items go to a person and are not auto-rejected.
- **Client problem it solves:** Ineligible submissions waste reviewer time and AI spend.
- **Built from:** `run_compliance_gate` and the five `_check_*` rules.
- **Evidence:** `backend/services/compliance_gate_service.py`; `database/compliance_gate_migration.sql`; commit `cab7d3a` (an ISO rule queried a column that didn't exist, so the check silently failed until fixed).
- **Gap to client-ready:** None. New rules are small code changes (days).
- **Constraints:** The rules are hardcoded in Python, with no rule editor. The results are only as good as the vendor flags in the database.
- **Domain:** Clean & structure
- **Fits client types:** procurement, grants, government programs, accelerators
- **Confidence:** high

#### SSDC-R10 — Govern a portfolio through stage gates and track pilots to outcome
- **What it does:** Records GO / CONDITIONAL GO / HOLD / RECYCLE / KILL decisions at five gates (discovery → scoping → evaluation → pilot approval → procurement), moves proposals forward and records why. It then tracks approved pilots: dates, success criteria, budget, milestones and outcomes.
- **Client problem it solves:** Innovation and procurement decisions go undocumented, and pilots drift with no measured outcome.
- **Built from:** `gate_decision_service.py` (GATE_ORDER, DECISION_STATUS_MAP), `pilot_service.py`, `PilotTracker.jsx`.
- **Evidence:** `backend/services/gate_decision_service.py`; `backend/services/pilot_service.py`; `database/gate_decisions_migration.sql`, `pilot_migration.sql`.
- **Gap to client-ready:** None for a single decision-maker per gate.
- **Constraints:** There is no multi-stakeholder voting (the manual claims it, the code has none) and no notifications on decisions. The gate names are fixed in code.
- **Domain:** Engage, coach & track
- **Fits client types:** accelerators, corporate innovation, government innovation units, VCs (deal flow), donors (grant tranches)
- **Confidence:** high

#### SSDC-R11 — Compare 2–4 competing proposals side by side, with an AI recommendation
- **What it does:** Puts the scores of several proposals for the same need in one view (rubric scores, gate result, grounding score, vendor trust score) and writes a two-paragraph comparison with a recommendation.
- **Client problem it solves:** Committees struggle to compare finalists consistently.
- **Built from:** `compare-proposals` and `compare-proposals/ai-summary` endpoints; `CaseProposalComparison.jsx`, `ProposalCompare.jsx`.
- **Evidence:** `backend/routes/sourcing_case_routes.py` (lines 293–380).
- **Gap to client-ready:** None.
- **Constraints:** The summary is generated from scores only, not from the proposal texts.
- **Domain:** Generate & publish
- **Fits client types:** procurement committees, investment committees, grant panels
- **Confidence:** high

#### SSDC-R12 — Produce an executive board brief and pipeline KPIs from live data
- **What it does:** Pulls proposals, evaluations, audits, grounding checks, AI costs, trends and cases into a printable executive brief, a set of pipeline KPIs and conversion analytics by intake channel.
- **Client problem it solves:** Leaders have no single view of the pipeline or of what the AI is costing.
- **Built from:** `board_brief_routes.py`, `pipeline_kpi_routes.py`, `channel_analytics_routes.py`, `dashboard_*_routes.py`, `BoardBrief.jsx`, `AnalyticsDashboard.jsx`.
- **Evidence:** the files above; `/api/v1/dashboard/impact` used in `HowItWorks.jsx`.
- **Gap to client-ready:** None for this data model.
- **Constraints:** Each query fetches whole tables with no pagination, which limits scale. PDF output relies on the browser's print function (reportlab is a dependency but is unused).
- **Domain:** Generate & publish
- **Fits client types:** government, chambers, accelerators, donors and development programs
- **Confidence:** high

#### SSDC-R13 — Generate vendor one-pagers and pipeline trend reports
- **What it does:** Writes a vendor factsheet (AI overview, capabilities, compliance status, trust score, engagement history) and an AI trend report on submitted proposals (key findings, sector breakdown, top technologies, compliance insights, recommendations, alignment score).
- **Client problem it solves:** Analysts spend hours writing vendor introductions and periodic summaries.
- **Built from:** `factsheet_service.py`; `chamber_trend_analyses_routes.py` (TREND_SYSTEM_PROMPT); `VendorFactsheet.jsx`, `TrendAnalysesList.jsx`.
- **Evidence:** the files above; `database/vendor_factsheets_migration.sql`.
- **Gap to client-ready:** None. Prompts need re-scoping for a new client (days).
- **Constraints:** Trend reports cover only proposals inside the platform, with no external market data. The prompt example hardcodes the period "Q1 2026". Factsheet quality depends on vendor data, including the trust score, which is SSDC-L03.
- **Domain:** Generate & publish
- **Fits client types:** chambers, trade promotion bodies, research and advisory firms, accelerators
- **Confidence:** medium-high

#### SSDC-R14 — Run a bilingual (EN/AR, RTL), role-based portal for staff, vendors and executives
- **What it does:** A web portal with five roles (admin, analyst, compliance officer, executive, vendor), a vendor self-service dashboard, a public sourcing board, vendor invitations and onboarding, and an Arabic interface with right-to-left layout.
- **Client problem it solves:** Multi-party processes need each party to see only its own view, in Arabic as well as English.
- **Built from:** Supabase `auth.get_user` with the role looked up in `chamber_users` (`auth.py`); `rolePermissions.js`; `language.jsx` (sets `dir="rtl"`); `locales/en.json` / `ar.json` (167 lines each); RLS migrations; `VendorDashboard.jsx`, `SourcingBoard.jsx`, `VendorOnboard.jsx`, `vendor_invite_routes.py`.
- **Evidence:** the files above; commit `42a282b` (RTL sidebar fix).
- **Gap to client-ready:** Rebrand and role mapping (days).
- **Constraints:** Arabic covers the shared UI strings. 33 of 52 pages use the language hook, so some page bodies stay in English. Single-tenant. The UAE PASS SSO is a stub (see P03).
- **Domain:** Deliver & control access
- **Fits client types:** government, chambers, GCC enterprises, donors working in Arabic-speaking regions
- **Confidence:** medium-high

### LATENT

#### SSDC-L01 — Add an AI governance layer to an existing AI system
- **What it does:** Wraps an organisation's own LLM calls with injection screening, grounding checks, cost/energy/carbon accounting, a hash-chained log, a model inventory and a regulator-facing evidence pack.
- **Client problem it solves:** Organisations deploying AI need governance controls and audit evidence, which they don't have.
- **Built from:** R02 + R03 + R04 + L04, plus the provider adapter in `ai_provider.py`.
- **Evidence:** as cited in those cards.
- **Gap to client-ready:** Pull the modules out of the Supabase/`chamber_*` schema into a standalone middleware or SDK, make the hash chain atomic, use real per-model pricing, and add tests. Weeks (3–6).
- **Constraints:** Same limits as R02–R04. No test suite exists in the repo.
- **Domain:** Deliver & control access
- **Fits client types:** government entities, regulated enterprises, any organisation preparing for an AI audit (ISO 42001, DESC AI Security Policy, EU AI Act)
- **Confidence:** medium

#### SSDC-L02 — Pre-audit a proposal against UAE/DESC security frameworks
- **What it does:** Produces control-by-control pass/warning/fail findings and recommendations against DESC ISR V3, the DESC AI Security Policy and the DESC CSP standards, plus a data-residency finding, an overall score and a status.
- **Client problem it solves:** Vendors and buyers can't tell early whether a solution will pass UAE government security requirements.
- **Built from:** `ComplianceEngine` (prompted auditor), compliance audit records and report page.
- **Evidence:** `backend/services/compliance_engine.py`; `frontend/src/pages/ComplianceAuditDetail.jsx`, `AuditReport.jsx`.
- **Gap to client-ready:** Control IDs and findings come from the model's general knowledge, not an authoritative control catalogue. It needs the real control library loaded, retrieval tied to it, and review by a compliance expert. Weeks (2–4) plus access to source standards.
- **Constraints:** The DESC standards may be restricted documents (licensing not verified). LLMs run in the US. The output is advisory and isn't an audit.
- **Domain:** Advise & method
- **Fits client types:** vendors selling into UAE government, UAE government buyers, cloud and SaaS providers, advisory firms
- **Confidence:** medium

#### SSDC-L03 — Verify vendor claims against a compliance knowledge base (RAG)
- **What it does:** Embeds a claim, retrieves the nearest reference passages and has an AI judge whether the claim is supported.
- **Client problem it solves:** Vendors over-claim certifications and controls, and nobody checks them against the standard.
- **Built from:** `compliance_knowledge_service.py` (OpenAI `text-embedding-3-small`, 1536 dimensions, 800/100 chunking, `verify_claim`); `chamber_compliance_knowledge` table with an ivfflat index.
- **Evidence:** `backend/services/compliance_knowledge_service.py`; `database/compliance_knowledge_migration.sql`.
- **Gap to client-ready:** The knowledge base is about 5 hand-written summary paragraphs (ISO 27001, CSA CCM, ISR V3). The `match_compliance_knowledge` RPC is called but isn't defined in any migration in the repo. It needs a real corpus, the RPC, and an evaluation set. Weeks (2–3).
- **Constraints:** Needs an OpenAI key. Source licensing for standards text.
- **Domain:** Analyze & model
- **Fits client types:** procurement, certification bodies, insurers, advisory firms
- **Confidence:** medium-low

#### SSDC-L04 — Generate a regulator-ready audit evidence pack
- **What it does:** Assembles one exportable bundle from live platform data: self-check controls, audit trail, incidents, access control, data residency, model inventory and evidence-validation statistics.
- **Client problem it solves:** Preparing evidence for a regulator or auditor takes weeks of manual collection.
- **Built from:** `audit_pack_service.py` (`generate_audit_pack`, section builders); `AuditEvidencePack.jsx`.
- **Evidence:** `backend/services/audit_pack_service.py`; `backend/routes/audit_pack_routes.py`.
- **Gap to client-ready:** The 19 "platform self-check" controls and their scores are hardcoded self-assessments in code (for example UAE Data Residency is "planned" at 40, Dispose Phase is "planned" at 30). They need to be backed by real evidence and made configurable per framework. Weeks (2–4).
- **Constraints:** Built for DESC only. The self-scores aren't measured.
- **Domain:** Generate & publish
- **Fits client types:** government entities, regulated vendors, AI platform operators
- **Confidence:** medium

#### SSDC-L05 — Score supplier trustworthiness on a credit-bureau-style scale
- **What it does:** Shows a 300–900 vendor trust score across five dimensions (performance, quality, compliance, integrity, entity, weighted 0.30/0.25/0.20/0.15/0.10), with positive and negative flags, score history, an AI narrative and vendor relationships.
- **Client problem it solves:** Buyers have no shared, evidence-based view of supplier reliability.
- **Built from:** `vscore_routes.py` (dossier assembly), `chamber_vscore_history`, `chamber_vendor_flags`, `VendorIntelligence.jsx`, `VendorReputationBadge.jsx`.
- **Evidence:** `backend/routes/vscore_routes.py`; `backend/routes/vendor_intelligence_routes.py`.
- **Gap to client-ready:** No code in the repo computes the score. The weights are returned as constants and scores are read from stored rows, which are presumably seeded. It needs a scoring model fed by engagements, flags and outcomes, a data pipeline and calibration. Weeks to months.
- **Constraints:** Legal exposure if published as a "credit bureau" without due process. Needs real engagement data.
- **Domain:** Analyze & model
- **Fits client types:** procurement networks, chambers, marketplaces, real estate developers (contractor vetting)
- **Confidence:** low-medium

#### SSDC-L06 — Deploy a white-label innovation-sourcing pipeline for another network
- **What it does:** Delivers the whole intake → matching → gate → evaluation → stage-gate → pilot → board-brief pipeline to another chamber, accelerator or ministry.
- **Client problem it solves:** Ecosystem organisations run sourcing through disconnected channels with no view of the full lifecycle.
- **Built from:** R01–R14 together.
- **Evidence:** whole repo; roadmap Phase 3 "white-label for other chamber networks" in `HowItWorks.jsx` (DeploymentRoadmapSection), which is a plan.
- **Gap to client-ready:** Prompts, copy and branding say "Dubai Chambers" throughout. Single-tenant schema. No tests or CI. Needs configuration extraction, multi-tenancy or a clean redeploy procedure, and a test suite. Weeks (4–8) for a clean single-tenant redeploy, months for multi-tenant.
- **Constraints:** Supabase, Railway, Vercel, Anthropic and optional OpenAI/Google, all hosted outside the UAE today.
- **Domain:** Deliver & control access
- **Fits client types:** chambers, accelerators, government innovation units, corporate venture arms, donor programs
- **Confidence:** medium

#### SSDC-L07 — Track security and compliance incidents with alerting
- **What it does:** Logs incidents by severity through to resolution and raises in-app alerts.
- **Client problem it solves:** Incidents aren't recorded in a form that meets regulatory reporting duties.
- **Built from:** `incident_service.py`, `incident_routes.py`, `chamber_alerts_service.py`, `AlertBell.jsx`.
- **Evidence:** the files above; `database/incident_management_migration.sql`, `alerts_migration.sql`.
- **Gap to client-ready:** Alerts are raised only in three places (login, incident creation, proposal submission). There is no anomaly detection, despite the manual's claim, and no DESC reporting integration. Needs alert rules and outbound notifications. Weeks.
- **Constraints:** In-app only, with no email, SMS or Slack.
- **Domain:** Deliver & control access
- **Fits client types:** platform operators, government entities
- **Confidence:** medium

### POTENTIAL

#### SSDC-P01 — Multi-model consensus scoring with disagreement reporting
- **Foundation:** provider adapters for Claude, GPT-4o and Gemini (`evaluation_engine.py`, `hallucination_service.py`), and the cross-model deviation already computed in R02.
- **Missing:** parallel calls, an aggregation rule, a disagreement threshold, cost controls, calibration against human scores.
- **Domain:** Analyze & model · **Confidence:** medium (credible build, 2–3 weeks)

#### SSDC-P02 — Semantic (embedding) matching and deduplication at scale
- **Foundation:** pgvector, the embedding code in `compliance_knowledge_service.py`, `duplicate_check_service.py` expecting stored embeddings, and the comment "In production, this would use vector embeddings" in `proposal_service.py`.
- **Missing:** embedding generation for proposals, cases and vendors; RPC functions; backfill; evaluation.
- **Domain:** Analyze & model · **Confidence:** medium-high (2–4 weeks)

#### SSDC-P03 — UAE government identity and registry integrations (UAE PASS, Dubai trade licence, eSupply)
- **Foundation:** stub routes and data models (`uaepass_routes.py`, `trade_license_routes.py` "stub — awaiting Dubai GRP integration", `trade_license_migration.sql`), plus the procurement-readiness stub described in `PlatformManual.jsx`.
- **Missing:** government onboarding, credentials, API contracts. Timing depends on third parties.
- **Domain:** Ingest & extract · **Confidence:** low-medium

#### SSDC-P04 — Novelty scoring against external prior art (patents, market databases)
- **Foundation:** the novelty dimension and the sector cross-reference in `evaluation_engine.py`.
- **Missing:** a patent or market data source, retrieval, licensing.
- **Domain:** Analyze & model · **Confidence:** medium

#### SSDC-P05 — Ingest scanned and Arabic-language documents
- **Foundation:** the PDF/DOCX extraction and sanitization pipeline (R03, R06), Arabic summaries already produced by the evaluator, and the RTL UI.
- **Missing:** Arabic-capable OCR, Arabic injection patterns, testing on Arabic proposals.
- **Domain:** Ingest & extract · **Confidence:** medium

#### SSDC-P06 — UAE-resident (sovereign) deployment of the AI pipeline
- **Foundation:** the Phase 1 roadmap targets DESC-certified AWS UAE / Azure UAE North (`HowItWorks.jsx`), and the data-residency gate rule exists (R09).
- **Missing:** everything operational. Hosting is Railway/Vercel/Supabase today, the audit pack lists the LLM providers as US-hosted, and its UAE Data Residency control is self-scored "planned" at 40.
- **Domain:** Deliver & control access · **Confidence:** low-medium (a plan, not a capability)

---

## 3. Cross-cutting enablers
- **Multi-provider LLM fallback** (Claude → retry → GPT-4o → Gemini) with tolerant JSON parsing that strips code fences: `ai_provider.py`, `evaluation_engine.py` `_call_ai`/`_parse_response`.
- **Hash-chained AI interaction log** with cost, energy and carbon fields, used by every AI feature: `ai_interaction_service.py`.
- **Document text extraction and injection screening** in front of any LLM: `document_sanitization_service.py`.
- **Role-based auth** using Supabase `get_user`, roles from a users table and RLS policies: `auth.py`, `database/*.sql`.
- **EN/AR RTL rendering toggle** and locale files: `frontend/src/lib/language.jsx`, `locales/`.
- **Deterministic rule gate pattern** (checks without AI, flag-not-reject): `compliance_gate_service.py`.
- **Friendly error envelope** `{error, message, user_action}` that doesn't leak raw exceptions: `main.py`, commits `7016e03`, `ca0f570`.
- **Storage object cleanup** on cascading deletes: commits `eac9ce2`, `3b85943`.
- **Self-documenting API** (Swagger `/docs`, in-app `ApiDocs.jsx`).

## 4. Know-how assets
- **DESC framework mapping:** how ISR V3, the DESC AI Security Policy (5-phase lifecycle: design, develop, deploy, monitor, dispose) and the CSP standards apply to an AI platform, laid out as a 19-control self-check (`audit_pack_service.py`).
- **OWASP LLM Top 10 mitigation mapping** and a **Digital Dubai AI ethics (10 principles)** assessment shown in the UI (`ComplianceAuditsList.jsx`, `AuditEvidencePack.jsx`). Depth not verified.
- **Innovation lifecycle method:** a 9-stage flow from signal intake to ecosystem intelligence, with stage gates, compliance tiers (open/standard/government/critical) and a 5-criterion rubric (`PlatformManual.jsx`, `HowItWorks.jsx`).
- **"σI / Added Intelligence" transparency framing:** cost, energy and carbon disclosed for every AI action, with humans keeping decision authority.
- **Dubai/UAE innovation ecosystem knowledge:** Business in Dubai, Expand North Star, Ignyte, 35+ business groups, D33 agenda alignment (`HowItWorks.jsx` ProblemSection). These figures are the client's, cited from public sources not given in the repo.
- **Phased go-to-market plan for UAE government AI deployments:** 12-week MVP, then ISO 27001, then DESC CSP certification (`HowItWorks.jsx` DeploymentRoadmapSection).

## 5. Proof points
- Deployed: frontend on a custom domain `smart-sourcing.devoneerstechnology.ai` (CORS commit `9fdddf6`), backend on Railway, frontend on Vercel.
- 162 merged PRs. Since April 2026 the work has been bug-fixing on real data paths (vendor columns, ISO rule, storage leaks), which points to a working demo environment.
- A guided 9-step demo path and a live "impact" endpoint (AI minutes, hours saved, total cost) are built into the product (`HowItWorks.jsx`).
- End-to-end seed script for demo data: `database/seed_e2e_test_data.py`.
- **Not found:** named pilot users, client sign-off, accuracy benchmarks, load tests, automated tests or CI.

## 6. Top 3 to lead with
1. **SSDC-L01 / R02–R04: AI governance layer.** Grounding checks, injection screening and a hash-chained cost/carbon log are working today and aren't tied to sourcing. Any organisation deploying LLMs under a regulator (DESC, ISO 42001, EU AI Act) faces this problem, so the market is the widest of anything in this project. Packaging takes weeks, not invention.
2. **SSDC-R01 (+R09, R11, R10): Evidence-scored proposal review with a rule gate and stage-gate.** This is the full demo-able loop: deterministic eligibility checks, a configurable rubric with reasoning and human override, side-by-side comparison and documented gate decisions. It fits procurement, grants, accelerators and investment committees with a prompt rewrite.
3. **SSDC-R05 + R06 + R07: Unstructured intake to structured, de-duplicated cases.** It's a small, quick-to-deploy wedge that solves an everyday problem (requests arriving by email, form or partner channel). It works in Arabic-speaking contexts and leads into the rest of the pipeline.

## 7. Open questions (not verifiable from the files)
- Is Dubai Chambers a contracted client, a running pilot, or a prospect? The repo shows a demo deployment and a "ready for commercial partnership" message, but no contract or usage evidence.
- Do the Supabase RPCs `match_compliance_knowledge` and the proposal-similarity `match_*` function exist in the live database? They aren't in any migration file.
- Where do the stored vScore values come from (seeded, manual, or an external process)?
- Are OpenAI and Google keys configured in production? Without them, "cross-model" checks run on Claude only.
- How much of the UI is in Arabic end to end, and have Arabic-language proposals been tested?
- Has anyone measured how accurate the evaluations or grounding checks are against human reviewers?
- Is it licensed or permitted to embed DESC standards text in a knowledge base?
- What does the history before 2026-04-07 contain (the shallow clone hides it), and has a security review or penetration test been done?
- The audit pack names data processing agreements with OpenAI and Google. Do these exist?

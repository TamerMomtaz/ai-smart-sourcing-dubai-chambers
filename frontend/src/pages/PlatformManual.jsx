import React, { useState, useMemo } from 'react';

const ROLE_COLORS = {
  Admin: 'bg-red-100 text-red-700 border border-red-200',
  Analyst: 'bg-blue-100 text-blue-700 border border-blue-200',
  Compliance: 'bg-green-100 text-green-700 border border-green-200',
  Vendor: 'bg-amber-100 text-amber-700 border border-amber-200',
  Executive: 'bg-purple-100 text-purple-700 border border-purple-200',
};

function RoleBadge({ role }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${ROLE_COLORS[role] || 'bg-gray-100 text-gray-600 border border-gray-200'}`}>
      {role}
    </span>
  );
}

function ManualItem({ name, description, roles, navPath }) {
  return (
    <div className="flex flex-col md:flex-row md:items-start gap-3 p-4 rounded-lg bg-white/60 border border-ink/5 hover:border-teal/20 transition-colors">
      <div className="flex-1 min-w-0">
        <h4 className="font-body text-sm font-semibold text-ink mb-1">{name}</h4>
        <p className="font-body text-xs text-ink/60 leading-relaxed">{description}</p>
      </div>
      <div className="flex flex-wrap items-center gap-1.5 shrink-0">
        {roles.map(r => <RoleBadge key={r} role={r} />)}
      </div>
      {navPath && (
        <span className="shrink-0 font-mono text-[10px] text-teal/70 bg-teal/5 px-2 py-1 rounded">
          {navPath}
        </span>
      )}
    </div>
  );
}

function Section({ title, icon, count, children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded-xl border border-ink/10 overflow-hidden bg-white shadow-sm">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-teal/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">{icon}</span>
          <h3 className="font-heading text-lg text-teal">{title}</h3>
          <span className="text-xs font-body text-ink/40 bg-ink/5 px-2 py-0.5 rounded-full">{count} items</span>
        </div>
        <svg
          className={`w-5 h-5 text-ink/40 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="px-6 pb-6 space-y-3 border-t border-ink/5 pt-4">
          {children}
        </div>
      )}
    </div>
  );
}

const ALL_ROLES = ['Admin', 'Analyst', 'Compliance', 'Vendor', 'Executive'];
const NON_VENDOR = ['Admin', 'Analyst', 'Compliance', 'Executive'];
const ADMIN_COMPLIANCE = ['Admin', 'Compliance'];
const ADMIN_ONLY = ['Admin'];
const ADMIN_ANALYST = ['Admin', 'Analyst'];
const ADMIN_ANALYST_EXEC = ['Admin', 'Analyst', 'Executive'];

const SECTIONS = [
  {
    title: 'Innovation Lifecycle',
    icon: '🔄',
    items: [
      {
        name: '1. Signal Intake',
        description: 'Multi-channel sourcing case creation. Captures innovation signals from internal teams, vendor submissions, market intelligence, and public sourcing board. Each signal becomes a structured sourcing case with automated metadata tagging.',
        features: ['Email/form/API intake channels', 'AI-assisted case structuring', 'Auto-classification by sector & technology', 'Public Sourcing Board for open innovation'],
        roles: ALL_ROLES,
        navPath: '/sourcing-cases',
      },
      {
        name: '2. AI Structuring',
        description: 'AI Assist extracts structured fields from raw text input. Natural language descriptions are parsed into standardized sourcing case fields using multi-model NLP pipeline with human review.',
        features: ['NLP field extraction from free text', 'Multi-model consensus parsing', 'Confidence scores per field', 'Human review & correction workflow'],
        roles: ALL_ROLES,
        navPath: '/sourcing-cases',
      },
      {
        name: '3. Deduplication',
        description: 'Detects overlapping cases across channels to prevent redundant evaluations. Semantic similarity analysis identifies near-duplicates even when phrased differently.',
        features: ['Semantic similarity scoring', 'Cross-channel duplicate detection', 'Merge or link duplicate cases', 'AI confidence threshold controls'],
        roles: ADMIN_ANALYST,
        navPath: '/sourcing-cases',
      },
      {
        name: '4. Vendor Discovery',
        description: 'AI matches vendors proactively to sourcing cases based on capability profiles, past performance, and compliance status. Reduces manual vendor search time significantly.',
        features: ['Semantic vendor-case alignment', 'vScore-weighted recommendations', 'DESC compliance filtering', 'Capability gap identification'],
        roles: ADMIN_ANALYST,
        navPath: '/vendors',
      },
      {
        name: '5. Compliance Gate',
        description: 'Five rule-based checks executed before AI evaluation begins. Ensures all submissions meet minimum compliance thresholds for DESC framework, trade licensing, and data governance.',
        features: ['DESC certification verification', 'Trade license validation', 'Data governance check', 'Security posture assessment', 'Conflict of interest screening'],
        roles: ADMIN_COMPLIANCE,
        navPath: '/compliance-audits',
      },
      {
        name: 'Compliance Tiers',
        description: 'Open / Standard / Government / Critical filtering applied to sourcing cases. Each tier enforces escalating compliance requirements, ensuring the right governance level for every innovation case.',
        features: ['4-tier classification system', 'Automatic tier assignment', 'Escalating compliance gates', 'Government-tier DESC enforcement'],
        roles: ALL_ROLES,
        navPath: '/sourcing-cases',
      },
      {
        name: '6. AI Evaluation',
        description: 'Five-dimension scoring with evidence attribution using multi-model pipeline. Each proposal receives independent assessments from Claude, GPT-4o, and Gemini with cross-validation.',
        features: ['5-dimension scoring framework', 'Multi-model consensus evaluation', 'Evidence attribution per score', 'Innovation novelty cross-referencing', 'Human override with reasoning'],
        roles: ADMIN_ANALYST,
        navPath: '/evaluations',
      },
      {
        name: '7. Stage-Gate',
        description: 'GO/KILL/HOLD/RECYCLE governance decisions at each lifecycle stage. Structured decision framework ensures consistent governance across all innovation proposals.',
        features: ['GO / KILL / HOLD / RECYCLE decisions', 'Multi-stakeholder voting', 'Decision audit trail', 'Automated notifications'],
        roles: ADMIN_ANALYST_EXEC,
        navPath: '/sourcing-cases',
      },
      {
        name: '8. Pilot Tracking',
        description: 'Setup to outcome lifecycle management for approved pilots. Tracks milestones, deliverables, vendor performance, and outcome metrics through the entire engagement.',
        features: ['Milestone tracking dashboard', 'Vendor delivery rating', 'Budget vs. actual monitoring', 'Outcome documentation'],
        roles: ALL_ROLES,
        navPath: '/pilot-tracker',
      },
      {
        name: '9. Ecosystem Intelligence',
        description: 'Board Brief, KPIs, and analytics aggregated across the entire innovation pipeline. Provides executive-level visibility into portfolio performance and strategic alignment.',
        features: ['Executive Board Brief generator', 'Pipeline KPI dashboard', 'Sector trend analysis', 'Channel performance analytics'],
        roles: ADMIN_ANALYST_EXEC,
        navPath: '/board-brief',
      },
    ],
  },
  {
    title: 'AI Capabilities',
    icon: '🤖',
    items: [
      {
        name: 'Multi-Model Pipeline',
        description: 'Claude Sonnet for deep reasoning, GPT-4o for breadth analysis, Gemini 2.0 Flash for speed validation. Three-model consensus ensures no single AI bias dominates evaluation outcomes.',
        roles: ALL_ROLES,
        navPath: '/ai-team',
      },
      {
        name: 'Evidence Validation Layer',
        description: 'Cross-model verification combined with RAG (Retrieval Augmented Generation) to ground AI outputs in factual evidence. Every claim is traced to source documents.',
        roles: ALL_ROLES,
        navPath: '/ai-interactions',
      },
      {
        name: 'Innovation Novelty Scoring',
        description: 'The 5th evaluation dimension cross-references proposals against existing portfolio, market intelligence, and patent databases to score true innovation differentiation.',
        roles: ADMIN_ANALYST,
        navPath: '/evaluations',
      },
      {
        name: 'AI Explainability',
        description: 'Evidence attribution per dimension ensures every AI score can be traced back to specific proposal content, vendor data, or market intelligence that informed the assessment.',
        roles: ALL_ROLES,
        navPath: '/evaluations',
      },
      {
        name: 'Human Override',
        description: 'Analysts can adjust any AI-generated score with documented reasoning. Override history is maintained in the audit trail for governance and continuous AI improvement.',
        roles: ADMIN_ANALYST,
        navPath: '/evaluations',
      },
      {
        name: 'Document Sanitization',
        description: 'OWASP LLM01 prompt injection defense. All user-submitted documents are sanitized before AI processing to prevent adversarial manipulation of evaluation outcomes.',
        roles: ADMIN_COMPLIANCE,
        navPath: '/documents',
      },
      {
        name: 'AI-Assisted Case Creation',
        description: 'NLP intake structuring transforms unstructured innovation signals into standardized sourcing cases. Reduces case creation time from hours to minutes.',
        roles: ALL_ROLES,
        navPath: '/sourcing-cases',
      },
      {
        name: 'Active Vendor Matching',
        description: 'Semantic vendor-case alignment proactively recommends qualified vendors for each sourcing case based on capability profiles, compliance status, and past performance.',
        roles: ADMIN_ANALYST,
        navPath: '/vendors',
      },
      {
        name: 'Vendor Factsheet Generation',
        description: 'AI-generated one-pager summaries for vendor introductions. Consolidates capability profile, compliance status, vScore, and engagement history into a structured factsheet ready for stakeholder sharing.',
        roles: ADMIN_ANALYST,
        navPath: '/vendors',
      },
      {
        name: 'Proposal Comparison Workspace',
        description: 'AI-generated comparative analysis with side-by-side comparison of up to 4 proposals for the same sourcing case. Scoring with evidence highlights for faster decision-making.',
        roles: ADMIN_ANALYST_EXEC,
        navPath: '/compare',
      },
    ],
  },
  {
    title: 'Compliance & Governance',
    icon: '🛡️',
    items: [
      {
        name: 'DESC Framework',
        description: 'Full alignment with ISR V3, AI Security Policy, and CSP Standards. The platform implements DESC-mandated controls across data governance, AI operations, and audit readiness.',
        roles: ALL_ROLES,
        navPath: '/compliance-audits',
      },
      {
        name: 'Platform Self-Check',
        description: '19 controls scored across security, governance, and compliance domains. Real-time self-assessment dashboard shows current compliance posture at a glance.',
        roles: ADMIN_COMPLIANCE,
        navPath: '/compliance-audits',
      },
      {
        name: 'AI Ethics Assessment',
        description: '10 Digital Dubai principles evaluated with 90% compliance target. Covers fairness, transparency, accountability, privacy, and human oversight dimensions.',
        roles: ADMIN_COMPLIANCE,
        navPath: '/compliance-audits',
      },
      {
        name: 'OWASP Security Posture',
        description: '6 out of 6 OWASP LLM Top 10 risks mitigated. Covers prompt injection, data leakage, insecure output handling, model denial of service, supply chain, and overreliance.',
        roles: ADMIN_COMPLIANCE,
        navPath: '/compliance-audits',
      },
      {
        name: 'Immutable Audit Logs',
        description: 'SHA-256 hash chain verification ensures audit log integrity. Every platform action is recorded with tamper-evident cryptographic linking.',
        roles: ADMIN_COMPLIANCE,
        navPath: '/ai-interactions',
      },
      {
        name: '7-Year Retention Policy',
        description: 'ISR V3 compliant data retention. All evaluation records, audit logs, and governance decisions are preserved for the mandated 7-year period.',
        roles: ADMIN_COMPLIANCE,
        navPath: '/compliance-audits',
      },
      {
        name: 'Audit Evidence Pack',
        description: 'One-click DESC bundle generation for regulatory submissions. Compiles compliance scores, audit trails, and governance documentation into a single exportable package.',
        roles: ADMIN_COMPLIANCE,
        navPath: '/compliance-audits',
      },
      {
        name: 'Incident Management',
        description: 'Severity tracking with DESC reporting integration. Security and compliance incidents are categorized, tracked through resolution, and reported per DESC requirements.',
        roles: ADMIN_COMPLIANCE,
        navPath: '/compliance-audits',
      },
      {
        name: 'Real-Time Alerting',
        description: 'Proactive anomaly detection across platform operations. Automated alerts for compliance threshold breaches, security events, and operational anomalies.',
        roles: ALL_ROLES,
        navPath: '/dashboard',
      },
      {
        name: 'AI Model Inventory',
        description: 'ISO 42001 governance for all AI models in the platform. Tracks model versions, training data provenance, performance metrics, and risk assessments.',
        roles: ADMIN_COMPLIANCE,
        navPath: '/model-inventory',
      },
    ],
  },
  {
    title: 'Vendor Intelligence',
    icon: '🏢',
    items: [
      {
        name: 'vScore Credit Bureau',
        description: '300-900 trust index across 5 dimensions: delivery track record, compliance posture, innovation capability, financial stability, and ecosystem engagement. Updated in real-time.',
        roles: ALL_ROLES,
        navPath: '/vendor-intelligence',
      },
      {
        name: 'DESC Certification Registry',
        description: 'Auto-filter vendors by DESC compliance status. Only certified vendors appear in government-tier sourcing cases, ensuring regulatory alignment from the start.',
        roles: ALL_ROLES,
        navPath: '/vendor-intelligence',
      },
      {
        name: 'Trade License Verification',
        description: 'Dubai GRP integration stub for automated trade license validation. Verifies vendor registration status, license expiry, and permitted activities.',
        roles: ADMIN_COMPLIANCE,
        navPath: '/vendors',
      },
      {
        name: 'Vendor Factsheets',
        description: 'AI-generated one-pager summaries for each vendor. Consolidates capability profile, compliance status, vScore history, and engagement track record.',
        roles: ALL_ROLES,
        navPath: '/vendors',
      },
      {
        name: 'Vendor-Side Dashboard',
        description: 'Dedicated vendor portal showing proposal submissions, vScore, open sourcing opportunities, and compliance status. Gives vendors full visibility into their platform engagement and next steps.',
        roles: ['Admin', 'Vendor'],
        navPath: '/vendor-dashboard',
      },
      {
        name: 'Procurement Readiness',
        description: 'eSupply/Smart Supplier dashboard integration stub. Shows vendor readiness status for government procurement platforms and smart supplier certification.',
        roles: ADMIN_ANALYST,
        navPath: '/vendor-intelligence',
      },
      {
        name: 'Compliance Tiers',
        description: 'Open / Standard / Government / Critical classification. Each tier has escalating compliance requirements, with automatic tier assignment based on vendor profile.',
        roles: ALL_ROLES,
        navPath: '/vendor-intelligence',
      },
    ],
  },
  {
    title: 'Platform Infrastructure',
    icon: '⚙️',
    items: [
      {
        name: 'Architecture',
        description: 'React/Vite frontend + FastAPI backend + Supabase PostgreSQL database. Modern microservices architecture optimized for UAE government cloud requirements.',
        roles: ADMIN_ONLY,
        navPath: '/api-reference',
      },
      {
        name: 'Security',
        description: 'Row Level Security (RLS) on all database tables, 5 distinct user roles, JWT-based authentication. Defense-in-depth security model aligned with DESC CSP standards.',
        roles: ADMIN_ONLY,
        navPath: '/users',
      },
      {
        name: 'Deployment',
        description: 'Vercel for frontend hosting with edge CDN, Railway for backend API with auto-scaling. CI/CD pipeline with automated testing and deployment gates.',
        roles: ADMIN_ONLY,
        navPath: null,
      },
      {
        name: 'Languages',
        description: 'English + Arabic (RTL) with full bidirectional support. All platform text is translated and layout automatically adjusts for right-to-left reading.',
        roles: ALL_ROLES,
        navPath: null,
      },
      {
        name: 'UAE PASS SSO',
        description: 'OAuth 2.0 stub ready for UAE PASS integration. Single sign-on for government users with UAE national identity verification.',
        roles: ADMIN_ONLY,
        navPath: null,
      },
      {
        name: 'Public Sourcing Board',
        description: 'Open innovation marketplace where external vendors can discover and apply to sourcing cases. Public-facing portal with self-service vendor onboarding.',
        roles: ALL_ROLES,
        navPath: '/sourcing-board',
      },
      {
        name: 'Channel Analytics',
        description: 'Source performance tracking across all intake channels. Measures signal quality, conversion rates, and time-to-evaluation per channel.',
        roles: ADMIN_ANALYST_EXEC,
        navPath: '/dashboard',
      },
      {
        name: 'Pipeline KPIs',
        description: '7 operational metrics: cases created, evaluations completed, average evaluation time, compliance pass rate, pilot conversion rate, vendor response time, decision cycle time.',
        roles: ADMIN_ANALYST_EXEC,
        navPath: '/dashboard',
      },
      {
        name: 'Business Groups → Cases',
        description: 'Direct need submission from business groups. Groups can create sourcing cases from their innovation needs without analyst intermediation, streamlining the intake pipeline.',
        roles: ALL_ROLES,
        navPath: '/business-groups',
      },
      {
        name: 'Guided Demo Path',
        description: '9-step interactive walkthrough in How It Works. Demonstrates the complete innovation lifecycle from signal intake through pilot tracking with live platform examples.',
        roles: ALL_ROLES,
        navPath: '/how-it-works',
      },
      {
        name: 'Deployment Roadmap',
        description: '3-phase deployment plan with DESC certification timeline. Covers sandbox validation, pilot rollout, and production launch with regulatory milestones and go-live criteria.',
        roles: ADMIN_ONLY,
        navPath: null,
      },
    ],
  },
];

function PlatformManual() {
  const [search, setSearch] = useState('');
  const [openSections, setOpenSections] = useState({});

  const toggleSection = (idx) => {
    setOpenSections(prev => ({ ...prev, [idx]: !prev[idx] }));
  };

  const filteredSections = useMemo(() => {
    if (!search.trim()) return SECTIONS;
    const q = search.toLowerCase();
    return SECTIONS.map(section => ({
      ...section,
      items: section.items.filter(item =>
        item.name.toLowerCase().includes(q) ||
        item.description.toLowerCase().includes(q) ||
        (item.features && item.features.some(f => f.toLowerCase().includes(q))) ||
        item.roles.some(r => r.toLowerCase().includes(q))
      ),
    })).filter(section => section.items.length > 0);
  }, [search]);

  const totalCapabilities = SECTIONS.reduce((sum, s) => sum + s.items.length, 0);

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="font-heading text-3xl md:text-4xl text-teal mb-2">
          Platform Manual — AI Smart Sourcing
        </h1>
        <p className="font-body text-ink/60 text-sm mb-3">
          Complete reference guide for the Innovation Orchestration Platform
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-block font-mono text-[11px] text-teal bg-teal/10 px-3 py-1 rounded-full font-semibold">
            v2.1 | April 2026
          </span>
          <span className="inline-block font-mono text-[11px] text-ink/50 bg-ink/5 px-3 py-1 rounded-full">
            {totalCapabilities} capabilities across {SECTIONS.length} domains
          </span>
        </div>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search capabilities, features, roles..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-xl border border-ink/10 bg-white font-body text-sm text-ink placeholder:text-ink/30 focus:outline-none focus:ring-2 focus:ring-teal/30 focus:border-teal/40 transition-colors"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/30 hover:text-ink/60 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        {search && (
          <p className="mt-2 font-body text-xs text-ink/40">
            {filteredSections.reduce((sum, s) => sum + s.items.length, 0)} results for "{search}"
          </p>
        )}
      </div>

      {/* Sections */}
      <div className="space-y-4">
        {filteredSections.map((section, idx) => {
          const sectionKey = SECTIONS.indexOf(section) !== -1 ? SECTIONS.indexOf(section) : idx;
          const isOpen = search.trim() ? true : !!openSections[sectionKey];

          return (
            <div key={section.title} className="rounded-xl border border-ink/10 overflow-hidden bg-white shadow-sm">
              <button
                onClick={() => !search.trim() && toggleSection(sectionKey)}
                className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-teal/5 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">{section.icon}</span>
                  <h3 className="font-heading text-lg text-teal">{section.title}</h3>
                  <span className="text-xs font-body text-ink/40 bg-ink/5 px-2 py-0.5 rounded-full">
                    {section.items.length} items
                  </span>
                </div>
                {!search.trim() && (
                  <svg
                    className={`w-5 h-5 text-ink/40 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                    fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                )}
              </button>
              {isOpen && (
                <div className="px-6 pb-6 space-y-3 border-t border-ink/5 pt-4">
                  {section.items.map(item => (
                    <ManualItem
                      key={item.name}
                      name={item.name}
                      description={item.description}
                      roles={item.roles}
                      navPath={item.navPath}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="mt-10 pt-6 border-t border-ink/10 flex flex-col md:flex-row items-center justify-between gap-4">
        <p className="font-body text-xs text-ink/40 text-center md:text-left">
          AI Smart Sourcing v2.1 | Built by Tamer Momtaz | Powered by {'\u03C3'}I — Added Intelligence | DEVONEERS
        </p>
        <button
          onClick={() => window.print()}
          className="px-5 py-2.5 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 transition-colors flex items-center gap-2 print:hidden"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Download as PDF
        </button>
      </div>
    </div>
  );
}

export default PlatformManual;

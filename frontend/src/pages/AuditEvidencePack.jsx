import React, { useState } from 'react';
import api, { getErrorMessage } from '../lib/api';

/* ── Section labels mapped to DESC framework domains ── */
const SECTION_META = {
  platform_self_check: { label: 'ISR V3 — Domain 13: Compliance & Audit', subtitle: 'Platform Self-Check (19 Controls)' },
  compliance_audits_summary: { label: 'ISR V3 — Domain 13: Compliance & Audit', subtitle: 'Compliance Audits Summary' },
  transparency_log: { label: 'AI Security Policy — Transparency', subtitle: 'Sigma-I Transparency Log' },
  incident_management: { label: 'ISR V3 — Domain 10: Incident Management', subtitle: 'Incidents & DESC Reports' },
  access_control: { label: 'ISR V3 — Domain 5: Access Control', subtitle: 'RBAC & RLS Summary' },
  data_residency: { label: 'CSP Standard — Data Residency', subtitle: 'Hosting & Migration Plan' },
  ai_model_inventory: { label: 'AI Security Policy — Transparency', subtitle: 'Model Inventory' },
  evidence_validation: { label: 'AI Security Policy — Hallucination Monitoring', subtitle: 'Evidence Validation Layer (Shield)' },
};

const SECTION_ORDER = [
  'platform_self_check',
  'compliance_audits_summary',
  'transparency_log',
  'incident_management',
  'access_control',
  'data_residency',
  'ai_model_inventory',
  'evidence_validation',
];

/* ── Reusable sub-components ── */

const StatCard = ({ label, value, color = 'text-[var(--color-accent)]' }) => (
  <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
    <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">{label}</p>
    <p className={`text-2xl font-bold ${color}`}>{value}</p>
  </div>
);

const PassRate = ({ label, rate }) => {
  const color = rate >= 80 ? 'text-emerald-400' : rate >= 50 ? 'text-amber-400' : 'text-red-400';
  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-gray-400 text-sm">{label}</span>
      <span className={`font-bold text-sm ${color}`}>{rate}%</span>
    </div>
  );
};

const Badge = ({ text, color }) => (
  <span className={`px-2 py-0.5 rounded text-xs font-bold border ${color}`}>{text}</span>
);

const statusColors = {
  active: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  aligned: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  planned: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
};

/* ── Section renderers ── */

function renderPlatformSelfCheck(data) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Controls" value={data.total_controls} />
        <StatCard label="Active" value={data.active} color="text-emerald-400" />
        <StatCard label="Aligned" value={data.aligned} color="text-blue-400" />
        <StatCard label="Avg Score" value={`${data.average_score}%`} />
      </div>
      <div className="space-y-2 mt-3">
        {data.controls?.map((c) => (
          <div key={c.id} className="flex items-center gap-3 bg-[#0F172A] rounded-lg border border-gray-700/30 px-4 py-2">
            <Badge text={c.status} color={statusColors[c.status] || statusColors.planned} />
            <span className="text-white text-sm flex-1">{c.title}</span>
            <span className="text-gray-400 text-xs">{c.score}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function renderComplianceSummary(data) {
  return (
    <div className="space-y-3">
      <StatCard label="Total Audits" value={data.total_audits} />
      <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
        <p className="text-white text-sm font-medium mb-2">Pass Rates by Framework</p>
        <PassRate label="ISR V3 Controls" rate={data.pass_rates?.isr_v3} />
        <PassRate label="AI Security Policy" rate={data.pass_rates?.ai_security_policy} />
        <PassRate label="CSP Standards" rate={data.pass_rates?.csp_standards} />
        <PassRate label="Data Residency" rate={data.pass_rates?.data_residency} />
      </div>
      {data.audits?.length > 0 && (
        <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-table-header-bg)]">
              <tr>
                <th className="text-left p-3 text-gray-400 font-medium">Date</th>
                <th className="text-left p-3 text-gray-400 font-medium">ISR V3</th>
                <th className="text-left p-3 text-gray-400 font-medium">AI Policy</th>
                <th className="text-left p-3 text-gray-400 font-medium">CSP</th>
                <th className="text-left p-3 text-gray-400 font-medium">Data Res.</th>
              </tr>
            </thead>
            <tbody>
              {data.audits.map((a) => (
                <tr key={a.id} className="border-t border-gray-700/30">
                  <td className="p-3 text-gray-400">{a.audit_timestamp ? new Date(a.audit_timestamp).toLocaleDateString() : '—'}</td>
                  <td className="p-3"><span className={a.isr_v3_compliance ? 'text-emerald-400' : 'text-red-400'}>{a.isr_v3_compliance ? 'Pass' : 'Fail'}</span></td>
                  <td className="p-3"><span className={a.ai_security_policy_compliance ? 'text-emerald-400' : 'text-red-400'}>{a.ai_security_policy_compliance ? 'Pass' : 'Fail'}</span></td>
                  <td className="p-3"><span className={a.csp_standards_compliance ? 'text-emerald-400' : 'text-red-400'}>{a.csp_standards_compliance ? 'Pass' : 'Fail'}</span></td>
                  <td className="p-3"><span className={a.data_residency_verified ? 'text-emerald-400' : 'text-red-400'}>{a.data_residency_verified ? 'Yes' : 'No'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function renderTransparencyLog(data) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Interactions" value={data.total_interactions} />
        <StatCard label="Total Cost" value={`$${data.total_cost_usd}`} />
        <StatCard label="Total Tokens" value={data.total_tokens?.toLocaleString()} />
        <StatCard label="Avg Latency" value={`${data.average_latency_ms}ms`} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
          <p className="text-white text-sm font-medium mb-2">By Operation Type</p>
          {Object.entries(data.by_operation_type || {}).sort((a, b) => b[1] - a[1]).map(([op, count]) => (
            <div key={op} className="flex justify-between py-1 text-sm">
              <span className="text-gray-400">{op.replace(/_/g, ' ')}</span>
              <span className="text-white font-medium">{count}</span>
            </div>
          ))}
        </div>
        <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
          <p className="text-white text-sm font-medium mb-2">By Model</p>
          {Object.entries(data.by_model || {}).sort((a, b) => b[1] - a[1]).map(([model, count]) => (
            <div key={model} className="flex justify-between py-1 text-sm">
              <span className="text-gray-400">{model}</span>
              <span className="text-white font-medium">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function renderIncidentManagement(data) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Incidents" value={data.total_incidents} />
        <StatCard label="Open" value={data.open} color={data.open > 0 ? 'text-red-400' : 'text-emerald-400'} />
        <StatCard label="Resolved" value={data.resolved} color="text-emerald-400" />
        <StatCard label="Reported to DESC" value={data.reported_to_desc} color="text-purple-400" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
          <p className="text-white text-sm font-medium mb-2">By Severity</p>
          {Object.entries(data.by_severity || {}).map(([sev, count]) => (
            <div key={sev} className="flex justify-between py-1 text-sm">
              <span className="text-gray-400 capitalize">{sev}</span>
              <span className="text-white font-medium">{count}</span>
            </div>
          ))}
          {Object.keys(data.by_severity || {}).length === 0 && <p className="text-gray-500 text-sm">No incidents</p>}
        </div>
        <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
          <p className="text-white text-sm font-medium mb-2">By Status</p>
          {Object.entries(data.by_status || {}).map(([st, count]) => (
            <div key={st} className="flex justify-between py-1 text-sm">
              <span className="text-gray-400">{st.replace(/_/g, ' ')}</span>
              <span className="text-white font-medium">{count}</span>
            </div>
          ))}
          {Object.keys(data.by_status || {}).length === 0 && <p className="text-gray-500 text-sm">No incidents</p>}
        </div>
      </div>
    </div>
  );
}

function renderAccessControl(data) {
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <StatCard label="Total Users" value={data.total_users} />
        <StatCard label="RBAC" value={data.rbac_enabled ? 'Enabled' : 'Disabled'} color={data.rbac_enabled ? 'text-emerald-400' : 'text-red-400'} />
        <StatCard label="Row-Level Security" value={data.rls_enabled ? 'Enabled' : 'Disabled'} color={data.rls_enabled ? 'text-emerald-400' : 'text-red-400'} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
          <p className="text-white text-sm font-medium mb-2">Users by Role</p>
          {Object.entries(data.by_role || {}).map(([role, count]) => (
            <div key={role} className="flex justify-between py-1 text-sm">
              <span className="text-gray-400">{role.replace(/_/g, ' ')}</span>
              <span className="text-white font-medium">{count}</span>
            </div>
          ))}
        </div>
        <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
          <p className="text-white text-sm font-medium mb-2">RLS-Protected Tables</p>
          <p className="text-emerald-400 text-sm font-bold mb-1">{data.rls_tables?.length || 0} tables</p>
          <div className="flex flex-wrap gap-1">
            {(data.rls_tables || []).map((t) => (
              <span key={t} className="px-2 py-0.5 rounded text-xs bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">{t}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function renderDataResidency(data) {
  const hosting = data.current_hosting || {};
  const plan = data.uae_migration_plan || {};
  return (
    <div className="space-y-3">
      <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
        <p className="text-white text-sm font-medium mb-2">Current Hosting</p>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between"><span className="text-gray-400">Database</span><span className="text-white">{hosting.database}</span></div>
          <div className="flex justify-between"><span className="text-gray-400">Backend</span><span className="text-white">{hosting.backend}</span></div>
          <div className="flex justify-between"><span className="text-gray-400">Frontend</span><span className="text-white">{hosting.frontend}</span></div>
        </div>
        {hosting.ai_providers?.length > 0 && (
          <div className="mt-3">
            <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">AI Providers</p>
            {hosting.ai_providers.map((p, i) => (
              <p key={i} className="text-gray-300 text-xs">{p}</p>
            ))}
          </div>
        )}
      </div>
      <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
        <p className="text-white text-sm font-medium mb-2">UAE Migration Plan</p>
        <div className="space-y-1 text-sm">
          <div className="flex justify-between"><span className="text-gray-400">Status</span><Badge text={plan.status || 'planned'} color="bg-amber-500/20 text-amber-400 border-amber-500/30" /></div>
          <div className="flex justify-between"><span className="text-gray-400">Target</span><span className="text-white">{plan.target}</span></div>
        </div>
        {plan.notes && <p className="text-gray-400 text-xs mt-2">{plan.notes}</p>}
      </div>
      {data.data_sovereignty_controls?.length > 0 && (
        <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
          <p className="text-white text-sm font-medium mb-2">Data Sovereignty Controls</p>
          <ul className="space-y-1">
            {data.data_sovereignty_controls.map((c, i) => (
              <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                <span className="text-emerald-400 mt-0.5">&#10003;</span> {c}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function renderModelInventory(data) {
  const gov = data.governance || {};
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <StatCard label="Total Models" value={data.total_models} />
        <StatCard label="Multi-Model" value={gov.multi_model_architecture ? 'Yes' : 'No'} color={gov.multi_model_architecture ? 'text-emerald-400' : 'text-red-400'} />
        <StatCard label="Failover" value={gov.failover_enabled ? 'Enabled' : 'Disabled'} color={gov.failover_enabled ? 'text-emerald-400' : 'text-red-400'} />
      </div>
      {data.models?.length > 0 && (
        <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-table-header-bg)]">
              <tr>
                <th className="text-left p-3 text-gray-400 font-medium">Model</th>
                <th className="text-left p-3 text-gray-400 font-medium">Operations</th>
                <th className="text-left p-3 text-gray-400 font-medium">Purposes</th>
              </tr>
            </thead>
            <tbody>
              {data.models.map((m) => (
                <tr key={m.model_name} className="border-t border-gray-700/30">
                  <td className="p-3 text-white font-medium">{m.model_name}</td>
                  <td className="p-3 text-gray-400">{m.total_operations}</td>
                  <td className="p-3 text-gray-400">{m.purposes?.join(', ').replace(/_/g, ' ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function renderEvidenceValidation(data) {
  const risk = data.risk_distribution || {};
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatCard label="Total Checks" value={data.total_checks} />
        <StatCard label="Avg Grounding" value={`${data.average_grounding_score}%`} color={data.average_grounding_score >= 80 ? 'text-emerald-400' : data.average_grounding_score >= 50 ? 'text-amber-400' : 'text-red-400'} />
        <StatCard label="Total Claims" value={data.total_claims} />
        <StatCard label="Grounded" value={data.grounded_claims} color="text-emerald-400" />
      </div>
      <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 p-4">
        <p className="text-white text-sm font-medium mb-2">Risk Distribution</p>
        <div className="flex gap-4 text-sm">
          <span className="text-emerald-400">Low: {risk.low || 0}</span>
          <span className="text-amber-400">Medium: {risk.medium || 0}</span>
          <span className="text-red-400">High: {risk.high || 0}</span>
        </div>
        {data.total_checks > 0 && (
          <div className="flex h-4 rounded overflow-hidden mt-2">
            {risk.low > 0 && <div className="bg-emerald-500" style={{ flex: risk.low }} />}
            {risk.medium > 0 && <div className="bg-amber-500" style={{ flex: risk.medium }} />}
            {risk.high > 0 && <div className="bg-red-500" style={{ flex: risk.high }} />}
          </div>
        )}
      </div>
    </div>
  );
}

const SECTION_RENDERERS = {
  platform_self_check: renderPlatformSelfCheck,
  compliance_audits_summary: renderComplianceSummary,
  transparency_log: renderTransparencyLog,
  incident_management: renderIncidentManagement,
  access_control: renderAccessControl,
  data_residency: renderDataResidency,
  ai_model_inventory: renderModelInventory,
  evidence_validation: renderEvidenceValidation,
};

/* ── Main Component ── */

export default function AuditEvidencePack() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [collapsed, setCollapsed] = useState({});

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.post('/api/v1/compliance/audit-pack');
      setData(res.data);
      // start all sections expanded
      setCollapsed({});
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const toggle = (key) => setCollapsed((prev) => ({ ...prev, [key]: !prev[key] }));

  const handlePrint = () => window.print();

  const handleDownloadJSON = () => {
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `desc-audit-evidence-pack-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="pt-2">
      {/* Print-only styles */}
      <style>{`
        @media print {
          .no-print { display: none !important; }
          body { background: #fff !important; color: #000 !important; }
          @page { margin: 14mm; }
          .print-section { page-break-inside: avoid; }
        }
      `}</style>

      {/* Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 no-print">
        <div>
          <h2 className="text-2xl font-bold text-white">DESC Audit Evidence Pack</h2>
          <p className="text-gray-400 text-sm mt-1">
            Comprehensive audit bundle for DESC regulatory review
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={generate}
            disabled={loading}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white font-semibold px-5 py-2 rounded-lg transition-colors text-sm disabled:opacity-50"
          >
            {loading ? 'Generating...' : data ? 'Regenerate Pack' : 'Generate Full Pack'}
          </button>
          {data && (
            <>
              <button
                onClick={handlePrint}
                className="bg-[#1E293B] hover:bg-[#334155] text-gray-300 font-medium px-4 py-2 rounded-lg transition border border-gray-600 text-sm"
              >
                Download as PDF
              </button>
              <button
                onClick={handleDownloadJSON}
                className="bg-[#1E293B] hover:bg-[#334155] text-gray-300 font-medium px-4 py-2 rounded-lg transition border border-gray-600 text-sm"
              >
                Download as JSON
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6 no-print">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {loading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[var(--color-accent)] mx-auto mb-3"></div>
          <p className="text-gray-400 text-sm">Aggregating evidence from all platform modules...</p>
        </div>
      )}

      {!data && !loading && !error && (
        <div className="bg-[#1E293B] rounded-xl border border-gray-700/50 p-12 text-center">
          <div className="text-4xl mb-4 text-gray-600">&#128203;</div>
          <p className="text-gray-400 text-sm mb-4">
            Click "Generate Full Pack" to aggregate evidence across all platform modules into a
            comprehensive DESC-compliant audit bundle.
          </p>
          <p className="text-gray-500 text-xs">
            Covers: Platform Controls, Compliance Audits, AI Transparency, Incidents,
            Access Control, Data Residency, Model Inventory, Evidence Validation
          </p>
        </div>
      )}

      {/* AI Security Posture — always visible */}
      <div className="mt-8 mb-6">
        <div className="bg-[#1E293B] rounded-xl border border-gray-700/50 px-6 py-5 mb-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <h3 className="text-lg font-bold text-white">AI Security Posture — OWASP Top 10 for LLM Applications</h3>
              <p className="text-gray-400 text-sm mt-1">
                Mapped against{' '}
                <a href="https://owasp.org/www-project-top-10-for-large-language-model-applications/" target="_blank" rel="noopener noreferrer" className="text-[var(--color-accent)] hover:underline">
                  OWASP LLM Top 10
                </a>
                {' '}and MITRE ATLAS frameworks
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg px-4 py-2 text-center">
                <p className="text-emerald-400 text-2xl font-bold">6/6</p>
                <p className="text-emerald-400/70 text-xs font-medium">risks mitigated</p>
              </div>
              <div className="bg-emerald-500/20 border border-emerald-500/30 rounded-lg px-4 py-2 text-center">
                <p className="text-emerald-400 text-2xl font-bold">100%</p>
                <p className="text-emerald-400/70 text-xs font-medium">coverage</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-[#0F172A] rounded-lg border border-gray-700/30 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-table-header-bg)]">
              <tr>
                <th className="text-left p-3 text-gray-400 font-medium">OWASP LLM Risk</th>
                <th className="text-left p-3 text-gray-400 font-medium">Platform Mitigation</th>
                <th className="text-left p-3 text-gray-400 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {[
                { risk: 'LLM01: Prompt Injection', mitigation: 'Document sanitization + input filtering', status: 'Active' },
                { risk: 'LLM02: Insecure Output', mitigation: 'Evidence Validation Layer G/P/U verification', status: 'Active' },
                { risk: 'LLM03: Training Data Poisoning', mitigation: 'No custom training — foundation models via API', status: 'Mitigated' },
                { risk: 'LLM04: Model DoS', mitigation: 'Rate limiting + multi-model fallback', status: 'Active' },
                { risk: 'LLM06: Sensitive Info Disclosure', mitigation: 'RLS + role-based access + no PII in prompts', status: 'Active' },
                { risk: 'LLM09: Overreliance', mitigation: 'Human override + stage-gate decisions', status: 'Active' },
              ].map((row) => (
                <tr key={row.risk} className="border-t border-gray-700/30">
                  <td className="p-3 text-white font-medium">{row.risk}</td>
                  <td className="p-3 text-gray-400">{row.mitigation}</td>
                  <td className="p-3">
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-bold border bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                      &#10003; {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Generated pack */}
      {data && !loading && (
        <div>
          {/* Pack header (shows in print) */}
          <div className="bg-[#1E293B] rounded-xl border border-gray-700/50 p-6 mb-4">
            <h3 className="text-lg font-bold text-white">DESC Audit Evidence Pack</h3>
            <p className="text-gray-400 text-sm mt-1">
              Generated: {data.generated_at ? new Date(data.generated_at).toLocaleString() : '—'}
              {data.generated_by && <> &middot; By: {data.generated_by}</>}
            </p>
          </div>

          {/* Sections */}
          {SECTION_ORDER.map((key) => {
            const section = data.sections?.[key];
            const meta = SECTION_META[key] || {};
            const renderer = SECTION_RENDERERS[key];
            if (!section || !renderer) return null;

            return (
              <div key={key} className="mb-4 print-section">
                <button
                  onClick={() => toggle(key)}
                  className="no-print w-full flex items-center justify-between bg-[#1E293B] rounded-xl border border-gray-700/50 px-6 py-4 hover:bg-[#253348] transition text-left"
                >
                  <div>
                    <span className="text-[var(--color-accent)] text-xs font-bold uppercase tracking-wide">{meta.label}</span>
                    <h4 className="text-white font-semibold mt-0.5">{meta.subtitle}</h4>
                  </div>
                  <span className="text-gray-500 text-sm">{collapsed[key] ? '\u25B6' : '\u25BC'}</span>
                </button>

                {/* Print-only header */}
                <div className="hidden" style={{ display: 'none' }}>
                  <div className="print-section-header">
                    <p style={{ color: '#0D9488', fontWeight: 700, fontSize: 12 }}>{meta.label}</p>
                    <h4 style={{ fontWeight: 600, fontSize: 16 }}>{meta.subtitle}</h4>
                  </div>
                </div>

                {!collapsed[key] && (
                  <div className="mt-2 px-2">
                    {renderer(section)}
                  </div>
                )}
              </div>
            );
          })}

          {/* Footer */}
          <div className="text-center text-gray-500 text-xs mt-8 mb-4">
            DESC Audit Evidence Pack | AI Smart Sourcing — Dubai Chambers | Powered by Sigma-I |{' '}
            {data.generated_at ? new Date(data.generated_at).toLocaleDateString() : ''} | Confidential
          </div>
        </div>
      )}
    </div>
  );
}

import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { useUserRole } from '../lib/userRole';

const ScoreBadge = ({ score }) => {
  if (score == null) return <span className="text-gray-400 text-sm">—</span>;
  const color = score > 80 ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    : score >= 50 ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    : 'bg-red-500/20 text-red-400 border-red-500/30';
  return (
    <span className={`px-2 py-1 rounded text-xs font-bold border ${color}`}>
      {score}
    </span>
  );
};

const StatusBadge = ({ status }) => {
  if (!status) return <span className="text-gray-400 text-sm">—</span>;
  const styles = {
    compliant: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    partially_compliant: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    non_compliant: 'bg-red-500/20 text-red-400 border-red-500/30',
  };
  return (
    <span className={`px-2 py-1 rounded text-xs font-bold border ${styles[status] || styles.non_compliant}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
};

/* ── Incident severity badge ── */
const SeverityBadge = ({ severity }) => {
  const styles = {
    low: 'bg-gray-500/20 text-gray-300 border-gray-500/30',
    medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    high: 'bg-red-500/20 text-red-400 border-red-500/30',
    critical: 'bg-red-700/30 text-red-300 border-red-700/40',
  };
  return (
    <span className={`px-2 py-1 rounded text-xs font-bold border ${styles[severity] || styles.low}`}>
      {severity}
    </span>
  );
};

/* ── Incident status badge ── */
const IncidentStatusBadge = ({ status }) => {
  const styles = {
    open: 'bg-red-500/20 text-red-400 border-red-500/30',
    investigating: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    contained: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    resolved: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    reported_to_desc: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  };
  return (
    <span className={`px-2 py-1 rounded text-xs font-bold border ${styles[status] || styles.open}`}>
      {status?.replace(/_/g, ' ')}
    </span>
  );
};

/* ── New Incident Form ── */
const NewIncidentForm = ({ onSubmit, onCancel }) => {
  const [form, setForm] = useState({
    title: '',
    description: '',
    severity: 'medium',
    incident_type: 'system_outage',
    affected_systems: '',
    desc_report_required: false,
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit({
        ...form,
        affected_systems: form.affected_systems
          ? form.affected_systems.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
      });
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass = 'w-full bg-[#0F172A] text-gray-200 border border-gray-600 rounded-lg px-3 py-2 text-sm focus:border-[var(--color-accent)] focus:outline-none';

  return (
    <form onSubmit={handleSubmit} className="bg-[#1E293B] rounded-xl border border-gray-700/50 p-6 mb-6">
      <h3 className="text-lg font-semibold text-white mb-4">Report New Incident</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="md:col-span-2">
          <label className="block text-gray-400 text-sm mb-1">Title</label>
          <input type="text" required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className={inputClass} />
        </div>
        <div className="md:col-span-2">
          <label className="block text-gray-400 text-sm mb-1">Description</label>
          <textarea rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className={inputClass} />
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Severity</label>
          <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })} className={inputClass}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
        </div>
        <div>
          <label className="block text-gray-400 text-sm mb-1">Type</label>
          <select value={form.incident_type} onChange={(e) => setForm({ ...form, incident_type: e.target.value })} className={inputClass}>
            <option value="security_breach">Security Breach</option>
            <option value="data_leak">Data Leak</option>
            <option value="system_outage">System Outage</option>
            <option value="ai_anomaly">AI Anomaly</option>
            <option value="compliance_violation">Compliance Violation</option>
            <option value="vendor_issue">Vendor Issue</option>
            <option value="performance_degradation">Performance Degradation</option>
            <option value="unauthorized_access">Unauthorized Access</option>
          </select>
        </div>
        <div className="md:col-span-2">
          <label className="block text-gray-400 text-sm mb-1">Affected Systems (comma-separated)</label>
          <input type="text" value={form.affected_systems} onChange={(e) => setForm({ ...form, affected_systems: e.target.value })} placeholder="e.g. api_gateway, database, rls_policies" className={inputClass} />
        </div>
        <div className="flex items-center gap-2">
          <input type="checkbox" id="desc_required" checked={form.desc_report_required} onChange={(e) => setForm({ ...form, desc_report_required: e.target.checked })} className="rounded" />
          <label htmlFor="desc_required" className="text-gray-400 text-sm">DESC Report Required</label>
        </div>
      </div>
      <div className="flex justify-end gap-3 mt-4">
        <button type="button" onClick={onCancel} className="px-4 py-2 rounded-lg bg-[#0F172A] border border-gray-600 text-gray-300 text-sm hover:bg-[#1a2744] transition">
          Cancel
        </button>
        <button type="submit" disabled={submitting} className="px-4 py-2 rounded-lg bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white text-sm font-semibold transition disabled:opacity-50">
          {submitting ? 'Submitting...' : 'Submit Incident'}
        </button>
      </div>
    </form>
  );
};

const ComplianceAuditsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [audits, setAudits] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [sortBy, setSortBy] = useState('audit_timestamp');
  const [statusFilter, setStatusFilter] = useState('');

  // Incident management state
  const [incidents, setIncidents] = useState([]);
  const [incidentSummary, setIncidentSummary] = useState(null);
  const [incidentLoading, setIncidentLoading] = useState(true);
  const [incidentError, setIncidentError] = useState(null);
  const [expandedIncident, setExpandedIncident] = useState(null);
  const [showNewIncidentForm, setShowNewIncidentForm] = useState(false);
  const { role } = useUserRole();

  const canManageIncidents = role === 'admin' || role === 'compliance_officer';

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20;

  useEffect(() => {
    fetchAudits();
  }, [page, sortBy, statusFilter]);

  useEffect(() => {
    fetchIncidents();
    fetchIncidentSummary();
  }, []);

  const fetchAudits = async () => {
    try {
      setLoading(true);
      setError(null);
      let url = `/api/v1/compliance-audit-results?page=${page}&page_size=${pageSize}&sort_by=${sortBy}`;
      if (statusFilter) url += `&status=${statusFilter}`;
      const res = await api.get(url);
      setAudits(res.data.audits || []);
      setPagination(res.data.pagination);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const fetchIncidents = async () => {
    try {
      setIncidentLoading(true);
      setIncidentError(null);
      const res = await api.get('/api/v1/incidents');
      setIncidents(res.data || []);
    } catch (err) {
      setIncidentError(getErrorMessage(err));
    } finally {
      setIncidentLoading(false);
    }
  };

  const fetchIncidentSummary = async () => {
    try {
      const res = await api.get('/api/v1/incidents/summary');
      setIncidentSummary(res.data);
    } catch {
      // summary is non-critical
    }
  };

  const handleNewIncident = async (data) => {
    try {
      await api.post('/api/v1/incidents', data);
      setShowNewIncidentForm(false);
      fetchIncidents();
      fetchIncidentSummary();
    } catch (err) {
      setIncidentError(getErrorMessage(err));
    }
  };

  const handlePageChange = (newPage) => {
    setSearchParams({ page: newPage.toString() });
  };

  const computeAvgResolution = () => {
    const resolved = incidents.filter((i) => i.resolution_date && i.created_at);
    if (resolved.length === 0) return 'N/A';
    const totalMs = resolved.reduce((acc, i) => {
      return acc + (new Date(i.resolution_date) - new Date(i.created_at));
    }, 0);
    const avgMs = totalMs / resolved.length;
    const avgHours = avgMs / (1000 * 60 * 60);
    if (avgHours < 24) return `${Math.round(avgHours)} hours`;
    return `${Math.round(avgHours / 24)} days`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--color-table-header-bg)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[var(--color-accent)] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading compliance audits...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-table-header-bg)] p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Compliance Audits</h1>
          <div className="flex items-center gap-3">
            <Link
              to="/proposals"
              className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white font-semibold px-5 py-2 rounded-lg transition-colors text-sm"
            >
              Run Audit on Proposal
            </Link>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setSearchParams({ page: '1' }); }}
              className="bg-[#1E293B] text-gray-300 border border-gray-600 rounded-lg px-3 py-2 text-sm"
            >
              <option value="">All Statuses</option>
              <option value="compliant">Compliant</option>
              <option value="partially_compliant">Partially Compliant</option>
              <option value="non_compliant">Non-Compliant</option>
            </select>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-[#1E293B] text-gray-300 border border-gray-600 rounded-lg px-3 py-2 text-sm"
            >
              <option value="audit_timestamp">Sort by Date</option>
              <option value="overall_score">Sort by Score</option>
            </select>
          </div>
        </header>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        <div className="bg-[#1E293B] rounded-xl overflow-hidden border border-gray-700/50">
          <div style={{ overflowX: 'auto', width: '100%' }}>
          <table className="w-full" style={{ minWidth: '900px' }}>
            <thead className="bg-[var(--color-table-header-bg)]">
              <tr>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">Proposal</th>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">Score</th>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">Status</th>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">DESC ISR V3 Controls</th>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">DESC AI Security Policy (5-Phase Lifecycle)</th>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">DESC CSP Standards (ISO/IEC 27001, ISO/IEC 27017, CSA CCM v4.0.5)</th>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">Data Residency</th>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">Date</th>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {audits.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center p-8 text-[#94A3B8]">
                    No compliance audits found
                  </td>
                </tr>
              ) : (
                audits.map((a) => (
                  <tr key={a.id} className="border-t border-gray-700/50 hover:bg-[var(--color-table-header-bg)]">
                    <td className="p-4">
                      <Link to={`/proposals/${a.proposal_id}`} className="text-[#3B82F6] hover:text-blue-300 text-sm font-medium">
                        {a.proposal_title || 'View Proposal'}
                      </Link>
                    </td>
                    <td className="p-4"><ScoreBadge score={a.overall_score} /></td>
                    <td className="p-4"><StatusBadge status={a.overall_status} /></td>
                    <td className="p-4">
                      <span className={a.isr_v3_compliance ? 'text-emerald-400' : 'text-red-400'}>
                        {a.isr_v3_compliance ? 'Pass' : 'Fail'}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={a.ai_security_policy_compliance ? 'text-emerald-400' : 'text-red-400'}>
                        {a.ai_security_policy_compliance ? 'Pass' : 'Fail'}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={a.csp_standards_compliance ? 'text-emerald-400' : 'text-red-400'}>
                        {a.csp_standards_compliance ? 'Pass' : 'Fail'}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className={a.data_residency_verified ? 'text-emerald-400' : 'text-red-400'}>
                        {a.data_residency_verified ? 'Verified' : 'No'}
                      </span>
                    </td>
                    <td className="p-4 text-gray-400 text-sm">
                      {a.audit_timestamp ? new Date(a.audit_timestamp).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="p-4 space-x-2">
                      <Link
                        to={`/compliance-audits/${a.id}`}
                        className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white text-sm font-medium px-3 py-1 rounded transition inline-block"
                      >
                        View Evidence
                      </Link>
                      <a
                        href={`/compliance-audits/${a.id}/report`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="bg-[#1E293B] hover:bg-[#334155] text-gray-300 text-sm font-medium px-3 py-1 rounded transition inline-block border border-gray-600"
                        title="Download Audit Report"
                      >
                        Report
                      </a>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
          </div>
        </div>

        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center space-x-2 mt-6">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
              className="px-4 py-2 rounded-lg bg-[#1E293B] border border-gray-700/50 text-gray-300 disabled:opacity-50 hover:bg-[var(--color-table-header-bg)] transition"
            >
              Previous
            </button>
            <span className="text-gray-400">
              Page {page} of {pagination.total_pages}
            </span>
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page === pagination.total_pages}
              className="px-4 py-2 rounded-lg bg-[#1E293B] border border-gray-700/50 text-gray-300 disabled:opacity-50 hover:bg-[var(--color-table-header-bg)] transition"
            >
              Next
            </button>
          </div>
        )}

        {/* ═══════════════════════════════════════════════════════════
            INCIDENT RESPONSE & DISASTER RECOVERY SECTION
            ═══════════════════════════════════════════════════════════ */}
        <div className="mt-12 border-t border-gray-700/50 pt-10">
          <h2 className="text-2xl font-bold text-white mb-6">Incident Response & Disaster Recovery</h2>

          {/* Summary cards */}
          {incidentSummary && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-[#1E293B] rounded-xl border border-gray-700/50 p-4">
                <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">Open Incidents</p>
                <p className={`text-2xl font-bold ${incidentSummary.open > 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                  {incidentSummary.open}
                </p>
              </div>
              <div className="bg-[#1E293B] rounded-xl border border-gray-700/50 p-4">
                <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">Resolved</p>
                <p className="text-2xl font-bold text-emerald-400">{incidentSummary.resolved}</p>
              </div>
              <div className="bg-[#1E293B] rounded-xl border border-gray-700/50 p-4">
                <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">Reported to DESC</p>
                <p className="text-2xl font-bold text-purple-400">{incidentSummary.reported_to_desc}</p>
              </div>
              <div className="bg-[#1E293B] rounded-xl border border-gray-700/50 p-4">
                <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">Avg Resolution Time</p>
                <p className="text-2xl font-bold text-blue-400">{computeAvgResolution()}</p>
              </div>
            </div>
          )}

          {/* Report new incident button */}
          {canManageIncidents && !showNewIncidentForm && (
            <button
              onClick={() => setShowNewIncidentForm(true)}
              className="mb-6 bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white font-semibold px-5 py-2 rounded-lg transition-colors text-sm"
            >
              Report New Incident
            </button>
          )}

          {/* New incident form */}
          {showNewIncidentForm && (
            <NewIncidentForm
              onSubmit={handleNewIncident}
              onCancel={() => setShowNewIncidentForm(false)}
            />
          )}

          {incidentError && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
              <p className="text-red-400">{incidentError}</p>
            </div>
          )}

          {/* Incidents table */}
          {incidentLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--color-accent)] mx-auto mb-2"></div>
              <p className="text-gray-400 text-sm">Loading incidents...</p>
            </div>
          ) : (
            <div className="bg-[#1E293B] rounded-xl overflow-hidden border border-gray-700/50">
              <div style={{ overflowX: 'auto', width: '100%' }}>
                <table className="w-full" style={{ minWidth: '800px' }}>
                  <thead className="bg-[var(--color-table-header-bg)]">
                    <tr>
                      <th className="text-left p-4 text-gray-400 text-sm font-medium">Date</th>
                      <th className="text-left p-4 text-gray-400 text-sm font-medium">Severity</th>
                      <th className="text-left p-4 text-gray-400 text-sm font-medium">Type</th>
                      <th className="text-left p-4 text-gray-400 text-sm font-medium">Title</th>
                      <th className="text-left p-4 text-gray-400 text-sm font-medium">Status</th>
                      <th className="text-left p-4 text-gray-400 text-sm font-medium">DESC Report</th>
                    </tr>
                  </thead>
                  <tbody>
                    {incidents.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-center p-8 text-[#94A3B8]">
                          No incidents recorded
                        </td>
                      </tr>
                    ) : (
                      incidents.map((inc) => (
                        <React.Fragment key={inc.id}>
                          <tr
                            className="border-t border-gray-700/50 hover:bg-[var(--color-table-header-bg)] cursor-pointer"
                            onClick={() => setExpandedIncident(expandedIncident === inc.id ? null : inc.id)}
                          >
                            <td className="p-4 text-gray-400 text-sm">
                              {inc.created_at ? new Date(inc.created_at).toLocaleDateString() : 'N/A'}
                            </td>
                            <td className="p-4"><SeverityBadge severity={inc.severity} /></td>
                            <td className="p-4 text-gray-300 text-sm">{inc.incident_type?.replace(/_/g, ' ')}</td>
                            <td className="p-4 text-white text-sm font-medium">{inc.title}</td>
                            <td className="p-4"><IncidentStatusBadge status={inc.status} /></td>
                            <td className="p-4">
                              {inc.desc_report_required ? (
                                <span className="text-purple-400 text-sm font-medium">
                                  {inc.desc_reported_at ? 'Reported' : 'Required'}
                                </span>
                              ) : (
                                <span className="text-gray-500 text-sm">N/A</span>
                              )}
                            </td>
                          </tr>
                          {expandedIncident === inc.id && (
                            <tr className="border-t border-gray-700/30">
                              <td colSpan={6} className="p-6 bg-[#0F172A]">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  <div>
                                    <h4 className="text-gray-400 text-xs uppercase tracking-wide mb-1">Description</h4>
                                    <p className="text-gray-300 text-sm">{inc.description || 'No description provided.'}</p>
                                  </div>
                                  <div>
                                    <h4 className="text-gray-400 text-xs uppercase tracking-wide mb-1">Resolution Notes</h4>
                                    <p className="text-gray-300 text-sm">{inc.resolution_notes || 'Pending resolution.'}</p>
                                  </div>
                                  <div>
                                    <h4 className="text-gray-400 text-xs uppercase tracking-wide mb-1">Root Cause</h4>
                                    <p className="text-gray-300 text-sm">{inc.root_cause || 'Under investigation.'}</p>
                                  </div>
                                  <div>
                                    <h4 className="text-gray-400 text-xs uppercase tracking-wide mb-1">Preventive Measures</h4>
                                    <p className="text-gray-300 text-sm">{inc.preventive_measures || 'To be determined.'}</p>
                                  </div>
                                  {inc.affected_systems && inc.affected_systems.length > 0 && (
                                    <div>
                                      <h4 className="text-gray-400 text-xs uppercase tracking-wide mb-1">Affected Systems</h4>
                                      <div className="flex flex-wrap gap-1">
                                        {inc.affected_systems.map((sys) => (
                                          <span key={sys} className="px-2 py-0.5 rounded text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                            {sys}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  <div>
                                    <h4 className="text-gray-400 text-xs uppercase tracking-wide mb-1">DESC Reporting Status</h4>
                                    <p className="text-gray-300 text-sm">
                                      {inc.desc_report_required
                                        ? inc.desc_reported_at
                                          ? `Reported on ${new Date(inc.desc_reported_at).toLocaleDateString()}`
                                          : 'Report required — pending submission'
                                        : 'Not required'}
                                    </p>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* ── Disaster Recovery Status ── */}
          <div className="mt-10">
            <h2 className="text-2xl font-bold text-white mb-4">Disaster Recovery Status</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { label: 'Database Backups', detail: 'Automated daily (Supabase)' },
                { label: 'Infrastructure', detail: 'Auto-healing containers (Railway)' },
                { label: 'Frontend', detail: 'Edge-distributed (Vercel CDN)' },
                { label: 'Data Recovery', detail: 'Point-in-time recovery available' },
                { label: 'RLS Protection', detail: 'Row-level security on all 19 tables' },
              ].map((item) => (
                <div key={item.label} className="bg-[#1E293B] rounded-xl border border-gray-700/50 p-4 flex items-start gap-3">
                  <span className="text-emerald-400 text-lg mt-0.5">&#10003;</span>
                  <div>
                    <p className="text-white text-sm font-medium">{item.label}</p>
                    <p className="text-gray-400 text-xs">{item.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceAuditsList;

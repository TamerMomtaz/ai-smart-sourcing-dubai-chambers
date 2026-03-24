import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

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

const ComplianceAuditsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [audits, setAudits] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [sortBy, setSortBy] = useState('audit_timestamp');
  const [statusFilter, setStatusFilter] = useState('');

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20;

  useEffect(() => {
    fetchAudits();
  }, [page, sortBy, statusFilter]);

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

  const handlePageChange = (newPage) => {
    setSearchParams({ page: newPage.toString() });
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
                <th className="text-left p-4 text-gray-400 text-sm font-medium">ISR v3</th>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">AI Security</th>
                <th className="text-left p-4 text-gray-400 text-sm font-medium">CSP</th>
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
      </div>
    </div>
  );
};

export default ComplianceAuditsList;

import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const ComplianceAuditsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [audits, setAudits] = useState([]);
  const [pagination, setPagination] = useState(null);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20;

  useEffect(() => {
    fetchAudits();
  }, [page]);

  const fetchAudits = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/compliance-audits?page=${page}&page_size=${pageSize}`);
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
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="animate-pulse text-teal font-heading text-2xl">Loading compliance audits...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="font-heading text-4xl text-teal">Compliance Audits</h1>
        </header>

        {error && (
          <div className="bg-burgundy/10 border border-burgundy rounded-lg p-4 mb-6">
            <p className="text-burgundy">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-teal text-white">
              <tr>
                <th className="text-left p-4">Audit ID</th>
                <th className="text-left p-4">Proposal</th>
                <th className="text-left p-4">Type</th>
                <th className="text-left p-4">ISR v3</th>
                <th className="text-left p-4">AI Security</th>
                <th className="text-left p-4">CSP</th>
                <th className="text-left p-4">Remediation</th>
                <th className="text-left p-4">Date</th>
              </tr>
            </thead>
            <tbody>
              {audits.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center p-8 text-ink/60">
                    No compliance audits found
                  </td>
                </tr>
              ) : (
                audits.map((a) => (
                  <tr key={a.id} className="border-b border-cream hover:bg-cream/50">
                    <td className="p-4 font-mono text-xs">{a.id.slice(0, 8)}...</td>
                    <td className="p-4">
                      <Link to={`/proposals/${a.proposal_id}`} className="text-teal hover:underline">
                        View Proposal
                      </Link>
                    </td>
                    <td className="p-4 capitalize">{a.audit_type}</td>
                    <td className="p-4">{a.isr_v3_compliance ? '✅' : '❌'}</td>
                    <td className="p-4">{a.ai_security_policy_compliance ? '✅' : '❌'}</td>
                    <td className="p-4">{a.csp_standards_compliance ? '✅' : '❌'}</td>
                    <td className="p-4">{a.remediation_required ? '⚠️' : '✅'}</td>
                    <td className="p-4">
                      {a.audit_timestamp ? new Date(a.audit_timestamp).toLocaleDateString() : 'N/A'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center space-x-2 mt-6">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
              className="px-4 py-2 rounded-lg bg-white border border-cream disabled:opacity-50 hover:bg-cream transition"
            >
              Previous
            </button>
            <span className="text-ink">
              Page {page} of {pagination.total_pages}
            </span>
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page === pagination.total_pages}
              className="px-4 py-2 rounded-lg bg-white border border-cream disabled:opacity-50 hover:bg-cream transition"
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
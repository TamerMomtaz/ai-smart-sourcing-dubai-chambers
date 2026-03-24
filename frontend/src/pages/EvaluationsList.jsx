import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const TEAL = '#0D9488';

const ShieldIcon = ({ size = 14, color = TEAL }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const ScoreBadge = ({ score }) => {
  if (score == null) return <span className="text-gray-500">—</span>;
  const color = score > 70 ? 'text-emerald-400 bg-emerald-500/20' : score >= 40 ? 'text-amber-400 bg-amber-500/20' : 'text-red-400 bg-red-500/20';
  return <span className={`${color} px-2 py-0.5 rounded-full text-xs font-bold`}>{score.toFixed(1)}</span>;
};

const STATUS_COLORS = {
  evaluated: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  requires_review: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  approved: 'bg-emerald-600/20 text-emerald-300 border-emerald-600/30',
  rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
};

const ShieldBadge = ({ evaluationId }) => {
  const [shieldData, setShieldData] = useState(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    if (evaluationId) fetchShield();
  }, [evaluationId]);

  const fetchShield = async () => {
    try {
      const { data } = await api.get(`/api/v1/evaluations/${evaluationId}/shield`);
      setShieldData(data);
    } catch (err) {
      // Not verified yet — that's fine
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      setVerifying(true);
      const { data } = await api.post(`/api/v1/evaluations/${evaluationId}/verify`);
      setShieldData(data);
    } catch (err) {
      console.error('Shield verify failed:', err);
    } finally {
      setVerifying(false);
    }
  };

  if (verifying) {
    return (
      <span className="flex items-center gap-1 text-xs" style={{ color: TEAL }}>
        <span className="animate-spin inline-block w-3 h-3 border-2 border-teal-400 border-t-transparent rounded-full" />
        Verifying...
      </span>
    );
  }

  if (shieldData) {
    const gs = parseFloat(shieldData.grounding_score) || 0;
    const gsColor = gs >= 85 ? '#10B981' : gs >= 65 ? '#F59E0B' : '#EF4444';
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: `${gsColor}20`, color: gsColor }}>
        <ShieldIcon size={12} color={gsColor} />
        {gs}%
      </span>
    );
  }

  return (
    <button
      onClick={handleVerify}
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border transition-colors hover:bg-teal-500/10"
      style={{ borderColor: `${TEAL}50`, color: TEAL }}
    >
      <ShieldIcon size={12} />
      Verify
    </button>
  );
};

const EvaluationsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [evaluations, setEvaluations] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [sortBy, setSortBy] = useState('evaluated_at');

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20;

  useEffect(() => { fetchEvaluations(); }, [page]);

  const fetchEvaluations = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/api/v1/evaluations?page=${page}&page_size=${pageSize}`);
      setEvaluations(res.data.evaluations || []);
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

  const sortedEvaluations = [...evaluations].sort((a, b) => {
    if (sortBy === 'composite_score') return (b.composite_score || 0) - (a.composite_score || 0);
    return new Date(b.evaluated_at || 0) - new Date(a.evaluated_at || 0);
  });

  return (
    <div className="min-h-screen bg-[#0F172A] p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Evaluations</h1>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-[#1E293B] text-gray-300 border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
          >
            <option value="evaluated_at">Sort by Date</option>
            <option value="composite_score">Sort by Score</option>
          </select>
        </header>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        <div className="bg-[#1E293B] rounded-xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#3B82F6] mx-auto mb-4"></div>
              <p className="text-gray-400">Loading evaluations...</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto', width: '100%' }}>
            <table className="w-full" style={{ minWidth: '900px' }}>
              <thead className="bg-[#0F172A] border-b border-gray-700">
                <tr>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Proposal</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Composite</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Relevance</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Feasibility</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Sector</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Compliance</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Status</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Shield</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Evaluated</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedEvaluations.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="text-center p-12 text-gray-500">No evaluations found</td>
                  </tr>
                ) : (
                  sortedEvaluations.map((ev) => (
                    <tr key={ev.id} className="border-b border-gray-700/50 hover:bg-[#0F172A]/50 transition-colors">
                      <td className="p-4">
                        <Link to={`/proposals/${ev.proposal_id}`} className="text-[#3B82F6] hover:text-blue-300 font-medium">
                          {ev.proposal_title || 'Untitled'}
                        </Link>
                      </td>
                      <td className="p-4"><ScoreBadge score={ev.composite_score} /></td>
                      <td className="p-4"><ScoreBadge score={ev.relevance_score} /></td>
                      <td className="p-4"><ScoreBadge score={ev.feasibility_score} /></td>
                      <td className="p-4"><ScoreBadge score={ev.sector_alignment_score} /></td>
                      <td className="p-4"><ScoreBadge score={ev.compliance_score} /></td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${STATUS_COLORS[ev.proposal_status] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
                          {ev.proposal_status?.replace(/_/g, ' ') || '—'}
                        </span>
                      </td>
                      <td className="p-4">
                        <ShieldBadge evaluationId={ev.id} />
                      </td>
                      <td className="p-4 text-gray-400 text-sm">
                        {ev.evaluated_at ? new Date(ev.evaluated_at).toLocaleDateString() : '—'}
                      </td>
                      <td className="p-4">
                        <Link
                          to={`/evaluations/${ev.id}`}
                          className="text-[#3B82F6] hover:text-blue-300 text-sm font-medium px-3 py-1 rounded border border-[#3B82F6]/30 hover:bg-[#3B82F6]/10 transition"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
            </div>
          )}
        </div>

        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center space-x-3 mt-6">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
              className="px-4 py-2 rounded-lg bg-[#1E293B] text-gray-300 border border-gray-700 disabled:opacity-40 hover:bg-gray-700 transition"
            >
              Previous
            </button>
            <span className="text-gray-400">Page {page} of {pagination.total_pages}</span>
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page === pagination.total_pages}
              className="px-4 py-2 rounded-lg bg-[#1E293B] text-gray-300 border border-gray-700 disabled:opacity-40 hover:bg-gray-700 transition"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvaluationsList;

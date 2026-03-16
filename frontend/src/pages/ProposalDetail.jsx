import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const STATUS_COLORS = {
  queued: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  evaluating: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  evaluated: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  approved: 'bg-emerald-600/20 text-emerald-300 border-emerald-600/30',
  rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
  requires_review: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
};

const ScoreBar = ({ label, score, reasoning }) => {
  const [expanded, setExpanded] = useState(false);
  if (score == null) return null;
  const color = score > 70 ? '#10B981' : score >= 40 ? '#F59E0B' : '#EF4444';
  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1">
        <span className="text-gray-300 font-medium">{label}</span>
        <span className="font-bold" style={{ color }}>{score}/100</span>
      </div>
      <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${score}%`, background: `linear-gradient(90deg, ${color}88, ${color})` }}
        />
      </div>
      {reasoning && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-[#3B82F6] hover:text-blue-300 mt-1"
        >
          {expanded ? '▾ Hide reasoning' : '▸ Show reasoning'}
        </button>
      )}
      {expanded && reasoning && (
        <p className="text-sm text-gray-400 mt-1 pl-2 border-l-2 border-gray-600">{reasoning}</p>
      )}
    </div>
  );
};

const ProposalDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [proposal, setProposal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [showArabic, setShowArabic] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => { fetchProposal(); }, [id]);

  const fetchProposal = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/proposals/${id}`);
      setProposal(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    if (!window.confirm('Run AI evaluation on this proposal?')) return;
    try {
      setActionLoading(true);
      await api.post(`/api/v1/proposals/${id}/evaluate`);
      setToast({ message: 'AI evaluation completed!', type: 'success' });
      await fetchProposal();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      setActionLoading(true);
      await api.patch(`/api/v1/proposals/${id}/status`, { status: newStatus });
      setToast({ message: `Status updated to ${newStatus}`, type: 'success' });
      await fetchProposal();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#3B82F6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading proposal...</p>
        </div>
      </div>
    );
  }

  if (error && !proposal) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-red-400 text-lg">{error}</div>
      </div>
    );
  }

  const evaluation = proposal?.evaluation;
  const aiCost = proposal?.ai_cost;

  return (
    <div className="min-h-screen bg-[#0F172A] p-8">
      {toast && (
        <div className={`fixed top-6 right-6 z-50 ${toast.type === 'success' ? 'bg-emerald-600' : 'bg-red-600'} text-white px-6 py-3 rounded-lg shadow-2xl`}>
          {toast.message}
          <button onClick={() => setToast(null)} className="ml-3 opacity-70 hover:opacity-100">×</button>
        </div>
      )}

      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">{proposal.title}</h1>
          <button onClick={() => navigate('/proposals')} className="text-[#3B82F6] hover:text-blue-300">
            ← Back to Proposals
          </button>
        </div>

        {/* Manual Review Banner */}
        {proposal.requires_manual_review && (
          <div className="mb-6 p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="text-orange-400 font-semibold">Flagged for Manual Review</p>
              <p className="text-orange-300 text-sm">{evaluation?.review_reason || 'This proposal requires human review before proceeding.'}</p>
            </div>
          </div>
        )}

        {/* Proposal Info */}
        <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div>
              <span className="text-gray-500 text-sm">Status</span>
              <div className="mt-1">
                <span className={`px-3 py-1 rounded-full text-xs font-medium border ${STATUS_COLORS[proposal.status] || 'bg-gray-500/20 text-gray-400'}`}>
                  {proposal.status?.replace(/_/g, ' ')}
                </span>
              </div>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Sector</span>
              <p className="text-white font-medium mt-1 capitalize">{proposal.sector}</p>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Technology Type</span>
              <p className="text-white font-medium mt-1">{proposal.technology_type}</p>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Maturity Level</span>
              <p className="text-white font-medium mt-1 capitalize">{proposal.maturity_level}</p>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Language</span>
              <p className="text-white font-medium mt-1">{proposal.language === 'en' ? 'English' : proposal.language === 'ar' ? 'Arabic' : 'Mixed'}</p>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Submitted</span>
              <p className="text-white font-medium mt-1">
                {proposal.submission_date ? new Date(proposal.submission_date).toLocaleDateString() : '—'}
              </p>
            </div>
          </div>
          {proposal.description && (
            <div className="mt-6 pt-4 border-t border-gray-700">
              <span className="text-gray-500 text-sm">Description</span>
              <p className="text-gray-300 mt-1 whitespace-pre-wrap">{proposal.description}</p>
            </div>
          )}
          {proposal.business_group && (
            <div className="mt-4 pt-4 border-t border-gray-700">
              <span className="text-gray-500 text-sm">Business Group</span>
              <p className="text-white font-medium mt-1">{proposal.business_group.name} — {proposal.business_group.chamber}</p>
            </div>
          )}
        </div>

        {/* Evaluation Scores */}
        {(proposal.composite_score != null || evaluation) && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <h3 className="text-xl font-bold text-white mb-6">AI Evaluation Scores</h3>

            {/* Composite Score - Large */}
            <div className="flex items-center justify-center mb-8">
              <div className="text-center">
                <div
                  className="text-6xl font-black"
                  style={{
                    color: (proposal.composite_score || 0) > 70 ? '#10B981' : (proposal.composite_score || 0) >= 40 ? '#F59E0B' : '#EF4444'
                  }}
                >
                  {proposal.composite_score?.toFixed(1) || '—'}
                </div>
                <p className="text-gray-400 text-sm mt-1">Composite Score</p>
              </div>
            </div>

            {/* Score Bars */}
            <ScoreBar
              label="Relevance"
              score={evaluation?.relevance_score ?? proposal.relevance_score}
              reasoning={evaluation?.relevance_reasoning}
            />
            <ScoreBar
              label="Feasibility"
              score={evaluation?.feasibility_score ?? proposal.feasibility_score}
              reasoning={evaluation?.feasibility_reasoning}
            />
            <ScoreBar
              label="Sector Alignment"
              score={evaluation?.sector_alignment_score ?? proposal.sector_alignment_score}
              reasoning={evaluation?.sector_reasoning}
            />
            <ScoreBar
              label="Compliance"
              score={evaluation?.compliance_score ?? proposal.compliance_score}
              reasoning={evaluation?.compliance_reasoning}
            />
          </div>
        )}

        {/* Executive Summary */}
        {evaluation && (evaluation.summary_en || evaluation.summary_ar) && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Executive Summary</h3>
              {evaluation.summary_ar && (
                <button
                  onClick={() => setShowArabic(!showArabic)}
                  className="text-sm text-[#3B82F6] hover:text-blue-300 px-3 py-1 border border-[#3B82F6]/30 rounded"
                >
                  {showArabic ? 'English' : 'العربية'}
                </button>
              )}
            </div>
            {showArabic && evaluation.summary_ar ? (
              <p className="text-gray-300 leading-relaxed" dir="rtl">{evaluation.summary_ar}</p>
            ) : (
              <p className="text-gray-300 leading-relaxed">{evaluation.summary_en}</p>
            )}
          </div>
        )}

        {/* AI Cost / ΣI */}
        {aiCost && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <h3 className="text-xl font-bold text-white mb-4">ΣI — Evaluation Cost</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-[#3B82F6]">{(aiCost.prompt_tokens + aiCost.completion_tokens).toLocaleString()}</p>
                <p className="text-gray-500 text-xs mt-1">Total Tokens</p>
              </div>
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-[#F59E0B]">${parseFloat(aiCost.cost_usd).toFixed(4)}</p>
                <p className="text-gray-500 text-xs mt-1">Cost (USD)</p>
              </div>
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-[#10B981]">{parseFloat(aiCost.energy_kwh).toFixed(6)}</p>
                <p className="text-gray-500 text-xs mt-1">Energy (kWh)</p>
              </div>
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-gray-300">{aiCost.latency_ms}ms</p>
                <p className="text-gray-500 text-xs mt-1">Latency</p>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-700/50">
          <div className="flex gap-3 flex-wrap">
            {(proposal.status === 'queued' || proposal.status === 'requires_review') && (
              <button
                onClick={handleEvaluate}
                disabled={actionLoading}
                className="bg-[#3B82F6] hover:bg-blue-600 text-white px-6 py-2.5 rounded-lg font-semibold disabled:opacity-50 transition-colors"
              >
                {actionLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-pulse">🧠</span> AI is evaluating... ~15s
                  </span>
                ) : proposal.status === 'requires_review' ? 'Re-evaluate' : 'Run AI Evaluation'}
              </button>
            )}
            <button
              onClick={() => handleStatusChange('approved')}
              disabled={actionLoading}
              className="bg-[#10B981] hover:bg-emerald-600 text-white px-6 py-2.5 rounded-lg font-semibold disabled:opacity-50 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => handleStatusChange('rejected')}
              disabled={actionLoading}
              className="bg-[#EF4444] hover:bg-red-600 text-white px-6 py-2.5 rounded-lg font-semibold disabled:opacity-50 transition-colors"
            >
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProposalDetail;

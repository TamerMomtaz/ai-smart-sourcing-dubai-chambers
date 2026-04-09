import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const TEAL = 'var(--color-accent)';

/* ── Score helpers ── */
const scoreColor = (s) => {
  if (s == null) return '#6B7280';
  return s > 70 ? '#10B981' : s >= 40 ? '#F59E0B' : '#EF4444';
};

const ScoreBar = ({ score, label, maxWidth = '100%' }) => {
  if (score == null) return <div className="text-gray-500 text-xs">--</div>;
  const color = scoreColor(score);
  return (
    <div style={{ maxWidth }}>
      <div className="flex justify-between items-center mb-0.5">
        <span className="text-gray-400 text-[11px]">{label}</span>
        <span className="text-[11px] font-bold" style={{ color }}>{score.toFixed(1)}</span>
      </div>
      <div className="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${score}%`, backgroundColor: color }} />
      </div>
    </div>
  );
};

const CompositeScore = ({ score }) => {
  if (score == null) return <span className="text-gray-500 text-2xl">--</span>;
  const color = scoreColor(score);
  return (
    <span className="font-bold text-3xl" style={{ color, fontFamily: '"JetBrains Mono", monospace' }}>
      {score.toFixed(1)}
    </span>
  );
};

const GateBadge = ({ status }) => {
  if (!status) return <span className="text-gray-500 text-xs">N/A</span>;
  const styles = {
    passed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    pass: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    compliant: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    conditional: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    partially_compliant: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
    fail: 'bg-red-500/20 text-red-400 border-red-500/30',
    non_compliant: 'bg-red-500/20 text-red-400 border-red-500/30',
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-bold border ${styles[status] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
};

const VScoreBadge = ({ score, tier }) => {
  if (score == null) return <span className="text-gray-500 text-xs">N/A</span>;
  const tierColors = {
    platinum: '#0D9488',
    gold: '#B8904A',
    silver: '#3B82F6',
    bronze: '#F59E0B',
    under_review: '#EF4444',
  };
  const color = tierColors[tier] || '#94A3B8';
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: `${color}20`, color }}>
      {score} {tier && `(${tier})`}
    </span>
  );
};

const ShieldIcon = ({ size = 14, color = TEAL }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const GroundingBadge = ({ score }) => {
  if (score == null) return <span className="text-gray-500 text-xs">Not verified</span>;
  const gs = parseFloat(score) || 0;
  const color = gs >= 85 ? '#10B981' : gs >= 65 ? '#F59E0B' : '#EF4444';
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: `${color}20`, color }}>
      <ShieldIcon size={12} color={color} />
      {gs}%
    </span>
  );
};

/* ── Proposal Column ── */
const ProposalColumn = ({ proposal, navigate }) => {
  const recommendation = proposal.ai_recommendation
    ? proposal.ai_recommendation.substring(0, 100) + (proposal.ai_recommendation.length > 100 ? '...' : '')
    : null;

  return (
    <div className="bg-[#1E293B] rounded-xl border border-gray-700/50 p-5 flex flex-col gap-4 min-w-[240px]">
      {/* Title + vendor */}
      <div>
        <h3 className="text-white font-semibold text-sm mb-1 line-clamp-2">{proposal.title}</h3>
        <p className="text-gray-400 text-xs">{proposal.vendor_name}</p>
      </div>

      {/* Composite score */}
      <div className="text-center py-2">
        <CompositeScore score={proposal.composite_score} />
        <p className="text-gray-500 text-[10px] mt-1">Composite Score</p>
      </div>

      {/* 5 dimension bars */}
      <div className="space-y-2">
        <ScoreBar score={proposal.relevance_score} label="Relevance" />
        <ScoreBar score={proposal.feasibility_score} label="Feasibility" />
        <ScoreBar score={proposal.sector_alignment_score} label="Sector Alignment" />
        <ScoreBar score={proposal.compliance_score} label="Compliance" />
        <ScoreBar score={proposal.innovation_score} label="Innovation" />
      </div>

      {/* Gate + grounding + vScore */}
      <div className="space-y-2 pt-2 border-t border-gray-700/30">
        <div className="flex items-center justify-between">
          <span className="text-gray-400 text-[11px]">Compliance Gate</span>
          <GateBadge status={proposal.gate_status} />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-gray-400 text-[11px]">Evidence Grounding</span>
          <GroundingBadge score={proposal.grounding_score} />
        </div>
        <div className="flex items-center justify-between">
          <span className="text-gray-400 text-[11px]">Vendor vScore</span>
          <VScoreBadge score={proposal.vscore} tier={proposal.vscore_tier} />
        </div>
      </div>

      {/* AI recommendation excerpt */}
      {recommendation && (
        <div className="pt-2 border-t border-gray-700/30">
          <p className="text-gray-500 text-[10px] mb-1">AI Recommendation</p>
          <p className="text-gray-300 text-xs leading-relaxed">{recommendation}</p>
        </div>
      )}

      {/* View Full Evaluation link */}
      <button
        onClick={() => navigate(`/proposals/${proposal.id}`)}
        className="text-[var(--color-accent)] text-xs hover:underline text-left mt-auto"
      >
        View Full Evaluation →
      </button>
    </div>
  );
};

/* ── Main Component ── */
const CaseProposalComparison = () => {
  const { caseId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [caseInfo, setCaseInfo] = useState(null);
  const [allProposals, setAllProposals] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [aiSummary, setAiSummary] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState(null);

  useEffect(() => {
    fetchComparisonData();
  }, [caseId]);

  const fetchComparisonData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/api/v1/sourcing-cases/${caseId}/compare-proposals`);
      setCaseInfo(res.data.case);
      setAllProposals(res.data.proposals || []);
      // Auto-select first 4 (or fewer)
      const autoSelect = (res.data.proposals || []).slice(0, 4).map(p => p.id);
      setSelectedIds(autoSelect);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const toggleProposal = (id) => {
    setSelectedIds(prev => {
      if (prev.includes(id)) return prev.filter(x => x !== id);
      if (prev.length >= 4) return prev;
      return [...prev, id];
    });
    setAiSummary(null);
  };

  const selectedProposals = allProposals.filter(p => selectedIds.includes(p.id));

  const handleAISummary = async () => {
    if (selectedIds.length < 2) return;
    try {
      setAiLoading(true);
      setAiError(null);
      const res = await api.post(`/api/v1/sourcing-cases/${caseId}/compare-proposals/ai-summary`, {
        proposal_ids: selectedIds,
      });
      setAiSummary(res.data.summary);
    } catch (err) {
      setAiError(getErrorMessage(err));
    } finally {
      setAiLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--color-table-header-bg)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[var(--color-accent)] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading comparison data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[var(--color-table-header-bg)] p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
            <p className="text-red-400">{error}</p>
          </div>
          <button onClick={() => navigate('/sourcing-cases')} className="mt-4 text-gray-400 hover:text-white text-sm">
            ← Back to Sourcing Cases
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-table-header-bg)] p-4 md:p-8">
      <div className="max-w-[1400px] mx-auto">
        {/* Top bar: case context */}
        <header className="mb-6">
          <button
            onClick={() => navigate('/sourcing-cases')}
            className="text-gray-400 hover:text-white text-sm mb-3 inline-block"
          >
            ← Back to Sourcing Cases
          </button>
          <div className="bg-[#1E293B] rounded-xl p-5 border border-gray-700/50">
            <h1 className="text-xl md:text-2xl font-bold text-white mb-2">
              Compare Proposals
            </h1>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-[var(--color-accent)] text-sm font-medium">{caseInfo?.title}</span>
              {caseInfo?.sector && (
                <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-500/15 text-blue-400 border border-blue-500/30">
                  {caseInfo.sector}
                </span>
              )}
            </div>
            {caseInfo?.problem_statement && (
              <p className="text-gray-400 text-sm line-clamp-2">{caseInfo.problem_statement}</p>
            )}
          </div>
        </header>

        {/* Proposal selector */}
        <div className="bg-[#1E293B] rounded-xl p-4 border border-gray-700/50 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-white text-sm font-semibold">
              Select proposals to compare (max 4)
            </h2>
            <span className="text-gray-400 text-xs">
              {selectedIds.length} of {Math.min(allProposals.length, 4)} selected
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            {allProposals.map(p => {
              const isSelected = selectedIds.includes(p.id);
              const isDisabled = !isSelected && selectedIds.length >= 4;
              return (
                <button
                  key={p.id}
                  onClick={() => !isDisabled && toggleProposal(p.id)}
                  disabled={isDisabled}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    isSelected
                      ? 'border-[var(--color-accent)] bg-accent-10 text-white'
                      : isDisabled
                      ? 'border-gray-700/30 bg-gray-800/50 text-gray-600 cursor-not-allowed'
                      : 'border-gray-700/50 bg-[#0F172A] text-gray-300 hover:border-gray-600'
                  }`}
                >
                  {isSelected && (
                    <span className="inline-block mr-1.5 text-[var(--color-accent)]">✓</span>
                  )}
                  {p.title}
                  {p.composite_score != null && (
                    <span className="ml-2 opacity-70">({p.composite_score.toFixed(1)})</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Side-by-side columns */}
        {selectedProposals.length === 0 ? (
          <div className="bg-[#1E293B] rounded-xl p-12 text-center border border-gray-700/50">
            <p className="text-gray-400">Select at least 2 proposals to compare.</p>
          </div>
        ) : (
          <div
            className="grid gap-4 mb-6"
            style={{ gridTemplateColumns: `repeat(${selectedProposals.length}, minmax(240px, 1fr))` }}
          >
            {selectedProposals.map(p => (
              <ProposalColumn key={p.id} proposal={p} navigate={navigate} />
            ))}
          </div>
        )}

        {/* AI Comparison Summary */}
        {selectedIds.length >= 2 && (
          <div className="bg-[#1E293B] rounded-xl p-5 border border-gray-700/50">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-white font-semibold text-lg">AI Comparison Summary</h2>
              <button
                onClick={handleAISummary}
                disabled={aiLoading || selectedIds.length < 2}
                className="px-5 py-2 rounded-lg font-medium text-sm text-white transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ backgroundColor: aiLoading ? '#374151' : 'var(--color-accent)' }}
              >
                {aiLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                    Analyzing...
                  </span>
                ) : (
                  `Compare ${selectedIds.length} Proposals with AI`
                )}
              </button>
            </div>
            {aiError && (
              <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 mb-4">
                <p className="text-red-400 text-sm">{aiError}</p>
              </div>
            )}
            {aiSummary && (
              <div className="bg-[#0F172A] rounded-lg p-4 border border-gray-700/30">
                <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">{aiSummary}</p>
              </div>
            )}
            {!aiSummary && !aiLoading && !aiError && (
              <p className="text-gray-500 text-sm">
                Click the button above to generate an AI-powered comparison of the selected proposals.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CaseProposalComparison;

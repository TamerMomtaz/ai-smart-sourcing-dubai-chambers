import React, { useEffect, useState } from 'react';
import api, { getErrorMessage } from '../lib/api';

const TEAL = 'var(--color-accent)';

const ShieldIcon = ({ size = 14, color = TEAL }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const ScoreBar = ({ score, label }) => {
  if (score == null) return <div className="text-gray-500 text-sm">—</div>;
  const color = score > 70 ? '#10B981' : score >= 40 ? '#F59E0B' : '#EF4444';
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-gray-400 text-xs">{label}</span>
        <span className="text-xs font-bold" style={{ color }}>{score.toFixed(1)}</span>
      </div>
      <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${score}%`, backgroundColor: color }} />
      </div>
    </div>
  );
};

const ScoreBadge = ({ score, large }) => {
  if (score == null) return <span className="text-gray-500">—</span>;
  const color = score > 70 ? '#10B981' : score >= 40 ? '#F59E0B' : '#EF4444';
  return (
    <span className={`font-bold ${large ? 'text-3xl' : 'text-lg'}`} style={{ color, fontFamily: '"JetBrains Mono", monospace' }}>
      {score.toFixed(1)}
    </span>
  );
};

const ComplianceBadge = ({ status }) => {
  if (!status) return <span className="text-gray-500 text-xs">—</span>;
  const styles = {
    compliant: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    partially_compliant: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    non_compliant: 'bg-red-500/20 text-red-400 border-red-500/30',
  };
  return (
    <span className={`px-2 py-1 rounded text-xs font-bold border ${styles[status] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
};

const ShieldBadge = ({ shieldData }) => {
  if (!shieldData) return <span className="text-gray-500 text-xs">Not verified</span>;
  const gs = parseFloat(shieldData.grounding_score) || 0;
  const color = gs >= 85 ? '#10B981' : gs >= 65 ? '#F59E0B' : '#EF4444';
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: `${color}20`, color }}>
      <ShieldIcon size={12} color={color} />
      {gs}%
    </span>
  );
};

const WinnerBadge = () => (
  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
    Best
  </span>
);

/* ─── Selection Card ─── */
const SelectionCard = ({ proposal, selected, onToggle, evaluation, shieldData }) => {
  const compositeScore = evaluation?.composite_score;
  const gs = shieldData ? parseFloat(shieldData.grounding_score) || null : null;

  return (
    <div
      onClick={onToggle}
      className={`relative cursor-pointer rounded-xl p-5 border-2 transition-all duration-200 ${
        selected
          ? 'border-[var(--color-accent)] bg-accent-10 shadow-lg shadow-accent-10'
          : 'border-gray-700/50 bg-[#1E293B] hover:border-gray-600'
      }`}
    >
      {selected && (
        <div className="absolute top-3 right-3 w-6 h-6 rounded-full bg-[var(--color-accent)] flex items-center justify-center">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </div>
      )}
      <h3 className="text-white font-semibold text-sm mb-2 pr-8">{proposal.title}</h3>
      <p className="text-gray-400 text-xs capitalize mb-3">{proposal.sector}</p>
      <div className="flex items-center gap-4">
        {compositeScore != null && (
          <div className="flex items-center gap-1.5">
            <span className="text-gray-500 text-xs">Score:</span>
            <span className={`text-xs font-bold ${compositeScore > 70 ? 'text-emerald-400' : compositeScore >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
              {compositeScore.toFixed(1)}
            </span>
          </div>
        )}
        {gs != null && (
          <div className="flex items-center gap-1">
            <ShieldIcon size={11} color={gs >= 85 ? '#10B981' : gs >= 65 ? '#F59E0B' : '#EF4444'} />
            <span className="text-xs font-bold" style={{ color: gs >= 85 ? '#10B981' : gs >= 65 ? '#F59E0B' : '#EF4444' }}>
              {gs}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

/* ─── Comparison Row ─── */
const ComparisonRow = ({ label, values, highlight }) => {
  const best = highlight ? Math.max(...values.filter(v => v != null)) : null;
  return (
    <div className="grid gap-4 items-center border-b border-gray-700/30 py-3" style={{ gridTemplateColumns: `160px repeat(${values.length}, 1fr)` }}>
      <div className="text-gray-400 text-sm font-medium">{label}</div>
      {values.map((val, i) => (
        <div key={i} className="flex items-center gap-2">
          {val != null ? (
            <>
              <span className={`text-sm font-bold ${val > 70 ? 'text-emerald-400' : val >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                {typeof val === 'number' ? val.toFixed(1) : val}
              </span>
              {highlight && val === best && values.filter(v => v === best).length === 1 && <WinnerBadge />}
            </>
          ) : (
            <span className="text-gray-500 text-sm">—</span>
          )}
        </div>
      ))}
    </div>
  );
};

/* ─── Main Component ─── */
const ProposalCompare = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [evaluationMap, setEvaluationMap] = useState({});
  const [shieldMap, setShieldMap] = useState({});
  const [complianceMap, setComplianceMap] = useState({});
  const [selectedIds, setSelectedIds] = useState([]);
  const [comparing, setComparing] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Fetch all evaluated proposals
  useEffect(() => {
    fetchEvaluatedProposals();
  }, []);

  const fetchEvaluatedProposals = async () => {
    try {
      setLoading(true);
      setError(null);
      // Get evaluations (which include proposal info)
      const res = await api.get('/api/v1/evaluations?page=1&page_size=100');
      const evals = res.data.evaluations || [];

      // Build a map of proposal_id -> evaluation
      const evalMap = {};
      const proposalIds = new Set();
      for (const ev of evals) {
        if (ev.proposal_id && !evalMap[ev.proposal_id]) {
          evalMap[ev.proposal_id] = ev;
          proposalIds.add(ev.proposal_id);
        }
      }
      setEvaluationMap(evalMap);

      // Fetch proposals for those IDs
      const proposalRes = await api.get('/api/v1/proposals?page=1&page_size=100');
      const allProposals = proposalRes.data.proposals || [];
      // Only show proposals that have evaluations
      const evaluated = allProposals.filter(p => proposalIds.has(p.id));
      setProposals(evaluated);

      // Fetch shield data for each evaluation (in parallel, non-blocking)
      const shieldPromises = evals.map(async (ev) => {
        try {
          const { data } = await api.get(`/api/v1/evaluations/${ev.id}/shield`);
          return { proposalId: ev.proposal_id, data };
        } catch {
          return { proposalId: ev.proposal_id, data: null };
        }
      });
      const shields = await Promise.all(shieldPromises);
      const sMap = {};
      for (const s of shields) {
        if (s.data) sMap[s.proposalId] = s.data;
      }
      setShieldMap(sMap);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const toggleSelect = (proposalId) => {
    setSelectedIds(prev => {
      if (prev.includes(proposalId)) {
        return prev.filter(id => id !== proposalId);
      }
      if (prev.length >= 3) return prev; // max 3
      return [...prev, proposalId];
    });
  };

  const handleCompare = async () => {
    setLoadingDetails(true);
    try {
      // Fetch compliance audits for selected proposals
      const compPromises = selectedIds.map(async (pid) => {
        try {
          const res = await api.get(`/api/v1/compliance-audit-results?page=1&page_size=5`);
          const audits = res.data.audits || [];
          const match = audits.find(a => a.proposal_id === pid);
          return { proposalId: pid, data: match || null };
        } catch {
          return { proposalId: pid, data: null };
        }
      });
      const compliances = await Promise.all(compPromises);
      const cMap = {};
      for (const c of compliances) {
        if (c.data) cMap[c.proposalId] = c.data;
      }
      setComplianceMap(cMap);
    } catch (err) {
      console.error('Error loading comparison details:', err);
    } finally {
      setLoadingDetails(false);
      setComparing(true);
    }
  };

  const handleBack = () => {
    setComparing(false);
  };

  const handleReset = () => {
    setSelectedIds([]);
    setComparing(false);
    setComplianceMap({});
  };

  // ─── Selection Mode ───
  if (!comparing) {
    return (
      <div className="min-h-screen bg-[var(--color-table-header-bg)] p-4 md:p-8">
        <div className="max-w-7xl mx-auto">
          <header className="mb-6">
            <h1 className="text-2xl md:text-3xl font-bold text-white mb-2">Compare Proposals</h1>
            <p className="text-gray-400 text-sm">
              Select 2 or 3 evaluated proposals to compare their scores, shield results, and compliance side by side.
            </p>
          </header>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
              <p className="text-red-400">{error}</p>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[var(--color-accent)] mx-auto mb-4"></div>
                <p className="text-gray-400">Loading evaluated proposals...</p>
              </div>
            </div>
          ) : proposals.length === 0 ? (
            <div className="bg-[#1E293B] rounded-xl p-12 text-center border border-gray-700/50">
              <p className="text-gray-400 text-lg mb-2">No evaluated proposals found</p>
              <p className="text-gray-500 text-sm">Proposals need to be evaluated before they can be compared.</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-24">
                {proposals.map((p) => (
                  <SelectionCard
                    key={p.id}
                    proposal={p}
                    selected={selectedIds.includes(p.id)}
                    onToggle={() => toggleSelect(p.id)}
                    evaluation={evaluationMap[p.id]}
                    shieldData={shieldMap[p.id]}
                  />
                ))}
              </div>

              {/* Floating compare bar */}
              <div className="fixed bottom-0 left-0 right-0 z-40 md:pl-64">
                <div className="bg-[#1E293B]/95 backdrop-blur-sm border-t border-gray-700/50 px-6 py-4">
                  <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="text-gray-300 text-sm">
                      <span className="font-bold text-white">{selectedIds.length}</span> of 3 proposals selected
                      {selectedIds.length > 0 && selectedIds.length < 2 && (
                        <span className="text-gray-500 ml-2">— select at least 2</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3">
                      {selectedIds.length > 0 && (
                        <button
                          onClick={handleReset}
                          className="px-4 py-2 text-gray-400 hover:text-white text-sm transition-colors"
                        >
                          Clear
                        </button>
                      )}
                      <button
                        onClick={handleCompare}
                        disabled={selectedIds.length < 2}
                        className="px-6 py-2.5 rounded-lg font-medium text-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                        style={{
                          backgroundColor: selectedIds.length >= 2 ? TEAL : '#374151',
                          color: 'white',
                        }}
                      >
                        {loadingDetails ? (
                          <span className="flex items-center gap-2">
                            <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                            Loading...
                          </span>
                        ) : (
                          `Compare ${selectedIds.length} proposal${selectedIds.length !== 1 ? 's' : ''}`
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    );
  }

  // ─── Comparison View ───
  const selected = selectedIds.map(id => ({
    proposal: proposals.find(p => p.id === id),
    evaluation: evaluationMap[id],
    shield: shieldMap[id] || null,
    compliance: complianceMap[id] || null,
  }));

  const colCount = selected.length;

  return (
    <div className="min-h-screen bg-[var(--color-table-header-bg)] p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-white mb-1">Proposal Comparison</h1>
            <p className="text-gray-400 text-sm">Side-by-side analysis of {colCount} proposals</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleBack}
              className="px-4 py-2 text-gray-400 hover:text-white text-sm border border-gray-700 rounded-lg transition-colors"
            >
              ← Back to Selection
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm rounded-lg transition-colors"
              style={{ backgroundColor: TEAL, color: 'white' }}
            >
              New Comparison
            </button>
          </div>
        </header>

        {/* Proposal Headers — mobile stacked */}
        <div className="md:hidden grid grid-cols-1 gap-4 mb-6">
          {selected.map(({ proposal, evaluation, shield }) => (
            <div key={proposal.id} className="bg-[#1E293B] rounded-xl p-5 border border-gray-700/50">
              <h3 className="text-white font-semibold text-base mb-1">{proposal.title}</h3>
              <p className="text-gray-400 text-xs capitalize mb-3">{proposal.sector}</p>
              <div className="flex items-center gap-3">
                <ScoreBadge score={evaluation?.composite_score} large />
                {shield && <ShieldBadge shieldData={shield} />}
              </div>
            </div>
          ))}
        </div>
        {/* Proposal Headers — desktop grid */}
        <div className="hidden md:grid gap-4 mb-6" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
          <div></div>
          {selected.map(({ proposal, evaluation, shield }) => (
            <div key={proposal.id} className="bg-[#1E293B] rounded-xl p-5 border border-gray-700/50">
              <h3 className="text-white font-semibold text-base mb-1">{proposal.title}</h3>
              <p className="text-gray-400 text-xs capitalize mb-3">{proposal.sector}</p>
              <div className="flex items-center gap-3">
                <ScoreBadge score={evaluation?.composite_score} large />
                {shield && <ShieldBadge shieldData={shield} />}
              </div>
            </div>
          ))}
        </div>

        {/* Scores Section */}
        <div className="bg-[#1E293B] rounded-xl p-4 md:p-6 border border-gray-700/50 mb-6 overflow-x-auto">
          <h3 className="text-white font-semibold text-lg mb-4">Score Breakdown</h3>
          <ComparisonRow
            label="Composite Score"
            values={selected.map(s => s.evaluation?.composite_score)}
            highlight
          />
          <ComparisonRow
            label="Relevance"
            values={selected.map(s => s.evaluation?.relevance_score)}
            highlight
          />
          <ComparisonRow
            label="Feasibility"
            values={selected.map(s => s.evaluation?.feasibility_score)}
            highlight
          />
          <ComparisonRow
            label="Sector Alignment"
            values={selected.map(s => s.evaluation?.sector_alignment_score)}
            highlight
          />
          <ComparisonRow
            label="Compliance"
            values={selected.map(s => s.evaluation?.compliance_score)}
            highlight
          />
        </div>

        {/* Visual Score Bars */}
        <div className="bg-[#1E293B] rounded-xl p-4 md:p-6 border border-gray-700/50 mb-6 overflow-x-auto">
          <h3 className="text-white font-semibold text-lg mb-4">Visual Comparison</h3>
          <div className="grid gap-6" style={{ gridTemplateColumns: `repeat(${colCount}, minmax(200px, 1fr))` }}>
            {selected.map(({ proposal, evaluation }) => (
              <div key={proposal.id}>
                <p className="text-gray-300 text-sm font-medium mb-3 truncate">{proposal.title}</p>
                <div className="space-y-3">
                  <ScoreBar score={evaluation?.relevance_score} label="Relevance" />
                  <ScoreBar score={evaluation?.feasibility_score} label="Feasibility" />
                  <ScoreBar score={evaluation?.sector_alignment_score} label="Sector" />
                  <ScoreBar score={evaluation?.compliance_score} label="Compliance" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Shield Results */}
        <div className="bg-[#1E293B] rounded-xl p-4 md:p-6 border border-gray-700/50 mb-6 overflow-x-auto">
          <div className="flex items-center gap-2 mb-4">
            <ShieldIcon size={18} color={TEAL} />
            <h3 className="text-white font-semibold text-lg">Evidence Validation Layer</h3>
          </div>
          <div className="grid gap-4" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Evidence Grounding Score</div>
            {selected.map(({ proposal, shield }) => (
              <div key={proposal.id}>
                {shield ? (
                  <ShieldBadge shieldData={shield} />
                ) : (
                  <span className="text-gray-500 text-xs">Not verified</span>
                )}
              </div>
            ))}
          </div>
          <div className="grid gap-4 mt-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Risk Level</div>
            {selected.map(({ proposal, shield }) => (
              <div key={proposal.id}>
                {shield ? (
                  <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                    shield.hallucination_risk === 'low' ? 'bg-emerald-500/20 text-emerald-400' :
                    shield.hallucination_risk === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                    'bg-red-500/20 text-red-400'
                  }`}>
                    {shield.hallucination_risk?.toUpperCase()}
                  </span>
                ) : (
                  <span className="text-gray-500 text-xs">—</span>
                )}
              </div>
            ))}
          </div>
          <div className="grid gap-4 mt-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Claims Verified</div>
            {selected.map(({ proposal, shield }) => (
              <div key={proposal.id}>
                {shield ? (
                  <span className="text-white text-sm font-mono">
                    {shield.grounded_claims}/{shield.total_claims}
                  </span>
                ) : (
                  <span className="text-gray-500 text-xs">—</span>
                )}
              </div>
            ))}
          </div>
          <div className="grid gap-4 mt-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Score Deviation</div>
            {selected.map(({ proposal, shield }) => (
              <div key={proposal.id}>
                {shield?.score_deviation != null ? (
                  <span className={`text-sm font-bold ${shield.deviation_within_threshold ? 'text-emerald-400' : 'text-red-400'}`}>
                    {parseFloat(shield.score_deviation).toFixed(1)}%
                    {shield.deviation_within_threshold ? ' (OK)' : ' (!)'}
                  </span>
                ) : (
                  <span className="text-gray-500 text-xs">—</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Compliance Audits */}
        <div className="bg-[#1E293B] rounded-xl p-4 md:p-6 border border-gray-700/50 mb-6 overflow-x-auto">
          <h3 className="text-white font-semibold text-lg mb-4">Compliance Status</h3>
          <div className="grid gap-4" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Status</div>
            {selected.map(({ proposal, compliance }) => (
              <div key={proposal.id}>
                <ComplianceBadge status={compliance?.compliance_status} />
              </div>
            ))}
          </div>
          <div className="grid gap-4 mt-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Score</div>
            {selected.map(({ proposal, compliance }) => (
              <div key={proposal.id}>
                {compliance?.compliance_score != null ? (
                  <span className={`text-sm font-bold ${compliance.compliance_score > 70 ? 'text-emerald-400' : compliance.compliance_score >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                    {compliance.compliance_score}
                  </span>
                ) : (
                  <span className="text-gray-500 text-xs">—</span>
                )}
              </div>
            ))}
          </div>
          <div className="grid gap-4 mt-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Framework</div>
            {selected.map(({ proposal, compliance }) => (
              <div key={proposal.id}>
                {compliance?.framework ? (
                  <span className="text-gray-300 text-sm">{compliance.framework}</span>
                ) : (
                  <span className="text-gray-500 text-xs">—</span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Proposal Details */}
        <div className="bg-[#1E293B] rounded-xl p-4 md:p-6 border border-gray-700/50 mb-6 overflow-x-auto">
          <h3 className="text-white font-semibold text-lg mb-4">Proposal Details</h3>
          <ComparisonRow
            label="Status"
            values={selected.map(s => s.evaluation?.proposal_status?.replace(/_/g, ' ') || '—')}
          />
          <div className="grid gap-4 items-center border-b border-gray-700/30 py-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Sector</div>
            {selected.map(({ proposal }) => (
              <div key={proposal.id} className="text-gray-300 text-sm capitalize">{proposal.sector || '—'}</div>
            ))}
          </div>
          <div className="grid gap-4 items-center border-b border-gray-700/30 py-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Technology</div>
            {selected.map(({ proposal }) => (
              <div key={proposal.id} className="text-gray-300 text-sm">{proposal.technology_type || '—'}</div>
            ))}
          </div>
          <div className="grid gap-4 items-center border-b border-gray-700/30 py-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Maturity</div>
            {selected.map(({ proposal }) => (
              <div key={proposal.id} className="text-gray-300 text-sm capitalize">{proposal.maturity_level || '—'}</div>
            ))}
          </div>
          <div className="grid gap-4 items-center py-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Evaluated</div>
            {selected.map(({ proposal, evaluation }) => (
              <div key={proposal.id} className="text-gray-400 text-sm">
                {evaluation?.evaluated_at ? new Date(evaluation.evaluated_at).toLocaleDateString() : '—'}
              </div>
            ))}
          </div>
        </div>

        {/* Safety Checks */}
        <div className="bg-[#1E293B] rounded-xl p-4 md:p-6 border border-gray-700/50 overflow-x-auto">
          <h3 className="text-white font-semibold text-lg mb-4">Safety Checks</h3>
          <div className="grid gap-4 items-center border-b border-gray-700/30 py-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Hallucination Check</div>
            {selected.map(({ proposal, evaluation }) => (
              <div key={proposal.id}>
                <span className={evaluation?.hallucination_check_passed ? 'text-emerald-400' : 'text-red-400'}>
                  {evaluation?.hallucination_check_passed ? '✓ Passed' : '✕ Failed'}
                </span>
              </div>
            ))}
          </div>
          <div className="grid gap-4 items-center py-3" style={{ gridTemplateColumns: `160px repeat(${colCount}, 1fr)` }}>
            <div className="text-gray-400 text-sm font-medium">Prompt Injection</div>
            {selected.map(({ proposal, evaluation }) => (
              <div key={proposal.id}>
                <span className={!evaluation?.prompt_injection_detected ? 'text-emerald-400' : 'text-red-400'}>
                  {!evaluation?.prompt_injection_detected ? '✓ Clean' : '⚠ Detected'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProposalCompare;

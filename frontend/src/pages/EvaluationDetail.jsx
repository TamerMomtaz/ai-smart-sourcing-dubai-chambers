import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { useUserRole } from '../lib/userRole';

const TEAL = 'var(--color-accent)';

const ShieldIcon = ({ size = 20, color = TEAL }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const PencilIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
  </svg>
);

const OverrideBadge = ({ aiScore, humanScore, reason }) => (
  <span className="inline-flex items-center gap-1.5 text-xs ml-2">
    <span className="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 font-medium">
      manually adjusted
    </span>
    <span className="text-gray-500">
      AI: {parseFloat(aiScore).toFixed(1)} → Analyst: {parseFloat(humanScore).toFixed(1)}
    </span>
  </span>
);

const ScoreBar = ({ label, score, reasoning, dimensionKey, overrides, canOverride, onRequestOverride }) => {
  const [expanded, setExpanded] = useState(false);
  if (score == null) return null;
  const color = score > 70 ? '#10B981' : score >= 40 ? '#F59E0B' : '#EF4444';

  // Find the most recent override for this dimension
  const latestOverride = overrides && overrides.find(o => o.dimension === dimensionKey);

  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1">
        <div className="flex items-center gap-1">
          <span className="text-gray-300 font-medium">{label}</span>
          {latestOverride && (
            <OverrideBadge
              aiScore={latestOverride.ai_original_score}
              humanScore={latestOverride.human_adjusted_score}
              reason={latestOverride.override_reason}
            />
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="font-bold" style={{ color }}>{score}/100</span>
          {canOverride && (
            <button
              onClick={() => onRequestOverride(dimensionKey, label, score)}
              className="text-gray-500 hover:text-amber-400 transition-colors p-1 rounded hover:bg-gray-700/50"
              title="Adjust score"
            >
              <PencilIcon />
            </button>
          )}
        </div>
      </div>
      <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${score}%`, background: `linear-gradient(90deg, ${color}88, ${color})` }} />
      </div>
      {reasoning && (
        <>
          <button onClick={() => setExpanded(!expanded)} className="text-xs text-[#3B82F6] hover:text-blue-300 mt-1">
            {expanded ? '▾ Hide reasoning' : '▸ Show reasoning'}
          </button>
          {expanded && <p className="text-sm text-gray-400 mt-1 pl-2 border-l-2 border-gray-600">{reasoning}</p>}
        </>
      )}
    </div>
  );
};

const ClaimItem = ({ claim }) => {
  const [expanded, setExpanded] = useState(false);
  const classColors = {
    grounded: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: 'G' },
    partial: { bg: 'bg-amber-500/20', text: 'text-amber-400', label: 'P' },
    ungrounded: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'U' },
  };
  const style = classColors[claim.classification] || classColors.ungrounded;

  return (
    <div className="border-b border-gray-700/30 py-3">
      <div
        className="flex items-start gap-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <span className={`${style.bg} ${style.text} w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5`}>
          {style.label}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-gray-300 text-sm">{claim.claim}</p>
          {expanded && (
            <div className="mt-2 pl-2 border-l-2 border-gray-600">
              {claim.source_excerpt ? (
                <p className="text-gray-500 text-xs italic">"{claim.source_excerpt}"</p>
              ) : (
                <p className="text-gray-600 text-xs italic">No matching text found</p>
              )}
              {claim.explanation && (
                <p className="text-gray-400 text-xs mt-1">{claim.explanation}</p>
              )}
            </div>
          )}
        </div>
        <span className="text-gray-600 text-xs flex-shrink-0">{expanded ? '▾' : '▸'}</span>
      </div>
    </div>
  );
};

const DescPill = ({ label, status }) => {
  const isGood = status === 'active' || status === 'verified' || status === 'passed' || status === 'enabled' || status === 'complete' || status === 'configured';
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${isGood ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30' : 'bg-red-500/15 text-red-400 border border-red-500/30'}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${isGood ? 'bg-emerald-400' : 'bg-red-400'}`} />
      {label}: {status}
    </span>
  );
};

const HallucinationShieldPanel = ({ evaluationId, shieldData: initialData }) => {
  const [shieldData, setShieldData] = useState(initialData || null);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [error, setError] = useState('');
  const [claimsExpanded, setClaimsExpanded] = useState(false);

  useEffect(() => {
    if (!initialData && evaluationId) {
      fetchShieldData();
    }
  }, [evaluationId]);

  const fetchShieldData = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/evaluations/${evaluationId}/shield`);
      setShieldData(data);
    } catch (err) {
      // 404 means not verified yet — that's fine
      if (err.response?.status !== 404) {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    try {
      setVerifying(true);
      setError('');
      const { data } = await api.post(`/api/v1/evaluations/${evaluationId}/verify`);
      setShieldData(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setVerifying(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
        <div className="flex items-center gap-3">
          <ShieldIcon size={20} />
          <span className="text-gray-400 text-sm animate-pulse">Loading shield data...</span>
        </div>
      </div>
    );
  }

  // Not verified yet — show verify button
  if (!shieldData) {
    return (
      <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ShieldIcon size={20} />
            <span className="text-gray-300 font-medium">Evidence Validation Layer</span>
            <span className="text-gray-500 text-sm">Not yet verified</span>
          </div>
          <button
            onClick={handleVerify}
            disabled={verifying}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-colors"
            style={{
              borderColor: 'var(--color-badge-bg)',
              color: TEAL,
              backgroundColor: verifying ? 'var(--color-accent-light)' : 'transparent',
            }}
          >
            {verifying ? (
              <>
                <span className="animate-spin inline-block w-4 h-4 border-2 border-[var(--color-accent)] border-t-transparent rounded-full" />
                Verifying AI integrity... ~20 seconds
              </>
            ) : (
              <>
                <ShieldIcon size={16} />
                Verify
              </>
            )}
          </button>
        </div>
        {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
      </div>
    );
  }

  // Shield data available — render full panel
  const gs = parseFloat(shieldData.grounding_score) || 0;
  const gsColor = gs >= 85 ? '#10B981' : gs >= 65 ? '#F59E0B' : '#EF4444';
  const riskColors = { low: 'bg-emerald-500/20 text-emerald-400', medium: 'bg-amber-500/20 text-amber-400', high: 'bg-red-500/20 text-red-400' };
  const riskClass = riskColors[shieldData.hallucination_risk] || riskColors.low;

  const claims = Array.isArray(shieldData.claims_detail) ? shieldData.claims_detail :
    (typeof shieldData.claims_detail === 'string' ? JSON.parse(shieldData.claims_detail) : []);

  const descStatus = typeof shieldData.desc_compliance_status === 'string'
    ? JSON.parse(shieldData.desc_compliance_status)
    : (shieldData.desc_compliance_status || {});

  const sourceCitations = claims.filter(c => c.source_excerpt && c.source_excerpt !== 'null' && c.source_excerpt !== null).length;

  return (
    <div className="bg-[#1E293B] rounded-xl mb-6 border border-gray-700/50 overflow-hidden">
      {/* Top bar */}
      <div className="px-6 py-4 border-b border-gray-700/50 flex items-center justify-between" style={{ borderTop: `3px solid ${TEAL}` }}>
        <div className="flex items-center gap-3">
          <ShieldIcon size={22} color={TEAL} />
          <span className="text-white font-semibold text-lg">Evidence Validation Layer</span>
          <p className="text-gray-400 text-sm mt-1">Every AI conclusion is verified against source evidence. Claims without supporting documentation are flagged for human review.</p>
        </div>
        <div className="flex items-center gap-3">
          <span
            className="text-2xl font-black"
            style={{ color: gsColor, fontFamily: '"JetBrains Mono", monospace' }}
          >
            {gs}%
          </span>
          <span className={`px-3 py-1 rounded-full text-xs font-bold ${riskClass}`}>
            {shieldData.hallucination_risk?.toUpperCase()} RISK
          </span>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6">
        <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4 text-center">
          <p className="text-2xl font-bold" style={{ color: TEAL, fontFamily: '"JetBrains Mono", monospace' }}>{gs}%</p>
          <p className="text-gray-500 text-xs mt-1">Evidence Grounding Score</p>
        </div>
        <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-white" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
            {shieldData.grounded_claims}/{shieldData.total_claims}
          </p>
          <p className="text-gray-500 text-xs mt-1">Claims Verified</p>
        </div>
        <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-[#3B82F6]" style={{ fontFamily: '"JetBrains Mono", monospace' }}>{sourceCitations}</p>
          <p className="text-gray-500 text-xs mt-1">Source Citations</p>
        </div>
        <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4 text-center">
          <p className={`text-2xl font-bold ${shieldData.hallucination_risk === 'low' ? 'text-emerald-400' : shieldData.hallucination_risk === 'medium' ? 'text-amber-400' : 'text-red-400'}`}>
            {shieldData.hallucination_risk?.charAt(0).toUpperCase() + shieldData.hallucination_risk?.slice(1)}
          </p>
          <p className="text-gray-500 text-xs mt-1">Hallucination Risk</p>
        </div>
      </div>

      {/* Two-column: grounding bars + cross-model */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 px-6 pb-6">
        {/* Left: Per-dimension grounding */}
        <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4">
          <h4 className="text-gray-300 font-medium text-sm mb-3">Per-Dimension Grounding</h4>
          {['grounded', 'partial', 'ungrounded'].map((type) => {
            const count = shieldData[`${type}_claims`] || 0;
            const pct = shieldData.total_claims > 0 ? (count / shieldData.total_claims) * 100 : 0;
            const colors = { grounded: '#10B981', partial: '#F59E0B', ungrounded: '#EF4444' };
            return (
              <div key={type} className="mb-3">
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400 capitalize">{type}</span>
                  <span style={{ color: colors[type] }}>{count} ({pct.toFixed(0)}%)</span>
                </div>
                <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: colors[type] }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Cross-model verification */}
        <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4">
          <h4 className="text-gray-300 font-medium text-sm mb-3">Cross-Model Verification</h4>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Primary Score</span>
              <span className="text-white font-bold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                {shieldData.primary_score != null ? parseFloat(shieldData.primary_score).toFixed(1) : '—'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Verification Score</span>
              <span className="text-white font-bold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                {shieldData.cross_model_score != null ? parseFloat(shieldData.cross_model_score).toFixed(1) : '—'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Provider</span>
              <span className="text-gray-300 text-sm" style={{ color: TEAL }}>{shieldData.cross_model_provider || '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">Deviation</span>
              <span className={`font-bold text-sm ${shieldData.deviation_within_threshold ? 'text-emerald-400' : 'text-red-400'}`} style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                {shieldData.score_deviation != null ? `${parseFloat(shieldData.score_deviation).toFixed(1)}%` : '—'}
                {shieldData.deviation_within_threshold ? ' (OK)' : ' (!)'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Claim-by-claim verification (expandable) */}
      {claims.length > 0 && (
        <div className="px-6 pb-6">
          <button
            onClick={() => setClaimsExpanded(!claimsExpanded)}
            className="flex items-center gap-2 text-sm font-medium mb-3"
            style={{ color: TEAL }}
          >
            <span>{claimsExpanded ? '▾' : '▸'}</span>
            Claim-by-claim verification ({claims.length} claims)
          </button>
          {claimsExpanded && (
            <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4 max-h-96 overflow-y-auto">
              {claims.map((claim, idx) => (
                <ClaimItem key={idx} claim={claim} />
              ))}
            </div>
          )}
        </div>
      )}

      {/* DESC compliance pills */}
      <div className="px-6 pb-4">
        <div className="flex flex-wrap gap-2">
          {Object.entries(descStatus).map(([key, value]) => (
            <DescPill key={key} label={key.replace(/_/g, ' ')} status={value} />
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="px-6 py-3 border-t border-gray-700/30 text-center">
        <span className="text-gray-500 text-xs">
          Shield integrity verified — {shieldData.verification_iu ? parseFloat(shieldData.verification_iu).toFixed(2) : '0'} IU consumed — logged to σI
        </span>
      </div>
    </div>
  );
};

const ConfidenceBadge = ({ level }) => {
  const config = {
    high: { bg: 'bg-emerald-500/15', text: 'text-emerald-400', border: 'border-emerald-500/30' },
    medium: { bg: 'bg-amber-500/15', text: 'text-amber-400', border: 'border-amber-500/30' },
    low: { bg: 'bg-red-500/15', text: 'text-red-400', border: 'border-red-500/30' },
  };
  const style = config[level] || config.medium;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text} border ${style.border}`}>
      {(level || 'medium').charAt(0).toUpperCase() + (level || 'medium').slice(1)} confidence
    </span>
  );
};

const DimensionAttribution = ({ dimensionKey, label, data }) => {
  const [expanded, setExpanded] = useState(false);
  if (!data) return null;

  const score = data.score || 0;
  const color = score > 70 ? '#10B981' : score >= 40 ? '#F59E0B' : '#EF4444';
  const evidence = Array.isArray(data.evidence) ? data.evidence : [];
  const risks = Array.isArray(data.risks) ? data.risks : [];

  return (
    <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4 mb-3">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <span className="text-gray-600 text-xs">{expanded ? '▾' : '▸'}</span>
          <span className="text-gray-300 font-medium">{label}</span>
          <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div className="h-full rounded-full" style={{ width: `${score}%`, backgroundColor: color }} />
          </div>
          <span className="text-sm font-bold" style={{ color }}>{score}/100</span>
        </div>
        <ConfidenceBadge level={data.confidence} />
      </div>
      {expanded && (
        <div className="mt-3 pl-6 space-y-3">
          {evidence.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-emerald-400 uppercase tracking-wide mb-1.5">Supporting Evidence</h5>
              <ul className="space-y-1">
                {evidence.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-emerald-500 mt-0.5 flex-shrink-0">+</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {risks.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-amber-400 uppercase tracking-wide mb-1.5">Risk Factors</h5>
              <ul className="space-y-1">
                {risks.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                    <span className="text-red-400 mt-0.5 flex-shrink-0">!</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {evidence.length === 0 && risks.length === 0 && (
            <p className="text-gray-500 text-sm italic">No detailed attribution available for this dimension.</p>
          )}
        </div>
      )}
    </div>
  );
};

const EvidenceAttributionPanel = ({ aiAttribution }) => {
  const [expanded, setExpanded] = useState(false);

  if (!aiAttribution || !aiAttribution.dimensions) return null;

  const dims = aiAttribution.dimensions;
  const dimensionLabels = {
    relevance: 'Relevance',
    feasibility: 'Feasibility',
    sector_alignment: 'Sector Alignment',
    compliance: 'Compliance',
  };

  return (
    <div className="bg-[#1E293B] rounded-xl mb-6 border border-gray-700/50 overflow-hidden">
      <div
        className="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-[#1E293B]/80 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <span className="text-lg">🔍</span>
          <div>
            <h3 className="text-lg font-semibold text-white">Why did the AI score this way?</h3>
            <p className="text-gray-500 text-xs mt-0.5">Evidence-based attribution for each scoring dimension</p>
          </div>
        </div>
        <span className="text-gray-500 text-sm">{expanded ? '▾ Collapse' : '▸ Expand'}</span>
      </div>

      {expanded && (
        <div className="px-6 pb-6">
          {Object.entries(dimensionLabels).map(([key, label]) => (
            <DimensionAttribution
              key={key}
              dimensionKey={key}
              label={label}
              data={dims[key]}
            />
          ))}

          {aiAttribution.overall_reasoning && (
            <div className="mt-4 p-4 bg-[var(--color-table-header-bg)] rounded-lg border-l-2 border-blue-500/50">
              <h5 className="text-xs font-semibold text-blue-400 uppercase tracking-wide mb-1.5">Overall Reasoning</h5>
              <p className="text-gray-300 text-sm">{aiAttribution.overall_reasoning}</p>
            </div>
          )}

          <div className="mt-4 pt-3 border-t border-gray-700/30 text-center">
            <span className="text-gray-500 text-xs">
              Every score is traceable. σI — Added Intelligence
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

const VSCORE_TIER_COLORS = {
  platinum: '#0D9488', gold: '#B8904A', silver: '#3B82F6', bronze: '#F59E0B', under_review: '#EF4444',
};
const VSCORE_TIER_LABELS = {
  platinum: 'Platinum', gold: 'Gold', silver: 'Silver', bronze: 'Bronze', under_review: 'Under Review',
};

const VendorContextBanner = ({ evaluation }) => {
  const [vendorData, setVendorData] = useState(null);

  useEffect(() => {
    if (!evaluation?.proposal?.submitter_id) return;
    const fetchVendorVscore = async () => {
      try {
        const { data } = await api.get(`/api/v1/vendors/${evaluation.proposal.submitter_id}/vscore`);
        setVendorData(data);
      } catch {
        // Not critical
      }
    };
    fetchVendorVscore();
  }, [evaluation?.proposal?.submitter_id]);

  if (!vendorData) return null;

  const tier = vendorData.vscore_tier;
  const tierColor = VSCORE_TIER_COLORS[tier] || '#94A3B8';
  const tierLabel = VSCORE_TIER_LABELS[tier] || tier;
  const engCount = vendorData.engagements?.length || 0;
  const certCount = (vendorData.flags || []).filter(f =>
    ['iso_27001', 'iso_9001', 'iso_14001', 'soc2_type2', 'desc_audit'].includes(f.flag_type)
  ).length;

  if (tier === 'under_review') {
    return (
      <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6 flex items-center gap-3">
        <span className="text-lg">⚠</span>
        <div className="flex-1">
          <span className="text-red-400 text-sm">
            This vendor is under review — vScore: <span className="font-bold">{vendorData.vscore}</span>. Enhanced due diligence recommended.
          </span>
        </div>
        <Link to={`/vendors/${vendorData.vendor_id}`} className="text-red-400 hover:underline text-sm">
          View Dossier →
        </Link>
      </div>
    );
  }

  if (engCount === 0) {
    return (
      <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 mb-6 flex items-center gap-3">
        <span className="text-lg">🆕</span>
        <span className="text-blue-400 text-sm">First-time vendor — limited engagement history</span>
        <Link to={`/vendors/${vendorData.vendor_id}`} className="text-blue-400 hover:underline text-sm ml-auto">
          View Dossier →
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-[#1E293B] border border-gray-700/50 rounded-xl p-4 mb-6 flex items-center gap-3 flex-wrap">
      <span className="text-lg">⚡</span>
      <Link to={`/vendors/${vendorData.vendor_id}`} className="font-semibold text-white hover:underline">
        {vendorData.vendor_name}
      </Link>
      <span className="text-gray-400 text-sm">—</span>
      <span className="text-sm">
        <span className="text-gray-400">vScore: </span>
        <span className="font-bold" style={{ color: tierColor }}>{vendorData.vscore}</span>
      </span>
      <span
        className="px-2 py-0.5 rounded-full text-xs font-bold"
        style={{ backgroundColor: `${tierColor}20`, color: tierColor }}
      >
        {tierLabel}
      </span>
      <span className="text-gray-500 text-sm">|</span>
      <span className="text-gray-400 text-sm">{engCount} prior engagements</span>
      <span className="text-gray-500 text-sm">|</span>
      <span className="text-gray-400 text-sm">{certCount} certifications on file</span>
    </div>
  );
};

const OverrideModal = ({ dimension, dimensionLabel, currentScore, onClose, onSubmit, submitting }) => {
  const [adjustedScore, setAdjustedScore] = useState(currentScore);
  const [reason, setReason] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!reason.trim()) return;
    onSubmit({ dimension, human_adjusted_score: adjustedScore, override_reason: reason.trim() });
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-[#1E293B] rounded-xl border border-gray-700/50 w-full max-w-md">
        <div className="p-6">
          <h3 className="text-lg font-semibold text-white mb-1">Adjust {dimensionLabel} Score</h3>
          <p className="text-gray-500 text-sm mb-4">Current AI score: <span className="text-white font-bold">{parseFloat(currentScore).toFixed(1)}</span></p>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="text-gray-400 text-sm block mb-2">Adjusted Score: <span className="text-white font-bold">{adjustedScore}</span></label>
              <input
                type="range"
                min="0"
                max="100"
                step="0.5"
                value={adjustedScore}
                onChange={(e) => setAdjustedScore(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
              />
              <div className="flex justify-between text-xs text-gray-600 mt-1">
                <span>0</span><span>25</span><span>50</span><span>75</span><span>100</span>
              </div>
            </div>
            <div className="mb-4">
              <label className="text-gray-400 text-sm block mb-2">Reason for adjustment <span className="text-red-400">*</span></label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Explain why this score needs adjustment..."
                className="w-full bg-gray-800 border border-gray-600 rounded-lg p-3 text-white text-sm resize-none focus:border-amber-500 focus:outline-none"
                rows={3}
                required
              />
            </div>
            <div className="flex gap-3 justify-end">
              <button type="button" onClick={onClose} className="px-4 py-2 text-gray-400 hover:text-white text-sm">
                Cancel
              </button>
              <button
                type="submit"
                disabled={!reason.trim() || submitting}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
              >
                {submitting ? 'Applying...' : 'Apply Override'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

const OverrideHistory = ({ overrides }) => {
  if (!overrides || overrides.length === 0) return null;

  return (
    <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        Override History
        <span className="text-xs bg-amber-500/15 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded-full">
          {overrides.length} adjustment{overrides.length !== 1 ? 's' : ''}
        </span>
      </h3>
      <div className="space-y-3">
        {overrides.map((o) => (
          <div key={o.id} className="bg-[var(--color-table-header-bg)] rounded-lg p-4 border-l-2 border-amber-500/50">
            <div className="flex items-center justify-between mb-1">
              <span className="text-gray-300 text-sm font-medium capitalize">{o.dimension.replace('_', ' ')}</span>
              <span className="text-gray-500 text-xs">{new Date(o.created_at).toLocaleString()}</span>
            </div>
            <div className="text-sm mb-1">
              <span className="text-gray-500">AI: </span>
              <span className="text-red-400 line-through">{parseFloat(o.ai_original_score).toFixed(1)}</span>
              <span className="text-gray-500"> → Analyst: </span>
              <span className="text-emerald-400 font-bold">{parseFloat(o.human_adjusted_score).toFixed(1)}</span>
            </div>
            <p className="text-gray-400 text-xs italic">"{o.override_reason}"</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const EvaluationDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { role } = useUserRole();
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showArabic, setShowArabic] = useState(false);
  const [overrides, setOverrides] = useState([]);
  const [overrideModal, setOverrideModal] = useState(null);
  const [overrideSubmitting, setOverrideSubmitting] = useState(false);

  const canOverride = role === 'admin' || role === 'analyst';

  useEffect(() => { fetchEvaluation(); fetchOverrides(); }, [id]);

  const fetchEvaluation = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/evaluations/${id}`);
      setEvaluation(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const fetchOverrides = async () => {
    try {
      const { data } = await api.get(`/api/v1/evaluations/${id}/overrides`);
      setOverrides(data.overrides || []);
    } catch {
      // Not critical
    }
  };

  const handleRequestOverride = (dimensionKey, dimensionLabel, currentScore) => {
    setOverrideModal({ dimension: dimensionKey, label: dimensionLabel, score: currentScore });
  };

  const handleSubmitOverride = async (payload) => {
    try {
      setOverrideSubmitting(true);
      const { data } = await api.post(`/api/v1/evaluations/${id}/override`, payload);
      setEvaluation(data);
      setOverrideModal(null);
      await fetchOverrides();
    } catch (err) {
      alert(getErrorMessage(err));
    } finally {
      setOverrideSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--color-table-header-bg)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#3B82F6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading evaluation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[var(--color-table-header-bg)] flex items-center justify-center">
        <div className="text-red-400 text-lg">{error}</div>
      </div>
    );
  }

  const aiCost = evaluation?.ai_cost;

  return (
    <div className="min-h-screen bg-[var(--color-table-header-bg)] p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Evaluation Detail</h1>
          <button onClick={() => navigate('/evaluations')} className="text-[#3B82F6] hover:text-blue-300">
            ← Back to Evaluations
          </button>
        </div>

        {/* Vendor Context Banner */}
        <VendorContextBanner evaluation={evaluation} />

        {/* Proposal Info */}
        {evaluation.proposal && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-3">Proposal</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <span className="text-gray-500 text-sm">Title</span>
                <p className="text-white font-medium">{evaluation.proposal.title}</p>
              </div>
              <div>
                <span className="text-gray-500 text-sm">Sector</span>
                <p className="text-gray-300 capitalize">{evaluation.proposal.sector}</p>
              </div>
              <div>
                <span className="text-gray-500 text-sm">Technology</span>
                <p className="text-gray-300">{evaluation.proposal.technology_type}</p>
              </div>
              <div>
                <span className="text-gray-500 text-sm">Maturity</span>
                <p className="text-gray-300 capitalize">{evaluation.proposal.maturity_level}</p>
              </div>
            </div>
          </div>
        )}

        {/* Composite Score - Large */}
        <div className="bg-[#1E293B] rounded-xl p-8 mb-6 border border-gray-700/50 text-center">
          <div
            className="text-7xl font-black"
            style={{
              color: (evaluation.composite_score || 0) > 70 ? '#10B981' : (evaluation.composite_score || 0) >= 40 ? '#F59E0B' : '#EF4444'
            }}
          >
            {evaluation.composite_score?.toFixed(1) || '—'}
          </div>
          <p className="text-gray-400 mt-2">
            Composite Score
            {overrides.some(o => o.dimension === 'composite') && (
              <span className="ml-2 px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 text-xs font-medium">manually adjusted</span>
            )}
            {overrides.some(o => o.dimension !== 'composite') && !overrides.some(o => o.dimension === 'composite') && (
              <span className="ml-2 px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 text-xs font-medium">recalculated from overrides</span>
            )}
          </p>
          <p className="text-gray-600 text-xs mt-1">
            Evaluated {evaluation.evaluated_at ? new Date(evaluation.evaluated_at).toLocaleString() : '—'}
          </p>
        </div>

        {/* Score Breakdown */}
        <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
          <h3 className="text-xl font-bold text-white mb-6">Score Breakdown</h3>
          <ScoreBar label="Relevance" score={evaluation.relevance_score} reasoning={evaluation.relevance_reasoning} dimensionKey="relevance" overrides={overrides} canOverride={canOverride} onRequestOverride={handleRequestOverride} />
          <ScoreBar label="Feasibility" score={evaluation.feasibility_score} reasoning={evaluation.feasibility_reasoning} dimensionKey="feasibility" overrides={overrides} canOverride={canOverride} onRequestOverride={handleRequestOverride} />
          <ScoreBar label="Sector Alignment" score={evaluation.sector_alignment_score} reasoning={evaluation.sector_reasoning} dimensionKey="sector_alignment" overrides={overrides} canOverride={canOverride} onRequestOverride={handleRequestOverride} />
          <ScoreBar label="Compliance" score={evaluation.compliance_score} reasoning={evaluation.compliance_reasoning} dimensionKey="compliance" overrides={overrides} canOverride={canOverride} onRequestOverride={handleRequestOverride} />
        </div>

        {/* Evidence Attribution Panel */}
        <EvidenceAttributionPanel aiAttribution={evaluation.ai_attribution} />

        {/* σI Evidence Validation Layer */}
        <HallucinationShieldPanel evaluationId={id} />

        {/* Executive Summary */}
        {(evaluation.summary_en || evaluation.summary_ar) && (
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

        {/* Safety Checks */}
        <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-3">Safety Checks</h3>
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <span className={evaluation.hallucination_check_passed ? 'text-emerald-400' : 'text-red-400'}>
                {evaluation.hallucination_check_passed ? '✓' : '✕'}
              </span>
              <span className="text-gray-300 text-sm">Hallucination Check</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={!evaluation.prompt_injection_detected ? 'text-emerald-400' : 'text-red-400'}>
                {!evaluation.prompt_injection_detected ? '✓' : '⚠'}
              </span>
              <span className="text-gray-300 text-sm">Prompt Injection</span>
            </div>
          </div>
        </div>

        {/* Override History */}
        <OverrideHistory overrides={overrides} />

        {/* Override Modal */}
        {overrideModal && (
          <OverrideModal
            dimension={overrideModal.dimension}
            dimensionLabel={overrideModal.label}
            currentScore={overrideModal.score}
            onClose={() => setOverrideModal(null)}
            onSubmit={handleSubmitOverride}
            submitting={overrideSubmitting}
          />
        )}

        {/* AI Cost */}
        {aiCost && (
          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">ΣI — Evaluation Cost</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 text-center">
                <p className="text-xl font-bold text-[#3B82F6]">{(aiCost.prompt_tokens + aiCost.completion_tokens).toLocaleString()}</p>
                <p className="text-gray-500 text-xs mt-1">Total Tokens</p>
              </div>
              <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 text-center">
                <p className="text-xl font-bold text-[#F59E0B]">${parseFloat(aiCost.cost_usd).toFixed(4)}</p>
                <p className="text-gray-500 text-xs mt-1">Cost (USD)</p>
              </div>
              <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 text-center">
                <p className="text-xl font-bold text-[#10B981]">{parseFloat(aiCost.energy_kwh).toFixed(6)}</p>
                <p className="text-gray-500 text-xs mt-1">Energy (kWh)</p>
              </div>
              <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 text-center">
                <p className="text-xl font-bold text-gray-300">{aiCost.latency_ms}ms</p>
                <p className="text-gray-500 text-xs mt-1">Latency</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvaluationDetail;

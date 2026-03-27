import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { useUserRole } from '../lib/userRole';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

const TIER_COLORS = {
  platinum: '#0D9488',
  gold: '#B8904A',
  silver: '#3B82F6',
  bronze: '#F59E0B',
  under_review: '#EF4444',
};

const TIER_LABELS = {
  platinum: 'Platinum',
  gold: 'Gold',
  silver: 'Silver',
  bronze: 'Bronze',
  under_review: 'Under Review',
};

const TierBadge = ({ tier }) => {
  const color = TIER_COLORS[tier] || '#94A3B8';
  return (
    <span
      className="px-2.5 py-1 rounded-full text-xs font-bold"
      style={{ backgroundColor: `${color}20`, color }}
    >
      {TIER_LABELS[tier] || tier}
    </span>
  );
};

const MetricCard = ({ label, value, sub, color }) => (
  <div className="bg-[var(--color-card-bg,#fff)] rounded-xl shadow-sm p-6 border border-[var(--color-border,#e5e7eb)]">
    <p className="text-[var(--color-muted,#6b7280)] text-xs font-body mb-1">{label}</p>
    <p className="text-3xl font-bold" style={{ color: color || 'var(--color-text)' }}>{value}</p>
    {sub && <p className="text-[var(--color-muted,#6b7280)] text-xs mt-1">{sub}</p>}
  </div>
);

/* ─── Mini vScore gauge for My vScore view ─── */
const VScoreGauge = ({ score, tier, size = 120 }) => {
  const [animated, setAnimated] = useState(0);
  const color = TIER_COLORS[tier] || '#94A3B8';
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = ((animated - 300) / 600) * circumference;

  useEffect(() => {
    if (score == null) return;
    const duration = 1500;
    const startTime = performance.now();
    const animate = (now) => {
      const elapsed = now - startTime;
      const pct = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - pct, 3);
      setAnimated(Math.round(300 + eased * (score - 300)));
      if (pct < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [score]);

  if (score == null) return null;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#334155" strokeWidth={6} />
          <circle
            cx={size / 2} cy={size / 2} r={radius} fill="none"
            stroke={color} strokeWidth={6} strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - Math.max(0, progress)}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dashoffset 0.3s ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-black text-white" style={{ fontSize: size > 80 ? '2rem' : '1.2rem' }}>
            {animated}
          </span>
        </div>
      </div>
      <span
        className="px-3 py-1 rounded-full text-sm font-bold"
        style={{ backgroundColor: `${color}20`, color }}
      >
        {TIER_LABELS[tier] || tier}
      </span>
    </div>
  );
};

const OUTCOME_COLORS = {
  completed: '#10B981',
  partial: '#F59E0B',
  failed: '#EF4444',
  ongoing: '#3B82F6',
};

/* ─── My vScore View (vendor role only) ─── */
const MyVScoreView = () => {
  const [vscore, setVscore] = useState(null);
  const [vendor, setVendor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [formulaOpen, setFormulaOpen] = useState(false);

  useEffect(() => {
    fetchMyVScore();
  }, []);

  const fetchMyVScore = async () => {
    try {
      setLoading(true);
      // Find vendor associated with current user
      const { data: myVendor } = await api.get('/api/v1/vendors/my-vendor');
      if (!myVendor?.vendor_id) {
        setError('No vendor profile found for your account.');
        return;
      }
      // Fetch vendor details and vScore dossier
      const [vendorRes, vscoreRes] = await Promise.all([
        api.get(`/api/v1/vendors/${myVendor.vendor_id}`),
        api.get(`/api/v1/vendors/${myVendor.vendor_id}/vscore`),
      ]);
      setVendor(vendorRes.data);
      setVscore(vscoreRes.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-[var(--color-accent)] font-heading text-2xl">Loading My vScore...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-500 font-body text-lg">{error}</div>
      </div>
    );
  }

  const radarData = vscore?.dimension_scores ? [
    { dim: 'Performance', value: vscore.dimension_scores.performance || 0, fullMark: 100 },
    { dim: 'Quality', value: vscore.dimension_scores.quality || 0, fullMark: 100 },
    { dim: 'Compliance', value: vscore.dimension_scores.compliance || 0, fullMark: 100 },
    { dim: 'Integrity', value: vscore.dimension_scores.integrity || 0, fullMark: 100 },
    { dim: 'Entity', value: vscore.dimension_scores.entity || 0, fullMark: 100 },
  ] : [];

  const positiveTypes = ['iso_27001', 'iso_9001', 'iso_14001', 'soc2_type2', 'commendation', 'desc_audit', 'award'];
  const positiveFlags = (vscore?.flags || []).filter(f => positiveTypes.includes(f.flag_type) || f.severity === 'info');
  const negativeFlags = (vscore?.flags || []).filter(f => !positiveTypes.includes(f.flag_type) && f.severity !== 'info');

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="font-heading text-3xl md:text-4xl text-[var(--color-accent)]">My vScore</h1>
          <p className="text-[var(--color-muted,#6b7280)] font-body mt-1">Your supplier credit score — powered by σI</p>
        </div>

        {/* Score Header */}
        {vscore && vscore.vscore != null && (
          <div className="space-y-4">
            <div className="bg-[#1E293B] rounded-xl p-5 md:p-8 shadow-lg">
              <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-8">
                <VScoreGauge score={vscore.vscore} tier={vscore.vscore_tier} size={120} />
                <div className="flex-1 text-center sm:text-left">
                  <div className="flex items-center justify-center sm:justify-start gap-3 mb-2">
                    <h2 className="text-xl md:text-2xl font-bold text-white">{vendor?.name || 'Your Company'}</h2>
                    {vscore.score_change !== 0 && (
                      <span className={`text-sm font-bold ${vscore.score_change > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {vscore.score_change > 0 ? '+' : ''}{vscore.score_change} {vscore.score_change > 0 ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-400 text-sm">
                    Based on {vscore.engagements?.length || 0} engagements, {vscore.flags?.length || 0} flags, {vscore.relationships?.length || 0} relationships
                  </p>
                </div>
              </div>
            </div>

            {/* Two-column: Radar + AI Narrative */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {radarData.length > 0 && (
                <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                  <h3 className="text-white font-semibold mb-3">Dimension Breakdown</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#334155" />
                      <PolarAngleAxis dataKey="dim" tick={{ fill: '#94A3B8', fontSize: 12 }} />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#64748B', fontSize: 10 }} />
                      <Radar
                        dataKey="value"
                        stroke={TIER_COLORS[vscore.vscore_tier] || '#0D9488'}
                        fill={TIER_COLORS[vscore.vscore_tier] || '#0D9488'}
                        fillOpacity={0.3}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                  <div className="mt-4 space-y-2">
                    {radarData.map(d => (
                      <div key={d.dim} className="flex items-center gap-2">
                        <span className="text-gray-400 text-xs w-24">{d.dim}</span>
                        <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${d.value}%`, backgroundColor: TIER_COLORS[vscore.vscore_tier] || '#0D9488' }} />
                        </div>
                        <span className="text-white text-xs font-bold w-8 text-right">{d.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-3">σI Risk Narrative</h3>
                {vscore.ai_narrative ? (
                  <blockquote className="border-l-4 border-[var(--color-accent)] pl-4 text-gray-300 text-sm leading-relaxed italic">
                    {vscore.ai_narrative}
                  </blockquote>
                ) : (
                  <p className="text-gray-500 text-sm italic">No AI narrative available yet.</p>
                )}
                <p className="text-gray-500 text-xs mt-4">
                  This assessment was generated by σI and logged to the transparency dashboard.
                </p>
              </div>
            </div>

            {/* Engagement Timeline */}
            {vscore.engagements?.length > 0 && (
              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-4">Engagement History</h3>
                <div className="space-y-3">
                  {vscore.engagements.map((e, i) => {
                    const outcomeColor = OUTCOME_COLORS[e.outcome] || '#94A3B8';
                    return (
                      <div key={i} className="bg-[#0F172A] rounded-lg p-4 border border-gray-700/50">
                        <div className="flex items-center gap-3 flex-wrap">
                          <span className="text-gray-500 text-xs">{e.start_date ? new Date(e.start_date).toLocaleDateString() : '—'}</span>
                          <span className="px-2 py-0.5 rounded text-xs font-bold bg-blue-500/20 text-blue-400 capitalize">{e.engagement_type}</span>
                          <span className="text-white text-sm font-medium flex-1">{e.engagement_title}</span>
                          <span className="px-2 py-0.5 rounded text-xs font-bold capitalize" style={{ backgroundColor: `${outcomeColor}20`, color: outcomeColor }}>{e.outcome}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Certifications & Flags */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-3">Positive Signals</h3>
                {positiveFlags.length === 0 ? (
                  <p className="text-gray-500 text-sm">No positive signals recorded.</p>
                ) : (
                  <div className="space-y-3">
                    {positiveFlags.map((f, i) => (
                      <div key={i} className="border-l-4 border-emerald-500 pl-3 py-2">
                        <p className="text-white text-sm font-medium">{f.title}</p>
                        <div className="flex gap-3 text-xs text-gray-400 mt-1">
                          {f.flag_date && <span>Issued: {new Date(f.flag_date).toLocaleDateString()}</span>}
                          <span className={`font-semibold ${f.resolution_status === 'resolved' ? 'text-emerald-400' : 'text-amber-400'}`}>{f.resolution_status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-3">Risk Flags</h3>
                {negativeFlags.length === 0 ? (
                  <p className="text-gray-500 text-sm">No risk flags recorded.</p>
                ) : (
                  <div className="space-y-3">
                    {negativeFlags.map((f, i) => (
                      <div key={i} className="border-l-4 border-red-500 pl-3 py-2">
                        <p className="text-white text-sm font-medium">{f.title}</p>
                        <div className="flex gap-3 text-xs text-gray-400 mt-1">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                            f.severity === 'critical' || f.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                            f.severity === 'medium' ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-500/20 text-gray-400'
                          }`}>{f.severity}</span>
                          <span className={`font-semibold ${f.resolution_status === 'resolved' ? 'text-emerald-400' : 'text-red-400'}`}>{f.resolution_status}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Score History */}
            {vscore.score_history?.length > 0 && (
              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-3">Score History</h3>
                <div className="space-y-2">
                  {vscore.score_history.map((h, i) => (
                    <div key={i} className="flex items-center gap-4 p-3 bg-[#0F172A] rounded-lg">
                      <span className="text-lg font-bold" style={{ color: TIER_COLORS[h.tier] || '#94A3B8' }}>{h.vscore}</span>
                      <span className="px-2 py-0.5 rounded-full text-xs font-bold" style={{ backgroundColor: `${TIER_COLORS[h.tier]}20`, color: TIER_COLORS[h.tier] || '#94A3B8' }}>
                        {TIER_LABELS[h.tier] || h.tier}
                      </span>
                      {h.score_change !== 0 && h.score_change != null && (
                        <span className={`text-xs font-bold ${h.score_change > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {h.score_change > 0 ? '+' : ''}{h.score_change}
                        </span>
                      )}
                      <span className="text-gray-500 text-xs ml-auto">{h.created_at ? new Date(h.created_at).toLocaleDateString() : ''}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Formula Transparency */}
            <div className="bg-[var(--color-card-bg,#fff)] rounded-xl shadow-sm border border-[var(--color-border,#e5e7eb)] overflow-hidden">
              <button
                onClick={() => setFormulaOpen(!formulaOpen)}
                className="w-full flex items-center justify-between p-5 text-left hover:bg-[var(--color-table-header-bg,#f9fafb)] transition"
              >
                <span className="font-semibold text-[var(--color-text)]">How is vScore calculated?</span>
                <span className="text-[var(--color-muted,#6b7280)]">{formulaOpen ? '▾' : '▸'}</span>
              </button>
              {formulaOpen && (
                <div className="px-5 pb-5 space-y-3">
                  {[
                    { label: 'Performance History', weight: 30, desc: 'Past engagement outcomes', color: '#3B82F6' },
                    { label: 'Proposal Quality', weight: 25, desc: 'AI evaluation scores and consistency', color: '#10B981' },
                    { label: 'Compliance & Governance', weight: 20, desc: 'DESC, ISO, data residency', color: '#F59E0B' },
                    { label: 'Claim Integrity', weight: 15, desc: 'Hallucination Shield grounding scores', color: '#8B5CF6' },
                    { label: 'Entity Intelligence', weight: 10, desc: 'Related company risks and tenure', color: '#EC4899' },
                  ].map((item) => (
                    <div key={item.label} className="flex flex-wrap sm:flex-nowrap items-center gap-2 sm:gap-3">
                      <div className="w-12 text-right text-sm font-bold" style={{ color: item.color }}>{item.weight}%</div>
                      <div className="flex-1 min-w-[80px]">
                        <div className="h-2 bg-[var(--color-table-header-bg,#f1f5f9)] rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${item.weight}%`, backgroundColor: item.color }} />
                        </div>
                      </div>
                      <div className="w-full sm:w-56">
                        <span className="text-sm text-[var(--color-text)] font-medium">{item.label}</span>
                        <span className="text-xs text-[var(--color-muted,#6b7280)] ml-2">— {item.desc}</span>
                      </div>
                    </div>
                  ))}
                  <p className="text-xs text-[var(--color-muted,#6b7280)] italic mt-3 pt-3 border-t border-[var(--color-border,#e5e7eb)]">
                    Score range: 300-900. Every component is traceable. σI — Added Intelligence.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {(!vscore || vscore.vscore == null) && (
          <div className="bg-[var(--color-card-bg,#fff)] rounded-xl shadow-sm p-8 text-center">
            <p className="text-[var(--color-muted,#6b7280)] text-lg">Your vScore is being calculated. Check back soon.</p>
          </div>
        )}

        <div className="text-center text-xs text-[var(--color-muted,#6b7280)] py-4 mt-4">
          Every score is traceable. Every factor is visible. σI — Added Intelligence
        </div>
      </div>
    </div>
  );
};

const VendorIntelligence = () => {
  const { role } = useUserRole();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState('vscore');
  const [sortDir, setSortDir] = useState('desc');
  const [methodologyOpen, setMethodologyOpen] = useState(false);
  const [descOnly, setDescOnly] = useState(false);

  useEffect(() => {
    if (role !== 'vendor') {
      fetchData();
    }
  }, [role]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const { data: result } = await api.get('/api/v1/vendors/intelligence');
      setData(result);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // Vendor role sees only their own vScore
  if (role === 'vendor') {
    return <MyVScoreView />;
  }

  const sortedVendors = useMemo(() => {
    if (!data?.vendors) return [];
    let filtered = data.vendors;
    if (descOnly) {
      filtered = filtered.filter(v => v.is_desc_approved);
    }
    if (search) {
      const q = search.toLowerCase();
      filtered = filtered.filter(v => v.name?.toLowerCase().includes(q));
    }
    return [...filtered].sort((a, b) => {
      let aVal, bVal;
      if (sortKey === 'vscore') { aVal = a.vscore || 0; bVal = b.vscore || 0; }
      else if (sortKey === 'name') { aVal = a.name || ''; bVal = b.name || ''; }
      else if (sortKey === 'engagements') { aVal = a.engagement_count || 0; bVal = b.engagement_count || 0; }
      else { aVal = a.vscore || 0; bVal = b.vscore || 0; }

      if (sortKey === 'name') {
        return sortDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
      }
      return sortDir === 'desc' ? bVal - aVal : aVal - bVal;
    });
  }, [data, search, sortKey, sortDir, descOnly]);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const sortArrow = (key) => {
    if (sortKey !== key) return '';
    return sortDir === 'desc' ? ' ▾' : ' ▴';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse text-[var(--color-accent)] font-heading text-2xl">Loading Vendor Intelligence...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-500 font-body text-lg">{error}</div>
      </div>
    );
  }

  const dist = data?.distribution || {};
  const totalCerts = Object.values(data?.certifications_summary || {}).reduce((a, b) => a + b, 0);

  return (
    <div className="min-h-screen p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="font-heading text-3xl md:text-4xl text-[var(--color-accent)]">Vendor Intelligence — vScore</h1>
            <p className="text-[var(--color-muted,#6b7280)] font-body mt-1">Supplier credit scoring powered by σI</p>
          </div>
          <div className="flex flex-wrap gap-2 mt-4 md:mt-0">
            {Object.entries(dist).map(([tier, count]) => (
              <span
                key={tier}
                className="px-3 py-1 rounded-full text-xs font-bold"
                style={{ backgroundColor: `${TIER_COLORS[tier]}20`, color: TIER_COLORS[tier] }}
              >
                {count} {TIER_LABELS[tier]}
              </span>
            ))}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <MetricCard label="Average vScore" value={data?.avg_vscore || 0} color="var(--color-accent)" sub="out of 900" />
          <MetricCard label="Total Engagements Tracked" value={data?.total_engagements || 0} color="#3B82F6" />
          <MetricCard label="Active Certifications" value={totalCerts} color="#10B981" sub="ISO, SOC2, DESC" />
          <MetricCard label="Risk Flags Open" value={data?.open_risk_flags || 0} color="#EF4444" />
        </div>

        {/* Leaderboard */}
        <div className="bg-[var(--color-card-bg,#fff)] rounded-xl shadow-md overflow-hidden mb-8">
          <div className="p-4 border-b border-[var(--color-border,#e5e7eb)] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <h2 className="font-heading text-xl text-[var(--color-text)]">Vendor Leaderboard</h2>
            <div className="flex items-center gap-4">
              <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                <span className="text-sm font-medium text-[var(--color-muted,#6b7280)]">Show DESC Certified Only</span>
                <div className="relative">
                  <input type="checkbox" checked={descOnly} onChange={(e) => setDescOnly(e.target.checked)} className="sr-only peer" />
                  <div className="w-11 h-6 bg-[var(--color-border,#d1d5db)] rounded-full peer peer-checked:bg-emerald-500 transition-colors" />
                  <div className="absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow peer-checked:translate-x-5 transition-transform" />
                </div>
              </label>
              <input
                type="text"
                placeholder="Search vendors..."
                value={search}
                onChange={e => setSearch(e.target.value)}
                className="border border-[var(--color-border,#d1d5db)] rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] bg-[var(--color-input-bg,#fff)] text-[var(--color-text)]"
              />
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" style={{ minWidth: '800px' }}>
              <thead>
                <tr className="bg-[var(--color-table-header-bg,#f9fafb)] text-left">
                  <th className="px-4 py-3 font-semibold text-[var(--color-muted,#6b7280)]">Rank</th>
                  <th className="px-4 py-3 font-semibold text-[var(--color-muted,#6b7280)]">Vendor</th>
                  <th className="px-4 py-3 font-semibold text-[var(--color-muted,#6b7280)] cursor-pointer select-none" onClick={() => handleSort('vscore')}>
                    vScore{sortArrow('vscore')}
                  </th>
                  <th className="px-4 py-3 font-semibold text-[var(--color-muted,#6b7280)]">Tier</th>
                  <th className="px-4 py-3 font-semibold text-[var(--color-muted,#6b7280)]">Country</th>
                  <th className="px-4 py-3 font-semibold text-[var(--color-muted,#6b7280)]">Sector</th>
                  <th className="px-4 py-3 font-semibold text-[var(--color-muted,#6b7280)] cursor-pointer select-none" onClick={() => handleSort('engagements')}>
                    Engagements{sortArrow('engagements')}
                  </th>
                  <th className="px-4 py-3 font-semibold text-[var(--color-muted,#6b7280)]">Flags</th>
                  <th className="px-4 py-3 font-semibold text-[var(--color-muted,#6b7280)]">Action</th>
                </tr>
              </thead>
              <tbody>
                {sortedVendors.map((v, i) => {
                  const tierColor = TIER_COLORS[v.tier] || '#94A3B8';
                  return (
                    <tr key={v.id} className="border-t border-[var(--color-border,#e5e7eb)] hover:bg-[var(--color-table-header-bg,#f9fafb)] transition">
                      <td className="px-4 py-3 font-bold text-[var(--color-muted,#6b7280)]">{i + 1}</td>
                      <td className="px-4 py-3">
                        <div className="font-semibold text-[var(--color-text)]">
                          {v.name}
                          {v.has_shortlisted_proposal && (
                            <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-600 border border-emerald-500/30">
                              Shortlisted
                            </span>
                          )}
                        </div>
                        {v.is_desc_approved && (
                          <span className="text-emerald-500 text-xs">DESC Certified</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-lg font-black" style={{ color: tierColor }}>
                          {v.vscore || '—'}
                        </span>
                      </td>
                      <td className="px-4 py-3"><TierBadge tier={v.tier} /></td>
                      <td className="px-4 py-3 text-[var(--color-muted,#6b7280)]">{v.country || '—'}</td>
                      <td className="px-4 py-3 text-[var(--color-muted,#6b7280)] capitalize">{v.sector || '—'}</td>
                      <td className="px-4 py-3 text-[var(--color-text)]">{v.engagement_count}</td>
                      <td className="px-4 py-3">
                        {v.flag_count_positive > 0 && (
                          <span className="text-emerald-500 font-medium mr-2">{v.flag_count_positive}</span>
                        )}
                        {v.flag_count_negative > 0 && (
                          <span className="text-red-500 font-medium">{v.flag_count_negative}</span>
                        )}
                        {v.flag_count_positive === 0 && v.flag_count_negative === 0 && (
                          <span className="text-[var(--color-muted,#6b7280)]">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          to={`/vendors/${v.id}`}
                          className="text-[var(--color-accent)] hover:underline text-sm font-medium"
                        >
                          View Dossier →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Score Distribution */}
        <div className="bg-[var(--color-card-bg,#fff)] rounded-xl shadow-sm p-6 mb-8 border border-[var(--color-border,#e5e7eb)]">
          <h2 className="font-heading text-xl text-[var(--color-text)] mb-4">Score Distribution</h2>
          <div className="space-y-3">
            {Object.entries(dist).map(([tier, count]) => {
              const total = sortedVendors.length || 1;
              const pct = (count / total) * 100;
              return (
                <div key={tier} className="flex items-center gap-3">
                  <div className="w-28 text-right">
                    <TierBadge tier={tier} />
                  </div>
                  <div className="flex-1 h-6 bg-[var(--color-table-header-bg,#f1f5f9)] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${pct}%`, backgroundColor: TIER_COLORS[tier] }}
                    />
                  </div>
                  <span className="w-8 text-sm font-bold text-[var(--color-text)]">{count}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Certification Overview */}
        {data?.certifications_summary && Object.keys(data.certifications_summary).length > 0 && (
          <div className="bg-[var(--color-card-bg,#fff)] rounded-xl shadow-sm p-6 mb-8 border border-[var(--color-border,#e5e7eb)]">
            <h2 className="font-heading text-xl text-[var(--color-text)] mb-4">Certification Overview</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(data.certifications_summary).map(([cert, count]) => (
                <div key={cert} className="bg-[var(--color-table-header-bg,#f9fafb)] rounded-lg p-4 text-center">
                  <p className="text-2xl font-bold text-[var(--color-accent)]">{count}</p>
                  <p className="text-xs text-[var(--color-muted,#6b7280)] mt-1 uppercase">{cert.replace(/_/g, ' ')}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Methodology */}
        <div className="bg-[var(--color-card-bg,#fff)] rounded-xl shadow-sm border border-[var(--color-border,#e5e7eb)] overflow-hidden mb-8">
          <button
            onClick={() => setMethodologyOpen(!methodologyOpen)}
            className="w-full flex items-center justify-between p-5 text-left hover:bg-[var(--color-table-header-bg,#f9fafb)] transition"
          >
            <span className="font-semibold text-[var(--color-text)]">How is vScore calculated?</span>
            <span className="text-[var(--color-muted,#6b7280)]">{methodologyOpen ? '▾' : '▸'}</span>
          </button>
          {methodologyOpen && (
            <div className="px-5 pb-5 space-y-3">
              {[
                { label: 'Performance History', weight: 30, desc: 'Past engagement outcomes', color: '#3B82F6' },
                { label: 'Proposal Quality', weight: 25, desc: 'AI evaluation scores and consistency', color: '#10B981' },
                { label: 'Compliance & Governance', weight: 20, desc: 'DESC, ISO, data residency', color: '#F59E0B' },
                { label: 'Claim Integrity', weight: 15, desc: 'Hallucination Shield grounding scores', color: '#8B5CF6' },
                { label: 'Entity Intelligence', weight: 10, desc: 'Related company risks and tenure', color: '#EC4899' },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-3">
                  <div className="w-12 text-right text-sm font-bold" style={{ color: item.color }}>
                    {item.weight}%
                  </div>
                  <div className="flex-1">
                    <div className="h-2 bg-[var(--color-table-header-bg,#f1f5f9)] rounded-full overflow-hidden">
                      <div className="h-full rounded-full" style={{ width: `${item.weight}%`, backgroundColor: item.color }} />
                    </div>
                  </div>
                  <div className="w-56">
                    <span className="text-sm text-[var(--color-text)] font-medium">{item.label}</span>
                    <span className="text-xs text-[var(--color-muted,#6b7280)] ml-2">— {item.desc}</span>
                  </div>
                </div>
              ))}
              <p className="text-xs text-[var(--color-muted,#6b7280)] italic mt-3 pt-3 border-t border-[var(--color-border,#e5e7eb)]">
                Score range: 300-900. Every component is traceable. σI — Added Intelligence.
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-[var(--color-muted,#6b7280)] py-4">
          Every score is traceable. Every factor is visible. σI — Added Intelligence
        </div>
      </div>
    </div>
  );
};

export default VendorIntelligence;

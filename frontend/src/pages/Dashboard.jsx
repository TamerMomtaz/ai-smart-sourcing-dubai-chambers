import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { useTranslation } from '../lib/language';
import { ROLE_BADGES } from '../config/rolePermissions';
import { useUserRole } from '../lib/userRole';
import DemoBanner from '../components/DemoBanner';
import VendorDashboard from './VendorDashboard';

// --- Animated counter hook ---
function useCountUp(target, duration = 1500) {
  const [value, setValue] = useState(0);
  const rafRef = useRef(null);
  const startRef = useRef(null);

  useEffect(() => {
    if (target == null || target === 0) {
      setValue(0);
      return;
    }
    const t = Number(target);
    startRef.current = performance.now();

    const animate = (now) => {
      const elapsed = now - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(eased * t);
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      } else {
        setValue(t);
      }
    };

    rafRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration]);

  return value;
}

// --- Sparkline SVG component ---
const Sparkline = ({ data, width = 400, height = 48 }) => {
  if (!data || data.length === 0) return null;
  const values = data.map(d => d.cumulative_hours);
  const max = Math.max(...values, 1);
  const min = 0;
  const points = values.map((v, i) => {
    const x = (i / Math.max(values.length - 1, 1)) * width;
    const y = height - ((v - min) / (max - min)) * (height - 4) - 2;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className="mt-2">
      <defs>
        <linearGradient id="sparkGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--color-accent)" stopOpacity="0.3" />
          <stop offset="100%" stopColor="var(--color-accent)" stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <polygon
        points={`0,${height} ${points} ${width},${height}`}
        fill="url(#sparkGrad)"
      />
      <polyline
        points={points}
        fill="none"
        stroke="var(--color-accent)"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
};

// --- Impact Meter Section ---
const ImpactMeter = ({ impact, timeline }) => {
  const [expanded, setExpanded] = useState(false);
  const { t } = useTranslation();

  const hoursAnim = useCountUp(impact?.time_saved?.total_hours);
  const daysAnim = useCountUp(impact?.time_saved?.working_days);
  const analystsAnim = useCountUp(impact?.time_saved?.analysts_equivalent);
  const aiMinAnim = useCountUp(impact?.ai_performance?.ai_minutes);

  const formatNum = useCallback((n, decimals = 1) => {
    if (n == null) return '0';
    return Number(n).toFixed(decimals).replace(/\.0$/, '');
  }, []);

  if (!impact) return null;

  const { time_saved, ai_performance, breakdown, methodology } = impact;

  const metrics = [
    {
      value: formatNum(hoursAnim),
      label: t('dashboard.hours_saved'),
      hero: true,
    },
    {
      value: formatNum(daysAnim),
      label: t('dashboard.days_saved'),
    },
    {
      value: formatNum(analystsAnim),
      label: t('dashboard.analysts_replaced'),
    },
    {
      value: formatNum(aiMinAnim),
      label: t('dashboard.ai_minutes'),
    },
  ];

  const opLabels = {
    proposal_evaluation: t('dashboard.evaluations'),
    evaluation: t('dashboard.evaluations'),
    compliance_check: t('dashboard.compliance'),
    trend_analysis: t('dashboard.trend_reports'),
    hallucination_check: t('dashboard.evidence_checks'),
  };

  return (
    <div className="bg-white rounded-xl shadow-md p-6 mb-8 border border-accent-20 relative overflow-hidden">
      {/* Subtle sigma badge */}
      <div className="absolute top-3 right-4 text-accent-10 text-6xl font-bold select-none pointer-events-none" aria-hidden="true">
        &sigma;I
      </div>

      {/* Header */}
      <div className="mb-5">
        <h2 className="font-heading text-xl text-[var(--color-accent)] flex items-center gap-2">
          <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-accent-10 text-sm font-bold text-[var(--color-accent)]">&sigma;</span>
          {t('dashboard.impact_meter')}
        </h2>
      </div>

      {/* ROW 1: Hero metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        {metrics.map((m, idx) => (
          <div
            key={idx}
            className={`rounded-lg p-4 text-center ${
              m.hero
                ? 'bg-accent-5 border-2 border-accent-30'
                : 'bg-gray-50 border border-gray-100'
            }`}
          >
            <div
              className="text-[var(--color-accent)] font-mono leading-none"
              style={{ fontSize: m.hero ? '2rem' : '1.75rem', fontWeight: 700 }}
            >
              {m.value}
            </div>
            <div className="text-xs text-gray-500 mt-1.5 leading-tight">{m.label}</div>
          </div>
        ))}
      </div>

      {/* Performance bar */}
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-gray-600 mb-4">
        <span>
          {t('dashboard.speed')} <strong className="text-[var(--color-accent)]">{ai_performance.speed_multiplier}x</strong> {t('dashboard.faster_than_manual')}
        </span>
        <span>
          {t('dashboard.cost')} <strong className="text-[var(--color-accent)]">${ai_performance.total_cost_usd}</strong> {t('dashboard.total')}
        </span>
        <span>
          {t('dashboard.cost_per_op')} <strong className="text-[var(--color-accent)]">${ai_performance.cost_per_operation}</strong>
        </span>
        <span>
          {t('dashboard.period')} <strong className="text-[var(--color-accent)]">{time_saved.period_days}</strong> {t('dashboard.days')}
        </span>
      </div>

      {/* ROW 2: Collapsible methodology */}
      <div className="border-t border-gray-100 pt-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-[var(--color-accent)] transition-colors w-full text-left"
        >
          <svg
            className={`w-4 h-4 transition-transform ${expanded ? 'rotate-90' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
          {t('dashboard.how_calculated')}
        </button>

        {expanded && (
          <div className="mt-3 space-y-3">
            {/* Breakdown table */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="space-y-2">
                {breakdown.map((b, idx) => (
                  <div key={idx} className="flex items-center justify-between text-sm font-mono">
                    <span className="text-gray-700">
                      {opLabels[b.operation] || b.operation}
                    </span>
                    <span className="text-gray-500">
                      {b.count} &times; {b.manual_hours_each} hrs
                      <span className="mx-2">=</span>
                      <span className="text-[var(--color-accent)] font-semibold">{b.total_hours_saved} {t('dashboard.hrs_saved')}</span>
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Methodology note */}
            <p className="text-xs text-gray-400 italic leading-relaxed">
              {methodology?.note}. {methodology?.assumptions}
            </p>
          </div>
        )}
      </div>

      {/* ROW 3: Sparkline */}
      {timeline && timeline.length > 1 && (
        <div className="border-t border-gray-100 mt-3 pt-3">
          <div className="text-xs text-gray-400 mb-1">{t('dashboard.cumulative_hours')}</div>
          <Sparkline data={timeline} />
        </div>
      )}

      {/* Footer */}
      <div className="mt-3 text-[10px] text-gray-300 text-right">
        {t('dashboard.metrics_note')}
      </div>
    </div>
  );
};

// --- Pilot & Engagement Outcomes Section ---
const OUTCOME_COLORS = {
  exceeded: { bg: 'bg-emerald-700', label: 'Exceeded' },
  completed: { bg: 'bg-emerald-500', label: 'Completed' },
  ongoing: { bg: 'bg-blue-500', label: 'Ongoing' },
  partial: { bg: 'bg-amber-500', label: 'Partial' },
  failed: { bg: 'bg-red-500', label: 'Failed' },
  cancelled: { bg: 'bg-gray-400', label: 'Cancelled' },
};

const OUTCOME_BADGE = {
  exceeded: 'bg-emerald-100 text-emerald-800',
  completed: 'bg-emerald-50 text-emerald-700',
  ongoing: 'bg-blue-100 text-blue-800',
  partial: 'bg-amber-100 text-amber-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-600',
};

const TYPE_BADGE = {
  pilot: 'bg-indigo-100 text-indigo-700',
  contract: 'bg-teal-100 text-teal-700',
  poc: 'bg-purple-100 text-purple-700',
  trial: 'bg-cyan-100 text-cyan-700',
};

const EngagementOutcomes = ({ data }) => {
  const { t } = useTranslation();
  if (!data) return null;

  const { metrics, distribution, recent_engagements } = data;
  const total = Object.values(distribution).reduce((s, v) => s + v, 0);

  return (
    <div className="bg-white rounded-xl shadow-md p-6 mb-8">
      <h2 className="font-heading text-xl text-teal mb-5">{t('dashboard.pilot_outcomes')}</h2>

      {/* ROW 1 — Metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4 text-center">
          <div className="text-blue-600 font-mono text-3xl font-bold">{metrics.active_pilots}</div>
          <div className="text-xs text-gray-500 mt-1">{t('dashboard.active_pilots')}</div>
        </div>
        <div className="bg-emerald-50 rounded-lg p-4 text-center">
          <div className="text-emerald-600 font-mono text-3xl font-bold">{metrics.completed_engagements}</div>
          <div className="text-xs text-gray-500 mt-1">{t('dashboard.completed_engagements')}</div>
        </div>
        <div className="bg-amber-50 rounded-lg p-4 text-center">
          <div className="text-amber-600 font-mono text-3xl font-bold">
            {metrics.avg_delivery_rating != null ? `★ ${metrics.avg_delivery_rating}/5` : '—'}
          </div>
          <div className="text-xs text-gray-500 mt-1">{t('dashboard.avg_rating')}</div>
        </div>
        <div className="bg-teal-50 rounded-lg p-4 text-center">
          <div className="text-teal font-mono text-3xl font-bold">{metrics.success_rate}%</div>
          <div className="text-xs text-gray-500 mt-1">{t('dashboard.success_rate')}</div>
        </div>
      </div>

      {/* ROW 2 — Stacked outcome bar */}
      {total > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
            <span>{t('dashboard.outcome_distribution')}</span>
            <span className="ml-auto">{total} total</span>
          </div>
          <div className="flex h-6 rounded-full overflow-hidden">
            {Object.entries(OUTCOME_COLORS).map(([key, { bg }]) => {
              const count = distribution[key] || 0;
              if (count === 0) return null;
              const pct = (count / total) * 100;
              return (
                <div
                  key={key}
                  className={`${bg} relative group`}
                  style={{ width: `${pct}%` }}
                  title={`${OUTCOME_COLORS[key].label}: ${count}`}
                />
              );
            })}
          </div>
          <div className="flex flex-wrap gap-3 mt-2">
            {Object.entries(OUTCOME_COLORS).map(([key, { bg, label }]) => {
              const count = distribution[key] || 0;
              if (count === 0) return null;
              return (
                <div key={key} className="flex items-center gap-1.5 text-xs text-gray-600">
                  <span className={`inline-block w-3 h-3 rounded-sm ${bg}`} />
                  {label} ({count})
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ROW 3 — Recent engagements list */}
      {recent_engagements && recent_engagements.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-gray-600 mb-3">{t('dashboard.recent_engagements')}</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-left text-xs text-gray-400">
                  <th className="pb-2 font-medium">{t('dashboard.vendor')}</th>
                  <th className="pb-2 font-medium">{t('dashboard.engagement')}</th>
                  <th className="pb-2 font-medium">{t('dashboard.type')}</th>
                  <th className="pb-2 font-medium">{t('dashboard.outcome')}</th>
                  <th className="pb-2 font-medium text-right">{t('dashboard.date')}</th>
                </tr>
              </thead>
              <tbody>
                {recent_engagements.map((eng) => (
                  <tr key={eng.id} className="border-b border-gray-50">
                    <td className="py-2 text-ink/80 font-medium">{eng.vendor_name}</td>
                    <td className="py-2 text-ink/70">{eng.engagement_title || '—'}</td>
                    <td className="py-2">
                      {eng.engagement_type && (
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${TYPE_BADGE[eng.engagement_type] || 'bg-gray-100 text-gray-600'}`}>
                          {eng.engagement_type}
                        </span>
                      )}
                    </td>
                    <td className="py-2">
                      {eng.outcome && (
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${OUTCOME_BADGE[eng.outcome] || 'bg-gray-100 text-gray-600'}`}>
                          {eng.outcome}
                        </span>
                      )}
                    </td>
                    <td className="py-2 text-ink/50 text-right whitespace-nowrap">
                      {eng.date ? new Date(eng.date).toLocaleDateString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {total === 0 && (
        <p className="text-ink/50 text-sm">{t('dashboard.no_engagement_data')}</p>
      )}
    </div>
  );
};

// --- Sector Intelligence Section (v2) ---
const SectorIntelligence = ({ sectors }) => {
  const [sortBy, setSortBy] = useState('avg_score_desc');
  const [filterBy, setFilterBy] = useState('all');

  if (!sectors || sectors.length === 0) return null;

  const scoreColor = (score) => {
    if (score >= 80) return { text: 'text-emerald-400', border: 'border-emerald-500', bg: 'bg-emerald-500' };
    if (score >= 60) return { text: 'text-amber-400', border: 'border-amber-500', bg: 'bg-amber-500' };
    return { text: 'text-red-400', border: 'border-red-500', bg: 'bg-red-500' };
  };

  // --- Summary metrics ---
  const activeSectorCount = sectors.length;
  const strongest = sectors.reduce((a, b) => (a.avg_score >= b.avg_score ? a : b), sectors[0]);
  const weakest = sectors.reduce((a, b) => (a.avg_score <= b.avg_score ? a : b), sectors[0]);
  const zeroDescCount = sectors.filter(s => (s.desc_certified || 0) === 0).length;

  // --- Filtering ---
  const filtered = sectors.filter(s => {
    if (filterBy === 'flagged') return (s.flagged || 0) > 0;
    if (filterBy === 'missing_desc') return (s.desc_certified || 0) < (s.total_vendor_count || 0);
    if (filterBy === 'top_tier') return (s.top_tier || 0) > 0;
    return true;
  });

  // --- Sorting ---
  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'avg_score_desc') return b.avg_score - a.avg_score;
    if (sortBy === 'avg_vscore_desc') return (b.avg_vscore || 0) - (a.avg_vscore || 0);
    if (sortBy === 'most_proposals') return (b.proposal_count || 0) - (a.proposal_count || 0);
    if (sortBy === 'most_risk') {
      const riskDiff = (b.flagged || 0) - (a.flagged || 0);
      return riskDiff !== 0 ? riskDiff : a.avg_score - b.avg_score;
    }
    return 0;
  });

  const weakestColor = weakest.avg_score < 75 ? 'text-red-500' : weakest.avg_score < 80 ? 'text-amber-500' : 'text-ink/70';

  return (
    <div className="mb-8">
      {/* Summary row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">🏭</span>
            <span className="font-heading text-3xl text-teal">{activeSectorCount}</span>
          </div>
          <h3 className="text-ink/70 text-sm">Active Sectors</h3>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">🏆</span>
            <span className="font-heading text-3xl text-emerald-500">{strongest.avg_score}</span>
          </div>
          <h3 className="text-ink/70 text-sm truncate">{strongest.sector}</h3>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">⚠️</span>
            <span className={`font-heading text-3xl ${weakestColor}`}>{weakest.avg_score}</span>
          </div>
          <h3 className="text-ink/70 text-sm truncate">{weakest.sector}</h3>
        </div>
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">🔍</span>
            <span className={`font-heading text-3xl ${zeroDescCount > 0 ? 'text-red-500' : 'text-teal'}`}>{zeroDescCount}</span>
          </div>
          <h3 className="text-ink/70 text-sm">No DESC Vendors</h3>
        </div>
      </div>

      <div className="mb-5">
        <h2 className="font-heading text-2xl text-teal">Sector Intelligence</h2>
        <p className="text-ink/50 text-sm mt-1">Innovation pipeline health by sector</p>
      </div>

      {/* Sort & filter controls */}
      <div className="bg-[var(--color-table-header-bg,#1E293B)] rounded-xl p-4 mb-5 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">Sort by</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="bg-[var(--color-table-header-bg,#0F172A)] text-white border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
          >
            <option value="avg_score_desc">Avg score (high→low)</option>
            <option value="avg_vscore_desc">Avg vScore (high→low)</option>
            <option value="most_proposals">Most proposals</option>
            <option value="most_risk">Most risk (flagged first)</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value)}
            className="bg-[var(--color-table-header-bg,#0F172A)] text-white border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
          >
            <option value="all">All sectors</option>
            <option value="flagged">Sectors with flagged proposals</option>
            <option value="missing_desc">Sectors missing DESC vendors</option>
            <option value="top_tier">Sectors with top-tier vendors</option>
          </select>
        </div>
        <span className="text-sm text-gray-400 ml-auto">
          Showing {sorted.length} of {sectors.length} sectors
        </span>
      </div>

      {/* Sector grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {sorted.map((s, idx) => {
          const colors = scoreColor(s.avg_score);
          const totalVendors = s.total_vendor_count || 0;
          const descCount = s.desc_certified || 0;
          const descPct = totalVendors > 0 ? Math.round((descCount / totalVendors) * 100) : 0;
          const descColorClass = descPct === 0 ? 'text-red-500' : descPct === 100 ? 'text-emerald-500' : 'text-ink/50';

          return (
            <div
              key={s.sector}
              className={`bg-white rounded-xl shadow-md p-5 border-l-4 ${colors.border} relative`}
            >
              {/* Rank badge */}
              <span className="absolute top-2 right-3 text-[10px] text-ink/30 font-mono">#{idx + 1}</span>

              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-heading text-base text-ink/90 leading-tight">{s.sector}</h3>
                  <span className="text-[11px] text-ink/40">{s.proposal_count || 0} proposals</span>
                </div>
                <div className="text-right flex-shrink-0 ml-3">
                  <div className={`font-mono text-2xl font-bold leading-none ${colors.text}`}>
                    {s.avg_score}
                  </div>
                  <div className="text-[10px] text-ink/40 mt-0.5">avg score</div>
                </div>
              </div>

              {/* vScore */}
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs text-ink/50">vScore</span>
                <span className="font-mono text-lg font-semibold text-teal">{s.avg_vscore}</span>
              </div>

              {/* Progress bar */}
              <div className="w-full bg-gray-100 rounded-full h-2 mb-3">
                <div
                  className={`h-2 rounded-full ${colors.bg} transition-all duration-500`}
                  style={{ width: `${Math.min(s.avg_score, 100)}%` }}
                />
              </div>

              {/* Status pills */}
              <div className="flex flex-wrap gap-1.5 mb-3">
                {s.shortlisted > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                    {s.shortlisted} shortlisted
                  </span>
                )}
                {s.under_review > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700">
                    {s.under_review} under review
                  </span>
                )}
                {s.flagged > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                    {s.flagged} flagged
                  </span>
                )}
                {s.desc_certified > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-teal-100 text-teal-700">
                    {s.desc_certified} DESC certified
                  </span>
                )}
                {s.top_tier > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700">
                    {s.top_tier} top tier
                  </span>
                )}
              </div>

              {/* DESC coverage line */}
              <div className={`text-xs border-t border-gray-100 pt-2 ${descColorClass}`}>
                DESC: {descCount} of {totalVendors} vendors certified ({descPct}%)
                {descPct === 0 && totalVendors > 0 && <span className="ml-1 font-semibold">— gap identified</span>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// --- Pipeline KPI Card ---
const KPICard = ({ name, value, display, benchmark, unit }) => {
  const numericValue = value != null ? Number(value) : 0;
  const animated = useCountUp(numericValue);

  const formatValue = () => {
    if (value == null) return '—';
    if (unit === 'usd') return `$${animated.toFixed(2)}`;
    if (unit === 'hours') {
      return numericValue >= 48
        ? `${(animated / 24).toFixed(1)}d`
        : `${animated.toFixed(1)}h`;
    }
    if (unit === 'percent') return `${animated.toFixed(1)}%`;
    if (unit === 'proposals_per_day') return animated.toFixed(1);
    return animated.toFixed(1);
  };

  const getTrend = () => {
    if (value == null) return { icon: '→', color: 'text-gray-400' };
    if (unit === 'hours') {
      if (numericValue <= 24) return { icon: '↑', color: 'text-emerald-500' };
      if (numericValue <= 48) return { icon: '→', color: 'text-amber-500' };
      return { icon: '↓', color: 'text-red-500' };
    }
    if (unit === 'usd') {
      if (numericValue <= 1) return { icon: '↑', color: 'text-emerald-500' };
      if (numericValue <= 5) return { icon: '→', color: 'text-amber-500' };
      return { icon: '↓', color: 'text-red-500' };
    }
    if (unit === 'percent') {
      if (numericValue >= 80) return { icon: '↑', color: 'text-emerald-500' };
      if (numericValue >= 50) return { icon: '→', color: 'text-amber-500' };
      return { icon: '↓', color: 'text-red-500' };
    }
    if (numericValue >= 3) return { icon: '↑', color: 'text-emerald-500' };
    if (numericValue >= 1) return { icon: '→', color: 'text-amber-500' };
    return { icon: '↓', color: 'text-red-500' };
  };

  const trend = getTrend();

  return (
    <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100 hover:shadow-md transition-shadow">
      <div className="text-xs text-ink/50 font-body mb-2 leading-tight">{name}</div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-mono font-bold text-teal">{formatValue()}</span>
        <span className={`text-lg font-bold ${trend.color}`}>{trend.icon}</span>
      </div>
      {display && value != null && (
        <div className="text-[11px] text-ink/60 mt-1 truncate" title={display}>{display}</div>
      )}
      <div className="text-[11px] text-ink/40 mt-1.5">{benchmark}</div>
    </div>
  );
};

// --- Pipeline Performance Section ---
const PipelineKPIs = ({ kpis }) => {
  if (!kpis || kpis.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="mb-4">
        <h2 className="font-heading text-2xl text-teal">Pipeline Performance</h2>
        <p className="text-ink/50 text-sm mt-1">Operational KPIs for the innovation sourcing workflow</p>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {kpis.map((kpi) => (
          <KPICard key={kpi.id} {...kpi} />
        ))}
      </div>
    </div>
  );
};

// --- Channel Analytics Section ---
const CHANNEL_LABELS = {
  manual: 'Manual',
  business_in_dubai: 'Business in Dubai',
  expand_north_star: 'Expand North Star',
  ignyte: 'Ignyte',
  partner_referral: 'Partner Referral',
  email: 'Email',
  api: 'API',
};

const CHANNEL_DOT_COLORS = {
  manual: 'bg-gray-500',
  business_in_dubai: 'bg-blue-500',
  expand_north_star: 'bg-purple-500',
  ignyte: 'bg-orange-500',
  partner_referral: 'bg-indigo-500',
  email: 'bg-sky-500',
  api: 'bg-emerald-500',
};

const CHANNEL_BAR_COLORS = {
  manual: 'bg-gray-400',
  business_in_dubai: 'bg-blue-500',
  expand_north_star: 'bg-purple-500',
  ignyte: 'bg-orange-500',
  partner_referral: 'bg-indigo-500',
  email: 'bg-sky-500',
  api: 'bg-emerald-500',
};

const ChannelAnalytics = ({ data }) => {
  if (!data) return null;

  const { channels, top_channel, best_converting, total_signals } = data;
  const maxCases = Math.max(...channels.map(ch => ch.total_cases), 1);

  return (
    <div className="mb-8">
      <div className="mb-4">
        <h2 className="font-heading text-2xl text-teal">Channel Analytics</h2>
        <p className="text-ink/50 text-sm mt-1">Volume, conversion rates, and performance by intake source</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
          <div className="text-xs text-ink/50 mb-1">Total Signals</div>
          <div className="text-3xl font-mono font-bold text-teal">{total_signals}</div>
          <div className="text-[11px] text-ink/40 mt-1">Across all channels</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
          <div className="text-xs text-ink/50 mb-1">Top Channel</div>
          <div className="flex items-center gap-2 mt-1">
            {top_channel && <span className={`inline-block w-3 h-3 rounded-full ${CHANNEL_DOT_COLORS[top_channel] || 'bg-gray-400'}`} />}
            <span className="text-lg font-heading font-bold text-ink/80">{top_channel ? CHANNEL_LABELS[top_channel] || top_channel : '—'}</span>
          </div>
          <div className="text-[11px] text-ink/40 mt-1">Highest volume</div>
        </div>
        <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
          <div className="text-xs text-ink/50 mb-1">Best Converting</div>
          <div className="flex items-center gap-2 mt-1">
            {best_converting && <span className={`inline-block w-3 h-3 rounded-full ${CHANNEL_DOT_COLORS[best_converting] || 'bg-gray-400'}`} />}
            <span className="text-lg font-heading font-bold text-ink/80">{best_converting ? CHANNEL_LABELS[best_converting] || best_converting : '—'}</span>
          </div>
          <div className="text-[11px] text-ink/40 mt-1">Highest conversion rate</div>
        </div>
      </div>

      {/* Volume bars */}
      <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100 mb-6">
        <h3 className="text-sm font-semibold text-ink/70 mb-4">Volume by Channel</h3>
        <div className="space-y-3">
          {channels.map((ch) => (
            <div key={ch.channel} className="flex items-center gap-3">
              <span className={`inline-block w-2.5 h-2.5 rounded-full flex-shrink-0 ${CHANNEL_DOT_COLORS[ch.channel] || 'bg-gray-400'}`} />
              <span className="text-sm text-ink/70 w-36 truncate flex-shrink-0">{CHANNEL_LABELS[ch.channel] || ch.channel}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-5 overflow-hidden">
                <div
                  className={`h-full rounded-full ${CHANNEL_BAR_COLORS[ch.channel] || 'bg-gray-400'} transition-all duration-500`}
                  style={{ width: `${Math.max((ch.total_cases / maxCases) * 100, ch.total_cases > 0 ? 2 : 0)}%` }}
                />
              </div>
              <span className="text-sm font-mono font-semibold text-ink/60 w-10 text-right flex-shrink-0">{ch.total_cases}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-left text-xs text-ink/50">
              <th className="px-5 py-3 font-medium">Channel</th>
              <th className="px-4 py-3 font-medium text-right">Cases</th>
              <th className="px-4 py-3 font-medium text-right">Active</th>
              <th className="px-4 py-3 font-medium text-right">Completed</th>
              <th className="px-4 py-3 font-medium text-right">Conversion</th>
              <th className="px-4 py-3 font-medium text-right">Avg Days</th>
              <th className="px-4 py-3 font-medium text-right">Proposals</th>
              <th className="px-4 py-3 font-medium text-right">Avg Score</th>
            </tr>
          </thead>
          <tbody>
            {channels.map((ch) => (
              <tr key={ch.channel} className="border-b border-gray-50 hover:bg-gray-50/50">
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    <span className={`inline-block w-2.5 h-2.5 rounded-full ${CHANNEL_DOT_COLORS[ch.channel] || 'bg-gray-400'}`} />
                    <span className="font-medium text-ink/80">{CHANNEL_LABELS[ch.channel] || ch.channel}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-mono text-ink/70">{ch.total_cases}</td>
                <td className="px-4 py-3 text-right font-mono text-ink/70">{ch.active_cases}</td>
                <td className="px-4 py-3 text-right font-mono text-ink/70">{ch.completed_cases}</td>
                <td className="px-4 py-3 text-right">
                  <span className={`font-mono font-semibold ${
                    ch.conversion_rate >= 50 ? 'text-emerald-600' :
                    ch.conversion_rate >= 20 ? 'text-amber-600' :
                    ch.total_cases > 0 ? 'text-ink/60' : 'text-ink/30'
                  }`}>
                    {ch.conversion_rate}%
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-mono text-ink/60">
                  {ch.avg_time_to_completion != null ? `${ch.avg_time_to_completion}d` : '—'}
                </td>
                <td className="px-4 py-3 text-right font-mono text-ink/70">{ch.linked_proposals}</td>
                <td className="px-4 py-3 text-right">
                  {ch.avg_evaluation_score != null ? (
                    <span className={`font-mono font-semibold ${
                      ch.avg_evaluation_score >= 70 ? 'text-emerald-600' :
                      ch.avg_evaluation_score >= 50 ? 'text-amber-600' : 'text-red-500'
                    }`}>
                      {ch.avg_evaluation_score}
                    </span>
                  ) : (
                    <span className="text-ink/30">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// --- Active Alerts Banner (above stat cards) ---
const ALERT_SEVERITY_STYLES = {
  critical: 'bg-red-100 text-red-800 border-red-300',
  high: 'bg-orange-100 text-orange-800 border-orange-300',
  medium: 'bg-amber-100 text-amber-800 border-amber-300',
  low: 'bg-blue-100 text-blue-800 border-blue-300',
};

const ALERT_TYPE_ICONS = {
  security: '\u{1F6E1}\uFE0F',
  compliance: '\u{1F512}',
  ai_anomaly: '\u{1F916}',
  system: '\u{2699}\uFE0F',
};

const ActiveAlerts = ({ alerts, onResolve }) => {
  const { t } = useTranslation();
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="bg-red-50 border border-red-200 rounded-xl p-5 mb-8">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
        </svg>
        <h3 className="font-heading text-base text-red-800">{t('alerts.active_alerts')}</h3>
        <span className="ml-auto text-xs text-red-600 font-semibold">{alerts.length} {t('alerts.unresolved')}</span>
      </div>
      <div className="space-y-2">
        {alerts.slice(0, 5).map((alert) => (
          <div
            key={alert.id}
            className="flex items-center gap-3 bg-white rounded-lg px-4 py-2.5 border border-red-100"
          >
            <span className="text-base">{ALERT_TYPE_ICONS[alert.alert_type] || '\u26A0\uFE0F'}</span>
            <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold border ${ALERT_SEVERITY_STYLES[alert.severity] || ALERT_SEVERITY_STYLES.medium}`}>
              {alert.severity?.toUpperCase()}
            </span>
            <span className="flex-1 text-sm text-ink font-medium truncate">{alert.title}</span>
            <button
              onClick={() => onResolve(alert.id)}
              className="text-xs px-2.5 py-1 rounded-md bg-teal/10 text-teal hover:bg-teal/20 transition-colors font-medium flex-shrink-0"
            >
              {t('alerts.mark_resolved')}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { session, loading: authLoading } = useAuth();
  const { role: userRole } = useUserRole();
  const { t } = useTranslation();
  const isVendor = userRole === 'vendor';
  const canViewAlerts = userRole === 'admin' || userRole === 'compliance_officer';
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [user, setUser] = useState(null);
  const [impact, setImpact] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [vendorSummary, setVendorSummary] = useState(null);
  const [engagements, setEngagements] = useState(null);
  const [sectors, setSectors] = useState(null);
  const [pipelineKpis, setPipelineKpis] = useState(null);
  const [activeAlerts, setActiveAlerts] = useState([]);
  const [channelAnalytics, setChannelAnalytics] = useState(null);
  const [activeSourcingCases, setActiveSourcingCases] = useState(0);
  const [signalsThisMonth, setSignalsThisMonth] = useState(0);

  useEffect(() => {
    // Don't fetch until auth has settled
    if (authLoading) return;

    // No session after auth settled — redirect to login
    if (!session) {
      navigate('/login', { replace: true });
      return;
    }

    const fetchData = async (retryCount = 0) => {
      try {
        if (retryCount === 0) setLoading(true);
        const [userRes, statsRes, impactRes, timelineRes] = await Promise.all([
          api.get('/api/v1/users/me'),
          api.get('/api/v1/dashboard/stats'),
          api.get('/api/v1/dashboard/impact').catch(() => ({ data: null })),
          api.get('/api/v1/dashboard/impact/timeline').catch(() => ({ data: null })),
        ]);
        setUser(userRes.data);
        setStats(statsRes.data);
        setImpact(impactRes.data);
        setTimeline(timelineRes.data?.timeline || null);

        // Fetch engagement outcomes and sector intelligence (non-critical)
        try {
          const engRes = await api.get('/api/v1/dashboard/engagements');
          setEngagements(engRes.data);
        } catch {
          // Non-critical
        }

        try {
          const sectorsRes = await api.get('/api/v1/dashboard/sectors');
          setSectors(sectorsRes.data);
        } catch {
          // Non-critical
        }

        // Fetch pipeline KPIs and channel analytics (admin/analyst/executive only)
        if (userRes.data?.role !== 'vendor') {
          try {
            const kpiRes = await api.get('/api/v1/dashboard/pipeline-kpis');
            setPipelineKpis(kpiRes.data?.kpis || null);
          } catch {
            // Non-critical
          }

          try {
            const channelRes = await api.get('/api/v1/dashboard/channel-analytics');
            setChannelAnalytics(channelRes.data || null);
          } catch {
            // Non-critical
          }
        }

        // Fetch sourcing cases for Active Sourcing Cases + Signals This Month
        try {
          const scRes = await api.get('/api/v1/sourcing-cases');
          const cases = scRes.data?.sourcing_cases || scRes.data || [];
          const activeStatuses = ['open', 'matching', 'evaluating'];
          setActiveSourcingCases(cases.filter(c => activeStatuses.includes(c.status)).length);
          const thirtyDaysAgo = new Date();
          thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
          setSignalsThisMonth(cases.filter(c => c.created_at && new Date(c.created_at) >= thirtyDaysAgo).length);
        } catch {
          // Non-critical
        }

        // Fetch active alerts (admin/compliance only)
        if (userRes.data?.role === 'admin' || userRes.data?.role === 'compliance_officer') {
          try {
            const alertsRes = await api.get('/api/v1/alerts');
            setActiveAlerts(alertsRes.data || []);
          } catch {
            // Non-critical
          }
        }

        // Fetch vendor-specific summary if vendor role
        if (userRes.data?.role === 'vendor') {
          try {
            const vendorRes = await api.get('/api/v1/dashboard/vendor-summary');
            setVendorSummary(vendorRes.data);
          } catch {
            // Non-critical
          }
        }

        setLoading(false);
      } catch (err) {
        const is403 = err?.response?.status === 403;
        if (is403 && retryCount < 1) {
          // Single retry after 1s for token propagation race
          setTimeout(() => fetchData(retryCount + 1), 1000);
          return;
        }
        if (is403) {
          setError('Session expired, redirecting to login...');
          setLoading(false);
          setTimeout(() => navigate('/login', { replace: true }), 2000);
        } else {
          setError(getErrorMessage(err));
          setLoading(false);
        }
      }
    };
    fetchData();
  }, [authLoading, session, navigate]);

  const handleResolveAlert = async (alertId) => {
    try {
      await api.put(`/api/v1/alerts/${alertId}/resolve`);
      setActiveAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch {
      // Silently fail
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[var(--color-accent)]"></div>
          <span className="text-teal font-heading text-lg">Loading dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-cream p-4 md:p-8">
        <div className="max-w-4xl mx-auto bg-burgundy/10 border border-burgundy rounded-lg p-6">
          <h2 className="font-heading text-2xl text-burgundy mb-2">Error Loading Dashboard</h2>
          <p className="text-ink">{error}</p>
        </div>
      </div>
    );
  }

  // Vendor role gets a dedicated dashboard experience
  if (isVendor) {
    return (
      <div className="min-h-screen bg-cream p-4 md:p-8">
        <div className="max-w-7xl mx-auto">
          <DemoBanner />
          <VendorDashboard user={user} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <DemoBanner />
        <header className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="font-heading text-3xl md:text-4xl text-teal mb-1">{t('nav.dashboard')}</h1>
            <p className="text-sm text-teal/70 font-medium mb-1">{t('dashboard.command_center')}</p>
            <p className="text-ink/70 flex items-center gap-2">
              {t('dashboard.title')}, {user?.full_name || t('common.user')}
              {user?.role && ROLE_BADGES[user.role] && (
                <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold border ${ROLE_BADGES[user.role].color}`}>
                  {ROLE_BADGES[user.role].label}
                </span>
              )}
            </p>
          </div>
          {!isVendor && (
            <button
              onClick={() => window.open('/board-brief', '_blank')}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 transition-colors shadow-md"
            >
              <span>📄</span> Executive Board Brief
            </button>
          )}
        </header>

        {/* Active Alerts — admin/compliance only */}
        {canViewAlerts && <ActiveAlerts alerts={activeAlerts} onResolve={handleResolveAlert} />}

        {/* Vendor-specific summary cards */}
        {isVendor && vendorSummary && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* Your Proposals */}
            <Link to="/proposals" className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">📋</span>
                <span className="font-heading text-4xl text-teal">{vendorSummary.proposal_count || 0}</span>
              </div>
              <h3 className="text-ink/70 text-sm font-medium">Your Proposals</h3>
              {vendorSummary.status_counts && Object.keys(vendorSummary.status_counts).length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {Object.entries(vendorSummary.status_counts).map(([status, count]) => (
                    <span key={status} className="inline-block bg-cream text-ink/60 px-2 py-0.5 rounded text-xs">
                      {status.replace(/_/g, ' ')}: {count}
                    </span>
                  ))}
                </div>
              )}
            </Link>

            {/* Your vScore */}
            <Link to="/vendor-intelligence" className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">⭐</span>
                <span className="font-heading text-4xl text-gold">
                  {vendorSummary.vscore?.average_compliance_score != null
                    ? vendorSummary.vscore.average_compliance_score.toFixed(1)
                    : '—'}
                </span>
              </div>
              <h3 className="text-ink/70 text-sm font-medium">Your vScore</h3>
              <div className="mt-2 text-xs text-ink/50">
                {vendorSummary.vscore?.submission_count || 0} submissions
                {vendorSummary.vscore?.is_desc_approved && (
                  <span className="ml-2 inline-flex items-center gap-1 text-emerald-600 font-semibold">
                    DESC Approved
                  </span>
                )}
              </div>
            </Link>

            {/* Your Latest Evaluation */}
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-2xl">📊</span>
                <span className={`font-heading text-4xl ${
                  vendorSummary.latest_evaluation?.composite_score > 70
                    ? 'text-teal'
                    : vendorSummary.latest_evaluation?.composite_score >= 40
                    ? 'text-gold'
                    : vendorSummary.latest_evaluation?.composite_score != null
                    ? 'text-burgundy'
                    : 'text-ink/30'
                }`}>
                  {vendorSummary.latest_evaluation?.composite_score != null
                    ? vendorSummary.latest_evaluation.composite_score.toFixed(1)
                    : '—'}
                </span>
              </div>
              <h3 className="text-ink/70 text-sm font-medium">Latest Evaluation</h3>
              {vendorSummary.latest_evaluation && (
                <div className="mt-2 space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-ink/50">Relevance</span>
                    <span className="font-medium text-ink/70">{vendorSummary.latest_evaluation.relevance_score?.toFixed(1) || '—'}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-ink/50">Feasibility</span>
                    <span className="font-medium text-ink/70">{vendorSummary.latest_evaluation.feasibility_score?.toFixed(1) || '—'}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-ink/50">Sector Alignment</span>
                    <span className="font-medium text-ink/70">{vendorSummary.latest_evaluation.sector_alignment_score?.toFixed(1) || '—'}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-ink/50">Compliance</span>
                    <span className="font-medium text-ink/70">{vendorSummary.latest_evaluation.compliance_score?.toFixed(1) || '—'}</span>
                  </div>
                  {vendorSummary.latest_evaluation.novelty_score != null && (
                    <div className="flex justify-between text-xs">
                      <span className="text-ink/50">Innovation Novelty</span>
                      <span className="font-medium text-ink/70">{vendorSummary.latest_evaluation.novelty_score?.toFixed(1) || '—'}</span>
                    </div>
                  )}
                  {vendorSummary.latest_evaluation.proposal_id && (
                    <Link
                      to={`/proposals/${vendorSummary.latest_evaluation.proposal_id}`}
                      className="block mt-2 text-xs text-teal hover:underline"
                    >
                      View full evaluation →
                    </Link>
                  )}
                </div>
              )}
              {!vendorSummary.latest_evaluation && (
                <p className="mt-2 text-xs text-ink/40">No evaluations yet</p>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4 md:gap-6 mb-8">
          <StatCard
            title="Active Sourcing Cases"
            value={activeSourcingCases}
            icon="🎯"
            color="teal"
          />
          <StatCard
            title="Signals This Month"
            value={signalsThisMonth}
            icon="📡"
            color="teal"
          />
          <StatCard
            title="Solutions Submitted"
            value={stats?.total_proposals || 0}
            icon="📋"
            color="teal"
          />
          <StatCard
            title="Evaluated"
            value={stats?.evaluated || 0}
            icon="✅"
            color="teal"
          />
          <StatCard
            title="Shortlisted"
            value={stats?.shortlisted || 0}
            icon="🏆"
            color="teal"
          />
          <StatCard
            title="Awaiting Assessment"
            value={stats?.pending_evaluation || 0}
            icon="⏳"
            color="gold"
          />
          <StatCard
            title="Compliance Audits"
            value={stats?.compliance_audits || 0}
            icon="🔒"
            color="teal"
          />
          <StatCard
            title="Average Score"
            value={stats?.average_score != null ? stats.average_score : '—'}
            icon="📊"
            color="gold"
          />
        </div>

        {/* Pipeline Performance KPIs — right after stat cards */}
        {!isVendor && <PipelineKPIs kpis={pipelineKpis} />}

        {/* Channel Analytics */}
        {!isVendor && <ChannelAnalytics data={channelAnalytics} />}

        {/* σI Impact Meter — below Pipeline & Channel Analytics */}
        {!isVendor && <ImpactMeter impact={impact} timeline={timeline} />}

        {/* Pilot & Engagement Outcomes */}
        <EngagementOutcomes data={engagements} />

        {/* Sector Intelligence */}
        <SectorIntelligence sectors={sectors} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="font-heading text-2xl text-teal mb-4">Recent Activity</h2>
            {stats?.recent_proposals?.length > 0 ? (
              <ul className="space-y-3">
                {stats.recent_proposals.slice(0, 5).map(p => (
                  <li key={p.id} className="border-b border-cream pb-2">
                    <Link to={`/proposals/${p.id}`} className="text-teal hover:underline font-medium">
                      {p.title}
                    </Link>
                    <div className="text-sm text-ink/60 mt-1">
                      {p.sector} • {p.status}
                      {p.composite_score != null && ` • Score: ${p.composite_score}`}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-ink/60">No recent proposals</p>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="font-heading text-2xl text-teal mb-4">Quick Links</h2>
            <div className="space-y-3">
              <QuickLink to="/proposals" label="View All Proposals" icon="📋" />
              {user?.role === 'vendor' && <QuickLink to="/proposals/new" label="Submit New Proposal" icon="➕" />}
              {(user?.role === 'analyst' || user?.role === 'executive') && <QuickLink to="/evaluations" label="Evaluations" icon="📊" />}
              <QuickLink to="/vendors" label="Vendors" icon="🏢" />
              <QuickLink to="/business-groups" label="Business Groups" icon="👥" />
              {user?.role === 'compliance_officer' && <QuickLink to="/compliance-audits" label="Compliance Audits" icon="🔒" />}
              <QuickLink to="/trend-analyses" label="Trend Analyses" icon="📈" />
              <QuickLink to="/ai-interactions" label="AI Interactions" icon="🤖" />
            </div>
          </div>
        </div>

        {/* Approved / Rejected summary */}
        {(stats?.approved > 0 || stats?.rejected > 0) && (
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="font-heading text-2xl text-teal mb-4">Decision Summary</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="border border-cream rounded-lg p-4 text-center">
                <div className="font-heading text-3xl text-teal">{stats.approved || 0}</div>
                <div className="text-sm text-ink/60 mt-1">Approved</div>
              </div>
              <div className="border border-cream rounded-lg p-4 text-center">
                <div className="font-heading text-3xl text-burgundy">{stats.rejected || 0}</div>
                <div className="text-sm text-ink/60 mt-1">Rejected</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon, color }) => {
  const colorClass = color === 'teal' ? 'text-teal' : 'text-gold';
  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span className={`font-heading text-3xl ${colorClass}`}>{value}</span>
      </div>
      <h3 className="text-ink/70 text-sm">{title}</h3>
    </div>
  );
};

const QuickLink = ({ to, label, icon }) => (
  <Link
    to={to}
    className="flex items-center space-x-3 p-3 rounded-lg hover:bg-cream transition-colors"
  >
    <span className="text-xl">{icon}</span>
    <span className="text-teal hover:underline">{label}</span>
  </Link>
);

export default Dashboard;

import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { useAuth } from '../lib/auth';
import { ROLE_BADGES } from '../config/rolePermissions';
import { useUserRole } from '../lib/userRole';
import DemoBanner from '../components/DemoBanner';

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
      label: 'analyst-hours saved',
      hero: true,
    },
    {
      value: formatNum(daysAnim),
      label: 'working days saved',
    },
    {
      value: formatNum(analystsAnim),
      label: 'full-time analysts replaced',
    },
    {
      value: formatNum(aiMinAnim),
      label: 'AI minutes (actual)',
    },
  ];

  const opLabels = {
    proposal_evaluation: 'Evaluations',
    evaluation: 'Evaluations',
    compliance_check: 'Compliance',
    trend_analysis: 'Trend Reports',
    hallucination_check: 'Shield Checks',
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
          Impact Meter &mdash; Return on Time
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
          Speed: <strong className="text-[var(--color-accent)]">{ai_performance.speed_multiplier}x</strong> faster than manual
        </span>
        <span>
          Cost: <strong className="text-[var(--color-accent)]">${ai_performance.total_cost_usd}</strong> total
        </span>
        <span>
          Cost per operation: <strong className="text-[var(--color-accent)]">${ai_performance.cost_per_operation}</strong>
        </span>
        <span>
          Period: <strong className="text-[var(--color-accent)]">{time_saved.period_days}</strong> days
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
          How we calculated this
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
                      <span className="text-[var(--color-accent)] font-semibold">{b.total_hours_saved} hrs saved</span>
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
          <div className="text-xs text-gray-400 mb-1">Cumulative hours saved over time</div>
          <Sparkline data={timeline} />
        </div>
      )}

      {/* Footer */}
      <div className="mt-3 text-[10px] text-gray-300 text-right">
        All metrics calculated from live platform data in real-time
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
  if (!data) return null;

  const { metrics, distribution, recent_engagements } = data;
  const total = Object.values(distribution).reduce((s, v) => s + v, 0);

  return (
    <div className="bg-white rounded-xl shadow-md p-6 mb-8">
      <h2 className="font-heading text-xl text-teal mb-5">Pilot & Engagement Outcomes</h2>

      {/* ROW 1 — Metric cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4 text-center">
          <div className="text-blue-600 font-mono text-3xl font-bold">{metrics.active_pilots}</div>
          <div className="text-xs text-gray-500 mt-1">Active Pilots</div>
        </div>
        <div className="bg-emerald-50 rounded-lg p-4 text-center">
          <div className="text-emerald-600 font-mono text-3xl font-bold">{metrics.completed_engagements}</div>
          <div className="text-xs text-gray-500 mt-1">Completed Engagements</div>
        </div>
        <div className="bg-amber-50 rounded-lg p-4 text-center">
          <div className="text-amber-600 font-mono text-3xl font-bold">
            {metrics.avg_delivery_rating != null ? `★ ${metrics.avg_delivery_rating}/5` : '—'}
          </div>
          <div className="text-xs text-gray-500 mt-1">Avg Delivery Rating</div>
        </div>
        <div className="bg-teal-50 rounded-lg p-4 text-center">
          <div className="text-teal font-mono text-3xl font-bold">{metrics.success_rate}%</div>
          <div className="text-xs text-gray-500 mt-1">Success Rate</div>
        </div>
      </div>

      {/* ROW 2 — Stacked outcome bar */}
      {total > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2 text-xs text-gray-500">
            <span>Outcome Distribution</span>
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
          <h3 className="text-sm font-semibold text-gray-600 mb-3">Recent Engagements</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-left text-xs text-gray-400">
                  <th className="pb-2 font-medium">Vendor</th>
                  <th className="pb-2 font-medium">Engagement</th>
                  <th className="pb-2 font-medium">Type</th>
                  <th className="pb-2 font-medium">Outcome</th>
                  <th className="pb-2 font-medium text-right">Date</th>
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
        <p className="text-ink/50 text-sm">No engagement data available yet.</p>
      )}
    </div>
  );
};

const Dashboard = () => {
  const { session, loading: authLoading } = useAuth();
  const { role: userRole } = useUserRole();
  const isVendor = userRole === 'vendor';
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [user, setUser] = useState(null);
  const [impact, setImpact] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [vendorSummary, setVendorSummary] = useState(null);
  const [engagements, setEngagements] = useState(null);

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

        // Fetch engagement outcomes (non-critical)
        try {
          const engRes = await api.get('/api/v1/dashboard/engagements');
          setEngagements(engRes.data);
        } catch {
          // Non-critical
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
      <div className="min-h-screen bg-cream p-8">
        <div className="max-w-4xl mx-auto bg-burgundy/10 border border-burgundy rounded-lg p-6">
          <h2 className="font-heading text-2xl text-burgundy mb-2">Error Loading Dashboard</h2>
          <p className="text-ink">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-7xl mx-auto">
        <DemoBanner />
        <header className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="font-heading text-4xl text-teal mb-2">Dashboard</h1>
            <p className="text-ink/70 flex items-center gap-2">
              Welcome back, {user?.full_name || 'User'}
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

        {/* σI Impact Meter — ABOVE existing stats */}
        {!isVendor && <ImpactMeter impact={impact} timeline={timeline} />}

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

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-6 mb-8">
          <StatCard
            title="Total Proposals"
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
            title="Pending Evaluation"
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

        {/* Pilot & Engagement Outcomes */}
        <EngagementOutcomes data={engagements} />

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

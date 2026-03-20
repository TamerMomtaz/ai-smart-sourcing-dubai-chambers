import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const GOLD = '#B8904A';
const TEAL = '#0D9488';
const DARK_SURFACE = '#1E293B';

const SigmaIcon = ({ size = 24, color = GOLD }) => (
  <span
    style={{
      fontFamily: 'Georgia, "Times New Roman", serif',
      fontSize: size,
      fontWeight: 700,
      color,
      letterSpacing: '-0.05em',
      userSelect: 'none',
    }}
  >
    σI
  </span>
);

const SummaryCard = ({ title, value, subtitle, icon }) => (
  <div
    className="rounded-xl p-6 flex flex-col justify-between"
    style={{ backgroundColor: DARK_SURFACE, minHeight: 160 }}
  >
    <div className="flex items-start justify-between">
      <span className="text-slate-400 text-sm font-medium uppercase tracking-wider">
        {title}
      </span>
      <span className="text-2xl">{icon}</span>
    </div>
    <div className="mt-3">
      <div
        className="text-3xl font-bold text-white"
        style={{ fontFamily: '"JetBrains Mono", "Fira Code", "Courier New", monospace' }}
      >
        {value}
      </div>
      {subtitle && (
        <div className="text-slate-400 text-xs mt-2 leading-relaxed">{subtitle}</div>
      )}
    </div>
  </div>
);

const getCostColor = (cost) => {
  if (cost < 0.01) return '#22C55E';
  if (cost <= 0.10) return '#F59E0B';
  return '#EF4444';
};

const ShieldIcon = ({ size = 20, color = TEAL }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const ShieldStatsSection = ({ stats }) => {
  if (!stats || stats.total_checks === 0) return null;

  const avgScore = stats.average_grounding_score || 0;
  const scoreColor = avgScore >= 85 ? '#10B981' : avgScore >= 65 ? '#F59E0B' : '#EF4444';
  const dist = stats.risk_distribution || {};

  return (
    <div className="rounded-xl p-6 mb-8" style={{ backgroundColor: DARK_SURFACE, borderTop: `3px solid ${TEAL}` }}>
      <div className="flex items-center gap-3 mb-6">
        <ShieldIcon size={24} color={TEAL} />
        <h3 className="text-white text-xl font-bold">Hallucination Shield — Aggregate Integrity</h3>
        {stats.all_verified && (
          <span className="ml-auto inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
            All evaluations verified
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[#0F172A] rounded-lg p-4 text-center">
          <p className="text-3xl font-bold" style={{ color: scoreColor, fontFamily: '"JetBrains Mono", monospace' }}>
            {avgScore}%
          </p>
          <p className="text-slate-400 text-xs mt-1">Avg Grounding Score</p>
        </div>
        <div className="bg-[#0F172A] rounded-lg p-4 text-center">
          <p className="text-3xl font-bold text-white" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
            {stats.total_checks}
            <span className="text-slate-500 text-sm">/{stats.total_evaluations || '?'}</span>
          </p>
          <p className="text-slate-400 text-xs mt-1">Checks Run</p>
        </div>
        <div className="bg-[#0F172A] rounded-lg p-4">
          <p className="text-slate-400 text-xs mb-2">Risk Distribution</p>
          <div className="flex items-end gap-2">
            <div className="flex-1 text-center">
              <p className="text-emerald-400 font-bold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>{dist.low || 0}</p>
              <p className="text-slate-500 text-xs">Low</p>
            </div>
            <div className="flex-1 text-center">
              <p className="text-amber-400 font-bold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>{dist.medium || 0}</p>
              <p className="text-slate-500 text-xs">Med</p>
            </div>
            <div className="flex-1 text-center">
              <p className="text-red-400 font-bold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>{dist.high || 0}</p>
              <p className="text-slate-500 text-xs">High</p>
            </div>
          </div>
        </div>
        <div className="bg-[#0F172A] rounded-lg p-4 text-center">
          <p className="text-3xl font-bold" style={{ color: TEAL, fontFamily: '"JetBrains Mono", monospace' }}>
            {(stats.total_verification_iu || 0).toFixed(2)}
          </p>
          <p className="text-slate-400 text-xs mt-1">Shield IU Consumed</p>
        </div>
      </div>
    </div>
  );
};

const AIInteractionsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [interactions, setInteractions] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [shieldStats, setShieldStats] = useState(null);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 50;

  useEffect(() => {
    fetchInteractions();
  }, [page]);

  useEffect(() => {
    fetchSummary();
    fetchShieldStats();
  }, []);

  const fetchSummary = async () => {
    try {
      setSummaryLoading(true);
      const res = await api.get('/api/v1/ai-interactions/summary');
      setSummary(res.data);
    } catch (err) {
      console.error('Failed to load summary:', getErrorMessage(err));
    } finally {
      setSummaryLoading(false);
    }
  };

  const fetchShieldStats = async () => {
    try {
      const res = await api.get('/api/v1/hallucination/stats');
      setShieldStats(res.data);
    } catch (err) {
      console.error('Failed to load shield stats:', err);
    }
  };

  const fetchInteractions = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/api/v1/ai-interactions?page=${page}&page_size=${pageSize}`);
      setInteractions(res.data.interactions || []);
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

  const formatNumber = (n, decimals = 2) => {
    if (n == null) return '0';
    return Number(n).toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const phoneCharges = summary
    ? Math.round((summary.total_energy_kwh || 0) / 0.012)
    : 0;

  const modelBreakdownText = summary?.model_breakdown?.length
    ? summary.model_breakdown
        .map((m) => `${m.model_name}: $${formatNumber(m.total_cost_usd, 4)}`)
        .join(' · ')
    : null;

  if (loading && summaryLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#0F172A' }}>
        <div className="text-center">
          <div className="mb-4">
            <SigmaIcon size={48} />
          </div>
          <div className="text-slate-400 text-lg animate-pulse">Loading ΣI Transparency Dashboard...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#0F172A' }}>
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center gap-4 mb-2">
            <div
              className="flex items-center justify-center rounded-lg px-3 py-1.5"
              style={{
                border: `2px solid ${GOLD}`,
                background: `linear-gradient(135deg, ${GOLD}15, ${GOLD}05)`,
              }}
            >
              <SigmaIcon size={28} />
            </div>
            <div>
              <h1
                className="text-4xl font-bold text-white"
                style={{ fontFamily: '"Inter", system-ui, sans-serif' }}
              >
                ΣI Transparency Dashboard
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Added Intelligence — Awareness Implemented |{' '}
                <span style={{ color: TEAL, fontWeight: 600 }}>Tamer Momtaz</span>
              </p>
            </div>
          </div>
        </header>

        {error && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-4 mb-6">
            <p className="text-red-300">{error}</p>
          </div>
        )}

        {/* Summary Cards */}
        {summary && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <SummaryCard
              title="Total Intelligence Units"
              value={formatNumber(summary.total_intelligence_units)}
              subtitle="1 IU ≈ 1,000 tokens ≈ ~750 words processed"
              icon="🧠"
            />
            <SummaryCard
              title="Total Cost"
              value={`$${formatNumber(summary.total_cost_usd)}`}
              subtitle={modelBreakdownText}
              icon="💰"
            />
            <SummaryCard
              title="Environmental Impact"
              value={`${formatNumber(summary.total_energy_kwh, 4)} kWh`}
              subtitle={
                <>
                  {formatNumber(summary.total_carbon_gco2, 4)} gCO₂ ·{' '}
                  {phoneCharges > 0
                    ? `= charging a phone ${phoneCharges} time${phoneCharges !== 1 ? 's' : ''}`
                    : '< 1 phone charge'}
                </>
              }
              icon="🌱"
            />
          </div>
        )}

        {/* Hallucination Shield Stats */}
        {shieldStats && <ShieldStatsSection stats={shieldStats} />}

        {/* Interactions Table */}
        <div className="rounded-xl overflow-hidden shadow-2xl" style={{ backgroundColor: DARK_SURFACE }}>
          <div className="px-6 py-4 border-b border-slate-700/50 flex items-center justify-between">
            <h2 className="text-white font-semibold text-lg">Interaction Log</h2>
            {pagination && (
              <span className="text-slate-400 text-sm">
                {pagination.total} total interactions
              </span>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="text-left p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">Timestamp</th>
                  <th className="text-left p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">Model</th>
                  <th className="text-left p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">Operation</th>
                  <th className="text-right p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">Tokens</th>
                  <th className="text-right p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">Latency</th>
                  <th className="text-right p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">Cost</th>
                  <th className="text-right p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">IU</th>
                </tr>
              </thead>
              <tbody>
                {interactions.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center p-12 text-slate-500">
                      No AI interactions recorded yet
                    </td>
                  </tr>
                ) : (
                  interactions.map((i) => {
                    const cost = parseFloat(i.cost_usd) || 0;
                    const costColor = getCostColor(cost);
                    return (
                      <tr key={i.id} className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors">
                        <td className="p-4 text-slate-300 text-xs">
                          {new Date(i.timestamp).toLocaleString()}
                        </td>
                        <td
                          className="p-4 text-xs"
                          style={{
                            fontFamily: '"JetBrains Mono", "Fira Code", monospace',
                            color: TEAL,
                          }}
                        >
                          {i.model_name}
                        </td>
                        <td className="p-4 text-slate-300 capitalize">{i.operation_type}</td>
                        <td
                          className="p-4 text-right text-slate-300"
                          style={{ fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}
                        >
                          {((i.prompt_tokens || 0) + (i.completion_tokens || 0)).toLocaleString()}
                          <span className="text-slate-500 text-xs ml-1">
                            ({i.prompt_tokens || 0}+{i.completion_tokens || 0})
                          </span>
                        </td>
                        <td
                          className="p-4 text-right text-slate-300"
                          style={{ fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}
                        >
                          {i.latency_ms}ms
                        </td>
                        <td className="p-4 text-right" style={{ fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}>
                          <span
                            className="inline-block px-2 py-0.5 rounded text-xs font-semibold"
                            style={{
                              color: costColor,
                              backgroundColor: `${costColor}18`,
                            }}
                          >
                            ${cost.toFixed(4)}
                          </span>
                        </td>
                        <td
                          className="p-4 text-right font-bold"
                          style={{
                            fontFamily: '"JetBrains Mono", "Fira Code", monospace',
                            color: TEAL,
                          }}
                        >
                          {i.intelligence_units != null
                            ? Number(i.intelligence_units).toFixed(2)
                            : 'N/A'}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center gap-3 mt-6">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
              className="px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-30"
              style={{
                backgroundColor: DARK_SURFACE,
                color: '#94A3B8',
                border: '1px solid #334155',
              }}
            >
              Previous
            </button>
            <span className="text-slate-400 text-sm" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
              {page} / {pagination.total_pages}
            </span>
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page === pagination.total_pages}
              className="px-4 py-2 rounded-lg text-sm font-medium transition disabled:opacity-30"
              style={{
                backgroundColor: DARK_SURFACE,
                color: '#94A3B8',
                border: '1px solid #334155',
              }}
            >
              Next
            </button>
          </div>
        )}

        {/* Explainer Section */}
        <div className="mt-10 rounded-xl p-8" style={{ backgroundColor: DARK_SURFACE }}>
          <h3 className="text-white text-xl font-bold mb-6 flex items-center gap-3">
            <SigmaIcon size={22} />
            <span>What is 1 Intelligence Unit (IU)?</span>
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="flex flex-col">
              <span className="text-slate-400 text-xs uppercase tracking-wider mb-1">Tokens</span>
              <span className="text-white font-semibold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                1 IU ≈ 1,000 tokens
              </span>
              <span className="text-slate-500 text-xs mt-1">≈ ~750 words</span>
            </div>
            <div className="flex flex-col">
              <span className="text-slate-400 text-xs uppercase tracking-wider mb-1">Cost</span>
              <span className="text-white font-semibold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                ~$0.003–$0.015
              </span>
              <span className="text-slate-500 text-xs mt-1">depending on model</span>
            </div>
            <div className="flex flex-col">
              <span className="text-slate-400 text-xs uppercase tracking-wider mb-1">Energy</span>
              <span className="text-white font-semibold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                ~0.001 kWh
              </span>
              <span className="text-slate-500 text-xs mt-1">powers an LED for 6 minutes</span>
            </div>
            <div className="flex flex-col">
              <span className="text-slate-400 text-xs uppercase tracking-wider mb-1">Footprint</span>
              <span className="text-white font-semibold" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                ~0.5 mL water · ~0.0004g CO₂
              </span>
              <span className="text-slate-500 text-xs mt-1">a human exhales 200g CO₂/hour</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-10 mb-4 text-center">
          <p className="text-slate-500 text-sm italic leading-relaxed">
            Every interaction has a cost. Knowing it is the first step to responsible AI.
          </p>
          <p className="mt-2 text-slate-600 text-xs">
            σI is a concept by Tamer Momtaz — Every interaction has a cost.{' '}
            Knowing it is the first step to responsible AI.
          </p>
          <p className="mt-4 text-slate-600 text-xs">
            <SigmaIcon size={12} /> and Intelligence Units (IU) are concepts by Tamer Momtaz.
          </p>
          <p className="text-slate-600 text-xs mt-1">
            &copy; 2026 Tamer Momtaz. All rights reserved.
          </p>
        </footer>
      </div>
    </div>
  );
};

export default AIInteractionsList;

import React, { useEffect, useState } from 'react';
import api, { getErrorMessage } from '../lib/api';

const GOLD = '#B8904A';
const TEAL = 'var(--color-accent)';
const DARK_SURFACE = '#1E293B';

const MODEL_PURPOSES = {
  'claude-sonnet': 'Primary evaluator',
  'claude-3-sonnet': 'Primary evaluator',
  'claude-3.5-sonnet': 'Primary evaluator',
  'claude-3-5-sonnet-20241022': 'Primary evaluator',
  'claude-sonnet-4-20250514': 'Primary evaluator',
  'gpt-4o': 'Fallback evaluator',
  'gpt-4o-mini': 'Lightweight evaluator',
  'gpt-4': 'Fallback evaluator',
  'gemini-2.0-flash': 'Backup evaluator',
  'gemini-1.5-flash': 'Backup evaluator',
  'gemini-2.5-flash-preview-05-20': 'Backup evaluator',
};

const getPurpose = (modelName) => {
  const key = (modelName || '').toLowerCase();
  for (const [pattern, purpose] of Object.entries(MODEL_PURPOSES)) {
    if (key.includes(pattern.toLowerCase())) return purpose;
  }
  if (key.includes('claude')) return 'Primary evaluator';
  if (key.includes('gpt')) return 'Fallback evaluator';
  if (key.includes('gemini')) return 'Backup evaluator';
  return 'AI evaluator';
};

const formatTimeAgo = (isoString) => {
  if (!isoString) return 'N/A';
  const diff = Date.now() - new Date(isoString).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

const formatCost = (cost) => `$${Number(cost || 0).toFixed(2)}`;
const formatLatency = (ms) => `${(Number(ms || 0) / 1000).toFixed(1)}s`;

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

const ModelInventory = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get('/api/v1/ai/model-inventory');
      setModels(res.data.models || []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const totalCalls = models.reduce((s, m) => s + (m.total_calls || 0), 0);
  const totalCost = models.reduce((s, m) => s + (m.total_cost || 0), 0);
  const totalTokens = models.reduce((s, m) => s + (m.total_tokens || 0), 0);

  if (loading) {
    return (
      <div
        className="min-h-screen flex items-center justify-center"
        style={{ backgroundColor: 'var(--color-table-header-bg)' }}
      >
        <div className="text-center">
          <div className="mb-4"><SigmaIcon size={48} /></div>
          <div className="text-slate-400 text-lg animate-pulse">Loading AI Model Inventory...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--color-table-header-bg)' }}>
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
                AI Model Inventory
              </h1>
              <p className="text-slate-400 text-sm mt-1">
                Model Governance &amp; Usage Tracking
              </p>
            </div>
          </div>
        </header>

        {/* Governance Banner */}
        <div
          className="rounded-xl p-6 mb-8"
          style={{ backgroundColor: DARK_SURFACE, borderLeft: `4px solid ${GOLD}` }}
        >
          <h2 className="text-white text-lg font-bold mb-2 flex items-center gap-2">
            <SigmaIcon size={18} />
            AI Model Governance
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            σI tracks every AI model interaction. Every interaction is logged.
            No model makes autonomous decisions.{' '}
            <span style={{ color: TEAL, fontWeight: 600 }}>Human IS the Loop.</span>
          </p>
          <p className="text-slate-400 text-xs mt-3">
            This inventory supports ISO/IEC 42001 and DESC AI Security Policy compliance.
          </p>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-500/50 rounded-lg p-4 mb-6">
            <p className="text-red-300">{error}</p>
          </div>
        )}

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="rounded-xl p-6" style={{ backgroundColor: DARK_SURFACE, minHeight: 130 }}>
            <span className="text-slate-400 text-sm font-medium uppercase tracking-wider">
              Models Active
            </span>
            <div
              className="text-3xl font-bold text-white mt-3"
              style={{ fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}
            >
              {models.length}
            </div>
            <div className="text-slate-400 text-xs mt-2">
              {totalCalls.toLocaleString()} total calls
            </div>
          </div>
          <div className="rounded-xl p-6" style={{ backgroundColor: DARK_SURFACE, minHeight: 130 }}>
            <span className="text-slate-400 text-sm font-medium uppercase tracking-wider">
              Total Cost
            </span>
            <div
              className="text-3xl font-bold text-white mt-3"
              style={{ fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}
            >
              {formatCost(totalCost)}
            </div>
            <div className="text-slate-400 text-xs mt-2">across all models</div>
          </div>
          <div className="rounded-xl p-6" style={{ backgroundColor: DARK_SURFACE, minHeight: 130 }}>
            <span className="text-slate-400 text-sm font-medium uppercase tracking-wider">
              Total Tokens
            </span>
            <div
              className="text-3xl font-bold text-white mt-3"
              style={{ fontFamily: '"JetBrains Mono", "Fira Code", monospace' }}
            >
              {totalTokens.toLocaleString()}
            </div>
            <div className="text-slate-400 text-xs mt-2">prompt + completion</div>
          </div>
        </div>

        {/* Model Inventory Table */}
        <div
          className="rounded-xl overflow-hidden shadow-2xl"
          style={{ backgroundColor: DARK_SURFACE }}
        >
          <div className="px-6 py-4 border-b border-slate-700/50 flex items-center justify-between">
            <h2 className="text-white font-semibold text-lg">Model Inventory</h2>
            <span className="text-slate-400 text-sm">{models.length} models</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" style={{ minWidth: '750px' }}>
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="text-left p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    Model
                  </th>
                  <th className="text-left p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    Purpose
                  </th>
                  <th className="text-right p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    Total Calls
                  </th>
                  <th className="text-right p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    Total Cost
                  </th>
                  <th className="text-right p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    Total Tokens
                  </th>
                  <th className="text-right p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    Avg Latency
                  </th>
                  <th className="text-right p-4 text-slate-400 font-medium uppercase text-xs tracking-wider">
                    Last Used
                  </th>
                </tr>
              </thead>
              <tbody>
                {models.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center p-12 text-slate-500">
                      No AI models recorded yet
                    </td>
                  </tr>
                ) : (
                  models.map((m) => (
                    <tr
                      key={m.model_name}
                      className="border-b border-slate-700/30 hover:bg-slate-700/20 transition-colors"
                    >
                      <td
                        className="p-4 font-semibold"
                        style={{
                          fontFamily: '"JetBrains Mono", "Fira Code", monospace',
                          color: TEAL,
                        }}
                      >
                        {m.model_name}
                      </td>
                      <td className="p-4 text-slate-300">{getPurpose(m.model_name)}</td>
                      <td
                        className="p-4 text-right text-white font-semibold"
                        style={{ fontFamily: '"JetBrains Mono", monospace' }}
                      >
                        {(m.total_calls || 0).toLocaleString()}
                      </td>
                      <td className="p-4 text-right" style={{ fontFamily: '"JetBrains Mono", monospace' }}>
                        <span
                          className="inline-block px-2 py-0.5 rounded text-xs font-semibold"
                          style={{
                            color: '#22C55E',
                            backgroundColor: '#22C55E18',
                          }}
                        >
                          {formatCost(m.total_cost)}
                        </span>
                      </td>
                      <td
                        className="p-4 text-right text-slate-300"
                        style={{ fontFamily: '"JetBrains Mono", monospace' }}
                      >
                        {(m.total_tokens || 0).toLocaleString()}
                      </td>
                      <td
                        className="p-4 text-right text-slate-300"
                        style={{ fontFamily: '"JetBrains Mono", monospace' }}
                      >
                        {formatLatency(m.avg_latency)}
                      </td>
                      <td className="p-4 text-right text-slate-400 text-xs">
                        {formatTimeAgo(m.last_used)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-10 mb-4 text-center">
          <p className="text-slate-500 text-sm italic leading-relaxed">
            Every model interaction is logged, audited, and traceable.
          </p>
          <p className="mt-2 text-slate-600 text-xs">
            <SigmaIcon size={12} /> AI Model Inventory &mdash; ISO/IEC 42001 &amp; DESC AI Security Policy
          </p>
        </footer>
      </div>
    </div>
  );
};

export default ModelInventory;

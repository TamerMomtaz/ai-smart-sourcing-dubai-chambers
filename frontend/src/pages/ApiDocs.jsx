import React, { useState } from 'react';
import { config } from '../config';

const BASE_URL = 'https://ai-smart-sourcing-dubai-chambers-production.up.railway.app';

const METHOD_COLORS = {
  GET: 'bg-emerald-500',
  POST: 'bg-teal',
  PUT: 'bg-amber-500',
  DELETE: 'bg-red-500',
};

const ENDPOINTS = [
  {
    category: 'Proposals',
    endpoints: [
      { method: 'GET', path: '/api/v1/proposals', description: 'List all proposals' },
      {
        method: 'POST', path: '/api/v1/proposals', description: 'Submit a new proposal',
        example: {
          request: '{\n  "title": "AI-Powered Trade Analytics",\n  "description": "Leverage ML to optimize trade flows...",\n  "sector": "technology",\n  "estimated_value": 250000\n}',
          response: '{\n  "id": "uuid",\n  "title": "AI-Powered Trade Analytics",\n  "status": "pending",\n  "created_at": "2026-03-24T12:00:00Z"\n}',
        },
      },
      { method: 'GET', path: '/api/v1/proposals/{id}', description: 'Get proposal details' },
      {
        method: 'POST', path: '/api/v1/proposals/{id}/evaluate', description: 'Trigger AI evaluation',
        example: {
          request: '// No body required — POST triggers evaluation',
          response: `{
  "scores": {
    "relevance_score": 85.0,
    "feasibility_score": 78.5,
    "sector_alignment_score": 90.0,
    "compliance_score": 72.0,
    "composite_score": 81.4
  },
  "reasoning": "...",
  "hallucination_check": { "grounding_score": 92.1 }
}`,
        },
      },
    ],
  },
  {
    category: 'Evaluations',
    endpoints: [
      { method: 'GET', path: '/api/v1/evaluations', description: 'List all evaluations' },
      { method: 'GET', path: '/api/v1/evaluations/{id}', description: 'Get evaluation with scores' },
      { method: 'POST', path: '/api/v1/evaluations/{id}/verify', description: 'Run Hallucination Shield' },
    ],
  },
  {
    category: 'Compliance',
    endpoints: [
      { method: 'GET', path: '/api/v1/compliance-audits', description: 'List audits' },
      { method: 'POST', path: '/api/v1/compliance-audits', description: 'Run DESC compliance audit' },
    ],
  },
  {
    category: 'Vendors',
    endpoints: [
      { method: 'GET', path: '/api/v1/vendors', description: 'List vendors with DESC status' },
    ],
  },
  {
    category: 'Intelligence',
    endpoints: [
      { method: 'GET', path: '/api/v1/trend-analyses', description: 'List trend reports' },
      { method: 'POST', path: '/api/v1/trend-analyses', description: 'Generate new AI trend report' },
      { method: 'GET', path: '/api/v1/reports/board-brief/data', description: 'Executive Board Brief data' },
    ],
  },
  {
    category: '\u03C3I Transparency',
    endpoints: [
      {
        method: 'GET', path: '/api/v1/dashboard/impact', description: 'Impact metrics (hours saved, cost)',
        tryIt: true,
        example: {
          response: `{
  "total_operations": 69,
  "total_hours_saved": 363,
  "total_cost_usd": 2.21,
  "speed_multiplier": 537.1,
  "total_iu": 189.9
}`,
        },
      },
      { method: 'GET', path: '/api/v1/ai-interactions/summary', description: 'AI interaction summary' },
      { method: 'GET', path: '/api/v1/hallucination/stats', description: 'Shield aggregate stats' },
    ],
  },
  {
    category: 'Authentication',
    endpoints: [
      { method: 'POST', path: '/auth/v1/token?grant_type=password', description: 'Login (via Supabase)' },
      { method: 'GET', path: '/api/v1/users/me', description: 'Current user profile' },
    ],
  },
];

function MethodBadge({ method }) {
  return (
    <span className={`${METHOD_COLORS[method]} text-white text-xs font-mono font-bold px-2.5 py-1 rounded-md inline-block min-w-[52px] text-center`}>
      {method}
    </span>
  );
}

function EndpointRow({ endpoint }) {
  const [expanded, setExpanded] = useState(false);
  const [tryResult, setTryResult] = useState(null);
  const [tryLoading, setTryLoading] = useState(false);
  const [tryError, setTryError] = useState(null);

  const handleTryIt = async (e) => {
    e.stopPropagation();
    setTryLoading(true);
    setTryError(null);
    setTryResult(null);
    try {
      const apiUrl = config.apiUrl || BASE_URL;
      const res = await fetch(`${apiUrl}${endpoint.path}`);
      const data = await res.json();
      setTryResult(JSON.stringify(data, null, 2));
      setExpanded(true);
    } catch (err) {
      setTryError(err.message || 'Request failed');
      setExpanded(true);
    } finally {
      setTryLoading(false);
    }
  };

  return (
    <div className="border border-ink/10 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-ink/[0.02] transition-colors"
      >
        <MethodBadge method={endpoint.method} />
        <code className="font-mono text-sm text-ink/80 flex-1">{endpoint.path}</code>
        <span className="text-ink/50 text-sm hidden sm:inline">{endpoint.description}</span>
        {endpoint.tryIt && (
          <button
            onClick={handleTryIt}
            disabled={tryLoading}
            className="ml-2 px-3 py-1 bg-teal text-white text-xs font-body font-semibold rounded-md hover:bg-teal/90 transition-colors disabled:opacity-50 shrink-0"
          >
            {tryLoading ? 'Calling...' : 'Try it \u2192'}
          </button>
        )}
        <svg
          className={`w-4 h-4 text-ink/40 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Description visible on mobile */}
      <div className="px-4 pb-2 sm:hidden">
        <span className="text-ink/50 text-sm">{endpoint.description}</span>
      </div>

      {expanded && (
        <div className="border-t border-ink/10 bg-[var(--color-table-header-bg)]/[0.02] p-4 space-y-3">
          <p className="text-sm text-ink/70">{endpoint.description}</p>

          {endpoint.example?.request && (
            <div>
              <p className="text-xs font-semibold text-ink/50 uppercase mb-1">Request Body</p>
              <pre className="bg-[#1E293B] text-emerald-300 text-xs p-4 rounded-lg overflow-x-auto font-mono leading-relaxed">
                {endpoint.example.request}
              </pre>
            </div>
          )}

          {endpoint.example?.response && (
            <div>
              <p className="text-xs font-semibold text-ink/50 uppercase mb-1">Response</p>
              <pre className="bg-[#1E293B] text-emerald-300 text-xs p-4 rounded-lg overflow-x-auto font-mono leading-relaxed">
                {endpoint.example.response}
              </pre>
            </div>
          )}

          {tryResult && (
            <div>
              <p className="text-xs font-semibold text-teal uppercase mb-1">Live Response</p>
              <pre className="bg-[#1E293B] text-teal text-xs p-4 rounded-lg overflow-x-auto font-mono leading-relaxed border border-teal/30">
                {tryResult}
              </pre>
            </div>
          )}

          {tryError && (
            <div>
              <p className="text-xs font-semibold text-red-500 uppercase mb-1">Error</p>
              <pre className="bg-[#1E293B] text-red-400 text-xs p-4 rounded-lg overflow-x-auto font-mono">
                {tryError}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ApiDocs() {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <div className="mb-10">
        <h1 className="font-heading text-4xl text-ink mb-2">API Reference</h1>
        <p className="font-body text-ink/60 text-lg mb-6">
          AI Smart Sourcing is API-first. Every feature available in the UI is also available via REST API.
        </p>

        <div className="bg-[#1E293B] rounded-lg p-4 mb-4">
          <p className="text-xs text-ink/40 uppercase font-semibold mb-1 text-slate-400">Base URL</p>
          <code className="text-emerald-300 font-mono text-sm break-all">{BASE_URL}</code>
        </div>

        <div className="bg-white border border-ink/10 rounded-lg p-4 flex items-start gap-3">
          <span className="text-lg">🔑</span>
          <div>
            <p className="font-body text-sm font-semibold text-ink">Authentication</p>
            <p className="font-body text-sm text-ink/60">
              Bearer token via Supabase Auth. Include header:{' '}
              <code className="bg-ink/5 px-1.5 py-0.5 rounded text-xs font-mono">Authorization: Bearer &lt;token&gt;</code>
            </p>
          </div>
        </div>
      </div>

      {/* Endpoints */}
      <div className="space-y-8">
        {ENDPOINTS.map((group) => (
          <section key={group.category}>
            <h2 className="font-heading text-2xl text-ink mb-4">{group.category}</h2>
            <div className="space-y-2">
              {group.endpoints.map((ep) => (
                <EndpointRow key={`${ep.method}-${ep.path}`} endpoint={ep} />
              ))}
            </div>
          </section>
        ))}
      </div>

      {/* Footer */}
      <div className="mt-12 pt-8 border-t border-ink/10 text-center mb-8">
        <p className="font-body text-ink/60 text-sm mb-1">
          API-first by design. Every capability accessible programmatically.
        </p>
        <p className="font-body text-ink/50 text-sm">
          Built with FastAPI &mdash; auto-generated OpenAPI spec at{' '}
          <a
            href={`${BASE_URL}/docs`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-teal hover:underline"
          >
            {BASE_URL}/docs
          </a>
        </p>
      </div>
    </div>
  );
}

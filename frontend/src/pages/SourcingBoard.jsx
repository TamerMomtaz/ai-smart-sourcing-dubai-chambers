import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { config } from '../config';

/* ── Badge configs (mirror SourcingCases patterns) ── */
const URGENCY_STYLES = {
  low: 'bg-gray-100 text-gray-600 border-gray-300',
  medium: 'bg-amber-100 text-amber-700 border-amber-300',
  high: 'bg-orange-100 text-orange-700 border-orange-300',
  critical: 'bg-red-100 text-red-700 border-red-300',
};

const COMPLIANCE_TIERS = {
  open: { label: 'Open', color: 'bg-gray-100 text-gray-600 border-gray-300' },
  standard: { label: 'Standard', color: 'bg-blue-100 text-blue-600 border-blue-300' },
  government: { label: 'Government', color: 'bg-amber-100 text-amber-700 border-amber-300' },
  critical: { label: 'Critical', color: 'bg-red-100 text-red-700 border-red-300' },
};

const SECTOR_COLORS = {
  technology: 'bg-indigo-100 text-indigo-700 border-indigo-300',
  healthcare: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  finance: 'bg-sky-100 text-sky-700 border-sky-300',
  energy: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  logistics: 'bg-purple-100 text-purple-700 border-purple-300',
  education: 'bg-pink-100 text-pink-700 border-pink-300',
  real_estate: 'bg-orange-100 text-orange-700 border-orange-300',
  government: 'bg-teal-100 text-teal-700 border-teal-300',
};

const Badge = ({ className, children }) => (
  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${className}`}>
    {children}
  </span>
);

function SourcingBoard() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Detail view
  const [selectedCase, setSelectedCase] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Filters
  const sectorFilter = searchParams.get('sector') || '';
  const urgencyFilter = searchParams.get('urgency') || '';
  const sortBy = searchParams.get('sort') || 'newest';

  useEffect(() => {
    fetchCases();
  }, [sectorFilter, urgencyFilter, sortBy]);

  const fetchCases = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (sectorFilter) params.set('sector', sectorFilter);
      if (urgencyFilter) params.set('urgency', urgencyFilter);
      if (sortBy) params.set('sort', sortBy);

      const res = await axios.get(
        `${config.apiUrl}/api/v1/public/sourcing-board?${params.toString()}`
      );
      setCases(res.data.cases || []);
    } catch (err) {
      setError('Failed to load sourcing opportunities. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const openDetail = async (caseId) => {
    setDetailLoading(true);
    try {
      const res = await axios.get(
        `${config.apiUrl}/api/v1/public/sourcing-board/${caseId}`
      );
      setSelectedCase(res.data);
    } catch {
      setError('Failed to load case details.');
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => setSelectedCase(null);

  const setFilter = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value) next.set(key, value);
    else next.delete(key);
    setSearchParams(next);
  };

  // Collect unique sectors for filter dropdown
  const sectors = useMemo(() => {
    const s = new Set(cases.map((c) => c.sector).filter(Boolean));
    return [...s].sort();
  }, [cases]);

  const formatDate = (iso) => {
    if (!iso) return '';
    return new Date(iso).toLocaleDateString('en-AE', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  /* ── Detail overlay ── */
  if (selectedCase) {
    return (
      <div className="min-h-screen bg-cream">
        {/* Header */}
        <header className="bg-teal text-white">
          <div className="max-w-5xl mx-auto px-6 py-8">
            <button
              onClick={closeDetail}
              className="flex items-center gap-1 text-white/80 hover:text-white text-sm mb-4 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Sourcing Board
            </button>
            <h1 className="font-heading text-3xl md:text-4xl mb-2">{selectedCase.title}</h1>
            <div className="flex flex-wrap gap-2 mt-3">
              {selectedCase.sector && (
                <Badge className="bg-white/20 text-white border-white/30">
                  {selectedCase.sector}
                </Badge>
              )}
              {selectedCase.urgency && (
                <Badge className="bg-white/20 text-white border-white/30">
                  {selectedCase.urgency.charAt(0).toUpperCase() + selectedCase.urgency.slice(1)} Priority
                </Badge>
              )}
              {selectedCase.compliance_tier && (
                <Badge className="bg-white/20 text-white border-white/30">
                  {(COMPLIANCE_TIERS[selectedCase.compliance_tier] || COMPLIANCE_TIERS.standard).label} Compliance
                </Badge>
              )}
            </div>
          </div>
        </header>

        <main className="max-w-5xl mx-auto px-6 py-10">
          <div className="grid md:grid-cols-3 gap-8">
            {/* Main content */}
            <div className="md:col-span-2 space-y-6">
              <section className="bg-white rounded-xl shadow-sm p-6">
                <h2 className="font-heading text-xl text-ink mb-4">Problem Statement</h2>
                <p className="font-body text-ink/80 whitespace-pre-wrap leading-relaxed">
                  {selectedCase.problem_statement || 'No description provided.'}
                </p>
              </section>

              {selectedCase.compliance_requirements && (
                <section className="bg-white rounded-xl shadow-sm p-6">
                  <h2 className="font-heading text-xl text-ink mb-4">Compliance Requirements</h2>
                  <p className="font-body text-ink/80 whitespace-pre-wrap leading-relaxed">
                    {selectedCase.compliance_requirements}
                  </p>
                </section>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="font-heading text-lg text-ink mb-4">Case Details</h3>
                <dl className="space-y-3 text-sm font-body">
                  {selectedCase.technology_domain && (
                    <>
                      <dt className="text-ink/50">Technology Domain</dt>
                      <dd className="text-ink font-medium">{selectedCase.technology_domain}</dd>
                    </>
                  )}
                  <dt className="text-ink/50">Posted</dt>
                  <dd className="text-ink font-medium">{formatDate(selectedCase.created_at)}</dd>
                  <dt className="text-ink/50">Proposals Submitted</dt>
                  <dd className="text-ink font-medium">{selectedCase.proposal_count || 0}</dd>
                </dl>
              </div>

              <button
                onClick={() => navigate(`/login?returnTo=/sourcing-cases`)}
                className="w-full bg-teal text-white font-body py-3 px-6 rounded-xl hover:bg-teal/90 transition-colors text-center font-medium shadow-sm"
              >
                Submit Your Proposal
              </button>
              <p className="text-xs text-center font-body text-ink/40">
                You'll need to sign in or create an account to submit a proposal.
              </p>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="border-t border-ink/10 mt-16">
          <div className="max-w-5xl mx-auto px-6 py-6 text-center">
            <p className="text-sm font-body text-ink/40">
              Powered by &sigma;I &mdash; AI Smart Sourcing Platform
            </p>
          </div>
        </footer>
      </div>
    );
  }

  /* ── Board list view ── */
  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <header className="bg-teal text-white">
        <div className="max-w-6xl mx-auto px-6 py-10 text-center">
          <h1 className="font-heading text-3xl md:text-4xl mb-2">
            Innovation Opportunities &mdash; Dubai Chambers
          </h1>
          <p className="font-body text-white/80 text-lg">
            Browse open sourcing needs and submit your solution
          </p>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Filter bar */}
        <div className="flex flex-wrap items-center gap-3 mb-8">
          <select
            value={sectorFilter}
            onChange={(e) => setFilter('sector', e.target.value)}
            className="px-3 py-2 border border-ink/20 rounded-lg font-body text-sm bg-white text-ink focus:outline-none focus:ring-2 focus:ring-teal"
          >
            <option value="">All Sectors</option>
            {sectors.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <select
            value={urgencyFilter}
            onChange={(e) => setFilter('urgency', e.target.value)}
            className="px-3 py-2 border border-ink/20 rounded-lg font-body text-sm bg-white text-ink focus:outline-none focus:ring-2 focus:ring-teal"
          >
            <option value="">All Urgency</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setFilter('sort', e.target.value)}
            className="px-3 py-2 border border-ink/20 rounded-lg font-body text-sm bg-white text-ink focus:outline-none focus:ring-2 focus:ring-teal"
          >
            <option value="newest">Newest First</option>
            <option value="urgency">By Urgency</option>
            <option value="proposals">Most Proposals</option>
          </select>

          {(sectorFilter || urgencyFilter) && (
            <button
              onClick={() => setSearchParams({ sort: sortBy })}
              className="text-sm text-teal hover:underline font-body"
            >
              Clear filters
            </button>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-20">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-teal"></div>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="text-center py-20">
            <p className="text-burgundy font-body mb-4">{error}</p>
            <button onClick={fetchCases} className="text-teal hover:underline font-body text-sm">
              Retry
            </button>
          </div>
        )}

        {/* Empty state */}
        {!loading && !error && cases.length === 0 && (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">&#128269;</div>
            <h3 className="font-heading text-xl text-ink mb-2">No open opportunities</h3>
            <p className="font-body text-ink/60">
              Check back soon for new sourcing needs from Dubai Chambers.
            </p>
          </div>
        )}

        {/* Card grid */}
        {!loading && !error && cases.length > 0 && (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {cases.map((c) => (
              <div
                key={c.id}
                className="bg-white rounded-xl shadow-sm border border-ink/5 hover:shadow-md transition-shadow flex flex-col"
              >
                <div className="p-6 flex-1 flex flex-col">
                  {/* Badges */}
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {c.sector && (
                      <Badge className={SECTOR_COLORS[c.sector?.toLowerCase()] || 'bg-gray-100 text-gray-600 border-gray-300'}>
                        {c.sector}
                      </Badge>
                    )}
                    {c.urgency && (
                      <Badge className={URGENCY_STYLES[c.urgency] || URGENCY_STYLES.medium}>
                        {c.urgency.charAt(0).toUpperCase() + c.urgency.slice(1)}
                      </Badge>
                    )}
                    {c.compliance_tier && (
                      <Badge className={(COMPLIANCE_TIERS[c.compliance_tier] || COMPLIANCE_TIERS.standard).color}>
                        {(COMPLIANCE_TIERS[c.compliance_tier] || COMPLIANCE_TIERS.standard).label}
                      </Badge>
                    )}
                  </div>

                  {/* Title */}
                  <h3 className="font-heading text-lg text-ink mb-2 line-clamp-2">{c.title}</h3>

                  {/* Problem excerpt */}
                  <p className="font-body text-sm text-ink/60 mb-4 line-clamp-3 flex-1">
                    {(c.problem_statement || '').slice(0, 200)}
                    {(c.problem_statement || '').length > 200 ? '...' : ''}
                  </p>

                  {/* Meta */}
                  <div className="flex items-center justify-between text-xs font-body text-ink/50 mt-auto pt-3 border-t border-ink/5">
                    <span>{c.proposal_count || 0} proposal{c.proposal_count !== 1 ? 's' : ''} submitted</span>
                    <span>{formatDate(c.created_at)}</span>
                  </div>
                </div>

                <div className="px-6 pb-5">
                  <button
                    onClick={() => openDetail(c.id)}
                    disabled={detailLoading}
                    className="w-full bg-teal text-white font-body py-2 px-4 rounded-lg hover:bg-teal/90 transition-colors text-sm disabled:opacity-50"
                  >
                    View Details & Apply
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-ink/10 mt-16">
        <div className="max-w-6xl mx-auto px-6 py-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm font-body text-ink/40">
            Powered by &sigma;I &mdash; AI Smart Sourcing Platform
          </p>
          <a
            href="/login"
            className="text-sm font-body text-teal hover:underline"
          >
            Sign in to manage proposals
          </a>
        </div>
      </footer>
    </div>
  );
}

export default SourcingBoard;

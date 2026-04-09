import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { config } from '../config';
import axios from 'axios';
import StatusBadge from '../components/StatusBadge';
import VScoreCircle from '../components/VScoreCircle';

const DIMENSION_LABELS = {
  performance: 'Performance',
  quality: 'Quality',
  compliance: 'Compliance',
  integrity: 'Integrity',
  entity: 'Entity',
};

const URGENCY_STYLES = {
  high: 'bg-red-500/10 text-red-400',
  medium: 'bg-amber-500/10 text-amber-400',
  low: 'bg-emerald-500/10 text-emerald-400',
};

const VendorDashboard = ({ user }) => {
  const [proposals, setProposals] = useState([]);
  const [vendorProfile, setVendorProfile] = useState(null);
  const [vscore, setVscore] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchVendorData();
  }, []);

  const fetchVendorData = async () => {
    try {
      setLoading(true);

      // Fetch proposals for this vendor
      const proposalsPromise = api.get('/api/v1/proposals?page_size=50').catch(() => ({ data: { proposals: [] } }));

      // Fetch vendor profile
      const myVendorPromise = api.get('/api/v1/vendors/my-vendor').catch(() => ({ data: null }));

      // Fetch open sourcing opportunities (public endpoint)
      const opportunitiesPromise = axios.get(
        `${config.apiUrl}/api/v1/public/sourcing-board?sort=newest`
      ).catch(() => ({ data: { cases: [] } }));

      const [proposalsRes, myVendorRes, opportunitiesRes] = await Promise.all([
        proposalsPromise,
        myVendorPromise,
        opportunitiesPromise,
      ]);

      // Set proposals (filter to vendor's own if the API returns all)
      const allProposals = proposalsRes.data?.proposals || proposalsRes.data || [];
      setProposals(allProposals);

      // Set opportunities
      const cases = opportunitiesRes.data?.cases || [];
      setOpportunities(cases.filter(c => c.status === 'open').slice(0, 5));

      // Fetch vScore if vendor profile exists
      if (myVendorRes.data?.vendor_id) {
        const vendorId = myVendorRes.data.vendor_id;
        const [vendorRes, vscoreRes] = await Promise.all([
          api.get(`/api/v1/vendors/${vendorId}`).catch(() => ({ data: null })),
          api.get(`/api/v1/vendors/${vendorId}/vscore`).catch(() => ({ data: null })),
        ]);
        setVendorProfile(vendorRes.data);
        setVscore(vscoreRes.data);
      }

      setLoading(false);
    } catch (err) {
      setError(getErrorMessage(err));
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[400px] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[var(--color-accent)]"></div>
          <span className="text-teal font-heading text-lg">Loading your dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-burgundy/10 border border-burgundy rounded-lg p-6">
        <h2 className="font-heading text-2xl text-burgundy mb-2">Error Loading Dashboard</h2>
        <p className="text-ink">{error}</p>
      </div>
    );
  }

  const vendorName = vendorProfile?.name || user?.full_name || 'Partner';

  return (
    <div>
      {/* Header */}
      <header className="mb-8">
        <h1 className="font-heading text-3xl md:text-4xl text-teal mb-1">
          Welcome back, {vendorName}
        </h1>
        <p className="text-ink/60 text-sm">Your innovation partner dashboard</p>
      </header>

      {/* 2-column grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Section 1: Your Submissions */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-heading text-xl text-teal">Your Submissions</h2>
            <Link
              to="/proposals/new"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal text-white rounded-lg text-sm font-semibold hover:bg-teal/90 transition-colors"
            >
              + Submit New Proposal
            </Link>
          </div>

          {proposals.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-ink/50 text-sm mb-3">You haven't submitted any proposals yet.</p>
              <Link
                to="/proposals/new"
                className="text-teal text-sm hover:underline font-medium"
              >
                Submit your first proposal
              </Link>
            </div>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {proposals.map((p) => (
                <Link
                  key={p.id}
                  to={`/proposals/${p.id}`}
                  className="block border border-gray-100 rounded-lg p-4 hover:bg-cream/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-medium text-ink/90 truncate">{p.title}</h3>
                      <p className="text-xs text-ink/50 mt-1">
                        {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}
                        {p.sector && <span className="ml-2">{p.sector}</span>}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {p.composite_score != null && (
                        <span className={`text-sm font-mono font-bold ${
                          p.composite_score >= 70 ? 'text-teal' :
                          p.composite_score >= 40 ? 'text-gold' : 'text-burgundy'
                        }`}>
                          {Number(p.composite_score).toFixed(1)}
                        </span>
                      )}
                      <StatusBadge status={p.status} />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}

          {proposals.length > 0 && (
            <div className="mt-4 pt-3 border-t border-gray-100">
              <Link to="/proposals" className="text-sm text-teal hover:underline font-medium">
                View all proposals
              </Link>
            </div>
          )}
        </div>

        {/* Section 2: Your vScore */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-heading text-xl text-teal">Your vScore</h2>
            {vendorProfile?.id && (
              <Link
                to={`/vendors/${vendorProfile.id}`}
                className="text-sm text-teal hover:underline font-medium"
              >
                View Full Profile
              </Link>
            )}
          </div>

          {vscore ? (
            <div>
              {/* Score + Tier */}
              <div className="flex items-center gap-6 mb-6">
                <VScoreCircle
                  score={vscore.vscore}
                  tier={vscore.vscore_tier}
                  size={80}
                />
                <div>
                  <div className="text-3xl font-mono font-bold text-teal">
                    {vscore.vscore || '—'}
                  </div>
                  <div className="text-xs text-ink/50 mt-1">out of 900</div>
                  {vscore.score_change !== 0 && (
                    <div className={`text-xs font-semibold mt-1 ${
                      vscore.score_change > 0 ? 'text-emerald-500' : 'text-red-500'
                    }`}>
                      {vscore.score_change > 0 ? '+' : ''}{vscore.score_change} since last update
                    </div>
                  )}
                </div>
              </div>

              {/* 5-dimension breakdown */}
              {vscore.dimension_scores && Object.keys(vscore.dimension_scores).length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-semibold text-ink/60 uppercase tracking-wide">Score Breakdown</h3>
                  {Object.entries(DIMENSION_LABELS).map(([key, label]) => {
                    const value = vscore.dimension_scores[key];
                    if (value == null) return null;
                    return (
                      <div key={key}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-ink/70">{label}</span>
                          <span className="font-mono font-semibold text-ink/80">{value}</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-700 ${
                              value >= 70 ? 'bg-teal' : value >= 40 ? 'bg-gold' : 'bg-burgundy'
                            }`}
                            style={{ width: `${Math.min(value, 100)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-ink/50 text-sm">No vScore data available yet.</p>
              <p className="text-ink/40 text-xs mt-2">Submit proposals and complete engagements to build your score.</p>
            </div>
          )}
        </div>

        {/* Section 3: Open Opportunities */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-heading text-xl text-teal">Open Opportunities</h2>
            <Link
              to="/sourcing-board"
              className="text-sm text-teal hover:underline font-medium"
            >
              Browse All Opportunities
            </Link>
          </div>

          {opportunities.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-ink/50 text-sm">No open opportunities at the moment.</p>
              <p className="text-ink/40 text-xs mt-2">Check back soon for new sourcing cases.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {opportunities.map((c) => (
                <Link
                  key={c.id}
                  to="/sourcing-board"
                  className="block border border-gray-100 rounded-lg p-4 hover:bg-cream/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-sm font-medium text-ink/90 truncate">{c.title}</h3>
                      <p className="text-xs text-ink/50 mt-1">
                        {c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {c.sector && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-teal/10 text-teal">
                          {c.sector}
                        </span>
                      )}
                      {c.urgency && (
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          URGENCY_STYLES[c.urgency] || 'bg-gray-500/10 text-gray-400'
                        }`}>
                          {c.urgency}
                        </span>
                      )}
                    </div>
                  </div>
                  {c.description && (
                    <p className="text-xs text-ink/40 mt-2 line-clamp-2">{c.description}</p>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Section 4: Your Compliance Status */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="font-heading text-xl text-teal mb-5">Your Compliance Status</h2>

          <div className="space-y-4">
            {/* DESC Certification */}
            <div className="flex items-center justify-between p-4 rounded-lg border border-gray-100">
              <div className="flex items-center gap-3">
                <span className="text-xl">
                  {vendorProfile?.desc_certified ? '\u2705' : '\u26A0\uFE0F'}
                </span>
                <div>
                  <h3 className="text-sm font-medium text-ink/90">DESC Certification</h3>
                  {vendorProfile?.desc_certification_level && (
                    <p className="text-xs text-ink/50 mt-0.5">Level: {vendorProfile.desc_certification_level}</p>
                  )}
                </div>
              </div>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                vendorProfile?.desc_certified
                  ? 'bg-emerald-500/10 text-emerald-600'
                  : 'bg-amber-500/10 text-amber-600'
              }`}>
                {vendorProfile?.desc_certified ? 'Certified' : 'Not Certified'}
              </span>
            </div>

            {/* Trade License */}
            <div className="flex items-center justify-between p-4 rounded-lg border border-gray-100">
              <div className="flex items-center gap-3">
                <span className="text-xl">
                  {vendorProfile?.trade_license_status === 'verified' ? '\u2705' :
                   vendorProfile?.trade_license_status === 'pending' ? '\u23F3' : '\u26A0\uFE0F'}
                </span>
                <div>
                  <h3 className="text-sm font-medium text-ink/90">Trade License</h3>
                  <p className="text-xs text-ink/50 mt-0.5">
                    {vendorProfile?.trade_license_status
                      ? vendorProfile.trade_license_status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
                      : 'Not submitted'}
                  </p>
                </div>
              </div>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                vendorProfile?.trade_license_status === 'verified'
                  ? 'bg-emerald-500/10 text-emerald-600'
                  : vendorProfile?.trade_license_status === 'pending'
                  ? 'bg-amber-500/10 text-amber-600'
                  : 'bg-red-500/10 text-red-500'
              }`}>
                {vendorProfile?.trade_license_status === 'verified' ? 'Verified' :
                 vendorProfile?.trade_license_status === 'pending' ? 'Pending' : 'Unverified'}
              </span>
            </div>

            {/* Compliance Score */}
            {vendorProfile?.average_compliance_score != null && (
              <div className="flex items-center justify-between p-4 rounded-lg border border-gray-100">
                <div className="flex items-center gap-3">
                  <span className="text-xl">
                    {vendorProfile.average_compliance_score >= 70 ? '\u2705' : '\u26A0\uFE0F'}
                  </span>
                  <div>
                    <h3 className="text-sm font-medium text-ink/90">Average Compliance Score</h3>
                  </div>
                </div>
                <span className={`font-mono font-bold text-lg ${
                  vendorProfile.average_compliance_score >= 70 ? 'text-teal' :
                  vendorProfile.average_compliance_score >= 40 ? 'text-gold' : 'text-burgundy'
                }`}>
                  {vendorProfile.average_compliance_score.toFixed(1)}
                </span>
              </div>
            )}
          </div>

          <p className="text-xs text-ink/40 mt-5 italic">
            Keep your compliance documents up to date to maintain your vScore and eligibility for sourcing cases.
          </p>
        </div>
      </div>
    </div>
  );
};

export default VendorDashboard;

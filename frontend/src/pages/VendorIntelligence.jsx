import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

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

const VendorIntelligence = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [sortKey, setSortKey] = useState('vscore');
  const [sortDir, setSortDir] = useState('desc');
  const [methodologyOpen, setMethodologyOpen] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

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

  const sortedVendors = useMemo(() => {
    if (!data?.vendors) return [];
    let filtered = data.vendors;
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
  }, [data, search, sortKey, sortDir]);

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
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
          <div>
            <h1 className="font-heading text-4xl text-[var(--color-accent)]">Vendor Intelligence — vScore</h1>
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
            <input
              type="text"
              placeholder="Search vendors..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="border border-[var(--color-border,#d1d5db)] rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] bg-[var(--color-input-bg,#fff)] text-[var(--color-text)]"
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
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
                        <div className="font-semibold text-[var(--color-text)]">{v.name}</div>
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

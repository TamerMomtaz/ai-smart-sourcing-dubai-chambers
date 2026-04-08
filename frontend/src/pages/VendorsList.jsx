import React, { useEffect, useState, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { useUserRole } from '../lib/userRole';
import VScoreCircle from '../components/VScoreCircle';

const DESCShieldIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="#10B981" fillOpacity="0.15" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M9 12l2 2 4-4" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const DESCCertifiedBadge = ({ providerName }) => (
  <div className="group relative inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-emerald-500/40 bg-emerald-500/10 text-emerald-500 text-xs font-semibold">
    <DESCShieldIcon size={14} />
    <span>DESC Certified</span>
    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
      {providerName ? `${providerName} — ` : ''}This vendor meets DESC ISR V3 Controls, DESC AI Security Policy (5-Phase Lifecycle), and DESC CSP Standards
      <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
    </div>
  </div>
);

const DescToggle = ({ enabled, onChange }) => (
  <label className="inline-flex items-center gap-2 cursor-pointer select-none">
    <span className="text-sm font-medium text-ink/80">DESC Certified Only</span>
    <div className="relative">
      <input type="checkbox" checked={enabled} onChange={(e) => onChange(e.target.checked)} className="sr-only peer" />
      <div className="w-9 h-5 bg-cream rounded-full peer peer-checked:bg-emerald-500 transition-colors" />
      <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow peer-checked:translate-x-4 transition-transform" />
    </div>
  </label>
);

const TIER_OPTIONS = [
  { value: '', label: 'All Tiers' },
  { value: 'platinum', label: 'Platinum' },
  { value: 'gold', label: 'Gold' },
  { value: 'silver', label: 'Silver' },
  { value: 'bronze', label: 'Bronze' },
  { value: 'under_review', label: 'Under Review' },
];

const COUNTRY_OPTIONS = [
  { value: '', label: 'All Countries' },
  { value: 'UAE', label: 'UAE' },
  { value: 'Saudi Arabia', label: 'Saudi Arabia' },
  { value: 'India', label: 'India' },
  { value: 'UK', label: 'UK' },
  { value: 'Egypt', label: 'Egypt' },
  { value: 'Netherlands', label: 'Netherlands' },
];

const SORT_OPTIONS = [
  { value: '', label: 'Newest' },
  { value: 'vscore_desc', label: 'vScore (High\u2192Low)' },
  { value: 'score_desc', label: 'Score (High\u2192Low)' },
  { value: 'name_asc', label: 'Name (A\u2192Z)' },
];

const FilterChip = ({ label, onRemove }) => (
  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-teal/10 text-teal text-sm font-medium">
    {label}
    <button onClick={onRemove} className="ml-0.5 hover:text-teal/70 transition" aria-label={`Remove ${label}`}>
      &times;
    </button>
  </span>
);

const SelectFilter = ({ value, onChange, options, className = '' }) => (
  <select
    value={value}
    onChange={(e) => onChange(e.target.value)}
    className={`border border-cream rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal bg-white ${className}`}
  >
    {options.map((o) => (
      <option key={o.value} value={o.value}>{o.label}</option>
    ))}
  </select>
);

const PAGE_SIZE = 12;

const InviteModal = ({ open, onClose, sectors }) => {
  const [vendorName, setVendorName] = useState('');
  const [vendorEmail, setVendorEmail] = useState('');
  const [sector, setSector] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [inviteUrl, setInviteUrl] = useState('');
  const [copied, setCopied] = useState(false);
  const [err, setErr] = useState('');

  const reset = () => {
    setVendorName(''); setVendorEmail(''); setSector('');
    setSubmitting(false); setInviteUrl(''); setCopied(false); setErr('');
  };

  const handleClose = () => { reset(); onClose(); };

  const handleSubmit = async () => {
    if (!vendorName || !vendorEmail) { setErr('Name and email are required'); return; }
    setSubmitting(true); setErr('');
    try {
      const res = await api.post('/api/v1/vendors/invite', {
        vendor_name: vendorName,
        vendor_email: vendorEmail,
        sector: sector,
      });
      const fullUrl = `${window.location.origin}${res.data.invite_url}`;
      setInviteUrl(fullUrl);
    } catch (e) {
      setErr(getErrorMessage(e));
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(inviteUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-heading text-2xl text-teal">Invite Vendor</h2>
          <button onClick={handleClose} className="text-ink/40 hover:text-ink transition text-xl">&times;</button>
        </div>

        {!inviteUrl ? (
          <>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ink/70 mb-1">Vendor Name *</label>
                <input type="text" value={vendorName} onChange={(e) => setVendorName(e.target.value)}
                  className="w-full border border-cream rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal" placeholder="e.g. Acme Corp" />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink/70 mb-1">Vendor Email *</label>
                <input type="email" value={vendorEmail} onChange={(e) => setVendorEmail(e.target.value)}
                  className="w-full border border-cream rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal" placeholder="vendor@company.com" />
              </div>
              <div>
                <label className="block text-sm font-medium text-ink/70 mb-1">Sector</label>
                <select value={sector} onChange={(e) => setSector(e.target.value)}
                  className="w-full border border-cream rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal bg-white">
                  <option value="">Select sector...</option>
                  {sectors.map((s) => <option key={s.name} value={s.name}>{s.name}</option>)}
                </select>
              </div>
            </div>
            {err && <p className="text-burgundy text-sm mt-3">{err}</p>}
            <button onClick={handleSubmit} disabled={submitting}
              className="mt-5 w-full bg-teal text-white py-2.5 rounded-lg font-medium hover:bg-teal/90 transition disabled:opacity-50">
              {submitting ? 'Generating...' : 'Generate Invite Link'}
            </button>
          </>
        ) : (
          <div className="space-y-4">
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
              <p className="text-emerald-700 text-sm font-medium mb-1">Invite link generated. Valid for 30 days.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-ink/70 mb-1">Invite Link</label>
              <input type="text" readOnly value={inviteUrl}
                className="w-full border border-cream rounded-lg px-4 py-2 text-sm bg-gray-50 text-ink/80" />
            </div>
            <button onClick={handleCopy}
              className="w-full bg-teal text-white py-2.5 rounded-lg font-medium hover:bg-teal/90 transition">
              {copied ? 'Copied!' : 'Copy Link'}
            </button>
            <button onClick={handleClose}
              className="w-full border border-cream text-ink/60 py-2.5 rounded-lg font-medium hover:bg-cream/50 transition">
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const VendorsList = () => {
  const { role } = useUserRole();
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [vendors, setVendors] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [showInviteModal, setShowInviteModal] = useState(false);

  // Filter state from URL
  const page = parseInt(searchParams.get('page') || '1', 10);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const sector = searchParams.get('sector') || '';
  const vscoreTier = searchParams.get('vscore_tier') || '';
  const country = searchParams.get('country') || '';
  const sortBy = searchParams.get('sort_by') || '';
  const descOnly = searchParams.get('desc_only') === '1';

  // Sectors loaded from business groups
  const [sectors, setSectors] = useState([]);

  useEffect(() => {
    api.get('/api/v1/business-groups')
      .then((res) => setSectors(res.data.business_groups || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetchVendors();
  }, [searchParams]);

  const fetchVendors = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: PAGE_SIZE.toString(),
      });
      const searchVal = searchParams.get('search');
      if (searchVal) params.append('search', searchVal);
      if (sector) params.append('sector', sector);
      if (vscoreTier) params.append('vscore_tier', vscoreTier);
      if (country) params.append('country', country);
      if (sortBy) params.append('sort_by', sortBy);

      const res = await api.get(`/api/v1/vendors?${params.toString()}`);
      setVendors(res.data.vendors || []);
      setPagination(res.data.pagination);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const updateParams = useCallback((updates) => {
    const params = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([k, v]) => {
      if (v) params.set(k, v);
      else params.delete(k);
    });
    // Reset to page 1 when filters change (unless only page itself is changing)
    if (!('page' in updates)) params.set('page', '1');
    setSearchParams(params);
  }, [searchParams, setSearchParams]);

  const handleSearch = () => {
    updateParams({ search: search || null });
  };

  const handlePageChange = (newPage) => {
    updateParams({ page: newPage.toString() });
  };

  const clearAllFilters = () => {
    setSearch('');
    setSearchParams({});
  };

  // Determine displayed vendors (DESC toggle is client-side on the already-fetched page)
  const displayed = descOnly
    ? vendors.filter((v) => v.is_desc_approved || v.desc_certified)
    : vendors;

  // Active filter chips
  const activeFilters = [];
  const searchVal = searchParams.get('search');
  if (searchVal) activeFilters.push({ key: 'search', label: `Search: ${searchVal}`, param: 'search' });
  if (sector) {
    const sectorName = sectors.find((s) => s.name === sector)?.name || sector;
    activeFilters.push({ key: 'sector', label: `Sector: ${sectorName}`, param: 'sector' });
  }
  if (vscoreTier) {
    const tierLabel = TIER_OPTIONS.find((t) => t.value === vscoreTier)?.label || vscoreTier;
    activeFilters.push({ key: 'vscore_tier', label: `Tier: ${tierLabel}`, param: 'vscore_tier' });
  }
  if (country) {
    activeFilters.push({ key: 'country', label: `Country: ${country}`, param: 'country' });
  }
  if (descOnly) activeFilters.push({ key: 'desc_only', label: 'DESC Certified Only', param: 'desc_only' });

  const sectorOptions = [
    { value: '', label: 'All Sectors' },
    ...sectors.map((s) => ({ value: s.name, label: s.name })),
  ];

  return (
    <div className="min-h-screen bg-cream p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="font-heading text-4xl text-teal">Vendors</h1>
        </header>

        {error && (
          <div className="bg-burgundy/10 border border-burgundy rounded-lg p-4 mb-6">
            <p className="text-burgundy">{error}</p>
          </div>
        )}

        {/* Filter Bar */}
        <div className="bg-white rounded-xl shadow-md p-4 mb-4">
          {/* Row 1: Search + DESC toggle */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-3 mb-3">
            <div className="flex flex-1 space-x-2">
              <input
                type="text"
                placeholder="Search vendors..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 border border-cream rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal"
              />
              <button onClick={handleSearch} className="bg-teal text-white px-5 py-2 rounded-lg hover:bg-teal/90 transition text-sm">
                Search
              </button>
              {role === 'admin' && (
                <button onClick={() => setShowInviteModal(true)} className="bg-[#C8A951] text-white px-5 py-2 rounded-lg hover:bg-[#B8993F] transition text-sm whitespace-nowrap font-medium">
                  + Invite Vendor
                </button>
              )}
            </div>
            <DescToggle
              enabled={descOnly}
              onChange={(val) => updateParams({ desc_only: val ? '1' : null })}
            />
          </div>
          {/* Row 2: Dropdowns */}
          <div className="flex flex-wrap items-center gap-3">
            <SelectFilter value={sector} onChange={(v) => updateParams({ sector: v || null })} options={sectorOptions} />
            <SelectFilter value={vscoreTier} onChange={(v) => updateParams({ vscore_tier: v || null })} options={TIER_OPTIONS} />
            <SelectFilter value={country} onChange={(v) => updateParams({ country: v || null })} options={COUNTRY_OPTIONS} />
            <SelectFilter value={sortBy} onChange={(v) => updateParams({ sort_by: v || null })} options={SORT_OPTIONS} />
          </div>
        </div>

        {/* Active Filter Chips + Results Count */}
        <div className="flex flex-wrap items-center gap-2 mb-4">
          {activeFilters.length > 0 && (
            <>
              {activeFilters.map((f) => (
                <FilterChip
                  key={f.key}
                  label={f.label}
                  onRemove={() => {
                    if (f.param === 'search') setSearch('');
                    updateParams({ [f.param]: null });
                  }}
                />
              ))}
              <button onClick={clearAllFilters} className="text-sm text-ink/50 hover:text-ink transition ml-1">
                Clear All
              </button>
            </>
          )}
          {pagination && (
            <span className="ml-auto text-sm text-ink/60">
              Showing {displayed.length} of {pagination.total} vendor{pagination.total !== 1 ? 's' : ''}
            </span>
          )}
        </div>

        {/* Vendor Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-pulse text-teal font-heading text-2xl">Loading vendors...</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displayed.length === 0 ? (
              <div className="col-span-full text-center p-8 text-ink/60">
                No vendors found
              </div>
            ) : (
              displayed.map((v) => (
                <div key={v.id} className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition relative">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="font-heading text-xl text-teal flex items-center gap-2">
                        {v.name}
                        {v.trade_license_status === 'verified' && (
                          <span title="Trade License Verified" className="text-emerald-500 text-base">&#10003;</span>
                        )}
                        {v.trade_license_status === 'pending' && (
                          <span title="License Verification Pending" className="text-amber-500 text-base">&#9203;</span>
                        )}
                        {(!v.trade_license_status || v.trade_license_status === 'unverified') && (
                          <span title="License Unverified" className="text-gray-400 text-base">&#9675;</span>
                        )}
                        {(v.trade_license_status === 'expired' || v.trade_license_status === 'invalid') && (
                          <span title={`Trade License ${v.trade_license_status === 'expired' ? 'Expired' : 'Invalid'}`} className="text-red-500 text-base">&#10007;</span>
                        )}
                      </h3>
                      {v.desc_certified && (
                        <div className="mt-1">
                          <DESCCertifiedBadge providerName={v.desc_provider_name} />
                        </div>
                      )}
                    </div>
                    {v.vscore != null ? (
                      <VScoreCircle score={v.vscore} tier={v.vscore_tier} size={56} />
                    ) : v.reputation_score != null ? (
                      <VScoreCircle score={v.reputation_score} tier={v.reputation_tier} size={56} legacy />
                    ) : null}
                  </div>
                  <div className="space-y-2 text-sm text-ink/70 mb-4">
                    <div>📍 {v.country}</div>
                    <div>📧 {v.contact_email}</div>
                    {v.website && <div>🌐 {v.website}</div>}
                    <div>📊 {v.submission_history_count || 0} submissions</div>
                    {v.average_compliance_score && (
                      <div>✅ Avg Score: {v.average_compliance_score.toFixed(1)}</div>
                    )}
                  </div>
                  <Link to={`/vendors/${v.id}`} className="text-teal hover:underline text-sm font-medium">
                    View Details →
                  </Link>
                </div>
              ))
            )}
          </div>
        )}

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center space-x-2 mt-6">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
              className="px-4 py-2 rounded-lg bg-white border border-cream disabled:opacity-50 hover:bg-cream transition"
            >
              Previous
            </button>
            <span className="text-ink">
              Page {page} of {pagination.total_pages}
            </span>
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page === pagination.total_pages}
              className="px-4 py-2 rounded-lg bg-white border border-cream disabled:opacity-50 hover:bg-cream transition"
            >
              Next
            </button>
          </div>
        )}
        <InviteModal open={showInviteModal} onClose={() => setShowInviteModal(false)} sectors={sectors} />
      </div>
    </div>
  );
};

export default VendorsList;

import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
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
    <span className="text-sm font-medium text-ink/80">Show DESC Certified Only</span>
    <div className="relative">
      <input type="checkbox" checked={enabled} onChange={(e) => onChange(e.target.checked)} className="sr-only peer" />
      <div className="w-9 h-5 bg-cream rounded-full peer peer-checked:bg-emerald-500 transition-colors" />
      <div className="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow peer-checked:translate-x-4 transition-transform" />
    </div>
  </label>
);

const VendorsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [vendors, setVendors] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [descOnly, setDescOnly] = useState(false);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20;

  useEffect(() => {
    fetchVendors();
  }, [page, searchParams]);

  const fetchVendors = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      });
      if (search) params.append('search', search);
      
      const res = await api.get(`/api/v1/vendors?${params.toString()}`);
      setVendors(res.data.vendors || []);
      setPagination(res.data.pagination);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    const params = new URLSearchParams({ page: '1' });
    if (search) params.set('search', search);
    setSearchParams(params);
  };

  const handlePageChange = (newPage) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', newPage.toString());
    setSearchParams(params);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="animate-pulse text-teal font-heading text-2xl">Loading vendors...</div>
      </div>
    );
  }

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

        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex flex-1 space-x-2">
              <input
                type="text"
                placeholder="Search vendors..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1 border border-cream rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal"
              />
              <button onClick={handleSearch} className="bg-teal text-white px-6 py-2 rounded-lg hover:bg-teal/90 transition">
                Search
              </button>
            </div>
            <DescToggle enabled={descOnly} onChange={setDescOnly} />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {(descOnly ? vendors.filter(v => v.is_desc_approved || v.desc_certified) : vendors).length === 0 ? (
            <div className="col-span-full text-center p-8 text-ink/60">
              No vendors found
            </div>
          ) : (
            (descOnly ? vendors.filter(v => v.is_desc_approved || v.desc_certified) : vendors).map((v) => (
              <div key={v.id} className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition relative">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-heading text-xl text-teal">{v.name}</h3>
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
      </div>
    </div>
  );
};

export default VendorsList;
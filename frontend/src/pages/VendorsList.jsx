import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const VendorsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [vendors, setVendors] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [search, setSearch] = useState(searchParams.get('search') || '');

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
    <div className="min-h-screen bg-cream p-8">
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
          <div className="flex space-x-2">
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
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {vendors.length === 0 ? (
            <div className="col-span-full text-center p-8 text-ink/60">
              No vendors found
            </div>
          ) : (
            vendors.map((v) => (
              <div key={v.id} className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="font-heading text-xl text-teal">{v.name}</h3>
                  {v.is_desc_approved && (
                    <span className="bg-gold/20 text-gold px-2 py-1 rounded text-xs font-medium">DESC</span>
                  )}
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
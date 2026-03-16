import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const ProposalsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [filters, setFilters] = useState({
    search: searchParams.get('search') || '',
    status: searchParams.get('status') || '',
    sector: searchParams.get('sector') || ''
  });

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20;

  useEffect(() => {
    fetchProposals();
  }, [page, searchParams]);

  const fetchProposals = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString()
      });
      if (filters.search) params.append('search', filters.search);
      if (filters.status) params.append('status', filters.status);
      if (filters.sector) params.append('sector', filters.sector);
      
      const res = await api.get(`/api/v1/proposals?${params.toString()}`);
      setProposals(res.data.proposals || []);
      setPagination(res.data.pagination);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    const params = new URLSearchParams({ page: '1' });
    if (newFilters.search) params.set('search', newFilters.search);
    if (newFilters.status) params.set('status', newFilters.status);
    if (newFilters.sector) params.set('sector', newFilters.sector);
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
        <div className="animate-pulse text-teal font-heading text-2xl">Loading proposals...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6 flex items-center justify-between">
          <h1 className="font-heading text-4xl text-teal">Proposals</h1>
          <Link to="/proposals/new" className="bg-teal text-white px-6 py-2 rounded-lg hover:bg-teal/90 transition">
            + New Proposal
          </Link>
        </header>

        {error && (
          <div className="bg-burgundy/10 border border-burgundy rounded-lg p-4 mb-6">
            <p className="text-burgundy">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-md p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Search proposals..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="border border-cream rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal"
            />
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="border border-cream rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal"
            >
              <option value="">All Statuses</option>
              <option value="draft">Draft</option>
              <option value="submitted">Submitted</option>
              <option value="evaluating">Evaluating</option>
              <option value="under_review">Under Review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
            <select
              value={filters.sector}
              onChange={(e) => handleFilterChange('sector', e.target.value)}
              className="border border-cream rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-teal"
            >
              <option value="">All Sectors</option>
              <option value="fintech">Fintech</option>
              <option value="healthcare">Healthcare</option>
              <option value="logistics">Logistics</option>
              <option value="energy">Energy</option>
              <option value="education">Education</option>
              <option value="government">Government</option>
              <option value="tourism">Tourism</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-teal text-white">
              <tr>
                <th className="text-left p-4">Title</th>
                <th className="text-left p-4">Sector</th>
                <th className="text-left p-4">Status</th>
                <th className="text-left p-4">Score</th>
                <th className="text-left p-4">Submitted</th>
                <th className="text-left p-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {proposals.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center p-8 text-ink/60">
                    No proposals found
                  </td>
                </tr>
              ) : (
                proposals.map((p) => (
                  <tr key={p.id} className="border-b border-cream hover:bg-cream/50">
                    <td className="p-4">
                      <Link to={`/proposals/${p.id}`} className="text-teal hover:underline font-medium">
                        {p.title}
                      </Link>
                    </td>
                    <td className="p-4 capitalize">{p.sector}</td>
                    <td className="p-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        p.status === 'approved' ? 'bg-teal/20 text-teal' :
                        p.status === 'rejected' ? 'bg-burgundy/20 text-burgundy' :
                        'bg-gold/20 text-gold'
                      }`}>
                        {p.status}
                      </span>
                    </td>
                    <td className="p-4">
                      {p.composite_score ? p.composite_score.toFixed(1) : 'N/A'}
                    </td>
                    <td className="p-4">
                      {p.submission_date ? new Date(p.submission_date).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="p-4">
                      <Link to={`/proposals/${p.id}`} className="text-teal hover:underline text-sm">
                        View →
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
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

export default ProposalsList;
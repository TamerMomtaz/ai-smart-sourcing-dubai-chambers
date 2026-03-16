import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const AIInteractionsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [interactions, setInteractions] = useState([]);
  const [pagination, setPagination] = useState(null);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 50;

  useEffect(() => {
    fetchInteractions();
  }, [page]);

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

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="animate-pulse text-teal font-heading text-2xl">Loading AI interactions...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="font-heading text-4xl text-teal">AI Interactions (ΣI Tracking)</h1>
        </header>

        {error && (
          <div className="bg-burgundy/10 border border-burgundy rounded-lg p-4 mb-6">
            <p className="text-burgundy">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-teal text-white">
              <tr>
                <th className="text-left p-3">Timestamp</th>
                <th className="text-left p-3">Model</th>
                <th className="text-left p-3">Operation</th>
                <th className="text-left p-3">Tokens</th>
                <th className="text-left p-3">Latency</th>
                <th className="text-left p-3">Cost</th>
                <th className="text-left p-3">ΣI Units</th>
              </tr>
            </thead>
            <tbody>
              {interactions.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center p-8 text-ink/60">
                    No AI interactions found
                  </td>
                </tr>
              ) : (
                interactions.map((i) => (
                  <tr key={i.id} className="border-b border-cream hover:bg-cream/50">
                    <td className="p-3">
                      {new Date(i.timestamp).toLocaleString()}
                    </td>
                    <td className="p-3 font-mono text-xs">{i.model_name}</td>
                    <td className="p-3 capitalize">{i.operation_type}</td>
                    <td className="p-3">
                      {i.prompt_tokens + i.completion_tokens}
                      <span className="text-ink/50 text-xs ml-1">({i.prompt_tokens}+{i.completion_tokens})</span>
                    </td>
                    <td className="p-3">{i.latency_ms}ms</td>
                    <td className="p-3">${i.cost_usd?.toFixed(4) || '0.0000'}</td>
                    <td className="p-3 font-bold text-teal">{i.intelligence_units?.toFixed(2) || 'N/A'}</td>
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

export default AIInteractionsList;
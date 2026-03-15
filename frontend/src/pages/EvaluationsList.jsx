import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const EvaluationsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [evaluations, setEvaluations] = useState([]);
  const [pagination, setPagination] = useState(null);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20;

  useEffect(() => {
    fetchEvaluations();
  }, [page]);

  const fetchEvaluations = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/proposals?page=${page}&page_size=${pageSize}&status=evaluated`);
      const proposalsWithEvals = res.data.proposals || [];
      setEvaluations(proposalsWithEvals.filter(p => p.composite_score !== null));
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
        <div className="animate-pulse text-teal font-heading text-2xl">Loading evaluations...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="font-heading text-4xl text-teal">Evaluations</h1>
        </header>

        {error && (
          <div className="bg-burgundy/10 border border-burgundy rounded-lg p-4 mb-6">
            <p className="text-burgundy">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-teal text-white">
              <tr>
                <th className="text-left p-4">Proposal</th>
                <th className="text-left p-4">Composite</th>
                <th className="text-left p-4">Relevance</th>
                <th className="text-left p-4">Feasibility</th>
                <th className="text-left p-4">Sector Alignment</th>
                <th className="text-left p-4">Compliance</th>
                <th className="text-left p-4">Evaluated</th>
              </tr>
            </thead>
            <tbody>
              {evaluations.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center p-8 text-ink/60">
                    No evaluations found
                  </td>
                </tr>
              ) : (
                evaluations.map((e) => (
                  <tr key={e.id} className="border-b border-cream hover:bg-cream/50">
                    <td className="p-4">
                      <Link to={`/proposals/${e.id}`} className="text-teal hover:underline font-medium">
                        {e.title}
                      </Link>
                    </td>
                    <td className="p-4 font-bold text-teal">{e.composite_score?.toFixed(1) || 'N/A'}</td>
                    <td className="p-4">{e.relevance_score?.toFixed(1) || 'N/A'}</td>
                    <td className="p-4">{e.feasibility_score?.toFixed(1) || 'N/A'}</td>
                    <td className="p-4">{e.sector_alignment_score?.toFixed(1) || 'N/A'}</td>
                    <td className="p-4">{e.compliance_score?.toFixed(1) || 'N/A'}</td>
                    <td className="p-4">
                      {e.evaluation_timestamp ? new Date(e.evaluation_timestamp).toLocaleDateString() : 'N/A'}
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

export default EvaluationsList;
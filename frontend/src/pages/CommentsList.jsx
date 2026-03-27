import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const CommentsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [comments, setComments] = useState([]);
  const [pagination, setPagination] = useState(null);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 30;

  useEffect(() => {
    fetchComments();
  }, [page]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/api/v1/comments?page=${page}&page_size=${pageSize}`);
      setComments(res.data.comments || []);
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
        <div className="animate-pulse text-teal font-heading text-2xl">Loading comments...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="font-heading text-4xl text-teal">Comments</h1>
        </header>

        {error && (
          <div className="bg-burgundy/10 border border-burgundy rounded-lg p-4 mb-6">
            <p className="text-burgundy">{error}</p>
          </div>
        )}

        <div className="space-y-4">
          {comments.length === 0 ? (
            <div className="bg-white rounded-xl shadow-md p-8 text-center text-ink/60">
              No comments found
            </div>
          ) : (
            comments.map((c) => (
              <div key={c.id} className="bg-white rounded-xl shadow-md p-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="text-sm text-ink/60">
                    {new Date(c.created_at).toLocaleString()}
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    c.visibility === 'internal' ? 'bg-burgundy/20 text-burgundy' : 'bg-teal/20 text-teal'
                  }`}>
                    {c.visibility}
                  </span>
                </div>
                <p className="text-ink">{c.comment_text}</p>
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

export default CommentsList;
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const ProposalDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [proposal, setProposal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    fetchProposal();
  }, [id]);

  const fetchProposal = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/proposals/${id}`);
      setProposal(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    try {
      setActionLoading(true);
      await api.post(`/api/v1/proposals/${id}/evaluate`);
      await fetchProposal();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      setActionLoading(true);
      await api.patch(`/api/v1/proposals/${id}/status`, { status: newStatus });
      await fetchProposal();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-teal font-heading text-xl">Loading proposal...</div>
      </div>
    );
  }

  if (error && !proposal) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-burgundy font-body text-lg">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="font-heading text-4xl text-ink">{proposal.title}</h1>
          <button
            onClick={() => navigate('/proposals')}
            className="text-teal hover:underline font-body"
          >
            ← Back to Proposals
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-burgundy/10 border border-burgundy rounded-lg text-burgundy">
            {error}
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm p-8 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <span className="text-gray-600 font-body text-sm">Status</span>
              <p className="text-ink font-semibold mt-1">{proposal.status}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Sector</span>
              <p className="text-ink font-semibold mt-1">{proposal.sector}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Technology Type</span>
              <p className="text-ink font-semibold mt-1">{proposal.technology_type}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Maturity Level</span>
              <p className="text-ink font-semibold mt-1">{proposal.maturity_level}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Language</span>
              <p className="text-ink font-semibold mt-1">{proposal.language}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Submission Date</span>
              <p className="text-ink font-semibold mt-1">
                {proposal.submission_date ? new Date(proposal.submission_date).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>

          {proposal.composite_score && (
            <div className="border-t pt-6">
              <h3 className="font-heading text-2xl text-ink mb-4">Evaluation Scores</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-600 font-body text-sm">Composite Score</span>
                  <p className="text-teal font-bold text-2xl mt-1">{proposal.composite_score}/100</p>
                </div>
                <div>
                  <span className="text-gray-600 font-body text-sm">Relevance</span>
                  <p className="text-ink font-semibold text-lg mt-1">{proposal.relevance_score}/100</p>
                </div>
                <div>
                  <span className="text-gray-600 font-body text-sm">Feasibility</span>
                  <p className="text-ink font-semibold text-lg mt-1">{proposal.feasibility_score}/100</p>
                </div>
                <div>
                  <span className="text-gray-600 font-body text-sm">Sector Alignment</span>
                  <p className="text-ink font-semibold text-lg mt-1">{proposal.sector_alignment_score}/100</p>
                </div>
                <div>
                  <span className="text-gray-600 font-body text-sm">Compliance</span>
                  <p className="text-ink font-semibold text-lg mt-1">{proposal.compliance_score}/100</p>
                </div>
              </div>
            </div>
          )}

          {proposal.is_duplicate && (
            <div className="border-t pt-6">
              <div className="p-4 bg-gold/10 border border-gold rounded-lg text-gold">
                ⚠ This proposal has been flagged as a potential duplicate.
              </div>
            </div>
          )}

          {proposal.requires_manual_review && (
            <div className="border-t pt-6">
              <div className="p-4 bg-burgundy/10 border border-burgundy rounded-lg text-burgundy">
                ⚠ This proposal requires manual review.
              </div>
            </div>
          )}

          <div className="border-t pt-6 flex gap-4">
            <button
              onClick={() => navigate(`/proposals/${id}/edit`)}
              className="bg-teal text-white py-2 px-6 rounded-lg font-semibold hover:bg-teal/90 transition-colors"
            >
              Edit
            </button>
            <button
              onClick={handleEvaluate}
              disabled={actionLoading}
              className="bg-gold text-white py-2 px-6 rounded-lg font-semibold hover:bg-gold/90 disabled:opacity-50 transition-colors"
            >
              {actionLoading ? 'Evaluating...' : 'Re-evaluate'}
            </button>
            {proposal.status === 'submitted' && (
              <button
                onClick={() => handleStatusChange('under_review')}
                disabled={actionLoading}
                className="bg-ink text-white py-2 px-6 rounded-lg font-semibold hover:bg-ink/90 disabled:opacity-50 transition-colors"
              >
                Move to Review
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProposalDetail;
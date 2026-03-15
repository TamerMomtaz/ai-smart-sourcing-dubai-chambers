import React from 'react';
import { Link } from 'react-router-dom';
import StatusBadge from './StatusBadge';
import ScoreBadge from './ScoreBadge';

const ProposalCard = ({ proposal }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <Link to={`/proposals/${proposal.id}`}>
      <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition cursor-pointer border border-transparent hover:border-teal">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-xl font-heading font-bold text-ink mb-2 line-clamp-2">
              {proposal.title}
            </h3>
            <div className="flex flex-wrap gap-2 mb-3">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium bg-teal/10 text-teal">
                {proposal.sector}
              </span>
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium bg-gold/10 text-gold">
                {proposal.technology_type?.replace('_', ' ')}
              </span>
              {proposal.maturity_level && (
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium bg-ink/10 text-ink">
                  {proposal.maturity_level}
                </span>
              )}
            </div>
          </div>
          <StatusBadge status={proposal.status} />
        </div>

        {proposal.composite_score !== null && proposal.composite_score !== undefined && (
          <div className="mb-4">
            <ScoreBadge score={proposal.composite_score} label="Composite Score" />
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 text-sm font-body">
          <div>
            <span className="text-ink/60">Submitted:</span>
            <p className="text-ink font-medium">{formatDate(proposal.submission_date)}</p>
          </div>
          {proposal.evaluation_timestamp && (
            <div>
              <span className="text-ink/60">Evaluated:</span>
              <p className="text-ink font-medium">{formatDate(proposal.evaluation_timestamp)}</p>
            </div>
          )}
        </div>

        {proposal.requires_manual_review && (
          <div className="mt-4 p-3 bg-gold/10 border border-gold rounded-lg">
            <p className="text-xs font-body text-gold font-medium">⚠️ Manual review required</p>
          </div>
        )}

        {proposal.is_duplicate && (
          <div className="mt-4 p-3 bg-burgundy/10 border border-burgundy rounded-lg">
            <p className="text-xs font-body text-burgundy font-medium">⚠️ Potential duplicate detected</p>
          </div>
        )}
      </div>
    </Link>
  );
};

export default ProposalCard;
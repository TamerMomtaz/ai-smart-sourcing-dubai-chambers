import React from 'react';
import { Link } from 'react-router-dom';
import StatusBadge from './StatusBadge';
import ScoreBadge from './ScoreBadge';

const DESCShieldMini = () => (
  <span className="group relative inline-flex items-center ml-1.5" title="Vendor is DESC Certified">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="#10B981" fillOpacity="0.15" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M9 12l2 2 4-4" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
    <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
      DESC Certified Vendor
      <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></span>
    </span>
  </span>
);

const SecurityFlagShield = () => (
  <span className="group relative inline-flex items-center ml-1.5" title="Content security flags detected">
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="#F59E0B" fillOpacity="0.15" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M12 9v4M12 17h.01" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
    <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
      Content security flags detected &mdash; review recommended
      <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></span>
    </span>
  </span>
);

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
              {proposal.vendor_desc_certified && <DESCShieldMini />}
              {proposal.content_flags && <SecurityFlagShield />}
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
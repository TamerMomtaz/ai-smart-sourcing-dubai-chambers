import React from 'react';
import { Link } from 'react-router-dom';
import VScoreCircle from './VScoreCircle';

const DESCShieldIcon = ({ size = 14 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" fill="#10B981" fillOpacity="0.15" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <path d="M9 12l2 2 4-4" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const VendorCard = ({ vendor }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <Link to={`/vendors/${vendor.id}`}>
      <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition cursor-pointer border border-transparent hover:border-teal">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-xl font-heading font-bold text-ink mb-2">
              {vendor.name}
            </h3>
            {(vendor.desc_certified || vendor.is_desc_approved) && (
              <div className="group relative inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-emerald-500/40 bg-emerald-500/10 text-emerald-500 text-xs font-body font-semibold mb-2">
                <DESCShieldIcon size={14} />
                <span>DESC Certified</span>
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                  {vendor.desc_provider_name ? `${vendor.desc_provider_name} — ` : ''}This vendor meets DESC ISR V3, AI Security, and CSP standards
                  <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900"></div>
                </div>
              </div>
            )}
          </div>
          <div className="flex items-start gap-2">
            {vendor.vscore != null ? (
              <VScoreCircle score={vendor.vscore} tier={vendor.vscore_tier} size={52} />
            ) : vendor.reputation_score != null ? (
              <VScoreCircle score={vendor.reputation_score} tier={vendor.reputation_tier} size={52} legacy />
            ) : null}
            {vendor.onboarding_status && !vendor.reputation_score && (
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium ${
                vendor.onboarding_status === 'active' ? 'bg-teal/10 text-teal' :
                vendor.onboarding_status === 'pending' ? 'bg-gold/10 text-gold' :
                'bg-ink/10 text-ink'
              }`}>
                {vendor.onboarding_status}
              </span>
            )}
          </div>
        </div>

        <div className="space-y-2 text-sm font-body mb-4">
          {vendor.country && (
            <div className="flex items-center text-ink/60">
              <span className="mr-2">🌍</span>
              <span>{vendor.country}</span>
            </div>
          )}
          {vendor.contact_email && (
            <div className="flex items-center text-ink/60">
              <span className="mr-2">✉️</span>
              <span className="truncate">{vendor.contact_email}</span>
            </div>
          )}
          {vendor.website && (
            <div className="flex items-center text-ink/60">
              <span className="mr-2">🔗</span>
              <span className="truncate">{vendor.website}</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm font-body pt-4 border-t border-ink/10">
          <div>
            <span className="text-ink/60">Submissions:</span>
            <p className="text-ink font-medium">{vendor.submission_history_count || 0}</p>
          </div>
          {vendor.average_compliance_score !== null && vendor.average_compliance_score !== undefined && (
            <div>
              <span className="text-ink/60">Avg. Compliance:</span>
              <p className="text-ink font-medium">{vendor.average_compliance_score.toFixed(1)}%</p>
            </div>
          )}
        </div>

        {vendor.desc_badge_issued_date && (
          <div className="mt-4 p-3 bg-teal/5 rounded-lg">
            <p className="text-xs font-body text-ink/60">
              DESC Badge Issued: {formatDate(vendor.desc_badge_issued_date)}
            </p>
          </div>
        )}
      </div>
    </Link>
  );
};

export default VendorCard;
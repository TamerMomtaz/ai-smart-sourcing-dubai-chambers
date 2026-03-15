import React from 'react';
import { Link } from 'react-router-dom';

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
            {vendor.is_desc_approved && (
              <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium bg-teal/10 text-teal mb-2">
                ✓ DESC Approved
              </div>
            )}
          </div>
          {vendor.onboarding_status && (
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium ${
              vendor.onboarding_status === 'active' ? 'bg-teal/10 text-teal' :
              vendor.onboarding_status === 'pending' ? 'bg-gold/10 text-gold' :
              'bg-ink/10 text-ink'
            }`}>
              {vendor.onboarding_status}
            </span>
          )}
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
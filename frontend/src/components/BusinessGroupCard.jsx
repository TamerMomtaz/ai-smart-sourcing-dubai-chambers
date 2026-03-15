import React from 'react';
import { Link } from 'react-router-dom';

const BusinessGroupCard = ({ group }) => {
  return (
    <Link to={`/business-groups/${group.id}`}>
      <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition cursor-pointer border border-transparent hover:border-teal">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-xl font-heading font-bold text-ink mb-2">
              {group.name}
            </h3>
            {group.chamber && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium bg-teal/10 text-teal mb-2">
                {group.chamber}
              </span>
            )}
          </div>
        </div>

        {group.description && (
          <p className="font-body text-ink/60 text-sm mb-4 line-clamp-2">
            {group.description}
          </p>
        )}

        {group.lead_user_name && (
          <div className="flex items-center space-x-2 text-sm font-body text-ink/60">
            <span>Lead:</span>
            <span className="text-ink font-medium">{group.lead_user_name}</span>
          </div>
        )}

        {group.evaluation_weight_config && (
          <div className="mt-4 pt-4 border-t border-ink/10">
            <p className="text-xs font-body text-ink/60">Custom evaluation weights configured</p>
          </div>
        )}
      </div>
    </Link>
  );
};

export default BusinessGroupCard;
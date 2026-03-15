import React from 'react';
import { Link } from 'react-router-dom';

const EmptyState = ({ title, description, actionText, actionLink }) => {
  return (
    <div className="text-center py-12">
      <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-teal/10 mb-4">
        <svg className="w-8 h-8 text-teal" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <h3 className="text-xl font-heading font-bold text-ink mb-2">{title}</h3>
      <p className="text-ink/60 font-body mb-6 max-w-md mx-auto">{description}</p>
      {actionText && actionLink && (
        <Link
          to={actionLink}
          className="inline-flex items-center px-6 py-3 bg-teal text-white rounded-lg font-body font-medium hover:bg-teal/90 transition"
        >
          {actionText}
        </Link>
      )}
    </div>
  );
};

export default EmptyState;
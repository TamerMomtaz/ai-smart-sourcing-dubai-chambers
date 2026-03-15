import React from 'react';

const SuccessBanner = ({ message, onDismiss }) => {
  if (!message) return null;

  return (
    <div className="mb-6 p-4 bg-teal/10 border border-teal rounded-lg flex items-start justify-between">
      <div className="flex items-start space-x-3">
        <svg className="w-5 h-5 text-teal mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
        </svg>
        <p className="text-teal font-body">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-teal hover:text-teal/80 transition"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      )}
    </div>
  );
};

export default SuccessBanner;
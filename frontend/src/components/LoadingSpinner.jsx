import React from 'react';

const LoadingSpinner = ({ size = 'md', text = null }) => {
  const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-12 w-12',
    lg: 'h-16 w-16'
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div className={`animate-spin rounded-full border-b-2 border-teal ${sizeClasses[size]}`}></div>
      {text && (
        <p className="mt-4 font-body text-ink/60 text-sm">{text}</p>
      )}
    </div>
  );
};

export default LoadingSpinner;
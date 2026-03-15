import React from 'react';

const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  const pages = [];
  const maxPagesToShow = 5;
  
  let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
  let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1);
  
  if (endPage - startPage < maxPagesToShow - 1) {
    startPage = Math.max(1, endPage - maxPagesToShow + 1);
  }

  for (let i = startPage; i <= endPage; i++) {
    pages.push(i);
  }

  return (
    <div className="flex items-center justify-center space-x-2">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 rounded-lg font-body text-sm font-medium text-ink border border-ink/20 hover:bg-teal hover:text-white hover:border-teal transition disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-ink"
      >
        Previous
      </button>

      {startPage > 1 && (
        <>
          <button
            onClick={() => onPageChange(1)}
            className="px-3 py-2 rounded-lg font-body text-sm font-medium text-ink border border-ink/20 hover:bg-teal hover:text-white hover:border-teal transition"
          >
            1
          </button>
          {startPage > 2 && (
            <span className="px-2 text-ink/40">...</span>
          )}
        </>
      )}

      {pages.map((page) => (
        <button
          key={page}
          onClick={() => onPageChange(page)}
          className={`px-3 py-2 rounded-lg font-body text-sm font-medium border transition ${
            page === currentPage
              ? 'bg-teal text-white border-teal'
              : 'text-ink border-ink/20 hover:bg-teal hover:text-white hover:border-teal'
          }`}
        >
          {page}
        </button>
      ))}

      {endPage < totalPages && (
        <>
          {endPage < totalPages - 1 && (
            <span className="px-2 text-ink/40">...</span>
          )}
          <button
            onClick={() => onPageChange(totalPages)}
            className="px-3 py-2 rounded-lg font-body text-sm font-medium text-ink border border-ink/20 hover:bg-teal hover:text-white hover:border-teal transition"
          >
            {totalPages}
          </button>
        </>
      )}

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 rounded-lg font-body text-sm font-medium text-ink border border-ink/20 hover:bg-teal hover:text-white hover:border-teal transition disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-ink"
      >
        Next
      </button>
    </div>
  );
};

export default Pagination;
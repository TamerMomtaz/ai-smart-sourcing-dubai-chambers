import React from 'react';

const StatusBadge = ({ status }) => {
  const getStatusStyles = (status) => {
    const normalized = status?.toLowerCase();
    switch (normalized) {
      case 'draft':
        return 'bg-ink/10 text-ink';
      case 'submitted':
        return 'bg-teal/10 text-teal';
      case 'evaluating':
      case 'in_progress':
      case 'processing':
        return 'bg-gold/10 text-gold';
      case 'under_review':
      case 'pending':
        return 'bg-amber-500/10 text-amber-600';
      case 'shortlisted':
        return 'bg-emerald-500/10 text-emerald-600';
      case 'needs_improvement':
        return 'bg-red-500/10 text-red-600';
      case 'revision_requested':
        return 'bg-purple-500/10 text-purple-600';
      case 'evaluated':
        return 'bg-blue-500/10 text-blue-600';
      case 'approved':
      case 'passed':
      case 'active':
      case 'completed':
        return 'bg-teal/10 text-teal';
      case 'rejected':
      case 'failed':
        return 'bg-burgundy/10 text-burgundy';
      default:
        return 'bg-ink/10 text-ink';
    }
  };

  const formatStatus = (status) => {
    if (!status) return 'Unknown';
    return status.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-body font-medium ${getStatusStyles(status)}`}>
      {formatStatus(status)}
    </span>
  );
};

export default StatusBadge;
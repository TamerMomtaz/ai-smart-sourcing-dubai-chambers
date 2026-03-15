import React from 'react';

const CommentCard = ({ comment }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getVisibilityIcon = (visibility) => {
    return visibility === 'internal' ? '🔒' : '👁️';
  };

  const getVisibilityColor = (visibility) => {
    return visibility === 'internal' ? 'bg-ink/10 text-ink' : 'bg-teal/10 text-teal';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 border border-ink/10">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-full bg-teal/10 flex items-center justify-center">
            <span className="text-sm font-body font-medium text-teal">
              {comment.user_name?.charAt(0) || '?'}
            </span>
          </div>
          <div>
            <p className="text-sm font-body font-medium text-ink">{comment.user_name || 'Unknown User'}</p>
            <p className="text-xs font-body text-ink/60">{formatDate(comment.created_at)}</p>
          </div>
        </div>
        <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-body font-medium ${getVisibilityColor(comment.visibility)}`}>
          {getVisibilityIcon(comment.visibility)} {comment.visibility === 'internal' ? 'Internal' : 'Visible to Vendor'}
        </span>
      </div>
      <p className="font-body text-ink whitespace-pre-wrap">{comment.comment_text}</p>
    </div>
  );
};

export default CommentCard;
import React from 'react';

const ScoreBadge = ({ score, label }) => {
  const getScoreColor = (score) => {
    if (score >= 80) return 'text-teal';
    if (score >= 60) return 'text-gold';
    return 'text-burgundy';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-teal/10';
    if (score >= 60) return 'bg-gold/10';
    return 'bg-burgundy/10';
  };

  if (score === null || score === undefined) return null;

  return (
    <div className="inline-flex flex-col items-start">
      {label && (
        <span className="text-xs font-body text-ink/60 mb-1">{label}</span>
      )}
      <div className={`inline-flex items-center px-3 py-1 rounded-lg ${getScoreBg(score)}`}>
        <span className={`text-lg font-heading font-bold ${getScoreColor(score)}`}>
          {score.toFixed(1)}
        </span>
        <span className={`text-sm font-body ml-1 ${getScoreColor(score)}`}>/100</span>
      </div>
    </div>
  );
};

export default ScoreBadge;
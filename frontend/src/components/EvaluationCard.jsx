import React from 'react';
import { Link } from 'react-router-dom';
import ScoreBadge from './ScoreBadge';

const EvaluationCard = ({ evaluation, proposalTitle }) => {
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

  return (
    <Link to={`/evaluations/${evaluation.id}`}>
      <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition cursor-pointer border border-transparent hover:border-teal">
        {proposalTitle && (
          <h3 className="text-lg font-heading font-bold text-ink mb-4">
            {proposalTitle}
          </h3>
        )}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <ScoreBadge score={evaluation.composite_score} label="Composite" />
          <ScoreBadge score={evaluation.relevance_score} label="Relevance" />
          <ScoreBadge score={evaluation.feasibility_score} label="Feasibility" />
          <ScoreBadge score={evaluation.sector_alignment_score} label="Sector Alignment" />
        </div>

        {evaluation.compliance_score !== null && evaluation.compliance_score !== undefined && (
          <div className="mb-4">
            <ScoreBadge score={evaluation.compliance_score} label="Compliance" />
          </div>
        )}

        <div className="flex items-center justify-between text-sm font-body text-ink/60 pt-4 border-t border-ink/10">
          <span>Evaluated: {formatDate(evaluation.evaluated_at)}</span>
          {evaluation.hallucination_check_passed === false && (
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-burgundy/10 text-burgundy">
              ⚠️ Hallucination Detected
            </span>
          )}
          {evaluation.prompt_injection_detected && (
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-burgundy/10 text-burgundy">
              ⚠️ Prompt Injection Detected
            </span>
          )}
        </div>
      </div>
    </Link>
  );
};

export default EvaluationCard;
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const EvaluationDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchEvaluation();
  }, [id]);

  const fetchEvaluation = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/evaluations/${id}`);
      setEvaluation(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-teal font-heading text-xl">Loading evaluation...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-burgundy font-body text-lg">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="font-heading text-4xl text-ink">Evaluation Detail</h1>
          <button
            onClick={() => navigate('/evaluations')}
            className="text-teal hover:underline font-body"
          >
            ← Back to Evaluations
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-8 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <span className="text-gray-600 font-body text-sm">Composite Score</span>
              <p className="text-teal font-bold text-3xl mt-1">{evaluation.composite_score}/100</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Evaluated At</span>
              <p className="text-ink font-semibold mt-1">
                {evaluation.evaluated_at ? new Date(evaluation.evaluated_at).toLocaleString() : 'N/A'}
              </p>
            </div>
          </div>

          <div className="border-t pt-6">
            <h3 className="font-heading text-2xl text-ink mb-4">Score Breakdown</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-ink font-semibold">Relevance</span>
                  <span className="text-teal font-bold">{evaluation.relevance_score}/100</span>
                </div>
                <p className="text-gray-600 text-sm">{evaluation.relevance_reasoning}</p>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-ink font-semibold">Feasibility</span>
                  <span className="text-teal font-bold">{evaluation.feasibility_score}/100</span>
                </div>
                <p className="text-gray-600 text-sm">{evaluation.feasibility_reasoning}</p>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-ink font-semibold">Sector Alignment</span>
                  <span className="text-teal font-bold">{evaluation.sector_alignment_score}/100</span>
                </div>
                <p className="text-gray-600 text-sm">{evaluation.sector_reasoning}</p>
              </div>
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-ink font-semibold">Compliance</span>
                  <span className="text-teal font-bold">{evaluation.compliance_score}/100</span>
                </div>
                <p className="text-gray-600 text-sm">{evaluation.compliance_reasoning}</p>
              </div>
            </div>
          </div>

          {evaluation.summary_en && (
            <div className="border-t pt-6">
              <h3 className="font-heading text-2xl text-ink mb-4">Summary (English)</h3>
              <p className="text-gray-700">{evaluation.summary_en}</p>
            </div>
          )}

          {evaluation.summary_ar && (
            <div className="border-t pt-6">
              <h3 className="font-heading text-2xl text-ink mb-4">Summary (Arabic)</h3>
              <p className="text-gray-700" dir="rtl">{evaluation.summary_ar}</p>
            </div>
          )}

          <div className="border-t pt-6">
            <div className="flex items-center gap-4">
              <div>
                <span className="text-gray-600 font-body text-sm">Hallucination Check</span>
                <p className="text-ink font-semibold mt-1">{evaluation.hallucination_check_passed ? '✓ Passed' : '✗ Failed'}</p>
              </div>
              <div>
                <span className="text-gray-600 font-body text-sm">Prompt Injection</span>
                <p className="text-ink font-semibold mt-1">{evaluation.prompt_injection_detected ? '⚠ Detected' : '✓ None'}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EvaluationDetail;
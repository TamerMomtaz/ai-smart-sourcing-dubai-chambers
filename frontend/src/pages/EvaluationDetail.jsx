import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const ScoreBar = ({ label, score, reasoning }) => {
  const [expanded, setExpanded] = useState(false);
  if (score == null) return null;
  const color = score > 70 ? '#10B981' : score >= 40 ? '#F59E0B' : '#EF4444';
  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1">
        <span className="text-gray-300 font-medium">{label}</span>
        <span className="font-bold" style={{ color }}>{score}/100</span>
      </div>
      <div className="w-full h-3 bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${score}%`, background: `linear-gradient(90deg, ${color}88, ${color})` }} />
      </div>
      {reasoning && (
        <>
          <button onClick={() => setExpanded(!expanded)} className="text-xs text-[#3B82F6] hover:text-blue-300 mt-1">
            {expanded ? '▾ Hide reasoning' : '▸ Show reasoning'}
          </button>
          {expanded && <p className="text-sm text-gray-400 mt-1 pl-2 border-l-2 border-gray-600">{reasoning}</p>}
        </>
      )}
    </div>
  );
};

const EvaluationDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showArabic, setShowArabic] = useState(false);

  useEffect(() => { fetchEvaluation(); }, [id]);

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
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#3B82F6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading evaluation...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-red-400 text-lg">{error}</div>
      </div>
    );
  }

  const aiCost = evaluation?.ai_cost;

  return (
    <div className="min-h-screen bg-[#0F172A] p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Evaluation Detail</h1>
          <button onClick={() => navigate('/evaluations')} className="text-[#3B82F6] hover:text-blue-300">
            ← Back to Evaluations
          </button>
        </div>

        {/* Proposal Info */}
        {evaluation.proposal && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-3">Proposal</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <span className="text-gray-500 text-sm">Title</span>
                <p className="text-white font-medium">{evaluation.proposal.title}</p>
              </div>
              <div>
                <span className="text-gray-500 text-sm">Sector</span>
                <p className="text-gray-300 capitalize">{evaluation.proposal.sector}</p>
              </div>
              <div>
                <span className="text-gray-500 text-sm">Technology</span>
                <p className="text-gray-300">{evaluation.proposal.technology_type}</p>
              </div>
              <div>
                <span className="text-gray-500 text-sm">Maturity</span>
                <p className="text-gray-300 capitalize">{evaluation.proposal.maturity_level}</p>
              </div>
            </div>
          </div>
        )}

        {/* Composite Score - Large */}
        <div className="bg-[#1E293B] rounded-xl p-8 mb-6 border border-gray-700/50 text-center">
          <div
            className="text-7xl font-black"
            style={{
              color: (evaluation.composite_score || 0) > 70 ? '#10B981' : (evaluation.composite_score || 0) >= 40 ? '#F59E0B' : '#EF4444'
            }}
          >
            {evaluation.composite_score?.toFixed(1) || '—'}
          </div>
          <p className="text-gray-400 mt-2">Composite Score</p>
          <p className="text-gray-600 text-xs mt-1">
            Evaluated {evaluation.evaluated_at ? new Date(evaluation.evaluated_at).toLocaleString() : '—'}
          </p>
        </div>

        {/* Score Breakdown */}
        <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
          <h3 className="text-xl font-bold text-white mb-6">Score Breakdown</h3>
          <ScoreBar label="Relevance" score={evaluation.relevance_score} reasoning={evaluation.relevance_reasoning} />
          <ScoreBar label="Feasibility" score={evaluation.feasibility_score} reasoning={evaluation.feasibility_reasoning} />
          <ScoreBar label="Sector Alignment" score={evaluation.sector_alignment_score} reasoning={evaluation.sector_reasoning} />
          <ScoreBar label="Compliance" score={evaluation.compliance_score} reasoning={evaluation.compliance_reasoning} />
        </div>

        {/* Executive Summary */}
        {(evaluation.summary_en || evaluation.summary_ar) && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Executive Summary</h3>
              {evaluation.summary_ar && (
                <button
                  onClick={() => setShowArabic(!showArabic)}
                  className="text-sm text-[#3B82F6] hover:text-blue-300 px-3 py-1 border border-[#3B82F6]/30 rounded"
                >
                  {showArabic ? 'English' : 'العربية'}
                </button>
              )}
            </div>
            {showArabic && evaluation.summary_ar ? (
              <p className="text-gray-300 leading-relaxed" dir="rtl">{evaluation.summary_ar}</p>
            ) : (
              <p className="text-gray-300 leading-relaxed">{evaluation.summary_en}</p>
            )}
          </div>
        )}

        {/* Safety Checks */}
        <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
          <h3 className="text-lg font-semibold text-white mb-3">Safety Checks</h3>
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              <span className={evaluation.hallucination_check_passed ? 'text-emerald-400' : 'text-red-400'}>
                {evaluation.hallucination_check_passed ? '✓' : '✕'}
              </span>
              <span className="text-gray-300 text-sm">Hallucination Check</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={!evaluation.prompt_injection_detected ? 'text-emerald-400' : 'text-red-400'}>
                {!evaluation.prompt_injection_detected ? '✓' : '⚠'}
              </span>
              <span className="text-gray-300 text-sm">Prompt Injection</span>
            </div>
          </div>
        </div>

        {/* AI Cost */}
        {aiCost && (
          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-semibold text-white mb-4">ΣI — Evaluation Cost</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-xl font-bold text-[#3B82F6]">{(aiCost.prompt_tokens + aiCost.completion_tokens).toLocaleString()}</p>
                <p className="text-gray-500 text-xs mt-1">Total Tokens</p>
              </div>
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-xl font-bold text-[#F59E0B]">${parseFloat(aiCost.cost_usd).toFixed(4)}</p>
                <p className="text-gray-500 text-xs mt-1">Cost (USD)</p>
              </div>
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-xl font-bold text-[#10B981]">{parseFloat(aiCost.energy_kwh).toFixed(6)}</p>
                <p className="text-gray-500 text-xs mt-1">Energy (kWh)</p>
              </div>
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-xl font-bold text-gray-300">{aiCost.latency_ms}ms</p>
                <p className="text-gray-500 text-xs mt-1">Latency</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EvaluationDetail;

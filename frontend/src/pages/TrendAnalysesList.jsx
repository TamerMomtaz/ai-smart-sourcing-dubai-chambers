import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bg = type === 'success' ? 'bg-emerald-600' : 'bg-red-600';
  return (
    <div className={`fixed top-6 right-6 z-50 ${bg} text-white px-6 py-3 rounded-lg shadow-2xl flex items-center gap-3`}>
      <span>{type === 'success' ? '✓' : '✕'}</span>
      <span>{message}</span>
      <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100">×</button>
    </div>
  );
};

const TrendReportCard = ({ report, analysisDate, submissionVolume, averageScores }) => {
  if (!report) return null;

  return (
    <div className="bg-[#1E293B] rounded-xl shadow-xl p-6 mb-6 border border-gray-700">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-xl font-bold text-white mb-1">{report.report_title || 'Trend Report'}</h3>
          <p className="text-gray-400 text-sm">
            {report.period || 'Current Period'} • {analysisDate ? new Date(analysisDate).toLocaleDateString() : ''} • {submissionVolume} proposals analyzed
          </p>
        </div>
        {report.d33_alignment_score != null && (
          <div className="text-center">
            <div className={`text-2xl font-bold ${report.d33_alignment_score >= 70 ? 'text-emerald-400' : report.d33_alignment_score >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
              {report.d33_alignment_score}
            </div>
            <div className="text-xs text-gray-500">D33 Alignment</div>
          </div>
        )}
      </div>

      {/* Key Findings */}
      {report.key_findings && report.key_findings.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Key Findings</h4>
          <ul className="space-y-2">
            {report.key_findings.map((finding, i) => (
              <li key={i} className="flex items-start gap-2 text-gray-300 text-sm">
                <span className="text-[#3B82F6] mt-0.5">•</span>
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Sector Breakdown */}
      {report.sector_breakdown && report.sector_breakdown.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Sector Breakdown</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-2 text-gray-400 font-medium">Sector</th>
                  <th className="text-right py-2 text-gray-400 font-medium">Count</th>
                  <th className="text-right py-2 text-gray-400 font-medium">Avg Score</th>
                  <th className="text-right py-2 text-gray-400 font-medium">Trend</th>
                </tr>
              </thead>
              <tbody>
                {report.sector_breakdown.map((s, i) => (
                  <tr key={i} className="border-b border-gray-700/50">
                    <td className="py-2 text-gray-300 capitalize">{s.sector}</td>
                    <td className="py-2 text-right text-gray-300">{s.count}</td>
                    <td className="py-2 text-right text-gray-300">{s.avg_score != null ? s.avg_score.toFixed(1) : '—'}</td>
                    <td className="py-2 text-right">
                      <span className={`text-xs font-medium ${s.trend === 'up' ? 'text-emerald-400' : s.trend === 'down' ? 'text-red-400' : 'text-gray-400'}`}>
                        {s.trend === 'up' ? '↑ Up' : s.trend === 'down' ? '↓ Down' : '→ Stable'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Top Technologies */}
      {report.top_technologies && report.top_technologies.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Top Technologies</h4>
          <div className="flex flex-wrap gap-2">
            {report.top_technologies.map((tech, i) => (
              <span key={i} className="bg-[#F59E0B]/20 text-[#F59E0B] px-3 py-1 rounded-full text-xs font-medium">
                {tech}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Compliance Insights */}
      {report.compliance_insights && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Compliance Insights</h4>
          <p className="text-gray-300 text-sm leading-relaxed">{report.compliance_insights}</p>
        </div>
      )}

      {/* Recommendations */}
      {report.recommendations && report.recommendations.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Recommendations</h4>
          <ol className="space-y-2 list-decimal list-inside">
            {report.recommendations.map((rec, i) => (
              <li key={i} className="text-gray-300 text-sm">{rec}</li>
            ))}
          </ol>
        </div>
      )}

      {/* Average Scores */}
      {averageScores && Object.keys(averageScores).length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Average Scores</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {Object.entries(averageScores).map(([key, val]) => (
              <div key={key} className="bg-[#0F172A] rounded-lg p-3 text-center">
                <div className="text-xs text-gray-500 mb-1 capitalize">{key.replace('_', ' ')}</div>
                <div className={`text-lg font-bold ${val > 70 ? 'text-emerald-400' : val >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                  {val?.toFixed(1) || 'N/A'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const PrintReportButton = () => {
  const handlePrint = () => {
    window.print();
  };

  return (
    <button
      onClick={handlePrint}
      className="bg-[#F59E0B] hover:bg-[#D97706] text-black font-semibold px-6 py-2.5 rounded-lg transition-colors flex items-center gap-2"
    >
      Export as PDF
    </button>
  );
};

const TrendAnalysesList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [toast, setToast] = useState(null);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20;

  useEffect(() => {
    fetchAnalyses();
  }, [page]);

  const fetchAnalyses = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/api/v1/trend-analyses?page=${page}&page_size=${pageSize}`);
      setAnalyses(res.data.trend_analyses || res.data.analyses || []);
      setPagination(res.data.pagination);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      const res = await api.post('/api/v1/trend-analyses/generate');
      setToast({ message: 'Trend report generated successfully!', type: 'success' });
      fetchAnalyses();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setGenerating(false);
    }
  };

  const handlePageChange = (newPage) => {
    setSearchParams({ page: newPage.toString() });
  };

  return (
    <div className="min-h-screen bg-[#0F172A] p-8">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      <div className="max-w-7xl mx-auto">
        {/* Print-specific CSS */}
        <style>{`
          @media print {
            body * { visibility: hidden; }
            .print-area, .print-area * { visibility: visible; }
            .print-area { position: absolute; left: 0; top: 0; width: 100%; padding: 20px; }
            .no-print { display: none !important; }
            .print-area { background: white !important; color: black !important; }
            .print-area h1, .print-area h3, .print-area h4 { color: black !important; }
            .print-area p, .print-area span, .print-area td, .print-area th, .print-area li { color: #333 !important; }
            .print-area .bg-\\[\\#1E293B\\], .print-area .bg-\\[\\#0F172A\\] { background: white !important; border: 1px solid #ddd !important; }
          }
        `}</style>

        <header className="mb-6 flex items-center justify-between no-print">
          <h1 className="text-3xl font-bold text-white">Trend Analyses</h1>
          <div className="flex items-center gap-3">
            {analyses.length > 0 && <PrintReportButton />}
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="bg-[#3B82F6] hover:bg-blue-600 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {generating ? (
                <>
                  <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
                  Generating Report...
                </>
              ) : (
                'Generate Trend Report'
              )}
            </button>
          </div>
        </header>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {loading ? (
          <div className="p-12 text-center">
            <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#3B82F6] mx-auto mb-4"></div>
            <p className="text-gray-400">Loading trend analyses...</p>
          </div>
        ) : analyses.length === 0 ? (
          /* empty state - no print-area wrapper needed */
          <div className="bg-[#1E293B] rounded-xl shadow-xl p-12 text-center border border-gray-700">
            <p className="text-gray-500 mb-4">No trend analyses found</p>
            <p className="text-gray-600 text-sm">Click "Generate Trend Report" to create your first AI-powered trend analysis.</p>
          </div>
        ) : (
          <div className="space-y-6 print-area">
            {analyses.map((a) => {
              const report = a.technology_trends_json || a.technology_trends || null;
              return (
                <TrendReportCard
                  key={a.id}
                  report={report}
                  analysisDate={a.analysis_date}
                  submissionVolume={a.submission_volume}
                  averageScores={a.average_scores}
                />
              );
            })}
          </div>
        )}

        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center space-x-3 mt-6 no-print">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page === 1}
              className="px-4 py-2 rounded-lg bg-[#1E293B] text-gray-300 border border-gray-700 disabled:opacity-40 hover:bg-gray-700 transition"
            >
              Previous
            </button>
            <span className="text-gray-400">
              Page {page} of {pagination.total_pages}
            </span>
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page === pagination.total_pages}
              className="px-4 py-2 rounded-lg bg-[#1E293B] text-gray-300 border border-gray-700 disabled:opacity-40 hover:bg-gray-700 transition"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrendAnalysesList;

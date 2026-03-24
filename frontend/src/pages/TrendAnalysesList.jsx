import React, { useEffect, useState, useRef } from 'react';
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
      <span>{type === 'success' ? '\u2713' : '\u2715'}</span>
      <span>{message}</span>
      <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100">\u00d7</button>
    </div>
  );
};

function getCurrentQuarter() {
  const now = new Date();
  const q = Math.ceil((now.getMonth() + 1) / 3);
  return { quarter: q, year: now.getFullYear(), label: `Q${q} ${now.getFullYear()}` };
}

function getReportPeriod(analysisDate) {
  if (!analysisDate) return null;
  const d = new Date(analysisDate);
  const q = Math.ceil((d.getMonth() + 1) / 3);
  return `Q${q} ${d.getFullYear()}`;
}

const PRINT_STYLES = `
@media print {
  /* Hide everything except the printing report */
  body * { visibility: hidden !important; }
  .printing-report, .printing-report * { visibility: visible !important; }
  .printing-report {
    position: absolute !important;
    left: 0 !important;
    top: 0 !important;
    width: 100% !important;
    padding: 24px !important;
    background: white !important;
    color: #1a1a1a !important;
  }

  /* Force page to end after content — prevent blank pages */
  html, body {
    height: auto !important;
    overflow: visible !important;
    margin: 0 !important;
    padding: 0 !important;
  }

  /* Prevent empty pages */
  .printing-report::after {
    content: '';
    display: block;
    page-break-after: avoid;
  }

  /* Hide non-printing report cards completely so they take no space */
  .space-y-6 > div:not(.printing-report) {
    display: none !important;
  }

  /* White background overrides */
  .printing-report .bg-\\[\\#1E293B\\],
  .printing-report .bg-\\[\\#0F172A\\] {
    background: white !important;
    border: 1px solid #e5e7eb !important;
  }

  /* Text colors for print */
  .printing-report h1, .printing-report h2, .printing-report h3, .printing-report h4 {
    color: #111827 !important;
  }
  .printing-report p, .printing-report span, .printing-report td,
  .printing-report th, .printing-report li, .printing-report div {
    color: #374151 !important;
  }

  /* Print header */
  .print-header { display: block !important; visibility: visible !important; }

  /* Print footer */
  .print-footer { display: block !important; visibility: visible !important; }

  /* Hide buttons, nav, sidebar, and non-printing content */
  .no-print, nav, aside, [role="navigation"] { display: none !important; }

  /* Collapse empty containers that are not part of the report */
  .min-h-screen { min-height: 0 !important; height: auto !important; }

  /* D33 score prominent */
  .d33-print-score { font-size: 28px !important; font-weight: bold !important; color: #016764 !important; }

  /* Page breaks */
  .print-section { page-break-inside: avoid; margin-bottom: 16px; }
  .print-page-break { page-break-before: always; }

  @page { margin: 20mm 15mm; }
}
`;

const TrendReportCard = ({ report, analysisDate, submissionVolume, averageScores, reportId }) => {
  const cardRef = useRef(null);

  if (!report) return null;

  const period = report.period || getReportPeriod(analysisDate) || 'Current Period';

  const handleExportPDF = () => {
    // Add printing class to only this report
    if (cardRef.current) {
      cardRef.current.classList.add('printing-report');
      window.print();
      cardRef.current.classList.remove('printing-report');
    }
  };

  return (
    <div ref={cardRef} id={`report-${reportId}`} className="bg-[#1E293B] rounded-xl shadow-xl p-6 mb-6 border border-gray-700">
      {/* Print-only header */}
      <div className="print-header hidden mb-6 border-b-2 border-gray-300 pb-4">
        <h1 className="text-2xl font-bold">AI Smart Sourcing — Dubai Chambers</h1>
        <p className="text-sm text-gray-500 mt-1">Trend Analysis Report</p>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-xl font-bold text-white">{report.report_title || 'Trend Report'}</h3>
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-[#F59E0B]/20 text-[#F59E0B]">
              {period}
            </span>
          </div>
          <p className="text-gray-400 text-sm">
            {analysisDate ? new Date(analysisDate).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) : ''}
            {' '}&middot;{' '}{submissionVolume} proposals analyzed
          </p>
        </div>
        <div className="flex items-center gap-3">
          {report.d33_alignment_score != null && (
            <div className="text-center">
              <div className={`text-2xl font-bold d33-print-score ${report.d33_alignment_score >= 70 ? 'text-emerald-400' : report.d33_alignment_score >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                {report.d33_alignment_score}
              </div>
              <div className="text-xs text-[#94A3B8]">D33 Alignment</div>
            </div>
          )}
          <button
            onClick={handleExportPDF}
            className="no-print bg-[#F59E0B] hover:bg-[#D97706] text-black font-semibold px-4 py-2 rounded-lg transition-colors text-sm flex items-center gap-1"
            title="Export this report as PDF"
          >
            Export PDF
          </button>
        </div>
      </div>

      {/* Key Findings */}
      {report.key_findings && report.key_findings.length > 0 && (
        <div className="mb-6 print-section">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Key Findings</h4>
          <ul className="space-y-2">
            {report.key_findings.map((finding, i) => (
              <li key={i} className="flex items-start gap-2 text-gray-300 text-sm">
                <span className="text-[#3B82F6] mt-0.5">&bull;</span>
                <span>{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Sector Breakdown */}
      {report.sector_breakdown && report.sector_breakdown.length > 0 && (
        <div className="mb-6 print-section print-page-break">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Sector Breakdown</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" style={{ minWidth: '700px' }}>
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
                    <td className="py-2 text-right text-gray-300">{s.avg_score != null ? s.avg_score.toFixed(1) : '\u2014'}</td>
                    <td className="py-2 text-right">
                      <span className={`text-xs font-medium ${s.trend === 'up' ? 'text-emerald-400' : s.trend === 'down' ? 'text-red-400' : 'text-gray-400'}`}>
                        {s.trend === 'up' ? '\u2191 Up' : s.trend === 'down' ? '\u2193 Down' : '\u2192 Stable'}
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
        <div className="mb-6 print-section">
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
        <div className="mb-6 print-section">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Compliance Insights</h4>
          <p className="text-gray-300 text-sm leading-relaxed">{report.compliance_insights}</p>
        </div>
      )}

      {/* Recommendations */}
      {report.recommendations && report.recommendations.length > 0 && (
        <div className="mb-6 print-section print-page-break">
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
        <div className="print-section">
          <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Average Scores</h4>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {Object.entries(averageScores).map(([key, val]) => (
              <div key={key} className="bg-[#0F172A] rounded-lg p-3 text-center">
                <div className="text-xs text-[#94A3B8] mb-1 capitalize">{key.replace('_', ' ')}</div>
                <div className={`text-lg font-bold ${val > 70 ? 'text-emerald-400' : val >= 40 ? 'text-amber-400' : 'text-red-400'}`}>
                  {val?.toFixed(1) || 'N/A'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Print-only footer */}
      <div className="print-footer hidden mt-8 pt-4 border-t-2 border-gray-300 text-center">
        <p className="text-sm text-gray-500">Generated by <strong>Tamer Momtaz</strong> | &sigma;I Technology</p>
      </div>
    </div>
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
  const currentQ = getCurrentQuarter();

  useEffect(() => {
    fetchAnalyses();
  }, [page]);

  const fetchAnalyses = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get(`/api/v1/trend-analyses?page=${page}&page_size=${pageSize}`);
      const data = res.data.trend_analyses || res.data.analyses || [];
      // Sort by analysis_date descending (latest first)
      data.sort((a, b) => new Date(b.analysis_date || 0) - new Date(a.analysis_date || 0));
      setAnalyses(data);
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
      await api.post('/api/v1/trend-analyses/generate');
      setToast({ message: `${currentQ.label} trend report generated successfully!`, type: 'success' });
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
        {/* Print CSS */}
        <style>{PRINT_STYLES}</style>

        <header className="mb-6 flex items-center justify-between no-print">
          <div>
            <h1 className="text-3xl font-bold text-white">Trend Analyses</h1>
            <p className="text-gray-400 mt-1">AI-powered market intelligence reports</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="bg-[#3B82F6] hover:bg-blue-600 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {generating ? (
                <>
                  <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span>
                  Generating...
                </>
              ) : (
                `Generate ${currentQ.label} Report`
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
          <div className="bg-[#1E293B] rounded-xl shadow-xl p-12 text-center border border-gray-700">
            <p className="text-[#94A3B8] mb-4">No trend analyses found</p>
            <p className="text-[#94A3B8] text-sm">Click "Generate {currentQ.label} Report" to create your first AI-powered trend analysis.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {analyses.map((a) => {
              const report = a.technology_trends_json || a.technology_trends || null;
              return (
                <TrendReportCard
                  key={a.id}
                  reportId={a.id}
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

import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';

const TIER_COLORS = {
  platinum: '#0D9488',
  gold: '#B8904A',
  silver: '#3B82F6',
  bronze: '#F59E0B',
  under_review: '#EF4444',
};

const TIER_LABELS = {
  platinum: 'Platinum',
  gold: 'Gold',
  silver: 'Silver',
  bronze: 'Bronze',
  under_review: 'Under Review',
};

function fmtDate(iso) {
  if (!iso) return 'N/A';
  try { return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }); }
  catch { return iso; }
}

function fmtScore(v) {
  if (v == null) return '-';
  return Number(v).toFixed(1);
}

export default function VendorFactsheet() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sourcingCaseId = searchParams.get('sourcing_case_id');

  const [factsheet, setFactsheet] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [emptyStateMessage, setEmptyStateMessage] = useState(null);

  useEffect(() => {
    fetchFactsheet();
  }, [id, sourcingCaseId]);

  const fetchFactsheet = async () => {
    try {
      setLoading(true);
      setEmptyStateMessage(null);
      const params = sourcingCaseId ? `?sourcing_case_id=${sourcingCaseId}` : '';
      const { data } = await api.get(`/api/v1/vendors/${id}/factsheet${params}`);
      setFactsheet(data);
    } catch (err) {
      setFactsheet(null);
      // 404 = no factsheet generated yet — page-body UI offers Generate button
      if (err?.friendly?.status !== 404) {
        setEmptyStateMessage(
          err?.friendly?.message || 'Factsheet data is being prepared.'
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setEmptyStateMessage(null);
      const body = sourcingCaseId ? { sourcing_case_id: sourcingCaseId } : {};
      const { data } = await api.post(`/api/v1/vendors/${id}/factsheet`, body);
      setFactsheet(data);
    } catch (err) {
      setEmptyStateMessage(
        err?.friendly?.message || 'Factsheet data is being prepared.'
      );
    } finally {
      setGenerating(false);
    }
  };

  const handlePrint = () => window.print();

  const handleShare = () => {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(
      () => alert('Link copied to clipboard'),
      () => alert('Could not copy link')
    );
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: 48, height: 48, border: '4px solid #e5e7eb', borderTopColor: '#0D9488', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
          <p style={{ color: '#6b7280' }}>Loading factsheet...</p>
        </div>
      </div>
    );
  }

  if (!factsheet) {
    return (
      <div className="max-w-3xl mx-auto py-8 px-4">
        <button onClick={() => navigate(-1)} className="text-teal hover:underline text-sm mb-6 block">
          ← Back
        </button>
        <div className="bg-white rounded-xl shadow-sm p-8 text-center">
          <p className="text-ink/70 mb-4">
            {emptyStateMessage || 'No factsheet has been generated for this vendor yet.'}
          </p>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-6 py-3 bg-teal text-white rounded-lg font-semibold hover:bg-teal/90 disabled:opacity-50 transition"
          >
            {generating ? 'Generating...' : 'Generate Factsheet'}
          </button>
        </div>
      </div>
    );
  }

  const c = factsheet.content || {};
  const v = c.vendor || {};
  const desc = c.desc_status || {};
  const tl = c.trade_license || {};
  const vs = c.vscore || {};
  const dims = vs.dimension_scores || {};
  const evals = c.top_evaluations || [];
  const pilots = c.pilots || [];
  const caseCtx = c.sourcing_case_context;
  const tierColor = TIER_COLORS[vs.vscore_tier] || '#94A3B8';

  return (
    <>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @media print {
          .no-print { display: none !important; }
          body { margin: 0; padding: 0; background: #fff !important; }
          @page { margin: 18mm 14mm; }
          .fs-container { padding: 0 !important; box-shadow: none !important; }
        }
      `}</style>

      <div className="max-w-4xl mx-auto py-6 px-4">
        {/* Action bar */}
        <div className="no-print flex flex-wrap items-center justify-between gap-3 mb-6">
          <button onClick={() => navigate(-1)} className="text-teal hover:underline text-sm">
            ← Back
          </button>
          <div className="flex gap-2">
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="px-4 py-2 bg-teal text-white rounded-lg text-sm font-semibold hover:bg-teal/90 disabled:opacity-50 transition"
            >
              {generating ? 'Regenerating...' : 'Regenerate'}
            </button>
            <button
              onClick={handlePrint}
              className="px-4 py-2 bg-[#1E293B] text-white rounded-lg text-sm font-semibold hover:bg-[#334155] transition"
            >
              Download as PDF
            </button>
            <button
              onClick={handleShare}
              className="px-4 py-2 border border-ink/20 text-ink rounded-lg text-sm font-semibold hover:bg-gray-50 transition"
            >
              Share
            </button>
          </div>
        </div>

        {/* Factsheet Card */}
        <div className="fs-container bg-white rounded-xl shadow-lg overflow-hidden">
          {/* Header */}
          <div style={{ backgroundColor: '#0D9488' }} className="px-8 py-6 text-white">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-widest opacity-70 mb-1">Vendor Factsheet</p>
                <h1 className="text-2xl md:text-3xl font-bold">{v.name || 'Unknown Vendor'}</h1>
                <p className="text-white/80 text-sm mt-1">
                  {v.country}{v.website ? ` \u00B7 ${v.website}` : ''}
                </p>
              </div>
              {/* vScore badge */}
              {vs.vscore != null && (
                <div className="flex flex-col items-center">
                  <div
                    className="w-16 h-16 rounded-full flex items-center justify-center border-4"
                    style={{ borderColor: 'rgba(255,255,255,0.4)', backgroundColor: 'rgba(255,255,255,0.15)' }}
                  >
                    <span className="text-xl font-black text-white">{vs.vscore}</span>
                  </div>
                  <span className="text-xs font-bold mt-1 uppercase tracking-wide opacity-80">
                    {TIER_LABELS[vs.vscore_tier] || vs.vscore_tier || ''}
                  </span>
                </div>
              )}
            </div>
          </div>

          <div className="px-8 py-6 space-y-6">
            {/* AI Executive Summary */}
            {factsheet.ai_summary && (
              <div className="bg-teal/5 border-l-4 border-teal rounded-r-lg p-4">
                <h2 className="text-xs uppercase tracking-wider text-teal font-bold mb-2">Executive Summary</h2>
                <p className="text-ink text-sm leading-relaxed">{factsheet.ai_summary}</p>
              </div>
            )}

            {/* Status Badges Row */}
            <div className="flex flex-wrap gap-3">
              {/* DESC */}
              <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold ${
                desc.approved ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-500'
              }`}>
                {desc.approved ? '\u2713 DESC Approved' : '\u2717 DESC Not Approved'}
              </span>
              {desc.certified && (
                <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
                  DESC Certified{desc.certification_level ? ` (${desc.certification_level})` : ''}
                </span>
              )}
              {/* Trade License */}
              <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold ${
                tl.status === 'verified' ? 'bg-emerald-100 text-emerald-700' :
                tl.status === 'pending' ? 'bg-amber-100 text-amber-700' :
                'bg-gray-100 text-gray-500'
              }`}>
                Trade License: {(tl.status || 'unverified').charAt(0).toUpperCase() + (tl.status || 'unverified').slice(1)}
              </span>
            </div>

            {/* vScore Dimensional Breakdown */}
            {Object.keys(dims).length > 0 && (
              <div>
                <h2 className="text-xs uppercase tracking-wider text-ink/50 font-bold mb-3">vScore Breakdown</h2>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  {['performance', 'quality', 'compliance', 'integrity', 'entity'].map(dim => (
                    <div key={dim} className="text-center">
                      <div className="relative w-14 h-14 mx-auto">
                        <svg width="56" height="56" viewBox="0 0 56 56">
                          <circle cx="28" cy="28" r="24" fill="none" stroke="#e5e7eb" strokeWidth="4" />
                          <circle
                            cx="28" cy="28" r="24" fill="none"
                            stroke={tierColor} strokeWidth="4" strokeLinecap="round"
                            strokeDasharray={2 * Math.PI * 24}
                            strokeDashoffset={2 * Math.PI * 24 * (1 - (dims[dim] || 0) / 100)}
                            transform="rotate(-90 28 28)"
                          />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-ink">
                          {dims[dim] ?? '-'}
                        </span>
                      </div>
                      <p className="text-[10px] text-ink/60 mt-1 capitalize">{dim}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top Evaluation Scores */}
            {evals.length > 0 && (
              <div>
                <h2 className="text-xs uppercase tracking-wider text-ink/50 font-bold mb-3">Top Evaluation Scores</h2>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="text-left px-3 py-2 text-ink/60 font-medium">Proposal</th>
                        <th className="px-3 py-2 text-ink/60 font-medium">Composite</th>
                        <th className="px-3 py-2 text-ink/60 font-medium">Relevance</th>
                        <th className="px-3 py-2 text-ink/60 font-medium">Feasibility</th>
                        <th className="px-3 py-2 text-ink/60 font-medium">Compliance</th>
                        <th className="px-3 py-2 text-ink/60 font-medium">Novelty</th>
                      </tr>
                    </thead>
                    <tbody>
                      {evals.map((ev, i) => (
                        <tr key={i} className="border-b border-gray-100">
                          <td className="px-3 py-2 text-ink font-medium max-w-[200px] truncate">{ev.proposal_title || '-'}</td>
                          <td className="px-3 py-2 text-center">
                            <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-bold ${
                              (ev.composite_score || 0) >= 70 ? 'bg-emerald-100 text-emerald-700' :
                              (ev.composite_score || 0) >= 40 ? 'bg-amber-100 text-amber-700' :
                              'bg-red-100 text-red-700'
                            }`}>
                              {fmtScore(ev.composite_score)}
                            </span>
                          </td>
                          <td className="px-3 py-2 text-center text-ink/70">{fmtScore(ev.relevance)}</td>
                          <td className="px-3 py-2 text-center text-ink/70">{fmtScore(ev.feasibility)}</td>
                          <td className="px-3 py-2 text-center text-ink/70">{fmtScore(ev.compliance)}</td>
                          <td className="px-3 py-2 text-center text-ink/70">{fmtScore(ev.novelty)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Sourcing Case Relevance */}
            {caseCtx && (
              <div className="bg-blue-50 rounded-lg p-4">
                <h2 className="text-xs uppercase tracking-wider text-blue-700 font-bold mb-2">Sourcing Case Relevance</h2>
                <p className="text-sm font-semibold text-ink">{caseCtx.title}</p>
                <p className="text-xs text-ink/60 mt-1">{caseCtx.problem_statement}</p>
                <div className="flex gap-3 mt-2">
                  {caseCtx.sector && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-teal/10 text-teal font-medium">
                      {caseCtx.sector}
                    </span>
                  )}
                  {caseCtx.urgency && (
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      caseCtx.urgency === 'critical' ? 'bg-red-100 text-red-700' :
                      caseCtx.urgency === 'high' ? 'bg-orange-100 text-orange-700' :
                      'bg-gray-100 text-gray-600'
                    }`}>
                      {caseCtx.urgency}
                    </span>
                  )}
                  {caseCtx.compliance_tier && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium">
                      {caseCtx.compliance_tier}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Pilot History */}
            {pilots.length > 0 && (
              <div>
                <h2 className="text-xs uppercase tracking-wider text-ink/50 font-bold mb-3">Pilot History</h2>
                <div className="space-y-2">
                  {pilots.map((p, i) => (
                    <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-gray-100">
                      <div>
                        <p className="text-sm font-medium text-ink">{p.title || 'Untitled Pilot'}</p>
                        <p className="text-xs text-ink/50">
                          {fmtDate(p.start_date)} — {fmtDate(p.end_date)}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          p.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                          p.status === 'active' ? 'bg-blue-100 text-blue-700' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {p.status}
                        </span>
                        {p.outcome_rating != null && (
                          <span className="text-amber-400 text-sm">
                            {'★'.repeat(Math.round(p.outcome_rating))}{'☆'.repeat(5 - Math.round(p.outcome_rating))}
                          </span>
                        )}
                        {p.adoption_decision && (
                          <span className={`text-xs font-bold ${
                            p.adoption_decision === 'adopt' ? 'text-emerald-600' : 'text-red-500'
                          }`}>
                            {p.adoption_decision === 'adopt' ? 'Adopted' : 'Rejected'}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Vendor Details Grid */}
            <div>
              <h2 className="text-xs uppercase tracking-wider text-ink/50 font-bold mb-3">Vendor Details</h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                {v.contact_email && (
                  <div>
                    <span className="text-ink/40 text-xs">Email</span>
                    <p className="text-ink font-medium">{v.contact_email}</p>
                  </div>
                )}
                {v.team_size && (
                  <div>
                    <span className="text-ink/40 text-xs">Team Size</span>
                    <p className="text-ink font-medium">{v.team_size}</p>
                  </div>
                )}
                {v.funding_stage && (
                  <div>
                    <span className="text-ink/40 text-xs">Funding Stage</span>
                    <p className="text-ink font-medium">{v.funding_stage}</p>
                  </div>
                )}
                {v.certifications && v.certifications.length > 0 && (
                  <div className="col-span-2 sm:col-span-3">
                    <span className="text-ink/40 text-xs">Certifications</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {v.certifications.map((cert, i) => (
                        <span key={i} className="px-2 py-0.5 bg-gray-100 rounded-full text-xs text-ink/70">
                          {cert}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="border-t pt-4 flex items-center justify-between text-xs text-ink/40">
              <span>Generated {fmtDate(factsheet.created_at)}</span>
              <span>Dubai Chambers — AI Smart Sourcing</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

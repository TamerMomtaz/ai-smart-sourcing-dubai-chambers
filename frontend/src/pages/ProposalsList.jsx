import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const TEAL = '#0D9488';

const ShieldIconSvg = ({ size = 12, color = TEAL }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ display: 'inline-block', verticalAlign: 'middle' }}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const ProposalShieldBadge = ({ proposalId }) => {
  const [gs, setGs] = useState(null);

  useEffect(() => {
    if (!proposalId) return;
    const fetchShield = async () => {
      try {
        // Fetch evaluation for this proposal, then check shield
        const evalRes = await api.get(`/api/v1/chamber-evaluations/proposal/${proposalId}`);
        const evaluation = evalRes.data;
        if (!evaluation?.id) return;
        const shieldRes = await api.get(`/api/v1/evaluations/${evaluation.id}/shield`);
        if (shieldRes.data?.grounding_score != null) {
          setGs(parseFloat(shieldRes.data.grounding_score));
        }
      } catch (err) {
        // Not verified or no evaluation — that's fine
      }
    };
    fetchShield();
  }, [proposalId]);

  if (gs == null) return null;
  const color = gs >= 85 ? '#10B981' : gs >= 65 ? '#F59E0B' : '#EF4444';

  return (
    <span className="inline-flex items-center gap-0.5 ml-1.5 text-xs font-bold" style={{ color }}>
      <ShieldIconSvg size={11} color={color} />
      {gs}%
    </span>
  );
};

const STATUS_COLORS = {
  queued: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  evaluating: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  evaluated: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  approved: 'bg-emerald-600/20 text-emerald-300 border-emerald-600/30',
  rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
  requires_review: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  draft: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  submitted: 'bg-blue-400/20 text-blue-300 border-blue-400/30',
};

const ScoreBadge = ({ score }) => {
  if (score == null) return <span className="text-gray-500 text-sm">—</span>;
  const color = score > 70 ? 'text-emerald-400' : score >= 40 ? 'text-amber-400' : 'text-red-400';
  const bg = score > 70 ? 'bg-emerald-500/20' : score >= 40 ? 'bg-amber-500/20' : 'bg-red-500/20';
  return (
    <span className={`${bg} ${color} px-2 py-0.5 rounded-full text-xs font-bold`}>
      {score.toFixed(1)}
    </span>
  );
};

const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bg = type === 'success' ? 'bg-emerald-600' : 'bg-red-600';
  return (
    <div className={`fixed top-6 right-6 z-50 ${bg} text-white px-6 py-3 rounded-lg shadow-2xl flex items-center gap-3 animate-slide-in`}>
      <span>{type === 'success' ? '✓' : '✕'}</span>
      <span>{message}</span>
      <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100">×</button>
    </div>
  );
};

const ProposalsList = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [proposals, setProposals] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [businessGroups, setBusinessGroups] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [evaluatingId, setEvaluatingId] = useState(null);
  const [auditingId, setAuditingId] = useState(null);
  const [toast, setToast] = useState(null);
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    sector: searchParams.get('sector') || '',
  });
  const [formData, setFormData] = useState({
    title: '',
    sector: '',
    technology_type: '',
    maturity_level: '',
    language: 'en',
    description: '',
  });

  // PDF upload state
  const [showIngestModal, setShowIngestModal] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [ingestStep, setIngestStep] = useState('upload'); // upload | extracting | review
  const [ingestData, setIngestData] = useState(null);
  const [ingestFile, setIngestFile] = useState(null);
  const [confirmingIngestion, setConfirmingIngestion] = useState(false);

  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = 20;

  useEffect(() => {
    fetchProposals();
  }, [page, searchParams]);

  useEffect(() => {
    fetchBusinessGroups();
  }, []);

  const fetchProposals = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
      if (filters.status) params.append('status', filters.status);
      if (filters.sector) params.append('sector', filters.sector);
      const res = await api.get(`/api/v1/proposals?${params.toString()}`);
      setProposals(res.data.proposals || []);
      setPagination(res.data.pagination);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const fetchBusinessGroups = async () => {
    try {
      const res = await api.get('/api/v1/business-groups');
      setBusinessGroups(res.data.business_groups || []);
    } catch (err) {
      console.error('Failed to load business groups:', err);
    }
  };

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    const params = new URLSearchParams({ page: '1' });
    if (newFilters.status) params.set('status', newFilters.status);
    if (newFilters.sector) params.set('sector', newFilters.sector);
    setSearchParams(params);
  };

  const handlePageChange = (newPage) => {
    const params = new URLSearchParams(searchParams);
    params.set('page', newPage.toString());
    setSearchParams(params);
  };

  const handleSubmitProposal = async (e) => {
    e.preventDefault();
    if (!formData.title || !formData.sector || !formData.technology_type || !formData.maturity_level) return;
    try {
      setSubmitting(true);
      await api.post('/api/v1/proposals', formData);
      setToast({ message: 'Proposal submitted! Status: Queued for AI evaluation', type: 'success' });
      setShowModal(false);
      setFormData({ title: '', sector: '', technology_type: '', maturity_level: '', language: 'en', description: '' });
      fetchProposals();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  const handleEvaluate = async (proposalId) => {
    if (!window.confirm('Run AI evaluation on this proposal?')) return;
    try {
      setEvaluatingId(proposalId);
      await api.post(`/api/v1/proposals/${proposalId}/evaluate`);
      setToast({ message: 'AI evaluation completed successfully!', type: 'success' });
      fetchProposals();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setEvaluatingId(null);
    }
  };

  const handleAudit = async (proposalId) => {
    try {
      setAuditingId(proposalId);
      const res = await api.post(`/api/v1/proposals/${proposalId}/audit`);
      const auditScore = res.data?.overall_score ?? null;
      // Optimistically update the proposal row
      setProposals((prev) =>
        prev.map((p) =>
          p.id === proposalId ? { ...p, has_audit: true, audit_score: auditScore } : p
        )
      );
      setToast({ message: 'Audit complete — view results on the Compliance Audits page', type: 'success' });
    } catch (err) {
      const msg = getErrorMessage(err);
      if (msg && (msg.includes('already audited') || (err.response && err.response.status === 400))) {
        setToast({ message: 'This proposal has already been audited', type: 'success' });
        fetchProposals();
      } else {
        setToast({ message: msg, type: 'error' });
      }
    } finally {
      setAuditingId(null);
    }
  };

  const handleUploadPDF = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIngestFile(file);
    setShowIngestModal(true);
    setIngestStep('extracting');
    setIngesting(true);

    try {
      const formPayload = new FormData();
      formPayload.append('file', file);
      const res = await api.post('/api/v1/proposals/ingest-document', formPayload, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setIngestData(res.data.extracted);
      setIngestStep('review');
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
      setShowIngestModal(false);
      setIngestStep('upload');
    } finally {
      setIngesting(false);
      // Reset file input
      e.target.value = '';
    }
  };

  const handleConfirmIngestion = async () => {
    if (!ingestData) return;
    try {
      setConfirmingIngestion(true);
      const payload = {
        ...ingestData,
        file_name: ingestFile?.name,
        file_size: ingestFile?.size || 0,
      };
      await api.post('/api/v1/proposals/confirm-ingestion', payload);
      setToast({ message: 'Proposal created from uploaded document!', type: 'success' });
      setShowIngestModal(false);
      setIngestData(null);
      setIngestFile(null);
      setIngestStep('upload');
      fetchProposals();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setConfirmingIngestion(false);
    }
  };

  const handleIngestFieldChange = (key, value) => {
    setIngestData(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="min-h-screen bg-[#0F172A] p-8">
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}

      <div className="max-w-7xl mx-auto">
        <header className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">Proposals</h1>
          <div className="flex items-center gap-3">
            <label className="bg-[#0D9488] hover:bg-teal-700 text-white font-semibold px-6 py-2.5 rounded-lg transition-colors cursor-pointer flex items-center gap-2">
              <span>Upload Proposal PDF</span>
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleUploadPDF}
                className="hidden"
              />
            </label>
            <button
              onClick={() => setShowModal(true)}
              className="bg-[#F59E0B] hover:bg-[#D97706] text-black font-semibold px-6 py-2.5 rounded-lg transition-colors"
            >
              + Submit New Proposal
            </button>
          </div>
        </header>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* Filters */}
        <div className="bg-[#1E293B] rounded-xl p-4 mb-6 flex gap-4">
          <select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
          >
            <option value="">All Statuses</option>
            <option value="queued">Queued</option>
            <option value="submitted">Submitted</option>
            <option value="evaluating">Evaluating</option>
            <option value="evaluated">Evaluated</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="requires_review">Requires Review</option>
          </select>
          <select
            value={filters.sector}
            onChange={(e) => handleFilterChange('sector', e.target.value)}
            className="bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#3B82F6]"
          >
            <option value="">All Sectors</option>
            {businessGroups.map((bg) => (
              <option key={bg.id} value={bg.name}>{bg.name}</option>
            ))}
          </select>
        </div>

        {/* Table */}
        <div className="bg-[#1E293B] rounded-xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#3B82F6] mx-auto mb-4"></div>
              <p className="text-gray-400">Loading proposals...</p>
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-[#0F172A] border-b border-gray-700">
                <tr>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Title</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Sector</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Status</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Score</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Submitted</th>
                  <th className="text-left p-4 text-gray-400 font-medium text-sm">Actions</th>
                </tr>
              </thead>
              <tbody>
                {proposals.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center p-12 text-gray-500">
                      No proposals found. Submit your first proposal!
                    </td>
                  </tr>
                ) : (
                  proposals.map((p) => (
                    <tr key={p.id} className="border-b border-gray-700/50 hover:bg-[#0F172A]/50 transition-colors">
                      <td className="p-4">
                        <Link to={`/proposals/${p.id}`} className="text-[#3B82F6] hover:text-blue-300 font-medium">
                          {p.title}
                        </Link>
                      </td>
                      <td className="p-4 text-gray-300 capitalize">{p.sector}</td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium border ${STATUS_COLORS[p.status] || STATUS_COLORS.draft}`}>
                          {p.status?.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="inline-flex items-center">
                          <ScoreBadge score={p.composite_score} />
                          {p.composite_score != null && <ProposalShieldBadge proposalId={p.id} />}
                        </span>
                      </td>
                      <td className="p-4 text-gray-400 text-sm">
                        {p.submission_date ? new Date(p.submission_date).toLocaleDateString() : '—'}
                      </td>
                      <td className="p-4 flex gap-2 items-center">
                        <Link
                          to={`/proposals/${p.id}`}
                          className="text-[#3B82F6] hover:text-blue-300 text-sm font-medium px-3 py-1 rounded border border-[#3B82F6]/30 hover:bg-[#3B82F6]/10 transition"
                        >
                          View
                        </Link>
                        {(p.status === 'queued' || p.status === 'submitted') && (
                          evaluatingId === p.id ? (
                            <span className="flex items-center gap-2 text-blue-400 text-sm">
                              <span className="animate-spin inline-block w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full"></span>
                              AI is evaluating...
                            </span>
                          ) : (
                            <button
                              onClick={() => handleEvaluate(p.id)}
                              className="bg-[#3B82F6] hover:bg-blue-600 text-white text-sm font-medium px-3 py-1 rounded transition"
                            >
                              Evaluate
                            </button>
                          )
                        )}
                        {p.status === 'evaluating' && (
                          <span className="flex items-center gap-2 text-blue-400 text-sm opacity-70">
                            <span className="animate-spin inline-block w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full"></span>
                            Evaluating...
                          </span>
                        )}
                        {(p.status === 'evaluated' || p.status === 'approved' || p.status === 'rejected') && p.composite_score != null && (
                          <ScoreBadge score={p.composite_score} />
                        )}
                        {(p.status === 'requires_review' || p.status === 'requires_manual_review') && (
                          <span className="bg-orange-500/20 text-orange-400 border border-orange-500/30 px-3 py-1 rounded-full text-xs font-medium">
                            Needs Review
                          </span>
                        )}
                        {auditingId === p.id ? (
                          <span className="flex items-center gap-2 text-teal-400 text-sm">
                            <span className="animate-spin inline-block w-4 h-4 border-2 border-teal-400 border-t-transparent rounded-full"></span>
                            Running DESC compliance audit...
                          </span>
                        ) : p.has_audit === true ? (
                          <button
                            onClick={() => handleAudit(p.id)}
                            title="Click to re-audit"
                            className="bg-[#0D9488] text-white px-2 py-0.5 rounded-full text-xs font-bold hover:bg-teal-700 transition cursor-pointer"
                          >
                            {p.audit_score != null ? p.audit_score : 'Audited'}
                          </button>
                        ) : (
                          <button
                            onClick={() => handleAudit(p.id)}
                            className="bg-[#0D9488] hover:bg-teal-700 text-white text-sm font-medium px-3 py-1 rounded transition"
                          >
                            Audit
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center space-x-3 mt-6">
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

      {/* Document Ingestion Modal */}
      {showIngestModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-[#1E293B] rounded-2xl shadow-2xl w-full max-w-lg p-8 max-h-[90vh] overflow-y-auto border border-gray-700">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">
                {ingestStep === 'extracting' ? 'Processing Document...' : 'Review Extracted Details'}
              </h2>
              <button
                onClick={() => { setShowIngestModal(false); setIngestStep('upload'); setIngestData(null); }}
                className="text-gray-400 hover:text-white text-2xl"
              >
                ×
              </button>
            </div>

            {ingestStep === 'extracting' && (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#0D9488] mx-auto mb-4"></div>
                <p className="text-gray-300 text-lg mb-2">AI is reading your document...</p>
                <p className="text-gray-500 text-sm">Extracting proposal details from {ingestFile?.name}</p>
              </div>
            )}

            {ingestStep === 'review' && ingestData && (
              <div className="space-y-4">
                <p className="text-emerald-400 text-sm mb-4">Details extracted successfully. Review and edit before submitting.</p>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Title *</label>
                  <input
                    type="text"
                    value={ingestData.title}
                    onChange={(e) => handleIngestFieldChange('title', e.target.value)}
                    className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#0D9488]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Sector *</label>
                  <select
                    value={ingestData.sector}
                    onChange={(e) => handleIngestFieldChange('sector', e.target.value)}
                    className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#0D9488]"
                  >
                    {['AI/ML', 'FinTech', 'HealthTech', 'CleanTech', 'EdTech', 'Construction', 'Cybersecurity', 'Supply Chain', 'AgTech', 'SpaceTech', 'Retail'].map(s => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Technology Type *</label>
                  <input
                    type="text"
                    value={ingestData.technology_type}
                    onChange={(e) => handleIngestFieldChange('technology_type', e.target.value)}
                    className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#0D9488]"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Maturity Level</label>
                  <select
                    value={ingestData.maturity_level}
                    onChange={(e) => handleIngestFieldChange('maturity_level', e.target.value)}
                    className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#0D9488]"
                  >
                    <option value="concept">Concept</option>
                    <option value="prototype">Prototype</option>
                    <option value="mvp">MVP</option>
                    <option value="production">Production</option>
                    <option value="scaled">Scaled</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Language</label>
                  <div className="flex gap-4">
                    {[{ value: 'en', label: 'English' }, { value: 'ar', label: 'Arabic' }, { value: 'mixed', label: 'Mixed' }].map((opt) => (
                      <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="ingest_language"
                          value={opt.value}
                          checked={ingestData.language === opt.value}
                          onChange={(e) => handleIngestFieldChange('language', e.target.value)}
                          className="text-[#0D9488] focus:ring-[#0D9488]"
                        />
                        <span className="text-gray-300 text-sm">{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                  <textarea
                    rows={4}
                    value={ingestData.description}
                    onChange={(e) => handleIngestFieldChange('description', e.target.value)}
                    className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#0D9488] resize-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">Company Name</label>
                    <input
                      type="text"
                      value={ingestData.company_name}
                      onChange={(e) => handleIngestFieldChange('company_name', e.target.value)}
                      className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#0D9488]"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">Country</label>
                    <input
                      type="text"
                      value={ingestData.company_country}
                      onChange={(e) => handleIngestFieldChange('company_country', e.target.value)}
                      className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#0D9488]"
                    />
                  </div>
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    onClick={handleConfirmIngestion}
                    disabled={confirmingIngestion}
                    className="flex-1 bg-[#0D9488] hover:bg-teal-700 text-white font-semibold py-2.5 rounded-lg disabled:opacity-50 transition-colors"
                  >
                    {confirmingIngestion ? 'Creating Proposal...' : 'Confirm Submission'}
                  </button>
                  <button
                    type="button"
                    onClick={() => { setShowIngestModal(false); setIngestStep('upload'); setIngestData(null); }}
                    className="flex-1 bg-gray-600 hover:bg-gray-500 text-white font-semibold py-2.5 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Submit Proposal Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-[#1E293B] rounded-2xl shadow-2xl w-full max-w-lg p-8 max-h-[90vh] overflow-y-auto border border-gray-700">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Submit New Proposal</h2>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-white text-2xl">×</button>
            </div>
            <form onSubmit={handleSubmitProposal} className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Title *</label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#F59E0B]"
                  placeholder="Proposal title"
                />
              </div>

              {/* Sector */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Sector *</label>
                <select
                  required
                  value={formData.sector}
                  onChange={(e) => setFormData({ ...formData, sector: e.target.value })}
                  className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#F59E0B]"
                >
                  <option value="">Select sector...</option>
                  {businessGroups.map((bg) => (
                    <option key={bg.id} value={bg.name}>{bg.name}</option>
                  ))}
                  <option value="other">Other</option>
                </select>
              </div>

              {/* Technology Type */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Technology Type *</label>
                <input
                  type="text"
                  required
                  value={formData.technology_type}
                  onChange={(e) => setFormData({ ...formData, technology_type: e.target.value })}
                  className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#F59E0B]"
                  placeholder="e.g. Machine Learning, Blockchain, IoT"
                />
              </div>

              {/* Maturity Level */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Maturity Level *</label>
                <select
                  required
                  value={formData.maturity_level}
                  onChange={(e) => setFormData({ ...formData, maturity_level: e.target.value })}
                  className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#F59E0B]"
                >
                  <option value="">Select maturity level...</option>
                  <option value="concept">Concept</option>
                  <option value="prototype">Prototype</option>
                  <option value="mvp">MVP</option>
                  <option value="production">Production</option>
                  <option value="scaled">Scaled</option>
                </select>
              </div>

              {/* Language */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Language</label>
                <div className="flex gap-4">
                  {[{ value: 'en', label: 'English' }, { value: 'ar', label: 'Arabic' }, { value: 'mixed', label: 'Mixed' }].map((opt) => (
                    <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="language"
                        value={opt.value}
                        checked={formData.language === opt.value}
                        onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                        className="text-[#F59E0B] focus:ring-[#F59E0B]"
                      />
                      <span className="text-gray-300 text-sm">{opt.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                <textarea
                  rows={5}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full bg-[#0F172A] text-white border border-gray-700 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#F59E0B] resize-none"
                  placeholder="Describe your technology solution..."
                />
              </div>

              {/* Buttons */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={submitting}
                  className="flex-1 bg-[#F59E0B] hover:bg-[#D97706] text-black font-semibold py-2.5 rounded-lg disabled:opacity-50 transition-colors"
                >
                  {submitting ? 'Submitting...' : 'Submit Proposal'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 bg-gray-600 hover:bg-gray-500 text-white font-semibold py-2.5 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProposalsList;

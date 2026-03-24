import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const STATUS_COLORS = {
  queued: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  evaluating: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  evaluated: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  approved: 'bg-emerald-600/20 text-emerald-300 border-emerald-600/30',
  rejected: 'bg-red-500/20 text-red-400 border-red-500/30',
  requires_review: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
};

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
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${score}%`, background: `linear-gradient(90deg, ${color}88, ${color})` }}
        />
      </div>
      {reasoning && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-[#3B82F6] hover:text-blue-300 mt-1"
        >
          {expanded ? '▾ Hide reasoning' : '▸ Show reasoning'}
        </button>
      )}
      {expanded && reasoning && (
        <p className="text-sm text-gray-400 mt-1 pl-2 border-l-2 border-gray-600">{reasoning}</p>
      )}
    </div>
  );
};

const FILE_TYPE_ICONS = {
  pdf: { color: 'text-red-400 bg-red-500/20 border-red-500/30', label: 'PDF' },
  docx: { color: 'text-blue-400 bg-blue-500/20 border-blue-500/30', label: 'DOCX' },
  pptx: { color: 'text-orange-400 bg-orange-500/20 border-orange-500/30', label: 'PPTX' },
  xlsx: { color: 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30', label: 'XLSX' },
};

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const ALLOWED_EXTENSIONS = ['pdf', 'docx', 'pptx', 'xlsx'];

const DocumentsSection = ({ proposalId, userRole, onToast }) => {
  const [documents, setDocuments] = useState([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const fetchDocuments = useCallback(async () => {
    try {
      setDocsLoading(true);
      const { data } = await api.get(`/api/v1/proposals/${proposalId}/documents`);
      setDocuments(data.documents || []);
    } catch (err) {
      onToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setDocsLoading(false);
    }
  }, [proposalId, onToast]);

  useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

  const uploadFile = async (file) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !ALLOWED_EXTENSIONS.includes(ext)) {
      onToast({ message: `File type .${ext} not allowed. Use PDF, DOCX, PPTX, or XLSX.`, type: 'error' });
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      onToast({ message: 'File exceeds 20MB limit.', type: 'error' });
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploading(true);
      setUploadProgress(0);
      await api.post(`/api/v1/proposals/${proposalId}/documents`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) setUploadProgress(Math.round((e.loaded * 100) / e.total));
        },
      });
      onToast({ message: `${file.name} uploaded successfully!`, type: 'success' });
      await fetchDocuments();
    } catch (err) {
      onToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) uploadFile(file);
    e.target.value = '';
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) uploadFile(file);
  };

  const handleDelete = async (docId, fileName) => {
    if (!window.confirm(`Delete "${fileName}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/api/v1/proposals/documents/${docId}`);
      onToast({ message: `${fileName} deleted.`, type: 'success' });
      await fetchDocuments();
    } catch (err) {
      onToast({ message: getErrorMessage(err), type: 'error' });
    }
  };

  return (
    <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
      <h3 className="text-xl font-bold text-white mb-4">Documents</h3>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors mb-4 ${
          dragOver ? 'border-[#3B82F6] bg-[#3B82F6]/10' : 'border-gray-600 hover:border-gray-500'
        }`}
      >
        {uploading ? (
          <div>
            <p className="text-gray-300 mb-2">Uploading... {uploadProgress}%</p>
            <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden max-w-md mx-auto">
              <div
                className="h-full bg-[#3B82F6] rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        ) : (
          <div>
            <p className="text-gray-400 mb-2">Drag & drop a file here, or</p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="bg-[#3B82F6] hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              Upload Document
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.pptx,.xlsx"
              onChange={handleFileSelect}
              className="hidden"
            />
            <p className="text-gray-500 text-xs mt-2">PDF, DOCX, PPTX, XLSX up to 20MB</p>
          </div>
        )}
      </div>

      {/* Document list */}
      {docsLoading ? (
        <p className="text-gray-400 text-sm">Loading documents...</p>
      ) : documents.length === 0 ? (
        <p className="text-gray-500 text-sm">No documents uploaded yet.</p>
      ) : (
        <div className="space-y-2">
          {documents.map((doc) => {
            const typeInfo = FILE_TYPE_ICONS[doc.file_type] || FILE_TYPE_ICONS.pdf;
            return (
              <div key={doc.id} className="flex items-center justify-between bg-[#0F172A] rounded-lg p-3 border border-gray-700/50">
                <div className="flex items-center gap-3 min-w-0">
                  <span className={`px-2 py-1 rounded text-xs font-bold border ${typeInfo.color}`}>
                    {typeInfo.label}
                  </span>
                  <div className="min-w-0">
                    <p className="text-white text-sm font-medium truncate">{doc.file_name}</p>
                    <p className="text-gray-500 text-xs">
                      {formatFileSize(doc.file_size)} &middot; {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : ''}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {doc.download_url && (
                    <a
                      href={doc.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[#3B82F6] hover:text-blue-300 text-sm font-medium"
                    >
                      Download
                    </a>
                  )}
                  {userRole === 'admin' && (
                    <button
                      onClick={() => handleDelete(doc.id, doc.file_name)}
                      className="text-red-400 hover:text-red-300 text-sm font-medium"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

const STATUS_BADGE = (score) => {
  if (score == null) return { bg: 'bg-gray-500/20', text: 'text-gray-400', border: 'border-gray-500/30', label: 'N/A' };
  if (score > 80) return { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30', label: 'Compliant' };
  if (score >= 50) return { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30', label: 'Partial' };
  return { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/30', label: 'Non-Compliant' };
};

const CONTROL_STATUS_STYLE = {
  pass: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  fail: 'bg-red-500/20 text-red-400 border-red-500/30',
  warning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
};

const ComplianceAuditSection = ({ proposalId, userRole, onToast, initialAudit }) => {
  const [auditResult, setAuditResult] = useState(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [existingAudit, setExistingAudit] = useState(initialAudit || null);
  const [expandedFramework, setExpandedFramework] = useState(null);
  const [loadingExisting, setLoadingExisting] = useState(!initialAudit);

  useEffect(() => {
    if (initialAudit) {
      setExistingAudit(initialAudit);
      setLoadingExisting(false);
    } else {
      fetchExistingAudit();
    }
  }, [proposalId, initialAudit]);

  const fetchExistingAudit = async () => {
    try {
      setLoadingExisting(true);
      const { data } = await api.get(`/api/v1/compliance-audit-results?proposal_id=${proposalId}&page=1&page_size=1`);
      const audits = data.audits || [];
      const match = audits.find(a => a.proposal_id === proposalId);
      if (match) {
        const { data: detail } = await api.get(`/api/v1/compliance-audit-results/${match.id}`);
        setExistingAudit(detail);
      }
    } catch {
      // Non-critical
    } finally {
      setLoadingExisting(false);
    }
  };

  const handleRunAudit = async () => {
    try {
      setAuditLoading(true);
      const { data } = await api.post(`/api/v1/proposals/${proposalId}/audit`);
      setAuditResult(data);
      setExistingAudit(null);
      onToast({ message: 'DESC compliance audit completed!', type: 'success' });
    } catch (err) {
      onToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setAuditLoading(false);
    }
  };

  const audit = auditResult || existingAudit;
  const canRunAudit = userRole === 'admin' || userRole === 'compliance_officer';
  const badge = STATUS_BADGE(audit?.overall_score);

  return (
    <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-white">DESC Compliance Audit</h3>
        {canRunAudit && (
          <button
            onClick={handleRunAudit}
            disabled={auditLoading}
            className="bg-teal-500 hover:bg-teal-600 text-white px-5 py-2 rounded-lg font-semibold disabled:opacity-50 transition-colors"
          >
            {auditLoading ? (
              <span className="flex items-center gap-2">
                <span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
                Running DESC compliance audit...
              </span>
            ) : audit ? 'Re-run Compliance Audit' : 'Run Compliance Audit'}
          </button>
        )}
      </div>

      {loadingExisting && !audit && (
        <p className="text-gray-400 text-sm">Checking for existing audits...</p>
      )}

      {!audit && !loadingExisting && (
        <p className="text-gray-500 text-sm">No compliance audit has been run on this proposal yet.</p>
      )}

      {audit && (
        <div className="space-y-6">
          {/* Overall Score Badge */}
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div
                className="text-5xl font-black"
                style={{
                  color: (audit.overall_score || 0) > 80 ? '#10B981' : (audit.overall_score || 0) >= 50 ? '#F59E0B' : '#EF4444'
                }}
              >
                {audit.overall_score ?? '—'}
              </div>
              <p className="text-gray-400 text-xs mt-1">Overall Score</p>
            </div>
            <div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${badge.bg} ${badge.text} ${badge.border}`}>
                {audit.overall_status?.replace(/_/g, ' ') || badge.label}
              </span>
            </div>
          </div>

          {/* Quick Compliance Checklist */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-[#0F172A] rounded-lg p-3 border border-gray-700/50 text-center">
              <span className="text-2xl">{audit.isr_v3_compliance ? '✅' : '❌'}</span>
              <p className="text-gray-300 text-sm mt-1 font-medium">ISR V3</p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-3 border border-gray-700/50 text-center">
              <span className="text-2xl">{audit.ai_security_policy_compliance ? '✅' : '❌'}</span>
              <p className="text-gray-300 text-sm mt-1 font-medium">AI Security</p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-3 border border-gray-700/50 text-center">
              <span className="text-2xl">{audit.csp_standards_compliance ? '✅' : '❌'}</span>
              <p className="text-gray-300 text-sm mt-1 font-medium">CSP Standards</p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-3 border border-gray-700/50 text-center">
              <span className="text-2xl">{audit.data_residency_verified ? '✅' : '❌'}</span>
              <p className="text-gray-300 text-sm mt-1 font-medium">Data Residency</p>
            </div>
          </div>

          {/* Summary */}
          {audit.summary && (
            <p className="text-gray-300 text-sm leading-relaxed border-l-2 border-teal-500 pl-4">{audit.summary}</p>
          )}

          {/* Framework Accordions */}
          {(audit.frameworks || []).map((fw, idx) => (
            <div key={idx} className="bg-[#0F172A] rounded-lg border border-gray-700/50">
              <button
                onClick={() => setExpandedFramework(expandedFramework === idx ? null : idx)}
                className="w-full flex items-center justify-between p-4 text-left"
              >
                <span className="text-white font-semibold">{fw.name}</span>
                <div className="flex items-center gap-2">
                  {(fw.controls || []).map((c, ci) => (
                    <span key={ci} className={`w-3 h-3 rounded-full ${c.status === 'pass' ? 'bg-emerald-400' : c.status === 'fail' ? 'bg-red-400' : 'bg-amber-400'}`} />
                  ))}
                  <span className="text-gray-400 ml-2">{expandedFramework === idx ? '▾' : '▸'}</span>
                </div>
              </button>
              {expandedFramework === idx && (
                <div className="px-4 pb-4 space-y-3">
                  {(fw.controls || []).map((ctrl, ci) => (
                    <div key={ci} className="bg-[#1E293B] rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-gray-300 text-sm font-medium">
                          <span className="text-gray-500 font-mono text-xs mr-2">{ctrl.control_id}</span>
                          {ctrl.control_name}
                        </span>
                        <span className={`px-2 py-0.5 rounded text-xs font-bold border ${CONTROL_STATUS_STYLE[ctrl.status] || CONTROL_STATUS_STYLE.warning}`}>
                          {ctrl.status?.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-gray-400 text-xs mt-1">{ctrl.finding}</p>
                      {ctrl.recommendation && (
                        <p className="text-teal-400 text-xs mt-1">Rec: {ctrl.recommendation}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Key Findings */}
          {audit.findings && (
            <div className="bg-[#0F172A] rounded-lg p-4 border border-gray-700/50">
              <h4 className="text-gray-300 text-sm font-semibold mb-2">Key Findings</h4>
              {Array.isArray(audit.findings) ? (
                <ul className="space-y-1">
                  {audit.findings.map((f, i) => (
                    <li key={i} className="text-gray-400 text-sm">• {typeof f === 'string' ? f : f.finding || f.description || JSON.stringify(f)}</li>
                  ))}
                </ul>
              ) : typeof audit.findings === 'object' ? (
                <p className="text-gray-400 text-sm">{JSON.stringify(audit.findings, null, 2)}</p>
              ) : (
                <p className="text-gray-400 text-sm">{audit.findings}</p>
              )}
            </div>
          )}

          {/* Data Residency & Vendor Certification */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#0F172A] rounded-lg p-4 border border-gray-700/50">
              <h4 className="text-gray-400 text-sm mb-2">Data Residency</h4>
              <span className={`px-2 py-1 rounded text-xs font-bold border ${audit.data_residency_verified || audit.data_residency?.compliant ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30'}`}>
                {audit.data_residency_verified || audit.data_residency?.compliant ? 'UAE Compliant' : 'Not Verified'}
              </span>
              {audit.data_residency?.finding && (
                <p className="text-gray-400 text-xs mt-2">{audit.data_residency.finding}</p>
              )}
            </div>
            <div className="bg-[#0F172A] rounded-lg p-4 border border-gray-700/50">
              <h4 className="text-gray-400 text-sm mb-2">Vendor Certification</h4>
              <span className={`px-2 py-1 rounded text-xs font-bold border ${audit.vendor_certification?.desc_approved ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border-amber-500/30'}`}>
                {audit.vendor_certification?.desc_approved ? 'DESC Approved' : 'Not DESC Approved'}
              </span>
              {audit.vendor_certification?.finding && (
                <p className="text-gray-400 text-xs mt-2">{audit.vendor_certification.finding}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const ROLE_BADGE_STYLES = {
  admin: 'bg-red-500/20 text-red-400 border-red-500/30',
  analyst: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  compliance_officer: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  vendor: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  executive: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  business_group_lead: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
};

const ROLE_LABELS = {
  admin: 'Admin',
  analyst: 'Analyst',
  compliance_officer: 'Compliance',
  vendor: 'Vendor',
  executive: 'Executive',
  business_group_lead: 'BG Lead',
};

const formatRelativeTime = (dateString) => {
  if (!dateString) return '';
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now - date;
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffSec < 60) return 'just now';
  if (diffMin < 60) return `${diffMin} minute${diffMin !== 1 ? 's' : ''} ago`;
  if (diffHr < 24) return `${diffHr} hour${diffHr !== 1 ? 's' : ''} ago`;
  if (diffDay === 1) return 'yesterday';
  if (diffDay < 30) return `${diffDay} days ago`;
  return date.toLocaleDateString();
};

const CommentsSection = ({ proposalId, userRole, currentUserId, onToast }) => {
  const [comments, setComments] = useState([]);
  const [commentsLoading, setCommentsLoading] = useState(true);
  const [commentText, setCommentText] = useState('');
  const [posting, setPosting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const fetchComments = useCallback(async () => {
    try {
      setCommentsLoading(true);
      const { data } = await api.get(`/api/v1/proposals/${proposalId}/comments`);
      setComments(data.comments || []);
    } catch (err) {
      onToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setCommentsLoading(false);
    }
  }, [proposalId, onToast]);

  useEffect(() => { fetchComments(); }, [fetchComments]);

  const handlePost = async () => {
    if (!commentText.trim()) return;
    try {
      setPosting(true);
      const { data } = await api.post(`/api/v1/proposals/${proposalId}/comments`, {
        content: commentText.trim(),
      });
      setComments((prev) => [data, ...prev]);
      setCommentText('');
      onToast({ message: 'Comment posted', type: 'success' });
    } catch (err) {
      onToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setPosting(false);
    }
  };

  const handleDelete = async (commentId) => {
    if (!window.confirm('Delete this comment?')) return;
    try {
      setDeletingId(commentId);
      await api.delete(`/api/v1/proposals/${proposalId}/comments/${commentId}`);
      setComments((prev) => prev.filter((c) => c.id !== commentId));
      onToast({ message: 'Comment deleted', type: 'success' });
    } catch (err) {
      onToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setDeletingId(null);
    }
  };

  const canDelete = (comment) => {
    return String(comment.user_id) === String(currentUserId) || userRole === 'admin';
  };

  return (
    <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
      <h3 className="text-xl font-bold text-white mb-4">Comments</h3>

      {/* Comment Input */}
      <div className="mb-6">
        <textarea
          value={commentText}
          onChange={(e) => setCommentText(e.target.value)}
          placeholder="Share your assessment of this proposal..."
          rows={3}
          maxLength={2000}
          className="w-full bg-[#0F172A] text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none placeholder-gray-500"
        />
        <div className="flex items-center justify-between mt-2">
          <span className="text-gray-500 text-xs">{commentText.length}/2000</span>
          <button
            onClick={handlePost}
            disabled={posting || !commentText.trim()}
            className="bg-[#0D9488] hover:bg-teal-700 text-white px-5 py-2 rounded-lg font-semibold text-sm disabled:opacity-50 transition-colors"
          >
            {posting ? 'Posting...' : 'Post Comment'}
          </button>
        </div>
      </div>

      {/* Separator */}
      <div className="border-t border-gray-700 mb-4" />

      {/* Comment List */}
      {commentsLoading ? (
        <p className="text-gray-400 text-sm">Loading comments...</p>
      ) : comments.length === 0 ? (
        <p className="text-gray-500 text-sm">No comments yet. Be the first to share your assessment.</p>
      ) : (
        <div className="space-y-3">
          {comments.map((c) => (
            <div key={c.id} className="bg-[#0F172A] rounded-lg p-4 border border-gray-700/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-white font-medium text-sm">{c.user_name || 'Unknown'}</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${ROLE_BADGE_STYLES[c.user_role] || ROLE_BADGE_STYLES.vendor}`}>
                    {ROLE_LABELS[c.user_role] || c.user_role}
                  </span>
                  <span className="text-gray-500 text-xs">{formatRelativeTime(c.created_at)}</span>
                </div>
                {canDelete(c) && (
                  <button
                    onClick={() => handleDelete(c.id)}
                    disabled={deletingId === c.id}
                    className="text-red-400 hover:text-red-300 text-xs font-medium disabled:opacity-50"
                  >
                    {deletingId === c.id ? 'Deleting...' : 'Delete'}
                  </button>
                )}
              </div>
              <p className="text-gray-300 text-sm whitespace-pre-wrap">{c.comment_text}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const ProposalDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [proposal, setProposal] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [showArabic, setShowArabic] = useState(false);
  const [toast, setToast] = useState(null);
  const [userRole, setUserRole] = useState('');
  const [currentUserId, setCurrentUserId] = useState('');

  useEffect(() => { fetchProposal(); }, [id]);

  useEffect(() => {
    api.get('/api/v1/users/me').then(({ data }) => {
      setUserRole(data.role || '');
      setCurrentUserId(data.id || '');
    }).catch(() => {});
  }, []);

  const fetchProposal = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/proposals/${id}`);
      setProposal(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    if (!window.confirm('Run AI evaluation on this proposal?')) return;
    try {
      setActionLoading(true);
      await api.post(`/api/v1/proposals/${id}/evaluate`);
      setToast({ message: 'AI evaluation completed!', type: 'success' });
      await fetchProposal();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setActionLoading(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      setActionLoading(true);
      await api.patch(`/api/v1/proposals/${id}/status`, { status: newStatus });
      setToast({ message: `Status updated to ${newStatus}`, type: 'success' });
      await fetchProposal();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#3B82F6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading proposal...</p>
        </div>
      </div>
    );
  }

  if (error && !proposal) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-red-400 text-lg">{error}</div>
      </div>
    );
  }

  const evaluation = proposal?.evaluation;
  const aiCost = proposal?.ai_cost;

  return (
    <div className="min-h-screen bg-[#0F172A] p-8">
      {toast && (
        <div className={`fixed top-6 right-6 z-50 ${toast.type === 'success' ? 'bg-emerald-600' : 'bg-red-600'} text-white px-6 py-3 rounded-lg shadow-2xl`}>
          {toast.message}
          <button onClick={() => setToast(null)} className="ml-3 opacity-70 hover:opacity-100">×</button>
        </div>
      )}

      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-3xl font-bold text-white">{proposal.title}</h1>
          <button onClick={() => navigate('/proposals')} className="text-[#3B82F6] hover:text-blue-300">
            ← Back to Proposals
          </button>
        </div>

        {/* Manual Review Banner */}
        {proposal.requires_manual_review && (
          <div className="mb-6 p-4 bg-orange-500/10 border border-orange-500/30 rounded-lg flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="text-orange-400 font-semibold">Flagged for Manual Review</p>
              <p className="text-orange-300 text-sm">{evaluation?.review_reason || 'This proposal requires human review before proceeding.'}</p>
            </div>
          </div>
        )}

        {/* Proposal Info */}
        <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            <div>
              <span className="text-gray-500 text-sm">Status</span>
              <div className="mt-1">
                <span className={`px-3 py-1 rounded-full text-xs font-medium border ${STATUS_COLORS[proposal.status] || 'bg-gray-500/20 text-gray-400'}`}>
                  {proposal.status?.replace(/_/g, ' ')}
                </span>
              </div>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Sector</span>
              <p className="text-white font-medium mt-1 capitalize">{proposal.sector}</p>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Technology Type</span>
              <p className="text-white font-medium mt-1">{proposal.technology_type}</p>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Maturity Level</span>
              <p className="text-white font-medium mt-1 capitalize">{proposal.maturity_level}</p>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Language</span>
              <p className="text-white font-medium mt-1">{proposal.language === 'en' ? 'English' : proposal.language === 'ar' ? 'Arabic' : 'Mixed'}</p>
            </div>
            <div>
              <span className="text-gray-500 text-sm">Submitted</span>
              <p className="text-white font-medium mt-1">
                {proposal.submission_date ? new Date(proposal.submission_date).toLocaleDateString() : '—'}
              </p>
            </div>
          </div>
          {proposal.description && (
            <div className="mt-6 pt-4 border-t border-gray-700">
              <span className="text-gray-500 text-sm">Description</span>
              <p className="text-gray-300 mt-1 whitespace-pre-wrap">{proposal.description}</p>
            </div>
          )}
          {proposal.business_group && (
            <div className="mt-4 pt-4 border-t border-gray-700">
              <span className="text-gray-500 text-sm">Business Group</span>
              <p className="text-white font-medium mt-1">{proposal.business_group.name} — {proposal.business_group.chamber}</p>
            </div>
          )}
        </div>

        {/* Documents */}
        <DocumentsSection proposalId={id} userRole={userRole} onToast={setToast} />

        {/* Evaluation Scores */}
        {(proposal.composite_score != null || evaluation) && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <h3 className="text-xl font-bold text-white mb-6">AI Evaluation Scores</h3>

            {/* Composite Score - Large */}
            <div className="flex items-center justify-center mb-8">
              <div className="text-center">
                <div
                  className="text-6xl font-black"
                  style={{
                    color: (proposal.composite_score || 0) > 70 ? '#10B981' : (proposal.composite_score || 0) >= 40 ? '#F59E0B' : '#EF4444'
                  }}
                >
                  {proposal.composite_score?.toFixed(1) || '—'}
                </div>
                <p className="text-gray-400 text-sm mt-1">Composite Score</p>
              </div>
            </div>

            {/* Score Bars */}
            <ScoreBar
              label="Relevance"
              score={evaluation?.relevance_score ?? proposal.relevance_score}
              reasoning={evaluation?.relevance_reasoning}
            />
            <ScoreBar
              label="Feasibility"
              score={evaluation?.feasibility_score ?? proposal.feasibility_score}
              reasoning={evaluation?.feasibility_reasoning}
            />
            <ScoreBar
              label="Sector Alignment"
              score={evaluation?.sector_alignment_score ?? proposal.sector_alignment_score}
              reasoning={evaluation?.sector_reasoning}
            />
            <ScoreBar
              label="Compliance"
              score={evaluation?.compliance_score ?? proposal.compliance_score}
              reasoning={evaluation?.compliance_reasoning}
            />
          </div>
        )}

        {/* Executive Summary */}
        {evaluation && (evaluation.summary_en || evaluation.summary_ar) && (
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

        {/* DESC Compliance Audit */}
        <ComplianceAuditSection proposalId={id} userRole={userRole} onToast={setToast} initialAudit={proposal?.compliance_audit} />

        {/* AI Cost / ΣI */}
        {aiCost && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <h3 className="text-xl font-bold text-white mb-4">ΣI — Evaluation Cost</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-[#3B82F6]">{(aiCost.prompt_tokens + aiCost.completion_tokens).toLocaleString()}</p>
                <p className="text-gray-500 text-xs mt-1">Total Tokens</p>
              </div>
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-[#F59E0B]">${parseFloat(aiCost.cost_usd).toFixed(4)}</p>
                <p className="text-gray-500 text-xs mt-1">Cost (USD)</p>
              </div>
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-[#10B981]">{parseFloat(aiCost.energy_kwh).toFixed(6)}</p>
                <p className="text-gray-500 text-xs mt-1">Energy (kWh)</p>
              </div>
              <div className="bg-[#0F172A] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-gray-300">{aiCost.latency_ms}ms</p>
                <p className="text-gray-500 text-xs mt-1">Latency</p>
              </div>
            </div>
          </div>
        )}

        {/* Comments */}
        <CommentsSection proposalId={id} userRole={userRole} currentUserId={currentUserId} onToast={setToast} />

        {/* Action Buttons */}
        <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-700/50">
          <div className="flex gap-3 flex-wrap">
            {(proposal.status === 'queued' || proposal.status === 'requires_review') && (
              <button
                onClick={handleEvaluate}
                disabled={actionLoading}
                className="bg-[#3B82F6] hover:bg-blue-600 text-white px-6 py-2.5 rounded-lg font-semibold disabled:opacity-50 transition-colors"
              >
                {actionLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="animate-pulse">🧠</span> AI is evaluating... ~15s
                  </span>
                ) : proposal.status === 'requires_review' ? 'Re-evaluate' : 'Run AI Evaluation'}
              </button>
            )}
            <button
              onClick={() => handleStatusChange('approved')}
              disabled={actionLoading}
              className="bg-[#10B981] hover:bg-emerald-600 text-white px-6 py-2.5 rounded-lg font-semibold disabled:opacity-50 transition-colors"
            >
              Approve
            </button>
            <button
              onClick={() => handleStatusChange('rejected')}
              disabled={actionLoading}
              className="bg-[#EF4444] hover:bg-red-600 text-white px-6 py-2.5 rounded-lg font-semibold disabled:opacity-50 transition-colors"
            >
              Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProposalDetail;

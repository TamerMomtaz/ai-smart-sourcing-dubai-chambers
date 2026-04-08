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
  on_hold: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  revision_requested: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  conditional: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
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
              <div key={doc.id} className="flex items-center justify-between bg-[var(--color-table-header-bg)] rounded-lg p-3 border border-gray-700/50">
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
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-white px-5 py-2 rounded-lg font-semibold disabled:opacity-50 transition-colors"
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
            <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 border border-gray-700/50 text-center">
              <span className="text-2xl">{audit.isr_v3_compliance ? '✅' : '❌'}</span>
              <p className="text-gray-300 text-sm mt-1 font-medium">DESC ISR V3 Controls</p>
            </div>
            <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 border border-gray-700/50 text-center">
              <span className="text-2xl">{audit.ai_security_policy_compliance ? '✅' : '❌'}</span>
              <p className="text-gray-300 text-sm mt-1 font-medium">DESC AI Security Policy (5-Phase Lifecycle)</p>
            </div>
            <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 border border-gray-700/50 text-center">
              <span className="text-2xl">{audit.csp_standards_compliance ? '✅' : '❌'}</span>
              <p className="text-gray-300 text-sm mt-1 font-medium">DESC CSP Standards (ISO/IEC 27001, ISO/IEC 27017, CSA CCM v4.0.5)</p>
            </div>
            <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 border border-gray-700/50 text-center">
              <span className="text-2xl">{audit.data_residency_verified ? '✅' : '❌'}</span>
              <p className="text-gray-300 text-sm mt-1 font-medium">Data Residency</p>
            </div>
          </div>

          {/* Summary */}
          {audit.summary && (
            <p className="text-gray-300 text-sm leading-relaxed border-l-2 border-[var(--color-accent)] pl-4">{audit.summary}</p>
          )}

          {/* Framework Accordions */}
          {(audit.frameworks || []).map((fw, idx) => (
            <div key={idx} className="bg-[var(--color-table-header-bg)] rounded-lg border border-gray-700/50">
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
                        <p className="text-[var(--color-accent)] text-xs mt-1">Rec: {ctrl.recommendation}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}

          {/* Key Findings */}
          {audit.findings && (
            <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4 border border-gray-700/50">
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
            <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4 border border-gray-700/50">
              <h4 className="text-gray-400 text-sm mb-2">Data Residency</h4>
              <span className={`px-2 py-1 rounded text-xs font-bold border ${audit.data_residency_verified || audit.data_residency?.compliant ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' : 'bg-red-500/20 text-red-400 border-red-500/30'}`}>
                {audit.data_residency_verified || audit.data_residency?.compliant ? 'UAE Compliant' : 'Not Verified'}
              </span>
              {audit.data_residency?.finding && (
                <p className="text-gray-400 text-xs mt-2">{audit.data_residency.finding}</p>
              )}
            </div>
            <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4 border border-gray-700/50">
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

// ── Stage-Gate Decision Panel ──────────────────────────────────────────────
const GATE_STAGES = [
  { key: 'discovery',       label: 'Discovery',  icon: '\uD83D\uDD0D' },
  { key: 'scoping',         label: 'Scoping',    icon: '\uD83D\uDCCB' },
  { key: 'evaluation',      label: 'Evaluation', icon: '\u2696\uFE0F' },
  { key: 'pilot_approval',  label: 'Pilot',      icon: '\uD83D\uDE80' },
  { key: 'procurement',     label: 'Procurement', icon: '\uD83D\uDCE6' },
];

const DECISION_COLORS = {
  go:             { bg: 'bg-emerald-600 hover:bg-emerald-700', label: 'GO' },
  kill:           { bg: 'bg-red-600 hover:bg-red-700',         label: 'KILL' },
  hold:           { bg: 'bg-amber-500 hover:bg-amber-600',     label: 'HOLD' },
  recycle:        { bg: 'bg-blue-600 hover:bg-blue-700',       label: 'RECYCLE' },
  conditional_go: { bg: 'bg-orange-500 hover:bg-orange-600',   label: 'CONDITIONAL GO' },
};

const DECISION_BADGE_STYLE = {
  go:             'bg-emerald-500/20 text-emerald-400 border-emerald-500/40',
  kill:           'bg-red-500/20 text-red-400 border-red-500/40',
  hold:           'bg-amber-500/20 text-amber-400 border-amber-500/40',
  recycle:        'bg-blue-500/20 text-blue-400 border-blue-500/40',
  conditional_go: 'bg-orange-500/20 text-orange-400 border-orange-500/40',
};

const GateDecisionSection = ({ proposalId, userRole, evaluation, onToast, onRefresh }) => {
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [selectedDecision, setSelectedDecision] = useState('');
  const [decisionReason, setDecisionReason] = useState('');
  const [conditions, setConditions] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const canDecide = userRole === 'admin' || userRole === 'analyst';

  const fetchHistory = useCallback(async () => {
    try {
      setHistoryLoading(true);
      const { data } = await api.get(`/api/v1/proposals/${proposalId}/gate-history`);
      setHistory(data.gate_decisions || []);
    } catch {
      // non-critical
    } finally {
      setHistoryLoading(false);
    }
  }, [proposalId]);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  // Derive current gate from history
  const completedGates = {};
  history.forEach((d) => { completedGates[d.gate_name] = d; });

  let currentGateIdx = 0;
  for (let i = 0; i < GATE_STAGES.length; i++) {
    const gd = completedGates[GATE_STAGES[i].key];
    if (gd && gd.decision === 'go') {
      currentGateIdx = i + 1;
    } else if (gd && gd.decision === 'conditional_go') {
      currentGateIdx = i + 1;
    } else if (gd) {
      // kill/hold/recycle — stay at this gate
      currentGateIdx = i;
      break;
    } else {
      currentGateIdx = i;
      break;
    }
  }
  if (currentGateIdx >= GATE_STAGES.length) currentGateIdx = GATE_STAGES.length - 1;
  const currentGate = GATE_STAGES[currentGateIdx].key;

  const handleSubmit = async () => {
    if (!selectedDecision || !decisionReason.trim()) return;
    try {
      setSubmitting(true);
      await api.post(`/api/v1/proposals/${proposalId}/gate-decision`, {
        gate_name: currentGate,
        decision: selectedDecision,
        decision_reason: decisionReason.trim(),
        conditions: conditions.trim() || null,
      });
      onToast({ message: `Gate decision recorded: ${DECISION_COLORS[selectedDecision]?.label}`, type: 'success' });
      setSelectedDecision('');
      setDecisionReason('');
      setConditions('');
      await fetchHistory();
      if (onRefresh) onRefresh();
    } catch (err) {
      onToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
      <h3 className="text-xl font-bold text-white mb-6">Stage-Gate Decision</h3>

      {/* Pipeline Visual */}
      <div className="flex items-center justify-between mb-8 overflow-x-auto pb-2">
        {GATE_STAGES.map((stage, idx) => {
          const gd = completedGates[stage.key];
          const isCurrent = idx === currentGateIdx && !(gd && (gd.decision === 'kill'));
          const isCompleted = gd && (gd.decision === 'go' || gd.decision === 'conditional_go');
          const isKilled = gd && gd.decision === 'kill';
          const isHeld = gd && gd.decision === 'hold';
          const isRecycled = gd && gd.decision === 'recycle';
          const isFuture = idx > currentGateIdx;

          let circleClass = 'border-2 border-gray-600 bg-transparent';
          if (isCompleted) circleClass = 'border-2 border-emerald-400 bg-emerald-500/30';
          if (isKilled) circleClass = 'border-2 border-red-400 bg-red-500/30';
          if (isHeld) circleClass = 'border-2 border-amber-400 bg-amber-500/30';
          if (isRecycled) circleClass = 'border-2 border-blue-400 bg-blue-500/30';
          if (isCurrent && !gd) circleClass = 'border-2 border-teal-400 bg-teal-500/20 animate-pulse';

          let badge = null;
          if (gd) {
            const bs = DECISION_BADGE_STYLE[gd.decision] || '';
            badge = (
              <span className={`absolute -top-6 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded text-[10px] font-bold border whitespace-nowrap ${bs}`}>
                {DECISION_COLORS[gd.decision]?.label || gd.decision}
              </span>
            );
          }

          return (
            <div key={stage.key} className="flex items-center flex-1 min-w-0">
              <div className="flex flex-col items-center relative min-w-[60px]">
                {badge}
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${circleClass}`}>
                  {isCompleted ? '\u2713' : isKilled ? '\u2717' : isHeld ? '\u23F8' : isRecycled ? '\u21BA' : stage.icon}
                </div>
                <span className={`text-xs mt-1 font-medium ${isCurrent ? 'text-teal-400' : isFuture ? 'text-gray-600' : 'text-gray-400'}`}>
                  {stage.label}
                </span>
              </div>
              {idx < GATE_STAGES.length - 1 && (
                <div className={`flex-1 h-0.5 mx-1 ${isCompleted ? 'bg-emerald-500/50' : 'bg-gray-700'}`} />
              )}
            </div>
          );
        })}
      </div>

      {/* AI Recommendation Summary */}
      {evaluation && (evaluation.summary_en || evaluation.composite_score != null) && (
        <div className="bg-[var(--color-table-header-bg)] rounded-lg p-4 mb-6 border border-gray-700/50">
          <h4 className="text-gray-400 text-sm font-semibold mb-2">AI Recommendation</h4>
          {evaluation.composite_score != null && (
            <p className="text-white text-sm mb-1">
              Composite Score: <span className="font-bold" style={{
                color: evaluation.composite_score > 70 ? '#10B981' : evaluation.composite_score >= 40 ? '#F59E0B' : '#EF4444'
              }}>{typeof evaluation.composite_score === 'number' ? evaluation.composite_score.toFixed(1) : evaluation.composite_score}</span>
            </p>
          )}
          {evaluation.summary_en && (
            <p className="text-gray-300 text-sm leading-relaxed">{evaluation.summary_en}</p>
          )}
        </div>
      )}

      {/* Decision Form (admin/analyst only) */}
      {canDecide && (
        <div className="space-y-4">
          <div>
            <label className="text-gray-400 text-sm font-medium block mb-2">
              Current Gate: <span className="text-teal-400 font-semibold">{GATE_STAGES[currentGateIdx]?.label}</span>
            </label>

            {/* Decision Buttons */}
            <div className="flex flex-wrap gap-2">
              {Object.entries(DECISION_COLORS).map(([key, cfg]) => (
                <button
                  key={key}
                  onClick={() => setSelectedDecision(key)}
                  className={`px-4 py-2 rounded-lg text-white text-sm font-bold transition-all ${cfg.bg} ${
                    selectedDecision === key ? 'ring-2 ring-white ring-offset-2 ring-offset-[#1E293B]' : 'opacity-70 hover:opacity-100'
                  }`}
                >
                  {cfg.label}
                </button>
              ))}
            </div>
          </div>

          {/* Decision Reason */}
          <div>
            <label className="text-gray-400 text-sm font-medium block mb-1">Decision Reason *</label>
            <textarea
              value={decisionReason}
              onChange={(e) => setDecisionReason(e.target.value)}
              placeholder="Provide rationale for this gate decision..."
              rows={3}
              className="w-full bg-[var(--color-table-header-bg)] text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none placeholder-gray-500"
            />
          </div>

          {/* Conditions (conditional_go) */}
          {selectedDecision === 'conditional_go' && (
            <div>
              <label className="text-gray-400 text-sm font-medium block mb-1">Conditions *</label>
              <textarea
                value={conditions}
                onChange={(e) => setConditions(e.target.value)}
                placeholder="Specify conditions that must be met..."
                rows={2}
                className="w-full bg-[var(--color-table-header-bg)] text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-orange-500 resize-none placeholder-gray-500"
              />
            </div>
          )}

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={submitting || !selectedDecision || !decisionReason.trim() || (selectedDecision === 'conditional_go' && !conditions.trim())}
            className="bg-teal-600 hover:bg-teal-700 text-white px-6 py-2.5 rounded-lg font-semibold disabled:opacity-50 transition-colors"
          >
            {submitting ? 'Recording...' : 'Record Decision'}
          </button>
        </div>
      )}

      {/* History Timeline */}
      {historyLoading ? (
        <p className="text-gray-400 text-sm mt-6">Loading gate history...</p>
      ) : history.length > 0 && (
        <div className="mt-8">
          <h4 className="text-gray-400 text-sm font-semibold mb-4">Decision History</h4>
          <div className="space-y-3 border-l-2 border-gray-700 pl-4 ml-2">
            {history.map((d) => {
              const bs = DECISION_BADGE_STYLE[d.decision] || '';
              const stageLabel = GATE_STAGES.find(s => s.key === d.gate_name)?.label || d.gate_name;
              return (
                <div key={d.id} className="relative">
                  <div className="absolute -left-[22px] top-1 w-3 h-3 rounded-full bg-gray-600 border-2 border-gray-800" />
                  <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 border border-gray-700/50">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-white text-sm font-semibold">{stageLabel}</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-bold border ${bs}`}>
                        {DECISION_COLORS[d.decision]?.label || d.decision}
                      </span>
                      <span className="text-gray-500 text-xs ml-auto">
                        {d.created_at ? new Date(d.created_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                    {d.decision_reason && (
                      <p className="text-gray-300 text-sm">{d.decision_reason}</p>
                    )}
                    {d.conditions && (
                      <p className="text-orange-400 text-xs mt-1">Conditions: {d.conditions}</p>
                    )}
                    {d.ai_score != null && (
                      <p className="text-gray-500 text-xs mt-1">AI Score: {d.ai_score}</p>
                    )}
                  </div>
                </div>
              );
            })}
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
  business_group_lead: 'bg-accent-10 text-[var(--color-accent)] border-accent-30',
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
          className="w-full bg-[var(--color-table-header-bg)] text-white border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)] resize-none placeholder-gray-500"
        />
        <div className="flex items-center justify-between mt-2">
          <span className="text-gray-500 text-xs">{commentText.length}/2000</span>
          <button
            onClick={handlePost}
            disabled={posting || !commentText.trim()}
            className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white px-5 py-2 rounded-lg font-semibold text-sm disabled:opacity-50 transition-colors"
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
            <div key={c.id} className="bg-[var(--color-table-header-bg)] rounded-lg p-4 border border-gray-700/50">
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
  const [vendorReputation, setVendorReputation] = useState(null);
  const [sourcingCase, setSourcingCase] = useState(null);
  const [gateLoading, setGateLoading] = useState(false);

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
      // Fetch sourcing case info if linked
      if (data.sourcing_case_id) {
        try {
          const { data: sc } = await api.get(`/api/v1/sourcing-cases/${data.sourcing_case_id}`);
          setSourcingCase(sc);
        } catch {
          // Non-critical
        }
      }
      // Fetch vendor reputation if submitter_id exists
      if (data.submitter_id) {
        try {
          const { data: rep } = await api.get(`/api/v1/vendors/${data.submitter_id}/reputation`);
          setVendorReputation(rep);
        } catch {
          // Non-critical
        }
      }
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

  const handleRunGate = async () => {
    try {
      setGateLoading(true);
      await api.post(`/api/v1/proposals/${id}/compliance-gate`);
      setToast({ message: 'Compliance gate checks completed!', type: 'success' });
      await fetchProposal();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setGateLoading(false);
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
      <div className="min-h-screen bg-[var(--color-table-header-bg)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#3B82F6] mx-auto mb-4"></div>
          <p className="text-gray-400">Loading proposal...</p>
        </div>
      </div>
    );
  }

  if (error && !proposal) {
    return (
      <div className="min-h-screen bg-[var(--color-table-header-bg)] flex items-center justify-center">
        <div className="text-red-400 text-lg">{error}</div>
      </div>
    );
  }

  const evaluation = proposal?.evaluation;
  const aiCost = proposal?.ai_cost;

  return (
    <div className="min-h-screen bg-[var(--color-table-header-bg)] p-4 md:p-8">
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

        {/* Sourcing Case Banner */}
        {proposal.sourcing_case_id && sourcingCase && (
          <div className="mb-6 p-4 bg-teal/10 border border-teal/30 rounded-lg flex items-center gap-3">
            <span className="text-2xl">🎯</span>
            <div className="flex-1">
              <p className="text-teal font-semibold text-sm">
                This proposal responds to:{' '}
                <button
                  onClick={() => navigate('/sourcing-cases')}
                  className="underline hover:text-teal/80 transition-colors"
                >
                  {sourcingCase.title}
                </button>
              </p>
            </div>
          </div>
        )}

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

        {/* Vendor Reputation / Previously Applied Indicator */}
        {vendorReputation && vendorReputation.submission_history && vendorReputation.submission_history.length > 1 && (
          <div className="mb-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg flex items-center gap-3">
            <span className="text-xl">⚡</span>
            <div className="flex-1">
              <p className="text-blue-300 text-sm">
                This vendor has submitted <span className="font-bold text-white">{vendorReputation.submission_history.length}</span> previous proposals.
                {vendorReputation.avg_evaluation_score != null && (
                  <> Average score: <span className="font-bold text-white">{vendorReputation.avg_evaluation_score.toFixed(1)}</span>.</>
                )}
                {' '}Reputation: <span className="font-bold" style={{
                  color: vendorReputation.reputation_tier === 'trusted' ? '#10B981' :
                         vendorReputation.reputation_tier === 'established' ? '#0D9488' :
                         vendorReputation.reputation_tier === 'emerging' ? '#F59E0B' :
                         vendorReputation.reputation_tier === 'flagged' ? '#EF4444' : '#94A3B8'
                }}>{vendorReputation.reputation_tier ? vendorReputation.reputation_tier.charAt(0).toUpperCase() + vendorReputation.reputation_tier.slice(1) : 'N/A'}</span>.
              </p>
            </div>
            {proposal.submitter_id && (
              <a
                href={`/vendors/${proposal.submitter_id}`}
                className="text-blue-400 hover:text-blue-300 text-sm font-medium whitespace-nowrap"
              >
                View Vendor →
              </a>
            )}
          </div>
        )}
        {vendorReputation && vendorReputation.submission_history && vendorReputation.submission_history.length <= 1 && (
          <div className="mb-6 p-4 bg-gray-500/10 border border-gray-500/30 rounded-lg flex items-center gap-3">
            <span className="text-xl">🆕</span>
            <p className="text-gray-300 text-sm">First-time vendor</p>
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

        {/* Compliance Gate */}
        {(() => {
          const gateStatus = proposal.compliance_gate_status || 'pending';
          const gateResult = proposal.compliance_gate_result;
          const canRunGate = userRole === 'admin' || userRole === 'analyst';
          return (
            <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-white">Compliance Gate</h3>
                {canRunGate && (
                  <button
                    onClick={handleRunGate}
                    disabled={gateLoading}
                    className="bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white px-5 py-2 rounded-lg font-semibold disabled:opacity-50 transition-colors"
                  >
                    {gateLoading ? (
                      <span className="flex items-center gap-2">
                        <span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
                        Running checks...
                      </span>
                    ) : gateResult ? 'Re-run Gate Check' : 'Run Gate Check'}
                  </button>
                )}
              </div>

              {gateStatus === 'pending' && !gateResult && (
                <p className="text-gray-500 text-sm">Compliance gate not yet run. Run gate checks before AI evaluation.</p>
              )}

              {gateStatus === 'pass' && (
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4 mb-4">
                  <p className="text-emerald-400 font-semibold flex items-center gap-2">
                    <span className="text-lg">&#10003;</span> All compliance checks passed
                  </p>
                </div>
              )}

              {gateStatus === 'flagged' && (
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-4">
                  <p className="text-amber-400 font-semibold flex items-center gap-2">
                    <span className="text-lg">&#9888;</span> {gateResult?.checks?.filter(c => c.result === 'flag').length || 0} flag(s) require review
                  </p>
                </div>
              )}

              {gateStatus === 'fail' && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-4">
                  <p className="text-red-400 font-semibold flex items-center gap-2">
                    <span className="text-lg">&#10007;</span> Submission incomplete — cannot proceed to evaluation
                  </p>
                </div>
              )}

              {gateResult && gateResult.checks && (
                <div className="space-y-2 mt-4">
                  {gateResult.checks.map((check, idx) => {
                    const icon = check.result === 'pass' ? '\u2713' : check.result === 'flag' ? '\u26A0' : '\u2717';
                    const colorClass = check.result === 'pass'
                      ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                      : check.result === 'flag'
                      ? 'text-amber-400 bg-amber-500/10 border-amber-500/30'
                      : 'text-red-400 bg-red-500/10 border-red-500/30';
                    return (
                      <div key={idx} className={`rounded-lg p-3 border ${colorClass}`}>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold">{icon}</span>
                          <span className="font-medium text-sm">{check.rule}</span>
                          <span className="ml-auto text-xs font-bold uppercase">{check.result}</span>
                        </div>
                        <p className="text-xs mt-1 opacity-80">{check.detail}</p>
                      </div>
                    );
                  })}
                </div>
              )}

              {gateResult && gateResult.recommendation && (
                <p className="text-gray-400 text-sm mt-4 italic">{gateResult.recommendation}</p>
              )}
            </div>
          );
        })()}

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
            {(evaluation?.novelty_score ?? proposal.novelty_score) != null && (
              <ScoreBar
                label="Innovation Novelty"
                score={evaluation?.novelty_score ?? proposal.novelty_score}
                reasoning={evaluation?.novelty_reasoning}
              />
            )}
          </div>
        )}

        {/* Stage-Gate Decision (admin/analyst) */}
        {(userRole === 'admin' || userRole === 'analyst') && (
          <GateDecisionSection
            proposalId={id}
            userRole={userRole}
            evaluation={{ composite_score: proposal.composite_score, summary_en: evaluation?.summary_en }}
            onToast={setToast}
            onRefresh={fetchProposal}
          />
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
              <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-[#3B82F6]">{(aiCost.prompt_tokens + aiCost.completion_tokens).toLocaleString()}</p>
                <p className="text-gray-500 text-xs mt-1">Total Tokens</p>
              </div>
              <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-[#F59E0B]">${parseFloat(aiCost.cost_usd).toFixed(4)}</p>
                <p className="text-gray-500 text-xs mt-1">Cost (USD)</p>
              </div>
              <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 text-center">
                <p className="text-2xl font-bold text-[#10B981]">{parseFloat(aiCost.energy_kwh).toFixed(6)}</p>
                <p className="text-gray-500 text-xs mt-1">Energy (kWh)</p>
              </div>
              <div className="bg-[var(--color-table-header-bg)] rounded-lg p-3 text-center">
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
            {(proposal.status === 'queued' || proposal.status === 'requires_review') && (() => {
              const gateBlocked = !proposal.compliance_gate_status || proposal.compliance_gate_status === 'pending' || proposal.compliance_gate_status === 'fail';
              return (
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleEvaluate}
                    disabled={actionLoading || gateBlocked}
                    title={gateBlocked ? 'Run compliance gate first' : ''}
                    className="bg-[#3B82F6] hover:bg-blue-600 text-white px-6 py-2.5 rounded-lg font-semibold disabled:opacity-50 transition-colors"
                  >
                    {actionLoading ? (
                      <span className="flex items-center gap-2">
                        <span className="animate-pulse">🧠</span> AI is evaluating... ~15s
                      </span>
                    ) : proposal.status === 'requires_review' ? 'Re-evaluate' : 'Run AI Evaluation'}
                  </button>
                  {gateBlocked && (
                    <span className="text-amber-400 text-xs">Gate check required</span>
                  )}
                </div>
              );
            })()}
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

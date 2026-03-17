import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const CONTROL_STATUS_STYLE = {
  pass: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  fail: 'bg-red-500/20 text-red-400 border-red-500/30',
  warning: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
};

const ComplianceAuditDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [audit, setAudit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedFramework, setExpandedFramework] = useState(null);
  const [expandedEvidence, setExpandedEvidence] = useState({});

  useEffect(() => {
    fetchAudit();
  }, [id]);

  const fetchAudit = async () => {
    try {
      setLoading(true);
      // Try the enriched endpoint first
      const { data } = await api.get(`/api/v1/compliance-audit-results/${id}`);
      setAudit(data);
    } catch {
      // Fallback to original endpoint
      try {
        const { data } = await api.get(`/api/v1/compliance-audits/${id}`);
        setAudit(data);
      } catch (err) {
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-teal-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading audit...</p>
        </div>
      </div>
    );
  }

  if (error && !audit) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-red-400 text-lg">{error}</div>
      </div>
    );
  }

  // Parse findings from either format
  const findings = audit?.findings_json || audit?.findings || {};
  const frameworks = audit?.frameworks || findings?.frameworks || [];
  const dataResidency = audit?.data_residency || findings?.data_residency || {};
  const vendorCert = audit?.vendor_certification || findings?.vendor_certification || {};
  const overallScore = audit?.overall_score ?? findings?.overall_score;
  const overallStatus = audit?.overall_status ?? findings?.overall_status;
  const summary = audit?.summary ?? findings?.summary;
  const scoreColor = (overallScore || 0) > 80 ? '#10B981' : (overallScore || 0) >= 50 ? '#F59E0B' : '#EF4444';

  return (
    <div className="min-h-screen bg-[#0F172A] p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white">Compliance Audit</h1>
            {audit?.proposal_title && (
              <Link to={`/proposals/${audit.proposal_id}`} className="text-[#3B82F6] hover:text-blue-300 text-sm mt-1 inline-block">
                {audit.proposal_title}
              </Link>
            )}
          </div>
          <button
            onClick={() => navigate('/compliance-audits')}
            className="text-[#3B82F6] hover:text-blue-300"
          >
            &larr; Back to Audits
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* AI Disclaimer */}
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mb-6">
          <p className="text-amber-300 text-sm">This audit was generated automatically by AI. Review the evidence below for each compliance control.</p>
        </div>

        {/* Overall Score */}
        <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
          <div className="flex items-center gap-8">
            <div className="text-center">
              <div className="text-6xl font-black" style={{ color: scoreColor }}>
                {overallScore ?? '—'}
              </div>
              <p className="text-gray-400 text-sm mt-1">Overall Score</p>
            </div>
            <div className="space-y-2">
              {overallStatus && (
                <span className={`px-3 py-1 rounded-full text-sm font-medium border ${
                  overallStatus === 'compliant' ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                  : overallStatus === 'partially_compliant' ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                  : 'bg-red-500/20 text-red-400 border-red-500/30'
                }`}>
                  {overallStatus.replace(/_/g, ' ')}
                </span>
              )}
              <div className="flex gap-3 mt-2">
                <span className="text-gray-500 text-xs">Type: <span className="text-gray-300">{audit?.audit_type}</span></span>
                <span className="text-gray-500 text-xs">Date: <span className="text-gray-300">{audit?.audit_timestamp ? new Date(audit.audit_timestamp).toLocaleString() : 'N/A'}</span></span>
              </div>
            </div>
          </div>
        </div>

        {/* Summary */}
        {summary && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <h3 className="text-lg font-bold text-white mb-3">Summary</h3>
            <p className="text-gray-300 leading-relaxed">{summary}</p>
          </div>
        )}

        {/* Framework Controls — Evidence & Findings */}
        {frameworks.length > 0 && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <h3 className="text-lg font-bold text-white mb-4">Evidence &amp; Findings</h3>
            <div className="space-y-3">
              {frameworks.map((fw, idx) => {
                const controls = fw.controls || [];
                const passCount = controls.filter(c => c.status === 'pass').length;
                const failCount = controls.filter(c => c.status === 'fail').length;
                const warnCount = controls.filter(c => c.status === 'warning').length;

                return (
                  <div key={idx} className="bg-[#0F172A] rounded-lg border border-gray-700/50">
                    <button
                      onClick={() => setExpandedFramework(expandedFramework === idx ? null : idx)}
                      className="w-full flex items-center justify-between p-4 text-left"
                    >
                      <span className="text-white font-semibold">{fw.name}</span>
                      <div className="flex items-center gap-3">
                        {passCount > 0 && <span className="text-emerald-400 text-xs">{passCount} pass</span>}
                        {warnCount > 0 && <span className="text-amber-400 text-xs">{warnCount} warn</span>}
                        {failCount > 0 && <span className="text-red-400 text-xs">{failCount} fail</span>}
                        <span className="text-gray-400">{expandedFramework === idx ? '▾' : '▸'}</span>
                      </div>
                    </button>
                    {expandedFramework === idx && (
                      <div className="px-4 pb-4 space-y-3">
                        {controls.map((ctrl, ci) => {
                          const evidenceKey = `${idx}-${ci}`;
                          const isEvidenceExpanded = expandedEvidence[evidenceKey];
                          return (
                            <div key={ci} className="bg-[#1E293B] rounded-lg p-4">
                              <div className="flex items-center justify-between mb-2">
                                <div>
                                  <span className="text-gray-500 font-mono text-xs mr-2">{ctrl.control_id}</span>
                                  <span className="text-gray-200 text-sm font-medium">{ctrl.control_name}</span>
                                </div>
                                <span className={`px-2 py-0.5 rounded text-xs font-bold border ${CONTROL_STATUS_STYLE[ctrl.status] || CONTROL_STATUS_STYLE.warning}`}>
                                  {ctrl.status?.toUpperCase()}
                                </span>
                              </div>
                              {(ctrl.finding || ctrl.recommendation) && (
                                <button
                                  onClick={() => setExpandedEvidence(prev => ({ ...prev, [evidenceKey]: !prev[evidenceKey] }))}
                                  className="text-teal-400 hover:text-teal-300 text-xs font-medium mt-1 flex items-center gap-1"
                                >
                                  {isEvidenceExpanded ? '▾ Hide evidence' : '▸ Show evidence'}
                                </button>
                              )}
                              {isEvidenceExpanded && (
                                <div className="mt-3 pl-3 border-l-2 border-gray-700 space-y-2">
                                  {ctrl.finding && (
                                    <div>
                                      <span className="text-gray-500 text-xs font-medium uppercase">Finding</span>
                                      <p className="text-gray-300 text-sm mt-0.5">{ctrl.finding}</p>
                                    </div>
                                  )}
                                  {ctrl.recommendation && (
                                    <div>
                                      <span className="text-gray-500 text-xs font-medium uppercase">Recommendation</span>
                                      <p className="text-teal-400 text-sm mt-0.5">{ctrl.recommendation}</p>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Data Residency & Vendor Certification */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-bold text-white mb-3">Data Residency</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${
              audit?.data_residency_verified || dataResidency?.compliant
                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                : 'bg-red-500/20 text-red-400 border-red-500/30'
            }`}>
              {audit?.data_residency_verified || dataResidency?.compliant ? 'UAE Compliant' : 'Not Verified'}
            </span>
            {dataResidency?.finding && (
              <p className="text-gray-400 text-sm mt-3">{dataResidency.finding}</p>
            )}
            {dataResidency?.recommendation && (
              <p className="text-teal-400 text-sm mt-2">Rec: {dataResidency.recommendation}</p>
            )}
          </div>
          <div className="bg-[#1E293B] rounded-xl p-6 border border-gray-700/50">
            <h3 className="text-lg font-bold text-white mb-3">Vendor Certification</h3>
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${
              vendorCert?.desc_approved
                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                : 'bg-amber-500/20 text-amber-400 border-amber-500/30'
            }`}>
              {vendorCert?.desc_approved ? 'DESC Approved' : 'Not DESC Approved'}
            </span>
            {vendorCert?.finding && (
              <p className="text-gray-400 text-sm mt-3">{vendorCert.finding}</p>
            )}
          </div>
        </div>

        {/* Compliance Flags */}
        <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
          <h3 className="text-lg font-bold text-white mb-4">Compliance Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-[#0F172A] rounded-lg p-4 text-center">
              <p className={`text-2xl font-bold ${audit?.isr_v3_compliance ? 'text-emerald-400' : 'text-red-400'}`}>
                {audit?.isr_v3_compliance ? 'Pass' : 'Fail'}
              </p>
              <p className="text-gray-500 text-xs mt-1">ISR V3</p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-4 text-center">
              <p className={`text-2xl font-bold ${audit?.ai_security_policy_compliance ? 'text-emerald-400' : 'text-red-400'}`}>
                {audit?.ai_security_policy_compliance ? 'Pass' : 'Fail'}
              </p>
              <p className="text-gray-500 text-xs mt-1">AI Security</p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-4 text-center">
              <p className={`text-2xl font-bold ${audit?.csp_standards_compliance ? 'text-emerald-400' : 'text-red-400'}`}>
                {audit?.csp_standards_compliance ? 'Pass' : 'Fail'}
              </p>
              <p className="text-gray-500 text-xs mt-1">CSP Standards</p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-4 text-center">
              <p className={`text-2xl font-bold ${audit?.remediation_required ? 'text-amber-400' : 'text-emerald-400'}`}>
                {audit?.remediation_required ? 'Yes' : 'No'}
              </p>
              <p className="text-gray-500 text-xs mt-1">Remediation</p>
            </div>
          </div>
        </div>

        {/* Raw Findings (fallback for old audits) */}
        {!frameworks.length && audit?.findings_json && (
          <div className="bg-[#1E293B] rounded-xl p-6 mb-6 border border-gray-700/50">
            <h3 className="text-lg font-bold text-white mb-3">Findings</h3>
            <pre className="bg-[#0F172A] p-4 rounded-lg overflow-x-auto text-sm text-gray-300">
              {JSON.stringify(audit.findings_json, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default ComplianceAuditDetail;

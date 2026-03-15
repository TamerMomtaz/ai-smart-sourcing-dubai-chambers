import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const ComplianceAuditDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [audit, setAudit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloadLoading, setDownloadLoading] = useState(false);

  useEffect(() => {
    fetchAudit();
  }, [id]);

  const fetchAudit = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/compliance-audits/${id}`);
      setAudit(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    try {
      setDownloadLoading(true);
      const { data } = await api.get(`/api/v1/compliance-audits/${id}/report`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `compliance-audit-${id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDownloadLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-teal font-heading text-xl">Loading audit...</div>
      </div>
    );
  }

  if (error && !audit) {
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
          <h1 className="font-heading text-4xl text-ink">Compliance Audit</h1>
          <button
            onClick={() => navigate('/compliance-audits')}
            className="text-teal hover:underline font-body"
          >
            ← Back to Audits
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-burgundy/10 border border-burgundy rounded-lg text-burgundy">
            {error}
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm p-8 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <span className="text-gray-600 font-body text-sm">Audit Type</span>
              <p className="text-ink font-semibold mt-1">{audit.audit_type}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Audit Timestamp</span>
              <p className="text-ink font-semibold mt-1">
                {audit.audit_timestamp ? new Date(audit.audit_timestamp).toLocaleString() : 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">ISR v3 Compliance</span>
              <p className="text-ink font-semibold mt-1">{audit.isr_v3_compliance ? '✓ Pass' : '✗ Fail'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">AI Security Policy</span>
              <p className="text-ink font-semibold mt-1">{audit.ai_security_policy_compliance ? '✓ Pass' : '✗ Fail'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">CSP Standards</span>
              <p className="text-ink font-semibold mt-1">{audit.csp_standards_compliance ? '✓ Pass' : '✗ Fail'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Data Residency</span>
              <p className="text-ink font-semibold mt-1">{audit.data_residency_verified ? '✓ Verified' : '✗ Not Verified'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Remediation Required</span>
              <p className="text-ink font-semibold mt-1">{audit.remediation_required ? 'Yes' : 'No'}</p>
            </div>
          </div>

          {audit.findings_json && (
            <div className="border-t pt-6">
              <h3 className="font-heading text-2xl text-ink mb-4">Findings</h3>
              <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
                {JSON.stringify(audit.findings_json, null, 2)}
              </pre>
            </div>
          )}

          <div className="border-t pt-6 flex gap-4">
            <button
              onClick={handleDownloadReport}
              disabled={downloadLoading}
              className="bg-teal text-white py-2 px-6 rounded-lg font-semibold hover:bg-teal/90 disabled:opacity-50 transition-colors"
            >
              {downloadLoading ? 'Downloading...' : 'Download Report'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceAuditDetail;
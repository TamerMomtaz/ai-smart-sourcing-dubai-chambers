import React from 'react';
import { Link } from 'react-router-dom';
import StatusBadge from './StatusBadge';

const ComplianceAuditCard = ({ audit }) => {
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAuditTypeLabel = (type) => {
    const labels = {
      isr_v3: 'DESC ISR V3 Controls',
      ai_security_policy: 'DESC AI Security Policy (5-Phase Lifecycle)',
      csp_standards: 'DESC CSP Standards (ISO/IEC 27001, ISO/IEC 27017, CSA CCM v4.0.5)',
      comprehensive: 'Comprehensive'
    };
    return labels[type] || type;
  };

  const getComplianceIcon = (passed) => {
    return passed ? '✓' : '✗';
  };

  const getComplianceColor = (passed) => {
    return passed ? 'text-teal' : 'text-burgundy';
  };

  return (
    <Link to={`/compliance-audits/${audit.id}`}>
      <div className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition cursor-pointer border border-transparent hover:border-teal">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-heading font-bold text-ink mb-2">
              {getAuditTypeLabel(audit.audit_type)} Audit
            </h3>
            <p className="text-sm font-body text-ink/60">
              {formatDate(audit.audit_timestamp)}
            </p>
          </div>
          <StatusBadge status={audit.status || 'completed'} />
        </div>

        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="flex items-center space-x-2">
            <span className={`text-lg ${getComplianceColor(audit.isr_v3_compliance)}`}>
              {getComplianceIcon(audit.isr_v3_compliance)}
            </span>
            <span className="text-sm font-body text-ink/60">DESC ISR V3 Controls</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`text-lg ${getComplianceColor(audit.ai_security_policy_compliance)}`}>
              {getComplianceIcon(audit.ai_security_policy_compliance)}
            </span>
            <span className="text-sm font-body text-ink/60">DESC AI Security Policy (5-Phase Lifecycle)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`text-lg ${getComplianceColor(audit.csp_standards_compliance)}`}>
              {getComplianceIcon(audit.csp_standards_compliance)}
            </span>
            <span className="text-sm font-body text-ink/60">DESC CSP Standards (ISO/IEC 27001, ISO/IEC 27017, CSA CCM v4.0.5)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`text-lg ${getComplianceColor(audit.data_residency_verified)}`}>
              {getComplianceIcon(audit.data_residency_verified)}
            </span>
            <span className="text-sm font-body text-ink/60">Data Residency</span>
          </div>
        </div>

        {audit.remediation_required && (
          <div className="p-3 bg-gold/10 border border-gold rounded-lg">
            <p className="text-xs font-body text-gold font-medium">⚠️ Remediation required</p>
          </div>
        )}

        {audit.hash_chain_signature && (
          <div className="mt-4 pt-4 border-t border-ink/10">
            <p className="text-xs font-mono text-ink/40 truncate">
              Hash: {audit.hash_chain_signature}
            </p>
          </div>
        )}
      </div>
    </Link>
  );
};

export default ComplianceAuditCard;
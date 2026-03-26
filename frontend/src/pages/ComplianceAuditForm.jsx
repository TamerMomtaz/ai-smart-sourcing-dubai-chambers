import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const ComplianceAuditForm = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    proposal_id: '',
    audit_type: 'comprehensive'
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.proposal_id.trim()) {
      setError('Proposal ID is required');
      return;
    }

    try {
      setLoading(true);
      await api.post('/api/v1/compliance-audits', formData);
      navigate('/compliance-audits');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="font-heading text-4xl text-ink mb-8">Trigger Compliance Audit</h1>

        {error && (
          <div className="mb-6 p-4 bg-burgundy/10 border border-burgundy rounded-lg text-burgundy">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm p-8 space-y-6">
          <div>
            <label className="block text-ink font-body font-semibold mb-2">Proposal ID</label>
            <input
              type="text"
              name="proposal_id"
              value={formData.proposal_id}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
              required
            />
          </div>

          <div>
            <label className="block text-ink font-body font-semibold mb-2">Audit Type</label>
            <select
              name="audit_type"
              value={formData.audit_type}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
            >
              <option value="isr_v3">DESC ISR V3 Controls</option>
              <option value="ai_security_policy">DESC AI Security Policy (5-Phase Lifecycle)</option>
              <option value="csp_standards">DESC CSP Standards (ISO/IEC 27001, ISO/IEC 27017, CSA CCM v4.0.5)</option>
              <option value="comprehensive">Comprehensive</option>
            </select>
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-teal text-white py-3 px-6 rounded-lg font-semibold hover:bg-teal/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Triggering...' : 'Trigger Audit'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/compliance-audits')}
              className="flex-1 bg-gray-200 text-ink py-3 px-6 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ComplianceAuditForm;
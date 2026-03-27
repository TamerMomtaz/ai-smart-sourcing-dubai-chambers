import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const BusinessGroupForm = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    relevance_weight: 0.25,
    feasibility_weight: 0.25,
    sector_alignment_weight: 0.25,
    compliance_weight: 0.25
  });

  useEffect(() => {
    if (isEdit) {
      fetchBusinessGroup();
    }
  }, [id]);

  const fetchBusinessGroup = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/business-groups/${id}`);
      if (data.evaluation_weight_config_json) {
        setFormData({
          relevance_weight: data.evaluation_weight_config_json.relevance_weight || 0.25,
          feasibility_weight: data.evaluation_weight_config_json.feasibility_weight || 0.25,
          sector_alignment_weight: data.evaluation_weight_config_json.sector_alignment_weight || 0.25,
          compliance_weight: data.evaluation_weight_config_json.compliance_weight || 0.25
        });
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: parseFloat(value) }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const total = Object.values(formData).reduce((sum, val) => sum + val, 0);
    if (Math.abs(total - 1.0) > 0.01) {
      setError('Weights must sum to 1.0');
      return;
    }

    try {
      setLoading(true);
      await api.patch(`/api/v1/business-groups/${id}/evaluation-config`, formData);
      navigate('/business-groups');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading && isEdit) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-teal font-heading text-xl">Loading business group...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-4 md:p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="font-heading text-4xl text-ink mb-8">Configure Evaluation Weights</h1>

        {error && (
          <div className="mb-6 p-4 bg-burgundy/10 border border-burgundy rounded-lg text-burgundy">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm p-8 space-y-6">
          <div>
            <label className="block text-ink font-body font-semibold mb-2">Relevance Weight</label>
            <input
              type="number"
              name="relevance_weight"
              value={formData.relevance_weight}
              onChange={handleChange}
              step="0.01"
              min="0"
              max="1"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
              required
            />
          </div>

          <div>
            <label className="block text-ink font-body font-semibold mb-2">Feasibility Weight</label>
            <input
              type="number"
              name="feasibility_weight"
              value={formData.feasibility_weight}
              onChange={handleChange}
              step="0.01"
              min="0"
              max="1"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
              required
            />
          </div>

          <div>
            <label className="block text-ink font-body font-semibold mb-2">Sector Alignment Weight</label>
            <input
              type="number"
              name="sector_alignment_weight"
              value={formData.sector_alignment_weight}
              onChange={handleChange}
              step="0.01"
              min="0"
              max="1"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
              required
            />
          </div>

          <div>
            <label className="block text-ink font-body font-semibold mb-2">Compliance Weight</label>
            <input
              type="number"
              name="compliance_weight"
              value={formData.compliance_weight}
              onChange={handleChange}
              step="0.01"
              min="0"
              max="1"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
              required
            />
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-teal text-white py-3 px-6 rounded-lg font-semibold hover:bg-teal/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Saving...' : 'Update Configuration'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/business-groups')}
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

export default BusinessGroupForm;
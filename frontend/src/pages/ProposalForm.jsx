import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const ProposalForm = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    title: '',
    sector: 'fintech',
    technology_type: 'ai_ml',
    maturity_level: 'concept',
    language: 'en'
  });

  useEffect(() => {
    if (isEdit) {
      fetchProposal();
    }
  }, [id]);

  const fetchProposal = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/proposals/${id}`);
      setFormData({
        title: data.title || '',
        sector: data.sector || 'fintech',
        technology_type: data.technology_type || 'ai_ml',
        maturity_level: data.maturity_level || 'concept',
        language: data.language || 'en'
      });
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!formData.title.trim()) {
      setError('Title is required');
      return;
    }

    try {
      setLoading(true);
      if (isEdit) {
        await api.patch(`/api/v1/proposals/${id}`, formData);
      } else {
        await api.post('/api/v1/proposals', formData);
      }
      navigate('/proposals');
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading && isEdit) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-teal font-heading text-xl">Loading proposal...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="font-heading text-4xl text-ink mb-8">
          {isEdit ? 'Edit Proposal' : 'Create Proposal'}
        </h1>

        {error && (
          <div className="mb-6 p-4 bg-burgundy/10 border border-burgundy rounded-lg text-burgundy">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm p-8 space-y-6">
          <div>
            <label className="block text-ink font-body font-semibold mb-2">Title</label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
              required
            />
          </div>

          <div>
            <label className="block text-ink font-body font-semibold mb-2">Sector</label>
            <select
              name="sector"
              value={formData.sector}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
            >
              <option value="fintech">FinTech</option>
              <option value="healthcare">Healthcare</option>
              <option value="logistics">Logistics</option>
              <option value="energy">Energy</option>
              <option value="education">Education</option>
              <option value="government">Government</option>
              <option value="tourism">Tourism</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-ink font-body font-semibold mb-2">Technology Type</label>
            <select
              name="technology_type"
              value={formData.technology_type}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
            >
              <option value="ai_ml">AI/ML</option>
              <option value="blockchain">Blockchain</option>
              <option value="iot">IoT</option>
              <option value="cloud">Cloud</option>
              <option value="cybersecurity">Cybersecurity</option>
              <option value="data_analytics">Data Analytics</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-ink font-body font-semibold mb-2">Maturity Level</label>
            <select
              name="maturity_level"
              value={formData.maturity_level}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
            >
              <option value="concept">Concept</option>
              <option value="prototype">Prototype</option>
              <option value="mvp">MVP</option>
              <option value="production">Production</option>
            </select>
          </div>

          <div>
            <label className="block text-ink font-body font-semibold mb-2">Language</label>
            <select
              name="language"
              value={formData.language}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal"
            >
              <option value="en">English</option>
              <option value="ar">Arabic</option>
            </select>
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-teal text-white py-3 px-6 rounded-lg font-semibold hover:bg-teal/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Saving...' : isEdit ? 'Update Proposal' : 'Create Proposal'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/proposals')}
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

export default ProposalForm;
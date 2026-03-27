import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const BusinessGroupDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [group, setGroup] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchBusinessGroup();
  }, [id]);

  const fetchBusinessGroup = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/business-groups/${id}`);
      setGroup(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-teal font-heading text-xl">Loading business group...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-burgundy font-body text-lg">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="font-heading text-4xl text-ink">{group.name}</h1>
          <button
            onClick={() => navigate('/business-groups')}
            className="text-teal hover:underline font-body"
          >
            ← Back to Business Groups
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-8 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <span className="text-gray-600 font-body text-sm">Chamber</span>
              <p className="text-ink font-semibold mt-1">{group.chamber || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Description</span>
              <p className="text-ink font-semibold mt-1">{group.description || 'N/A'}</p>
            </div>
          </div>

          {group.evaluation_weight_config_json && (
            <div className="border-t pt-6">
              <h3 className="font-heading text-2xl text-ink mb-4">Evaluation Weights</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-gray-600 font-body text-sm">Relevance</span>
                  <p className="text-teal font-bold text-2xl mt-1">{(group.evaluation_weight_config_json.relevance_weight * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <span className="text-gray-600 font-body text-sm">Feasibility</span>
                  <p className="text-teal font-bold text-2xl mt-1">{(group.evaluation_weight_config_json.feasibility_weight * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <span className="text-gray-600 font-body text-sm">Sector Alignment</span>
                  <p className="text-teal font-bold text-2xl mt-1">{(group.evaluation_weight_config_json.sector_alignment_weight * 100).toFixed(0)}%</p>
                </div>
                <div>
                  <span className="text-gray-600 font-body text-sm">Compliance</span>
                  <p className="text-teal font-bold text-2xl mt-1">{(group.evaluation_weight_config_json.compliance_weight * 100).toFixed(0)}%</p>
                </div>
              </div>
            </div>
          )}

          <div className="border-t pt-6 flex gap-4">
            <button
              onClick={() => navigate(`/business-groups/${id}/edit`)}
              className="bg-teal text-white py-2 px-6 rounded-lg font-semibold hover:bg-teal/90 transition-colors"
            >
              Configure Weights
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BusinessGroupDetail;
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const VendorDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [vendor, setVendor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchVendor();
  }, [id]);

  const fetchVendor = async () => {
    try {
      setLoading(true);
      const { data } = await api.get(`/api/v1/vendors/${id}`);
      setVendor(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-teal font-heading text-xl">Loading vendor...</div>
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
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="font-heading text-4xl text-ink">{vendor.name}</h1>
          <button
            onClick={() => navigate('/vendors')}
            className="text-teal hover:underline font-body"
          >
            ← Back to Vendors
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-8 space-y-6">
          <div className="grid grid-cols-2 gap-6">
            <div>
              <span className="text-gray-600 font-body text-sm">Company Registration</span>
              <p className="text-ink font-semibold mt-1">{vendor.company_registration || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Country</span>
              <p className="text-ink font-semibold mt-1">{vendor.country || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Contact Email</span>
              <p className="text-ink font-semibold mt-1">{vendor.contact_email || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Contact Phone</span>
              <p className="text-ink font-semibold mt-1">{vendor.contact_phone || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Website</span>
              <p className="text-ink font-semibold mt-1">
                {vendor.website ? (
                  <a href={vendor.website} target="_blank" rel="noopener noreferrer" className="text-teal hover:underline">
                    {vendor.website}
                  </a>
                ) : 'N/A'}
              </p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">DESC Approved</span>
              <p className="text-ink font-semibold mt-1">{vendor.is_desc_approved ? 'Yes' : 'No'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Onboarding Status</span>
              <p className="text-ink font-semibold mt-1">{vendor.onboarding_status || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Submission History</span>
              <p className="text-ink font-semibold mt-1">{vendor.submission_history_count || 0} proposals</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">Average Compliance Score</span>
              <p className="text-ink font-semibold mt-1">{vendor.average_compliance_score || 'N/A'}</p>
            </div>
            <div>
              <span className="text-gray-600 font-body text-sm">API Access</span>
              <p className="text-ink font-semibold mt-1">{vendor.api_access_enabled ? 'Enabled' : 'Disabled'}</p>
            </div>
          </div>

          <div className="border-t pt-6 flex gap-4">
            <button
              onClick={() => navigate(`/vendors/${id}/edit`)}
              className="bg-teal text-white py-2 px-6 rounded-lg font-semibold hover:bg-teal/90 transition-colors"
            >
              Edit
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VendorDetail;
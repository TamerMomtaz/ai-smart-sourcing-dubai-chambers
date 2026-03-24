import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { ReputationGauge, TIER_COLORS, TIER_LABELS } from '../components/VendorReputationBadge';

const VendorDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [vendor, setVendor] = useState(null);
  const [reputation, setReputation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentUser, setCurrentUser] = useState(null);
  const [formulaOpen, setFormulaOpen] = useState(false);

  useEffect(() => {
    api.get('/api/v1/users/me').then(res => setCurrentUser(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    fetchVendor();
    fetchReputation();
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

  const fetchReputation = async () => {
    try {
      const { data } = await api.get(`/api/v1/vendors/${id}/reputation`);
      setReputation(data);
    } catch {
      // Non-critical — reputation data may not exist
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

  const tierColor = TIER_COLORS[reputation?.reputation_tier] || '#94A3B8';
  const tierLabel = TIER_LABELS[reputation?.reputation_tier] || reputation?.reputation_tier || 'N/A';

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

        {/* Reputation Profile Section */}
        {reputation && reputation.reputation_score != null && (
          <div className="mb-6 space-y-4">
            {/* Reputation Summary Card */}
            <div className="bg-[#1E293B] rounded-xl p-8 shadow-lg">
              <div className="flex items-center gap-8">
                <ReputationGauge score={reputation.reputation_score} tier={reputation.reputation_tier} size={96} />
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-2xl font-bold text-white">Reputation Profile</h2>
                    <span
                      className="px-3 py-1 rounded-full text-sm font-bold"
                      style={{ backgroundColor: `${tierColor}20`, color: tierColor }}
                    >
                      {tierLabel}
                    </span>
                  </div>
                  <p className="text-gray-400 text-sm">
                    Based on {reputation.total_evaluations || 0} evaluation{reputation.total_evaluations !== 1 ? 's' : ''} across {reputation.submission_history?.length || 0} submission{(reputation.submission_history?.length || 0) !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
                <p className="text-gray-500 text-xs font-body mb-1">Avg Evaluation Score</p>
                <p className="text-2xl font-bold text-ink">
                  {reputation.avg_evaluation_score != null ? `${reputation.avg_evaluation_score.toFixed(1)}` : '—'}
                  <span className="text-sm text-gray-400 font-normal">/100</span>
                </p>
              </div>
              <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
                <p className="text-gray-500 text-xs font-body mb-1">Compliance Rate</p>
                <p className="text-2xl font-bold text-ink">
                  {reputation.compliance_pass_rate != null ? `${reputation.compliance_pass_rate.toFixed(1)}%` : '—'}
                </p>
              </div>
              <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
                <p className="text-gray-500 text-xs font-body mb-1">Claim Verifiability</p>
                <p className="text-2xl font-bold text-ink">
                  {reputation.avg_grounding_score != null ? `${reputation.avg_grounding_score.toFixed(1)}%` : '—'}
                </p>
                <p className="text-gray-400 text-xs mt-0.5">from Shield</p>
              </div>
              <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
                <p className="text-gray-500 text-xs font-body mb-1">DESC Status</p>
                <p className="text-2xl font-bold text-ink">
                  {reputation.desc_certified ? (
                    <span className="text-emerald-500">Certified ✓</span>
                  ) : (
                    <span className="text-amber-500">Pending</span>
                  )}
                </p>
              </div>
            </div>

            {/* History Indicators */}
            <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
              <h3 className="text-sm font-semibold text-ink mb-3">History</h3>
              <div className="flex flex-wrap gap-4 text-sm">
                {reputation.shortlist_count > 0 && (
                  <span className="text-emerald-600 font-medium">
                    Shortlisted {reputation.shortlist_count} time{reputation.shortlist_count !== 1 ? 's' : ''}
                  </span>
                )}
                {reputation.rejection_count > 0 && (
                  <span className="text-red-500 font-medium">
                    Rejected {reputation.rejection_count} time{reputation.rejection_count !== 1 ? 's' : ''}
                  </span>
                )}
                {reputation.submission_history?.length > 0 && (
                  <span className="text-gray-500">
                    First submission: {new Date(reputation.submission_history[reputation.submission_history.length - 1].date).toLocaleDateString()}
                  </span>
                )}
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                  vendor.onboarding_status === 'active' ? 'bg-emerald-100 text-emerald-700' :
                  vendor.onboarding_status === 'pending' ? 'bg-amber-100 text-amber-700' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {vendor.onboarding_status}
                </span>
              </div>
            </div>

            {/* Submission History Timeline */}
            {reputation.submission_history?.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
                <h3 className="text-sm font-semibold text-ink mb-3">Submission Timeline</h3>
                <div className="space-y-3">
                  {reputation.submission_history.map((s, i) => (
                    <div key={i} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                      <div className="w-2 h-2 rounded-full flex-shrink-0" style={{
                        backgroundColor: s.score > 70 ? '#10B981' : s.score >= 40 ? '#F59E0B' : s.score != null ? '#EF4444' : '#94A3B8'
                      }} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-ink truncate">{s.proposal_title}</p>
                        <p className="text-xs text-gray-500">
                          {s.date ? new Date(s.date).toLocaleDateString() : '—'} · {s.status}
                        </p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        {s.score != null && (
                          <span className="text-sm font-bold" style={{
                            color: s.score > 70 ? '#10B981' : s.score >= 40 ? '#F59E0B' : '#EF4444'
                          }}>
                            {s.score.toFixed(1)}
                          </span>
                        )}
                        {s.compliance != null && (
                          <p className="text-xs text-gray-400">Compliance: {s.compliance.toFixed(0)}%</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Reputation Formula Transparency */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <button
                onClick={() => setFormulaOpen(!formulaOpen)}
                className="w-full flex items-center justify-between p-5 text-left hover:bg-gray-50 transition"
              >
                <span className="text-sm font-semibold text-ink">How is this score calculated?</span>
                <span className="text-gray-400">{formulaOpen ? '▾' : '▸'}</span>
              </button>
              {formulaOpen && reputation.formula && (
                <div className="px-5 pb-5 space-y-3">
                  {[
                    { label: 'Evaluation Quality', weight: reputation.formula.evaluation_weight, color: '#3B82F6' },
                    { label: 'Compliance Track Record', weight: reputation.formula.compliance_weight, color: '#10B981' },
                    { label: 'Claim Verifiability (Shield)', weight: reputation.formula.grounding_weight, color: '#F59E0B' },
                    { label: 'DESC Certification', weight: reputation.formula.desc_weight, color: '#8B5CF6' },
                    { label: 'Engagement History', weight: reputation.formula.engagement_weight, color: '#EC4899' },
                  ].map((item, i) => (
                    <div key={i} className="flex items-center gap-3">
                      <div className="w-24 text-right text-sm font-bold" style={{ color: item.color }}>
                        {(item.weight * 100).toFixed(0)}%
                      </div>
                      <div className="flex-1">
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${item.weight * 100}%`, backgroundColor: item.color }}
                          />
                        </div>
                      </div>
                      <span className="text-sm text-gray-600 w-48">{item.label}</span>
                    </div>
                  ))}
                  <p className="text-xs text-gray-400 italic mt-2 pt-2 border-t border-gray-100">
                    σI — Every score is traceable. Every component is visible.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Existing Vendor Info */}
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

          {vendor.updated_at && (
            <div className="border-t pt-4">
              <span className="text-gray-600 font-body text-sm">Last Modified</span>
              <p className="text-ink font-semibold mt-1">{new Date(vendor.updated_at).toLocaleString()}</p>
            </div>
          )}

          <div className="border-t pt-6 flex gap-4">
            {currentUser?.role === 'admin' || currentUser?.role === 'executive' ? (
              <button
                onClick={() => navigate(`/vendors/${id}/edit`)}
                className="bg-teal text-white py-2 px-6 rounded-lg font-semibold hover:bg-teal/90 transition-colors"
              >
                Edit
              </button>
            ) : (
              <button
                disabled
                className="bg-gray-300 text-gray-500 py-2 px-6 rounded-lg font-semibold cursor-not-allowed"
                title="Only admins can edit vendor records"
              >
                Edit
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VendorDetail;

import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { ReputationGauge, TIER_COLORS as REP_TIER_COLORS, TIER_LABELS as REP_TIER_LABELS } from '../components/VendorReputationBadge';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';

const VSCORE_TIER_COLORS = {
  platinum: '#0D9488',
  gold: '#B8904A',
  silver: '#3B82F6',
  bronze: '#F59E0B',
  under_review: '#EF4444',
};

const VSCORE_TIER_LABELS = {
  platinum: 'Platinum',
  gold: 'Gold',
  silver: 'Silver',
  bronze: 'Bronze',
  under_review: 'Under Review',
};

const OUTCOME_COLORS = {
  completed: '#10B981',
  partial: '#F59E0B',
  failed: '#EF4444',
  ongoing: '#3B82F6',
};

const VScoreGauge = ({ score, tier, size = 120 }) => {
  const [animated, setAnimated] = useState(0);
  const color = VSCORE_TIER_COLORS[tier] || '#94A3B8';
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = ((animated - 300) / 600) * circumference;

  useEffect(() => {
    if (score == null) return;
    const duration = 1500;
    const startTime = performance.now();
    const animate = (now) => {
      const elapsed = now - startTime;
      const pct = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - pct, 3); // ease-out cubic
      setAnimated(Math.round(300 + eased * (score - 300)));
      if (pct < 1) requestAnimationFrame(animate);
    };
    requestAnimationFrame(animate);
  }, [score]);

  if (score == null) return null;

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#334155" strokeWidth={6} />
          <circle
            cx={size / 2} cy={size / 2} r={radius} fill="none"
            stroke={color} strokeWidth={6} strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - Math.max(0, progress)}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
            style={{ transition: 'stroke-dashoffset 0.3s ease-out' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-black text-white" style={{ fontSize: size > 80 ? '2rem' : '1.2rem' }}>
            {animated}
          </span>
        </div>
      </div>
      <span
        className="px-3 py-1 rounded-full text-sm font-bold"
        style={{ backgroundColor: `${color}20`, color }}
      >
        {VSCORE_TIER_LABELS[tier] || tier}
      </span>
    </div>
  );
};

const StarRating = ({ rating }) => {
  if (rating == null) return null;
  return (
    <span className="text-amber-400">
      {'★'.repeat(Math.round(rating))}{'☆'.repeat(5 - Math.round(rating))}
    </span>
  );
};

const VendorDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [vendor, setVendor] = useState(null);
  const [reputation, setReputation] = useState(null);
  const [vscore, setVscore] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentUser, setCurrentUser] = useState(null);
  const [formulaOpen, setFormulaOpen] = useState(false);
  const [vscoreFormulaOpen, setVscoreFormulaOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('dossier');

  useEffect(() => {
    api.get('/api/v1/users/me').then(res => setCurrentUser(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    fetchVendor();
    fetchReputation();
    fetchVscore();
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
      // Non-critical
    }
  };

  const fetchVscore = async () => {
    try {
      const { data } = await api.get(`/api/v1/vendors/${id}/vscore`);
      setVscore(data);
    } catch {
      // Non-critical — vScore data may not exist
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

  const tierColor = VSCORE_TIER_COLORS[vscore?.vscore_tier] || REP_TIER_COLORS[reputation?.reputation_tier] || '#94A3B8';

  // Radar chart data
  const radarData = vscore?.dimension_scores ? [
    { dim: 'Performance', value: vscore.dimension_scores.performance || 0, fullMark: 100 },
    { dim: 'Quality', value: vscore.dimension_scores.quality || 0, fullMark: 100 },
    { dim: 'Compliance', value: vscore.dimension_scores.compliance || 0, fullMark: 100 },
    { dim: 'Integrity', value: vscore.dimension_scores.integrity || 0, fullMark: 100 },
    { dim: 'Entity', value: vscore.dimension_scores.entity || 0, fullMark: 100 },
  ] : [];

  const positiveFlags = (vscore?.flags || []).filter(f => {
    const posTypes = ['iso_27001', 'iso_9001', 'iso_14001', 'soc2_type2', 'commendation', 'desc_audit', 'award'];
    return posTypes.includes(f.flag_type) || f.severity === 'info';
  });
  const negativeFlags = (vscore?.flags || []).filter(f => {
    const posTypes = ['iso_27001', 'iso_9001', 'iso_14001', 'soc2_type2', 'commendation', 'desc_audit', 'award'];
    return !posTypes.includes(f.flag_type) && f.severity !== 'info';
  });

  return (
    <div className="min-h-screen bg-cream p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <h1 className="font-heading text-3xl md:text-4xl text-ink">{vendor.name}</h1>
          <button
            onClick={() => navigate('/vendors')}
            className="text-teal hover:underline font-body"
          >
            ← Back to Vendors
          </button>
        </div>

        {/* vScore Dossier Section */}
        {vscore && vscore.vscore != null && (
          <div className="mb-6 space-y-4">
            {/* Score Header */}
            <div className="bg-[#1E293B] rounded-xl p-5 md:p-8 shadow-lg">
              <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-8">
                <VScoreGauge score={vscore.vscore} tier={vscore.vscore_tier} size={120} />
                <div className="flex-1 text-center sm:text-left">
                  <div className="flex items-center justify-center sm:justify-start gap-3 mb-2">
                    <h2 className="text-xl md:text-2xl font-bold text-white">vScore Dossier</h2>
                    {vscore.score_change !== 0 && (
                      <span className={`text-sm font-bold ${vscore.score_change > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                        {vscore.score_change > 0 ? '+' : ''}{vscore.score_change} {vscore.score_change > 0 ? '↑' : '↓'}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-400 text-sm">
                    Based on {vscore.engagements?.length || 0} engagements, {vscore.flags?.length || 0} flags, {vscore.relationships?.length || 0} relationships
                  </p>
                </div>
              </div>
            </div>

            {/* Two-column: Radar + AI Narrative */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Radar Chart */}
              {radarData.length > 0 && (
                <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                  <h3 className="text-white font-semibold mb-3">Dimension Breakdown</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#334155" />
                      <PolarAngleAxis dataKey="dim" tick={{ fill: '#94A3B8', fontSize: 12 }} />
                      <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#64748B', fontSize: 10 }} />
                      <Radar
                        dataKey="value"
                        stroke={VSCORE_TIER_COLORS[vscore.vscore_tier] || '#0D9488'}
                        fill={VSCORE_TIER_COLORS[vscore.vscore_tier] || '#0D9488'}
                        fillOpacity={0.3}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                  {/* Dimension bars */}
                  <div className="mt-4 space-y-2">
                    {radarData.map(d => (
                      <div key={d.dim} className="flex items-center gap-2">
                        <span className="text-gray-400 text-xs w-24">{d.dim}</span>
                        <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${d.value}%`, backgroundColor: VSCORE_TIER_COLORS[vscore.vscore_tier] || '#0D9488' }} />
                        </div>
                        <span className="text-white text-xs font-bold w-8 text-right">{d.value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* AI Narrative */}
              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-3">σI Risk Narrative</h3>
                {vscore.ai_narrative ? (
                  <blockquote className="border-l-4 border-[var(--color-accent)] pl-4 text-gray-300 text-sm leading-relaxed italic">
                    {vscore.ai_narrative}
                  </blockquote>
                ) : (
                  <p className="text-gray-500 text-sm italic">No AI narrative available for this vendor.</p>
                )}
                <p className="text-gray-500 text-xs mt-4">
                  This assessment was generated by σI and logged to the transparency dashboard.
                </p>
              </div>
            </div>

            {/* Engagement Timeline */}
            {vscore.engagements?.length > 0 && (
              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-4">Engagement Timeline</h3>
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gray-700" />
                  <div className="space-y-4">
                    {vscore.engagements.map((e, i) => {
                      const outcomeColor = OUTCOME_COLORS[e.outcome] || '#94A3B8';
                      return (
                        <EngagementNode key={i} engagement={e} outcomeColor={outcomeColor} />
                      );
                    })}
                  </div>
                </div>
              </div>
            )}

            {/* Certifications & Flags */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Positive Signals */}
              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-3">Positive Signals</h3>
                {positiveFlags.length === 0 ? (
                  <p className="text-gray-500 text-sm">No positive signals recorded.</p>
                ) : (
                  <div className="space-y-3">
                    {positiveFlags.map((f, i) => (
                      <div key={i} className="border-l-4 border-emerald-500 pl-3 py-2">
                        <p className="text-white text-sm font-medium">{f.title}</p>
                        <div className="flex gap-3 text-xs text-gray-400 mt-1">
                          {f.flag_date && <span>Issued: {new Date(f.flag_date).toLocaleDateString()}</span>}
                          {f.expiry_date && <span>Expires: {new Date(f.expiry_date).toLocaleDateString()}</span>}
                          <span className={`font-semibold ${f.resolution_status === 'resolved' ? 'text-emerald-400' : 'text-amber-400'}`}>
                            {f.resolution_status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Risk Flags */}
              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-3">Risk Flags</h3>
                {negativeFlags.length === 0 ? (
                  <p className="text-gray-500 text-sm">No risk flags recorded.</p>
                ) : (
                  <div className="space-y-3">
                    {negativeFlags.map((f, i) => (
                      <div key={i} className="border-l-4 border-red-500 pl-3 py-2">
                        <p className="text-white text-sm font-medium">{f.title}</p>
                        <div className="flex gap-3 text-xs text-gray-400 mt-1">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                            f.severity === 'critical' ? 'bg-red-500/20 text-red-400' :
                            f.severity === 'high' ? 'bg-red-500/20 text-red-400' :
                            f.severity === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                            'bg-gray-500/20 text-gray-400'
                          }`}>
                            {f.severity}
                          </span>
                          <span className={`font-semibold ${f.resolution_status === 'resolved' ? 'text-emerald-400' : 'text-red-400'}`}>
                            {f.resolution_status}
                          </span>
                        </div>
                        {f.resolution_notes && (
                          <p className="text-gray-500 text-xs mt-1 italic">{f.resolution_notes}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Related Entities */}
            {vscore.relationships?.length > 0 && (
              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-4">Related Entities</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {vscore.relationships.map((r, i) => {
                    // Check if related entity has unresolved flags
                    const relatedNegFlags = (vscore.flags || []).filter(f => f.resolution_status !== 'resolved' && f.severity !== 'info');
                    return (
                      <div key={i} className="bg-[#0F172A] rounded-lg p-4 border border-gray-700/50">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="px-2 py-0.5 rounded text-xs font-bold bg-blue-500/20 text-blue-400 capitalize">
                            {r.relationship_type}
                          </span>
                          <span className="text-white font-medium">{r.related_entity_name}</span>
                        </div>
                        {r.notes && <p className="text-gray-400 text-sm">{r.notes}</p>}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Score History */}
            {vscore.score_history?.length > 0 && (
              <div className="bg-[#1E293B] rounded-xl p-6 shadow-lg">
                <h3 className="text-white font-semibold mb-3">Score History</h3>
                <div className="space-y-2">
                  {vscore.score_history.map((h, i) => (
                    <div key={i} className="flex items-center gap-4 p-3 bg-[#0F172A] rounded-lg">
                      <span className="text-lg font-bold" style={{ color: VSCORE_TIER_COLORS[h.tier] || '#94A3B8' }}>
                        {h.vscore}
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-xs font-bold" style={{
                        backgroundColor: `${VSCORE_TIER_COLORS[h.tier]}20`,
                        color: VSCORE_TIER_COLORS[h.tier] || '#94A3B8'
                      }}>
                        {VSCORE_TIER_LABELS[h.tier] || h.tier}
                      </span>
                      {h.score_change !== 0 && h.score_change != null && (
                        <span className={`text-xs font-bold ${h.score_change > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {h.score_change > 0 ? '+' : ''}{h.score_change}
                        </span>
                      )}
                      <span className="text-gray-500 text-xs ml-auto">
                        {h.created_at ? new Date(h.created_at).toLocaleDateString() : ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* vScore Formula Transparency */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <button
                onClick={() => setVscoreFormulaOpen(!vscoreFormulaOpen)}
                className="w-full flex items-center justify-between p-5 text-left hover:bg-gray-50 transition"
              >
                <span className="text-sm font-semibold text-ink">How is vScore calculated?</span>
                <span className="text-gray-400">{vscoreFormulaOpen ? '▾' : '▸'}</span>
              </button>
              {vscoreFormulaOpen && (
                <div className="px-5 pb-5 space-y-3">
                  {[
                    { label: 'Performance History', weight: 30, desc: 'Past engagement outcomes', color: '#3B82F6' },
                    { label: 'Proposal Quality', weight: 25, desc: 'AI evaluation scores and consistency', color: '#10B981' },
                    { label: 'Compliance & Governance', weight: 20, desc: 'DESC, ISO, data residency', color: '#F59E0B' },
                    { label: 'Claim Integrity', weight: 15, desc: 'Hallucination Shield grounding scores', color: '#8B5CF6' },
                    { label: 'Entity Intelligence', weight: 10, desc: 'Related company risks and tenure', color: '#EC4899' },
                  ].map((item) => (
                    <div key={item.label} className="flex flex-wrap sm:flex-nowrap items-center gap-2 sm:gap-3">
                      <div className="w-12 text-right text-sm font-bold" style={{ color: item.color }}>
                        {item.weight}%
                      </div>
                      <div className="flex-1 min-w-[80px]">
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${item.weight}%`, backgroundColor: item.color }} />
                        </div>
                      </div>
                      <div className="w-full sm:w-56">
                        <span className="text-sm text-gray-600">{item.label}</span>
                        <span className="text-xs text-gray-400 ml-1">— {item.desc}</span>
                      </div>
                    </div>
                  ))}
                  <p className="text-xs text-gray-400 italic mt-2 pt-2 border-t border-gray-100">
                    Score range: 300-900. Every component is traceable. σI — Added Intelligence.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Reputation Profile Section (legacy, shown if no vscore) */}
        {(!vscore || vscore.vscore == null) && reputation && reputation.reputation_score != null && (
          <div className="mb-6 space-y-4">
            <div className="bg-[#1E293B] rounded-xl p-5 md:p-8 shadow-lg">
              <div className="flex flex-col sm:flex-row items-center gap-4 sm:gap-8">
                <ReputationGauge score={reputation.reputation_score} tier={reputation.reputation_tier} size={96} />
                <div className="text-center sm:text-left">
                  <div className="flex items-center gap-3 mb-2">
                    <h2 className="text-2xl font-bold text-white">Reputation Profile</h2>
                    <span
                      className="px-3 py-1 rounded-full text-sm font-bold"
                      style={{ backgroundColor: `${REP_TIER_COLORS[reputation.reputation_tier]}20`, color: REP_TIER_COLORS[reputation.reputation_tier] || '#94A3B8' }}
                    >
                      {REP_TIER_LABELS[reputation.reputation_tier] || reputation.reputation_tier || 'N/A'}
                    </span>
                  </div>
                  <p className="text-gray-400 text-sm">
                    Based on {reputation.total_evaluations || 0} evaluation{reputation.total_evaluations !== 1 ? 's' : ''} across {reputation.submission_history?.length || 0} submission{(reputation.submission_history?.length || 0) !== 1 ? 's' : ''}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Existing Vendor Info */}
        <div className="bg-white rounded-xl shadow-sm p-5 md:p-8 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
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

          {currentUser?.role === 'admin' && (
            <div className="border-t pt-6 flex gap-4">
              <button
                onClick={() => {
                  if (window.confirm('Changes to vendor data will be logged to the audit trail. Proceed?')) {
                    navigate(`/vendors/${id}/edit`);
                  }
                }}
                className="bg-teal text-white py-2 px-6 rounded-lg font-semibold hover:bg-teal/90 transition-colors"
              >
                Admin Edit
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const EngagementNode = ({ engagement: e, outcomeColor }) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="relative pl-10">
      <div
        className="absolute left-2.5 top-4 w-3 h-3 rounded-full border-2"
        style={{ borderColor: outcomeColor, backgroundColor: `${outcomeColor}40` }}
      />
      <div
        className="bg-[#0F172A] rounded-lg p-4 border border-gray-700/50 cursor-pointer hover:border-gray-600 transition"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-gray-500 text-xs">
            {e.start_date ? new Date(e.start_date).toLocaleDateString() : '—'}
          </span>
          <span className="px-2 py-0.5 rounded text-xs font-bold bg-blue-500/20 text-blue-400 capitalize">
            {e.engagement_type}
          </span>
          <span className="text-white text-sm font-medium flex-1">{e.engagement_title}</span>
          <span
            className="px-2 py-0.5 rounded text-xs font-bold capitalize"
            style={{ backgroundColor: `${outcomeColor}20`, color: outcomeColor }}
          >
            {e.outcome}
          </span>
        </div>
        {expanded && (
          <div className="mt-3 pt-3 border-t border-gray-700/50 text-sm space-y-1">
            {e.delivery_rating != null && (
              <div className="flex items-center gap-2">
                <span className="text-gray-400">Delivery:</span>
                <StarRating rating={e.delivery_rating} />
              </div>
            )}
            {e.quality_rating != null && (
              <div className="flex items-center gap-2">
                <span className="text-gray-400">Quality:</span>
                <StarRating rating={e.quality_rating} />
              </div>
            )}
            {e.counterparty && <p className="text-gray-400">Counterparty: <span className="text-gray-300">{e.counterparty}</span></p>}
            {e.contract_value && <p className="text-gray-400">Value: <span className="text-gray-300">{e.contract_value}</span></p>}
            {e.notes && <p className="text-gray-500 italic">{e.notes}</p>}
          </div>
        )}
      </div>
    </div>
  );
};

export default VendorDetail;

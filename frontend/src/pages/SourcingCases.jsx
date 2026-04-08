import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { useUserRole } from '../lib/userRole';
import StatusBadge from '../components/StatusBadge';

/* ── Urgency badge colors ── */
const URGENCY_STYLES = {
  low: 'bg-gray-500/15 text-gray-400 border-gray-500/30',
  medium: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  high: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  critical: 'bg-red-500/15 text-red-400 border-red-500/30',
};

/* ── Source channel labels & styles ── */
const SOURCE_LABELS = {
  manual: 'Manual',
  business_in_dubai: 'Business in Dubai',
  expand_north_star: 'Expand North Star',
  ignyte: 'Ignyte',
  partner_referral: 'Partner Referral',
  email: 'Email',
  api: 'API',
};

const SOURCE_STYLES = {
  manual: 'bg-gray-100 text-gray-600 border-gray-200',
  business_in_dubai: 'bg-blue-100 text-blue-700 border-blue-200',
  expand_north_star: 'bg-purple-100 text-purple-700 border-purple-200',
  ignyte: 'bg-orange-100 text-orange-700 border-orange-200',
  partner_referral: 'bg-indigo-100 text-indigo-700 border-indigo-200',
  email: 'bg-sky-100 text-sky-700 border-sky-200',
  api: 'bg-emerald-100 text-emerald-700 border-emerald-200',
};

const SourceBadge = ({ source }) => {
  const label = SOURCE_LABELS[source] || source || 'Manual';
  const cls = SOURCE_STYLES[source] || SOURCE_STYLES.manual;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${cls}`}>
      {label}
    </span>
  );
};

const UrgencyBadge = ({ urgency }) => {
  const cls = URGENCY_STYLES[urgency] || URGENCY_STYLES.medium;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {(urgency || 'medium').charAt(0).toUpperCase() + (urgency || 'medium').slice(1)}
    </span>
  );
};

/* ── Status timeline ── */
const LIFECYCLE = ['intake', 'open', 'matching', 'evaluating', 'shortlisted', 'pilot', 'completed', 'closed'];

const StatusTimeline = ({ current }) => {
  const idx = LIFECYCLE.indexOf(current);
  return (
    <div className="flex items-center gap-1 mt-4">
      {LIFECYCLE.map((step, i) => {
        const done = i <= idx;
        const isCurrent = i === idx;
        return (
          <React.Fragment key={step}>
            <div className="flex flex-col items-center">
              <div
                className={`w-3.5 h-3.5 rounded-full border-2 transition-colors ${
                  isCurrent
                    ? 'bg-teal border-teal ring-2 ring-teal/30'
                    : done
                    ? 'bg-teal/70 border-teal/70'
                    : 'bg-gray-200 border-gray-300'
                }`}
              />
              <span className={`text-[9px] mt-1 whitespace-nowrap capitalize ${done ? 'text-ink/70 font-medium' : 'text-ink/40'}`}>
                {step}
              </span>
            </div>
            {i < LIFECYCLE.length - 1 && (
              <div className={`flex-1 h-0.5 min-w-[12px] mt-[-14px] ${i < idx ? 'bg-teal/60' : 'bg-gray-200'}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

/* ── Toast ── */
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);
  const bg = type === 'success' ? 'bg-emerald-600' : 'bg-red-600';
  return (
    <div className={`fixed top-6 right-6 z-50 ${bg} text-white px-6 py-3 rounded-lg shadow-2xl flex items-center gap-3`}>
      <span>{type === 'success' ? '✓' : '✕'}</span>
      <span>{message}</span>
      <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100">×</button>
    </div>
  );
};

/* ── Bullseye icon (target) ── */
const BullseyeIcon = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10" />
    <circle cx="12" cy="12" r="6" />
    <circle cx="12" cy="12" r="2" />
  </svg>
);

/* ═══════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════ */
const SourcingCases = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { role: userRole } = useUserRole();
  const canCreate = ['admin', 'analyst'].includes(userRole);

  const [loading, setLoading] = useState(true);
  const [cases, setCases] = useState([]);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  /* ── Detail view ── */
  const [selectedCase, setSelectedCase] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  /* ── Discovered vendors ── */
  const [discoveredVendors, setDiscoveredVendors] = useState([]);
  const [discoverLoading, setDiscoverLoading] = useState(false);
  const [matchFilter, setMatchFilter] = useState('all');

  /* ── Create modal ── */
  const [showCreate, setShowCreate] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [analysts, setAnalysts] = useState([]);
  const [businessGroups, setBusinessGroups] = useState([]);

  /* ── AI Assist ── */
  const [rawText, setRawText] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiReasoning, setAiReasoning] = useState('');
  const [showReasoning, setShowReasoning] = useState(false);
  const [aiApplied, setAiApplied] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    problem_statement: '',
    requesting_entity: '',
    sector: '',
    technology_domain: '',
    urgency: 'medium',
    compliance_requirements: '',
    assigned_analyst_id: '',
    business_group_id: '',
  });

  /* ── Status change modal ── */
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [updatingStatus, setUpdatingStatus] = useState(false);

  /* ── Duplicate check ── */
  const [dupCheckLoading, setDupCheckLoading] = useState(false);
  const [dupResults, setDupResults] = useState(null);
  const [showDupModal, setShowDupModal] = useState(false);
  const [merging, setMerging] = useState(false);

  /* ── Scan duplicates (admin) ── */
  const [scanLoading, setScanLoading] = useState(false);
  const [scanResults, setScanResults] = useState(null);
  const [showScanModal, setShowScanModal] = useState(false);

  /* ── Filters ── */
  const [filters, setFilters] = useState({
    status: searchParams.get('status') || '',
    sector: searchParams.get('sector') || '',
    urgency: searchParams.get('urgency') || '',
    source_channel: searchParams.get('source_channel') || '',
  });
  const [sortBy, setSortBy] = useState(searchParams.get('sort') || 'created_at');

  /* ── Fetch list ── */
  const fetchCases = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.sector) params.append('sector', filters.sector);
      if (filters.urgency) params.append('urgency', filters.urgency);
      if (filters.source_channel) params.append('source_channel', filters.source_channel);
      params.append('sort_by', sortBy);
      const res = await api.get(`/api/v1/sourcing-cases?${params.toString()}`);
      let list = res.data.sourcing_cases || [];
      if (sortBy === 'proposal_count') {
        list = [...list].sort((a, b) => (b.proposal_count || 0) - (a.proposal_count || 0));
      }
      setCases(list);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [filters, sortBy]);

  useEffect(() => { fetchCases(); }, [fetchCases]);

  /* ── Fetch analysts & business groups for the create modal ── */
  useEffect(() => {
    const load = async () => {
      try {
        const [aRes, bgRes] = await Promise.all([
          api.get('/api/v1/users?role=analyst'),
          api.get('/api/v1/business-groups'),
        ]);
        setAnalysts(aRes.data.users || aRes.data || []);
        setBusinessGroups(bgRes.data.business_groups || bgRes.data || []);
      } catch {
        // non-critical
      }
    };
    load();
  }, []);

  /* ── Filter handlers ── */
  const handleFilter = (key, value) => {
    const f = { ...filters, [key]: value };
    setFilters(f);
    const p = new URLSearchParams();
    if (f.status) p.set('status', f.status);
    if (f.sector) p.set('sector', f.sector);
    if (f.urgency) p.set('urgency', f.urgency);
    if (f.source_channel) p.set('source_channel', f.source_channel);
    if (sortBy !== 'created_at') p.set('sort', sortBy);
    setSearchParams(p);
  };

  const handleSort = (val) => {
    setSortBy(val);
    const p = new URLSearchParams(searchParams);
    if (val !== 'created_at') p.set('sort', val);
    else p.delete('sort');
    setSearchParams(p);
  };

  /* ── Create (with duplicate check) ── */
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!formData.title.trim() || !formData.problem_statement.trim()) return;

    // Step 1: Check for duplicates before creating
    try {
      setDupCheckLoading(true);
      const checkRes = await api.post('/api/v1/sourcing-cases/check-duplicate', {
        title: formData.title.trim(),
        problem_statement: formData.problem_statement.trim(),
        sector: formData.sector || undefined,
        technology_domain: formData.technology_domain || undefined,
      });
      const dupData = checkRes.data;
      if (dupData.duplicates_found && dupData.matches && dupData.matches.length > 0) {
        setDupResults(dupData);
        setShowDupModal(true);
        setDupCheckLoading(false);
        return; // Wait for user decision
      }
    } catch {
      // If duplicate check fails, proceed with creation anyway
    } finally {
      setDupCheckLoading(false);
    }

    // No duplicates found — proceed with creation
    await doCreateCase();
  };

  const doCreateCase = async () => {
    try {
      setSubmitting(true);
      const body = { ...formData };
      Object.keys(body).forEach(k => { if (!body[k]) delete body[k]; });
      await api.post('/api/v1/sourcing-cases', body);
      setToast({ message: 'Sourcing case created successfully', type: 'success' });
      setShowCreate(false);
      setShowDupModal(false);
      setDupResults(null);
      setFormData({
        title: '', problem_statement: '', requesting_entity: '', sector: '',
        technology_domain: '', urgency: 'medium', compliance_requirements: '',
        assigned_analyst_id: '', business_group_id: '',
      });
      setRawText('');
      setAiReasoning('');
      setAiApplied(false);
      setShowReasoning(false);
      fetchCases();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  /* ── Merge with existing case ── */
  const handleMergeWithExisting = async (targetCaseId) => {
    // "Merge" here means: don't create the new case, just navigate to the existing one
    setShowDupModal(false);
    setShowCreate(false);
    setDupResults(null);
    setToast({ message: 'Navigated to existing case instead of creating duplicate', type: 'success' });
    openDetail(targetCaseId);
  };

  /* ── Merge two existing cases (from scan results) ── */
  const handleMergeCases = async (sourceId, targetId) => {
    try {
      setMerging(true);
      await api.post(`/api/v1/sourcing-cases/${sourceId}/merge/${targetId}`);
      setToast({ message: 'Cases merged successfully', type: 'success' });
      setShowScanModal(false);
      setScanResults(null);
      fetchCases();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setMerging(false);
    }
  };

  /* ── Scan all open cases for duplicates (admin) ── */
  const handleScanDuplicates = async () => {
    try {
      setScanLoading(true);
      const res = await api.post('/api/v1/sourcing-cases/scan-duplicates');
      setScanResults(res.data);
      setShowScanModal(true);
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setScanLoading(false);
    }
  };

  /* ── AI Assist handler ── */
  const handleAiAssist = async () => {
    if (!rawText.trim() || rawText.trim().length < 10) {
      setToast({ message: 'Please enter at least 10 characters of text to analyze', type: 'error' });
      return;
    }
    try {
      setAiLoading(true);
      const res = await api.post('/api/v1/sourcing-cases/ai-structure', { raw_text: rawText });
      const data = res.data;
      setFormData(f => ({
        ...f,
        title: data.suggested_title || f.title,
        problem_statement: data.problem_statement || f.problem_statement,
        sector: data.sector || f.sector,
        technology_domain: data.technology_domain || f.technology_domain,
        urgency: data.urgency || f.urgency,
        compliance_requirements: (data.compliance_flags || []).join(', ') || f.compliance_requirements,
      }));
      setAiReasoning(data.reasoning || '');
      setAiApplied(true);
      setShowReasoning(true);
      setToast({ message: 'AI analysis complete — fields auto-filled', type: 'success' });
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setAiLoading(false);
    }
  };

  /* ── Detail ── */
  const openDetail = async (caseId) => {
    try {
      setDetailLoading(true);
      const res = await api.get(`/api/v1/sourcing-cases/${caseId}`);
      setSelectedCase(res.data);
      fetchMatchedVendors(caseId);
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setDetailLoading(false);
    }
  };

  /* ── Status update ── */
  const handleStatusUpdate = async () => {
    if (!selectedCase || !newStatus) return;
    try {
      setUpdatingStatus(true);
      await api.put(`/api/v1/sourcing-cases/${selectedCase.id}/status`, { status: newStatus });
      setToast({ message: `Status updated to "${newStatus}"`, type: 'success' });
      setShowStatusModal(false);
      // Refresh detail
      openDetail(selectedCase.id);
      fetchCases();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setUpdatingStatus(false);
    }
  };

  /* ── Fetch cached matched vendors ── */
  const fetchMatchedVendors = useCallback(async (caseId) => {
    try {
      const res = await api.get(`/api/v1/sourcing-cases/${caseId}/matched-vendors`);
      setDiscoveredVendors(res.data.matched_vendors || []);
    } catch {
      // not critical — may not have matches yet
      setDiscoveredVendors([]);
    }
  }, []);

  /* ── Discover vendors (AI matching) ── */
  const handleDiscoverVendors = async () => {
    if (!selectedCase) return;
    try {
      setDiscoverLoading(true);
      const res = await api.post(`/api/v1/sourcing-cases/${selectedCase.id}/discover-vendors`);
      setDiscoveredVendors(res.data.matched_vendors || []);
      setToast({ message: `Discovered ${res.data.count || 0} matching vendors`, type: 'success' });
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setDiscoverLoading(false);
    }
  };

  /* ── Invite vendor (update match status) ── */
  const handleInviteVendor = async (matchId) => {
    try {
      await api.put(`/api/v1/sourcing-cases/vendor-matches/${matchId}/status`, { status: 'invited' });
      setDiscoveredVendors(prev => prev.map(m => m.id === matchId ? { ...m, status: 'invited' } : m));
      setToast({ message: 'Vendor invited to submit', type: 'success' });
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    }
  };

  /* ═══════ RENDER ═══════ */

  /* ── Detail view ── */
  if (selectedCase) {
    return (
      <div className="min-h-screen">
        {toast && <Toast {...toast} onClose={() => setToast(null)} />}

        {/* Back button */}
        <button
          onClick={() => setSelectedCase(null)}
          className="mb-4 text-teal hover:underline font-body text-sm flex items-center gap-1"
        >
          ← Back to Sourcing Cases
        </button>

        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-teal"><BullseyeIcon size={24} /></span>
                <h1 className="font-heading text-2xl md:text-3xl text-ink truncate">{selectedCase.title}</h1>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                <StatusBadge status={selectedCase.status} />
                <UrgencyBadge urgency={selectedCase.urgency} />
                {selectedCase.source_channel && (
                  <SourceBadge source={selectedCase.source_channel} />
                )}
                {selectedCase.sector && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-teal/10 text-teal border border-teal/20">
                    {selectedCase.sector}
                  </span>
                )}
                {selectedCase.technology_domain && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gold/10 text-gold border border-gold/20">
                    {selectedCase.technology_domain}
                  </span>
                )}
              </div>
            </div>
            {canCreate && (
              <button
                onClick={() => { setNewStatus(selectedCase.status); setShowStatusModal(true); }}
                className="px-4 py-2 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 transition-colors"
              >
                Change Status
              </button>
            )}
          </div>

          <StatusTimeline current={selectedCase.status} />

          {/* Details grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
            <div>
              <h3 className="font-body text-xs text-ink/50 uppercase tracking-wider mb-1">Problem Statement</h3>
              <p className="text-ink font-body text-sm whitespace-pre-wrap">{selectedCase.problem_statement}</p>
            </div>
            <div className="space-y-3">
              {selectedCase.requesting_entity && (
                <div>
                  <h3 className="font-body text-xs text-ink/50 uppercase tracking-wider mb-1">Requesting Entity</h3>
                  <p className="text-ink font-body text-sm">{selectedCase.requesting_entity}</p>
                </div>
              )}
              {selectedCase.compliance_requirements && (
                <div>
                  <h3 className="font-body text-xs text-ink/50 uppercase tracking-wider mb-1">Compliance Requirements</h3>
                  <p className="text-ink font-body text-sm whitespace-pre-wrap">{selectedCase.compliance_requirements}</p>
                </div>
              )}
              {selectedCase.assigned_analyst && (
                <div>
                  <h3 className="font-body text-xs text-ink/50 uppercase tracking-wider mb-1">Assigned Analyst</h3>
                  <p className="text-ink font-body text-sm">{selectedCase.assigned_analyst.email}</p>
                </div>
              )}
              <div>
                <h3 className="font-body text-xs text-ink/50 uppercase tracking-wider mb-1">Created</h3>
                <p className="text-ink font-body text-sm">{new Date(selectedCase.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Linked Proposals */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-heading text-xl text-ink">Linked Proposals ({selectedCase.proposals?.length || 0})</h2>
            <button
              onClick={() => navigate(`/proposals?sourcing_case=${selectedCase.id}`)}
              className="text-teal text-sm hover:underline font-body"
            >
              View in Proposals →
            </button>
          </div>
          {(selectedCase.proposals?.length || 0) === 0 ? (
            <p className="text-ink/50 font-body text-sm">No proposals linked to this case yet.</p>
          ) : (
            <div className="space-y-3">
              {selectedCase.proposals.map(p => (
                <div
                  key={p.id}
                  onClick={() => navigate(`/proposals/${p.id}`)}
                  className="flex items-center justify-between p-3 rounded-lg border border-ink/10 hover:border-teal/30 hover:bg-teal/5 cursor-pointer transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <p className="font-body text-sm font-medium text-ink truncate">{p.title}</p>
                    <div className="flex gap-2 mt-1">
                      <StatusBadge status={p.status} />
                      {p.sector && (
                        <span className="text-xs text-ink/50">{p.sector}</span>
                      )}
                    </div>
                  </div>
                  {p.composite_score != null && (
                    <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${
                      p.composite_score > 70 ? 'bg-emerald-100 text-emerald-700' :
                      p.composite_score >= 40 ? 'bg-amber-100 text-amber-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {p.composite_score.toFixed(1)}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* AI-Discovered Matches */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-1">
            <h2 className="font-heading text-xl text-ink">AI-Discovered Matches</h2>
            {canCreate && (
              <button
                onClick={handleDiscoverVendors}
                disabled={discoverLoading}
                className="px-4 py-2 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 disabled:opacity-50 transition-colors flex items-center gap-2"
              >
                {discoverLoading ? (
                  <>
                    <span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
                    Discovering...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                    </svg>
                    Discover Matching Vendors
                  </>
                )}
              </button>
            )}
          </div>
          <p className="text-xs text-ink/40 font-body mb-4">
            AI-Discovered Matches — σI identifies vendors whose capabilities align with this sourcing need
          </p>

          {/* Filter tabs */}
          {discoveredVendors.length > 0 && (
            <div className="flex gap-2 mb-4">
              {['all', 'suggested', 'invited', 'submitted'].map(f => (
                <button
                  key={f}
                  onClick={() => setMatchFilter(f)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                    matchFilter === f
                      ? 'bg-teal text-white border-teal'
                      : 'bg-white text-ink/60 border-ink/15 hover:border-teal/30'
                  }`}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                  {f !== 'all' && (
                    <span className="ml-1 opacity-70">
                      ({discoveredVendors.filter(m => m.status === f).length})
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}

          {discoveredVendors.length === 0 ? (
            <p className="text-ink/50 font-body text-sm">
              No discovered vendors yet. Click "Discover Matching Vendors" to run AI matching.
            </p>
          ) : (
            <div className="space-y-3">
              {discoveredVendors
                .filter(m => matchFilter === 'all' || m.status === matchFilter)
                .map((m, idx) => (
                <div
                  key={m.id}
                  className="p-4 rounded-lg border border-ink/10 hover:border-teal/20 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-ink/40 font-body font-bold">#{idx + 1}</span>
                        <span
                          onClick={() => navigate(`/vendors/${m.vendor_id}`)}
                          className="font-body text-sm font-semibold text-ink hover:text-teal cursor-pointer"
                        >
                          {m.vendor_name || 'Unknown Vendor'}
                        </span>
                        {/* vScore badge */}
                        {m.vendor_vscore != null && (
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            m.vendor_vscore >= 800 ? 'bg-emerald-100 text-emerald-700' :
                            m.vendor_vscore >= 600 ? 'bg-amber-100 text-amber-700' :
                            'bg-gray-100 text-gray-600'
                          }`}>
                            vScore: {m.vendor_vscore}
                          </span>
                        )}
                        {/* DESC badge */}
                        {m.vendor_desc_certified && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-700">
                            DESC
                          </span>
                        )}
                        {/* Status badge */}
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${
                          m.status === 'invited' ? 'bg-blue-50 text-blue-600 border-blue-200' :
                          m.status === 'submitted' ? 'bg-emerald-50 text-emerald-600 border-emerald-200' :
                          m.status === 'declined' ? 'bg-red-50 text-red-600 border-red-200' :
                          'bg-gray-50 text-gray-500 border-gray-200'
                        }`}>
                          {m.status}
                        </span>
                      </div>
                      {/* Match score bar */}
                      <div className="flex items-center gap-2 mb-1.5">
                        <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden max-w-[180px]">
                          <div
                            className={`h-full rounded-full ${
                              m.match_score >= 80 ? 'bg-emerald-500' :
                              m.match_score >= 60 ? 'bg-amber-500' :
                              'bg-red-400'
                            }`}
                            style={{ width: `${Math.min(m.match_score || 0, 100)}%` }}
                          />
                        </div>
                        <span className={`text-xs font-bold ${
                          m.match_score >= 80 ? 'text-emerald-600' :
                          m.match_score >= 60 ? 'text-amber-600' :
                          'text-red-500'
                        }`}>
                          {m.match_score}/100
                        </span>
                        {m.avg_evaluation_score != null && (
                          <span className="text-xs text-ink/40 ml-2">
                            Avg eval: {m.avg_evaluation_score}
                          </span>
                        )}
                      </div>
                      {/* Reasoning */}
                      {m.match_reasoning && (
                        <p className="text-xs text-ink/60 font-body">{m.match_reasoning}</p>
                      )}
                    </div>
                    {/* Invite button */}
                    {canCreate && m.status === 'suggested' && (
                      <button
                        onClick={() => handleInviteVendor(m.id)}
                        className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition-colors whitespace-nowrap"
                      >
                        Invite to Submit
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Status change modal */}
        {showStatusModal && (
          <div className="fixed inset-0 bg-ink/50 z-50 flex items-center justify-center p-4" onClick={() => setShowStatusModal(false)}>
            <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
              <h2 className="font-heading text-xl text-ink mb-4">Change Status</h2>
              <select
                value={newStatus}
                onChange={e => setNewStatus(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal mb-4"
              >
                {LIFECYCLE.map(s => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
              <div className="flex gap-3">
                <button
                  onClick={handleStatusUpdate}
                  disabled={updatingStatus || newStatus === selectedCase.status}
                  className="flex-1 bg-teal text-white py-2.5 rounded-lg font-semibold hover:bg-teal/90 disabled:opacity-50 transition-colors"
                >
                  {updatingStatus ? 'Updating...' : 'Update'}
                </button>
                <button
                  onClick={() => setShowStatusModal(false)}
                  className="flex-1 bg-gray-200 text-ink py-2.5 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  /* ── List view ── */
  return (
    <div className="min-h-screen">
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}

      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <span className="text-teal"><BullseyeIcon size={28} /></span>
          <h1 className="font-heading text-3xl md:text-4xl text-ink">Sourcing Cases</h1>
        </div>
        <div className="flex items-center gap-3">
          {userRole === 'admin' && (
            <button
              onClick={handleScanDuplicates}
              disabled={scanLoading}
              className="px-4 py-2.5 bg-amber-500 text-white rounded-lg font-body text-sm font-semibold hover:bg-amber-600 disabled:opacity-50 transition-colors flex items-center gap-2"
            >
              {scanLoading ? (
                <>
                  <span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
                  Scanning...
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M16 16v1a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h2"/>
                    <rect x="8" y="2" width="14" height="14" rx="2"/>
                  </svg>
                  Check Duplicates
                </>
              )}
            </button>
          )}
          {canCreate && (
            <button
              onClick={() => setShowCreate(true)}
              className="px-5 py-2.5 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 transition-colors flex items-center gap-2"
            >
              <span className="text-lg leading-none">+</span> Create New Case
            </button>
          )}
        </div>
      </div>

      {/* Filter bar */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6 flex flex-wrap gap-3 items-center">
        <select
          value={filters.status}
          onChange={e => handleFilter('status', e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal"
        >
          <option value="">All Statuses</option>
          {LIFECYCLE.map(s => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>
        <select
          value={filters.sector}
          onChange={e => handleFilter('sector', e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal"
        >
          <option value="">All Sectors</option>
          {businessGroups.map(bg => (
            <option key={bg.id} value={bg.name || bg.sector_name}>{bg.name || bg.sector_name}</option>
          ))}
          <option value="fintech">FinTech</option>
          <option value="healthcare">Healthcare</option>
          <option value="logistics">Logistics</option>
          <option value="energy">Energy</option>
          <option value="education">Education</option>
          <option value="government">Government</option>
          <option value="tourism">Tourism</option>
        </select>
        <select
          value={filters.urgency}
          onChange={e => handleFilter('urgency', e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal"
        >
          <option value="">All Urgency</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
          <option value="critical">Critical</option>
        </select>
        <select
          value={filters.source_channel}
          onChange={e => handleFilter('source_channel', e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal"
        >
          <option value="">All Sources</option>
          {Object.entries(SOURCE_LABELS).map(([key, label]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-ink/50 font-body">Sort:</span>
          <select
            value={sortBy}
            onChange={e => handleSort(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal"
          >
            <option value="created_at">Newest</option>
            <option value="urgency">Urgency</option>
            <option value="proposal_count">Most Proposals</option>
          </select>
        </div>
      </div>

      {/* Loading / error */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-teal"></div>
        </div>
      )}

      {error && (
        <div className="p-4 bg-burgundy/10 border border-burgundy rounded-lg text-burgundy mb-6">
          {error}
        </div>
      )}

      {/* Card grid */}
      {!loading && !error && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cases.length === 0 ? (
            <div className="col-span-full text-center py-16">
              <span className="text-ink/30 text-5xl"><BullseyeIcon size={48} /></span>
              <p className="text-ink/50 font-body mt-4">No sourcing cases found.</p>
              {canCreate && (
                <button
                  onClick={() => setShowCreate(true)}
                  className="mt-4 px-5 py-2.5 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 transition-colors"
                >
                  Create First Case
                </button>
              )}
            </div>
          ) : (
            cases.map(c => (
              <div
                key={c.id}
                onClick={() => openDetail(c.id)}
                className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition cursor-pointer border border-transparent hover:border-teal/30 flex flex-col"
              >
                {/* Title */}
                <h3 className="font-heading text-lg text-ink mb-2 line-clamp-2">{c.title}</h3>

                {/* Requesting entity */}
                {c.requesting_entity && (
                  <p className="text-xs text-ink/50 font-body mb-2">{c.requesting_entity}</p>
                )}

                {/* Badges */}
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {c.source_channel && c.source_channel !== 'manual' && (
                    <SourceBadge source={c.source_channel} />
                  )}
                  {c.sector && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-teal/10 text-teal">
                      {c.sector}
                    </span>
                  )}
                  <UrgencyBadge urgency={c.urgency} />
                  <StatusBadge status={c.status} />
                </div>

                {/* Footer */}
                <div className="mt-auto pt-3 border-t border-ink/5 flex items-center justify-between text-xs text-ink/50 font-body">
                  <span>{new Date(c.created_at).toLocaleDateString()}</span>
                  <span className="flex items-center gap-1">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    {c.proposal_count || 0} proposals
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {detailLoading && (
        <div className="fixed inset-0 bg-ink/30 z-50 flex items-center justify-center">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-teal"></div>
        </div>
      )}

      {/* ── Create Modal ── */}
      {showCreate && (
        <div className="fixed inset-0 bg-ink/50 z-50 flex items-center justify-center p-4 overflow-y-auto" onClick={() => setShowCreate(false)}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-2xl my-8" onClick={e => e.stopPropagation()}>
            <h2 className="font-heading text-2xl text-ink mb-6">Create Sourcing Case</h2>

            {/* ── AI Assist Section ── */}
            <div className="mb-6 p-4 bg-gradient-to-r from-teal/5 to-teal/10 border border-teal/20 rounded-xl">
              <label className="block text-ink font-body font-semibold mb-1 text-sm">
                Paste raw request (email, referral, brief description)
              </label>
              <textarea
                value={rawText}
                onChange={e => setRawText(e.target.value)}
                rows={4}
                className="w-full px-4 py-2.5 border border-teal/30 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal text-sm bg-white"
                placeholder="Paste an email, referral note, or brief description here and let AI extract the structured fields..."
              />
              <button
                type="button"
                onClick={handleAiAssist}
                disabled={aiLoading || !rawText.trim()}
                className="mt-2 px-5 py-2.5 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 disabled:opacity-50 transition-colors flex items-center gap-2"
              >
                {aiLoading ? (
                  <>
                    <span className="animate-spin inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full"></span>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 2a4 4 0 0 1 4 4c0 1.95-1.4 3.58-3.25 3.93L12 22"/>
                      <path d="M12 2a4 4 0 0 0-4 4c0 1.95 1.4 3.58 3.25 3.93"/>
                      <path d="M8.56 13.68C5.49 15.19 3.2 18.05 3.2 21.6"/>
                      <path d="M15.44 13.68c3.07 1.51 5.36 4.37 5.36 7.92"/>
                    </svg>
                    AI Assist — Structure This Request
                  </>
                )}
              </button>

              {/* AI Reasoning collapsible */}
              {aiReasoning && (
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={() => setShowReasoning(r => !r)}
                    className="text-teal text-xs font-body font-medium hover:underline flex items-center gap-1"
                  >
                    <span className={`inline-block transition-transform ${showReasoning ? 'rotate-90' : ''}`}>▶</span>
                    AI Reasoning
                  </button>
                  {showReasoning && (
                    <div className="mt-2 p-3 bg-white/80 rounded-lg border border-teal/10 text-xs text-ink/70 font-body">
                      {aiReasoning}
                    </div>
                  )}
                </div>
              )}

              {aiApplied && (
                <p className="mt-2 text-xs text-ink/50 font-body">
                  AI-suggested. Review before saving.
                </p>
              )}
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              {/* Title */}
              <div>
                <label className="block text-ink font-body font-semibold mb-1 text-sm">Title *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={e => setFormData(f => ({ ...f, title: e.target.value }))}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal text-sm"
                  placeholder="e.g. Smart Water Monitoring Solution"
                  required
                />
              </div>

              {/* Problem Statement */}
              <div>
                <label className="block text-ink font-body font-semibold mb-1 text-sm">Problem Statement *</label>
                <textarea
                  value={formData.problem_statement}
                  onChange={e => setFormData(f => ({ ...f, problem_statement: e.target.value }))}
                  rows={3}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal text-sm"
                  placeholder="Describe the need or opportunity..."
                  required
                />
              </div>

              {/* Two-col row */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-ink font-body font-semibold mb-1 text-sm">Requesting Entity</label>
                  <input
                    type="text"
                    value={formData.requesting_entity}
                    onChange={e => setFormData(f => ({ ...f, requesting_entity: e.target.value }))}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal text-sm"
                    placeholder="e.g. Dubai Municipality, DEWA"
                  />
                </div>
                <div>
                  <label className="block text-ink font-body font-semibold mb-1 text-sm">Sector</label>
                  <select
                    value={formData.sector}
                    onChange={e => setFormData(f => ({ ...f, sector: e.target.value }))}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal text-sm"
                  >
                    <option value="">Select sector...</option>
                    {businessGroups.map(bg => (
                      <option key={bg.id} value={bg.name || bg.sector_name}>{bg.name || bg.sector_name}</option>
                    ))}
                    <option value="fintech">FinTech</option>
                    <option value="healthcare">Healthcare</option>
                    <option value="logistics">Logistics</option>
                    <option value="energy">Energy</option>
                    <option value="education">Education</option>
                    <option value="government">Government</option>
                    <option value="tourism">Tourism</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-ink font-body font-semibold mb-1 text-sm">Technology Domain</label>
                  <input
                    type="text"
                    value={formData.technology_domain}
                    onChange={e => setFormData(f => ({ ...f, technology_domain: e.target.value }))}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal text-sm"
                    placeholder="e.g. Cybersecurity, AI/ML, IoT"
                  />
                </div>
                <div>
                  <label className="block text-ink font-body font-semibold mb-1 text-sm">Urgency</label>
                  <select
                    value={formData.urgency}
                    onChange={e => setFormData(f => ({ ...f, urgency: e.target.value }))}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal text-sm"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </div>

              {/* Compliance */}
              <div>
                <label className="block text-ink font-body font-semibold mb-1 text-sm">Compliance Requirements</label>
                <textarea
                  value={formData.compliance_requirements}
                  onChange={e => setFormData(f => ({ ...f, compliance_requirements: e.target.value }))}
                  rows={2}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal text-sm"
                  placeholder="e.g. Must be DESC certified"
                />
              </div>

              {/* Assign analyst */}
              <div>
                <label className="block text-ink font-body font-semibold mb-1 text-sm">Assign Analyst</label>
                <select
                  value={formData.assigned_analyst_id}
                  onChange={e => setFormData(f => ({ ...f, assigned_analyst_id: e.target.value }))}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal text-sm"
                >
                  <option value="">None</option>
                  {analysts.map(a => (
                    <option key={a.id} value={a.id}>{a.email}{a.full_name ? ` (${a.full_name})` : ''}</option>
                  ))}
                </select>
              </div>

              {/* Actions */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={submitting || dupCheckLoading}
                  className="flex-1 bg-teal text-white py-2.5 rounded-lg font-semibold hover:bg-teal/90 disabled:opacity-50 transition-colors"
                >
                  {dupCheckLoading ? 'Checking for duplicates...' : submitting ? 'Creating...' : 'Create Case'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="flex-1 bg-gray-200 text-ink py-2.5 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Duplicate Check Modal ── */}
      {showDupModal && dupResults && (
        <div className="fixed inset-0 bg-ink/50 z-50 flex items-center justify-center p-4 overflow-y-auto" onClick={() => { setShowDupModal(false); setDupResults(null); }}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-xl my-8" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <span className="text-amber-500 text-2xl">&#9888;</span>
              <h2 className="font-heading text-xl text-ink">Similar Case Detected</h2>
            </div>
            <p className="text-sm text-ink/60 font-body mb-4">
              We found {dupResults.matches.length} existing case{dupResults.matches.length !== 1 ? 's' : ''} that may overlap with your new case.
              {dupResults.recommendation === 'merge' && ' We recommend merging with the existing case.'}
              {dupResults.recommendation === 'review' && ' Please review before proceeding.'}
            </p>

            <div className="space-y-3 mb-6 max-h-64 overflow-y-auto">
              {dupResults.matches.map(m => (
                <div key={m.case_id} className="p-4 rounded-lg border border-ink/10 bg-gray-50">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="font-body text-sm font-semibold text-ink">{m.title}</p>
                      <div className="flex flex-wrap gap-1.5 mt-1.5">
                        <StatusBadge status={m.status} />
                        {m.sector && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-teal/10 text-teal">
                            {m.sector}
                          </span>
                        )}
                        {m.source_channel && (
                          <SourceBadge source={m.source_channel} />
                        )}
                      </div>
                      <p className="text-xs text-ink/50 font-body mt-2">{m.reasoning}</p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        m.similarity_score >= 85 ? 'bg-red-100 text-red-700' :
                        m.similarity_score >= 60 ? 'bg-amber-100 text-amber-700' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {m.similarity_score}% match
                      </span>
                      {userRole === 'admin' && (
                        <button
                          onClick={() => handleMergeWithExisting(m.case_id)}
                          className="mt-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 transition-colors whitespace-nowrap"
                        >
                          View Existing
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => { setShowDupModal(false); setDupResults(null); doCreateCase(); }}
                disabled={submitting}
                className="flex-1 bg-teal text-white py-2.5 rounded-lg font-semibold hover:bg-teal/90 disabled:opacity-50 transition-colors text-sm"
              >
                {submitting ? 'Creating...' : 'Create Anyway'}
              </button>
              <button
                onClick={() => { setShowDupModal(false); setDupResults(null); }}
                className="flex-1 bg-gray-200 text-ink py-2.5 rounded-lg font-semibold hover:bg-gray-300 transition-colors text-sm"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Scan Duplicates Results Modal ── */}
      {showScanModal && scanResults && (
        <div className="fixed inset-0 bg-ink/50 z-50 flex items-center justify-center p-4 overflow-y-auto" onClick={() => { setShowScanModal(false); setScanResults(null); }}>
          <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-2xl my-8" onClick={e => e.stopPropagation()}>
            <h2 className="font-heading text-xl text-ink mb-2">Duplicate Scan Results</h2>
            <p className="text-sm text-ink/50 font-body mb-4">
              Scanned {scanResults.total_cases_scanned} open cases. Found {scanResults.groups?.length || 0} potential duplicate group{(scanResults.groups?.length || 0) !== 1 ? 's' : ''}.
            </p>

            {(!scanResults.groups || scanResults.groups.length === 0) ? (
              <div className="text-center py-8">
                <span className="text-4xl">&#10003;</span>
                <p className="text-ink/60 font-body mt-2">No duplicate cases detected.</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {scanResults.groups.map((group, gi) => (
                  <div key={gi} className="p-4 rounded-lg border border-amber-200 bg-amber-50/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        group.similarity_score >= 85 ? 'bg-red-100 text-red-700' :
                        'bg-amber-100 text-amber-700'
                      }`}>
                        {group.similarity_score}% similar
                      </span>
                    </div>
                    <div className="space-y-2 mb-3">
                      {group.cases.map(c => (
                        <div key={c.case_id} className="flex items-center justify-between p-2 bg-white rounded-lg border border-ink/5">
                          <div className="min-w-0 flex-1">
                            <p className="font-body text-sm font-medium text-ink truncate">{c.title}</p>
                            <div className="flex gap-1.5 mt-1">
                              <StatusBadge status={c.status} />
                              {c.sector && (
                                <span className="text-[10px] text-ink/50">{c.sector}</span>
                              )}
                              {c.source_channel && (
                                <SourceBadge source={c.source_channel} />
                              )}
                            </div>
                          </div>
                          <button
                            onClick={() => { setShowScanModal(false); setScanResults(null); openDetail(c.case_id); }}
                            className="ml-2 text-teal text-xs hover:underline font-body whitespace-nowrap"
                          >
                            View
                          </button>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-ink/50 font-body mb-3">{group.reasoning}</p>
                    {group.cases.length === 2 && (
                      <button
                        onClick={() => handleMergeCases(group.cases[1].case_id, group.cases[0].case_id)}
                        disabled={merging}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg text-xs font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
                      >
                        {merging ? 'Merging...' : `Merge into "${group.cases[0].title.substring(0, 40)}..."`}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}

            <div className="mt-4 pt-4 border-t border-ink/10">
              <button
                onClick={() => { setShowScanModal(false); setScanResults(null); }}
                className="w-full bg-gray-200 text-ink py-2.5 rounded-lg font-semibold hover:bg-gray-300 transition-colors text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SourcingCases;

import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { useUserRole } from '../lib/userRole';

/* ── Status styles ── */
const STATUS_STYLES = {
  setup: 'bg-amber-500/15 text-amber-600 border-amber-500/30',
  active: 'bg-teal/15 text-teal border-teal/30',
  completed: 'bg-emerald-500/15 text-emerald-600 border-emerald-500/30',
  cancelled: 'bg-red-500/15 text-red-600 border-red-500/30',
  extended: 'bg-purple-500/15 text-purple-600 border-purple-500/30',
};

const PilotStatusBadge = ({ status }) => {
  const cls = STATUS_STYLES[status] || STATUS_STYLES.setup;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {(status || 'setup').charAt(0).toUpperCase() + (status || 'setup').slice(1)}
    </span>
  );
};

/* ── Adoption decision styles ── */
const ADOPTION_STYLES = {
  adopt: 'bg-emerald-600 text-white',
  extend: 'bg-purple-600 text-white',
  pivot: 'bg-amber-600 text-white',
  terminate: 'bg-red-600 text-white',
  pending: 'bg-gray-400 text-white',
};

/* ── Status timeline ── */
const LIFECYCLE = ['setup', 'active', 'completed'];

const StatusTimeline = ({ current }) => {
  const idx = LIFECYCLE.indexOf(current);
  const effectiveIdx = current === 'extended' ? 1 : current === 'cancelled' ? -1 : idx;
  return (
    <div className="flex items-center gap-1 mt-4">
      {LIFECYCLE.map((step, i) => {
        const done = i <= effectiveIdx;
        const isCurrent = i === effectiveIdx;
        return (
          <React.Fragment key={step}>
            <div className="flex flex-col items-center">
              <div
                className={`w-4 h-4 rounded-full border-2 transition-colors ${
                  isCurrent
                    ? 'bg-teal border-teal ring-2 ring-teal/30'
                    : done
                    ? 'bg-teal/70 border-teal/70'
                    : 'bg-gray-200 border-gray-300'
                }`}
              />
              <span className={`text-[10px] mt-1 whitespace-nowrap capitalize ${done ? 'text-ink/70 font-medium' : 'text-ink/40'}`}>
                {step}
              </span>
            </div>
            {i < LIFECYCLE.length - 1 && (
              <div className={`flex-1 h-0.5 min-w-[18px] mt-[-14px] ${i < effectiveIdx ? 'bg-teal/60' : 'bg-gray-200'}`} />
            )}
          </React.Fragment>
        );
      })}
      {(current === 'cancelled' || current === 'extended') && (
        <div className="flex flex-col items-center ml-2">
          <div className={`w-4 h-4 rounded-full border-2 ${current === 'cancelled' ? 'bg-red-500 border-red-500' : 'bg-purple-500 border-purple-500'}`} />
          <span className={`text-[10px] mt-1 whitespace-nowrap capitalize ${current === 'cancelled' ? 'text-red-600' : 'text-purple-600'} font-medium`}>
            {current}
          </span>
        </div>
      )}
    </div>
  );
};

/* ── Star rating ── */
const StarRating = ({ rating, onChange, readonly = false }) => {
  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          disabled={readonly}
          onClick={() => onChange && onChange(star)}
          className={`text-lg ${readonly ? 'cursor-default' : 'cursor-pointer hover:scale-110'} transition-transform ${
            star <= (rating || 0) ? 'text-amber-400' : 'text-gray-300'
          }`}
        >
          ★
        </button>
      ))}
    </div>
  );
};

/* ── Budget progress bar ── */
const BudgetBar = ({ allocated, spent }) => {
  if (!allocated) return null;
  const pct = Math.min(100, Math.round(((spent || 0) / allocated) * 100));
  const color = pct > 90 ? 'bg-red-500' : pct > 70 ? 'bg-amber-500' : 'bg-teal';
  return (
    <div>
      <div className="flex justify-between text-xs text-ink/60 mb-1">
        <span>Budget: {(spent || 0).toLocaleString()} / {allocated.toLocaleString()}</span>
        <span>{pct}%</span>
      </div>
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
      </div>
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

/* ── Flask icon ── */
const FlaskIcon = ({ size = 20 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 3h6" />
    <path d="M10 9V3" />
    <path d="M14 9V3" />
    <path d="M10 9l-4.5 9.5a2 2 0 001.8 2.9h9.4a2 2 0 001.8-2.9L14 9" />
  </svg>
);

/* ═══════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════ */
const PilotTracker = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const { role: userRole } = useUserRole();
  const canEdit = ['admin', 'analyst'].includes(userRole);

  const [loading, setLoading] = useState(true);
  const [pilots, setPilots] = useState([]);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  /* ── Detail view ── */
  const [selectedPilot, setSelectedPilot] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  /* ── Create modal ── */
  const [showCreate, setShowCreate] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [proposals, setProposals] = useState([]);
  const [formData, setFormData] = useState({
    proposal_id: '',
    title: '',
    start_date: '',
    end_date: '',
    success_criteria: '',
    budget_allocated: '',
  });

  /* ── Edit state ── */
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [saving, setSaving] = useState(false);

  /* ── Filters ── */
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || '');

  /* ── Fetch list ── */
  const fetchPilots = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      const res = await api.get(`/api/v1/pilots?${params.toString()}`);
      setPilots(res.data.pilots || []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => { fetchPilots(); }, [fetchPilots]);

  /* ── Fetch shortlisted proposals for create modal ── */
  useEffect(() => {
    if (!showCreate) return;
    const load = async () => {
      try {
        const res = await api.get('/api/v1/proposals?status=shortlisted&page_size=100');
        const list = res.data.proposals || res.data || [];
        setProposals(list);
      } catch {
        // non-critical
      }
    };
    load();
  }, [showCreate]);

  /* ── Filter handler ── */
  const handleFilter = (value) => {
    setStatusFilter(value);
    const p = new URLSearchParams();
    if (value) p.set('status', value);
    setSearchParams(p);
  };

  /* ── Create ── */
  const handleCreate = async (e) => {
    e.preventDefault();
    if (!formData.proposal_id || !formData.title.trim()) return;
    try {
      setSubmitting(true);
      const body = { ...formData };
      if (body.budget_allocated) body.budget_allocated = parseFloat(body.budget_allocated);
      else delete body.budget_allocated;
      Object.keys(body).forEach(k => { if (!body[k] && body[k] !== 0) delete body[k]; });
      await api.post('/api/v1/pilots', body);
      setToast({ message: 'Pilot created successfully', type: 'success' });
      setShowCreate(false);
      setFormData({ proposal_id: '', title: '', start_date: '', end_date: '', success_criteria: '', budget_allocated: '' });
      fetchPilots();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setSubmitting(false);
    }
  };

  /* ── Auto-fill title from selected proposal ── */
  const handleProposalSelect = (proposalId) => {
    const selected = proposals.find(p => p.id === proposalId);
    setFormData(f => ({
      ...f,
      proposal_id: proposalId,
      title: selected ? selected.title : f.title,
    }));
  };

  /* ── Detail ── */
  const openDetail = async (pilotId) => {
    try {
      setDetailLoading(true);
      const res = await api.get(`/api/v1/pilots/${pilotId}`);
      setSelectedPilot(res.data);
      setEditing(false);
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setDetailLoading(false);
    }
  };

  /* ── Start editing ── */
  const startEdit = () => {
    setEditData({
      status: selectedPilot.status || 'setup',
      budget_spent: selectedPilot.budget_spent || '',
      outcome_rating: selectedPilot.outcome_rating || null,
      outcome_summary: selectedPilot.outcome_summary || '',
      lessons_learned: selectedPilot.lessons_learned || '',
      adoption_decision: selectedPilot.adoption_decision || 'pending',
    });
    setEditing(true);
  };

  /* ── Save edit ── */
  const handleSave = async () => {
    try {
      setSaving(true);
      const body = { ...editData };
      if (body.budget_spent !== '' && body.budget_spent !== null) body.budget_spent = parseFloat(body.budget_spent);
      else delete body.budget_spent;
      if (!body.outcome_rating) delete body.outcome_rating;
      if (!body.outcome_summary) delete body.outcome_summary;
      if (!body.lessons_learned) delete body.lessons_learned;
      await api.put(`/api/v1/pilots/${selectedPilot.id}`, body);
      setToast({ message: 'Pilot updated successfully', type: 'success' });
      setEditing(false);
      openDetail(selectedPilot.id);
      fetchPilots();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  /* ── Adoption decision ── */
  const handleAdoptionDecision = async (decision) => {
    try {
      setSaving(true);
      await api.put(`/api/v1/pilots/${selectedPilot.id}`, { adoption_decision: decision });
      setToast({ message: `Adoption decision set to "${decision}"`, type: 'success' });
      openDetail(selectedPilot.id);
      fetchPilots();
    } catch (err) {
      setToast({ message: getErrorMessage(err), type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  /* ═══════ RENDER ═══════ */

  /* ── Detail view ── */
  if (selectedPilot) {
    const p = selectedPilot;
    return (
      <div className="min-h-screen">
        {toast && <Toast {...toast} onClose={() => setToast(null)} />}

        {/* Back button */}
        <button
          onClick={() => { setSelectedPilot(null); setEditing(false); }}
          className="mb-4 text-teal hover:underline font-body text-sm flex items-center gap-1"
        >
          ← Back to Pilot Tracker
        </button>

        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-teal"><FlaskIcon size={24} /></span>
                <h1 className="font-heading text-2xl md:text-3xl text-ink truncate">{p.title}</h1>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                <PilotStatusBadge status={p.status} />
                {p.vendor?.company_name || p.vendor?.name ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/15 text-blue-600 border border-blue-500/30">
                    {p.vendor.company_name || p.vendor.name}
                  </span>
                ) : null}
                {p.adoption_decision && p.adoption_decision !== 'pending' && (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${ADOPTION_STYLES[p.adoption_decision]}`}>
                    {p.adoption_decision.toUpperCase()}
                  </span>
                )}
              </div>
            </div>
            {canEdit && !editing && (
              <button
                onClick={startEdit}
                className="px-4 py-2 bg-teal text-white rounded-lg text-sm font-medium hover:bg-teal/90 transition-colors"
              >
                Edit Pilot
              </button>
            )}
          </div>

          {/* Status Timeline */}
          <StatusTimeline current={p.status} />

          {/* Dates & Budget */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-4 border-t border-ink/10">
            <div>
              <span className="text-xs text-ink/50 uppercase tracking-wide">Start Date</span>
              <p className="font-body text-sm text-ink mt-1">{p.start_date || '—'}</p>
            </div>
            <div>
              <span className="text-xs text-ink/50 uppercase tracking-wide">End Date</span>
              <p className="font-body text-sm text-ink mt-1">{p.end_date || '—'}</p>
            </div>
            <div>
              <span className="text-xs text-ink/50 uppercase tracking-wide">Created</span>
              <p className="font-body text-sm text-ink mt-1">{p.created_at ? new Date(p.created_at).toLocaleDateString() : '—'}</p>
            </div>
          </div>

          {p.budget_allocated && (
            <div className="mt-4">
              <BudgetBar allocated={p.budget_allocated} spent={p.budget_spent} />
            </div>
          )}
        </div>

        {/* Success Criteria */}
        {p.success_criteria && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <h2 className="font-heading text-lg text-ink mb-3">Success Criteria</h2>
            <p className="font-body text-sm text-ink/70 whitespace-pre-wrap">{p.success_criteria}</p>
          </div>
        )}

        {/* Linked Proposal */}
        {p.proposal && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <h2 className="font-heading text-lg text-ink mb-3">Linked Proposal</h2>
            <div className="border border-ink/10 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-body text-sm font-semibold text-ink">{p.proposal.title}</h3>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {p.proposal.sector && (
                      <span className="text-xs text-ink/50">{p.proposal.sector}</span>
                    )}
                    {p.proposal.technology_type && (
                      <span className="text-xs text-ink/50">• {p.proposal.technology_type}</span>
                    )}
                  </div>
                </div>
                {p.proposal.composite_score != null && (
                  <div className="text-right">
                    <span className="text-xs text-ink/50">Eval Score</span>
                    <p className="font-heading text-lg text-teal">{Number(p.proposal.composite_score).toFixed(1)}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Outcome Section */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="font-heading text-lg text-ink mb-4">Outcome</h2>

          {editing ? (
            <div className="space-y-4">
              {/* Status */}
              <div>
                <label className="block text-xs text-ink/60 font-medium mb-1">Status</label>
                <select
                  value={editData.status}
                  onChange={e => setEditData(d => ({ ...d, status: e.target.value }))}
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="setup">Setup</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="extended">Extended</option>
                </select>
              </div>

              {/* Budget Spent */}
              <div>
                <label className="block text-xs text-ink/60 font-medium mb-1">Budget Spent</label>
                <input
                  type="number"
                  value={editData.budget_spent}
                  onChange={e => setEditData(d => ({ ...d, budget_spent: e.target.value }))}
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm"
                  placeholder="Amount spent"
                />
              </div>

              {/* Outcome Rating */}
              <div>
                <label className="block text-xs text-ink/60 font-medium mb-1">Outcome Rating</label>
                <StarRating
                  rating={editData.outcome_rating}
                  onChange={(val) => setEditData(d => ({ ...d, outcome_rating: val }))}
                />
              </div>

              {/* Outcome Summary */}
              <div>
                <label className="block text-xs text-ink/60 font-medium mb-1">Outcome Summary</label>
                <textarea
                  value={editData.outcome_summary}
                  onChange={e => setEditData(d => ({ ...d, outcome_summary: e.target.value }))}
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm"
                  rows={3}
                  placeholder="Summarize the pilot outcome..."
                />
              </div>

              {/* Lessons Learned */}
              <div>
                <label className="block text-xs text-ink/60 font-medium mb-1">Lessons Learned</label>
                <textarea
                  value={editData.lessons_learned}
                  onChange={e => setEditData(d => ({ ...d, lessons_learned: e.target.value }))}
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm"
                  rows={3}
                  placeholder="Key takeaways from this pilot..."
                />
              </div>

              {/* Save / Cancel */}
              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-5 py-2 bg-teal text-white rounded-lg text-sm font-medium hover:bg-teal/90 transition-colors disabled:opacity-50"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={() => setEditing(false)}
                  className="px-5 py-2 bg-ink/10 text-ink rounded-lg text-sm font-medium hover:bg-ink/20 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Rating */}
              <div>
                <span className="text-xs text-ink/50 uppercase tracking-wide">Rating</span>
                <div className="mt-1">
                  {p.outcome_rating ? (
                    <StarRating rating={p.outcome_rating} readonly />
                  ) : (
                    <span className="text-sm text-ink/40">Not rated yet</span>
                  )}
                </div>
              </div>

              {/* Summary */}
              <div>
                <span className="text-xs text-ink/50 uppercase tracking-wide">Summary</span>
                <p className="font-body text-sm text-ink/70 mt-1 whitespace-pre-wrap">
                  {p.outcome_summary || 'No summary yet.'}
                </p>
              </div>

              {/* Lessons Learned */}
              <div>
                <span className="text-xs text-ink/50 uppercase tracking-wide">Lessons Learned</span>
                <p className="font-body text-sm text-ink/70 mt-1 whitespace-pre-wrap">
                  {p.lessons_learned || 'No lessons recorded yet.'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Adoption Decision */}
        {canEdit && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <h2 className="font-heading text-lg text-ink mb-4">Adoption Decision</h2>
            <p className="text-sm text-ink/60 mb-4">
              Current: <span className="font-semibold">{(p.adoption_decision || 'pending').toUpperCase()}</span>
            </p>
            <div className="flex flex-wrap gap-3">
              {['adopt', 'extend', 'pivot', 'terminate'].map((decision) => (
                <button
                  key={decision}
                  onClick={() => handleAdoptionDecision(decision)}
                  disabled={saving}
                  className={`px-5 py-2.5 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 ${
                    p.adoption_decision === decision
                      ? ADOPTION_STYLES[decision]
                      : 'bg-ink/5 text-ink hover:bg-ink/10'
                  }`}
                >
                  {decision.toUpperCase()}
                </button>
              ))}
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
          <span className="text-teal"><FlaskIcon size={28} /></span>
          <div>
            <h1 className="font-heading text-2xl md:text-3xl text-ink">Pilot Tracker</h1>
            <p className="font-body text-sm text-ink/60">Manage pilot programs from setup to outcome</p>
          </div>
        </div>
        {canEdit && (
          <button
            onClick={() => setShowCreate(true)}
            className="px-5 py-2.5 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 transition-colors flex items-center gap-2"
          >
            + Create Pilot
          </button>
        )}
      </div>

      {/* Filter bar */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="flex flex-wrap gap-3 items-center">
          <label className="text-sm text-ink/60 font-medium">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => handleFilter(e.target.value)}
            className="border border-ink/20 rounded-lg px-3 py-2 text-sm min-w-[150px]"
          >
            <option value="">All</option>
            <option value="setup">Setup</option>
            <option value="active">Active</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
            <option value="extended">Extended</option>
          </select>
          {statusFilter && (
            <button
              onClick={() => handleFilter('')}
              className="text-xs text-teal hover:underline"
            >
              Clear filter
            </button>
          )}
          <span className="ml-auto text-xs text-ink/40">{pilots.length} pilot{pilots.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-20">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-teal"></div>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6 text-center">
          <p className="text-red-700 font-body">{error}</p>
          <button onClick={fetchPilots} className="mt-3 text-sm text-teal hover:underline">Retry</button>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && pilots.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm p-12 text-center">
          <div className="text-5xl mb-4">🧪</div>
          <h2 className="font-heading text-xl text-ink mb-2">No pilots yet</h2>
          <p className="font-body text-sm text-ink/60 mb-6">
            Create a pilot to track shortlisted proposals through their lifecycle.
          </p>
          {canEdit && (
            <button
              onClick={() => setShowCreate(true)}
              className="px-5 py-2.5 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 transition-colors"
            >
              + Create Pilot
            </button>
          )}
        </div>
      )}

      {/* Card grid */}
      {!loading && !error && pilots.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pilots.map((pilot) => (
            <button
              key={pilot.id}
              onClick={() => openDetail(pilot.id)}
              className="bg-white rounded-xl shadow-sm p-6 text-left hover:shadow-md transition-shadow border border-transparent hover:border-teal/20"
            >
              {/* Title & Status */}
              <div className="flex items-start justify-between gap-2 mb-3">
                <h3 className="font-heading text-base text-ink line-clamp-2 flex-1">{pilot.title}</h3>
                <PilotStatusBadge status={pilot.status} />
              </div>

              {/* Vendor */}
              {pilot.vendor_name && (
                <p className="text-xs text-ink/50 mb-2">🏢 {pilot.vendor_name}</p>
              )}

              {/* Date range */}
              <div className="text-xs text-ink/50 mb-3">
                {pilot.start_date && pilot.end_date
                  ? `${pilot.start_date} → ${pilot.end_date}`
                  : pilot.start_date
                  ? `Starts ${pilot.start_date}`
                  : 'Dates not set'}
              </div>

              {/* Budget */}
              {pilot.budget_allocated && (
                <div className="mb-3">
                  <BudgetBar allocated={pilot.budget_allocated} spent={pilot.budget_spent} />
                </div>
              )}

              {/* Outcome rating */}
              {pilot.outcome_rating && (
                <div className="pt-2 border-t border-ink/10">
                  <StarRating rating={pilot.outcome_rating} readonly />
                </div>
              )}

              {/* Adoption decision */}
              {pilot.adoption_decision && pilot.adoption_decision !== 'pending' && (
                <div className="mt-2">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold ${ADOPTION_STYLES[pilot.adoption_decision]}`}>
                    {pilot.adoption_decision.toUpperCase()}
                  </span>
                </div>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Detail loading overlay */}
      {detailLoading && (
        <div className="fixed inset-0 bg-black/20 z-40 flex items-center justify-center">
          <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-teal"></div>
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowCreate(false)}>
          <div className="bg-white rounded-2xl w-full max-w-lg mx-4 p-6 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h2 className="font-heading text-xl text-ink">Create Pilot</h2>
              <button onClick={() => setShowCreate(false)} className="text-ink/40 hover:text-ink text-xl">×</button>
            </div>

            <form onSubmit={handleCreate} className="space-y-4">
              {/* Proposal select */}
              <div>
                <label className="block text-xs text-ink/60 font-medium mb-1">Proposal (shortlisted) *</label>
                <select
                  value={formData.proposal_id}
                  onChange={(e) => handleProposalSelect(e.target.value)}
                  required
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">Select a proposal...</option>
                  {proposals.map(p => (
                    <option key={p.id} value={p.id}>{p.title}</option>
                  ))}
                </select>
              </div>

              {/* Title */}
              <div>
                <label className="block text-xs text-ink/60 font-medium mb-1">Title *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={e => setFormData(f => ({ ...f, title: e.target.value }))}
                  required
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm"
                  placeholder="Pilot title"
                />
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs text-ink/60 font-medium mb-1">Start Date</label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={e => setFormData(f => ({ ...f, start_date: e.target.value }))}
                    className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-ink/60 font-medium mb-1">End Date</label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={e => setFormData(f => ({ ...f, end_date: e.target.value }))}
                    className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
              </div>

              {/* Success Criteria */}
              <div>
                <label className="block text-xs text-ink/60 font-medium mb-1">Success Criteria</label>
                <textarea
                  value={formData.success_criteria}
                  onChange={e => setFormData(f => ({ ...f, success_criteria: e.target.value }))}
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm"
                  rows={3}
                  placeholder="Define what success looks like..."
                />
              </div>

              {/* Budget */}
              <div>
                <label className="block text-xs text-ink/60 font-medium mb-1">Budget Allocated</label>
                <input
                  type="number"
                  value={formData.budget_allocated}
                  onChange={e => setFormData(f => ({ ...f, budget_allocated: e.target.value }))}
                  className="w-full border border-ink/20 rounded-lg px-3 py-2 text-sm"
                  placeholder="0.00"
                  min="0"
                  step="0.01"
                />
              </div>

              {/* Submit */}
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  disabled={submitting || !formData.proposal_id || !formData.title.trim()}
                  className="flex-1 py-2.5 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 transition-colors disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Create Pilot'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-5 py-2.5 bg-ink/10 text-ink rounded-lg font-body text-sm font-semibold hover:bg-ink/20 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PilotTracker;

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const WeightBar = ({ label, value }) => {
  const pct = Math.round((value || 0) * 100);
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-gray-400 w-28 truncate">{label}</span>
      <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
        <div
          className="h-full rounded-full bg-[#3B82F6]"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-gray-300 w-10 text-right font-mono">{pct}%</span>
    </div>
  );
};

const BusinessGroupsList = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [groups, setGroups] = useState([]);

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get('/api/v1/chamber-business-groups');
      setGroups(res.data.business_groups || res.data || []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[var(--color-table-header-bg)] flex items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-[#3B82F6] mx-auto"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-table-header-bg)] p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-white">Business Groups</h1>
          <p className="text-gray-400 mt-1">Dubai Chambers — Evaluation Groups & Weight Configuration</p>
        </header>

        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {groups.length === 0 ? (
            <div className="col-span-full bg-[#1E293B] rounded-xl shadow-xl p-12 text-center border border-gray-700">
              <p className="text-[#94A3B8] mb-2">No business groups found</p>
              <p className="text-[#94A3B8] text-sm">Business groups will appear here once configured.</p>
            </div>
          ) : (
            groups.map((g) => {
              const weights = g.evaluation_weight_config_json || g.evaluation_weight_config || null;
              return (
                <Link key={g.id} to={`/business-groups/${g.id}`} className="block group">
                  <div className="bg-[#1E293B] rounded-xl shadow-xl p-6 border border-gray-700 hover:border-[#3B82F6] transition-all duration-200 h-full flex flex-col">
                    {/* Group name */}
                    <h3 className="text-xl font-bold text-white mb-1 group-hover:text-[#3B82F6] transition-colors">
                      {g.name}
                    </h3>

                    {/* Chamber subtitle */}
                    <p className="text-sm text-[#F59E0B] mb-3">
                      {g.chamber || 'Dubai Chamber of Commerce'}
                    </p>

                    {/* Description */}
                    {g.description && (
                      <p className="text-gray-400 text-sm mb-4 line-clamp-3 flex-grow">
                        {g.description}
                      </p>
                    )}
                    {!g.description && <div className="flex-grow" />}

                    {/* Proposal count badge */}
                    <div className="flex items-center gap-2 mb-4">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-[#3B82F6]/20 text-[#3B82F6]">
                        {g.proposal_count != null ? g.proposal_count : '—'} proposals
                      </span>
                      {g.lead_name && (
                        <span className="text-xs text-[#94A3B8]">
                          Lead: {g.lead_name}
                        </span>
                      )}
                    </div>

                    {/* Evaluation weights */}
                    {weights ? (
                      <div className="border-t border-gray-700 pt-4 space-y-2">
                        <p className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-2">Evaluation Weights</p>
                        <WeightBar label="Relevance" value={weights.relevance_weight} />
                        <WeightBar label="Feasibility" value={weights.feasibility_weight} />
                        <WeightBar label="Sector Alignment" value={weights.sector_alignment_weight} />
                        <WeightBar label="Compliance" value={weights.compliance_weight} />
                      </div>
                    ) : (
                      <div className="border-t border-gray-700 pt-4">
                        <p className="text-xs text-[#94A3B8]">Default evaluation weights</p>
                      </div>
                    )}
                  </div>
                </Link>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};

export default BusinessGroupsList;

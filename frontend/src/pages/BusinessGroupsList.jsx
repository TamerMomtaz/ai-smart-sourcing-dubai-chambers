import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

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
      const res = await api.get('/api/v1/business-groups');
      setGroups(res.data.groups || []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="animate-pulse text-teal font-heading text-2xl">Loading business groups...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-6">
          <h1 className="font-heading text-4xl text-teal">Business Groups</h1>
        </header>

        {error && (
          <div className="bg-burgundy/10 border border-burgundy rounded-lg p-4 mb-6">
            <p className="text-burgundy">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {groups.length === 0 ? (
            <div className="col-span-full text-center p-8 text-ink/60">
              No business groups found
            </div>
          ) : (
            groups.map((g) => (
              <div key={g.id} className="bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition">
                <h3 className="font-heading text-xl text-teal mb-2">{g.name}</h3>
                <div className="text-sm text-ink/70 mb-4">
                  <div>🏢 {g.chamber}</div>
                  {g.description && <div className="mt-2">{g.description}</div>}
                </div>
                <Link to={`/business-groups/${g.id}`} className="text-teal hover:underline text-sm font-medium">
                  View Details →
                </Link>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default BusinessGroupsList;
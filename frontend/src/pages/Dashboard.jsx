import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [userRes, statsRes] = await Promise.all([
          api.get('/api/v1/users/me'),
          fetchDashboardStats()
        ]);
        setUser(userRes.data);
        setStats(statsRes);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const fetchDashboardStats = async () => {
    const userRes = await api.get('/api/v1/users/me');
    const role = userRes.data.role;
    
    if (role === 'executive') {
      const res = await api.get('/api/v1/dashboard/executive');
      return res.data;
    } else if (role === 'analyst') {
      const res = await api.get('/api/v1/dashboard/analyst');
      return res.data;
    } else {
      const [proposals, vendors] = await Promise.all([
        api.get('/proposals?page=1&page_size=1'),
        role === 'vendor' ? api.get('/vendors/') : Promise.resolve({ data: {} })
      ]);
      return {
        total_proposals: proposals.data.total || 0,
        my_proposals: proposals.data.total || 0
      };
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="animate-pulse text-teal font-heading text-2xl">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-cream p-8">
        <div className="max-w-4xl mx-auto bg-burgundy/10 border border-burgundy rounded-lg p-6">
          <h2 className="font-heading text-2xl text-burgundy mb-2">Error Loading Dashboard</h2>
          <p className="text-ink">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="font-heading text-4xl text-teal mb-2">Dashboard</h1>
          <p className="text-ink/70">Welcome back, {user?.full_name || 'User'}</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Total Proposals"
            value={stats?.pipeline_status?.total_proposals || stats?.total_proposals || 0}
            icon="📋"
            color="teal"
          />
          <StatCard
            title="Under Review"
            value={stats?.pipeline_status?.under_review || 0}
            icon="🔍"
            color="gold"
          />
          <StatCard
            title="Approved"
            value={stats?.pipeline_status?.approved || 0}
            icon="✅"
            color="teal"
          />
          <StatCard
            title="Evaluating"
            value={stats?.pipeline_status?.evaluating || 0}
            icon="⚙️"
            color="gold"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="font-heading text-2xl text-teal mb-4">Recent Activity</h2>
            {stats?.recent_proposals?.length > 0 ? (
              <ul className="space-y-3">
                {stats.recent_proposals.slice(0, 5).map(p => (
                  <li key={p.id} className="border-b border-cream pb-2">
                    <Link to={`/proposals/${p.id}`} className="text-teal hover:underline font-medium">
                      {p.title}
                    </Link>
                    <div className="text-sm text-ink/60 mt-1">
                      {p.sector} • {p.status}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-ink/60">No recent proposals</p>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="font-heading text-2xl text-teal mb-4">Quick Links</h2>
            <div className="space-y-3">
              <QuickLink to="/proposals" label="View All Proposals" icon="📋" />
              {user?.role === 'vendor' && <QuickLink to="/proposals/new" label="Submit New Proposal" icon="➕" />}
              {(user?.role === 'analyst' || user?.role === 'executive') && <QuickLink to="/evaluations" label="Evaluations" icon="📊" />}
              <QuickLink to="/vendors" label="Vendors" icon="🏢" />
              <QuickLink to="/business-groups" label="Business Groups" icon="👥" />
              {user?.role === 'compliance_officer' && <QuickLink to="/compliance-audits" label="Compliance Audits" icon="🔒" />}
              <QuickLink to="/trend-analyses" label="Trend Analyses" icon="📈" />
              <QuickLink to="/ai-interactions" label="AI Interactions" icon="🤖" />
            </div>
          </div>
        </div>

        {stats?.sector_trends && stats.sector_trends.length > 0 && (
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="font-heading text-2xl text-teal mb-4">Sector Trends</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {stats.sector_trends.map(st => (
                <div key={st.sector} className="border border-cream rounded-lg p-4">
                  <div className="text-sm text-ink/60 mb-1">{st.sector}</div>
                  <div className="font-heading text-xl text-teal">{st.proposal_count}</div>
                  <div className="text-xs text-ink/50 mt-1">Avg: {st.average_score?.toFixed(1) || 'N/A'}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon, color }) => {
  const colorClass = color === 'teal' ? 'text-teal' : 'text-gold';
  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span className={`font-heading text-3xl ${colorClass}`}>{value}</span>
      </div>
      <h3 className="text-ink/70 text-sm">{title}</h3>
    </div>
  );
};

const QuickLink = ({ to, label, icon }) => (
  <Link
    to={to}
    className="flex items-center space-x-3 p-3 rounded-lg hover:bg-cream transition-colors"
  >
    <span className="text-xl">{icon}</span>
    <span className="text-teal hover:underline">{label}</span>
  </Link>
);

export default Dashboard;
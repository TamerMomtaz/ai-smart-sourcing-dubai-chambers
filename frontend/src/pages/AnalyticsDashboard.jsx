import React, { useState, useEffect } from 'react';
import api, { getErrorMessage } from '../lib/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';

const AnalyticsDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [trendAnalyses, setTrendAnalyses] = useState([]);
  const [selectedSector, setSelectedSector] = useState('all');

  useEffect(() => {
    fetchData();
  }, [selectedSector]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      let dashboardEndpoint = '/dashboard/analyst';
      if (selectedSector !== 'all') {
        dashboardEndpoint = `/dashboard/sector/${selectedSector}`;
      }

      const [dashboardResponse, trendsResponse] = await Promise.all([
        api.get(dashboardEndpoint),
        api.get('/trend-analyses', { params: { limit: 5 } }),
      ]);

      setDashboardData(dashboardResponse.data);
      setTrendAnalyses(trendsResponse.data.trend_analyses || []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" text="Loading analytics..." />
      </div>
    );
  }

  const sectors = ['all', 'fintech', 'healthcare', 'logistics', 'energy', 'education', 'government', 'tourism'];

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-4xl font-heading font-bold text-ink mb-2">Analytics Dashboard</h1>
          <p className="text-ink/60 font-body">AI-powered insights and trend analysis</p>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-body font-medium text-ink mb-2">Sector</label>
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="w-full px-4 py-2 border border-ink/20 rounded-lg font-body text-ink focus:outline-none focus:ring-2 focus:ring-teal"
            >
              {sectors.map((sector) => (
                <option key={sector} value={sector}>
                  {sector === 'all' ? 'All Sectors' : sector.charAt(0).toUpperCase() + sector.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Stats */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <p className="text-sm text-ink/60 font-body mb-1">Total Proposals</p>
            <p className="text-3xl font-heading text-teal">
              {dashboardData.pipeline_status?.total_proposals || dashboardData.total_proposals || 0}
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-6">
            <p className="text-sm text-ink/60 font-body mb-1">Evaluating</p>
            <p className="text-3xl font-heading text-gold">
              {dashboardData.pipeline_status?.evaluating || 0}
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-6">
            <p className="text-sm text-ink/60 font-body mb-1">Approved</p>
            <p className="text-3xl font-heading text-teal">
              {dashboardData.pipeline_status?.approved || 0}
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-6">
            <p className="text-sm text-ink/60 font-body mb-1">Avg Score</p>
            <p className="text-3xl font-heading text-gold">
              {dashboardData.average_score?.toFixed(1) || 'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* Trend Analyses */}
      {trendAnalyses.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-2xl font-heading text-teal mb-4">Recent Trend Analyses</h2>
          <div className="space-y-4">
            {trendAnalyses.map((trend) => (
              <div key={trend.id} className="border border-cream rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-body font-medium text-ink">{trend.sector || 'General'}</p>
                    <p className="text-sm text-ink/60 font-body mt-1">
                      {new Date(trend.analysis_date).toLocaleDateString()} - {trend.submission_volume} submissions
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;

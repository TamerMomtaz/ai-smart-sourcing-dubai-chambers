import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { getErrorMessage } from '../lib/api';
import { useTranslation } from '../lib/language';

const SECTORS = [
  'FinTech', 'Healthcare', 'Logistics', 'Energy', 'Education',
  'Government', 'Tourism', 'Cybersecurity', 'AI/ML', 'Smart City',
  'Real Estate', 'Retail', 'Manufacturing', 'Agriculture', 'Media',
];

const Settings = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [user, setUser] = useState(null);
  const [notifications, setNotifications] = useState({
    email_enabled: true,
    proposal_status_updates: true,
    weekly_digest: true,
    compliance_alerts: true
  });
  const [profile, setProfile] = useState({
    full_name: '',
    preferred_language: 'en'
  });

  /* ── Sector Assignments (admin only) ── */
  const [sectorAssignments, setSectorAssignments] = useState([]);
  const [analysts, setAnalysts] = useState([]);
  const [sectorLoading, setSectorLoading] = useState(false);
  const [sectorSaving, setSectorSaving] = useState(false);

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/v1/users/me');
      setUser(response.data);
      setProfile({
        full_name: response.data.full_name || '',
        preferred_language: response.data.preferred_language || 'en'
      });
      if (response.data.notification_preferences) {
        setNotifications(response.data.notification_preferences);
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  /* ── Sector assignment helpers ── */
  const fetchSectorAssignments = useCallback(async () => {
    setSectorLoading(true);
    try {
      const [asnRes, analystRes] = await Promise.all([
        api.get('/api/v1/sector-assignments'),
        api.get('/api/v1/users?role=analyst'),
      ]);
      setSectorAssignments(asnRes.data.sector_assignments || []);
      setAnalysts(analystRes.data.users || analystRes.data || []);
    } catch {
      // non-critical — admin section simply won't populate
    } finally {
      setSectorLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchSectorAssignments();
    }
  }, [user, fetchSectorAssignments]);

  const handleSectorAssign = async (sector, assignedUserId) => {
    setSectorSaving(true);
    setError(null);
    setSuccess(null);
    try {
      if (!assignedUserId) {
        // Remove assignment — find existing and delete
        const existing = sectorAssignments.find(a => a.sector === sector);
        if (existing) {
          await api.delete(`/api/v1/sector-assignments/${existing.id}`);
        }
      } else {
        await api.put('/api/v1/sector-assignments', {
          sector,
          assigned_user_id: assignedUserId,
        });
      }
      setSuccess('Sector assignment updated');
      setTimeout(() => setSuccess(null), 3000);
      await fetchSectorAssignments();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSectorSaving(false);
    }
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.patch('/api/v1/users/me', profile);
      setSuccess(t('settings.profile_updated'));
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleNotificationUpdate = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.patch('/api/v1/users/me', {
        notification_preferences: notifications
      });
      setSuccess(t('settings.notifications_updated'));
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const handleSignOut = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-4xl font-heading font-bold text-ink mb-2">{t('settings.title')}</h1>
          <p className="text-ink/60 font-body">{t('settings.subtitle')}</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-burgundy/10 border border-burgundy rounded-lg">
            <p className="text-burgundy font-body">{error}</p>
          </div>
        )}

        {success && (
          <div className="mb-6 p-4 bg-teal/10 border border-teal rounded-lg">
            <p className="text-teal font-body">{success}</p>
          </div>
        )}

        {/* User Info Card */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-2xl font-heading font-bold text-ink mb-4">{t('settings.account_info')}</h2>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-body font-medium text-ink/60 mb-1">{t('settings.email')}</label>
              <p className="font-body text-ink">{user?.email}</p>
            </div>
            <div>
              <label className="block text-sm font-body font-medium text-ink/60 mb-1">{t('settings.role')}</label>
              <p className="font-body text-ink capitalize">{user?.role?.replace('_', ' ')}</p>
            </div>
            <div>
              <label className="block text-sm font-body font-medium text-ink/60 mb-1">{t('settings.chamber')}</label>
              <p className="font-body text-ink">{user?.chamber || t('common.na')}</p>
            </div>
            {user?.business_group && (
              <div>
                <label className="block text-sm font-body font-medium text-ink/60 mb-1">{t('settings.business_group')}</label>
                <p className="font-body text-ink">{user.business_group}</p>
              </div>
            )}
          </div>
        </div>

        {/* Profile Settings */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-2xl font-heading font-bold text-ink mb-4">{t('settings.profile_settings')}</h2>
          <form onSubmit={handleProfileUpdate}>
            <div className="space-y-4">
              <div>
                <label htmlFor="full_name" className="block text-sm font-body font-medium text-ink mb-2">
                  {t('settings.full_name')}
                </label>
                <input
                  type="text"
                  id="full_name"
                  value={profile.full_name}
                  onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                  className="w-full px-4 py-2 border border-ink/20 rounded-lg font-body text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                  required
                />
              </div>
              <div>
                <label htmlFor="preferred_language" className="block text-sm font-body font-medium text-ink mb-2">
                  {t('settings.preferred_language')}
                </label>
                <select
                  id="preferred_language"
                  value={profile.preferred_language}
                  onChange={(e) => setProfile({ ...profile, preferred_language: e.target.value })}
                  className="w-full px-4 py-2 border border-ink/20 rounded-lg font-body text-ink focus:outline-none focus:ring-2 focus:ring-teal"
                >
                  <option value="en">{t('settings.english')}</option>
                  <option value="ar">{t('settings.arabic')}</option>
                </select>
              </div>
            </div>
            <div className="mt-6">
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2 bg-teal text-white rounded-lg font-body font-medium hover:bg-teal/90 transition disabled:opacity-50"
              >
                {saving ? t('settings.saving') : t('settings.save_profile')}
              </button>
            </div>
          </form>
        </div>

        {/* Notification Preferences */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-2xl font-heading font-bold text-ink mb-4">{t('settings.notifications')}</h2>
          <form onSubmit={handleNotificationUpdate}>
            <div className="space-y-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="email_enabled"
                  checked={notifications.email_enabled}
                  onChange={(e) => setNotifications({ ...notifications, email_enabled: e.target.checked })}
                  className="h-4 w-4 text-teal focus:ring-teal border-ink/20 rounded"
                />
                <label htmlFor="email_enabled" className="ml-3 font-body text-ink">
                  {t('settings.email_notifications')}
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="proposal_status_updates"
                  checked={notifications.proposal_status_updates}
                  onChange={(e) => setNotifications({ ...notifications, proposal_status_updates: e.target.checked })}
                  className="h-4 w-4 text-teal focus:ring-teal border-ink/20 rounded"
                />
                <label htmlFor="proposal_status_updates" className="ml-3 font-body text-ink">
                  {t('settings.proposal_updates')}
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="weekly_digest"
                  checked={notifications.weekly_digest}
                  onChange={(e) => setNotifications({ ...notifications, weekly_digest: e.target.checked })}
                  className="h-4 w-4 text-teal focus:ring-teal border-ink/20 rounded"
                />
                <label htmlFor="weekly_digest" className="ml-3 font-body text-ink">
                  {t('settings.weekly_digest')}
                </label>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="compliance_alerts"
                  checked={notifications.compliance_alerts}
                  onChange={(e) => setNotifications({ ...notifications, compliance_alerts: e.target.checked })}
                  className="h-4 w-4 text-teal focus:ring-teal border-ink/20 rounded"
                />
                <label htmlFor="compliance_alerts" className="ml-3 font-body text-ink">
                  {t('settings.compliance_alerts')}
                </label>
              </div>
            </div>
            <div className="mt-6">
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2 bg-teal text-white rounded-lg font-body font-medium hover:bg-teal/90 transition disabled:opacity-50"
              >
                {saving ? t('settings.saving') : t('settings.save_preferences')}
              </button>
            </div>
          </form>
        </div>

        {/* Sector Assignments (admin only) */}
        {user?.role === 'admin' && (
          <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <h2 className="text-2xl font-heading font-bold text-ink mb-2">Sector Assignments</h2>
            <p className="text-ink/60 font-body text-sm mb-4">
              Assign analysts to sectors. New sourcing cases will be auto-assigned to the mapped analyst.
            </p>
            {sectorLoading ? (
              <div className="flex justify-center py-6">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal"></div>
              </div>
            ) : (
              <div className="space-y-3">
                {SECTORS.map(sector => {
                  const current = sectorAssignments.find(a => a.sector === sector);
                  return (
                    <div key={sector} className="flex items-center gap-4">
                      <span className="w-40 font-body text-ink text-sm font-medium">{sector}</span>
                      <select
                        value={current?.assigned_user_id || ''}
                        onChange={e => handleSectorAssign(sector, e.target.value)}
                        disabled={sectorSaving}
                        className="flex-1 px-4 py-2 border border-ink/20 rounded-lg font-body text-ink text-sm focus:outline-none focus:ring-2 focus:ring-teal disabled:opacity-50"
                      >
                        <option value="">Unassigned</option>
                        {analysts.map(a => (
                          <option key={a.id} value={a.id}>
                            {a.full_name || a.email}{a.full_name ? ` (${a.email})` : ''}
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Security Section */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-2xl font-heading font-bold text-ink mb-4">{t('settings.security')}</h2>
          <div className="space-y-4">
            <div>
              <p className="font-body text-ink/60 mb-4">
                {t('settings.sign_out_message')}
              </p>
              <button
                onClick={handleSignOut}
                className="px-6 py-2 bg-burgundy text-white rounded-lg font-body font-medium hover:bg-burgundy/90 transition"
              >
                {t('auth.sign_out')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
import React, { useState, useEffect, useRef, useCallback } from 'react';
import api from '../lib/api';
import { useTranslation } from '../lib/language';
import { useUserRole } from '../lib/userRole';

const SEVERITY_STYLES = {
  critical: 'bg-red-100 text-red-800 border-red-300',
  high: 'bg-orange-100 text-orange-800 border-orange-300',
  medium: 'bg-amber-100 text-amber-800 border-amber-300',
  low: 'bg-blue-100 text-blue-800 border-blue-300',
};

const TYPE_ICONS = {
  security: '\u{1F6E1}\uFE0F',
  compliance: '\u{1F512}',
  ai_anomaly: '\u{1F916}',
  system: '\u{2699}\uFE0F',
};

function AlertBell() {
  const [alerts, setAlerts] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const panelRef = useRef(null);
  const { t } = useTranslation();
  const { role } = useUserRole();

  const canView = role === 'admin' || role === 'compliance_officer';

  const fetchAlerts = useCallback(async () => {
    if (!canView) return;
    try {
      setLoading(true);
      const res = await api.get('/api/v1/alerts');
      setAlerts(res.data || []);
    } catch {
      // Silently fail — alerts are non-critical
    } finally {
      setLoading(false);
    }
  }, [canView]);

  useEffect(() => {
    fetchAlerts();
    // Refresh every 60 seconds
    const interval = setInterval(fetchAlerts, 60000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  // Close panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const handleResolve = async (alertId) => {
    try {
      await api.put(`/api/v1/alerts/${alertId}/resolve`);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    } catch {
      // Silently fail
    }
  };

  if (!canView) return null;

  const unreadCount = alerts.filter((a) => !a.is_read).length;
  const displayCount = alerts.length;

  const formatTime = (ts) => {
    if (!ts) return '';
    const d = new Date(ts);
    const now = new Date();
    const diffMs = now - d;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return t('alerts.just_now');
    if (diffMin < 60) return `${diffMin}m ${t('alerts.ago')}`;
    const diffHrs = Math.floor(diffMin / 60);
    if (diffHrs < 24) return `${diffHrs}h ${t('alerts.ago')}`;
    return d.toLocaleDateString();
  };

  return (
    <div className="relative" ref={panelRef}>
      {/* Bell button */}
      <button
        onClick={() => setOpen(!open)}
        className="relative p-2 text-ink hover:text-teal transition-colors rounded-lg hover:bg-teal/10"
        aria-label={t('alerts.title')}
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
        </svg>
        {displayCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold text-white bg-red-500 rounded-full">
            {displayCount > 99 ? '99+' : displayCount}
          </span>
        )}
      </button>

      {/* Alert panel */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-xl border border-ink/10 z-50 max-h-[70vh] flex flex-col">
          {/* Header */}
          <div className="px-4 py-3 border-b border-ink/10 flex items-center justify-between">
            <h3 className="font-heading text-sm text-ink font-semibold">{t('alerts.title')}</h3>
            <span className="text-xs text-ink/50">
              {displayCount} {t('alerts.unresolved')}
            </span>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto">
            {loading && alerts.length === 0 && (
              <div className="p-6 text-center text-ink/50 text-sm">{t('common.loading')}</div>
            )}
            {!loading && alerts.length === 0 && (
              <div className="p-6 text-center text-ink/50 text-sm">{t('alerts.none')}</div>
            )}
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="px-4 py-3 border-b border-ink/5 hover:bg-cream/50 transition-colors"
              >
                <div className="flex items-start gap-2">
                  <span className="text-base mt-0.5">{TYPE_ICONS[alert.alert_type] || '\u26A0\uFE0F'}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold border ${SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.medium}`}>
                        {alert.severity?.toUpperCase()}
                      </span>
                      <span className="text-[10px] text-ink/40">{formatTime(alert.created_at)}</span>
                    </div>
                    <p className="text-sm font-medium text-ink leading-snug">{alert.title}</p>
                    {alert.description && (
                      <p className="text-xs text-ink/60 mt-0.5 line-clamp-2">{alert.description}</p>
                    )}
                  </div>
                </div>
                <div className="mt-2 flex justify-end">
                  <button
                    onClick={() => handleResolve(alert.id)}
                    className="text-xs px-2.5 py-1 rounded-md bg-teal/10 text-teal hover:bg-teal/20 transition-colors font-medium"
                  >
                    {t('alerts.mark_resolved')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default AlertBell;

import React, { useState, useEffect, useMemo } from 'react';
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { useUserRole } from '../lib/userRole';
import { getErrorMessage } from '../lib/api';
import { ROLE_SIDEBAR_ITEMS, DEFAULT_ITEMS, ROUTE_TO_KEY } from '../config/rolePermissions';
import ThemeSwitcher from './ThemeSwitcher';

/* Sidebar highlight state is now driven by HowItWorks custom events */

function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const [sidebarHighlight, setSidebarHighlight] = useState({ item: null, tooltip: '' });
  const location = useLocation();
  const navigate = useNavigate();
  const { signOut, user } = useAuth();
  const { role, roleLoading } = useUserRole();

  // Listen for sidebar highlight events from the HowItWorks experience
  useEffect(() => {
    const handler = (e) => setSidebarHighlight(e.detail);
    window.addEventListener('highlight-sidebar', handler);
    return () => window.removeEventListener('highlight-sidebar', handler);
  }, []);

  const handleSignOut = async () => {
    setLoggingOut(true);
    try {
      await signOut();
      navigate('/login', { replace: true });
    } catch (err) {
      console.error('Sign out error:', getErrorMessage(err));
    } finally {
      setLoggingOut(false);
    }
  };

  const allNavigation = [
    { name: 'How It Works', href: '/guide', icon: '💡', key: 'how-it-works' },
    { name: 'Dashboard', href: '/dashboard', icon: '📊', key: 'dashboard' },
    { name: 'Sourcing Cases', href: '/sourcing-cases', icon: '🎯', key: 'sourcing-cases' },
    { name: 'Proposals', href: '/proposals', icon: '📝', key: 'proposals' },
    { name: 'Vendors', href: '/vendors', icon: '🏢', key: 'vendors' },
    { name: 'Vendor Intelligence', href: '/vendor-intelligence', icon: '🛡️', key: 'vendor-intelligence' },
    { name: 'Evaluations', href: '/evaluations', icon: '⭐', key: 'evaluations' },
    { name: 'Compare', href: '/compare', icon: '⚖️', key: 'compare' },
    { name: 'Compliance Audits', href: '/compliance-audits', icon: '🔒', key: 'compliance-audits' },
    { name: 'Documents', href: '/documents', icon: '📄', key: 'documents' },
    { name: 'Business Groups', href: '/business-groups', icon: '🏛️', key: 'business-groups' },
    { name: 'Trend Analyses', href: '/trend-analyses', icon: '📈', key: 'trend-analyses' },
    { name: 'ΣI Transparency', href: '/ai-interactions', icon: '🔬', key: 'ai-interactions' },
    { name: 'Users', href: '/users', icon: '👥', key: 'users' },
    { name: 'Executive Board Brief', href: '/board-brief', icon: '📄', key: 'board-brief' },
    { name: 'API Docs', href: '/api-reference', icon: '🔗', key: 'api-docs' },
  ];

  const allowedKeys = ROLE_SIDEBAR_ITEMS[role] || DEFAULT_ITEMS;
  const navigation = useMemo(
    () => {
      if (roleLoading) return [];
      return allNavigation
        .filter(item => allowedKeys.includes(item.key))
        .map(item => {
          // Vendor role sees "My vScore" instead of "Vendor Intelligence"
          if (role === 'vendor' && item.key === 'vendor-intelligence') {
            return { ...item, name: 'My vScore' };
          }
          return item;
        });
    },
    [role, roleLoading]
  );

  const isActive = (path) => location.pathname === path || (path !== '/' && path !== '/dashboard' && location.pathname.startsWith(path));

  // Route protection: check if current path is allowed for user's role
  const isRouteAllowed = useMemo(() => {
    if (roleLoading) return true; // don't block while loading
    const pathname = location.pathname;
    // Find matching route key
    const matchedKey = Object.entries(ROUTE_TO_KEY).find(([routePath]) => {
      return pathname === routePath || pathname.startsWith(routePath + '/');
    });
    if (!matchedKey) return true; // unknown routes are allowed
    const routeKey = matchedKey[1];
    if (routeKey === null) return true; // explicitly always-allowed routes
    return allowedKeys.includes(routeKey);
  }, [location.pathname, allowedKeys, roleLoading]);

  return (
    <div className="min-h-screen bg-cream" style={{ overflowX: 'hidden' }}>
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-ink/50 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white shadow-md transform transition-transform duration-200 ease-in-out md:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-ink/10">
            <h1 className="font-heading text-2xl text-teal">AI Smart Sourcing</h1>
            <p className="font-body text-xs text-ink/60 mt-1">Dubai Chambers | by Tamer Momtaz</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4">
            <ul className="space-y-2">
              {navigation.map((item) => {
                const isHighlighted = sidebarHighlight.item === item.name;
                return (
                  <li key={item.name} className="relative">
                    <Link
                      to={item.href}
                      className={`flex items-center px-4 py-3 rounded-lg font-body text-sm transition-colors min-h-[44px] ${
                        isActive(item.href)
                          ? 'bg-teal text-white'
                          : 'text-ink hover:bg-teal/10 hover:text-teal'
                      }${isHighlighted ? ' sidebar-highlight' : ''}`}
                      onClick={() => setSidebarOpen(false)}
                    >
                      <span className="mr-3">{item.icon}</span>
                      {item.name}
                    </Link>
                    {/* Tooltip during experience */}
                    {isHighlighted && sidebarHighlight.tooltip && (
                      <span className="sidebar-highlight-tooltip">
                        &larr; {sidebarHighlight.tooltip}
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Theme switcher and sign out */}
          <div className="p-4 border-t border-ink/10">
            <ThemeSwitcher />
            <div className="mb-3 mt-2">
              <p className="font-body text-sm text-ink font-medium truncate">
                {user?.email || 'User'}
              </p>
            </div>
            <button
              onClick={handleSignOut}
              disabled={loggingOut}
              className="w-full px-4 py-2 min-h-[44px] bg-burgundy text-white rounded-lg font-body text-sm hover:bg-burgundy/90 transition-colors disabled:opacity-50"
            >
              {loggingOut ? 'Signing out...' : 'Sign Out'}
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="md:pl-64">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-ink/10 sticky top-0 z-30">
          <div className="px-4 py-3 flex items-center justify-between min-h-[52px]">
            <button
              onClick={() => setSidebarOpen(true)}
              className="md:hidden text-ink hover:text-teal transition-colors p-2 -ml-2 min-w-[44px] min-h-[44px] flex items-center justify-center"
              aria-label="Open menu"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
            <h1 className="md:hidden font-heading text-lg text-teal flex-1 text-center">AI Smart Sourcing</h1>
            <div className="md:hidden w-9 h-9 rounded-full bg-teal text-white flex items-center justify-center text-sm font-bold">
              {(user?.email || 'U').charAt(0).toUpperCase()}
            </div>
            <div className="hidden md:block flex-1"></div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 md:p-6" style={{ overflowX: 'auto', minWidth: 0 }}>
          {isRouteAllowed ? (
            <Outlet />
          ) : (
            <div className="min-h-[60vh] flex items-center justify-center">
              <div className="bg-white rounded-xl shadow-md p-8 max-w-md text-center">
                <div className="text-5xl mb-4">🔒</div>
                <h2 className="font-heading text-2xl text-ink mb-2">Access Restricted</h2>
                <p className="text-ink/60 mb-6">You don't have permission to view this page.</p>
                <Link
                  to="/dashboard"
                  className="inline-block px-6 py-2.5 bg-teal text-white rounded-lg font-body text-sm font-semibold hover:bg-teal/90 transition-colors"
                >
                  Back to Dashboard
                </Link>
              </div>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="px-6 py-4 text-center text-xs text-ink/50 font-body">
          Created by Tamer Momtaz | Powered by σI (Added Intelligence)
        </footer>
      </div>
    </div>
  );
}

export default Layout;

import React, { useState } from 'react';
import { Link, useLocation, useNavigate, Outlet } from 'react-router-dom';
import { useAuth } from '../lib/auth';
import { getErrorMessage } from '../lib/api';

function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { signOut, user } = useAuth();

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

  const navigation = [
    { name: 'Dashboard', href: '/', icon: '📊' },
    { name: 'Proposals', href: '/proposals', icon: '📝' },
    { name: 'Vendors', href: '/vendors', icon: '🏢' },
    { name: 'Evaluations', href: '/evaluations', icon: '⭐' },
    { name: 'Compliance Audits', href: '/compliance-audits', icon: '🔒' },
    { name: 'Documents', href: '/documents', icon: '📄' },
    { name: 'Business Groups', href: '/business-groups', icon: '🏛️' },
    { name: 'Trend Analyses', href: '/trend-analyses', icon: '📈' },
    { name: 'AI Interactions', href: '/ai-interactions', icon: '🤖' },
    { name: 'Users', href: '/users', icon: '👥' },
  ];

  const isActive = (path) => location.pathname === path || (path !== '/' && location.pathname.startsWith(path));

  return (
    <div className="min-h-screen bg-cream">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-ink/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        ></div>
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-64 bg-white shadow-md transform transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-ink/10">
            <h1 className="font-heading text-2xl text-teal">AI Smart Sourcing</h1>
            <p className="font-body text-xs text-ink/60 mt-1">Dubai Chambers</p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4">
            <ul className="space-y-2">
              {navigation.map((item) => (
                <li key={item.name}>
                  <Link
                    to={item.href}
                    className={`flex items-center px-4 py-2 rounded-lg font-body text-sm transition-colors ${
                      isActive(item.href)
                        ? 'bg-teal text-white'
                        : 'text-ink hover:bg-teal/10 hover:text-teal'
                    }`}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <span className="mr-3">{item.icon}</span>
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* User info and sign out */}
          <div className="p-4 border-t border-ink/10">
            <div className="mb-3">
              <p className="font-body text-sm text-ink font-medium truncate">
                {user?.email || 'User'}
              </p>
            </div>
            <button
              onClick={handleSignOut}
              disabled={loggingOut}
              className="w-full px-4 py-2 bg-burgundy text-white rounded-lg font-body text-sm hover:bg-burgundy/90 transition-colors disabled:opacity-50"
            >
              {loggingOut ? 'Signing out...' : 'Sign Out'}
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Header */}
        <header className="bg-white shadow-sm border-b border-ink/10 sticky top-0 z-30">
          <div className="px-4 py-4 flex items-center justify-between">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-ink hover:text-teal transition-colors"
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
            <div className="flex-1"></div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6"><Outlet /></main>
      </div>
    </div>
  );
}

export default Layout;

export const ROLE_SIDEBAR_ITEMS = {
  admin: [
    'how-it-works', 'dashboard', 'proposals', 'evaluations',
    'compliance-audits', 'vendors', 'documents', 'business-groups',
    'trend-analyses', 'ai-interactions', 'users', 'board-brief',
    'compare', 'api-docs'
  ],
  analyst: [
    'how-it-works', 'dashboard', 'proposals', 'evaluations',
    'trend-analyses', 'ai-interactions', 'documents', 'api-docs'
  ],
  compliance_officer: [
    'how-it-works', 'dashboard', 'compliance-audits', 'evaluations',
    'vendors', 'ai-interactions', 'documents'
  ],
  vendor: [
    'how-it-works', 'dashboard', 'proposals', 'documents',
    'business-groups'
  ],
  executive: [
    'how-it-works', 'dashboard', 'board-brief', 'trend-analyses',
    'evaluations', 'ai-interactions', 'proposals'
  ]
};

// Fallback for unknown roles
export const DEFAULT_ROLE = 'viewer';
export const DEFAULT_ITEMS = ['how-it-works', 'dashboard'];

// Role display configuration for badges
export const ROLE_BADGES = {
  admin: { label: 'Admin', color: 'bg-red-100 text-red-700 border-red-200' },
  analyst: { label: 'Analyst', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  compliance_officer: { label: 'Compliance', color: 'bg-green-100 text-green-700 border-green-200' },
  vendor: { label: 'Vendor', color: 'bg-amber-100 text-amber-700 border-amber-200' },
  executive: { label: 'Executive', color: 'bg-purple-100 text-purple-700 border-purple-200' },
};

// Map route paths to sidebar keys
export const ROUTE_TO_KEY = {
  '/guide': 'how-it-works',
  '/dashboard': 'dashboard',
  '/proposals': 'proposals',
  '/vendors': 'vendors',
  '/evaluations': 'evaluations',
  '/compare': 'compare',
  '/compliance-audits': 'compliance-audits',
  '/documents': 'documents',
  '/business-groups': 'business-groups',
  '/trend-analyses': 'trend-analyses',
  '/ai-interactions': 'ai-interactions',
  '/users': 'users',
  '/board-brief': 'board-brief',
  '/settings': null,  // always allowed
  '/analytics': null,  // always allowed
  '/comments': null,   // always allowed
  '/desc-certified-providers': null, // always allowed
  '/api-reference': 'api-docs',
  '/api-docs': null, // always allowed (public route)
};

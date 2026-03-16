import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './lib/auth';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import ProposalsList from './pages/ProposalsList';
import ProposalForm from './pages/ProposalForm';
import ProposalDetail from './pages/ProposalDetail';
import VendorsList from './pages/VendorsList';
import VendorForm from './pages/VendorForm';
import VendorDetail from './pages/VendorDetail';
import BusinessGroupsList from './pages/BusinessGroupsList';
import BusinessGroupForm from './pages/BusinessGroupForm';
import BusinessGroupDetail from './pages/BusinessGroupDetail';
import EvaluationsList from './pages/EvaluationsList';
import EvaluationDetail from './pages/EvaluationDetail';
import ComplianceAuditsList from './pages/ComplianceAuditsList';
import ComplianceAuditForm from './pages/ComplianceAuditForm';
import ComplianceAuditDetail from './pages/ComplianceAuditDetail';
import TrendAnalysesList from './pages/TrendAnalysesList';
import AIInteractionsList from './pages/AIInteractionsList';
import CommentsList from './pages/CommentsList';
import DocumentsList from './pages/DocumentsList';
import DocumentDetail from './pages/DocumentDetail';
import DESCCertifiedProvidersList from './pages/DESCCertifiedProvidersList';
import AnalyticsDashboard from './pages/AnalyticsDashboard';
import Settings from './pages/Settings';
import UsersPage from './pages/UsersPage';
import NotFound from './components/NotFound';
import LoadingSpinner from './components/LoadingSpinner';

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#0F172A]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#F59E0B]"></div>
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
};

const PublicRoute = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center min-h-screen"><LoadingSpinner /></div>;
  return !user ? children : <Navigate to="/dashboard" />;
};

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
          <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="analytics" element={<AnalyticsDashboard />} />
            <Route path="proposals" element={<ProposalsList />} />
            <Route path="proposals/new" element={<ProposalForm />} />
            <Route path="proposals/:id" element={<ProposalDetail />} />
            <Route path="proposals/:id/edit" element={<ProposalForm />} />
            <Route path="vendors" element={<VendorsList />} />
            <Route path="vendors/new" element={<VendorForm />} />
            <Route path="vendors/:id" element={<VendorDetail />} />
            <Route path="vendors/:id/edit" element={<VendorForm />} />
            <Route path="business-groups" element={<BusinessGroupsList />} />
            <Route path="business-groups/new" element={<BusinessGroupForm />} />
            <Route path="business-groups/:id" element={<BusinessGroupDetail />} />
            <Route path="business-groups/:id/edit" element={<BusinessGroupForm />} />
            <Route path="evaluations" element={<EvaluationsList />} />
            <Route path="evaluations/:id" element={<EvaluationDetail />} />
            <Route path="compliance-audits" element={<ComplianceAuditsList />} />
            <Route path="compliance-audits/new" element={<ComplianceAuditForm />} />
            <Route path="compliance-audits/:id" element={<ComplianceAuditDetail />} />
            <Route path="compliance-audits/:id/edit" element={<ComplianceAuditForm />} />
            <Route path="trend-analyses" element={<TrendAnalysesList />} />
            <Route path="ai-interactions" element={<AIInteractionsList />} />
            <Route path="comments" element={<CommentsList />} />
            <Route path="documents" element={<DocumentsList />} />
            <Route path="documents/:id" element={<DocumentDetail />} />
            <Route path="desc-certified-providers" element={<DESCCertifiedProvidersList />} />
            <Route path="users" element={<UsersPage />} />
            <Route path="settings" element={<Settings />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
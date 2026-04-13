import { useEffect, useState, lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store';
import { ToastContainer } from './components/UI/Toast';

import LoginPage from './pages/LoginPage';
import Layout from './components/UI/Layout';
import DashboardPage from './pages/DashboardPage';

const TicketListPage = lazy(() => import('./pages/TicketListPage'));
const TicketDetailPage = lazy(() => import('./pages/TicketDetailPage'));
const ContactsPage = lazy(() => import('./pages/ContactsPage'));
const TopologyPage = lazy(() => import('./pages/TopologyPage'));
const SLAConfigPage = lazy(() => import('./pages/SLAConfigPage'));
const EscalationPage = lazy(() => import('./pages/EscalationPage'));
const EmailSettingsPage = lazy(() => import('./pages/EmailSettingsPage'));
const VoiceSettingsPage = lazy(() => import('./pages/VoiceSettingsPage'));
const JiraSettingsPage = lazy(() => import('./pages/JiraSettingsPage'));
const LDAPSettingsPage = lazy(() => import('./pages/LDAPSettingsPage'));
const ReportsPage = lazy(() => import('./pages/ReportsPage'));
const SystemHealthPage = lazy(() => import('./pages/SystemHealthPage'));
const NodeDetailPage = lazy(() => import('./pages/NodeDetailPage'));
const ProjectsPage = lazy(() => import('./pages/ProjectsPage'));
const ProjectDashboardPage = lazy(() => import('./pages/ProjectDashboardPage'));
const VoiceTestPage = lazy(() => import('./pages/VoiceTestPage'));

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  );
}

function PrivateRoute({ children }) {
  const token = useAuthStore((s) => s.token);
  return token ? children : <Navigate to="/login" replace />;
}

function ManagerRoute({ children }) {
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);
  if (token && !user) return <LoadingFallback />;
  const allowed = ['manager', 'tenant_admin', 'super_admin', 'admin', 'agent_l3'];
  if (!allowed.includes(user?.role)) return <Navigate to="/" replace />;
  return children;
}

function AppContent() {
  return (
    <Layout>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/tickets" element={<TicketListPage />} />
          <Route path="/tickets/:id" element={<TicketDetailPage />} />
          <Route path="/contacts" element={<ContactsPage />} />
          <Route path="/projects" element={<ManagerRoute><ProjectsPage /></ManagerRoute>} />
          <Route path="/projects/:projectId/dashboard" element={<ProjectDashboardPage />} />
          <Route path="/voice-test" element={<VoiceTestPage />} />
          <Route path="/topology" element={<TopologyPage />} />
          <Route path="/topology/:nodeId" element={<NodeDetailPage />} />
          <Route path="/settings/sla" element={<ManagerRoute><SLAConfigPage /></ManagerRoute>} />
          <Route path="/settings/escalation" element={<ManagerRoute><EscalationPage /></ManagerRoute>} />
          <Route path="/settings/email" element={<ManagerRoute><EmailSettingsPage /></ManagerRoute>} />
          <Route path="/settings/voice" element={<ManagerRoute><VoiceSettingsPage /></ManagerRoute>} />
          <Route path="/settings/jira" element={<ManagerRoute><JiraSettingsPage /></ManagerRoute>} />
          <Route path="/settings/ldap" element={<ManagerRoute><LDAPSettingsPage /></ManagerRoute>} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/system" element={<SystemHealthPage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}

export default function App() {
  const { token, user, fetchMe } = useAuthStore();
  const [authReady, setAuthReady] = useState(false);

  // Only fetchMe on initial mount (page refresh with existing token)
  // Login flow handles its own fetchMe internally
  useEffect(() => {
    if (token && !user) {
      fetchMe().finally(() => setAuthReady(true));
    } else {
      setAuthReady(true);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (token && !user) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-50">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!token) {
    return (
      <>
        <ToastContainer />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      </>
    );
  }

  return (
    <>
      <ToastContainer />
      <PrivateRoute>
        <AppContent />
      </PrivateRoute>
    </>
  );
}

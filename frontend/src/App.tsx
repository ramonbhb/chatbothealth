import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import AdminPage from './pages/AdminPage';
import CleanWizardPage from './pages/CleanWizardPage';
import CleaningListPage from './pages/CleaningListPage';
import DashboardPage from './pages/DashboardPage';
import DocWizardPage from './pages/DocWizardPage';
import LoginPage from './pages/LoginPage';
import ProjectListPage from './pages/ProjectListPage';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="page"><p>Loading...</p></div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== 'admin') return <Navigate to="/" replace />;
  return <>{children}</>;
}

export default function App() {
  const { user, loading } = useAuth();

  if (loading) return <div className="page"><p>Loading...</p></div>;

  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route path="/" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
      <Route path="/projects" element={<PrivateRoute><ProjectListPage /></PrivateRoute>} />
      <Route path="/projects/:id" element={<PrivateRoute><DocWizardPage /></PrivateRoute>} />
      <Route path="/cleaning" element={<PrivateRoute><CleaningListPage /></PrivateRoute>} />
      <Route path="/cleaning/:id" element={<PrivateRoute><CleanWizardPage /></PrivateRoute>} />
      <Route path="/admin" element={<PrivateRoute><AdminRoute><AdminPage /></AdminRoute></PrivateRoute>} />
    </Routes>
  );
}

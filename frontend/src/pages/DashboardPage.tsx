import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="page">
      <header className="header">
        <div>
          <h1>Health Research Assistant</h1>
          <p>Welcome, {user?.full_name}</p>
        </div>
        <div className="header-actions">
          {user?.role === 'admin' && <Link to="/admin" className="btn secondary">Admin</Link>}
          <button onClick={logout} className="btn secondary">Logout</button>
        </div>
      </header>

      <div className="dashboard-grid">
        <Link to="/projects/new" className="dashboard-card">
          <h2>Project Document</h2>
          <p>
            Document your study: data, methods, and expected outputs (tables, figures, models).
          </p>
          <span className="card-action">Start wizard →</span>
        </Link>
        <Link to="/cleaning/new" className="dashboard-card">
          <h2>Data Cleaning</h2>
          <p>Design and generate a data_clean.py script based on your dataset schema and cleaning requirements.</p>
          <span className="card-action">Start wizard →</span>
        </Link>
      </div>

      <div className="dashboard-links">
        <Link to="/projects">View project sessions</Link>
        <Link to="/cleaning">View cleaning sessions</Link>
      </div>
    </div>
  );
}

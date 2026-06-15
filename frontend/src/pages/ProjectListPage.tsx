import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, WizardSession } from '../api/client';

export default function ProjectListPage() {
  const [sessions, setSessions] = useState<WizardSession[]>([]);

  useEffect(() => {
    api.listProjects().then(setSessions);
  }, []);

  return (
    <div className="page">
      <header className="header">
        <Link to="/">← Dashboard</Link>
        <h1>Project Sessions</h1>
        <Link to="/projects/new" className="btn">New Project</Link>
      </header>
      <ul className="session-list">
        {sessions.map((s) => (
          <li key={s.id}>
            <Link to={`/projects/${s.id}`}>
              <strong>{s.title}</strong>
              <span>Step: {s.current_step}</span>
              <span>{new Date(s.updated_at).toLocaleString()}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

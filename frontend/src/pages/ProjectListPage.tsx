import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, WizardSession } from '../api/client';
import { DOC_STEP_LABELS } from '../constants';

function sectionCount(session: WizardSession) {
  return Object.keys(session.section_data).filter((k) => !k.startsWith('_') && session.section_data[k]).length;
}

export default function ProjectListPage() {
  const [sessions, setSessions] = useState<WizardSession[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.listProjects()
      .then(setSessions)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div className="page">
      <header className="header">
        <Link to="/">← Dashboard</Link>
        <h1>Project Sessions</h1>
        <Link to="/projects/new" className="btn">New Project</Link>
      </header>
      {error && <p className="error">{error}</p>}
      {sessions.length === 0 && <p className="muted">No saved sessions yet. Start a new project to create one.</p>}
      <ul className="session-list">
        {sessions.map((s) => (
          <li key={s.id}>
            <Link to={`/projects/${s.id}`}>
              <strong>{s.title}</strong>
              <span>{DOC_STEP_LABELS[s.current_step] || s.current_step}</span>
              <span>{sectionCount(s)} sections filled</span>
              <span>{new Date(s.updated_at).toLocaleString()}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

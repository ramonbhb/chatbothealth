import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, WizardSession } from '../api/client';
import { CLEAN_STEP_LABELS } from '../constants';

export default function CleaningListPage() {
  const [sessions, setSessions] = useState<WizardSession[]>([]);

  useEffect(() => {
    api.listCleaning().then(setSessions);
  }, []);

  return (
    <div className="page">
      <header className="header">
        <Link to="/">← Dashboard</Link>
        <h1>Cleaning Sessions</h1>
        <Link to="/cleaning/new" className="btn">New Cleaning</Link>
      </header>
      <ul className="session-list">
        {sessions.map((s) => (
          <li key={s.id}>
            <Link to={`/cleaning/${s.id}`}>
              <strong>{s.title}</strong>
              <span>{CLEAN_STEP_LABELS[s.current_step] || s.current_step}</span>
              <span>{new Date(s.updated_at).toLocaleString()}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

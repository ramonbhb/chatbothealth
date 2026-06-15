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
        <Link to="/">← Painel</Link>
        <h1>Sessões de Projeto</h1>
        <Link to="/projects/new" className="btn">Novo Projeto</Link>
      </header>
      {error && <p className="error">{error}</p>}
      {sessions.length === 0 && <p className="muted">Nenhuma sessão salva ainda. Inicie um novo projeto para criar uma.</p>}
      <ul className="session-list">
        {sessions.map((s) => (
          <li key={s.id}>
            <Link to={`/projects/${s.id}`}>
              <strong>{s.title}</strong>
              <span>{DOC_STEP_LABELS[s.current_step] || s.current_step}</span>
              <span>{sectionCount(s)} seções preenchidas</span>
              <span>{new Date(s.updated_at).toLocaleString('pt-BR')}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

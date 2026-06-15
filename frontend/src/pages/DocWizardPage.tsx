import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, WizardSession } from '../api/client';
import { ChatPanel } from '../components/ChatPanel';
import { Stepper } from '../components/Stepper';
import { DOC_SECTIONS, DOC_STEPS } from '../constants';

const STEP_INDEX: Record<string, number> = {
  basics: 0,
  intake: 1,
  review: 2,
  quality: 3,
  export: 4,
};

export default function DocWizardPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = id === 'new';
  const [session, setSession] = useState<WizardSession | null>(null);
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(!isNew);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState(DOC_SECTIONS[0].key);

  useEffect(() => {
    if (isNew) return;
    api.getProject(Number(id))
      .then(setSession)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const stepIndex = session ? STEP_INDEX[session.current_step] ?? 0 : 0;

  const createSession = async () => {
    const s = await api.createProject(title || 'Untitled Project');
    navigate(`/projects/${s.id}`, { replace: true });
    setSession(s);
  };

  const refresh = async () => {
    if (!session) return;
    const s = await api.getProject(session.id);
    setSession(s);
  };

  const handleChat = async (content: string) => {
    if (!session) return;
    await api.projectChat(session.id, content);
    await refresh();
  };

  const extractSection = async (sectionKey: string) => {
    if (!session) return;
    await api.extractSection(session.id, sectionKey);
    await refresh();
  };

  const runQuality = async () => {
    if (!session) return;
    await api.qualityCheck(session.id);
    await refresh();
  };

  const goToStep = async (step: string) => {
    if (!session) return;
    await api.updateProject(session.id, { current_step: step });
    await refresh();
  };

  if (loading) return <div className="page"><p>Loading...</p></div>;

  return (
    <div className="page wizard-page">
      <header className="header">
        <Link to="/">← Dashboard</Link>
        <h1>Project Document Wizard</h1>
      </header>

      <Stepper steps={DOC_STEPS} current={stepIndex} />
      {error && <p className="error">{error}</p>}

      {!session && (
        <div className="wizard-section">
          <h2>Project Basics</h2>
          <label>
            Project Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="My Health DS Project" />
          </label>
          <button onClick={createSession}>Continue</button>
        </div>
      )}

      {session && stepIndex === 0 && (
        <div className="wizard-section">
          <h2>{session.title}</h2>
          <p>Confirm project basics and proceed to guided intake.</p>
          <button onClick={() => goToStep('intake')}>Start Guided Intake</button>
        </div>
      )}

      {session && stepIndex === 1 && (
        <div className="wizard-section split">
          <div>
            <h2>Guided Intake</h2>
            <p>Discuss each section with the assistant. Current focus: <strong>{activeSection.replace(/_/g, ' ')}</strong></p>
            <div className="section-tabs">
              {DOC_SECTIONS.map((s) => (
                <button
                  key={s.key}
                  className={activeSection === s.key ? 'active' : ''}
                  onClick={() => setActiveSection(s.key)}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
          <ChatPanel
            messages={session.messages}
            onSend={handleChat}
            placeholder={`Discuss the ${activeSection.replace(/_/g, ' ')} section...`}
          />
          <div className="wizard-actions">
            <button onClick={() => extractSection(activeSection)}>Extract Section Content</button>
            <button onClick={() => goToStep('review')}>Proceed to Review</button>
          </div>
        </div>
      )}

      {session && stepIndex === 2 && (
        <div className="wizard-section">
          <h2>Section Review</h2>
          {DOC_SECTIONS.map((s) => (
            <div key={s.key} className="review-block">
              <h3>{s.label}</h3>
              <textarea
                value={String(session.section_data[s.key] || '')}
                onChange={async (e) => {
                  const updated = { ...session.section_data, [s.key]: e.target.value };
                  await api.updateProject(session.id, { section_data: updated });
                  setSession({ ...session, section_data: updated });
                }}
                rows={4}
              />
            </div>
          ))}
          <button onClick={() => goToStep('quality')}>Run Quality Gate</button>
        </div>
      )}

      {session && stepIndex === 3 && (
        <div className="wizard-section">
          <h2>Quality Gate</h2>
          <button onClick={runQuality}>Run Checklist</button>
          <ul className="checklist">
            {(session.quality_checklist.items || []).map((item, i) => (
              <li key={i} className={item.passed ? 'pass' : 'fail'}>
                {item.passed ? '✓' : '✗'} {item.item}
                {item.note && <small> — {item.note}</small>}
              </li>
            ))}
          </ul>
          <button onClick={() => goToStep('export')}>Proceed to Export</button>
        </div>
      )}

      {session && stepIndex === 4 && (
        <div className="wizard-section">
          <h2>Export</h2>
          <p>Download your project document as project.docx</p>
          <button onClick={() => api.exportProject(session.id)}>Download project.docx</button>
        </div>
      )}
    </div>
  );
}

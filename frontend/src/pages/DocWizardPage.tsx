import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, WizardSession } from '../api/client';
import { ChatPanel } from '../components/ChatPanel';
import { LoadingPanel } from '../components/LoadingPanel';
import { Stepper } from '../components/Stepper';
import { DOC_SECTIONS, DOC_SECTION_HINTS, DOC_STEP_KEYS, DOC_STEPS, PROJECT_COLLECTION_GOALS } from '../constants';

const STEP_INDEX: Record<string, number> = {
  basics: 0,
  intake: 1,
  review: 2,
  quality: 3,
  export: 4,
};

function sectionLabel(key: string) {
  return DOC_SECTIONS.find((s) => s.key === key)?.label || key;
}

function countFilledSections(sectionData: Record<string, string>) {
  return DOC_SECTIONS.filter((s) => String(sectionData[s.key] || '').trim()).length;
}

export default function DocWizardPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = id === 'new';
  const [session, setSession] = useState<WizardSession | null>(null);
  const [title, setTitle] = useState('');
  const [fullText, setFullText] = useState('');
  const [loading, setLoading] = useState(!isNew);
  const [error, setError] = useState('');
  const [saveMessage, setSaveMessage] = useState('');
  const [importing, setImporting] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [checklistLoading, setChecklistLoading] = useState(false);
  const [activeSection, setActiveSection] = useState(DOC_SECTIONS[0].key);

  useEffect(() => {
    if (isNew) return;
    api.getProject(Number(id))
      .then((s) => {
        setSession(s);
        setTitle(s.title);
        const current = s.section_data._current_section;
        if (typeof current === 'string') setActiveSection(current);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const stepIndex = session ? STEP_INDEX[session.current_step] ?? 0 : 0;

  const ensureSession = async (): Promise<WizardSession> => {
    if (session) return session;
    const s = await api.createProject(title || 'Untitled Project');
    navigate(`/projects/${s.id}`, { replace: true });
    setSession(s);
    setTitle(s.title);
    return s;
  };

  const refresh = async () => {
    if (!session) return;
    const s = await api.getProject(session.id);
    setSession(s);
    setTitle(s.title);
  };

  const saveDraft = async (exit = false) => {
    if (!session) return;
    const payload = {
      title: title || session.title,
      current_step: session.current_step,
      section_data: session.section_data,
    };
    const saved = await api.saveProjectDraft(session.id, payload);
    setSession(saved);
    setSaveMessage(`Draft saved at ${new Date(saved.updated_at).toLocaleString()}`);
    if (exit) navigate('/projects');
  };

  const goToStep = async (step: string) => {
    const s = session || (await ensureSession());
    const updated = await api.updateProject(s.id, { current_step: step });
    setSession(updated);
  };

  const goToStepIndex = (index: number) => {
    if (!session && index > 0) return;
    goToStep(DOC_STEP_KEYS[index]);
  };

  const importFullText = async () => {
    if (fullText.trim().length < 20) {
      setError('Please paste at least 20 characters to import.');
      return;
    }
    setImporting(true);
    setError('');
    setSaveMessage('');
    try {
      const s = await ensureSession();
      const updated = await api.importFullText(s.id, fullText.trim());
      const filled = countFilledSections(updated.section_data);
      if (filled === 0) {
        setError('Import failed: no sections were extracted. Please try again or fill sections manually.');
        return;
      }
      setSession(updated);
      setFullText('');
      setSaveMessage(`Imported into ${filled} section${filled === 1 ? '' : 's'}. Review and edit below.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Import failed');
    } finally {
      setImporting(false);
    }
  };

  const skipToManual = async () => {
    setError('');
    await ensureSession();
    await goToStep('review');
    setSaveMessage('Fill in each section manually below. You can switch to guided chat anytime.');
  };

  const startGuidedChat = async () => {
    setError('');
    await ensureSession();
    await goToStep('intake');
  };

  const selectSection = async (sectionKey: string) => {
    setActiveSection(sectionKey);
    if (!session) return;
    const updatedData = { ...session.section_data, _current_section: sectionKey };
    const updated = await api.updateProject(session.id, { section_data: updatedData });
    setSession(updated);
  };

  const handleChat = async (content: string) => {
    if (!session) return;
    await api.projectChat(session.id, content);
    await refresh();
  };

  const extractSection = async (sectionKey: string) => {
    if (!session) return;
    setExtracting(true);
    setError('');
    try {
      const result = await api.extractSection(session.id, sectionKey);
      await refresh();
      const content = String(result.content || '');
      const preview = content.length > 120 ? `${content.slice(0, 120)}…` : content;
      setSaveMessage(
        content
          ? `Copied into "${sectionLabel(sectionKey)}": ${preview}`
          : `No content extracted for "${sectionLabel(sectionKey)}". Continue the chat and try again.`
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Extract failed');
    } finally {
      setExtracting(false);
    }
  };

  const runQuality = async () => {
    if (!session || checklistLoading) return;
    setChecklistLoading(true);
    setError('');
    try {
      await api.qualityCheck(session.id);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Quality check failed');
    } finally {
      setChecklistLoading(false);
    }
  };

  const updateSection = async (key: string, value: string) => {
    if (!session) return;
    const updated = { ...session.section_data, [key]: value };
    setSession({ ...session, section_data: updated });
  };

  const persistSections = async () => {
    if (!session) return;
    const updated = await api.updateProject(session.id, { section_data: session.section_data });
    setSession(updated);
  };

  const hasSectionContent = (key: string) => Boolean(String(session?.section_data[key] || '').trim());

  if (loading) return <div className="page"><p>Loading...</p></div>;

  const showImportScreen = !session || stepIndex === 0;

  return (
    <div className="page wizard-page">
      <header className="header">
        <div>
          <Link to="/projects">← All sessions</Link>
          <h1>Project Document Wizard</h1>
          {session && <p className="muted">Session #{session.id} · Last updated {new Date(session.updated_at).toLocaleString()}</p>}
        </div>
        {session && (
          <div className="header-actions">
            <button type="button" className="btn secondary" onClick={() => saveDraft(false)}>Save draft</button>
            <button type="button" className="btn secondary" onClick={() => saveDraft(true)}>Save &amp; exit</button>
          </div>
        )}
      </header>

      {session && (
        <Stepper steps={DOC_STEPS} current={stepIndex} onStepClick={goToStepIndex} />
      )}
      {!session && <Stepper steps={DOC_STEPS} current={0} />}

      <div className="purpose-banner">
        <strong>Goal:</strong> Capture a complete picture of your study —
        <ul className="collection-goals">
          {PROJECT_COLLECTION_GOALS.map((g) => (
            <li key={g}>{g}</li>
          ))}
        </ul>
        Paste full text, use guided chat, or fill sections manually — whatever works best for you.
      </div>

      {saveMessage && <p className="save-message">{saveMessage}</p>}
      {error && <pre className="error debug-error">{error}</pre>}

      {showImportScreen && (
        <div className="wizard-section">
          <h2>Start your project document</h2>
          <p className="muted">
            Provide your project in whatever form you prefer. We focus on data, methods,
            and deliverables (tables, figures, models).
          </p>
          <label>
            Project Title
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={async () => {
                if (session && title !== session.title) {
                  const updated = await api.updateProject(session.id, { title });
                  setSession(updated);
                }
              }}
              placeholder="My Health DS Project"
            />
          </label>

          <div className="import-panel import-panel-primary">
            <h3>Paste your full project text</h3>
            <p className="muted">
              Paste a complete project description and the assistant will split it into all predefined sections automatically.
            </p>
            <textarea
              value={fullText}
              onChange={(e) => setFullText(e.target.value)}
              rows={14}
              placeholder="Paste your full project text here..."
            />
            <button type="button" onClick={importFullText} disabled={importing || fullText.trim().length < 20}>
              {importing ? 'Splitting with AI…' : 'Import & split into sections'}
            </button>
          </div>

          <div className="wizard-actions import-alternatives">
            <button type="button" className="btn secondary" onClick={skipToManual}>
              Skip — fill sections manually
            </button>
            <button type="button" className="btn secondary" onClick={startGuidedChat}>
              Skip — use guided chat instead
            </button>
          </div>
        </div>
      )}

      {session && stepIndex === 1 && (
        <div className="wizard-section split">
          <div>
            <h2>Guided Intake</h2>
            <p className="muted">
              Chat about one section at a time. The chat is <strong>not</strong> copied automatically —
              click <strong>Extract section</strong> to copy the conversation into the section field below.
            </p>
            <p>Current focus: <strong>{sectionLabel(activeSection)}</strong></p>
            {DOC_SECTION_HINTS[activeSection] && (
              <p className="section-hint">{DOC_SECTION_HINTS[activeSection]}</p>
            )}
            {hasSectionContent(activeSection) && (
              <p className="section-filled">✓ This section already has saved content</p>
            )}
            <div className="section-tabs">
              {DOC_SECTIONS.map((s) => (
                <button
                  key={s.key}
                  type="button"
                  className={`${activeSection === s.key ? 'active' : ''} ${hasSectionContent(s.key) ? 'filled' : ''}`}
                  onClick={() => selectSection(s.key)}
                >
                  {s.label}
                </button>
              ))}
            </div>
            {hasSectionContent(activeSection) && (
              <div className="extract-preview">
                <strong>Saved content preview</strong>
                <p>{String(session.section_data[activeSection]).slice(0, 300)}{String(session.section_data[activeSection]).length > 300 ? '…' : ''}</p>
              </div>
            )}
          </div>
          <ChatPanel
            messages={session.messages}
            onSend={handleChat}
            placeholder={`Discuss the ${sectionLabel(activeSection)} section…`}
          />
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('basics')}>Back</button>
            <button type="button" className="btn secondary" onClick={() => extractSection(activeSection)} disabled={extracting}>
              {extracting ? 'Extracting…' : 'Extract section from chat'}
            </button>
            <button type="button" onClick={() => goToStep('review')}>Proceed to review</button>
          </div>
        </div>
      )}

      {session && stepIndex === 2 && (
        <div className="wizard-section">
          <h2>Section Review</h2>
          <p className="muted">
            Edit any section directly. Prioritize <strong>Data</strong>, <strong>Methods</strong>,
            <strong> Expected Artifacts</strong>, and <strong>Analysis Workflow</strong>.
          </p>
          {DOC_SECTIONS.map((s) => (
            <div key={s.key} className="review-block">
              <h3>{s.label}</h3>
              <textarea
                value={String(session.section_data[s.key] || '')}
                onChange={(e) => updateSection(s.key, e.target.value)}
                onBlur={persistSections}
                rows={4}
                placeholder={`Enter content for ${s.label}…`}
              />
            </div>
          ))}
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('basics')}>Back to import</button>
            <button type="button" className="btn secondary" onClick={() => goToStep('intake')}>Use guided chat</button>
            <button type="button" onClick={() => goToStep('quality')}>Run quality gate</button>
          </div>
        </div>
      )}

      {session && stepIndex === 3 && (
        <div className="wizard-section">
          <h2>Quality Gate</h2>
          <p className="muted">Review your document against a quality checklist powered by the assistant.</p>
          <button type="button" onClick={runQuality} disabled={checklistLoading}>
            {checklistLoading ? 'Running checklist…' : 'Run checklist'}
          </button>
          {checklistLoading && (
            <LoadingPanel message="Running quality checklist — reviewing your sections…" />
          )}
          {!checklistLoading && (session.quality_checklist.items || []).length > 0 && (
            <ul className="checklist">
              {(session.quality_checklist.items || []).map((item, i) => (
                <li key={i} className={item.passed ? 'pass' : 'fail'}>
                  {item.passed ? '✓' : '✗'} {item.item}
                  {item.note && <small> — {item.note}</small>}
                </li>
              ))}
            </ul>
          )}
          {!checklistLoading && !(session.quality_checklist.items || []).length && (
            <p className="muted">No checklist results yet. Click Run checklist to evaluate your document.</p>
          )}
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('review')} disabled={checklistLoading}>Back to review</button>
            <button type="button" onClick={() => goToStep('export')} disabled={checklistLoading}>Proceed to export</button>
          </div>
        </div>
      )}

      {session && stepIndex === 4 && (
        <div className="wizard-section">
          <h2>Export</h2>
          <p>Download your project document as project.docx</p>
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('review')}>Edit sections</button>
            <button type="button" onClick={() => api.exportProject(session.id)}>Download project.docx</button>
          </div>
        </div>
      )}
    </div>
  );
}

import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, WizardSession } from '../api/client';
import { ChatPanel } from '../components/ChatPanel';
import { DatasetExplorer } from '../components/DatasetExplorer';
import { LoadingPanel } from '../components/LoadingPanel';
import { Stepper } from '../components/Stepper';
import { CLEAN_BUSINESS_TOPICS, CLEAN_STEP_KEYS, CLEAN_STEPS } from '../constants';

const STEP_INDEX: Record<string, number> = {
  select_dataset: 0,
  link_project: 1,
  schema_explore: 2,
  discussion: 3,
  script_draft: 4,
  validation: 5,
  export: 6,
};

interface SchemaData {
  tables: Array<{
    id: number;
    name: string;
    description: string;
    sample_rows?: Array<Record<string, unknown>>;
    columns: Array<{
      id: number;
      name: string;
      data_type: string;
      nullable: boolean;
      is_primary_key: boolean;
      is_foreign_key: boolean;
      description: string;
      valid_values: string;
      is_phi: boolean;
    }>;
  }>;
}

export default function CleanWizardPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isNew = id === 'new';
  const [session, setSession] = useState<WizardSession | null>(null);
  const [title, setTitle] = useState('');
  const [datasets, setDatasets] = useState<Array<{ id: number; name: string; description: string }>>([]);
  const [schema, setSchema] = useState<SchemaData | null>(null);
  const [loading, setLoading] = useState(!isNew);
  const [error, setError] = useState('');
  const [saveMessage, setSaveMessage] = useState('');
  const [generating, setGenerating] = useState(false);
  const [validating, setValidating] = useState(false);
  const [kickoffLoading, setKickoffLoading] = useState(false);

  const loadSchema = async (datasetId: number) => {
    const sch = await api.getSchema(datasetId);
    setSchema(sch as unknown as SchemaData);
  };

  useEffect(() => {
    api.listDatasets().then(setDatasets).catch(() => {});
    if (isNew) return;
    api.getCleaning(Number(id))
      .then(async (s) => {
        setSession(s);
        setTitle(s.title);
        if (s.dataset_id) await loadSchema(s.dataset_id);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const stepIndex = session ? STEP_INDEX[session.current_step] ?? 0 : 0;

  const createSession = async () => {
    const s = await api.createCleaning(title || 'Untitled Cleaning');
    navigate(`/cleaning/${s.id}`, { replace: true });
    setSession(s);
    setTitle(s.title);
  };

  const refresh = async () => {
    if (!session) return;
    const s = await api.getCleaning(session.id);
    setSession(s);
    if (s.dataset_id) await loadSchema(s.dataset_id);
  };

  const goToStep = async (step: string) => {
    if (!session) return;
    const updated = await api.updateCleaning(session.id, { current_step: step });
    setSession(updated);
    if (updated.dataset_id) await loadSchema(updated.dataset_id);
  };

  const goToStepIndex = (index: number) => {
    if (!session) return;
    goToStep(CLEAN_STEP_KEYS[index]);
  };

  const saveDraft = async (exit = false) => {
    if (!session) return;
    const updated = await api.updateCleaning(session.id, {
      title: title || session.title,
      current_step: session.current_step,
      script_content: session.script_content,
    });
    setSession(updated);
    setSaveMessage(`Draft saved at ${new Date(updated.updated_at).toLocaleString()}`);
    if (exit) navigate('/cleaning');
  };

  const selectDataset = async (datasetId: number) => {
    if (!session) return;
    const updated = await api.updateCleaning(session.id, {
      dataset_id: datasetId,
      current_step: 'link_project',
    });
    setSession(updated);
    await loadSchema(datasetId);
  };

  const startDiscussion = async () => {
    if (!session) return;
    await goToStep('discussion');
  };

  useEffect(() => {
    if (!session || stepIndex !== 3 || session.messages.length > 0 || kickoffLoading) return;
    let cancelled = false;
    (async () => {
      setKickoffLoading(true);
      try {
        await api.cleaningKickoff(session.id);
        if (!cancelled) await refresh();
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Could not start planning discussion');
      } finally {
        if (!cancelled) setKickoffLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [session?.id, stepIndex]);

  const handleChat = async (content: string) => {
    if (!session) return;
    await api.cleaningChat(session.id, content);
    await refresh();
  };

  const generateScript = async () => {
    if (!session || generating) return;
    setGenerating(true);
    setError('');
    try {
      const result = await api.generateScript(session.id);
      setSession({
        ...session,
        script_content: result.script_content,
        validation_result: result.validation_result,
        current_step: 'script_draft',
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Script generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const validateScript = async () => {
    if (!session || validating) return;
    setValidating(true);
    setError('');
    try {
      const result = await api.validateScript(session.id);
      setSession({ ...session, validation_result: result, current_step: 'validation' });
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Validation failed');
    } finally {
      setValidating(false);
    }
  };

  if (loading) return <div className="page"><p>Loading...</p></div>;

  return (
    <div className="page wizard-page">
      <header className="header">
        <div>
          <Link to="/cleaning">← All sessions</Link>
          <h1>Data Cleaning Wizard</h1>
          {session && (
            <p className="muted">
              Session #{session.id} · Last updated {new Date(session.updated_at).toLocaleString()}
            </p>
          )}
        </div>
        {session && (
          <div className="header-actions">
            <button type="button" className="btn secondary" onClick={() => saveDraft(false)}>Save draft</button>
            <button type="button" className="btn secondary" onClick={() => saveDraft(true)}>Save &amp; exit</button>
          </div>
        )}
      </header>

      {session ? (
        <Stepper steps={CLEAN_STEPS} current={stepIndex} onStepClick={goToStepIndex} />
      ) : (
        <Stepper steps={CLEAN_STEPS} current={0} />
      )}

      {saveMessage && <p className="save-message">{saveMessage}</p>}
      {error && <pre className="error debug-error">{error}</pre>}

      {!session && (
        <div className="wizard-section">
          <h2>New Cleaning Session</h2>
          <label>
            Session Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Cohort cleaning pipeline" />
          </label>
          <button type="button" onClick={createSession}>Continue</button>
        </div>
      )}

      {session && stepIndex === 0 && (
        <div className="wizard-section">
          <h2>Select Dataset</h2>
          {datasets.map((d) => (
            <button
              key={d.id}
              type="button"
              className={`dataset-card ${session.dataset_id === d.id ? 'selected' : ''}`}
              onClick={() => selectDataset(d.id)}
            >
              <strong>{d.name}</strong>
              <p>{d.description}</p>
              {session.dataset_id === d.id && <span className="muted">Currently selected</span>}
            </button>
          ))}
          {session.dataset_id && (
            <div className="wizard-actions">
              <button type="button" onClick={() => goToStep('link_project')}>Continue</button>
            </div>
          )}
        </div>
      )}

      {session && stepIndex === 1 && (
        <div className="wizard-section">
          <h2>Link Project (Optional)</h2>
          <p className="muted">Optionally associate this cleaning session with a project document session.</p>
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('select_dataset')}>Back</button>
            <button type="button" onClick={() => goToStep('schema_explore')}>Skip — Explore Data</button>
          </div>
        </div>
      )}

      {session && stepIndex === 2 && (
        <div className="wizard-section">
          <h2>Explore Data</h2>
          <p className="muted">
            Review the database structure and up to 10 sample rows per table (de-identified examples).
            Use this to understand what is available before planning cleaning and modeling steps.
          </p>
          {schema ? (
            <DatasetExplorer tables={schema.tables} />
          ) : (
            <LoadingPanel message="Loading dataset structure and samples…" />
          )}
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('link_project')}>Back</button>
            <button type="button" onClick={startDiscussion}>Continue to Planning Discussion</button>
          </div>
        </div>
      )}

      {session && stepIndex === 3 && (
        <div className="wizard-section split">
          <h2>Planning Discussion</h2>
          <p className="muted">
            Work through your modeling and cleaning goals in plain language. The assistant will ask about
            cohort definition, filters, joins, and the final dataset you need.
          </p>
          <div className="topic-checklist">
            <strong>Topics we will cover</strong>
            <ul>
              {CLEAN_BUSINESS_TOPICS.map((topic) => (
                <li key={topic}>{topic}</li>
              ))}
            </ul>
          </div>
          {kickoffLoading && session.messages.length === 0 ? (
            <LoadingPanel message="Reviewing your data structure and samples…" />
          ) : (
            <ChatPanel
              messages={session.messages}
              onSend={handleChat}
              placeholder="Describe your modeling goal, cohort rules, filters, or transformations..."
            />
          )}
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('schema_explore')}>Back</button>
            <button type="button" onClick={generateScript} disabled={generating}>
              {generating ? 'Generating…' : 'Generate Script'}
            </button>
          </div>
          {generating && <LoadingPanel message="Generating data_clean.py from your discussion…" />}
        </div>
      )}

      {session && stepIndex === 4 && (
        <div className="wizard-section">
          <h2>Script Draft</h2>
          <textarea
            className="code-editor"
            value={session.script_content}
            onChange={async (e) => {
              const value = e.target.value;
              setSession({ ...session, script_content: value });
            }}
            onBlur={async () => {
              await api.updateCleaning(session.id, { script_content: session.script_content });
            }}
            rows={20}
          />
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('discussion')}>Back</button>
            <button type="button" onClick={validateScript} disabled={validating}>
              {validating ? 'Validating…' : 'Validate Script'}
            </button>
          </div>
          {validating && <LoadingPanel message="Validating script syntax and safety…" />}
        </div>
      )}

      {session && stepIndex === 5 && (
        <div className="wizard-section">
          <h2>Validation Results</h2>
          <div className={`validation-result ${session.validation_result?.valid ? 'valid' : 'invalid'}`}>
            <p>Syntax: {session.validation_result?.syntax_ok ? 'OK' : 'Failed'}</p>
            <p>Safety: {session.validation_result?.safety_ok ? 'OK' : 'Failed'}</p>
            <p>Lint: {session.validation_result?.lint_ok ? 'OK' : 'Failed'}</p>
            <ul>
              {((session.validation_result?.issues as string[]) || []).map((issue, i) => (
                <li key={i}>{issue}</li>
              ))}
            </ul>
          </div>
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('script_draft')}>Back to script</button>
            <button type="button" onClick={() => goToStep('export')}>Proceed to Export</button>
          </div>
        </div>
      )}

      {session && stepIndex === 6 && (
        <div className="wizard-section">
          <h2>Export</h2>
          <p>Download data_clean.py for your execution team.</p>
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('validation')}>Back</button>
            <button type="button" className="btn secondary" onClick={() => goToStep('script_draft')}>Edit script</button>
            <button type="button" onClick={() => api.exportCleaning(session.id)}>Download data_clean.py</button>
          </div>
        </div>
      )}
    </div>
  );
}

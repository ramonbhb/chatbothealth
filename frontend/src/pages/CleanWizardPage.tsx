import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { api, WizardSession } from '../api/client';
import { ChatPanel } from '../components/ChatPanel';
import { SchemaBrowser } from '../components/SchemaBrowser';
import { Stepper } from '../components/Stepper';
import { CLEAN_STEPS } from '../constants';

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

  useEffect(() => {
    api.listDatasets().then(setDatasets).catch(() => {});
    if (isNew) return;
    api.getCleaning(Number(id))
      .then(async (s) => {
        setSession(s);
        if (s.dataset_id) {
          const sch = await api.getSchema(s.dataset_id);
          setSchema(sch as unknown as SchemaData);
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id, isNew]);

  const stepIndex = session ? STEP_INDEX[session.current_step] ?? 0 : 0;

  const createSession = async () => {
    const s = await api.createCleaning(title || 'Untitled Cleaning');
    navigate(`/cleaning/${s.id}`, { replace: true });
    setSession(s);
  };

  const refresh = async () => {
    if (!session) return;
    const s = await api.getCleaning(session.id);
    setSession(s);
  };

  const selectDataset = async (datasetId: number) => {
    if (!session) return;
    await api.updateCleaning(session.id, { dataset_id: datasetId, current_step: 'link_project' });
    const sch = await api.getSchema(datasetId);
    setSchema(sch as unknown as SchemaData);
    await refresh();
  };

  const goToStep = async (step: string) => {
    if (!session) return;
    await api.updateCleaning(session.id, { current_step: step });
    await refresh();
  };

  const handleChat = async (content: string) => {
    if (!session) return;
    await api.cleaningChat(session.id, content);
    await refresh();
  };

  const generateScript = async () => {
    if (!session) return;
    const result = await api.generateScript(session.id);
    setSession({
      ...session,
      script_content: result.script_content,
      validation_result: result.validation_result,
      current_step: 'script_draft',
    });
  };

  const validateScript = async () => {
    if (!session) return;
    const result = await api.validateScript(session.id);
    setSession({ ...session, validation_result: result, current_step: 'validation' });
  };

  if (loading) return <div className="page"><p>Loading...</p></div>;

  return (
    <div className="page wizard-page">
      <header className="header">
        <Link to="/">← Dashboard</Link>
        <h1>Data Cleaning Wizard</h1>
      </header>

      <Stepper steps={CLEAN_STEPS} current={stepIndex} />
      {error && <p className="error">{error}</p>}

      {!session && (
        <div className="wizard-section">
          <h2>New Cleaning Session</h2>
          <label>
            Session Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Cohort cleaning pipeline" />
          </label>
          <button onClick={createSession}>Continue</button>
        </div>
      )}

      {session && stepIndex === 0 && (
        <div className="wizard-section">
          <h2>Select Dataset</h2>
          {datasets.map((d) => (
            <button key={d.id} className="dataset-card" onClick={() => selectDataset(d.id)}>
              <strong>{d.name}</strong>
              <p>{d.description}</p>
            </button>
          ))}
        </div>
      )}

      {session && stepIndex === 1 && (
        <div className="wizard-section">
          <h2>Link Project (Optional)</h2>
          <p>Optionally associate this cleaning session with a project document session.</p>
          <button onClick={() => goToStep('schema_explore')}>Skip — Explore Schema</button>
        </div>
      )}

      {session && stepIndex === 2 && schema && (
        <div className="wizard-section">
          <h2>Schema Exploration</h2>
          <SchemaBrowser tables={schema.tables} />
          <button onClick={() => goToStep('discussion')}>Start Discussion</button>
        </div>
      )}

      {session && stepIndex === 3 && (
        <div className="wizard-section split">
          <h2>Cleaning Discussion</h2>
          <ChatPanel
            messages={session.messages}
            onSend={handleChat}
            placeholder="Describe cleaning rules, joins, exclusions, derived variables..."
          />
          <button onClick={generateScript}>Generate Script</button>
        </div>
      )}

      {session && stepIndex === 4 && (
        <div className="wizard-section">
          <h2>Script Draft</h2>
          <textarea
            className="code-editor"
            value={session.script_content}
            onChange={async (e) => {
              await api.updateCleaning(session.id, { script_content: e.target.value });
              setSession({ ...session, script_content: e.target.value });
            }}
            rows={20}
          />
          <button onClick={validateScript}>Validate Script</button>
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
          <button onClick={() => goToStep('export')}>Proceed to Export</button>
        </div>
      )}

      {session && stepIndex === 6 && (
        <div className="wizard-section">
          <h2>Export</h2>
          <p>Download data_clean.py for your execution team.</p>
          <button onClick={() => api.exportCleaning(session.id)}>Download data_clean.py</button>
        </div>
      )}
    </div>
  );
}

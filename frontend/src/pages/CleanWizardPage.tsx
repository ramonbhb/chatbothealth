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
    const s = await api.createCleaning(title || 'Limpeza sem título');
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
    setSaveMessage(`Rascunho salvo em ${new Date(updated.updated_at).toLocaleString('pt-BR')}`);
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
        if (!cancelled) setError(e instanceof Error ? e.message : 'Não foi possível iniciar a discussão de planejamento');
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
      setError(e instanceof Error ? e.message : 'Falha na geração do script');
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
      setError(e instanceof Error ? e.message : 'Falha na validação');
    } finally {
      setValidating(false);
    }
  };

  if (loading) return <div className="page"><p>Carregando...</p></div>;

  return (
    <div className="page wizard-page">
      <header className="header">
        <div>
          <Link to="/cleaning">← Todas as sessões</Link>
          <h1>Assistente de Limpeza de Dados</h1>
          {session && (
            <p className="muted">
              Sessão #{session.id} · Última atualização {new Date(session.updated_at).toLocaleString('pt-BR')}
            </p>
          )}
        </div>
        {session && (
          <div className="header-actions">
            <button type="button" className="btn secondary" onClick={() => saveDraft(false)}>Salvar rascunho</button>
            <button type="button" className="btn secondary" onClick={() => saveDraft(true)}>Salvar e sair</button>
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
          <h2>Nova Sessão de Limpeza</h2>
          <label>
            Título da Sessão
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Pipeline de limpeza da coorte" />
          </label>
          <button type="button" onClick={createSession}>Continuar</button>
        </div>
      )}

      {session && stepIndex === 0 && (
        <div className="wizard-section">
          <h2>Selecionar Conjunto de Dados</h2>
          {datasets.map((d) => (
            <button
              key={d.id}
              type="button"
              className={`dataset-card ${session.dataset_id === d.id ? 'selected' : ''}`}
              onClick={() => selectDataset(d.id)}
            >
              <strong>{d.name}</strong>
              <p>{d.description}</p>
              {session.dataset_id === d.id && <span className="muted">Selecionado atualmente</span>}
            </button>
          ))}
          {session.dataset_id && (
            <div className="wizard-actions">
              <button type="button" onClick={() => goToStep('link_project')}>Continuar</button>
            </div>
          )}
        </div>
      )}

      {session && stepIndex === 1 && (
        <div className="wizard-section">
          <h2>Vincular Projeto (Opcional)</h2>
          <p className="muted">Opcionalmente, associe esta sessão de limpeza a uma sessão de documento de projeto.</p>
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('select_dataset')}>Voltar</button>
            <button type="button" onClick={() => goToStep('schema_explore')}>Pular — Explorar Dados</button>
          </div>
        </div>
      )}

      {session && stepIndex === 2 && (
        <div className="wizard-section">
          <h2>Explorar Dados</h2>
          <p className="muted">
            Revise a estrutura do banco de dados e até 10 linhas de amostra por tabela (exemplos desidentificados).
            Use isso para entender o que está disponível antes de planejar limpeza e modelagem.
          </p>
          {schema ? (
            <DatasetExplorer tables={schema.tables} />
          ) : (
            <LoadingPanel message="Carregando estrutura e amostras do conjunto de dados…" />
          )}
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('link_project')}>Voltar</button>
            <button type="button" onClick={startDiscussion}>Continuar para Discussão de Planejamento</button>
          </div>
        </div>
      )}

      {session && stepIndex === 3 && (
        <div className="wizard-section split">
          <h2>Discussão de Planejamento</h2>
          <p className="muted">
            Trabalhe seus objetivos de modelagem e limpeza em linguagem simples. O assistente perguntará sobre
            definição da coorte, filtros, junções e o conjunto final de dados necessário.
          </p>
          <div className="topic-checklist">
            <strong>Tópicos que abordaremos</strong>
            <ul>
              {CLEAN_BUSINESS_TOPICS.map((topic) => (
                <li key={topic}>{topic}</li>
              ))}
            </ul>
          </div>
          {kickoffLoading && session.messages.length === 0 ? (
            <LoadingPanel message="Analisando a estrutura e amostras dos seus dados…" />
          ) : (
            <ChatPanel
              messages={session.messages}
              onSend={handleChat}
              placeholder="Descreva seu objetivo de modelagem, regras da coorte, filtros ou transformações..."
            />
          )}
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('schema_explore')}>Voltar</button>
            <button type="button" onClick={generateScript} disabled={generating}>
              {generating ? 'Gerando…' : 'Gerar Script'}
            </button>
          </div>
          {generating && <LoadingPanel message="Gerando data_clean.py a partir da sua discussão…" />}
        </div>
      )}

      {session && stepIndex === 4 && (
        <div className="wizard-section">
          <h2>Rascunho do Script</h2>
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
            <button type="button" className="btn secondary" onClick={() => goToStep('discussion')}>Voltar</button>
            <button type="button" onClick={validateScript} disabled={validating}>
              {validating ? 'Validando…' : 'Validar Script'}
            </button>
          </div>
          {validating && <LoadingPanel message="Validando sintaxe e segurança do script…" />}
        </div>
      )}

      {session && stepIndex === 5 && (
        <div className="wizard-section">
          <h2>Resultados da Validação</h2>
          <div className={`validation-result ${session.validation_result?.valid ? 'valid' : 'invalid'}`}>
            <p>Sintaxe: {session.validation_result?.syntax_ok ? 'OK' : 'Falhou'}</p>
            <p>Segurança: {session.validation_result?.safety_ok ? 'OK' : 'Falhou'}</p>
            <p>Lint: {session.validation_result?.lint_ok ? 'OK' : 'Falhou'}</p>
            <ul>
              {((session.validation_result?.issues as string[]) || []).map((issue, i) => (
                <li key={i}>{issue}</li>
              ))}
            </ul>
          </div>
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('script_draft')}>Voltar ao script</button>
            <button type="button" onClick={() => goToStep('export')}>Ir para Exportação</button>
          </div>
        </div>
      )}

      {session && stepIndex === 6 && (
        <div className="wizard-section">
          <h2>Exportar</h2>
          <p>Baixe o data_clean.py para sua equipe de execução.</p>
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('validation')}>Voltar</button>
            <button type="button" className="btn secondary" onClick={() => goToStep('script_draft')}>Editar script</button>
            <button type="button" onClick={() => api.exportCleaning(session.id)}>Baixar data_clean.py</button>
          </div>
        </div>
      )}
    </div>
  );
}

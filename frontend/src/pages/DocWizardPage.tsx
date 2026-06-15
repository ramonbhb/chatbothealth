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
    const s = await api.createProject(title || 'Projeto sem título');
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
    setSaveMessage(`Rascunho salvo em ${new Date(saved.updated_at).toLocaleString('pt-BR')}`);
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
      setError('Cole pelo menos 20 caracteres para importar.');
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
        setError('Falha na importação: nenhuma seção foi extraída. Tente novamente ou preencha as seções manualmente.');
        return;
      }
      setSession(updated);
      setFullText('');
      setSaveMessage(`Importado em ${filled} seção${filled === 1 ? '' : 'ões'}. Revise e edite abaixo.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Falha na importação');
    } finally {
      setImporting(false);
    }
  };

  const skipToManual = async () => {
    setError('');
    await ensureSession();
    await goToStep('review');
    setSaveMessage('Preencha cada seção manualmente abaixo. Você pode mudar para o chat guiado a qualquer momento.');
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
          ? `Copiado para "${sectionLabel(sectionKey)}": ${preview}`
          : `Nenhum conteúdo extraído para "${sectionLabel(sectionKey)}". Continue o chat e tente novamente.`
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Falha na extração');
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
      setError(e instanceof Error ? e.message : 'Falha no controle de qualidade');
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

  if (loading) return <div className="page"><p>Carregando...</p></div>;

  const showImportScreen = !session || stepIndex === 0;

  return (
    <div className="page wizard-page">
      <header className="header">
        <div>
          <Link to="/projects">← Todas as sessões</Link>
          <h1>Assistente de Documento do Projeto</h1>
          {session && <p className="muted">Sessão #{session.id} · Última atualização {new Date(session.updated_at).toLocaleString('pt-BR')}</p>}
        </div>
        {session && (
          <div className="header-actions">
            <button type="button" className="btn secondary" onClick={() => saveDraft(false)}>Salvar rascunho</button>
            <button type="button" className="btn secondary" onClick={() => saveDraft(true)}>Salvar e sair</button>
          </div>
        )}
      </header>

      {session && (
        <Stepper steps={DOC_STEPS} current={stepIndex} onStepClick={goToStepIndex} />
      )}
      {!session && <Stepper steps={DOC_STEPS} current={0} />}

      <div className="purpose-banner">
        <strong>Objetivo:</strong> Capturar uma visão completa do seu estudo —
        <ul className="collection-goals">
          {PROJECT_COLLECTION_GOALS.map((g) => (
            <li key={g}>{g}</li>
          ))}
        </ul>
        Cole o texto completo, use o chat guiado ou preencha as seções manualmente — o que funcionar melhor para você.
      </div>

      {saveMessage && <p className="save-message">{saveMessage}</p>}
      {error && <pre className="error debug-error">{error}</pre>}

      {showImportScreen && (
        <div className="wizard-section">
          <h2>Inicie o documento do seu projeto</h2>
          <p className="muted">
            Forneça seu projeto no formato que preferir. Focamos em dados, métodos
            e entregáveis (tabelas, gráficos, modelos).
          </p>
          <label>
            Título do Projeto
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={async () => {
                if (session && title !== session.title) {
                  const updated = await api.updateProject(session.id, { title });
                  setSession(updated);
                }
              }}
              placeholder="Meu Projeto de Ciência de Dados em Saúde"
            />
          </label>

          <div className="import-panel import-panel-primary">
            <h3>Cole o texto completo do projeto</h3>
            <p className="muted">
              Cole uma descrição completa do projeto e o assistente dividirá automaticamente em todas as seções predefinidas.
            </p>
            <textarea
              value={fullText}
              onChange={(e) => setFullText(e.target.value)}
              rows={14}
              placeholder="Cole o texto completo do seu projeto aqui..."
            />
            <button type="button" onClick={importFullText} disabled={importing || fullText.trim().length < 20}>
              {importing ? 'Dividindo com IA…' : 'Importar e dividir em seções'}
            </button>
          </div>

          <div className="wizard-actions import-alternatives">
            <button type="button" className="btn secondary" onClick={skipToManual}>
              Pular — preencher seções manualmente
            </button>
            <button type="button" className="btn secondary" onClick={startGuidedChat}>
              Pular — usar chat guiado
            </button>
          </div>
        </div>
      )}

      {session && stepIndex === 1 && (
        <div className="wizard-section split">
          <div>
            <h2>Coleta Guiada</h2>
            <p className="muted">
              Converse sobre uma seção por vez. O chat <strong>não</strong> é copiado automaticamente —
              clique em <strong>Extrair seção</strong> para copiar a conversa para o campo da seção abaixo.
            </p>
            <p>Foco atual: <strong>{sectionLabel(activeSection)}</strong></p>
            {DOC_SECTION_HINTS[activeSection] && (
              <p className="section-hint">{DOC_SECTION_HINTS[activeSection]}</p>
            )}
            {hasSectionContent(activeSection) && (
              <p className="section-filled">✓ Esta seção já tem conteúdo salvo</p>
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
                <strong>Prévia do conteúdo salvo</strong>
                <p>{String(session.section_data[activeSection]).slice(0, 300)}{String(session.section_data[activeSection]).length > 300 ? '…' : ''}</p>
              </div>
            )}
          </div>
          <ChatPanel
            messages={session.messages}
            onSend={handleChat}
            placeholder={`Converse sobre a seção ${sectionLabel(activeSection)}…`}
          />
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('basics')}>Voltar</button>
            <button type="button" className="btn secondary" onClick={() => extractSection(activeSection)} disabled={extracting}>
              {extracting ? 'Extraindo…' : 'Extrair seção do chat'}
            </button>
            <button type="button" onClick={() => goToStep('review')}>Ir para revisão</button>
          </div>
        </div>
      )}

      {session && stepIndex === 2 && (
        <div className="wizard-section">
          <h2>Revisão de Seções</h2>
          <p className="muted">
            Edite qualquer seção diretamente. Priorize <strong>Dados</strong>, <strong>Métodos</strong>,
            <strong> Artefatos Esperados</strong> e <strong>Fluxo de Análise</strong>.
          </p>
          {DOC_SECTIONS.map((s) => (
            <div key={s.key} className="review-block">
              <h3>{s.label}</h3>
              <textarea
                value={String(session.section_data[s.key] || '')}
                onChange={(e) => updateSection(s.key, e.target.value)}
                onBlur={persistSections}
                rows={4}
                placeholder={`Digite o conteúdo para ${s.label}…`}
              />
            </div>
          ))}
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('basics')}>Voltar à importação</button>
            <button type="button" className="btn secondary" onClick={() => goToStep('intake')}>Usar chat guiado</button>
            <button type="button" onClick={() => goToStep('quality')}>Executar controle de qualidade</button>
          </div>
        </div>
      )}

      {session && stepIndex === 3 && (
        <div className="wizard-section">
          <h2>Controle de Qualidade</h2>
          <p className="muted">Revise seu documento com uma lista de verificação gerada pelo assistente.</p>
          <button type="button" onClick={runQuality} disabled={checklistLoading}>
            {checklistLoading ? 'Executando lista…' : 'Executar lista de verificação'}
          </button>
          {checklistLoading && (
            <LoadingPanel message="Executando controle de qualidade — revisando suas seções…" />
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
            <p className="muted">Nenhum resultado ainda. Clique em Executar lista de verificação para avaliar seu documento.</p>
          )}
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('review')} disabled={checklistLoading}>Voltar à revisão</button>
            <button type="button" onClick={() => goToStep('export')} disabled={checklistLoading}>Ir para exportação</button>
          </div>
        </div>
      )}

      {session && stepIndex === 4 && (
        <div className="wizard-section">
          <h2>Exportar</h2>
          <p>Baixe o documento do projeto como project.docx</p>
          <div className="wizard-actions">
            <button type="button" className="btn secondary" onClick={() => goToStep('review')}>Editar seções</button>
            <button type="button" onClick={() => api.exportProject(session.id)}>Baixar project.docx</button>
          </div>
        </div>
      )}
    </div>
  );
}

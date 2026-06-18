export interface CleaningVersion {
  id: number;
  session_id: number;
  version_number: number;
  label: string;
  script_content: string;
  validation_result: Record<string, unknown>;
  messages_snapshot: Array<{ role: string; content: string }>;
  notes: string;
  created_at: string;
}

interface CleaningVersionsPanelProps {
  versions: CleaningVersion[];
  hasDraftScript: boolean;
  onSaveVersion: (label: string, notes: string) => Promise<void>;
  onNewVersion: (saveCurrent: boolean, currentLabel: string, notes: string) => Promise<void>;
  onRestore: (versionId: number) => Promise<void>;
  onExport: (versionId: number) => Promise<void>;
  saving?: boolean;
}

export function CleaningVersionsPanel({
  versions,
  hasDraftScript,
  onSaveVersion,
  onNewVersion,
  onRestore,
  onExport,
  saving = false,
}: CleaningVersionsPanelProps) {
  const handleSave = async () => {
    const label = window.prompt('Nome da versão (opcional):') ?? '';
    const notes = window.prompt('Notas sobre esta versão (opcional):') ?? '';
    await onSaveVersion(label, notes);
  };

  const handleNew = async () => {
    const saveCurrent = hasDraftScript
      ? window.confirm(
          'Deseja salvar o rascunho atual antes de iniciar uma nova versão?\n\n'
          + 'Cada nova versão parte da base zerada (tabelas originais), sem usar saídas de versões anteriores.'
        )
      : false;
    let currentLabel = '';
    if (saveCurrent) {
      currentLabel = window.prompt('Nome para salvar o rascunho atual:') ?? '';
    }
    const notes = window.prompt('Notas (opcional):') ?? '';
    await onNewVersion(saveCurrent, currentLabel, notes);
  };

  return (
    <div className="cleaning-versions-panel">
      <div className="versions-header">
        <strong>Versões de limpeza</strong>
        <p className="muted small">
          Cada versão salva é independente e parte da base zerada (tabelas fonte originais).
        </p>
      </div>
      <div className="versions-actions">
        <button
          type="button"
          className="btn secondary small"
          onClick={handleSave}
          disabled={saving || !hasDraftScript}
          title={hasDraftScript ? undefined : 'Gere ou edite um script antes de salvar'}
        >
          Salvar versão atual
        </button>
        <button type="button" className="btn secondary small" onClick={handleNew} disabled={saving}>
          Nova versão (base zerada)
        </button>
      </div>
      {versions.length === 0 ? (
        <p className="muted small">Nenhuma versão salva ainda.</p>
      ) : (
        <ul className="versions-list">
          {versions.map((v) => (
            <li key={v.id} className="version-item">
              <div>
                <strong>{v.label}</strong>
                <span className="muted"> · v{v.version_number}</span>
                <br />
                <small className="muted">
                  {new Date(v.created_at).toLocaleString('pt-BR')}
                  {v.validation_result?.valid ? ' · ✓ válida' : v.script_content ? ' · pendente' : ''}
                </small>
                {v.notes && <p className="version-notes">{v.notes}</p>}
              </div>
              <div className="version-item-actions">
                <button type="button" className="btn secondary small" onClick={() => onRestore(v.id)}>
                  Abrir
                </button>
                <button
                  type="button"
                  className="btn secondary small"
                  onClick={() => onExport(v.id)}
                  disabled={!v.script_content}
                >
                  Exportar
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

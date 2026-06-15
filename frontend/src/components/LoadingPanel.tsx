interface LoadingPanelProps {
  message?: string;
}

export function LoadingPanel({ message = 'Carregando…' }: LoadingPanelProps) {
  return (
    <div className="loading-panel" role="status" aria-live="polite" aria-busy="true">
      <div className="loading-spinner" aria-hidden="true" />
      <p>{message}</p>
    </div>
  );
}

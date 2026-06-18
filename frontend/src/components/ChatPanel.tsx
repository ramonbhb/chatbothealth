import { useState } from 'react';

interface ChatPanelProps {
  messages: Array<{ role: string; content: string }>;
  onSend: (content: string) => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatPanel({ messages, onSend, disabled, placeholder }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || sending) return;
    setSending(true);
    try {
      await onSend(input.trim());
      setInput('');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.length === 0 && !sending && (
          <p className="chat-empty">Inicie a conversa. O assistente fará perguntas guiadas.</p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg ${msg.role}`}>
            <strong>{msg.role === 'user' ? 'Você' : 'Assistente'}</strong>
            <div className="chat-bubble">
              <p>{msg.content}</p>
            </div>
          </div>
        ))}
        {sending && (
          <div className="chat-msg assistant typing">
            <strong>Assistente</strong>
            <div className="chat-bubble">
              <p>Preparando resposta…</p>
            </div>
          </div>
        )}
      </div>
      <div className="chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={placeholder || 'Digite sua mensagem...'}
          disabled={disabled || sending}
          rows={3}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
        />
        <button onClick={handleSend} disabled={disabled || sending || !input.trim()}>
          {sending ? 'Aguardando…' : 'Enviar'}
        </button>
      </div>
    </div>
  );
}

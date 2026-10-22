import { useState, useEffect, useRef, type FormEvent } from 'react';

const API_URL = 'http://localhost:8011';

type Message = {
  role: 'user' | 'assistant';
  content: string;
};

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setLoading(true);
    setError(null);

    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage, session_id: sessionId }),
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ Error: Could not get response' }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = async () => {
    try {
      await fetch(`${API_URL}/chat/${sessionId}`, { method: 'DELETE' });
      setMessages([]);
      setError(null);
    } catch (err) {
      setError('Failed to clear chat');
    }
  };

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`);
      if (!res.ok) throw new Error('Backend not responding');
      const data = await res.json();
      setError(null);
      return data.model;
    } catch {
      setError('⚠️ Cannot connect to backend. Make sure it\'s running on port 8011.');
      return null;
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="app">
      <header>
        <h1>🤖 AI Chatbot</h1>
        <span className="model-badge">Qwen3.8-27B</span>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <div className="chat-container">
        <div className="messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-bubble">
                <span className="role-label">{msg.role === 'user' ? 'You' : 'AI'}</span>
                <p>{msg.content}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={sendMessage} className="input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={loading ? 'Thinking...' : 'Type a message...'}
            disabled={loading}
            autoFocus
          />
          <button type="submit" disabled={loading || !input.trim()}>
            {loading ? '⏳' : '➤'}
          </button>
        </form>
      </div>

      <footer>
        <button onClick={clearChat} className="clear-btn">Clear Chat</button>
        <button onClick={checkHealth} className="health-btn">Reconnect</button>
      </footer>
    </div>
  );
}

export default App;
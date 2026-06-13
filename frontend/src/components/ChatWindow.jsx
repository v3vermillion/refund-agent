import { useEffect, useRef, useState } from "react";
import { sendChat } from "../api.js";
import DecisionBadge from "./DecisionBadge.jsx";

// Stable per-conversation session id, reused across turns.
function newSessionId() {
  return (crypto.randomUUID && crypto.randomUUID()) || `sess-${Date.now()}`;
}

const SUGGESTIONS = [
  "I'd like a refund on my Wireless Headphones. Email jane.doe@example.com, order ORD-1001.",
  "Refund my 4K OLED Television. Email diego.romero@example.com, order ORD-1006.",
  "Return my Clearance Jacket. Email aisha.khan@example.com, order ORD-1004.",
];

export default function ChatWindow() {
  const [sessionId, setSessionId] = useState(newSessionId);
  const [messages, setMessages] = useState([
    {
      role: "agent",
      text: "Hi! I can help you request a refund. To get started, what's the email on your account?",
      decision: null,
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, busy]);

  async function submit(text) {
    const content = (text ?? input).trim();
    if (!content || busy) return;
    setInput("");
    // [[retry]] is an internal demo trigger consumed by the backend — don't render it in the chat.
    const shown = content.replace(/\[\[retry\]\]/gi, "").trim() || content;
    setMessages((m) => [...m, { role: "user", text: shown }]);
    setBusy(true);
    try {
      const res = await sendChat(sessionId, content);
      setMessages((m) => [
        ...m,
        { role: "agent", text: res.reply, decision: res.decision, traceId: res.trace_id },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: "agent",
          text: "⚠️ I couldn't reach the backend. Make sure it's running on port 8000.",
          decision: null,
          error: true,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function resetConversation() {
    setSessionId(newSessionId());
    setMessages([
      {
        role: "agent",
        text: "New conversation started. What's the email on your account?",
        decision: null,
      },
    ]);
  }

  return (
    <div className="chat">
      <div className="chat-head">
        <div>
          <h2>Chat</h2>
          <p className="muted">Verify with an email, then reference an order ID to request a refund.</p>
        </div>
        <button className="ghost-btn" onClick={resetConversation}>
          New conversation
        </button>
      </div>

      <div className="messages" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`row row-${m.role}`}>
            <div className={`bubble bubble-${m.role} ${m.error ? "bubble-error" : ""}`}>
              {m.role === "agent" && m.decision && (
                <div className="bubble-decision">
                  <DecisionBadge decision={m.decision} />
                </div>
              )}
              <div className="bubble-text">{m.text}</div>
            </div>
          </div>
        ))}
        {busy && (
          <div className="row row-agent">
            <div className="bubble bubble-agent">
              <div className="typing">
                <span />
                <span />
                <span />
              </div>
            </div>
          </div>
        )}
      </div>

      {messages.length <= 1 && (
        <div className="suggestions">
          {SUGGESTIONS.map((s, i) => (
            <button key={i} className="chip" onClick={() => submit(s)} disabled={busy}>
              {s.length > 52 ? s.slice(0, 52) + "…" : s}
            </button>
          ))}
        </div>
      )}

      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          disabled={busy}
          autoFocus
        />
        <button type="submit" disabled={busy || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}

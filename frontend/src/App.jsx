import { useEffect, useState } from "react";
import ChatWindow from "./components/ChatWindow.jsx";
import AdminTraces from "./components/AdminTraces.jsx";
import { fetchHealth } from "./api.js";

export default function App() {
  const [view, setView] = useState("chat");
  const [online, setOnline] = useState(null);

  useEffect(() => {
    let active = true;
    const ping = async () => {
      const ok = await fetchHealth();
      if (active) setOnline(ok);
    };
    ping();
    const id = setInterval(ping, 8000);
    return () => {
      active = false;
      clearInterval(id);
    };
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">↺</span>
          <div>
            <div className="brand-name">Refund Agent</div>
            <div className="brand-sub">AI customer support · refunds</div>
          </div>
        </div>

        <nav className="tabs" role="tablist">
          <button
            role="tab"
            aria-selected={view === "chat"}
            className={view === "chat" ? "tab active" : "tab"}
            onClick={() => setView("chat")}
          >
            Chat
          </button>
          <button
            role="tab"
            aria-selected={view === "admin"}
            className={view === "admin" ? "tab active" : "tab"}
            onClick={() => setView("admin")}
          >
            Admin
          </button>
        </nav>

        <div className="health" title="Backend health">
          <span
            className={
              online === null ? "dot dot-unknown" : online ? "dot dot-ok" : "dot dot-down"
            }
          />
          <span className="health-label">
            {online === null ? "checking…" : online ? "backend online" : "backend offline"}
          </span>
        </div>
      </header>

      <main className="main">
        {view === "chat" ? <ChatWindow /> : <AdminTraces />}
      </main>
    </div>
  );
}

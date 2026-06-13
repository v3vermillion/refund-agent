import { useEffect, useState } from "react";
import { fetchTraces } from "../api.js";
import DecisionBadge from "./DecisionBadge.jsx";

export default function AdminTraces() {
  const [traces, setTraces] = useState([]);
  const [expanded, setExpanded] = useState(() => new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  async function load() {
    try {
      const data = await fetchTraces();
      setTraces(data);
      setError(false);
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, []);

  function toggle(id) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  const flaggedCount = traces.filter((t) => t.injection_flagged).length;

  return (
    <div className="admin">
      <div className="admin-head">
        <div>
          <h2>Admin · reasoning traces</h2>
          <p className="muted">
            Every turn's tool I/O, reasoning, retries, tokens, latency, and decision.
          </p>
        </div>
        <div className="admin-stats">
          <Stat label="Traces" value={traces.length} />
          <Stat label="Injection flags" value={flaggedCount} tone={flaggedCount ? "alert" : null} />
          <button className="ghost-btn" onClick={load}>
            Refresh
          </button>
        </div>
      </div>

      {loading && <div className="empty">Loading traces…</div>}
      {error && <div className="empty error">Couldn't reach the backend on port 8000.</div>}
      {!loading && !error && traces.length === 0 && (
        <div className="empty">No traces yet — send a message in the Chat tab.</div>
      )}

      <div className="trace-list">
        {traces.map((t) => {
          const open = expanded.has(t.trace_id);
          return (
            <div
              key={t.trace_id}
              className={`trace-card ${t.injection_flagged ? "trace-flagged" : ""}`}
            >
              <div
                className="trace-summary"
                role="button"
                tabIndex={0}
                onClick={() => toggle(t.trace_id)}
                onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && toggle(t.trace_id)}
              >
                <span className="caret">{open ? "▾" : "▸"}</span>
                <div className="trace-summary-main">
                  <div className="trace-user">{t.user_message}</div>
                  <div className="trace-meta">
                    <span>{new Date(t.timestamp).toLocaleTimeString()}</span>
                    <span>·</span>
                    <span>{t.tokens} tok</span>
                    <span>·</span>
                    <span>{t.latency_ms} ms</span>
                    {t.retries > 0 && (
                      <>
                        <span>·</span>
                        <span className="retry">{t.retries} retr{t.retries === 1 ? "y" : "ies"}</span>
                      </>
                    )}
                  </div>
                </div>
                <div className="trace-badges">
                  {t.injection_flagged && <span className="badge badge-injection">⚠ Injection</span>}
                  <DecisionBadge decision={t.decision} />
                </div>
              </div>

              {open && (
                <div className="trace-detail">
                  <Field label="Agent reply" value={t.agent_reply} block />
                  <Field label="Reasoning" value={t.reasoning} block />

                  <div className="trace-field">
                    <div className="field-label">Tool calls ({t.tool_calls.length})</div>
                    {t.tool_calls.length === 0 ? (
                      <div className="field-value muted">none</div>
                    ) : (
                      <div className="tool-calls">
                        {t.tool_calls.map((tc, i) => (
                          <div className="tool-call" key={i}>
                            <div className="tool-name">{tc.tool}</div>
                            <pre className="tool-io">
                              <span className="io-label">in </span>
                              {JSON.stringify(tc.input)}
                            </pre>
                            <pre className="tool-io">
                              <span className="io-label">out</span>
                              {JSON.stringify(tc.output)}
                            </pre>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="trace-stats-row">
                    <MiniStat label="Decision" value={t.decision || "—"} />
                    <MiniStat label="Tokens" value={t.tokens} />
                    <MiniStat label="Latency" value={`${t.latency_ms} ms`} />
                    <MiniStat label="Retries" value={t.retries} />
                    <MiniStat label="Session" value={t.session_id.slice(0, 8)} />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Field({ label, value, block }) {
  return (
    <div className="trace-field">
      <div className="field-label">{label}</div>
      <div className={`field-value ${block ? "field-block" : ""}`}>{value || "—"}</div>
    </div>
  );
}

function Stat({ label, value, tone }) {
  return (
    <div className={`stat ${tone === "alert" ? "stat-alert" : ""}`}>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

function MiniStat({ label, value }) {
  return (
    <div className="mini-stat">
      <span className="mini-label">{label}</span>
      <span className="mini-value">{value}</span>
    </div>
  );
}

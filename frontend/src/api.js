// Thin API client. Knows only the locked contract — no business logic.
// In dev, Vite proxies /api → http://localhost:8000 (see vite.config.js).

const BASE = "/api";

export async function sendChat(sessionId, message) {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json();
}

export async function fetchTraces() {
  const res = await fetch(`${BASE}/traces`);
  if (!res.ok) throw new Error(`Traces failed: ${res.status}`);
  return res.json();
}

export async function fetchHealth() {
  try {
    const res = await fetch(`${BASE}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

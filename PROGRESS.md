# PROGRESS — Refund Agent build log

Living continuity doc. Update after each completed step so a fresh session can resume cleanly.

## Build checklist (from SPEC §10)

- [x] Spec + contract locked (SPEC.md created)
- [x] Foundational files: SPEC.md, scripts/seed_data.py, README.md (already present, matches)
- [x] Synthetic data seeded (15 customers, 17 orders covering every branch)
- [x] backend/store.py — JSON loader + lookups + in-memory trace log
- [x] backend/tools.py — the 4 tools (lookup_order computes days_since_purchase + within_window)
- [x] backend/data/refund_policy.md — policy text fed to the agent
- [x] backend/agent.py — agent loop + system prompt + policy reasoning + injection handling
- [x] backend/main.py — FastAPI: POST /chat, GET /traces, GET /health
- [x] backend/requirements.txt + .env.example + .gitignore (.env ignored)
- [x] frontend/ — Vite + React: ChatWindow + AdminTraces
- [x] .github/workflows/ci.yml — install deps + run tests on push
- [x] backend/tests/ — ~12 injection/policy cases asserting correct decisions
- [x] Verified: backend deps install, imports clean, /health + /traces respond, frontend builds,
      deterministic tool tests pass (8 passed). Live-agent injection suite needs ANTHROPIC_API_KEY.

## Decisions & state

- **Model:** `claude-haiku-4-5-20251001` for the agent loop (cost-efficient, supports tool use).
- **Fixed "today":** 2026-06-08 (matches seed anchor) — date math done in Python in tools.py.
- **Decision wire values:** `APPROVED | DENIED | ESCALATED` (null until a final decision is reached).
- **Architecture separation:** tools fetch/compute facts only; ALL policy reasoning is in agent.py.
  `issue_refund` is idempotent (errors on already_refunded) and is the *only* tool that mutates.
- **Decision signaling:** the agent emits a machine-readable `<<<DECISION:...>>>` /
  `<<<INJECTION>>>` sentinel that the backend parses and strips from the user-facing reply, so
  the trace's `decision` / `injection_flagged` fields are exact, not regex-guessed from prose.
- **Sessions:** in-memory per `session_id` (conversation history + verified customer identity).
- **Traces:** in-memory list in store.py, newest-first via GET /traces.

## Test strategy

`backend/tests/test_injection.py` runs the SPEC §9 cases. Tests that need a live model are
guarded by `ANTHROPIC_API_KEY`; the deterministic tool/policy-fact tests always run (so CI is
green without a key, and the full agent suite runs locally with a key).

"""
main.py — FastAPI app exposing exactly the three locked endpoints:

  POST /chat    — the single conversational endpoint
  GET  /traces  — all reasoning traces for the admin dashboard
  GET  /health  — liveness check

This layer is thin: it validates the request, delegates to the agent, records a
trace, and shapes the response per the API contract in SPEC.md §4. No business
logic lives here.
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv

# Load .env from the repo root (one level up from backend/) and from backend/,
# so `uvicorn main:app` picks up ANTHROPIC_API_KEY without any extra config.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_BACKEND_DIR, "..", ".env"))
load_dotenv(os.path.join(_BACKEND_DIR, ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import store
from agent import run_agent_turn

app = FastAPI(title="Refund Agent", version="1.0.0")

# The Vite dev server runs on a different origin; allow the browser to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- request/response models (the locked contract) ------------------------
class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    decision: str | None
    injection_flagged: bool
    trace_id: str


# Demo-only: include this marker anywhere in a chat message to inject ONE real
# transient rate-limit (HTTP 429) on that turn's first model call. It exercises
# the genuine retry/backoff path so the trace shows honest retry telemetry; the
# marker is stripped before the message is processed or stored. Normal messages
# never retry. See agent._injected_rate_limit.
DEMO_RETRY_MARKER = "[[retry]]"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    session_id = req.session_id or str(uuid.uuid4())
    session = store.get_session(session_id)

    # Demo-only: opt in to a real injected retry via the marker, then strip it so
    # the stored/displayed message stays clean. Normal messages never retry.
    message = req.message
    inject_retry_faults = 0
    if DEMO_RETRY_MARKER in message.lower():
        inject_retry_faults = 1
        message = re.sub(re.escape(DEMO_RETRY_MARKER), "", message, flags=re.IGNORECASE).strip()

    result = run_agent_turn(session["history"], message, inject_retry_faults=inject_retry_faults)

    trace_id = str(uuid.uuid4())
    store.add_trace(
        {
            "trace_id": trace_id,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_message": message,
            "agent_reply": result["reply"],
            "decision": result["decision"],
            "tool_calls": result["tool_calls"],
            "reasoning": result["reasoning"],
            "retries": result["retries"],
            "retry_events": result.get("retry_events", []),
            "tokens": result["tokens"],
            "latency_ms": result["latency_ms"],
            "injection_flagged": result["injection_flagged"],
        }
    )

    return ChatResponse(
        session_id=session_id,
        reply=result["reply"],
        decision=result["decision"],
        injection_flagged=result["injection_flagged"],
        trace_id=trace_id,
    )


@app.get("/traces")
def traces() -> list[dict]:
    return store.get_traces()

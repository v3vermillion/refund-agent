"""
Resilience tests for transient API failures — deterministic, no real key.

These mock the Anthropic client so they always run in CI. They lock in that a
rate-limit (429) or a transient 5xx degrades into a polite reply (HTTP 200 from
/chat) instead of crashing, and that the bounded backoff retries then succeeds.
"""

import types

import anthropic
import httpx
import agent


class _FakeClient:
    def __init__(self, behavior):
        self.messages = types.SimpleNamespace(create=behavior)


def _status_error(cls, status, retry_after=None):
    headers = {"retry-after": retry_after} if retry_after is not None else {}
    req = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    resp = httpx.Response(status, headers=headers, request=req)
    return cls("boom", response=resp, body=None)


def test_rate_limit_degrades_gracefully(monkeypatch):
    monkeypatch.setattr(agent.time, "sleep", lambda *a, **k: None)

    def always_429(**kwargs):
        raise _status_error(anthropic.RateLimitError, 429, retry_after="0")

    monkeypatch.setattr(agent, "_get_client", lambda: _FakeClient(always_429))

    result = agent.run_agent_turn([], "I want a refund")

    assert result["decision"] is None
    assert result["injection_flagged"] is False
    assert "try again" in result["reply"].lower() or "high demand" in result["reply"].lower()
    assert result["retries"] >= agent.MAX_API_RETRIES


def test_transient_5xx_then_success(monkeypatch):
    monkeypatch.setattr(agent.time, "sleep", lambda *a, **k: None)
    calls = {"n": 0}

    def flaky(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise _status_error(anthropic.InternalServerError, 503)
        usage = types.SimpleNamespace(input_tokens=10, output_tokens=5)
        text = types.SimpleNamespace(type="text", text="Hi <<<DECISION:NONE>>>")
        return types.SimpleNamespace(usage=usage, content=[text], stop_reason="end_turn")

    resp, retries = agent._create_message(
        _FakeClient(flaky), model="m", max_tokens=1, system="s", tools=[], messages=[]
    )

    assert retries == 1
    assert resp.stop_reason == "end_turn"


def test_retry_after_header_parsed():
    err = _status_error(anthropic.RateLimitError, 429, retry_after="2")
    assert agent._retry_after_seconds(err) == 2.0
    err_none = _status_error(anthropic.RateLimitError, 429)
    assert agent._retry_after_seconds(err_none) is None

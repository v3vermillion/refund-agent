"""
store.py — the data layer.

Responsibilities (and ONLY these):
  * load the seeded JSON (customers + orders) once at import,
  * expose simple lookups over that data,
  * hold the in-memory trace log that the admin dashboard reads,
  * hold per-session conversation state (history + verified identity).

There is deliberately NO refund/policy logic in here. This module fetches and
stores facts; the agent reasons about them. Swapping these JSON files for a
real database later would not change any other module's interface.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Optional

# --- paths -------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_HERE, "data")
_CUSTOMERS_PATH = os.path.join(_DATA_DIR, "customers.json")
_ORDERS_PATH = os.path.join(_DATA_DIR, "orders.json")
_POLICY_PATH = os.path.join(_DATA_DIR, "refund_policy.md")


def _load_json(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing data file: {path}\n"
            "Run `python scripts/seed_data.py` first to generate the mock CRM."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- in-memory data (loaded once) -------------------------------------------
_customers: list[dict[str, Any]] = _load_json(_CUSTOMERS_PATH)
_orders: list[dict[str, Any]] = _load_json(_ORDERS_PATH)

# index for O(1) lookups
_customers_by_email: dict[str, dict[str, Any]] = {
    c["email"].lower(): c for c in _customers
}
_orders_by_id: dict[str, dict[str, Any]] = {o["order_id"]: o for o in _orders}


# --- refund policy text ------------------------------------------------------
def load_policy_text() -> str:
    """The written refund policy — the agent's single source of truth."""
    if not os.path.exists(_POLICY_PATH):
        raise FileNotFoundError(f"Missing policy file: {_POLICY_PATH}")
    with open(_POLICY_PATH, "r", encoding="utf-8") as f:
        return f.read()


# --- lookups (read-only, no policy logic) ------------------------------------
def get_customer_by_email(email: str) -> Optional[dict[str, Any]]:
    if not email:
        return None
    return _customers_by_email.get(email.strip().lower())


def get_order(order_id: str) -> Optional[dict[str, Any]]:
    if not order_id:
        return None
    return _orders_by_id.get(order_id.strip())


def get_orders_for_customer(customer_id: str) -> list[dict[str, Any]]:
    return [o for o in _orders if o["customer_id"] == customer_id]


def mark_refunded(order_id: str) -> bool:
    """Flip already_refunded -> True (in-memory). Returns False if not found."""
    order = _orders_by_id.get(order_id)
    if order is None:
        return False
    order["already_refunded"] = True
    order["status"] = "returned"
    return True


# --- trace log (powers GET /traces) ------------------------------------------
_traces: list[dict[str, Any]] = []
_traces_lock = threading.Lock()


def add_trace(trace: dict[str, Any]) -> None:
    with _traces_lock:
        _traces.append(trace)


def get_traces() -> list[dict[str, Any]]:
    """Newest-first, so the admin dashboard shows the latest run on top."""
    with _traces_lock:
        return list(reversed(_traces))


# --- per-session conversation state ------------------------------------------
# Maps session_id -> {"history": [...anthropic messages...],
#                     "customer": {...} | None}
_sessions: dict[str, dict[str, Any]] = {}
_sessions_lock = threading.Lock()


def get_session(session_id: str) -> dict[str, Any]:
    with _sessions_lock:
        if session_id not in _sessions:
            _sessions[session_id] = {"history": [], "customer": None}
        return _sessions[session_id]

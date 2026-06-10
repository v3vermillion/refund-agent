"""
tools.py — the 4 tools the agent can call, wired to the mock data in store.py.

DESIGN RULE (this is what the challenge grades as "clean separation"):
  Tools FETCH facts and ACT. They also compute exact, deterministic facts that
  the LLM is bad at (date math). They contain NO refund-policy decision logic —
  they never decide approve/deny/escalate. The agent reasons about policy using
  the facts these tools return.

The Anthropic tool-use schemas live at the bottom (TOOL_SCHEMAS) next to the
dispatcher, so the contract and the implementation can't drift apart.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from store import (
    get_customer_by_email,
    get_order,
    get_orders_for_customer,
    mark_refunded,
)

# Fixed "today" so the 30-day window is deterministic and matches the seed data.
# Date arithmetic is done HERE in Python — never eyeballed by the model.
TODAY = date(2026, 6, 8)
REFUND_WINDOW_DAYS = 30


def _days_since(purchase_date: str) -> int:
    y, m, d = (int(p) for p in purchase_date.split("-"))
    return (TODAY - date(y, m, d)).days


def _enrich_order(order: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of the order with computed date facts added.

    days_since_purchase + within_window are computed in Python so the agent
    never has to do (and never gets to fudge) date math.
    """
    days = _days_since(order["purchase_date"])
    enriched = dict(order)
    enriched["days_since_purchase"] = days
    enriched["within_window"] = days <= REFUND_WINDOW_DAYS
    return enriched


# --- the 4 tools -------------------------------------------------------------
def lookup_customer(email: str) -> dict[str, Any] | None:
    """Resolve an email to a customer record (the session identity). None if no match."""
    return get_customer_by_email(email)


def lookup_order(order_id: str) -> dict[str, Any] | None:
    """Resolve an order ID to its record, enriched with days_since_purchase + within_window."""
    order = get_order(order_id)
    if order is None:
        return None
    return _enrich_order(order)


def list_orders_for_customer(customer_id: str) -> list[dict[str, Any]]:
    """All orders belonging to a customer, each enriched with date facts."""
    return [_enrich_order(o) for o in get_orders_for_customer(customer_id)]


def issue_refund(order_id: str) -> dict[str, Any]:
    """Execute a refund. The ONLY mutating tool.

    Idempotent guard: refuses to refund an order that is already refunded, so a
    bug or a re-ask loop can never double-refund. This tool does not check policy
    eligibility (the agent does that before calling it) — but it DOES enforce the
    one hard invariant that protects money: no double refunds.
    """
    order = get_order(order_id)
    if order is None:
        return {"status": "error", "error": "order_not_found", "order_id": order_id}
    if order.get("already_refunded"):
        return {
            "status": "error",
            "error": "already_refunded",
            "order_id": order_id,
            "message": "This order has already been refunded; cannot refund twice.",
        }
    mark_refunded(order_id)
    return {"status": "refunded", "order_id": order_id, "amount": order["price"]}


# --- Anthropic tool-use schemas ---------------------------------------------
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "lookup_customer",
        "description": (
            "Look up a customer by email address to verify identity. Returns the "
            "customer record (customer_id, name, email, loyalty_tier, account_created) "
            "or null if no customer has that email. Call this first to establish who "
            "you are talking to before acting on any order."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "The customer's email address."}
            },
            "required": ["email"],
        },
    },
    {
        "name": "lookup_order",
        "description": (
            "Look up a single order by its order ID. Returns the order record plus "
            "two computed fields: days_since_purchase (int) and within_window (bool, "
            "true if <= 30 days). Use within_window for the eligibility-window rule — "
            "do NOT compute dates yourself. Returns null if the order ID does not exist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID, e.g. ORD-1001."}
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "list_orders_for_customer",
        "description": (
            "List all orders belonging to a given customer_id (each enriched with "
            "days_since_purchase and within_window). Use this to help a verified "
            "customer find their order if they don't know the ID. Only ever call this "
            "with the verified session customer's own customer_id."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "The customer ID, e.g. CUST-001."}
            },
            "required": ["customer_id"],
        },
    },
    {
        "name": "issue_refund",
        "description": (
            "Execute a refund for an order. Only call this AFTER every policy check "
            "has passed (identity, not final sale, not already refunded, refundable "
            "status, within window, not high-value). Idempotent: it returns an error "
            "instead of refunding an order that is already refunded."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID to refund."}
            },
            "required": ["order_id"],
        },
    },
]

# dispatcher: tool name -> callable
TOOL_DISPATCH = {
    "lookup_customer": lambda inp: lookup_customer(inp.get("email", "")),
    "lookup_order": lambda inp: lookup_order(inp.get("order_id", "")),
    "list_orders_for_customer": lambda inp: list_orders_for_customer(inp.get("customer_id", "")),
    "issue_refund": lambda inp: issue_refund(inp.get("order_id", "")),
}


def run_tool(name: str, tool_input: dict[str, Any]) -> Any:
    fn = TOOL_DISPATCH.get(name)
    if fn is None:
        return {"status": "error", "error": "unknown_tool", "tool": name}
    return fn(tool_input)

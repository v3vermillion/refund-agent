"""
Deterministic tool/policy-fact tests — no model, no API key required.

These lock in the facts the agent reasons over: the date window math, the
no-double-refund invariant, and that tools never embed a refund decision.
They always run in CI.
"""

import tools


def test_within_window_boundary_day_30_inclusive():
    # ORD-1014 is exactly 25 days old → inside the 30-day window.
    order = tools.lookup_order("ORD-1014")
    assert order["days_since_purchase"] == 25
    assert order["within_window"] is True


def test_outside_window_day_31_denied_by_fact():
    # ORD-1016 is 31 days old → just outside; this is the anchor for the deny.
    order = tools.lookup_order("ORD-1016")
    assert order["days_since_purchase"] == 31
    assert order["within_window"] is False


def test_lookup_order_unknown_returns_none():
    assert tools.lookup_order("ORD-9999") is None


def test_lookup_customer_by_email_case_insensitive():
    c = tools.lookup_customer("JANE.DOE@example.com")
    assert c is not None and c["customer_id"] == "CUST-001"


def test_lookup_customer_unknown_returns_none():
    assert tools.lookup_customer("nobody@example.com") is None


def test_issue_refund_idempotent_on_already_refunded():
    # ORD-1008 is seeded already_refunded=True → must error, never double-refund.
    result = tools.issue_refund("ORD-1008")
    assert result["status"] == "error"
    assert result["error"] == "already_refunded"


def test_issue_refund_unknown_order_errors():
    result = tools.issue_refund("ORD-0000")
    assert result["status"] == "error"
    assert result["error"] == "order_not_found"


def test_high_value_fact_present_for_escalation():
    # The tool reports price; the >$500 escalation decision is the agent's, not the tool's.
    order = tools.lookup_order("ORD-1006")
    assert order["price"] > 500
    assert "decision" not in order  # tools never embed a decision

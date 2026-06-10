"""
seed_data.py — generates the mock CRM: 15 customers + their orders.

Run once:  python scripts/seed_data.py
Writes:    backend/data/customers.json
           backend/data/orders.json

The data is deliberately constructed so that EVERY refund-policy branch is
exercised by at least one order (see the "scenario" comments below). This is
what lets the prompt-injection demo show the agent holding the line on each rule.
"""

import json
import os
from datetime import date, timedelta

# --- anchor "today" so the 30-day window is deterministic every run ----------
# We hardcode TODAY so the seeded dates don't drift relative to the policy
# window between runs. The agent is told this same date (see agent.py).
TODAY = date(2026, 6, 8)


def d(days_ago: int) -> str:
    """ISO date string for N days before TODAY."""
    return (TODAY - timedelta(days=days_ago)).isoformat()


# --- 15 customers ------------------------------------------------------------
customers = [
    {"customer_id": "CUST-001", "name": "Jane Doe",        "email": "jane.doe@example.com",      "loyalty_tier": "gold",     "account_created": "2023-01-15"},
    {"customer_id": "CUST-002", "name": "Marcus Lee",      "email": "marcus.lee@example.com",    "loyalty_tier": "standard", "account_created": "2024-06-02"},
    {"customer_id": "CUST-003", "name": "Aisha Khan",      "email": "aisha.khan@example.com",    "loyalty_tier": "standard", "account_created": "2025-02-20"},
    {"customer_id": "CUST-004", "name": "Diego Romero",    "email": "diego.romero@example.com",  "loyalty_tier": "gold",     "account_created": "2022-11-10"},
    {"customer_id": "CUST-005", "name": "Emily Carter",    "email": "emily.carter@example.com",  "loyalty_tier": "none",     "account_created": "2026-01-05"},
    {"customer_id": "CUST-006", "name": "Tomás Silva",     "email": "tomas.silva@example.com",   "loyalty_tier": "standard", "account_created": "2024-09-19"},
    {"customer_id": "CUST-007", "name": "Hannah Wright",   "email": "hannah.wright@example.com", "loyalty_tier": "standard", "account_created": "2023-07-30"},
    {"customer_id": "CUST-008", "name": "Raj Patel",       "email": "raj.patel@example.com",     "loyalty_tier": "gold",     "account_created": "2021-04-22"},
    {"customer_id": "CUST-009", "name": "Sofia Russo",     "email": "sofia.russo@example.com",   "loyalty_tier": "standard", "account_created": "2025-11-01"},
    {"customer_id": "CUST-010", "name": "Daniel Kim",      "email": "daniel.kim@example.com",    "loyalty_tier": "none",     "account_created": "2026-03-14"},
    {"customer_id": "CUST-011", "name": "Olivia Brooks",   "email": "olivia.brooks@example.com", "loyalty_tier": "standard", "account_created": "2024-02-28"},
    {"customer_id": "CUST-012", "name": "Liam Murphy",     "email": "liam.murphy@example.com",   "loyalty_tier": "gold",     "account_created": "2022-08-08"},
    {"customer_id": "CUST-013", "name": "Mei Tanaka",      "email": "mei.tanaka@example.com",    "loyalty_tier": "standard", "account_created": "2025-05-17"},
    {"customer_id": "CUST-014", "name": "Noah Bennett",    "email": "noah.bennett@example.com",  "loyalty_tier": "standard", "account_created": "2023-12-03"},
    {"customer_id": "CUST-015", "name": "Zoe Adams",       "email": "zoe.adams@example.com",     "loyalty_tier": "none",     "account_created": "2026-02-11"},
]


# --- orders ------------------------------------------------------------------
# Each dict's "scenario" key is a NOTE for us (stripped before writing JSON) so
# we can see at a glance which policy branch each order covers.
orders_raw = [
    # ---- CLEAN APPROVE cases (in window, delivered, not final sale, < $500) --
    {"order_id": "ORD-1001", "customer_id": "CUST-001", "item_name": "Wireless Headphones", "category": "electronics", "price": 129.99, "purchase_date": d(8),  "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "CLEAN APPROVE"},
    {"order_id": "ORD-1002", "customer_id": "CUST-002", "item_name": "Running Shoes",       "category": "apparel",     "price": 89.95,  "purchase_date": d(3),  "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "CLEAN APPROVE"},
    {"order_id": "ORD-1003", "customer_id": "CUST-007", "item_name": "Coffee Grinder",      "category": "home",        "price": 45.00,  "purchase_date": d(20), "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "CLEAN APPROVE"},

    # ---- FINAL SALE (rule 3) → always DENY -----------------------------------
    {"order_id": "ORD-1004", "customer_id": "CUST-003", "item_name": "Clearance Jacket",    "category": "apparel",     "price": 59.99,  "purchase_date": d(5),  "status": "delivered", "is_final_sale": True,  "already_refunded": False, "scenario": "FINAL SALE -> deny"},
    {"order_id": "ORD-1005", "customer_id": "CUST-009", "item_name": "Outlet Sunglasses",   "category": "accessories", "price": 24.99,  "purchase_date": d(2),  "status": "delivered", "is_final_sale": True,  "already_refunded": False, "scenario": "FINAL SALE -> deny"},

    # ---- HIGH VALUE > $500 (rule 5) → ESCALATE -------------------------------
    {"order_id": "ORD-1006", "customer_id": "CUST-004", "item_name": "4K OLED Television",  "category": "electronics", "price": 1299.00, "purchase_date": d(6),  "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "HIGH VALUE -> escalate"},
    {"order_id": "ORD-1007", "customer_id": "CUST-008", "item_name": "Designer Watch",      "category": "accessories", "price": 750.00,  "purchase_date": d(12), "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "HIGH VALUE -> escalate"},

    # ---- ALREADY REFUNDED (rule 4) → DENY ------------------------------------
    {"order_id": "ORD-1008", "customer_id": "CUST-006", "item_name": "Bluetooth Speaker",   "category": "electronics", "price": 79.99,  "purchase_date": d(15), "status": "returned",  "is_final_sale": False, "already_refunded": True,  "scenario": "ALREADY REFUNDED -> deny"},

    # ---- OUTSIDE 30-DAY WINDOW (rule 1) → DENY -------------------------------
    {"order_id": "ORD-1009", "customer_id": "CUST-011", "item_name": "Yoga Mat",            "category": "fitness",     "price": 35.00,  "purchase_date": d(47), "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "OUTSIDE WINDOW -> deny"},
    {"order_id": "ORD-1010", "customer_id": "CUST-012", "item_name": "Desk Lamp",           "category": "home",        "price": 42.50,  "purchase_date": d(90), "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "OUTSIDE WINDOW -> deny"},

    # ---- NOT YET DELIVERED (rule 2) → not refundable yet ---------------------
    {"order_id": "ORD-1011", "customer_id": "CUST-005", "item_name": "Standing Desk",       "category": "furniture",   "price": 320.00, "purchase_date": d(1),  "status": "processing", "is_final_sale": False, "already_refunded": False, "scenario": "PROCESSING -> not yet refundable"},
    {"order_id": "ORD-1012", "customer_id": "CUST-013", "item_name": "Winter Coat",         "category": "apparel",     "price": 140.00, "purchase_date": d(0),  "status": "shipped",    "is_final_sale": False, "already_refunded": False, "scenario": "SHIPPED -> refundable (edge: in transit)"},

    # ---- HIGH VALUE + FINAL SALE (rule precedence: final sale denies first) --
    {"order_id": "ORD-1013", "customer_id": "CUST-014", "item_name": "Limited Sneakers",    "category": "apparel",     "price": 680.00, "purchase_date": d(4),  "status": "delivered", "is_final_sale": True,  "already_refunded": False, "scenario": "FINAL SALE + HIGH VALUE -> deny (final sale wins)"},

    # ---- extra clean & filler orders so customers have 1-3 each ---------------
    {"order_id": "ORD-1014", "customer_id": "CUST-001", "item_name": "Phone Case",          "category": "accessories", "price": 19.99,  "purchase_date": d(25), "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "CLEAN APPROVE (in window edge: day 25)"},
    {"order_id": "ORD-1015", "customer_id": "CUST-010", "item_name": "Mechanical Keyboard", "category": "electronics", "price": 110.00, "purchase_date": d(9),  "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "CLEAN APPROVE"},
    {"order_id": "ORD-1016", "customer_id": "CUST-015", "item_name": "Water Bottle",        "category": "fitness",     "price": 28.00,  "purchase_date": d(31), "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "EDGE: 31 days -> just outside window, deny"},
    {"order_id": "ORD-1017", "customer_id": "CUST-008", "item_name": "Wireless Earbuds",    "category": "electronics", "price": 199.00, "purchase_date": d(7),  "status": "delivered", "is_final_sale": False, "already_refunded": False, "scenario": "CLEAN APPROVE (gold customer, 2nd order)"},
]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(here, "..", "backend", "data")
    os.makedirs(data_dir, exist_ok=True)

    # strip the internal "scenario" notes before writing the real data
    orders = [{k: v for k, v in o.items() if k != "scenario"} for o in orders_raw]

    with open(os.path.join(data_dir, "customers.json"), "w") as f:
        json.dump(customers, f, indent=2)
    with open(os.path.join(data_dir, "orders.json"), "w") as f:
        json.dump(orders, f, indent=2)

    # console summary so you can eyeball coverage
    print(f"Wrote {len(customers)} customers and {len(orders)} orders.")
    print("\nPolicy-branch coverage:")
    for o in orders_raw:
        print(f"  {o['order_id']}  {o['scenario']}")


if __name__ == "__main__":
    main()

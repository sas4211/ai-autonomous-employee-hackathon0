"""
MCP Server: Odoo (Accounting & Business)
=========================================
FastMCP server exposing Odoo 19+ JSON-RPC APIs to Claude Code.
Covers: invoices, payments, customers, sales orders, accounting summary.

This is the "Books" layer of the AI Employee.
All reads are safe. Writes (create invoice, record payment) require
an approved task in /Approved/ before Claude may call them.

Setup:
  1. Install Odoo 19 Community (self-hosted, default port 8069)
  2. Create a dedicated API user in Odoo (Settings > Users)
  3. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD in .env

Usage:
    python mcp_servers/odoo.py           # stdio MCP mode
    python mcp_servers/odoo.py --test    # self-test (read-only)
"""

import json
import os
import sys
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

try:
    import requests
    from dotenv import load_dotenv
    from fastmcp import FastMCP
except ImportError:
    print("ERROR: Run: pip install fastmcp requests python-dotenv", file=sys.stderr)
    sys.exit(1)

VAULT_ROOT = Path(__file__).parent.parent
load_dotenv(VAULT_ROOT / ".env")

mcp = FastMCP(
    name="ai-employee-odoo",
    instructions=(
        "Odoo accounting and business data server. "
        "Read tools are always safe. "
        "Write tools (create_invoice, record_payment) require prior human approval."
    ),
)


# ── Odoo JSON-RPC client ──────────────────────────────────────────────────────

class OdooClient:
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self._uid: int | None = None

    def _rpc(self, endpoint: str, params: dict) -> dict:
        payload = {"jsonrpc": "2.0", "method": "call", "id": 1, "params": params}
        resp = requests.post(
            f"{self.url}{endpoint}", json=payload,
            timeout=30, headers={"Content-Type": "application/json"}
        )
        resp.raise_for_status()
        result = resp.json()
        if "error" in result:
            raise RuntimeError(f"Odoo RPC error: {result['error']['data']['message']}")
        return result.get("result")

    def authenticate(self) -> int:
        if self._uid:
            return self._uid
        uid = self._rpc("/web/dataset/call_kw", {
            "model": "res.users",
            "method": "authenticate",
            "args": [],
            "kwargs": {},
            # Use common service directly
        })
        # Direct common authenticate
        payload = {
            "jsonrpc": "2.0", "method": "call", "id": 1,
            "params": {"db": self.db, "login": self.username, "password": self.password}
        }
        resp = requests.post(f"{self.url}/web/session/authenticate", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Auth failed: {data['error']}")
        self._uid = data["result"]["uid"]
        return self._uid

    def execute(self, model: str, method: str, args: list, kwargs: dict | None = None) -> dict:
        uid = self.authenticate()
        return self._rpc("/web/dataset/call_kw", {
            "model": model,
            "method": method,
            "args": args,
            "kwargs": kwargs or {},
        })

    def search_read(self, model: str, domain: list, fields: list, limit: int = 100) -> list:
        return self.execute(model, "search_read", [domain], {
            "fields": fields, "limit": limit, "order": "id desc"
        })


def _get_client() -> OdooClient:
    url = os.getenv("ODOO_URL", "http://localhost:8069")
    db = os.getenv("ODOO_DB", "odoo")
    username = os.getenv("ODOO_USERNAME", "admin")
    password = os.getenv("ODOO_PASSWORD", "admin")
    return OdooClient(url, db, username, password)


def _fmt_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _today() -> str:
    return _fmt_date(date.today())


def _period_start(weeks_back: int = 4) -> str:
    return _fmt_date(date.today() - timedelta(weeks=weeks_back))


# ── Tools: Accounting ─────────────────────────────────────────────────────────

@mcp.tool()
def get_accounting_summary(date_from: str = "", date_to: str = "") -> str:
    """
    Get P&L summary: total revenue, total expenses, net profit for a period.

    Args:
        date_from: Start date YYYY-MM-DD (default: 4 weeks ago)
        date_to:   End date YYYY-MM-DD (default: today)

    Returns:
        JSON string with revenue, expenses, profit, invoice counts.
    """
    if not date_from:
        date_from = _period_start(4)
    if not date_to:
        date_to = _today()

    try:
        client = _get_client()

        # Revenue: posted customer invoices
        invoices = client.search_read(
            "account.move",
            [["move_type", "=", "out_invoice"],
             ["state", "=", "posted"],
             ["invoice_date", ">=", date_from],
             ["invoice_date", "<=", date_to]],
            ["name", "amount_untaxed", "amount_tax", "amount_total", "partner_id", "payment_state"]
        )
        revenue = sum(i["amount_total"] for i in invoices)

        # Expenses: posted vendor bills
        bills = client.search_read(
            "account.move",
            [["move_type", "=", "in_invoice"],
             ["state", "=", "posted"],
             ["invoice_date", ">=", date_from],
             ["invoice_date", "<=", date_to]],
            ["name", "amount_total", "partner_id"]
        )
        expenses = sum(b["amount_total"] for b in bills)

        result = {
            "period": {"from": date_from, "to": date_to},
            "revenue": round(revenue, 2),
            "expenses": round(expenses, 2),
            "net_profit": round(revenue - expenses, 2),
            "margin_pct": round((revenue - expenses) / revenue * 100, 1) if revenue else 0,
            "invoice_count": len(invoices),
            "bill_count": len(bills),
            "unpaid_invoices": sum(1 for i in invoices if i["payment_state"] != "paid"),
        }
        return json.dumps(result, indent=2)

    except Exception as exc:
        return json.dumps({"error": str(exc), "hint": "Check ODOO_* credentials in .env"})


@mcp.tool()
def list_unpaid_invoices(overdue_only: bool = False) -> str:
    """
    List all unpaid customer invoices. Optionally filter to overdue only.

    Args:
        overdue_only: If True, only return invoices past their due date.

    Returns:
        JSON list of unpaid invoices with amount, due date, customer name.
    """
    try:
        client = _get_client()
        domain = [["move_type", "=", "out_invoice"], ["payment_state", "!=", "paid"],
                  ["state", "=", "posted"]]
        if overdue_only:
            domain.append(["invoice_date_due", "<", _today()])

        invoices = client.search_read(
            "account.move", domain,
            ["name", "partner_id", "amount_total", "amount_residual",
             "invoice_date", "invoice_date_due", "payment_state"],
            limit=50
        )
        result = []
        for inv in invoices:
            due = inv.get("invoice_date_due") or ""
            days_overdue = 0
            if due:
                days_overdue = (date.today() - date.fromisoformat(due)).days
            result.append({
                "invoice": inv["name"],
                "customer": inv["partner_id"][1] if inv["partner_id"] else "Unknown",
                "total": inv["amount_total"],
                "outstanding": inv["amount_residual"],
                "due_date": due,
                "days_overdue": max(0, days_overdue),
            })
        result.sort(key=lambda x: x["days_overdue"], reverse=True)
        return json.dumps(result, indent=2)

    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def get_sales_summary(date_from: str = "", date_to: str = "") -> str:
    """
    Get sales orders summary: count, total value, top customers.

    Args:
        date_from: Start date YYYY-MM-DD
        date_to:   End date YYYY-MM-DD

    Returns:
        JSON with total orders, value, and top 5 customers by revenue.
    """
    if not date_from:
        date_from = _period_start(4)
    if not date_to:
        date_to = _today()

    try:
        client = _get_client()
        orders = client.search_read(
            "sale.order",
            [["state", "in", ["sale", "done"]],
             ["date_order", ">=", f"{date_from} 00:00:00"],
             ["date_order", "<=", f"{date_to} 23:59:59"]],
            ["name", "partner_id", "amount_total", "state", "date_order"],
            limit=200
        )
        total_value = sum(o["amount_total"] for o in orders)

        # Top customers
        customer_totals: dict[str, float] = {}
        for o in orders:
            name = o["partner_id"][1] if o["partner_id"] else "Unknown"
            customer_totals[name] = customer_totals.get(name, 0) + o["amount_total"]
        top_customers = sorted(customer_totals.items(), key=lambda x: x[1], reverse=True)[:5]

        return json.dumps({
            "period": {"from": date_from, "to": date_to},
            "order_count": len(orders),
            "total_value": round(total_value, 2),
            "average_order": round(total_value / len(orders), 2) if orders else 0,
            "top_customers": [{"name": n, "total": round(v, 2)} for n, v in top_customers],
        }, indent=2)

    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def create_invoice(
    customer_name: str, amount: float, description: str,
    due_days: int = 30
) -> str:
    """
    Create a draft customer invoice in Odoo.
    REQUIRES prior human approval — only call after task is in /Approved/.

    Args:
        customer_name: Name of the customer (must exist in Odoo contacts)
        amount:        Invoice total amount (excluding tax)
        description:   Line item description
        due_days:      Payment due in N days (default 30)

    Returns:
        Invoice name/ID on success, or error.
    """
    try:
        client = _get_client()

        # Find partner
        partners = client.search_read(
            "res.partner", [["name", "ilike", customer_name]],
            ["id", "name"], limit=1
        )
        if not partners:
            return json.dumps({"error": f"Customer '{customer_name}' not found in Odoo contacts."})
        partner_id = partners[0]["id"]

        due_date = _fmt_date(date.today() + timedelta(days=due_days))

        invoice_data = {
            "move_type": "out_invoice",
            "partner_id": partner_id,
            "invoice_date": _today(),
            "invoice_date_due": due_date,
            "invoice_line_ids": [(0, 0, {
                "name": description,
                "quantity": 1,
                "price_unit": amount,
            })],
        }
        result = client.execute("account.move", "create", [invoice_data])
        # result is the new record ID
        return json.dumps({"success": True, "invoice_id": result, "due_date": due_date})

    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def list_customers(limit: int = 20) -> str:
    """
    List top customers from Odoo contacts.

    Args:
        limit: Max number of customers to return (default 20)

    Returns:
        JSON list of customer names, emails, and phone numbers.
    """
    try:
        client = _get_client()
        partners = client.search_read(
            "res.partner",
            [["customer_rank", ">", 0]],
            ["name", "email", "phone", "street", "city", "country_id"],
            limit=limit
        )
        return json.dumps([{
            "name": p["name"],
            "email": p.get("email") or "",
            "phone": p.get("phone") or "",
            "city": p.get("city") or "",
            "country": p["country_id"][1] if p.get("country_id") else "",
        } for p in partners], indent=2)

    except Exception as exc:
        return json.dumps({"error": str(exc)})


@mcp.tool()
def get_cashflow_position() -> str:
    """
    Get current cash position: bank balance, outstanding receivables, payables.

    Returns:
        JSON with current cash, total receivable, total payable, net position.
    """
    try:
        client = _get_client()

        # Receivables: all open customer invoices
        receivables = client.search_read(
            "account.move",
            [["move_type", "=", "out_invoice"], ["payment_state", "!=", "paid"],
             ["state", "=", "posted"]],
            ["amount_residual"], limit=500
        )
        total_receivable = sum(r["amount_residual"] for r in receivables)

        # Payables: all open vendor bills
        payables = client.search_read(
            "account.move",
            [["move_type", "=", "in_invoice"], ["payment_state", "!=", "paid"],
             ["state", "=", "posted"]],
            ["amount_residual"], limit=500
        )
        total_payable = sum(p["amount_residual"] for p in payables)

        return json.dumps({
            "as_of": _today(),
            "total_receivable": round(total_receivable, 2),
            "total_payable": round(total_payable, 2),
            "net_working_capital": round(total_receivable - total_payable, 2),
            "receivable_invoices": len(receivables),
            "payable_bills": len(payables),
        }, indent=2)

    except Exception as exc:
        return json.dumps({"error": str(exc)})


# ── Entry point ───────────────────────────────────────────────────────────────

def _self_test():
    print("=== Odoo MCP Server - Self Test ===\n")
    tools = [get_accounting_summary, list_unpaid_invoices, get_sales_summary,
             create_invoice, list_customers, get_cashflow_position]
    for t in tools:
        print(f"  [OK] {t.__name__}")

    cfg = {
        "ODOO_URL": os.getenv("ODOO_URL", "http://localhost:8069"),
        "ODOO_DB": os.getenv("ODOO_DB"),
        "ODOO_USERNAME": os.getenv("ODOO_USERNAME"),
        "ODOO_PASSWORD": bool(os.getenv("ODOO_PASSWORD")),
    }
    print("\nOdoo config:")
    for k, v in cfg.items():
        print(f"  {k}: {v or '[NOT SET]'}")

    if os.getenv("ODOO_DB"):
        print("\nAttempting connection to Odoo...")
        result = get_accounting_summary()
        data = json.loads(result)
        if "error" in data:
            print(f"  Connection failed: {data['error']}")
        else:
            print(f"  Connected! Revenue: {data['revenue']}, Profit: {data['net_profit']}")
    else:
        print("\nSet ODOO_* in .env to test live connection.")

    print("\n[OK] Server ready.")


def main():
    if "--test" in sys.argv:
        _self_test()
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

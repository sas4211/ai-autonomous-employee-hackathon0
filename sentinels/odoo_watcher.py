"""
Sentinel: Odoo Watcher
=======================
Polls Odoo for business events and drops task files into /Inbox:
  - Overdue invoices (> due date)
  - New customer orders confirmed today

Extends BaseWatcher -- implements check_for_updates() and create_action_file().

Usage:
    python sentinels/odoo_watcher.py           # run once
    python sentinels/odoo_watcher.py --loop    # poll every 30 minutes
"""

import os
import sys
from datetime import date
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher

try:
    import requests
except ImportError:
    print("ERROR: Run: pip install requests")
    sys.exit(1)

POLL_INTERVAL = 1800  # 30 minutes


# ── Odoo JSON-RPC client ──────────────────────────────────────────────────────

class OdooSession:
    def __init__(self, url, db, username, password):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.password = password
        self.session = requests.Session()
        self._uid = None

    def authenticate(self):
        if self._uid:
            return
        resp = self.session.post(
            f"{self.url}/web/session/authenticate",
            json={
                "jsonrpc": "2.0", "method": "call", "id": 1,
                "params": {
                    "db": self.db, "login": self.username, "password": self.password
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Odoo auth failed: {data['error']}")
        self._uid = data["result"]["uid"]

    def search_read(self, model, domain, fields, limit=50):
        self.authenticate()
        resp = self.session.post(
            f"{self.url}/web/dataset/call_kw",
            json={
                "jsonrpc": "2.0", "method": "call", "id": 1,
                "params": {
                    "model": model, "method": "search_read",
                    "args": [domain],
                    "kwargs": {
                        "fields": fields, "limit": limit, "order": "id desc"
                    },
                },
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("result", [])


# ── Watcher class ─────────────────────────────────────────────────────────────

class OdooWatcher(BaseWatcher):
    """
    Polls Odoo for overdue invoices and new orders.
    Each event becomes a separate item dict returned by check_for_updates().
    """

    def __init__(self):
        super().__init__(VAULT_ROOT, check_interval=POLL_INTERVAL)
        self.odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
        self.odoo_db = os.getenv("ODOO_DB", "")
        self.odoo_user = os.getenv("ODOO_USERNAME", "admin")
        self.odoo_pass = os.getenv("ODOO_PASSWORD", "admin")

    def check_for_updates(self) -> list:
        """Return list of Odoo event dicts. Returns [] if Odoo is not configured."""
        if not self.odoo_db:
            self.logger.info(
                "Odoo not configured -- skipping (set ODOO_DB in .env)"
            )
            return []

        self.logger.info("Checking Odoo for business events...")
        try:
            odoo = OdooSession(self.odoo_url, self.odoo_db, self.odoo_user, self.odoo_pass)
            items = []
            items.extend(self._check_overdue_invoices(odoo))
            items.extend(self._check_new_orders(odoo))
            self.logger.info(f"Odoo check complete. {len(items)} new event(s).")
            return items
        except Exception as exc:
            self.logger.error(
                f"Odoo connection failed (graceful degradation): {exc}\n"
                f"  Check ODOO_URL={self.odoo_url} is reachable."
            )
            return []

    def create_action_file(self, item: dict) -> "Path | None":
        """Create an /Inbox task file for one Odoo event."""
        event_type = item.get("type")
        slug = item.get("slug", "")

        if self.task_exists(slug):
            self.logger.info(f"Task for {slug} already exists -- skipping")
            return None

        if event_type == "overdue_invoices":
            return self._write_overdue_task(item)
        elif event_type == "new_orders":
            return self._write_orders_task(item)
        return None

    # ── Private: data fetching ────────────────────────────────────────────────

    def _check_overdue_invoices(self, odoo: OdooSession) -> list:
        today = date.today().isoformat()
        invoices = odoo.search_read(
            "account.move",
            [
                ["move_type", "=", "out_invoice"],
                ["state", "=", "posted"],
                ["payment_state", "!=", "paid"],
                ["invoice_date_due", "<", today],
            ],
            ["name", "partner_id", "amount_residual", "invoice_date_due"],
            limit=20,
        )
        if not invoices:
            return []
        slug = f"overdue-invoices-{self.datestamp()}"
        return [{"type": "overdue_invoices", "slug": slug, "invoices": invoices}]

    def _check_new_orders(self, odoo: OdooSession) -> list:
        today = date.today().isoformat()
        orders = odoo.search_read(
            "sale.order",
            [
                ["state", "=", "sale"],
                ["date_order", ">=", f"{today} 00:00:00"],
                ["date_order", "<=", f"{today} 23:59:59"],
            ],
            ["name", "partner_id", "amount_total"],
            limit=10,
        )
        if not orders:
            return []
        slug = f"new-orders-{self.datestamp()}"
        return [{"type": "new_orders", "slug": slug, "orders": orders}]

    # ── Private: file writing ─────────────────────────────────────────────────

    def _write_overdue_task(self, item: dict) -> Path:
        invoices = item["invoices"]
        lines = "\n".join(
            f"| {i['name']} | "
            f"{i['partner_id'][1] if i['partner_id'] else 'Unknown'} | "
            f"{i['amount_residual']:.2f} | "
            f"{i.get('invoice_date_due', '')} |"
            for i in invoices
        )
        filename = f"{self.datestamp()}_odoo-overdue-invoices.md"
        content = (
            f"# Task: Follow Up on Overdue Invoices\n\n"
            f"> Status: **New**\n> Created: {self.datestamp()}\n"
            f"> Priority: High\n> Owner: --\n"
            f"> Type: odoo_followup\n> Source: odoo_watcher\n\n---\n\n"
            f"## Description\n\n{len(invoices)} overdue invoice(s) require follow-up.\n"
            f"Draft a polite payment reminder email for each customer.\n\n"
            f"## Overdue Invoices\n\n"
            f"| Invoice | Customer | Outstanding | Due Date |\n"
            f"|---------|----------|-------------|----------|\n"
            f"{lines}\n\n"
            f"## Acceptance Criteria\n\n"
            f"- [ ] Reminder emails drafted for all overdue invoices\n"
            f"- [ ] Drafts routed to /Pending_Approval/ for human review\n"
        )
        path = self.write_task(self.inbox, filename, content)
        self.logger.info(f"OVERDUE INVOICES: {len(invoices)} found >> {filename}")
        self.log_event("odoo.overdue_invoices", {"count": len(invoices), "task": filename})
        return path

    def _write_orders_task(self, item: dict) -> Path:
        orders = item["orders"]
        total = sum(o["amount_total"] for o in orders)
        lines = "\n".join(
            f"| {o['name']} | "
            f"{o['partner_id'][1] if o['partner_id'] else 'Unknown'} | "
            f"{o['amount_total']:.2f} |"
            for o in orders
        )
        filename = f"{self.datestamp()}_odoo-new-orders.md"
        content = (
            f"# Task: New Orders Received Today\n\n"
            f"> Status: **New**\n> Created: {self.datestamp()}\n"
            f"> Priority: Medium\n> Owner: --\n"
            f"> Type: odoo_orders\n> Source: odoo_watcher\n\n---\n\n"
            f"## Description\n\n{len(orders)} new order(s) confirmed today -- "
            f"total: {total:.2f}.\n"
            f"Log in the CEO briefing and send confirmation emails to customers.\n\n"
            f"## Orders Today\n\n"
            f"| Order | Customer | Value |\n|-------|----------|-------|\n{lines}\n\n"
            f"## Acceptance Criteria\n\n"
            f"- [ ] Orders added to today's CEO briefing metrics\n"
            f"- [ ] Confirmation emails drafted (if not auto-sent by Odoo)\n"
        )
        path = self.write_task(self.inbox, filename, content)
        self.logger.info(f"NEW ORDERS: {len(orders)} today (total {total:.2f}) >> {filename}")
        self.log_event("odoo.new_orders", {"count": len(orders), "total": total, "task": filename})
        return path


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help=f"Poll every {POLL_INTERVAL // 60} min")
    args = parser.parse_args()

    watcher = OdooWatcher()

    if args.loop:
        print(f"[Odoo Sentinel] Polling every {POLL_INTERVAL // 60} minutes. Ctrl+C to stop.\n")
        watcher.run()
    else:
        watcher.run_once()


if __name__ == "__main__":
    main()

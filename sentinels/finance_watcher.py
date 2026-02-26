"""
Sentinel: Finance Watcher
==========================
Downloads banking transactions from CSV files or a bank API and:
  - Logs all transactions to /Accounting/Current_Month.md
  - Creates /Inbox tasks for any transaction over the alert threshold ($500)

Extends BaseWatcher -- implements check_for_updates() and create_action_file().

Sources (in priority order):
  1. CSV files in FINANCE_CSV_DIR (e.g., bank exports downloaded manually)
  2. Plaid API (if PLAID_ACCESS_TOKEN set) -- for supported banks

Setup (CSV mode -- no API needed):
  1. Export transactions from your bank as a CSV
  2. Place CSV files in a folder (default: ~/Downloads/bank_statements/)
  3. Set FINANCE_CSV_DIR in .env to that folder path

Setup (Plaid API mode):
  1. Create a Plaid account: https://dashboard.plaid.com/
  2. Complete Link flow to get an access token for your bank
  3. Set in .env: PLAID_ACCESS_TOKEN, PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV

CSV format expected (standard bank export):
    Date,Description,Amount,Balance
    2026-02-23,Grocery store,-45.20,1254.80

Usage:
    python sentinels/finance_watcher.py          # run once
    python sentinels/finance_watcher.py --loop   # check hourly
"""

import csv
import io
import json
import os
import sys
from datetime import datetime, date, timezone
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from base_watcher import BaseWatcher

try:
    import requests
except ImportError:
    print("ERROR: Run: pip install requests")
    sys.exit(1)

POLL_INTERVAL = 3600          # 1 hour
ALERT_THRESHOLD = 500.0       # flag transactions larger than this
ACCOUNTING_DIR = VAULT_ROOT / "Accounting"
STATE_FILE = VAULT_ROOT / ".claude" / "finance_watcher_state.json"


# ── State helpers ─────────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"seen_transaction_ids": [], "last_csv_mtime": {}}


def _save_state(state: dict):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")


# ── Watcher class ─────────────────────────────────────────────────────────────

class FinanceWatcher(BaseWatcher):
    """
    Reads new bank transactions from CSV files or Plaid API.
    Logs all transactions to /Accounting/Current_Month.md.
    Creates /Inbox alerts for transactions over ALERT_THRESHOLD.
    """

    def __init__(self):
        super().__init__(VAULT_ROOT, check_interval=POLL_INTERVAL)
        self.csv_dir = os.getenv("FINANCE_CSV_DIR", str(Path.home() / "Downloads" / "bank_statements"))
        self.alert_threshold = float(os.getenv("FINANCE_ALERT_THRESHOLD", str(ALERT_THRESHOLD)))
        # Plaid credentials (optional)
        self.plaid_access_token = os.getenv("PLAID_ACCESS_TOKEN")
        self.plaid_client_id = os.getenv("PLAID_CLIENT_ID")
        self.plaid_secret = os.getenv("PLAID_SECRET")
        self.plaid_env = os.getenv("PLAID_ENV", "sandbox")  # sandbox | development | production

    def check_for_updates(self) -> list:
        """Return list of new transaction dicts. Returns [] if nothing configured."""
        csv_dir = Path(self.csv_dir)
        has_csv = csv_dir.exists() and any(csv_dir.glob("*.csv"))
        has_plaid = bool(self.plaid_access_token and self.plaid_client_id)

        if not has_csv and not has_plaid:
            self.logger.info(
                "Finance watcher not configured -- skipping "
                "(set FINANCE_CSV_DIR to a folder with bank CSV files, or set PLAID_* credentials)"
            )
            return []

        state = _load_state()
        transactions = []

        if has_plaid:
            transactions.extend(self._fetch_plaid(state))
        elif has_csv:
            transactions.extend(self._fetch_csv(csv_dir, state))

        _save_state(state)
        self.logger.info(f"Finance: {len(transactions)} new transaction(s) found.")
        return transactions

    def create_action_file(self, txn: dict) -> "Path | None":
        """
        1. Always: append transaction to /Accounting/Current_Month.md
        2. If amount > threshold: also create an /Inbox task for human review
        """
        # Always log to accounting
        self._log_transaction(txn)

        # Alert if over threshold
        amount = abs(txn.get("amount", 0))
        if amount >= self.alert_threshold:
            return self._write_alert_task(txn)

        return None  # no task file for normal transactions

    # ── Private: data sources ─────────────────────────────────────────────────

    def _fetch_csv(self, csv_dir: Path, state: dict) -> list:
        """Read new transactions from CSV files in the configured directory."""
        seen = set(state.get("seen_transaction_ids", []))
        new_transactions = []

        for csv_file in sorted(csv_dir.glob("*.csv")):
            mtime = str(csv_file.stat().st_mtime)
            # Skip if file hasn't changed since last check
            if state.get("last_csv_mtime", {}).get(str(csv_file)) == mtime:
                continue

            try:
                with csv_file.open(encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Build a unique ID from date+description+amount
                        txn_id = f"{row.get('Date','')}-{row.get('Description','')}-{row.get('Amount','')}"
                        if txn_id in seen:
                            continue
                        seen.add(txn_id)

                        try:
                            amount = float(row.get("Amount", "0").replace(",", ""))
                        except ValueError:
                            amount = 0.0

                        new_transactions.append({
                            "id": txn_id,
                            "date": row.get("Date", self.datestamp()),
                            "description": row.get("Description", "Unknown"),
                            "amount": amount,
                            "balance": row.get("Balance", ""),
                            "source": csv_file.name,
                        })

                state.setdefault("last_csv_mtime", {})[str(csv_file)] = mtime

            except Exception as exc:
                self.logger.error(f"Error reading {csv_file.name}: {exc}")

        state["seen_transaction_ids"] = list(seen)
        return new_transactions

    def _fetch_plaid(self, state: dict) -> list:
        """Fetch recent transactions via Plaid API."""
        try:
            base_url = {
                "sandbox": "https://sandbox.plaid.com",
                "development": "https://development.plaid.com",
                "production": "https://production.plaid.com",
            }.get(self.plaid_env, "https://sandbox.plaid.com")

            today = date.today().isoformat()
            start_date = state.get("plaid_last_date", today)

            resp = requests.post(
                f"{base_url}/transactions/get",
                json={
                    "client_id": self.plaid_client_id,
                    "secret": self.plaid_secret,
                    "access_token": self.plaid_access_token,
                    "start_date": start_date,
                    "end_date": today,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            seen = set(state.get("seen_transaction_ids", []))
            new_transactions = []
            for t in data.get("transactions", []):
                txn_id = t["transaction_id"]
                if txn_id in seen:
                    continue
                seen.add(txn_id)
                new_transactions.append({
                    "id": txn_id,
                    "date": t.get("date", self.datestamp()),
                    "description": t.get("name", "Unknown"),
                    "amount": -t.get("amount", 0),  # Plaid: positive=debit; we flip sign
                    "balance": "",
                    "source": "Plaid",
                    "category": ", ".join(t.get("category", [])),
                })

            state["seen_transaction_ids"] = list(seen)
            state["plaid_last_date"] = today
            return new_transactions

        except Exception as exc:
            self.logger.error(f"Plaid API error (graceful degradation): {exc}")
            return []

    # ── Private: file writing ─────────────────────────────────────────────────

    def _log_transaction(self, txn: dict):
        """Append a transaction line to /Accounting/Current_Month.md."""
        ACCOUNTING_DIR.mkdir(exist_ok=True)
        month = self.datestamp()[:7]  # YYYY-MM
        log_file = ACCOUNTING_DIR / f"{month}_transactions.md"

        # Create file with header if it doesn't exist
        if not log_file.exists():
            log_file.write_text(
                f"# Transactions: {month}\n\n"
                f"> Auto-generated by finance_watcher.py\n"
                f"> Updated: {self.datestamp()}\n\n"
                f"| Date | Description | Amount | Balance | Source |\n"
                f"|------|-------------|--------|---------|--------|\n",
                encoding="utf-8",
            )

        # Also write/update Current_Month.md symlink
        current = ACCOUNTING_DIR / "Current_Month.md"
        if not current.exists() or current.read_text(encoding="utf-8").split("\n")[0] != f"# Transactions: {month}":
            current.write_text(log_file.read_text(encoding="utf-8"), encoding="utf-8")

        amount_str = f"{txn['amount']:+.2f}" if txn.get("amount") is not None else "?"
        sign = "+" if txn.get("amount", 0) >= 0 else ""
        with log_file.open("a", encoding="utf-8") as f:
            f.write(
                f"| {txn['date']} | {txn['description'][:50]} | "
                f"{amount_str} | {txn.get('balance', '')} | {txn.get('source', '')} |\n"
            )
        # Keep Current_Month.md in sync
        current.write_text(log_file.read_text(encoding="utf-8"), encoding="utf-8")

        self.log_event(
            "finance.transaction",
            {
                "date": txn["date"],
                "description": txn["description"],
                "amount": txn.get("amount"),
            },
        )

    def _write_alert_task(self, txn: dict) -> Path:
        """Create /Inbox task for large transactions requiring human attention."""
        amount = txn.get("amount", 0)
        direction = "incoming" if amount > 0 else "outgoing"
        abs_amount = abs(amount)
        slug = f"finance-alert-{txn['date']}"
        filename = f"{txn['date']}_finance-alert-{txn['id'][:8]}.md"

        content = (
            f"# Task: Large Transaction Alert -- {direction.title()} ${abs_amount:.2f}\n\n"
            f"> Status: **New**\n"
            f"> Created: {self.datestamp()}\n"
            f"> Priority: High\n"
            f"> Owner: --\n"
            f"> Type: finance_alert\n"
            f"> Source: finance_watcher\n\n"
            f"---\n\n"
            f"## Transaction Details\n\n"
            f"| Field | Value |\n|-------|-------|\n"
            f"| Date | {txn['date']} |\n"
            f"| Description | {txn['description']} |\n"
            f"| Amount | {amount:+.2f} |\n"
            f"| Balance After | {txn.get('balance', 'N/A')} |\n"
            f"| Source | {txn.get('source', 'bank')} |\n\n"
            f"---\n\n"
            f"## Rules of Engagement\n\n"
            f"- **Payment over $500 -- this requires human review**\n"
            f"- Do not approve or reject any payment without human sign-off\n"
            f"- If this is an unexpected charge, escalate to `/Review/`\n\n"
            f"## What Claude Should Do\n\n"
            f"1. Review the transaction details\n"
            f"2. Check if this matches any known invoice or expected payment in Odoo\n"
            f"3. Flag to human via `/Needs_Action/` if unrecognised\n"
            f"4. Log result and move task to `/Done`\n\n"
            f"## Acceptance Criteria\n\n"
            f"- [ ] Transaction verified against Odoo records (if available)\n"
            f"- [ ] Human notified if unexpected\n"
            f"- [ ] Task moved to `/Done`\n"
        )
        path = self.write_task(self.inbox, filename, content)
        self.logger.info(
            f"FINANCE ALERT: {direction} ${abs_amount:.2f} ({txn['description']}) >> {filename}"
        )
        self.log_event(
            "finance.large_transaction",
            {"amount": amount, "description": txn["description"], "task": filename},
        )
        return path


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Finance / bank transaction watcher")
    parser.add_argument("--loop", action="store_true", help="Poll hourly")
    args = parser.parse_args()

    watcher = FinanceWatcher()

    if args.loop:
        print(f"[Finance Sentinel] Polling every {POLL_INTERVAL // 60} minutes. Ctrl+C to stop.\n")
        watcher.run()
    else:
        watcher.run_once()


if __name__ == "__main__":
    main()

"""
audit_logic.py — Subscription & transaction audit logic for the AI Employee vault.

Called by the weekly audit skill to identify subscription charges and flag anomalies.
Output is written to /Inbox as a task file for CEO review.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Subscription pattern registry
# ---------------------------------------------------------------------------

SUBSCRIPTION_PATTERNS: dict[str, str] = {
    "netflix.com": "Netflix",
    "spotify.com": "Spotify",
    "adobe.com": "Adobe Creative Cloud",
    "notion.so": "Notion",
    "slack.com": "Slack",
    "github.com": "GitHub",
    "dropbox.com": "Dropbox",
    "zoom.us": "Zoom",
    "canva.com": "Canva",
    "figma.com": "Figma",
    "openai.com": "OpenAI",
    "anthropic.com": "Anthropic / Claude",
    "aws.amazon.com": "AWS",
    "azure.com": "Microsoft Azure",
    "google.com/cloud": "Google Cloud",
    "mailchimp.com": "Mailchimp",
    "hubspot.com": "HubSpot",
    "zapier.com": "Zapier",
    "make.com": "Make (Integromat)",
    "airtable.com": "Airtable",
}


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------


def analyze_transaction(transaction: dict) -> dict | None:
    """
    Check whether a transaction matches a known subscription pattern.

    Args:
        transaction: dict with keys: description (str), amount (float), date (str)

    Returns:
        Enriched dict if matched, else None.
    """
    description = transaction.get("description", "").lower()
    for pattern, name in SUBSCRIPTION_PATTERNS.items():
        if pattern in description:
            return {
                "type": "subscription",
                "name": name,
                "amount": transaction.get("amount"),
                "date": transaction.get("date"),
                "raw_description": transaction.get("description"),
            }
    return None


def flag_anomalies(
    transactions: list[dict],
    cost_threshold: float = 600.0,
    inactivity_days: int = 30,
    increase_pct: float = 20.0,
) -> list[dict]:
    """
    Apply the subscription audit rules from Business_Goals.md:
      - No login in `inactivity_days` days
      - Cost increase > `increase_pct`%
      - Monthly software spend > `cost_threshold`

    Args:
        transactions: list of transaction dicts
        cost_threshold: monthly software spend alert threshold (default $600)
        inactivity_days: flag if last login older than this many days
        increase_pct: flag if cost increased by more than this percentage

    Returns:
        List of flagged items with reason.
    """
    flagged: list[dict] = []
    cutoff = datetime.utcnow() - timedelta(days=inactivity_days)

    monthly_software_spend = 0.0
    seen: dict[str, dict] = {}  # name → last known transaction

    for txn in transactions:
        result = analyze_transaction(txn)
        if not result:
            continue

        name = result["name"]
        amount = result["amount"] or 0.0
        monthly_software_spend += amount

        if name in seen:
            prev_amount = seen[name]["amount"] or 0.0
            if prev_amount > 0 and amount > prev_amount:
                pct_increase = ((amount - prev_amount) / prev_amount) * 100
                if pct_increase > increase_pct:
                    flagged.append(
                        {
                            **result,
                            "flag": "cost_increase",
                            "reason": f"Cost increased {pct_increase:.1f}% (was ${prev_amount:.2f})",
                        }
                    )

        seen[name] = result

    if monthly_software_spend > cost_threshold:
        flagged.append(
            {
                "type": "budget_alert",
                "name": "Total software spend",
                "amount": monthly_software_spend,
                "flag": "over_budget",
                "reason": f"Monthly software spend ${monthly_software_spend:.2f} exceeds threshold ${cost_threshold:.2f}",
            }
        )

    return flagged


# ---------------------------------------------------------------------------
# Vault integration
# ---------------------------------------------------------------------------

DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
VAULT_ROOT = Path(__file__).parent.parent


def write_audit_task(flagged: list[dict]) -> None:
    """Write a task file to /Inbox summarising the flagged subscriptions."""
    if not flagged:
        logger.info("[audit_logic] No anomalies found — no task created.")
        return

    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    inbox = VAULT_ROOT / "Inbox"
    inbox.mkdir(exist_ok=True)
    task_path = inbox / f"{date_str}_subscription-audit.md"

    lines = [
        f"# Subscription Audit — {date_str}\n",
        "> Generated by: audit_logic.py\n",
        "> Action required: Review flagged items below\n\n",
        "---\n\n",
        "## Flagged Items\n\n",
        "| Name | Amount | Flag | Reason |\n",
        "|------|--------|------|--------|\n",
    ]
    for item in flagged:
        lines.append(
            f"| {item.get('name','')} "
            f"| ${item.get('amount', 0):.2f} "
            f"| {item.get('flag','')} "
            f"| {item.get('reason','')} |\n"
        )

    lines += [
        "\n---\n\n",
        "Move to `/Approved` to action, or `/Rejected` to dismiss.\n",
    ]

    if DRY_RUN:
        logger.info("[DRY RUN] Would write audit task:\n%s", "".join(lines))
        return

    task_path.write_text("".join(lines), encoding="utf-8")
    logger.info("[audit_logic] Audit task written to %s", task_path)


# ---------------------------------------------------------------------------
# CLI entry point (for manual/scheduled runs)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Run subscription audit on transactions JSON")
    parser.add_argument("transactions_file", help="Path to transactions JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Log only, do not write files")
    args = parser.parse_args()

    if args.dry_run:
        os.environ["DRY_RUN"] = "true"

    with open(args.transactions_file, encoding="utf-8") as f:
        txns = json.load(f)

    flagged = flag_anomalies(txns)
    logger.info("Flagged %d items.", len(flagged))
    write_audit_task(flagged)

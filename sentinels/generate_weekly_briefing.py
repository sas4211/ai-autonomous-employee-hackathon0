"""
generate_weekly_briefing.py — Autonomous Monday Morning CEO Briefing Generator
==============================================================================

Triggered by the scheduler every Sunday at 23:00.

Process:
  1. Read Business_Goals.md  → revenue targets, active projects, subscription rules
  2. Scan /Done              → tasks completed in the last 7 days
  3. Read Bank_Transactions.md → revenue, expenses, subscriptions
  4. Run audit_logic.py      → flag subscription anomalies
  5. Write Monday Morning CEO Briefing → /Briefings/YYYY-MM-DD_monday_briefing.md
  6. Log the run             → /Logs/YYYY-MM-DD_monday_briefing_generated.md

Usage:
    python sentinels/generate_weekly_briefing.py            # full run
    python sentinels/generate_weekly_briefing.py --dry-run  # preview only
    python sentinels/generate_weekly_briefing.py --force    # overwrite existing
"""

import os
import re
import sys
import json
import logging
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap — allow running from any cwd
# ---------------------------------------------------------------------------
VAULT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VAULT_ROOT / "sentinels"))

from audit_logic import analyze_transaction, flag_anomalies  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
FORCE = "--force" in sys.argv

# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------
TODAY = date.today()
MONDAY = TODAY - timedelta(days=TODAY.weekday())          # this Monday
LAST_MONDAY = MONDAY - timedelta(weeks=1)                 # 7 days ago
WEEK_START = LAST_MONDAY.isoformat()
WEEK_END = (MONDAY - timedelta(days=1)).isoformat()       # last Sunday


# ---------------------------------------------------------------------------
# 1. Parse Business_Goals.md
# ---------------------------------------------------------------------------

def read_business_goals() -> dict:
    path = VAULT_ROOT / "Business_Goals.md"
    if not path.exists():
        logger.warning("Business_Goals.md not found — using defaults")
        return {"monthly_goal": 10000, "mtd": 0, "projects": [], "thresholds": {}}

    text = path.read_text(encoding="utf-8")

    # Monthly goal
    monthly_goal = 10000
    m = re.search(r"Monthly goal:\s*\$?([\d,]+)", text)
    if m:
        monthly_goal = int(m.group(1).replace(",", ""))

    # Current MTD
    mtd = 0
    m = re.search(r"Current MTD:\s*\$?([\d,]+)", text)
    if m:
        mtd = int(m.group(1).replace(",", ""))

    # Active projects
    projects = re.findall(r"^\d+\.\s+(.+?)(?:\n|$)", text, re.MULTILINE)

    # Alert thresholds
    thresholds = {}
    for row in re.finditer(r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|", text):
        metric, target, alert = row.group(1), row.group(2), row.group(3)
        if metric.lower() in ("metric", "---"):
            continue
        thresholds[metric.strip()] = {"target": target.strip(), "alert": alert.strip()}

    return {
        "monthly_goal": monthly_goal,
        "mtd": mtd,
        "projects": projects,
        "thresholds": thresholds,
    }


# ---------------------------------------------------------------------------
# 2. Scan /Done for this week's completed tasks
# ---------------------------------------------------------------------------

def read_done_tasks(since: date) -> list[dict]:
    done_dir = VAULT_ROOT / "Done"
    if not done_dir.exists():
        return []

    tasks = []
    for f in sorted(done_dir.glob("*.md")):
        # Filename format: YYYY-MM-DD_<slug>.md
        m = re.match(r"(\d{4}-\d{2}-\d{2})_(.*?)\.md", f.name)
        if not m:
            continue
        task_date_str, slug = m.group(1), m.group(2)
        try:
            task_date = date.fromisoformat(task_date_str)
        except ValueError:
            continue
        if task_date >= since:
            # Try to read result from file
            text = f.read_text(encoding="utf-8", errors="ignore")
            result_m = re.search(r"Result[:\s]+(.+?)(?:\n|$)", text, re.IGNORECASE)
            result = result_m.group(1).strip() if result_m else "Completed"
            tasks.append({
                "date": task_date_str,
                "slug": slug.replace("-", " ").title(),
                "result": result,
                "path": str(f),
            })
    return tasks


# ---------------------------------------------------------------------------
# 3. Parse Bank_Transactions.md
# ---------------------------------------------------------------------------

def parse_transactions_md() -> list[dict]:
    path = VAULT_ROOT / "Bank_Transactions.md"
    if not path.exists():
        logger.warning("Bank_Transactions.md not found — financial data unavailable")
        return []

    text = path.read_text(encoding="utf-8")
    transactions = []

    in_table = False
    for line in text.splitlines():
        # Detect transaction table header
        if re.match(r"\|\s*Date\s*\|", line, re.IGNORECASE):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 5:
                date_str, desc, amount_str, category, txn_type = parts[0], parts[1], parts[2], parts[3], parts[4]
                # Skip empty rows
                if not date_str or date_str == "...":
                    continue
                try:
                    amount = float(amount_str.replace(",", "").replace("$", ""))
                except ValueError:
                    continue
                transactions.append({
                    "date": date_str,
                    "description": desc,
                    "amount": abs(amount),
                    "category": category,
                    "type": txn_type,
                    "raw_amount": amount,
                })
        elif in_table and not line.startswith("|"):
            # Another section started
            if line.startswith("##"):
                in_table = False

    return transactions


# ---------------------------------------------------------------------------
# 4. Calculate financial summary for the period
# ---------------------------------------------------------------------------

def calculate_financials(transactions: list[dict], week_start: str, week_end: str) -> dict:
    week_revenue = 0.0
    week_expenses = 0.0
    mtd_revenue = 0.0
    mtd_expenses = 0.0
    current_month = TODAY.strftime("%Y-%m")

    for t in transactions:
        if not t["date"].startswith("20"):
            continue
        is_credit = t["type"].lower() == "credit"
        is_debit = t["type"].lower() == "debit"

        # This week
        if week_start <= t["date"] <= week_end:
            if is_credit:
                week_revenue += t["amount"]
            elif is_debit:
                week_expenses += t["amount"]

        # Month to date
        if t["date"].startswith(current_month):
            if is_credit:
                mtd_revenue += t["amount"]
            elif is_debit:
                mtd_expenses += t["amount"]

    return {
        "week_revenue": week_revenue,
        "week_expenses": week_expenses,
        "week_net": week_revenue - week_expenses,
        "mtd_revenue": mtd_revenue,
        "mtd_expenses": mtd_expenses,
        "mtd_net": mtd_revenue - mtd_expenses,
    }


# ---------------------------------------------------------------------------
# 5. Detect bottlenecks from Done tasks (tasks with long slugs = likely long)
# ---------------------------------------------------------------------------

def detect_bottlenecks(done_tasks: list[dict]) -> list[dict]:
    """
    Simple heuristic: any task slug containing 'delayed', 'overdue', 'slow',
    or 'pending' is a candidate bottleneck.
    """
    flags = ["delay", "overdue", "slow", "pending", "stuck", "blocked"]
    bottlenecks = []
    for task in done_tasks:
        if any(f in task["slug"].lower() for f in flags):
            bottlenecks.append(task)
    return bottlenecks


# ---------------------------------------------------------------------------
# 6. Write the Monday Morning CEO Briefing
# ---------------------------------------------------------------------------

def write_briefing(
    goals: dict,
    done_tasks: list[dict],
    financials: dict,
    flagged_subs: list[dict],
    bottlenecks: list[dict],
) -> Path:
    briefing_dir = VAULT_ROOT / "Briefings"
    briefing_dir.mkdir(exist_ok=True)
    filename = f"{TODAY.isoformat()}_monday_briefing.md"
    output = briefing_dir / filename

    if output.exists() and not FORCE:
        logger.info("Briefing already exists for %s — skip (use --force to overwrite)", TODAY)
        return output

    # --- Revenue trend ---
    monthly_goal = goals["monthly_goal"]
    mtd = financials["mtd_revenue"]
    pct_of_goal = (mtd / monthly_goal * 100) if monthly_goal else 0
    trend = "On track" if pct_of_goal >= (TODAY.day / 28 * 100 * 0.9) else "Behind"

    # --- Subscription flag summary ---
    sub_suggestions = ""
    if flagged_subs:
        sub_suggestions = "\n### Cost Optimization\n\n"
        for flag in flagged_subs:
            sub_suggestions += (
                f"- **{flag.get('name', 'Unknown')}**: {flag.get('reason', '')}. "
                f"Cost: ${flag.get('amount', 0):.2f}/month.\n"
                f"  - [ACTION] Review → Move to `/Pending_Approval`\n"
            )
    else:
        sub_suggestions = "\n### Cost Optimization\n\n- No subscription anomalies detected this week. ✅\n"

    # --- Active projects / upcoming deadlines ---
    deadlines_section = "\n### Upcoming Deadlines\n\n"
    if goals["projects"]:
        for p in goals["projects"]:
            deadlines_section += f"- {p}\n"
    else:
        deadlines_section += "- No active projects listed in Business_Goals.md\n"

    # --- Completed tasks table ---
    if done_tasks:
        task_rows = "\n".join(
            f"| {t['date']} | {t['slug']} | {t['result']} |"
            for t in done_tasks
        )
    else:
        task_rows = "| — | No tasks completed this week | — |"

    # --- Bottlenecks table ---
    if bottlenecks:
        bn_rows = "\n".join(
            f"| {b['slug']} | — | — | Flagged |"
            for b in bottlenecks
        )
    else:
        bn_rows = "| — | No bottlenecks detected | — | — |"

    # --- Build the document ---
    briefing = f"""# Monday Morning CEO Briefing — {TODAY.isoformat()}

---
generated: {datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
period: {WEEK_START} → {WEEK_END}
prepared_by: AI Employee (generate_weekly_briefing.py)
---

## Executive Summary

{"Revenue is ahead of target" if trend == "On track" else "Revenue is behind target"} for {TODAY.strftime("%B %Y")}. \
{len(done_tasks)} task(s) completed this week. \
{"No subscription anomalies detected." if not flagged_subs else f"{len(flagged_subs)} subscription flag(s) require your attention."}

---

## Revenue

| Metric | Value | Status |
|--------|------:|--------|
| This Week | ${financials['week_revenue']:,.2f} | — |
| Month-to-Date | ${mtd:,.2f} | {pct_of_goal:.0f}% of ${monthly_goal:,} target |
| MTD Expenses | ${financials['mtd_expenses']:,.2f} | — |
| MTD Net Profit | ${financials['mtd_net']:,.2f} | — |
| Trend | — | **{trend}** |

---

## Completed Tasks

| Date | Task | Result |
|------|------|--------|
{task_rows}

---

## Bottlenecks

| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
{bn_rows}

---

## Proactive Suggestions
{sub_suggestions}{deadlines_section}

---

## Decisions Needed

| Item | Risk | Waiting Since |
|------|------|---------------|
| Review flagged subscriptions | Medium | {TODAY.isoformat()} |
| Update active projects in Business_Goals.md | Low | — |

---

## Financial Detail — Week {WEEK_START} → {WEEK_END}

| Metric | Amount |
|--------|-------:|
| Revenue (credits) | ${financials['week_revenue']:,.2f} |
| Expenses (debits) | ${financials['week_expenses']:,.2f} |
| Net | ${financials['week_net']:,.2f} |

---

## Next 7 Days — Priorities

1. Process any pending items in `/Pending_Approval`
2. Update `Business_Goals.md` with current MTD figures
3. Review flagged subscriptions for cancellation
4. Chase overdue invoices if collection rate < 90%
5. Schedule client check-ins for active projects

---

*Generated by AI Employee v0.1 · `generate_weekly_briefing.py`*
"""

    if DRY_RUN:
        logger.info("[DRY RUN] Would write briefing:\n%s", briefing[:500] + "...")
        return output

    output.write_text(briefing, encoding="utf-8")
    logger.info("Briefing written → %s", output)
    return output


# ---------------------------------------------------------------------------
# 7. Log the run
# ---------------------------------------------------------------------------

def log_run(briefing_path: Path, done_count: int, flagged_count: int) -> None:
    logs_dir = VAULT_ROOT / "Logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"{TODAY.isoformat()}_monday_briefing_generated.md"

    entry = (
        f"# Log: Monday Briefing Generated — {TODAY.isoformat()}\n\n"
        f"> Level: ACTION\n"
        f"> Actor: generate_weekly_briefing.py\n"
        f"> Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
        f"---\n\n"
        f"## Summary\n\n"
        f"- Briefing written: `{briefing_path.name}`\n"
        f"- Period: {WEEK_START} → {WEEK_END}\n"
        f"- Done tasks included: {done_count}\n"
        f"- Subscription flags: {flagged_count}\n"
        f"- Dry run: {DRY_RUN}\n"
    )

    if not DRY_RUN:
        log_file.write_text(entry, encoding="utf-8")
        logger.info("Log written → %s", log_file)
    else:
        logger.info("[DRY RUN] Would write log: %s", log_file)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if "--dry-run" in sys.argv:
        os.environ["DRY_RUN"] = "true"
        global DRY_RUN
        DRY_RUN = True

    logger.info("=== Monday Morning CEO Briefing Generator ===")
    logger.info("Period: %s → %s", WEEK_START, WEEK_END)

    # Step 1: Business Goals
    logger.info("Reading Business_Goals.md...")
    goals = read_business_goals()
    logger.info("  Monthly goal: $%s | MTD: $%s", goals["monthly_goal"], goals["mtd"])

    # Step 2: Done tasks
    logger.info("Scanning /Done for tasks since %s...", LAST_MONDAY)
    done_tasks = read_done_tasks(since=LAST_MONDAY)
    logger.info("  Found %d completed task(s) this week", len(done_tasks))

    # Step 3: Transactions
    logger.info("Parsing Bank_Transactions.md...")
    transactions = parse_transactions_md()
    logger.info("  Found %d transaction(s)", len(transactions))

    # Step 4: Financials + audit
    financials = calculate_financials(transactions, WEEK_START, WEEK_END)
    logger.info(
        "  Week revenue: $%.2f | MTD revenue: $%.2f",
        financials["week_revenue"], financials["mtd_revenue"]
    )

    flagged = flag_anomalies(transactions)
    logger.info("  Subscription flags: %d", len(flagged))

    # Step 5: Bottlenecks
    bottlenecks = detect_bottlenecks(done_tasks)

    # Step 6: Write briefing
    briefing_path = write_briefing(goals, done_tasks, financials, flagged, bottlenecks)

    # Step 7: Log
    log_run(briefing_path, len(done_tasks), len(flagged))

    logger.info("=== Done. Briefing: %s ===", briefing_path.name)


if __name__ == "__main__":
    main()

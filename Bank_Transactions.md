# Bank Transactions Log

---
last_updated: 2026-02-26
currency: USD
account: Business Checking
---

## Instructions

Add new transactions as rows in the table below.
The weekly audit reads this file every **Sunday night** automatically and includes it in the Monday Morning CEO Briefing.

**Categories**: Revenue | Subscription | Expense | Payroll | Tax | Transfer
**Type**: credit (money in) | debit (money out)

---

## Transactions

| Date | Description | Amount | Category | Type | Notes |
|------|-------------|-------:|----------|------|-------|
| 2026-02-03 | Client A — Invoice #001 | 2450.00 | Revenue | credit | Project Alpha milestone 1 |
| 2026-02-05 | Adobe Creative Cloud | -54.99 | Subscription | debit | Monthly |
| 2026-02-05 | Notion.so | -15.00 | Subscription | debit | Monthly team plan |
| 2026-02-08 | Client B — Invoice #002 | 1800.00 | Revenue | credit | Project Beta deposit |
| 2026-02-10 | Slack | -12.50 | Subscription | debit | Pro plan |
| 2026-02-10 | Canva Pro | -12.99 | Subscription | debit | Monthly |
| 2026-02-12 | AWS (amazon.com) | -34.20 | Subscription | debit | Cloud hosting |
| 2026-02-14 | OpenAI API | -22.00 | Subscription | debit | GPT usage |
| 2026-02-14 | Anthropic / Claude | -20.00 | Subscription | debit | Claude API |
| 2026-02-17 | Client C — Invoice #003 | 3200.00 | Revenue | credit | New project kickoff |
| 2026-02-19 | Zoom | -15.99 | Subscription | debit | Pro plan |
| 2026-02-19 | GitHub | -4.00 | Subscription | debit | Pro plan |
| 2026-02-20 | Office supplies | -87.50 | Expense | debit | Printer cartridges |
| 2026-02-24 | Figma | -12.00 | Subscription | debit | Starter plan |
| 2026-02-25 | Client A — Invoice #004 | 2450.00 | Revenue | credit | Project Alpha milestone 2 |

---

## Monthly Summary (auto-calculated by weekly audit)

> This section is overwritten by generate_weekly_briefing.py each Sunday.

| Month | Revenue | Expenses | Net |
|-------|--------:|---------:|----:|
| Feb 2026 | $9,900.00 | $291.17 | $9,608.83 |

---

## Subscription Register

> Subscriptions detected by audit_logic.py pattern matching.

| Service | Monthly Cost | Last Seen | Flag |
|---------|------------:|-----------|------|
| Adobe Creative Cloud | $54.99 | 2026-02-05 | — |
| Notion | $15.00 | 2026-02-05 | — |
| Slack | $12.50 | 2026-02-10 | — |
| Canva | $12.99 | 2026-02-10 | — |
| AWS | $34.20 | 2026-02-12 | — |
| OpenAI | $22.00 | 2026-02-14 | — |
| Anthropic / Claude | $20.00 | 2026-02-14 | — |
| Zoom | $15.99 | 2026-02-19 | — |
| GitHub | $4.00 | 2026-02-19 | — |
| Figma | $12.00 | 2026-02-24 | — |

**Total software spend: $203.67/month** (threshold: $500 → under budget ✅)

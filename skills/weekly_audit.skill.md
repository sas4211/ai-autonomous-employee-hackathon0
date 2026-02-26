# Skill: Weekly Business & Accounting Audit

> Skill Name: `weekly_audit.generate`
> Category: Business Intelligence / Accounting
> Type: Scheduled Output
> Trigger: Every Monday 09:00 (via scheduler) OR manual task in /Inbox
> Output: `/Briefings/YYYY-MM-DD_weekly_audit.md`

---

## Purpose

Generate a comprehensive weekly audit that combines:
1. **Accounting data** from Odoo (revenue, expenses, overdue invoices, cashflow)
2. **Sales performance** from Odoo (orders, top customers, pipeline)
3. **Social media metrics** from Facebook, Instagram, Twitter/X
4. **Vault operations** (tasks completed, approvals, trust progress)
5. **CEO executive summary** — key decisions needed this week

This is the "Monday Morning CEO Briefing" mentioned in the hackathon spec.

---

## Data Sources

| Source | MCP Server | Tools Used |
|--------|-----------|------------|
| Odoo P&L | `odoo` | `get_accounting_summary(date_from, date_to)` |
| Odoo unpaid | `odoo` | `list_unpaid_invoices(overdue_only=True)` |
| Odoo sales | `odoo` | `get_sales_summary(date_from, date_to)` |
| Odoo cashflow | `odoo` | `get_cashflow_position()` |
| Social summary | `social_media` | `get_social_summary(days=7)` |
| Vault state | filesystem | Scan all folders + read trust_ledger.md |

---

## Workflow

### Step 1 — Define the Period

- `date_from`: Monday of last week (7 days ago)
- `date_to`: Yesterday (Sunday)
- `social_days`: 7

### Step 2 — Pull All Data (parallel where possible)

Call all MCP tools in sequence:
1. `get_accounting_summary(date_from, date_to)`
2. `list_unpaid_invoices(overdue_only=True)`
3. `get_sales_summary(date_from, date_to)`
4. `get_cashflow_position()`
5. `get_social_summary(days=7)`
6. Scan vault folders (count files in each)
7. Read `/Logs/trust_ledger.md`

**Graceful degradation**: If any source fails (Odoo offline, API error), use "Data unavailable — check credentials" for that section. Do NOT abort the entire audit.

### Step 3 — Analyse

Calculate:
- Revenue vs prior week (if prior briefing exists in /Briefings/)
- Collection rate: paid / (paid + overdue)
- Social engagement rate: engaged / reach
- Task throughput: completed tasks this week
- Decisions needed: approval queue + overdue invoices

### Step 4 — Write the Audit

Save to `/Briefings/YYYY-MM-DD_weekly_audit.md` using the template below.

### Step 5 — Update Ledger and Dashboard

- Update trust ledger: briefing dates +1
- Refresh Dashboard.md
- Log in /Logs/

---

## Audit Template

```markdown
# Weekly Business Audit — Week of YYYY-MM-DD

> Generated: YYYY-MM-DD
> Period: date_from → date_to
> Prepared by: Claude Code

---

## Executive Summary

[2–3 sentences: revenue, key risk, one decision needed this week]

---

## Financial Performance

| Metric | This Week | Notes |
|--------|-----------|-------|
| Revenue | £/$ X | +/-X% vs prior |
| Expenses | £/$ X | |
| Net Profit | £/$ X | Margin: X% |
| Cash Receivable | £/$ X | |
| Cash Payable | £/$ X | |

### Overdue Invoices (ACTION REQUIRED)

| Invoice | Customer | Amount | Days Overdue |
|---------|----------|--------|-------------|
| ... | ... | ... | ... |

---

## Sales Performance

| Metric | Value |
|--------|-------|
| Orders confirmed | X |
| Total order value | £/$ X |
| Average order value | £/$ X |

### Top Customers This Week

| Customer | Revenue |
|----------|---------|
| ... | ... |

---

## Social Media Performance

| Platform | Reach | Engagement | Posts |
|----------|-------|------------|-------|
| Facebook | X | X | X |
| Instagram | X | X | X |
| Twitter/X | X mentions | — | — |

### Best Performing Content

[Note the highest-engagement post if available]

---

## Operations

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Tasks completed | X | 10+ | [on track / behind] |
| Approvals processed | X | 5+ | |
| Briefing dates | X | 3+ | |
| Rollbacks | X | 1 | |

---

## Decisions Needed This Week

1. [Decision 1 — priority — deadline]
2. [Decision 2 — priority — deadline]

---

## Risks & Bottlenecks

- [Risk 1 — severity — mitigation]
- [Risk 2 — severity — mitigation]

---

## Next 7 Days — Priorities

1. [Action 1]
2. [Action 2]
3. [Action 3]
```

---

## Error Handling

If Odoo is unavailable:
- Note "Odoo offline — accounting data unavailable" in the Financial section
- Still generate the social and vault sections
- Flag in Risks: "Odoo connection required for full audit"

If social APIs return errors:
- Note "Social data unavailable — check .env credentials"
- Still generate financial and vault sections

**Never abort the entire audit because one source is down.**

---

## Rules

- One audit file per week (skip if already exists for this Monday)
- Always update the trust ledger after generation
- Always include the Decisions Needed section
- Tag urgent items clearly — they should jump off the page

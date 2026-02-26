# Skill: Odoo Accounting & Business Operations

> Skill Name: `odoo_accounting.query` / `odoo_accounting.write`
> Category: Accounting / Business Operations
> Type: Read (always safe) / Write (requires approval)
> MCP Server: `odoo`
> Trigger: Weekly audit, overdue invoice tasks, new order notifications

---

## Purpose

Interface with Odoo 19 Community (self-hosted) to query financial data and
perform accounting operations. This is the "Books" integration layer.

---

## Available Operations

### Read Tools (always safe, no approval needed)

| Tool | Description | Use When |
|------|-------------|----------|
| `get_accounting_summary` | P&L for a period | Weekly audit, CEO briefing |
| `list_unpaid_invoices` | Outstanding + overdue invoices | Follow-up tasks, cashflow review |
| `get_sales_summary` | Orders, revenue, top customers | Weekly audit, performance review |
| `get_cashflow_position` | Receivables vs payables | Monday briefing, risk assessment |
| `list_customers` | Customer contact list | Before drafting emails |

### Write Tools (require human approval)

| Tool | Description | Approval Trigger |
|------|-------------|-----------------|
| `create_invoice` | Create draft invoice in Odoo | "Create invoice" task in /Approved |

---

## Odoo Setup Requirements

```
ODOO_URL      = http://localhost:8069   (default Odoo port)
ODOO_DB       = your_database_name     (see Settings > Technical > Databases)
ODOO_USERNAME = api_user@company.com   (dedicated API user recommended)
ODOO_PASSWORD = your_password          (.env file, never committed)
```

**Recommended Odoo user permissions:**
- Accounting: Read access + Invoice creation
- Sales: Read access
- Contacts: Read access
- No system administration access needed

---

## Weekly Accounting Workflow

Triggered every Monday as part of `weekly_audit.generate`:

1. Call `get_accounting_summary(date_from, date_to)` — pull P&L
2. Call `list_unpaid_invoices(overdue_only=True)` — flag overdue
3. Call `get_sales_summary(date_from, date_to)` — sales performance
4. Call `get_cashflow_position()` — net working capital
5. Compose financial section of the weekly audit report
6. If overdue invoices exist: queue a follow-up task in /Inbox

---

## Overdue Invoice Follow-Up

When `odoo_watcher.py` drops an overdue invoice task into /Inbox:

1. Read the task — extract invoice list
2. For each invoice, call `list_customers()` to get contact email
3. Draft a polite payment reminder email (see template below)
4. Route to `/Pending_Approval/` for each email
5. After approval: send via `communications.send_email`
6. Log the send in `/Logs/external_actions.md`

### Payment Reminder Template

```
Subject: Friendly reminder — Invoice [number] payment due

Hi [Customer name],

I hope you're well. I wanted to follow up on invoice [number]
for [amount], which was due on [date].

If you've already arranged payment, please disregard this message.
If you have any questions about the invoice, please don't hesitate
to get in touch.

You can also pay online at: [payment link if configured in Odoo]

Thank you for your business.

Kind regards,
[Business name]
```

---

## Create Invoice Workflow

When asked to create an invoice:

1. Verify approval file exists in /Approved/ with invoice details
2. Call `list_customers(limit=5)` to confirm customer exists in Odoo
3. Call `create_invoice(customer_name, amount, description, due_days)`
4. Log the creation (level: ACTION) in `/Logs/odoo_actions.md`
5. Optionally draft a "invoice sent" email for approval

---

## Error Handling

| Scenario | Response |
|----------|---------|
| Odoo offline (connection refused) | Log DEGRADED, skip Odoo sections in audit, note in report |
| Authentication failed (401) | Log ERROR, move task to /Review, note "Check ODOO credentials in .env" |
| Customer not found | Log WARNING, move to /Needs_Action with question "Confirm customer name" |
| Database does not exist | Log ERROR, escalate to /Review |

**Graceful degradation:** If Odoo is down, generate the weekly audit with "Accounting data unavailable" in the financial section. Never abort the entire audit.

---

## Rules

- Read operations require no approval
- `create_invoice` and any write always require prior approval
- Always log Odoo API calls in `/Logs/odoo_actions.md`
- Never store Odoo credentials anywhere except `.env`
- If Odoo is unreachable, degrade gracefully and flag in the audit

# Plan: Generate & Send Invoice — Client A

---
created: 2026-02-26T13:10:00Z
status: in_progress
task_source: /Needs_Action/2026-02-26_whatsapp_client-a.md
domain: business
risk: medium
---

## Objective

Generate invoice INV-2026-02-005 for Client A and send via email after approval.

## Client Lookup (from /Accounting/Rates.md)

| Field | Value |
|-------|-------|
| Client ID | CLIENT_A |
| Name | Client A |
| Email | client_a@email.com |
| Rate Type | project |
| Rate | $2,450.00 per milestone |
| Payment Terms | Net 30 |

## Invoice Calculation

| Line | Value |
|------|------:|
| Base amount (project milestone) | $2,450.00 |
| Rush surcharge | $0.00 |
| Late fee | $0.00 |
| Tax (0%) | $0.00 |
| **Total** | **$2,450.00** |

Invoice number: **INV-2026-02-005**
Due date: **2026-03-28** (Net 30 from today)

## Execution Checklist

- [x] Read /Needs_Action trigger file
- [x] Looked up Client A in /Accounting/Rates.md
- [x] Calculated invoice amount: $2,450.00
- [x] Assigned invoice number: INV-2026-02-005
- [ ] Create approval request in /Pending_Approval/
- [ ] Human approves → send email via Gmail MCP
- [ ] Log transaction to /Accounting/Current_Month.md
- [ ] Update invoice number in /Accounting/Rates.md (next: INV-2026-02-006)
- [ ] Move task files to /Done

## Risk Assessment

- Email send to external party → **requires human approval** (HITL gate)
- Amount $2,450 > $500 → flagged per WhatsApp rules, but approval covers this
- Rollback: cannot unsend email; if sent in error, send correction immediately

## Approval Required

Routing to /Pending_Approval before any email is sent.

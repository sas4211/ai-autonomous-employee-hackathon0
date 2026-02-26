# Plan: Generate & Send Invoice — Client B

---
created: 2026-02-26T13:20:00Z
status: in_progress
task_source: /Needs_Action/2026-02-26_whatsapp_client-b.md
domain: business
risk: medium
---

## Objective

Generate invoice INV-2026-02-006 for Client B (hourly) and send via email after approval.

## Client Lookup (from /Accounting/Rates.md)

| Field | Value |
|-------|-------|
| Client ID | CLIENT_B |
| Name | Client B |
| Email | client_b@email.com |
| Rate Type | hourly |
| Rate | $95.00/hr (max 40h/mo) |
| Payment Terms | Net 30 |

## Invoice Calculation

| Line | Value |
|------|------:|
| Hours worked (February) | 20 |
| Hourly rate | $95.00 |
| Base amount (20 × $95.00) | $1,900.00 |
| Rush surcharge | $0.00 |
| Late fee | $0.00 |
| Tax (0%) | $0.00 |
| **Total** | **$1,900.00** |

Invoice number: **INV-2026-02-006**
Due date: **2026-03-28** (Net 30 from today)

## Execution Checklist

- [x] Read /Needs_Action trigger file
- [x] Looked up Client B in /Accounting/Rates.md
- [x] Calculated invoice amount: 20h × $95 = $1,900.00
- [x] Assigned invoice number: INV-2026-02-006
- [ ] Create approval request in /Pending_Approval/
- [ ] Human approves → send email via Gmail MCP
- [ ] Log transaction to /Accounting/Current_Month.md
- [ ] Update invoice counter in /Accounting/Rates.md
- [ ] Move task files to /Done

## Risk Assessment

- Email send to external party → requires human approval
- Amount $1,900 > $500 → covered by approval gate
- Hours (20) within monthly cap (40h) → no overage
